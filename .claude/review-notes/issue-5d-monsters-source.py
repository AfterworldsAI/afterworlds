# ruff: noqa: E501
"""The SRD 5.2.1 *Monsters* and *Monsters A-Z* parts as the release prints them
-- CRD Issue 5d.

Every leaf of both parts below their ``# Monsters`` and ``# Monsters A–Z``
headings, in printed order: *Monsters* (pp. 254-257), then *Monsters A-Z*
(pp. 258-344), as (full container label path, exact leaf text). The release,
like the PDF, prints the general rules first. Each text was qualified against the official
PDF (``docs/sources/DnD5_5e_SRD_CC_v5_2_1.pdf``) before it was written here:
prose word for word, every table row cell for cell, and every stat block's
ability table by its MOD and SAVE columns (see the monsters review packet).
The two part headings are left with the other part headings. The generator
names its spans from these texts; a text the release prints differently fails
to locate, loudly.
"""

from __future__ import annotations

LEAVES: tuple[tuple[tuple[str, ...], str], ...] = (
    (
        (
            "Monsters",
            "Stat Block Overview",
        ),
        "## Stat Block Overview",
    ),
    (
        (
            "Monsters",
            "Stat Block Overview",
        ),
        "A monster has a stat block that contains the rules necessary to use it in the game. Stat blocks are divided into the following parts:",
    ),
    (
        (
            "Monsters",
            "Stat Block Overview",
        ),
        "**Name and General Details.** The name of the monster is followed by its size, creature type (along with any descriptive tags), and alignment.",
    ),
    (
        (
            "Monsters",
            "Stat Block Overview",
        ),
        "**Combat Highlights.** Armor Class, Hit Points, Speed, and Initiative are provided here.",
    ),
    (
        (
            "Monsters",
            "Stat Block Overview",
        ),
        "**Ability Scores.** A monster's ability scores, ability modifiers, and saving throws are listed here.",
    ),
    (
        (
            "Monsters",
            "Stat Block Overview",
        ),
        "**Other Details.** The monster's Senses, Languages, and CR entries appear here. Additional details appear in some monsters, such as skill proficiencies, Resistances, Immunities, and Gear. If a monster lacks those details, entries for them don't appear.",
    ),
    (
        (
            "Monsters",
            "Stat Block Overview",
        ),
        "**Traits.** Monster characteristics that are active at all times or during certain situations appear here.",
    ),
    (
        (
            "Monsters",
            "Stat Block Overview",
        ),
        '**Actions.** The monster can take the actions here in addition to those in "Playing the Game."',
    ),
    (
        (
            "Monsters",
            "Stat Block Overview",
        ),
        "**Bonus Actions.** This section provides a monster's Bonus Actions, if any.",
    ),
    (
        (
            "Monsters",
            "Stat Block Overview",
        ),
        "**Reactions and Legendary Actions.** These sections provide Reactions and Legendary Actions, if any.",
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
        ),
        "## Parts of a Stat Block",
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
        ),
        'The rules for a stat block are detailed in "Rules Glossary" and in this section.',
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Size",
        ),
        "### Size",
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Size",
        ),
        'A monster is Tiny, Small, Medium, Large, Huge, or Gargantuan. If size options are presented, you choose the creature\'s size from those options. See "Playing the Game" for information on size.',
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Creature Type",
        ),
        "### Creature Type",
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Creature Type",
        ),
        "Each monster has a tag that identifies the type of creature it is. Certain spells, magic items, class features, and other effects in the game interact in special ways with creatures of a particular type.",
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Creature Type",
        ),
        "The game includes the following creature types, which have no rules of their own:",
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Creature Type",
        ),
        "**Aberrations** are utterly alien beings, such as aboleths and cloakers.",
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Creature Type",
        ),
        "**Beasts** are non-Humanoid natural creatures, like horses and wolves, as well as most giant animals.",
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Creature Type",
        ),
        "**Celestials** are magical creatures, such as angels and pegasi, with ties to the Upper Planes.",
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Creature Type",
        ),
        "**Constructs** are magically created creatures such as homunculi and shield guardians.",
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Creature Type",
        ),
        "**Dragons** are scaly beings of ancient origin, such as red dragons and wyverns.",
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Creature Type",
        ),
        "**Elementals** are beings from the Elemental Planes, such as efreet and water elementals.",
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Creature Type",
        ),
        "**Fey** are creatures tied to the Feywild or the forces of nature, such as dryads and goblins.",
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Creature Type",
        ),
        "**Fiends** are creatures tied to terrifying Lower Planes, such as balors and hell hounds.",
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Creature Type",
        ),
        "**Giants** are towering beings with humanlike shapes, like fire giants and trolls.",
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Creature Type",
        ),
        "**Humanoids** are people defined by their roles and professions, such as mages, pirates, and warriors. They include members of varied species.",
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Creature Type",
        ),
        "**Monstrosities** are unnatural creatures with strange origins, such as mimics and owlbears.",
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Creature Type",
        ),
        "**Oozes** are gelatinous creatures, including black puddings and gelatinous cubes.",
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Creature Type",
        ),
        "**Plants** are sentient vegetation and fungal monsters, such as shambling mounds and treants.",
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Creature Type",
        ),
        "**Undead** are spirits and the reanimated dead, such as ghosts, vampires, and zombies.",
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Creature Type",
            "Descriptive Tags",
        ),
        "#### Descriptive Tags",
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Creature Type",
            "Descriptive Tags",
        ),
        "A monster might have one or more tags in parentheses following its type. Such tags provide additional categorization and have no rules of their own, but certain game effects might refer to them.",
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Alignment",
        ),
        "### Alignment",
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Alignment",
        ),
        "The alignment specified in a monster's stat block is a default suggestion of how to roleplay the monster, inspired by its traditional role in the game or real-world folklore. Change a monster's alignment to suit your storytelling needs. The Neutral alignment, in particular, is an invitation for you to consider whether an individual leans toward one of the other alignments.",
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Alignment",
        ),
        '"Character Creation" describes the nine alignments and unaligned creatures.',
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Armor Class",
        ),
        "### Armor Class",
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Armor Class",
        ),
        'A monster\'s Armor Class (AC) includes its natural armor, Dexterity, gear, and other defenses. See "Playing the Game" for information on Armor Class.',
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Initiative",
        ),
        "### Initiative",
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Initiative",
        ),
        "The Initiative entry specifies the monster's Initiative modifier followed by the monster's Initiative score in parentheses. Use the modifier when you roll to determine a monster's Initiative. A monster's Initiative modifier is typically equal to its Dexterity modifier, but some monsters have additional modifiers, such as Proficiency Bonus, applied to that number.",
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Initiative",
        ),
        "If you don't want to roll a monster's Initiative, use the Initiative score as the monster's Initiative in combat. Initiative is further detailed in \"Playing the Game.\"",
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Hit Points",
        ),
        "### Hit Points",
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Hit Points",
        ),
        "A monster's Hit Points are presented as a number followed by parentheses, where the monster's Hit Point Dice are provided, along with any contribution from its Constitution. Either use the number for the monster's Hit Points or roll the die expression in parentheses to determine the monster's Hit Points randomly; don't use both.",
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Hit Points",
        ),
        "A monster's size typically determines the die used to calculate its Hit Points, as shown in the Hit Dice by Size table.",
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Hit Points",
        ),
        "**Hit Dice by Size**\n\n<table>\n  <thead>\n    <tr>\n      <th>Monster Size</th>\n      <th>Hit Die</th>\n      <th>Average HP per Die</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>Tiny</td>\n      <td>d4</td>\n      <td>2½</td>\n    </tr>\n    <tr>\n      <td>Small</td>\n      <td>d6</td>\n      <td>3½</td>\n    </tr>\n    <tr>\n      <td>Medium</td>\n      <td>d8</td>\n      <td>4½</td>\n    </tr>\n    <tr>\n      <td>Large</td>\n      <td>d10</td>\n      <td>5½</td>\n    </tr>\n    <tr>\n      <td>Huge</td>\n      <td>d12</td>\n      <td>6½</td>\n    </tr>\n    <tr>\n      <td>Gargantuan</td>\n      <td>d20</td>\n      <td>10½</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Hit Points",
        ),
        "A monster's Constitution modifier is multiplied by the number of Hit Dice it possesses, and the result is added to its Hit Points. For example, if a monster has a Constitution of 12 (+1 modifier) and 2d8 Hit Dice, it has 2d8 + 2 Hit Points (average 11).",
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Hit Points",
        ),
        'For more on Hit Points, see "Playing the Game."',
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Speed",
        ),
        "### Speed",
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Speed",
        ),
        'The Speed entry specifies a monster\'s Speed. Some monsters have one or more of the following speeds: Burrow, Climb, Fly, Swim. Rules for Speed and these specials speeds appear in "Rules Glossary."',
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Ability Scores",
        ),
        "### Ability Scores",
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Ability Scores",
        ),
        'Every monster has six ability scores along with corresponding ability score modifiers and saving throw modifiers. For more information on ability scores and saving throws, see "Playing the Game."',
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Skills",
        ),
        "### Skills",
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Skills",
        ),
        "The Skills entry specifies a monster's skill proficiencies, if any. For example, a monster that is very perceptive and stealthy might have bonuses to Wisdom (Perception) and Dexterity (Stealth) checks. A skill bonus is the sum of a monster's relevant ability modifier and its Proficiency Bonus. Other modifiers might apply.",
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Resistances and Vulnerabilities",
        ),
        "### Resistances and Vulnerabilities",
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Resistances and Vulnerabilities",
        ),
        'These entries list a monster\'s Resistances and Vulnerabilities, if any. See "Playing the Game" for more information.',
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Resistances and Vulnerabilities",
        ),
        "> **Running a Monster**\n>\n> To ensure a monster acts in accordance with its Challenge Rating, follow these rules during combat:\n>\n> **Special Abilities.** If the monster has a special ability that deals a lot of damage but has a limited number of uses, such as a recharging breath weapon or a spell it can cast only once per day, have it use that special ability as quickly and as often as possible.\n>\n> **Multiattack.** If the monster has Multiattack, have it use Multiattack on any of its turns in which it's not using one of its more powerful abilities.\n>\n> **Bonus Actions, Reactions, Legendary Actions.** If the monster has Bonus Actions, Reactions, or Legendary Actions in its stat block, make sure it uses them as often as it can.",
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Immunities",
        ),
        "### Immunities",
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Immunities",
        ),
        'This entry lists the monster\'s Immunities, if any. If the monster has damage and condition Immunities, the damage types are listed before the conditions. See "Playing the Game" for details.',
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Gear",
        ),
        "### Gear",
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Gear",
        ),
        'Monsters have proficiency with their equipment. If a monster has equipment that can be given away or retrieved, the items are listed in the Gear entry. The monster\'s stat block might include special flourishes that happen when the monster uses an item, and the stat block might ignore the rules in "Equipment" for that item. When used by someone else, a retrievable item uses its "Equipment" rules, ignoring any special flourishes in the stat block.',
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Gear",
        ),
        "The Gear entry doesn't necessarily list all of a monster's equipment. For example, a monster that wears clothes is assumed to be dressed appropriately, and those clothes aren't in this entry.",
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Gear",
        ),
        "Equipment mentioned outside the Gear entry is considered to be supernatural or highly specialized, and it is unusable when the monster is defeated.",
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Gear",
            "Ammunition and Ranged Attacks",
        ),
        "#### Ammunition and Ranged Attacks",
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Gear",
            "Ammunition and Ranged Attacks",
        ),
        "A monster that requires ammunition to make ranged attacks carries the necessary ammunition.",
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Gear",
            "Equipping a Monster with Other Items",
        ),
        "#### Equipping a Monster with Other Items",
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Gear",
            "Equipping a Monster with Other Items",
        ),
        'You may equip monsters with additional gear however you like, using the items in "Equipment" for inspiration. You decide how much of a monster\'s equipment is recoverable after the creature is slain and whether any of that equipment is still usable.',
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Gear",
            "Equipping a Monster with Other Items",
        ),
        'Beware of giving a monster combat-oriented magic items, since those might alter the monster\'s Challenge Rating. If you do give a monster a magic item, the monster can have Attunement with magic items as noted in "Equipment." A monster with a class tag after its creature type is considered a member of that class for Attunement purposes.',
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Senses",
        ),
        "### Senses",
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Senses",
        ),
        'The Senses entry specifies a monster\'s Passive Perception score, as well as any special senses the monster possesses. Passive Perception and special senses are described in "Rules Glossary."',
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Languages",
        ),
        "### Languages",
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Languages",
        ),
        "This entry lists languages that the monster can use to communicate. Sometimes a monster can understand a language but can't communicate with it, which is noted in its entry. \"None\" indicates that a creature doesn't comprehend any language.",
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Languages",
            "Telepathy",
        ),
        "#### Telepathy",
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Languages",
            "Telepathy",
        ),
        'Telepathy is a magical ability that allows a creature to communicate mentally with another creature within a specified range. See "Rules Glossary" for more information.',
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Challenge Rating",
        ),
        "### Challenge Rating",
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Challenge Rating",
        ),
        'Challenge Rating is defined in "Rules Glossary," while guidance on using CR to plan potential combat encounters is in "Gameplay Toolbox."',
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Challenge Rating",
            "Experience Points",
        ),
        "#### Experience Points",
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Challenge Rating",
            "Experience Points",
        ),
        "The number of Experience Points (XP) a monster is worth is based on its CR, as detailed in the Experience Points by Challenge Rating table. XP is awarded for defeating the monster in combat or otherwise neutralizing it.",
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Challenge Rating",
            "Experience Points",
        ),
        "Unless a rule says otherwise, a monster summoned by a spell or another magical ability is worth the XP noted in its stat block.",
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Challenge Rating",
            "Experience Points",
        ),
        "**Experience Points by Challenge Rating**\n\n<table>\n  <thead>\n    <tr>\n      <th>CR</th>\n      <th>XP</th>\n      <th>CR</th>\n      <th>XP</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>0</td>\n      <td>0 or 10</td>\n      <td>14</td>\n      <td>11,500</td>\n    </tr>\n    <tr>\n      <td>1/8</td>\n      <td>25</td>\n      <td>15</td>\n      <td>13,000</td>\n    </tr>\n    <tr>\n      <td>1/4</td>\n      <td>50</td>\n      <td>16</td>\n      <td>15,000</td>\n    </tr>\n    <tr>\n      <td>1/2</td>\n      <td>100</td>\n      <td>17</td>\n      <td>18,000</td>\n    </tr>\n    <tr>\n      <td>1</td>\n      <td>200</td>\n      <td>18</td>\n      <td>20,000</td>\n    </tr>\n    <tr>\n      <td>2</td>\n      <td>450</td>\n      <td>19</td>\n      <td>22,000</td>\n    </tr>\n    <tr>\n      <td>3</td>\n      <td>700</td>\n      <td>20</td>\n      <td>25,000</td>\n    </tr>\n    <tr>\n      <td>4</td>\n      <td>1,100</td>\n      <td>21</td>\n      <td>33,000</td>\n    </tr>\n    <tr>\n      <td>5</td>\n      <td>1,800</td>\n      <td>22</td>\n      <td>41,000</td>\n    </tr>\n    <tr>\n      <td>6</td>\n      <td>2,300</td>\n      <td>23</td>\n      <td>50,000</td>\n    </tr>\n    <tr>\n      <td>7</td>\n      <td>2,900</td>\n      <td>24</td>\n      <td>62,000</td>\n    </tr>\n    <tr>\n      <td>8</td>\n      <td>3,900</td>\n      <td>25</td>\n      <td>75,000</td>\n    </tr>\n    <tr>\n      <td>9</td>\n      <td>5,000</td>\n      <td>26</td>\n      <td>90,000</td>\n    </tr>\n    <tr>\n      <td>10</td>\n      <td>5,900</td>\n      <td>27</td>\n      <td>105,000</td>\n    </tr>\n    <tr>\n      <td>11</td>\n      <td>7,200</td>\n      <td>28</td>\n      <td>120,000</td>\n    </tr>\n    <tr>\n      <td>12</td>\n      <td>8,400</td>\n      <td>29</td>\n      <td>135,000</td>\n    </tr>\n    <tr>\n      <td>13</td>\n      <td>10,000</td>\n      <td>30</td>\n      <td>155,000</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Challenge Rating",
            "Proficiency Bonus",
        ),
        "#### Proficiency Bonus",
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Challenge Rating",
            "Proficiency Bonus",
        ),
        "A monster's Proficiency Bonus (PB) is determined by its CR, as shown in the Proficiency Bonus by Challenge Rating table, and is reflected in saving throws, skills, and other statistics where the monster's exceptional aptitude is a factor.",
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Challenge Rating",
            "Proficiency Bonus",
        ),
        "**Proficiency Bonus by Challenge Rating**\n\n<table>\n  <thead>\n    <tr>\n      <th>CR</th>\n      <th>PB</th>\n      <th>CR</th>\n      <th>PB</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>0–4</td>\n      <td>+2</td>\n      <td>17–20</td>\n      <td>+6</td>\n    </tr>\n    <tr>\n      <td>5–8</td>\n      <td>+3</td>\n      <td>21–24</td>\n      <td>+7</td>\n    </tr>\n    <tr>\n      <td>9–12</td>\n      <td>+4</td>\n      <td>25–28</td>\n      <td>+8</td>\n    </tr>\n    <tr>\n      <td>13–16</td>\n      <td>+5</td>\n      <td>29–30</td>\n      <td>+9</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Traits",
        ),
        "### Traits",
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Traits",
        ),
        "A monster's traits, if any, are features that are active at all times or in certain situations.",
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Actions",
        ),
        'A monster can take the actions in this section or take one of the actions available to all creatures, as described in "Playing the Game."',
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Actions",
            "Attack Notation",
        ),
        "#### Attack Notation",
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Actions",
            "Attack Notation",
        ),
        'The entry for a monster\'s attack identifies whether the attack is a melee or a ranged attack and then provides the attack roll\'s bonus, its reach or range, and what happens on a hit. An attack is against one target unless its entry says otherwise. For details on different kinds of attacks, see "Playing the Game" and "Spells."',
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Actions",
            "Attack Notation",
        ),
        '**_Hit._** Any damage dealt or other effects that occur as a result of an attack hitting a target are described after the "Hit:" notation.',
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Actions",
            "Attack Notation",
        ),
        '**_Miss._** If an attack has an effect that occurs on a miss, that information follows the "Miss:" notation.',
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Actions",
            "Attack Notation",
        ),
        '**_Hit or Miss._** If an attack has an effect that occurs regardless of whether it hits or misses its target, that information follows the "Hit or Miss:" notation.',
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Actions",
            "Saving Throw Effect Notation",
        ),
        "#### Saving Throw Effect Notation",
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Actions",
            "Saving Throw Effect Notation",
        ),
        "If an effect forces a saving throw, the effect identifies the kind of save required and then provides the save's DC, a description of which creatures make the save, and an explanation of what happens on a failed or successful save.",
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Actions",
            "Saving Throw Effect Notation",
        ),
        '"Half damage only" on a successful save means the target takes half as much damage (round down) as targets that fail the save, while also ignoring all other parts of the effect.',
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Actions",
            "Damage Notation",
        ),
        "#### Damage Notation",
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Actions",
            "Damage Notation",
        ),
        "A stat block usually provides both a number and a die expression for each instance of damage. For example, an attack might deal 4 (1d4 + 2) damage on a hit. You decide whether to use the number or the die expression in parentheses; don't use both.",
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Actions",
            "Multiattack",
        ),
        "#### Multiattack",
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Actions",
            "Multiattack",
        ),
        'Some creatures can make more than one attack when they take the Attack action. Such creatures have the Multiattack entry in the "Actions" section of their stat block. This entry details the attacks a creature can make, as well as any additional abilities it can use, as part of the Attack action.',
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Actions",
            "Spellcasting",
        ),
        "#### Spellcasting",
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Actions",
            "Spellcasting",
        ),
        "If a monster can cast any spells, its stat block lists the spells and provides the monster's spellcasting ability, spell save DC (if any spells require a saving throw), and spell attack bonus (if any spells require an attack roll). Unless noted otherwise, a spell of level 1 or higher is always cast at its lowest possible level and can't be cast at a higher level.",
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Actions",
            "Spellcasting",
        ),
        'A monster\'s spell can have special rules or restrictions. For example, a green hag can cast the _Invisibility_ spell, but the spell has a "self only" restriction, which means the spell affects only the hag.',
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Actions",
            "Spellcasting",
        ),
        "_Spell Components._ The Spellcasting trait notes whether the monster's spellcasting ignores the need for certain spell components. If any spell components are required, describe the monster's use of Verbal, Somatic, or Material components to signal to characters that it is casting a spell. A monster that requires Material components has them.",
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Actions",
            "Spellcasting",
        ),
        "_Casting Times of 1+ Minutes._ If a spell has a casting time of 1 minute or more yet is listed in a spellcasting action, the monster doesn't cast the spell in just one action unless the action's description states otherwise; the monster must take the Magic action on each of its turns and maintain Concentration to cast the spell, as described in \"Rules Glossary.\"",
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Bonus Action",
        ),
        "### Bonus Action",
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Bonus Action",
        ),
        'If a monster has Bonus Action options, they are listed in this section. See "Playing the Game" for details on Bonus Actions.',
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Reactions",
        ),
        "### Reactions",
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Reactions",
        ),
        'If the monster has Reaction options, those are listed in this section along with their triggers. See "Playing the Game" for details on Reactions.',
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Legendary Actions",
        ),
        "### Legendary Actions",
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Legendary Actions",
        ),
        "If the monster has Legendary Action options, those are listed in this section. A Legendary Action is an action that a monster can take immediately after another creature's turn. Only one of these actions can be taken at a time and only after another creature's turn ends. The monster can't take a Legendary Action if it has the Incapacitated condition or is otherwise unable to take actions.",
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Legendary Actions",
        ),
        "The monster has a limited number of Legendary Action uses, and that number is specified in the stat block. The monster expends one use whenever it takes a Legendary Action, and it regains all expended uses at the start of each of its turns.",
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Limited Usage",
        ),
        "### Limited Usage",
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Limited Usage",
        ),
        "Some parts of a stat block have restrictions on the number of times they can be used. Here are the most common ways that usage is limited:",
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Limited Usage",
        ),
        '**X/Day.** This notation means the stat block part can be used a certain number of times (represented by X) and that a monster must finish a Long Rest to regain expended uses. For example, a Reaction that includes "1/Day" means the Reaction can be taken once and that the monster must finish a Long Rest to take it again.',
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Limited Usage",
        ),
        "**Recharge X–Y.** This notation means a monster can use the stat block part once. At the start of each of the monster's turns, roll 1d6. If the roll is within the number range given in the notation (represented by X–Y), the monster regains the use of that part, which also recharges when the monster finishes a Short or Long Rest. For example, \"Recharge 5–6\" in an action means a monster can take the action once. Then, at the start of each of the monster's turns, it regains the use of that action if it rolls a 5 or 6 on 1d6.",
    ),
    (
        (
            "Monsters",
            "Parts of a Stat Block",
            "Limited Usage",
        ),
        "**Recharge after a Short or Long Rest.** This notation means the monster can use the stat block part once and must then finish a Short or Long Rest to use it again.",
    ),
    (
        (
            "Monsters A–Z",
            "Aboleth",
        ),
        "## Aboleth",
    ),
    (
        (
            "Monsters A–Z",
            "Aboleth",
            "Aboleth",
        ),
        "### Aboleth",
    ),
    (
        (
            "Monsters A–Z",
            "Aboleth",
            "Aboleth",
        ),
        "_Large Aberration, Lawful Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Aboleth",
            "Aboleth",
        ),
        "**AC** 17 **Initiative** +7 (17) <br>\n**HP** 150 (20d10 + 40) <br>\n**Speed** 10 ft., Swim 40 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Aboleth",
            "Aboleth",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>21</td>\n      <td>+5</td>\n      <td>+5</td>\n      <td><strong>DEX</strong></td>\n      <td>9</td>\n      <td>−1</td>\n      <td>+3</td>\n      <td><strong>CON</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+6</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+8</td>\n      <td><strong>WIS</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+6</td>\n      <td><strong>CHA</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+4</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Aboleth",
            "Aboleth",
        ),
        "**Skills** History +12, Perception +10<br>\n**Senses** Darkvision 120 ft.; Passive Perception 20<br>\n**Languages** Deep Speech; telepathy 120 ft.<br>\n**CR** 10 (XP 5,900, or 7,200 in lair; PB +4)",
    ),
    (
        (
            "Monsters A–Z",
            "Aboleth",
            "Aboleth",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Aboleth",
            "Aboleth",
            "Traits",
        ),
        "**_Amphibious._** The aboleth can breathe air and water.",
    ),
    (
        (
            "Monsters A–Z",
            "Aboleth",
            "Aboleth",
            "Traits",
        ),
        "**_Eldritch Restoration._** If destroyed, the aboleth gains a new body in 5d10 days, reviving with all its Hit Points in the Far Realm or another location chosen by the GM.",
    ),
    (
        (
            "Monsters A–Z",
            "Aboleth",
            "Aboleth",
            "Traits",
        ),
        "**_Legendary Resistance (3/Day, or 4/Day in Lair)._** If the aboleth fails a saving throw, it can choose to succeed instead.",
    ),
    (
        (
            "Monsters A–Z",
            "Aboleth",
            "Aboleth",
            "Traits",
        ),
        "**_Mucus Cloud._** While underwater, the aboleth is surrounded by mucus. _Constitution Saving Throw:_ DC 14, each creature in a 5-foot Emanation originating from the aboleth at the end of the aboleth's turn. _Failure:_ The target is cursed. Until the curse ends, the target's skin becomes slimy, the target can breathe air and water, and it can't regain Hit Points unless it is underwater. <br>\n&emsp;While the cursed creature is outside a body of water, the creature takes 6 (1d12) Acid damage at the end of every 10 minutes unless moisture is applied to its skin before those minutes have passed.",
    ),
    (
        (
            "Monsters A–Z",
            "Aboleth",
            "Aboleth",
            "Traits",
        ),
        "**_Probing Telepathy._** If a creature the aboleth can see communicates telepathically with the aboleth, the aboleth learns the creature's greatest desires.",
    ),
    (
        (
            "Monsters A–Z",
            "Aboleth",
            "Aboleth",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Aboleth",
            "Aboleth",
            "Actions",
        ),
        "**_Multiattack._** The aboleth makes two Tentacle attacks and uses either Consume Memories or Dominate Mind if available.",
    ),
    (
        (
            "Monsters A–Z",
            "Aboleth",
            "Aboleth",
            "Actions",
        ),
        "**_Tentacle._** _Melee Attack Roll:_ +9, reach 15 ft. _Hit:_ 12 (2d6 + 5) Bludgeoning damage. If the target is a Large or smaller creature, it has the Grappled condition (escape DC 14) from one of four tentacles.",
    ),
    (
        (
            "Monsters A–Z",
            "Aboleth",
            "Aboleth",
            "Actions",
        ),
        "**_Consume Memories._** _Intelligence Saving Throw:_ DC 16, one creature within 30 feet that is Charmed or Grappled by the aboleth. _Failure:_ 10 (3d6) Psychic damage. <br>\n&emsp;_Success:_ Half damage. _Failure or Success:_ The aboleth gains the target's memories if the target is a Humanoid and is reduced to 0 Hit Points by this action.",
    ),
    (
        (
            "Monsters A–Z",
            "Aboleth",
            "Aboleth",
            "Actions",
        ),
        "**_Dominate Mind (2/Day)._** _Wisdom Saving Throw:_ DC 16, one creature the aboleth can see within 30 feet. _Failure:_ The target has the Charmed condition until the aboleth dies or is on a different plane of existence from the target. While Charmed, the target acts as an ally to the aboleth and is under its control while within 60 feet of it. In addition, the aboleth and the target can communicate telepathically with each other over any distance. <br>\n&emsp;The target repeats the save whenever it takes damage as well as after every 24 hours it spends at least 1 mile away from the aboleth, ending the effect on itself on a success.",
    ),
    (
        (
            "Monsters A–Z",
            "Aboleth",
            "Aboleth",
            "Legendary Actions",
        ),
        "#### Legendary Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Aboleth",
            "Aboleth",
            "Legendary Actions",
        ),
        "_Legendary Action Uses: 3 (4 in Lair). Immediately after another creature's turn, the aboleth can expend a use to take one of the following actions. The aboleth regains all expended uses at the start of each of its turns._",
    ),
    (
        (
            "Monsters A–Z",
            "Aboleth",
            "Aboleth",
            "Legendary Actions",
        ),
        "**_Lash._** The aboleth makes one Tentacle attack.",
    ),
    (
        (
            "Monsters A–Z",
            "Aboleth",
            "Aboleth",
            "Legendary Actions",
        ),
        "**_Psychic Drain._** If the aboleth has at least one creature Charmed or Grappled, it uses Consume Memories and regains 5 (1d10) Hit Points.",
    ),
    (
        (
            "Monsters A–Z",
            "Air Elemental",
        ),
        "## Air Elemental",
    ),
    (
        (
            "Monsters A–Z",
            "Air Elemental",
            "Air Elemental",
        ),
        "### Air Elemental",
    ),
    (
        (
            "Monsters A–Z",
            "Air Elemental",
            "Air Elemental",
        ),
        "_Large Elemental, Neutral_",
    ),
    (
        (
            "Monsters A–Z",
            "Air Elemental",
            "Air Elemental",
        ),
        "**AC** 15 **Initiative** +5 (15) <br>\n**HP** 90 (12d10 + 24) <br>\n**Speed** 10 ft., Fly 90 ft. (hover) <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Air Elemental",
            "Air Elemental",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>DEX</strong></td>\n      <td>20</td>\n      <td>+5</td>\n      <td>+5</td>\n      <td><strong>CON</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>6</td>\n      <td>−2</td>\n      <td>−2</td>\n      <td><strong>WIS</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CHA</strong></td>\n      <td>6</td>\n      <td>−2</td>\n      <td>−2</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Air Elemental",
            "Air Elemental",
        ),
        "**Resistances** Bludgeoning, Lightning, Piercing, Slashing<br>\n**Immunities** Poison, Thunder; Exhaustion, Grappled, Paralyzed, Petrified, Poisoned, Prone, Restrained, Unconscious<br>\n**Senses** Darkvision 60 ft.; Passive Perception 10<br>\n**Languages** Primordial (Auran)<br>\n**CR** 5 (XP 1,800; PB +3)",
    ),
    (
        (
            "Monsters A–Z",
            "Air Elemental",
            "Air Elemental",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Air Elemental",
            "Air Elemental",
            "Traits",
        ),
        "**_Air Form._** The elemental can enter a creature's space and stop there. It can move through a space as narrow as 1 inch without expending extra movement to do so.",
    ),
    (
        (
            "Monsters A–Z",
            "Air Elemental",
            "Air Elemental",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Air Elemental",
            "Air Elemental",
            "Actions",
        ),
        "**_Multiattack._** The elemental makes two Thunderous Slam attacks.",
    ),
    (
        (
            "Monsters A–Z",
            "Air Elemental",
            "Air Elemental",
            "Actions",
        ),
        "**_Thunderous Slam._** _Melee Attack Roll:_ +8, reach 10 ft. _Hit:_ 14 (2d8 + 5) Thunder damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Air Elemental",
            "Air Elemental",
            "Actions",
        ),
        "**_Whirlwind (Recharge 4–6)._** _Strength Saving Throw:_ DC 13, one Medium or smaller creature in the elemental's space. _Failure:_ 24 (4d10 + 2) Thunder damage, and the target is pushed up to 20 feet straight away from the elemental and has the Prone condition. _Success:_ Half damage only.",
    ),
    (
        (
            "Monsters A–Z",
            "Animated Objects",
        ),
        "## Animated Objects",
    ),
    (
        (
            "Monsters A–Z",
            "Animated Objects",
            "Animated Armor",
        ),
        "### Animated Armor",
    ),
    (
        (
            "Monsters A–Z",
            "Animated Objects",
            "Animated Armor",
        ),
        "_Medium Construct, Unaligned_",
    ),
    (
        (
            "Monsters A–Z",
            "Animated Objects",
            "Animated Armor",
        ),
        "**AC** 18 **Initiative** +2 (12) <br>\n**HP** 33 (6d8 + 6) <br>\n**Speed** 25 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Animated Objects",
            "Animated Armor",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>DEX</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CON</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>1</td>\n      <td>−5</td>\n      <td>−5</td>\n      <td><strong>WIS</strong></td>\n      <td>3</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>CHA</strong></td>\n      <td>1</td>\n      <td>−5</td>\n      <td>−5</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Animated Objects",
            "Animated Armor",
        ),
        "**Immunities** Poison, Psychic; Charmed, Deafened, Exhaustion, Frightened, Paralyzed, Petrified, Poisoned<br>\n**Senses** Blindsight 60 ft.; Passive Perception 6<br>\n**Languages** None<br>\n**CR** 1 (XP 200; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Animated Objects",
            "Animated Armor",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Animated Objects",
            "Animated Armor",
            "Actions",
        ),
        "**_Multiattack._** The armor makes two Slam attacks.",
    ),
    (
        (
            "Monsters A–Z",
            "Animated Objects",
            "Animated Armor",
            "Actions",
        ),
        "**_Slam._** _Melee Attack Roll:_ +4, reach 5 ft. _Hit:_ 5 (1d6 + 2) Bludgeoning damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Animated Objects",
            "Animated Flying Sword",
        ),
        "### Animated Flying Sword",
    ),
    (
        (
            "Monsters A–Z",
            "Animated Objects",
            "Animated Flying Sword",
        ),
        "_Small Construct, Unaligned_",
    ),
    (
        (
            "Monsters A–Z",
            "Animated Objects",
            "Animated Flying Sword",
        ),
        "**AC** 17 **Initiative** +4 (14) <br>\n**HP** 14 (4d6) <br>\n**Speed** 5 ft., Fly 50 ft. (hover) <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Animated Objects",
            "Animated Flying Sword",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>DEX</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+4</td>\n      <td><strong>CON</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>1</td>\n      <td>−5</td>\n      <td>−5</td>\n      <td><strong>WIS</strong></td>\n      <td>5</td>\n      <td>−3</td>\n      <td>−3</td>\n      <td><strong>CHA</strong></td>\n      <td>1</td>\n      <td>−5</td>\n      <td>−5</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Animated Objects",
            "Animated Flying Sword",
        ),
        "**Immunities** Poison, Psychic; Charmed, Deafened, Exhaustion, Frightened, Paralyzed, Petrified, Poisoned<br>\n**Senses** Blindsight 60 ft.; Passive Perception 7<br>\n**Languages** None<br>\n**CR** 1/4 (XP 50; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Animated Objects",
            "Animated Flying Sword",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Animated Objects",
            "Animated Flying Sword",
            "Actions",
        ),
        "**_Slash._** _Melee Attack Roll:_ +4, reach 5 ft. _Hit:_ 6 (1d8 + 2) Slashing damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Animated Objects",
            "Animated Rug of Smothering",
        ),
        "### Animated Rug of Smothering",
    ),
    (
        (
            "Monsters A–Z",
            "Animated Objects",
            "Animated Rug of Smothering",
        ),
        "_Large Construct, Unaligned_",
    ),
    (
        (
            "Monsters A–Z",
            "Animated Objects",
            "Animated Rug of Smothering",
        ),
        "**AC** 12 **Initiative** +4 (14) <br>\n**HP** 27 (5d10) <br>\n**Speed** 10 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Animated Objects",
            "Animated Rug of Smothering",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>17</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>DEX</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CON</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>1</td>\n      <td>−5</td>\n      <td>−5</td>\n      <td><strong>WIS</strong></td>\n      <td>3</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>CHA</strong></td>\n      <td>1</td>\n      <td>−5</td>\n      <td>−5</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Animated Objects",
            "Animated Rug of Smothering",
        ),
        "**Immunities** Poison, Psychic; Charmed, Deafened, Exhaustion, Frightened, Paralyzed, Petrified, Poisoned<br>\n**Senses** Blindsight 60 ft.; Passive Perception 6<br>\n**Languages** None<br>\n**CR** 2 (XP 450; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Animated Objects",
            "Animated Rug of Smothering",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Animated Objects",
            "Animated Rug of Smothering",
            "Actions",
        ),
        "**_Smother._** _Melee Attack Roll:_ +5, reach 5 ft. _Hit:_ 10 (2d6 + 3) Bludgeoning damage. If the target is a Medium or smaller creature, the rug can give it the Grappled condition (escape DC 13) instead of dealing damage. Until the grapple ends, the target has the Blinded and Restrained conditions, is suffocating, and takes 10 (2d6 + 3) Bludgeoning damage at the start of each of its turns. The rug can smother only one creature at a time. <br>\n&emsp;While grappling the target, the rug can't take this action, the rug halves the damage it takes (round down), and the target takes the same amount of damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Ankheg",
        ),
        "## Ankheg",
    ),
    (
        (
            "Monsters A–Z",
            "Ankheg",
            "Ankheg",
        ),
        "### Ankheg",
    ),
    (
        (
            "Monsters A–Z",
            "Ankheg",
            "Ankheg",
        ),
        "_Large Monstrosity, Unaligned_",
    ),
    (
        (
            "Monsters A–Z",
            "Ankheg",
            "Ankheg",
        ),
        "**AC** 14 **Initiative** +0 (10) <br>\n**HP** 45 (6d10 + 12) <br>\n**Speed** 30 ft., Burrow 10 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Ankheg",
            "Ankheg",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>17</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>DEX</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CON</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>1</td>\n      <td>−5</td>\n      <td>−5</td>\n      <td><strong>WIS</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CHA</strong></td>\n      <td>6</td>\n      <td>−2</td>\n      <td>−2</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Ankheg",
            "Ankheg",
        ),
        "**Senses** Darkvision 60 ft., Tremorsense 60 ft.; Passive Perception 11<br>\n**Languages** None<br>\n**CR** 2 (XP 450; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Ankheg",
            "Ankheg",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Ankheg",
            "Ankheg",
            "Traits",
        ),
        "**_Tunneler._** The ankheg can burrow through solid rock at half its Burrow Speed and leaves a 10-foot-diameter tunnel in its wake.",
    ),
    (
        (
            "Monsters A–Z",
            "Ankheg",
            "Ankheg",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Ankheg",
            "Ankheg",
            "Actions",
        ),
        "**_Bite._** _Melee Attack Roll:_ +5 (with Advantage if the target is Grappled by the ankheg), reach 5 ft. _Hit:_ 10 (2d6 + 3) Slashing damage plus 3 (1d6) Acid damage. If the target is a Large or smaller creature, it has the Grappled condition (escape DC 13).",
    ),
    (
        (
            "Monsters A–Z",
            "Ankheg",
            "Ankheg",
            "Actions",
        ),
        "**_Acid Spray (Recharge 6)._** _Dexterity Saving Throw:_ DC 12, each creature in a 30-foot-long, 5-foot-wide Line. _Failure:_ 14 (4d6) Acid damage. _Success:_ Half damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Assassin",
        ),
        "## Assassin",
    ),
    (
        (
            "Monsters A–Z",
            "Assassin",
            "Assassin",
        ),
        "### Assassin",
    ),
    (
        (
            "Monsters A–Z",
            "Assassin",
            "Assassin",
        ),
        "_Medium or Small Humanoid, Neutral_",
    ),
    (
        (
            "Monsters A–Z",
            "Assassin",
            "Assassin",
        ),
        "**AC** 16 **Initiative** +10 (20) <br>\n**HP** 97 (15d8 + 30) <br>\n**Speed** 30 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Assassin",
            "Assassin",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>DEX</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+7</td>\n      <td><strong>CON</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+6</td>\n      <td><strong>WIS</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CHA</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Assassin",
            "Assassin",
        ),
        "**Skills** Acrobatics +7, Perception +6, Stealth +10<br>\n**Resistances** Poison<br>\n**Gear** Light Crossbow, Shortsword, Studded Leather Armor<br>\n**Senses** Passive Perception 16<br>\n**Languages** Common, Thieves' Cant<br>\n**CR** 8 (XP 3,900; PB +3)",
    ),
    (
        (
            "Monsters A–Z",
            "Assassin",
            "Assassin",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Assassin",
            "Assassin",
            "Traits",
        ),
        "**_Evasion._** If the assassin is subjected to an effect that allows it to make a Dexterity saving throw to take only half damage, the assassin instead takes no damage if it succeeds on the save and only half damage if it fails. It can't use this trait if it has the Incapacitated condition.",
    ),
    (
        (
            "Monsters A–Z",
            "Assassin",
            "Assassin",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Assassin",
            "Assassin",
            "Actions",
        ),
        "**_Multiattack._** The assassin makes three attacks, using Shortsword or Light Crossbow in any combination.",
    ),
    (
        (
            "Monsters A–Z",
            "Assassin",
            "Assassin",
            "Actions",
        ),
        "**_Shortsword._** _Melee Attack Roll:_ +7, reach 5 ft. _Hit:_ 7 (1d6 + 4) Piercing damage plus 17 (5d6) Poison damage, and the target has the Poisoned condition until the start of the assassin's next turn.",
    ),
    (
        (
            "Monsters A–Z",
            "Assassin",
            "Assassin",
            "Actions",
        ),
        "**_Light Crossbow._** _Ranged Attack Roll:_ +7, range 80/320 ft. _Hit:_ 8 (1d8 + 4) Piercing damage plus 21 (6d6) Poison damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Assassin",
            "Assassin",
            "Bonus Actions",
        ),
        "#### Bonus Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Assassin",
            "Assassin",
            "Bonus Actions",
        ),
        "**_Cunning Action._** The assassin takes the Dash, Disengage, or Hide action.",
    ),
    (
        (
            "Monsters A–Z",
            "Awakened Plants",
        ),
        "## Awakened Plants",
    ),
    (
        (
            "Monsters A–Z",
            "Awakened Plants",
            "Awakened Shrub",
        ),
        "### Awakened Shrub",
    ),
    (
        (
            "Monsters A–Z",
            "Awakened Plants",
            "Awakened Shrub",
        ),
        "_Small Plant, Neutral_",
    ),
    (
        (
            "Monsters A–Z",
            "Awakened Plants",
            "Awakened Shrub",
        ),
        "**AC** 9 **Initiative** −1 (9) <br>\n**HP** 10 (3d6) <br>\n**Speed** 20 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Awakened Plants",
            "Awakened Shrub",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>3</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>DEX</strong></td>\n      <td>8</td>\n      <td>−1</td>\n      <td>−1</td>\n      <td><strong>CON</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>WIS</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CHA</strong></td>\n      <td>6</td>\n      <td>−2</td>\n      <td>−2</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Awakened Plants",
            "Awakened Shrub",
        ),
        "**Vulnerabilities** Fire<br>\n**Resistances** Piercing<br>\n**Senses** Passive Perception 10<br>\n**Languages** Common plus one other language<br>\n**CR** 0 (XP 10; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Awakened Plants",
            "Awakened Shrub",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Awakened Plants",
            "Awakened Shrub",
            "Actions",
        ),
        "**_Rake._** _Melee Attack Roll:_ +1, reach 5 ft. _Hit:_ 1 Slashing damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Awakened Plants",
            "Awakened Tree",
        ),
        "### Awakened Tree",
    ),
    (
        (
            "Monsters A–Z",
            "Awakened Plants",
            "Awakened Tree",
        ),
        "_Huge Plant, Neutral_",
    ),
    (
        (
            "Monsters A–Z",
            "Awakened Plants",
            "Awakened Tree",
        ),
        "**AC** 13 **Initiative** −2 (8) <br>\n**HP** 59 (7d12 + 14) <br>\n**Speed** 20 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Awakened Plants",
            "Awakened Tree",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>19</td>\n      <td>+4</td>\n      <td>+4</td>\n      <td><strong>DEX</strong></td>\n      <td>6</td>\n      <td>−2</td>\n      <td>−2</td>\n      <td><strong>CON</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>WIS</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CHA</strong></td>\n      <td>7</td>\n      <td>−2</td>\n      <td>−2</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Awakened Plants",
            "Awakened Tree",
        ),
        "**Vulnerabilities** Fire<br>\n**Resistances** Bludgeoning, Piercing<br>\n**Senses** Passive Perception 10<br>\n**Languages** Common plus one other language<br>\n**CR** 2 (XP 450; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Awakened Plants",
            "Awakened Tree",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Awakened Plants",
            "Awakened Tree",
            "Actions",
        ),
        "**_Slam._** _Melee Attack Roll:_ +6, reach 10 ft. _Hit:_ 14 (3d6 + 4) Bludgeoning damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Axe Beak",
        ),
        "## Axe Beak",
    ),
    (
        (
            "Monsters A–Z",
            "Axe Beak",
            "Axe Beak",
        ),
        "### Axe Beak",
    ),
    (
        (
            "Monsters A–Z",
            "Axe Beak",
            "Axe Beak",
        ),
        "_Large Monstrosity, Unaligned_",
    ),
    (
        (
            "Monsters A–Z",
            "Axe Beak",
            "Axe Beak",
        ),
        "**AC** 11 **Initiative** +1 (11) <br>\n**HP** 19 (3d10 + 3) <br>\n**Speed** 50 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Axe Beak",
            "Axe Beak",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>DEX</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CON</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>2</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>WIS</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CHA</strong></td>\n      <td>5</td>\n      <td>−3</td>\n      <td>−3</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Axe Beak",
            "Axe Beak",
        ),
        "**Senses** Passive Perception 10<br>\n**Languages** None<br>\n**CR** 1/4 (XP 50; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Axe Beak",
            "Axe Beak",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Axe Beak",
            "Axe Beak",
            "Actions",
        ),
        "**_Beak._** _Melee Attack Roll:_ +4, reach 5 ft. _Hit:_ 6 (1d8 + 2) Slashing damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Azer",
        ),
        "## Azer",
    ),
    (
        (
            "Monsters A–Z",
            "Azer",
            "Azer Sentinel",
        ),
        "### Azer Sentinel",
    ),
    (
        (
            "Monsters A–Z",
            "Azer",
            "Azer Sentinel",
        ),
        "_Medium Elemental, Lawful Neutral_",
    ),
    (
        (
            "Monsters A–Z",
            "Azer",
            "Azer Sentinel",
        ),
        "**AC** 17 **Initiative** +1 (11) <br>\n**HP** 39 (6d8 + 12) <br>\n**Speed** 30 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Azer",
            "Azer Sentinel",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>17</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>DEX</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CON</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+4</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>WIS</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CHA</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Azer",
            "Azer Sentinel",
        ),
        "**Immunities** Fire, Poison; Poisoned<br>\n**Senses** Passive Perception 11<br>\n**Languages** Primordial (Ignan)<br>\n**CR** 2 (XP 450; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Azer",
            "Azer Sentinel",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Azer",
            "Azer Sentinel",
            "Traits",
        ),
        "**_Fire Aura._** At the end of each of the azer's turns, each creature of the azer's choice in a 5-foot Emanation originating from the azer takes 5 (1d10) Fire damage unless the azer has the Incapacitated condition.",
    ),
    (
        (
            "Monsters A–Z",
            "Azer",
            "Azer Sentinel",
            "Traits",
        ),
        "**_Illumination._** The azer sheds Bright Light in a 10-foot radius and Dim Light for an additional 10 feet.",
    ),
    (
        (
            "Monsters A–Z",
            "Azer",
            "Azer Sentinel",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Azer",
            "Azer Sentinel",
            "Actions",
        ),
        "**_Burning Hammer._** _Melee Attack Roll:_ +5, reach 5 ft. _Hit:_ 8 (1d10 + 3) Bludgeoning damage plus 3 (1d6) Fire damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Balor",
        ),
        "## Balor",
    ),
    (
        (
            "Monsters A–Z",
            "Balor",
            "Balor",
        ),
        "### Balor",
    ),
    (
        (
            "Monsters A–Z",
            "Balor",
            "Balor",
        ),
        "_Huge Fiend (Demon), Chaotic Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Balor",
            "Balor",
        ),
        "**AC** 19 **Initiative** +14 (24) <br>\n**HP** 287 (23d12 + 138) <br>\n**Speed** 40 ft., Fly 80 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Balor",
            "Balor",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>26</td>\n      <td>+8</td>\n      <td>+8</td>\n      <td><strong>DEX</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CON</strong></td>\n      <td>22</td>\n      <td>+6</td>\n      <td>+12</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>20</td>\n      <td>+5</td>\n      <td>+5</td>\n      <td><strong>WIS</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+9</td>\n      <td><strong>CHA</strong></td>\n      <td>22</td>\n      <td>+6</td>\n      <td>+6</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Balor",
            "Balor",
        ),
        "**Skills** Perception +9<br>\n**Resistances** Cold, Lightning<br>\n**Immunities** Fire, Poison; Charmed, Frightened, Poisoned<br>\n**Senses** Truesight 120 ft.; Passive Perception 19<br>\n**Languages** Abyssal; telepathy 120 ft.<br>\n**CR** 19 (XP 22,000; PB +6)",
    ),
    (
        (
            "Monsters A–Z",
            "Balor",
            "Balor",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Balor",
            "Balor",
            "Traits",
        ),
        "**_Death Throes._** The balor explodes when it dies. _Dexterity Saving Throw:_ DC 20, each creature in a 30-foot Emanation originating from the balor. _Failure:_ 31 (9d6) Fire damage plus 31 (9d6) Force damage. _Success:_ Half damage. _Failure or Success:_ If the balor dies outside the Abyss, it gains a new body instantly, reviving with all its Hit Points somewhere in the Abyss.",
    ),
    (
        (
            "Monsters A–Z",
            "Balor",
            "Balor",
            "Traits",
        ),
        "**_Fire Aura._** At the end of each of the balor's turns, each creature in a 5-foot Emanation originating from the balor takes 13 (3d8) Fire damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Balor",
            "Balor",
            "Traits",
        ),
        "**_Legendary Resistance (3/Day)._** If the balor fails a saving throw, it can choose to succeed instead.",
    ),
    (
        (
            "Monsters A–Z",
            "Balor",
            "Balor",
            "Traits",
        ),
        "**_Magic Resistance._** The balor has Advantage on saving throws against spells and other magical effects.",
    ),
    (
        (
            "Monsters A–Z",
            "Balor",
            "Balor",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Balor",
            "Balor",
            "Actions",
        ),
        "**_Multiattack._** The balor makes one Flame Whip attack and one Lightning Blade attack.",
    ),
    (
        (
            "Monsters A–Z",
            "Balor",
            "Balor",
            "Actions",
        ),
        "**_Flame Whip._** _Melee Attack Roll:_ +14, reach 30 ft. _Hit:_ 18 (3d6 + 8) Force damage plus 17 (5d6) Fire damage. If the target is a Huge or smaller creature, the balor pulls the target up to 25 feet straight toward itself, and the target has the Prone condition.",
    ),
    (
        (
            "Monsters A–Z",
            "Balor",
            "Balor",
            "Actions",
        ),
        "**_Lightning Blade._** _Melee Attack Roll:_ +14, reach 10 ft. _Hit:_ 21 (3d8 + 8) Force damage plus 22 (4d10) Lightning damage, and the target can't take Reactions until the start of the balor's next turn.",
    ),
    (
        (
            "Monsters A–Z",
            "Balor",
            "Balor",
            "Bonus Actions",
        ),
        "#### Bonus Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Balor",
            "Balor",
            "Bonus Actions",
        ),
        "**_Teleport._** The balor teleports itself or a willing demon within 10 feet of itself up to 60 feet to an unoccupied space the balor can see.",
    ),
    (
        (
            "Monsters A–Z",
            "Bandits",
        ),
        "## Bandits",
    ),
    (
        (
            "Monsters A–Z",
            "Bandits",
            "Bandit",
        ),
        "### Bandit",
    ),
    (
        (
            "Monsters A–Z",
            "Bandits",
            "Bandit",
        ),
        "_Medium or Small Humanoid, Neutral_",
    ),
    (
        (
            "Monsters A–Z",
            "Bandits",
            "Bandit",
        ),
        "**AC** 12 **Initiative** +1 (11) <br>\n**HP** 11 (2d8 + 2) <br>\n**Speed** 30 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Bandits",
            "Bandit",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>DEX</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CON</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>WIS</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CHA</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Bandits",
            "Bandit",
        ),
        "**Gear** Leather Armor, Light Crossbow, Scimitar<br>\n**Senses** Passive Perception 10<br>\n**Languages** Common, Thieves' Cant<br>\n**CR** 1/8 (XP 25; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Bandits",
            "Bandit",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Bandits",
            "Bandit",
            "Actions",
        ),
        "**_Scimitar._** _Melee Attack Roll:_ +3, reach 5 ft. _Hit:_ 4 (1d6 + 1) Slashing damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Bandits",
            "Bandit",
            "Actions",
        ),
        "**_Light Crossbow._** _Ranged Attack Roll:_ +3, range 80/320 ft. _Hit:_ 5 (1d8 + 1) Piercing damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Bandits",
            "Bandit Captain",
        ),
        "### Bandit Captain",
    ),
    (
        (
            "Monsters A–Z",
            "Bandits",
            "Bandit Captain",
        ),
        "_Medium or Small Humanoid, Neutral_",
    ),
    (
        (
            "Monsters A–Z",
            "Bandits",
            "Bandit Captain",
        ),
        "**AC** 15 **Initiative** +3 (13) <br>\n**HP** 52 (8d8 + 16) <br>\n**Speed** 30 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Bandits",
            "Bandit Captain",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+4</td>\n      <td><strong>DEX</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+5</td>\n      <td><strong>CON</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>WIS</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+2</td>\n      <td><strong>CHA</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Bandits",
            "Bandit Captain",
        ),
        "**Skills** Athletics +4, Deception +4<br>\n**Gear** Pistol, Scimitar, Studded Leather Armor<br>\n**Senses** Passive Perception 10<br>\n**Languages** Common, Thieves' Cant<br>\n**CR** 2 (XP 450; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Bandits",
            "Bandit Captain",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Bandits",
            "Bandit Captain",
            "Actions",
        ),
        "**_Multiattack._** The bandit makes two attacks, using Scimitar and Pistol in any combination.",
    ),
    (
        (
            "Monsters A–Z",
            "Bandits",
            "Bandit Captain",
            "Actions",
        ),
        "**_Scimitar._** _Melee Attack Roll:_ +5, reach 5 ft. _Hit:_ 6 (1d6 + 3) Slashing damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Bandits",
            "Bandit Captain",
            "Actions",
        ),
        "**_Pistol._** _Ranged Attack Roll:_ +5, range 30/90 ft. _Hit:_ 8 (1d10 + 3) Piercing damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Bandits",
            "Bandit Captain",
            "Reactions",
        ),
        "#### Reactions",
    ),
    (
        (
            "Monsters A–Z",
            "Bandits",
            "Bandit Captain",
            "Reactions",
        ),
        "**_Parry._** _Trigger:_ The bandit is hit by a melee attack roll while holding a weapon. _Response:_ The bandit adds 2 to its AC against that attack, possibly causing it to miss.",
    ),
    (
        (
            "Monsters A–Z",
            "Barbed Devil",
        ),
        "## Barbed Devil",
    ),
    (
        (
            "Monsters A–Z",
            "Barbed Devil",
            "Barbed Devil",
        ),
        "### Barbed Devil",
    ),
    (
        (
            "Monsters A–Z",
            "Barbed Devil",
            "Barbed Devil",
        ),
        "_Medium Fiend (Devil), Lawful Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Barbed Devil",
            "Barbed Devil",
        ),
        "**AC** 15 **Initiative** +3 (13) <br>\n**HP** 110 (13d8 + 52) <br>\n**Speed** 30 ft., Climb 30 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Barbed Devil",
            "Barbed Devil",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+6</td>\n      <td><strong>DEX</strong></td>\n      <td>17</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>CON</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+7</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>WIS</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+5</td>\n      <td><strong>CHA</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+5</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Barbed Devil",
            "Barbed Devil",
        ),
        "**Skills** Deception +5, Insight +5, Perception +8<br>\n**Resistances** Cold<br>\n**Immunities** Fire, Poison; Poisoned<br>\n**Senses** Darkvision 120 ft. (unimpeded by magical Darkness); Passive Perception 18<br>\n**Languages** Infernal; telepathy 120 ft.<br>\n**CR** 5 (XP 1,800; PB +3)",
    ),
    (
        (
            "Monsters A–Z",
            "Barbed Devil",
            "Barbed Devil",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Barbed Devil",
            "Barbed Devil",
            "Traits",
        ),
        "**_Barbed Hide._** At the start of each of its turns, the devil deals 5 (1d10) Piercing damage to any creature it is grappling or any creature grappling it.",
    ),
    (
        (
            "Monsters A–Z",
            "Barbed Devil",
            "Barbed Devil",
            "Traits",
        ),
        "**_Diabolical Restoration._** If the devil dies outside the Nine Hells, its body disappears in sulfurous smoke, and it gains a new body instantly, reviving with all its Hit Points somewhere in the Nine Hells.",
    ),
    (
        (
            "Monsters A–Z",
            "Barbed Devil",
            "Barbed Devil",
            "Traits",
        ),
        "**_Magic Resistance._** The devil has Advantage on saving throws against spells and other magical effects.",
    ),
    (
        (
            "Monsters A–Z",
            "Barbed Devil",
            "Barbed Devil",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Barbed Devil",
            "Barbed Devil",
            "Actions",
        ),
        "**_Multiattack._** The devil makes one Claws attack and one Tail attack, or it makes two Hurl Flame attacks.",
    ),
    (
        (
            "Monsters A–Z",
            "Barbed Devil",
            "Barbed Devil",
            "Actions",
        ),
        "**_Claws._** _Melee Attack Roll:_ +6, reach 5 ft. _Hit:_ 10 (2d6 + 3) Piercing damage. If the target is a Large or smaller creature, it has the Grappled condition (escape DC 13) from both claws.",
    ),
    (
        (
            "Monsters A–Z",
            "Barbed Devil",
            "Barbed Devil",
            "Actions",
        ),
        "**_Tail._** _Melee Attack Roll:_ +6, reach 10 ft. _Hit:_ 14 (2d10 + 3) Slashing damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Barbed Devil",
            "Barbed Devil",
            "Actions",
        ),
        "**_Hurl Flame._** _Ranged Attack Roll:_ +5, range 150 ft. _Hit:_ 17 (5d6) Fire damage. If the target is a flammable object that isn't being worn or carried, it starts burning.",
    ),
    (
        (
            "Monsters A–Z",
            "Basilisk",
        ),
        "## Basilisk",
    ),
    (
        (
            "Monsters A–Z",
            "Basilisk",
            "Basilisk",
        ),
        "### Basilisk",
    ),
    (
        (
            "Monsters A–Z",
            "Basilisk",
            "Basilisk",
        ),
        "_Medium Monstrosity, Unaligned_",
    ),
    (
        (
            "Monsters A–Z",
            "Basilisk",
            "Basilisk",
        ),
        "**AC** 15 **Initiative** −1 (9) <br>\n**HP** 52 (8d8 + 16) <br>\n**Speed** 20 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Basilisk",
            "Basilisk",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>DEX</strong></td>\n      <td>8</td>\n      <td>−1</td>\n      <td>−1</td>\n      <td><strong>CON</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>2</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>WIS</strong></td>\n      <td>8</td>\n      <td>−1</td>\n      <td>−1</td>\n      <td><strong>CHA</strong></td>\n      <td>7</td>\n      <td>−2</td>\n      <td>−2</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Basilisk",
            "Basilisk",
        ),
        "**Senses** Darkvision 60 ft.; Passive Perception 9<br>\n**Languages** None<br>\n**CR** 3 (XP 700; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Basilisk",
            "Basilisk",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Basilisk",
            "Basilisk",
            "Actions",
        ),
        "**_Bite._** _Melee Attack Roll:_ +5, reach 5 ft. _Hit:_ 10 (2d6 + 3) Piercing damage plus 7 (2d6) Poison damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Basilisk",
            "Basilisk",
            "Bonus Actions",
        ),
        "#### Bonus Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Basilisk",
            "Basilisk",
            "Bonus Actions",
        ),
        "**_Petrifying Gaze (Recharge 4–6)._** _Constitution Saving Throw:_ DC 12, each creature in a 30-foot Cone. If the basilisk sees its reflection in the Cone, the basilisk must make this save. _First Failure:_ The target has the Restrained condition and repeats the save at the end of its next turn if it is still Restrained, ending the effect on itself on a success. _Second Failure:_ The target has the Petrified condition instead of the Restrained condition.",
    ),
    (
        (
            "Monsters A–Z",
            "Bearded Devil",
        ),
        "## Bearded Devil",
    ),
    (
        (
            "Monsters A–Z",
            "Bearded Devil",
            "Bearded Devil",
        ),
        "### Bearded Devil",
    ),
    (
        (
            "Monsters A–Z",
            "Bearded Devil",
            "Bearded Devil",
        ),
        "_Medium Fiend (Devil), Lawful Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Bearded Devil",
            "Bearded Devil",
        ),
        "**AC** 13 **Initiative** +2 (12) <br>\n**HP** 58 (9d8 + 18) <br>\n**Speed** 30 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Bearded Devil",
            "Bearded Devil",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+5</td>\n      <td><strong>DEX</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CON</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+4</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>9</td>\n      <td>−1</td>\n      <td>−1</td>\n      <td><strong>WIS</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CHA</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+4</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Bearded Devil",
            "Bearded Devil",
        ),
        "**Resistances** Cold<br>\n**Immunities** Fire, Poison; Frightened, Poisoned<br>\n**Senses** Darkvision 120 ft. (unimpeded by magical Darkness); Passive Perception 10<br>\n**Languages** Infernal; telepathy 120 ft.<br>\n**CR** 3 (XP 700; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Bearded Devil",
            "Bearded Devil",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Bearded Devil",
            "Bearded Devil",
            "Traits",
        ),
        "**_Magic Resistance._** The devil has Advantage on saving throws against spells and other magical effects.",
    ),
    (
        (
            "Monsters A–Z",
            "Bearded Devil",
            "Bearded Devil",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Bearded Devil",
            "Bearded Devil",
            "Actions",
        ),
        "**_Multiattack._** The devil makes one Beard attack and one Infernal Glaive attack.",
    ),
    (
        (
            "Monsters A–Z",
            "Bearded Devil",
            "Bearded Devil",
            "Actions",
        ),
        "**_Beard._** _Melee Attack Roll:_ +5, reach 5 ft. _Hit:_ 7 (1d8 + 3) Piercing damage, and the target has the Poisoned condition until the start of the devil's next turn. Until this poison ends, the target can't regain Hit Points.",
    ),
    (
        (
            "Monsters A–Z",
            "Bearded Devil",
            "Bearded Devil",
            "Actions",
        ),
        "**_Infernal Glaive._** _Melee Attack Roll:_ +5, reach 10 ft. _Hit:_ 8 (1d10 + 3) Slashing damage. If the target is a creature and doesn't already have an infernal wound, it is subjected to the following effect. _Constitution Saving Throw:_ DC 12. _Failure:_ The target receives an infernal wound. While wounded, the target loses 5 (1d10) Hit Points at the start of each of its turns. The wound closes after 1 minute, after a spell restores Hit Points to the target, or after the target or a creature within 5 feet of it takes an action to stanch the wound, doing so by succeeding on a DC 12 Wisdom (Medicine) check.",
    ),
    (
        (
            "Monsters A–Z",
            "Behir",
        ),
        "## Behir",
    ),
    (
        (
            "Monsters A–Z",
            "Behir",
            "Behir",
        ),
        "### Behir",
    ),
    (
        (
            "Monsters A–Z",
            "Behir",
            "Behir",
        ),
        "_Huge Monstrosity, Neutral Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Behir",
            "Behir",
        ),
        "**AC** 17 **Initiative** +3 (13) <br>\n**HP** 168 (16d12 + 64) <br>\n**Speed** 50 ft., Climb 50 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Behir",
            "Behir",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>23</td>\n      <td>+6</td>\n      <td>+6</td>\n      <td><strong>DEX</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>CON</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+4</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>7</td>\n      <td>−2</td>\n      <td>−2</td>\n      <td><strong>WIS</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CHA</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Behir",
            "Behir",
        ),
        "**Skills** Perception +6, Stealth +7<br>\n**Immunities** Lightning<br>\n**Senses** Darkvision 90 ft.; Passive Perception 16<br>\n**Languages** Draconic<br>\n**CR** 11 (XP 7,200; PB +4)",
    ),
    (
        (
            "Monsters A–Z",
            "Behir",
            "Behir",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Behir",
            "Behir",
            "Actions",
        ),
        "**_Multiattack._** The behir makes one Bite attack and uses Constrict.",
    ),
    (
        (
            "Monsters A–Z",
            "Behir",
            "Behir",
            "Actions",
        ),
        "**_Bite._** _Melee Attack Roll:_ +10, reach 10 ft. _Hit:_ 19 (2d12 + 6) Piercing damage plus 11 (2d10) Lightning damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Behir",
            "Behir",
            "Actions",
        ),
        "**_Constrict._** _Strength Saving Throw:_ DC 18, one Large or smaller creature the behir can see within 5 feet. _Failure:_ 28 (5d8 + 6) Bludgeoning damage. The target has the Grappled condition (escape DC 16), and it has the Restrained condition until the grapple ends.",
    ),
    (
        (
            "Monsters A–Z",
            "Behir",
            "Behir",
            "Actions",
        ),
        "**_Lightning Breath (Recharge 5–6)._** _Dexterity Saving Throw:_ DC 16, each creature in a 90-foot-long, 5-foot-wide Line. _Failure:_ 66 (12d10) Lightning damage. _Success:_ Half damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Behir",
            "Behir",
            "Bonus Actions",
        ),
        "#### Bonus Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Behir",
            "Behir",
            "Bonus Actions",
        ),
        "**_Swallow._** _Dexterity Saving Throw:_ DC 18, one Large or smaller creature Grappled by the behir (the behir can have only one creature swallowed at a time). _Failure:_ The behir swallows the target, which is no longer Grappled. While swallowed, a creature has the Blinded and Restrained conditions, has Total Cover against attacks and other effects outside the behir, and takes 21 (6d6) Acid damage at the start of each of the behir's turns. <br>\n&emsp;If the behir takes 30 damage or more on a single turn from the swallowed creature, the behir must succeed on a DC 14 Constitution saving throw at the end of that turn or regurgitate the creature, which falls in a space within 10 feet of the behir and has the Prone condition. If the behir dies, a swallowed creature is no longer Restrained and can escape from the corpse by using 15 feet of movement, exiting Prone.",
    ),
    (
        (
            "Monsters A–Z",
            "Berserker",
        ),
        "## Berserker",
    ),
    (
        (
            "Monsters A–Z",
            "Berserker",
            "Berserker",
        ),
        "### Berserker",
    ),
    (
        (
            "Monsters A–Z",
            "Berserker",
            "Berserker",
        ),
        "_Medium or Small Humanoid, Neutral_",
    ),
    (
        (
            "Monsters A–Z",
            "Berserker",
            "Berserker",
        ),
        "**AC** 13 **Initiative** +1 (11) <br>\n**HP** 67 (9d8 + 27) <br>\n**Speed** 30 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Berserker",
            "Berserker",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>DEX</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CON</strong></td>\n      <td>17</td>\n      <td>+3</td>\n      <td>+3</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>9</td>\n      <td>−1</td>\n      <td>−1</td>\n      <td><strong>WIS</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CHA</strong></td>\n      <td>9</td>\n      <td>−1</td>\n      <td>−1</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Berserker",
            "Berserker",
        ),
        "**Gear** Greataxe, Hide Armor<br>\n**Senses** Passive Perception 10<br>\n**Languages** Common<br>\n**CR** 2 (XP 450; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Berserker",
            "Berserker",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Berserker",
            "Berserker",
            "Traits",
        ),
        "**_Bloodied Frenzy._** While Bloodied, the berserker has Advantage on attack rolls and saving throws.",
    ),
    (
        (
            "Monsters A–Z",
            "Berserker",
            "Berserker",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Berserker",
            "Berserker",
            "Actions",
        ),
        "**_Greataxe._** _Melee Attack Roll:_ +5, reach 5 ft. _Hit:_ 9 (1d12 + 3) Slashing damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Black Dragons",
        ),
        "## Black Dragons",
    ),
    (
        (
            "Monsters A–Z",
            "Black Dragons",
            "Black Dragon Wyrmling",
        ),
        "### Black Dragon Wyrmling",
    ),
    (
        (
            "Monsters A–Z",
            "Black Dragons",
            "Black Dragon Wyrmling",
        ),
        "_Medium Dragon (Chromatic), Chaotic Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Black Dragons",
            "Black Dragon Wyrmling",
        ),
        "**AC** 17 **Initiative** +4 (14) <br>\n**HP** 33 (6d8 + 6) <br>\n**Speed** 30 ft., Fly 60 ft., Swim 30 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Black Dragons",
            "Black Dragon Wyrmling",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>DEX</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+4</td>\n      <td><strong>CON</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>WIS</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+2</td>\n      <td><strong>CHA</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Black Dragons",
            "Black Dragon Wyrmling",
        ),
        "**Skills** Perception +4, Stealth +4<br>\n**Immunities** Acid<br>\n**Senses** Blindsight 10 ft., Darkvision 60 ft.; Passive Perception 14<br>\n**Languages** Draconic<br>\n**CR** 2 (XP 450; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Black Dragons",
            "Black Dragon Wyrmling",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Black Dragons",
            "Black Dragon Wyrmling",
            "Traits",
        ),
        "**_Amphibious._** The dragon can breathe air and water.",
    ),
    (
        (
            "Monsters A–Z",
            "Black Dragons",
            "Black Dragon Wyrmling",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Black Dragons",
            "Black Dragon Wyrmling",
            "Actions",
        ),
        "**_Multiattack._** The dragon makes two Rend attacks.",
    ),
    (
        (
            "Monsters A–Z",
            "Black Dragons",
            "Black Dragon Wyrmling",
            "Actions",
        ),
        "**_Rend._** _Melee Attack Roll:_ +4, reach 5 ft. _Hit:_ 5 (1d6 + 2) Slashing damage plus 2 (1d4) Acid damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Black Dragons",
            "Black Dragon Wyrmling",
            "Actions",
        ),
        "**_Acid Breath (Recharge 5–6)._** _Dexterity Saving Throw:_ DC 11, each creature in a 15-foot-long, 5-foot-wide Line. _Failure:_ 22 (5d8) Acid damage. _Success:_ Half damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Black Dragons",
            "Young Black Dragon",
        ),
        "### Young Black Dragon",
    ),
    (
        (
            "Monsters A–Z",
            "Black Dragons",
            "Young Black Dragon",
        ),
        "_Large Dragon (Chromatic), Chaotic Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Black Dragons",
            "Young Black Dragon",
        ),
        "**AC** 18 **Initiative** +5 (15) <br>\n**HP** 127 (15d10 + 45) <br>\n**Speed** 40 ft., Fly 80 ft., Swim 40 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Black Dragons",
            "Young Black Dragon",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>19</td>\n      <td>+4</td>\n      <td>+4</td>\n      <td><strong>DEX</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+5</td>\n      <td><strong>CON</strong></td>\n      <td>17</td>\n      <td>+3</td>\n      <td>+3</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>WIS</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+3</td>\n      <td><strong>CHA</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Black Dragons",
            "Young Black Dragon",
        ),
        "**Skills** Perception +6, Stealth +5<br>\n**Immunities** Acid<br>\n**Senses** Blindsight 30 ft., Darkvision 120 ft.; Passive Perception 16<br>\n**Languages** Common, Draconic<br>\n**CR** 7 (XP 2,900; PB +3)",
    ),
    (
        (
            "Monsters A–Z",
            "Black Dragons",
            "Young Black Dragon",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Black Dragons",
            "Young Black Dragon",
            "Traits",
        ),
        "**_Amphibious._** The dragon can breathe air and water.",
    ),
    (
        (
            "Monsters A–Z",
            "Black Dragons",
            "Young Black Dragon",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Black Dragons",
            "Young Black Dragon",
            "Actions",
        ),
        "**_Multiattack._** The dragon makes three Rend attacks.",
    ),
    (
        (
            "Monsters A–Z",
            "Black Dragons",
            "Young Black Dragon",
            "Actions",
        ),
        "**_Rend._** _Melee Attack Roll:_ +7, reach 10 ft. _Hit:_ 9 (2d4 + 4) Slashing damage plus 3 (1d6) Acid damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Black Dragons",
            "Young Black Dragon",
            "Actions",
        ),
        "**_Acid Breath (Recharge 5–6)._** _Dexterity Saving Throw:_ DC 14, each creature in a 30-foot-long, 5-foot-wide Line. _Failure:_ 49 (14d6) Acid damage. _Success:_ Half damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Black Dragons",
            "Adult Black Dragon",
        ),
        "### Adult Black Dragon",
    ),
    (
        (
            "Monsters A–Z",
            "Black Dragons",
            "Adult Black Dragon",
        ),
        "_Huge Dragon (Chromatic), Chaotic Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Black Dragons",
            "Adult Black Dragon",
        ),
        "**AC** 19 **Initiative** +12 (22) <br>\n**HP** 195 (17d12 + 85) <br>\n**Speed** 40 ft., Fly 80 ft., Swim 40 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Black Dragons",
            "Adult Black Dragon",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>23</td>\n      <td>+6</td>\n      <td>+6</td>\n      <td><strong>DEX</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+7</td>\n      <td><strong>CON</strong></td>\n      <td>21</td>\n      <td>+5</td>\n      <td>+5</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>WIS</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+6</td>\n      <td><strong>CHA</strong></td>\n      <td>19</td>\n      <td>+4</td>\n      <td>+4</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Black Dragons",
            "Adult Black Dragon",
        ),
        "**Skills** Perception +11, Stealth +7<br>\n**Immunities** Acid<br>\n**Senses** Blindsight 60 ft., Darkvision 120 ft.; Passive Perception 21<br>\n**Languages** Common, Draconic<br>\n**CR** 14 (XP 11,500, or 13,000 in lair; PB +5)",
    ),
    (
        (
            "Monsters A–Z",
            "Black Dragons",
            "Adult Black Dragon",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Black Dragons",
            "Adult Black Dragon",
            "Traits",
        ),
        "**_Amphibious._** The dragon can breathe air and water.",
    ),
    (
        (
            "Monsters A–Z",
            "Black Dragons",
            "Adult Black Dragon",
            "Traits",
        ),
        "**_Legendary Resistance (3/Day, or 4/Day in Lair)._** If the dragon fails a saving throw, it can choose to succeed instead.",
    ),
    (
        (
            "Monsters A–Z",
            "Black Dragons",
            "Adult Black Dragon",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Black Dragons",
            "Adult Black Dragon",
            "Actions",
        ),
        "**_Multiattack._** The dragon makes three Rend attacks. It can replace one attack with a use of Spellcasting to cast _Acid Arrow_ (level 3 version).",
    ),
    (
        (
            "Monsters A–Z",
            "Black Dragons",
            "Adult Black Dragon",
            "Actions",
        ),
        "**_Rend._** _Melee Attack Roll:_ +11, reach 10 ft. _Hit:_ 13 (2d6 + 6) Slashing damage plus 4 (1d8) Acid damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Black Dragons",
            "Adult Black Dragon",
            "Actions",
        ),
        "**_Acid Breath (Recharge 5–6)._** _Dexterity Saving Throw:_ DC 18, each creature in a 60-foot-long, 5-foot-wide Line. _Failure:_ 54 (12d8) Acid damage. _Success:_ Half damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Black Dragons",
            "Adult Black Dragon",
            "Actions",
        ),
        "**_Spellcasting._** The dragon casts one of the following spells, requiring no Material components and using Charisma as the spellcasting ability (spell save DC 17, +9 to hit with spell attacks): <br>\n&emsp;**At Will:** _Acid Arrow_ (level 3 version), _Detect Magic_, _Fear_ <br>\n&emsp;**1/Day Each:** _Speak with Dead_, _Vitriolic Sphere_",
    ),
    (
        (
            "Monsters A–Z",
            "Black Dragons",
            "Adult Black Dragon",
            "Legendary Actions",
        ),
        "#### Legendary Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Black Dragons",
            "Adult Black Dragon",
            "Legendary Actions",
        ),
        "_Legendary Action Uses: 3 (4 in Lair). Immediately after another creature's turn, the dragon can expend a use to take one of the following actions. The dragon regains all expended uses at the start of each of its turns._",
    ),
    (
        (
            "Monsters A–Z",
            "Black Dragons",
            "Adult Black Dragon",
            "Legendary Actions",
        ),
        "**_Cloud of Insects._** _Dexterity Saving Throw:_ DC 17, one creature the dragon can see within 120 feet. _Failure:_ 22 (4d10) Poison damage, and the target has Disadvantage on saving throws to maintain Concentration until the end of its next turn. _Failure or Success:_ The dragon can't take this action again until the start of its next turn.",
    ),
    (
        (
            "Monsters A–Z",
            "Black Dragons",
            "Adult Black Dragon",
            "Legendary Actions",
        ),
        "**_Frightful Presence._** The dragon uses Spellcasting to cast _Fear_. The dragon can't take this action again until the start of its next turn.",
    ),
    (
        (
            "Monsters A–Z",
            "Black Dragons",
            "Adult Black Dragon",
            "Legendary Actions",
        ),
        "**_Pounce._** The dragon moves up to half its Speed, and it makes one Rend attack.",
    ),
    (
        (
            "Monsters A–Z",
            "Black Dragons",
            "Ancient Black Dragon",
        ),
        "### Ancient Black Dragon",
    ),
    (
        (
            "Monsters A–Z",
            "Black Dragons",
            "Ancient Black Dragon",
        ),
        "_Gargantuan Dragon (Chromatic), Chaotic Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Black Dragons",
            "Ancient Black Dragon",
        ),
        "**AC** 22 **Initiative** +16 (26) <br>\n**HP** 367 (21d20 + 147) <br>\n**Speed** 40 ft., Fly 80 ft., Swim 40 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Black Dragons",
            "Ancient Black Dragon",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>27</td>\n      <td>+8</td>\n      <td>+8</td>\n      <td><strong>DEX</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+9</td>\n      <td><strong>CON</strong></td>\n      <td>25</td>\n      <td>+7</td>\n      <td>+7</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>WIS</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+9</td>\n      <td><strong>CHA</strong></td>\n      <td>22</td>\n      <td>+6</td>\n      <td>+6</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Black Dragons",
            "Ancient Black Dragon",
        ),
        "**Skills** Perception +16, Stealth +9<br>\n**Immunities** Acid<br>\n**Senses** Blindsight 60 ft., Darkvision 120 ft.; Passive Perception 26<br>\n**Languages** Common, Draconic<br>\n**CR** 21 (XP 33,000, or 41,000 in lair; PB +7)",
    ),
    (
        (
            "Monsters A–Z",
            "Black Dragons",
            "Ancient Black Dragon",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Black Dragons",
            "Ancient Black Dragon",
            "Traits",
        ),
        "**_Amphibious._** The dragon can breathe air and water.",
    ),
    (
        (
            "Monsters A–Z",
            "Black Dragons",
            "Ancient Black Dragon",
            "Traits",
        ),
        "**_Legendary Resistance (4/Day, or 5/Day in Lair)._** If the dragon fails a saving throw, it can choose to succeed instead.",
    ),
    (
        (
            "Monsters A–Z",
            "Black Dragons",
            "Ancient Black Dragon",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Black Dragons",
            "Ancient Black Dragon",
            "Actions",
        ),
        "**_Multiattack._** The dragon makes three Rend attacks. It can replace one attack with a use of Spellcasting to cast _Acid Arrow_ (level 4 version).",
    ),
    (
        (
            "Monsters A–Z",
            "Black Dragons",
            "Ancient Black Dragon",
            "Actions",
        ),
        "**_Rend._** _Melee Attack Roll:_ +15, reach 15 ft. _Hit:_ 17 (2d8 + 8) Slashing damage plus 9 (2d8) Acid damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Black Dragons",
            "Ancient Black Dragon",
            "Actions",
        ),
        "**_Acid Breath (Recharge 5–6)._** _Dexterity Saving Throw:_ DC 22, each creature in a 90-foot-long, 10-foot-wide Line. _Failure:_ 67 (15d8) Acid damage. _Success:_ Half damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Black Dragons",
            "Ancient Black Dragon",
            "Actions",
        ),
        "**_Spellcasting._** The dragon casts one of the following spells, requiring no Material components and using Charisma as the spellcasting ability (spell save DC 21, +13 to hit with spell attacks): <br>\n&emsp;**At Will:** _Acid Arrow_ (level 4 version), _Detect Magic_, _Fear_ <br>\n&emsp;**1/Day Each:** _Create Undead_, _Speak with Dead_, _Vitriolic Sphere_ (level 5 version)",
    ),
    (
        (
            "Monsters A–Z",
            "Black Dragons",
            "Ancient Black Dragon",
            "Legendary Actions",
        ),
        "#### Legendary Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Black Dragons",
            "Ancient Black Dragon",
            "Legendary Actions",
        ),
        "_Legendary Action Uses: 3 (4 in Lair). Immediately after another creature's turn, the dragon can expend a use to take one of the following actions. The dragon regains all expended uses at the start of each of its turns._",
    ),
    (
        (
            "Monsters A–Z",
            "Black Dragons",
            "Ancient Black Dragon",
            "Legendary Actions",
        ),
        "**_Cloud of Insects._** _Dexterity Saving Throw:_ DC 21, one creature the dragon can see within 120 feet. _Failure:_ 33 (6d10) Poison damage, and the target has Disadvantage on saving throws to maintain Concentration until the end of its next turn. _Failure or Success:_ The dragon can't take this action again until the start of its next turn.",
    ),
    (
        (
            "Monsters A–Z",
            "Black Dragons",
            "Ancient Black Dragon",
            "Legendary Actions",
        ),
        "**_Frightful Presence._** The dragon uses Spellcasting to cast _Fear_. The dragon can't take this action again until the start of its next turn.",
    ),
    (
        (
            "Monsters A–Z",
            "Black Dragons",
            "Ancient Black Dragon",
            "Legendary Actions",
        ),
        "**_Pounce._** The dragon moves up to half its Speed, and it makes one Rend attack.",
    ),
    (
        (
            "Monsters A–Z",
            "Black Pudding",
        ),
        "## Black Pudding",
    ),
    (
        (
            "Monsters A–Z",
            "Black Pudding",
            "Black Pudding",
        ),
        "### Black Pudding",
    ),
    (
        (
            "Monsters A–Z",
            "Black Pudding",
            "Black Pudding",
        ),
        "_Large Ooze, Unaligned_",
    ),
    (
        (
            "Monsters A–Z",
            "Black Pudding",
            "Black Pudding",
        ),
        "**AC** 7 **Initiative** −3 (7) <br>\n**HP** 68 (8d10 + 24) <br>\n**Speed** 20 ft., Climb 20 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Black Pudding",
            "Black Pudding",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>DEX</strong></td>\n      <td>5</td>\n      <td>−3</td>\n      <td>−3</td>\n      <td><strong>CON</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>1</td>\n      <td>−5</td>\n      <td>−5</td>\n      <td><strong>WIS</strong></td>\n      <td>6</td>\n      <td>−2</td>\n      <td>−2</td>\n      <td><strong>CHA</strong></td>\n      <td>1</td>\n      <td>−5</td>\n      <td>−5</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Black Pudding",
            "Black Pudding",
        ),
        "**Immunities** Acid, Cold, Lightning, Slashing; Charmed, Deafened, Exhaustion, Frightened, Grappled, Prone, Restrained<br>\n**Senses** Blindsight 60 ft.; Passive Perception 8<br>\n**Languages** None<br>\n**CR** 4 (XP 1,100; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Black Pudding",
            "Black Pudding",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Black Pudding",
            "Black Pudding",
            "Traits",
        ),
        "**_Amorphous._** The pudding can move through a space as narrow as 1 inch without expending extra movement to do so.",
    ),
    (
        (
            "Monsters A–Z",
            "Black Pudding",
            "Black Pudding",
            "Traits",
        ),
        "**_Corrosive Form._** A creature that hits the pudding with a melee attack roll takes 4 (1d8) Acid damage. Nonmagical ammunition is destroyed immediately after hitting the pudding and dealing any damage. Any nonmagical weapon takes a cumulative −1 penalty to attack rolls immediately after dealing damage to the pudding and coming into contact with it. The weapon is destroyed if the penalty reaches −5. The penalty can be removed by casting the _Mending_ spell on the weapon. <br>\n&emsp;In 1 minute, the pudding can eat through 2 feet of nonmagical wood or metal.",
    ),
    (
        (
            "Monsters A–Z",
            "Black Pudding",
            "Black Pudding",
            "Traits",
        ),
        "**_Spider Climb._** The pudding can climb difficult surfaces, including along ceilings, without needing to make an ability check.",
    ),
    (
        (
            "Monsters A–Z",
            "Black Pudding",
            "Black Pudding",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Black Pudding",
            "Black Pudding",
            "Actions",
        ),
        "**_Dissolving Pseudopod._** _Melee Attack Roll:_ +5, reach 10 ft. _Hit:_ 17 (4d6 + 3) Acid damage. Nonmagical armor worn by the target takes a −1 penalty to the AC it offers. The armor is destroyed if the penalty reduces its AC to 10. The penalty can be removed by casting the _Mending_ spell on the armor.",
    ),
    (
        (
            "Monsters A–Z",
            "Black Pudding",
            "Black Pudding",
            "Reactions",
        ),
        "#### Reactions",
    ),
    (
        (
            "Monsters A–Z",
            "Black Pudding",
            "Black Pudding",
            "Reactions",
        ),
        "**_Split._** _Trigger:_ While the pudding is Large or Medium and has 10+ Hit Points, it becomes Bloodied or is subjected to Lightning or Slashing damage. _Response:_ The pudding splits into two new **Black Puddings**. Each new pudding is one size smaller than the original pudding and acts on its Initiative. The original pudding's Hit Points are divided evenly between the new puddings (round down).",
    ),
    (
        (
            "Monsters A–Z",
            "Blink Dog",
        ),
        "## Blink Dog",
    ),
    (
        (
            "Monsters A–Z",
            "Blink Dog",
            "Blink Dog",
        ),
        "### Blink Dog",
    ),
    (
        (
            "Monsters A–Z",
            "Blink Dog",
            "Blink Dog",
        ),
        "_Medium Fey, Lawful Good_",
    ),
    (
        (
            "Monsters A–Z",
            "Blink Dog",
            "Blink Dog",
        ),
        "**AC** 13 **Initiative** +3 (13) <br>\n**HP** 22 (4d8 + 4) <br>\n**Speed** 40 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Blink Dog",
            "Blink Dog",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>DEX</strong></td>\n      <td>17</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>CON</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>WIS</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CHA</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Blink Dog",
            "Blink Dog",
        ),
        "**Skills** Perception +5, Stealth +5<br>\n**Senses** Darkvision 60 ft.; Passive Perception 15<br>\n**Languages** Blink Dog; understands Elvish and Sylvan but can't speak them<br>\n**CR** 1/4 (XP 50; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Blink Dog",
            "Blink Dog",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Blink Dog",
            "Blink Dog",
            "Actions",
        ),
        "**_Bite._** _Melee Attack Roll:_ +5, reach 5 ft. _Hit:_ 5 (1d4 + 3) Piercing damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Blink Dog",
            "Blink Dog",
            "Bonus Actions",
        ),
        "#### Bonus Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Blink Dog",
            "Blink Dog",
            "Bonus Actions",
        ),
        "**_Teleport (Recharge 4–6)._** The dog teleports up to 40 feet to an unoccupied space it can see.",
    ),
    (
        (
            "Monsters A–Z",
            "Blue Dragons",
        ),
        "## Blue Dragons",
    ),
    (
        (
            "Monsters A–Z",
            "Blue Dragons",
            "Blue Dragon Wyrmling",
        ),
        "### Blue Dragon Wyrmling",
    ),
    (
        (
            "Monsters A–Z",
            "Blue Dragons",
            "Blue Dragon Wyrmling",
        ),
        "_Medium Dragon (Chromatic), Lawful Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Blue Dragons",
            "Blue Dragon Wyrmling",
        ),
        "**AC** 17 **Initiative** +2 (12) <br>\n**HP** 65 (10d8 + 20) <br>\n**Speed** 30 ft., Burrow 15 ft., Fly 60 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Blue Dragons",
            "Blue Dragon Wyrmling",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>17</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>DEX</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+2</td>\n      <td><strong>CON</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>WIS</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+2</td>\n      <td><strong>CHA</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Blue Dragons",
            "Blue Dragon Wyrmling",
        ),
        "**Skills** Perception +4, Stealth +2<br>\n**Immunities** Lightning<br>\n**Senses** Blindsight 10 ft., Darkvision 60 ft.; Passive Perception 14<br>\n**Languages** Draconic<br>\n**CR** 3 (XP 700; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Blue Dragons",
            "Blue Dragon Wyrmling",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Blue Dragons",
            "Blue Dragon Wyrmling",
            "Actions",
        ),
        "**_Multiattack._** The dragon makes two Rend attacks.",
    ),
    (
        (
            "Monsters A–Z",
            "Blue Dragons",
            "Blue Dragon Wyrmling",
            "Actions",
        ),
        "**_Rend._** _Melee Attack Roll:_ +5, reach 5 ft. _Hit:_ 8 (1d10 + 3) Slashing damage plus 3 (1d6) Lightning damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Blue Dragons",
            "Blue Dragon Wyrmling",
            "Actions",
        ),
        "**_Lightning Breath (Recharge 5–6)._** _Dexterity Saving Throw:_ DC 12, each creature in a 30-foot-long, 5-foot-wide Line. _Failure:_ 21 (6d6) Lightning damage. _Success:_ Half damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Blue Dragons",
            "Young Blue Dragon",
        ),
        "### Young Blue Dragon",
    ),
    (
        (
            "Monsters A–Z",
            "Blue Dragons",
            "Young Blue Dragon",
        ),
        "_Large Dragon (Chromatic), Lawful Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Blue Dragons",
            "Young Blue Dragon",
        ),
        "**AC** 18 **Initiative** +4 (14) <br>\n**HP** 152 (16d10 + 64) <br>\n**Speed** 40 ft., Burrow 20 ft., Fly 80 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Blue Dragons",
            "Young Blue Dragon",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>21</td>\n      <td>+5</td>\n      <td>+5</td>\n      <td><strong>DEX</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+4</td>\n      <td><strong>CON</strong></td>\n      <td>19</td>\n      <td>+4</td>\n      <td>+4</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>WIS</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+5</td>\n      <td><strong>CHA</strong></td>\n      <td>17</td>\n      <td>+3</td>\n      <td>+3</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Blue Dragons",
            "Young Blue Dragon",
        ),
        "**Skills** Perception +9, Stealth +4<br>\n**Immunities** Lightning<br>\n**Senses** Blindsight 30 ft., Darkvision 120 ft.; Passive Perception 19<br>\n**Languages** Common, Draconic<br>\n**CR** 9 (XP 5,000; PB +4)",
    ),
    (
        (
            "Monsters A–Z",
            "Blue Dragons",
            "Young Blue Dragon",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Blue Dragons",
            "Young Blue Dragon",
            "Actions",
        ),
        "**_Multiattack._** The dragon makes three Rend attacks.",
    ),
    (
        (
            "Monsters A–Z",
            "Blue Dragons",
            "Young Blue Dragon",
            "Actions",
        ),
        "**_Rend._** _Melee Attack Roll:_ +9, reach 10 ft. _Hit:_ 12 (2d6 + 5) Slashing damage plus 5 (1d10) Lightning damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Blue Dragons",
            "Young Blue Dragon",
            "Actions",
        ),
        "**_Lightning Breath (Recharge 5–6)._** _Dexterity Saving Throw:_ DC 16, each creature in a 60-foot-long, 5-foot-wide Line. _Failure:_ 55 (10d10) Lightning damage. _Success:_ Half damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Blue Dragons",
            "Adult Blue Dragon",
        ),
        "### Adult Blue Dragon",
    ),
    (
        (
            "Monsters A–Z",
            "Blue Dragons",
            "Adult Blue Dragon",
        ),
        "_Huge Dragon (Chromatic), Lawful Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Blue Dragons",
            "Adult Blue Dragon",
        ),
        "**AC** 19 **Initiative** +10 (20) <br>\n**HP** 212 (17d12 + 102) <br>\n**Speed** 40 ft., Burrow 30 ft., Fly 80 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Blue Dragons",
            "Adult Blue Dragon",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>25</td>\n      <td>+7</td>\n      <td>+7</td>\n      <td><strong>DEX</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+5</td>\n      <td><strong>CON</strong></td>\n      <td>23</td>\n      <td>+6</td>\n      <td>+6</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>WIS</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+7</td>\n      <td><strong>CHA</strong></td>\n      <td>20</td>\n      <td>+5</td>\n      <td>+5</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Blue Dragons",
            "Adult Blue Dragon",
        ),
        "**Skills** Perception +12, Stealth +5<br>\n**Immunities** Lightning<br>\n**Senses** Blindsight 60 ft., Darkvision 120 ft.; Passive Perception 22<br>\n**Languages** Common, Draconic<br>\n**CR** 16 (XP 15,000, or 18,000 in lair; PB +5)",
    ),
    (
        (
            "Monsters A–Z",
            "Blue Dragons",
            "Adult Blue Dragon",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Blue Dragons",
            "Adult Blue Dragon",
            "Traits",
        ),
        "**_Legendary Resistance (3/Day, or 4/Day in Lair)._** If the dragon fails a saving throw, it can choose to succeed instead.",
    ),
    (
        (
            "Monsters A–Z",
            "Blue Dragons",
            "Adult Blue Dragon",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Blue Dragons",
            "Adult Blue Dragon",
            "Actions",
        ),
        "**_Multiattack._** The dragon makes three Rend attacks. It can replace one attack with a use of Spellcasting to cast _Shatter_.",
    ),
    (
        (
            "Monsters A–Z",
            "Blue Dragons",
            "Adult Blue Dragon",
            "Actions",
        ),
        "**_Rend._** _Melee Attack Roll:_ +12, reach 10 ft. _Hit:_ 16 (2d8 + 7) Slashing damage plus 5 (1d10) Lightning damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Blue Dragons",
            "Adult Blue Dragon",
            "Actions",
        ),
        "**_Lightning Breath (Recharge 5–6)._** _Dexterity Saving Throw:_ DC 19, each creature in a 90-foot-long, 5-foot-wide Line. _Failure:_ 60 (11d10) Lightning damage. _Success:_ Half damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Blue Dragons",
            "Adult Blue Dragon",
            "Actions",
        ),
        "**_Spellcasting._** The dragon casts one of the following spells, requiring no Material components and using Charisma as the spellcasting ability (spell save DC 18): <br>\n&emsp;**At Will:** _Detect Magic_, _Invisibility_, _Mage Hand_, _Shatter_ <br>\n&emsp;**1/Day Each:** _Scrying_, _Sending_",
    ),
    (
        (
            "Monsters A–Z",
            "Blue Dragons",
            "Adult Blue Dragon",
            "Legendary Actions",
        ),
        "#### Legendary Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Blue Dragons",
            "Adult Blue Dragon",
            "Legendary Actions",
        ),
        "_Legendary Action Uses: 3 (4 in Lair). Immediately after another creature's turn, the dragon can expend a use to take one of the following actions. The dragon regains all expended uses at the start of each of its turns._",
    ),
    (
        (
            "Monsters A–Z",
            "Blue Dragons",
            "Adult Blue Dragon",
            "Legendary Actions",
        ),
        "**_Cloaked Flight._** The dragon uses Spellcasting to cast _Invisibility_ on itself, and it can fly up to half its Fly Speed. The dragon can't take this action again until the start of its next turn.",
    ),
    (
        (
            "Monsters A–Z",
            "Blue Dragons",
            "Adult Blue Dragon",
            "Legendary Actions",
        ),
        "**_Sonic Boom._** The dragon uses Spellcasting to cast _Shatter_. The dragon can't take this action again until the start of its next turn.",
    ),
    (
        (
            "Monsters A–Z",
            "Blue Dragons",
            "Adult Blue Dragon",
            "Legendary Actions",
        ),
        "**_Tail Swipe._** The dragon makes one Rend attack.",
    ),
    (
        (
            "Monsters A–Z",
            "Blue Dragons",
            "Ancient Blue Dragon",
        ),
        "### Ancient Blue Dragon",
    ),
    (
        (
            "Monsters A–Z",
            "Blue Dragons",
            "Ancient Blue Dragon",
        ),
        "_Gargantuan Dragon (Chromatic), Lawful Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Blue Dragons",
            "Ancient Blue Dragon",
        ),
        "**AC** 22 **Initiative** +14 (24) <br>\n**HP** 481 (26d20 + 208) <br>\n**Speed** 40 ft., Burrow 40 ft., Fly 80 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Blue Dragons",
            "Ancient Blue Dragon",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>29</td>\n      <td>+9</td>\n      <td>+9</td>\n      <td><strong>DEX</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+7</td>\n      <td><strong>CON</strong></td>\n      <td>27</td>\n      <td>+8</td>\n      <td>+8</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+4</td>\n      <td><strong>WIS</strong></td>\n      <td>17</td>\n      <td>+3</td>\n      <td>+10</td>\n      <td><strong>CHA</strong></td>\n      <td>25</td>\n      <td>+7</td>\n      <td>+7</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Blue Dragons",
            "Ancient Blue Dragon",
        ),
        "**Skills** Perception +17, Stealth +7<br>\n**Immunities** Lightning<br>\n**Senses** Blindsight 60 ft., Darkvision 120 ft.; Passive Perception 27<br>\n**Languages** Common, Draconic<br>\n**CR** 23 (XP 50,000, or 62,000 in lair; PB +7)",
    ),
    (
        (
            "Monsters A–Z",
            "Blue Dragons",
            "Ancient Blue Dragon",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Blue Dragons",
            "Ancient Blue Dragon",
            "Traits",
        ),
        "**_Legendary Resistance (4/Day, or 5/Day in Lair)._** If the dragon fails a saving throw, it can choose to succeed instead.",
    ),
    (
        (
            "Monsters A–Z",
            "Blue Dragons",
            "Ancient Blue Dragon",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Blue Dragons",
            "Ancient Blue Dragon",
            "Actions",
        ),
        "**_Multiattack._** The dragon makes three Rend attacks. It can replace one attack with a use of Spellcasting to cast _Shatter_ (level 3 version).",
    ),
    (
        (
            "Monsters A–Z",
            "Blue Dragons",
            "Ancient Blue Dragon",
            "Actions",
        ),
        "**_Rend._** _Melee Attack Roll:_ +16, reach 15 ft. _Hit:_ 18 (2d8 + 9) Slashing damage plus 11 (2d10) Lightning damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Blue Dragons",
            "Ancient Blue Dragon",
            "Actions",
        ),
        "**_Lightning Breath (Recharge 5–6)._** _Dexterity Saving Throw:_ DC 23, each creature in a 120-foot-long, 10-foot-wide Line. _Failure:_ 88 (16d10) Lightning damage. _Success:_ Half damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Blue Dragons",
            "Ancient Blue Dragon",
            "Actions",
        ),
        "**_Spellcasting._** The dragon casts one of the following spells, requiring no Material components and using Charisma as the spellcasting ability (spell save DC 22): <br>\n&emsp;**At Will:** _Detect Magic_, _Invisibility_, _Mage Hand_, _Shatter_ (level 3 version) <br>\n&emsp;**1/Day Each:** _Scrying_, _Sending_",
    ),
    (
        (
            "Monsters A–Z",
            "Blue Dragons",
            "Ancient Blue Dragon",
            "Legendary Actions",
        ),
        "#### Legendary Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Blue Dragons",
            "Ancient Blue Dragon",
            "Legendary Actions",
        ),
        "_Legendary Action Uses: 3 (4 in Lair). Immediately after another creature's turn, the dragon can expend a use to take one of the following actions. The dragon regains all expended uses at the start of each of its turns._",
    ),
    (
        (
            "Monsters A–Z",
            "Blue Dragons",
            "Ancient Blue Dragon",
            "Legendary Actions",
        ),
        "**_Cloaked Flight._** The dragon uses Spellcasting to cast _Invisibility_ on itself, and it can fly up to half its Fly Speed. The dragon can't take this action again until the start of its next turn.",
    ),
    (
        (
            "Monsters A–Z",
            "Blue Dragons",
            "Ancient Blue Dragon",
            "Legendary Actions",
        ),
        "**_Sonic Boom._** The dragon uses Spellcasting to cast _Shatter_ (level 3 version). The dragon can't take this action again until the start of its next turn.",
    ),
    (
        (
            "Monsters A–Z",
            "Blue Dragons",
            "Ancient Blue Dragon",
            "Legendary Actions",
        ),
        "**_Tail Swipe._** The dragon makes one Rend attack.",
    ),
    (
        (
            "Monsters A–Z",
            "Bone Devil",
        ),
        "## Bone Devil",
    ),
    (
        (
            "Monsters A–Z",
            "Bone Devil",
            "Bone Devil",
        ),
        "### Bone Devil",
    ),
    (
        (
            "Monsters A–Z",
            "Bone Devil",
            "Bone Devil",
        ),
        "_Large Fiend (Devil), Lawful Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Bone Devil",
            "Bone Devil",
        ),
        "**AC** 16 **Initiative** +7 (17) <br>\n**HP** 161 (17d10 + 68) <br>\n**Speed** 40 ft., Fly 40 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Bone Devil",
            "Bone Devil",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+8</td>\n      <td><strong>DEX</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>CON</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+4</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+5</td>\n      <td><strong>WIS</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+6</td>\n      <td><strong>CHA</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+7</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Bone Devil",
            "Bone Devil",
        ),
        "**Skills** Deception +7, Insight +6<br>\n**Resistances** Cold<br>\n**Immunities** Fire, Poison; Poisoned<br>\n**Senses** Darkvision 120 ft. (unimpeded by magical Darkness); Passive Perception 12<br>\n**Languages** Infernal; telepathy 120 ft.<br>\n**CR** 9 (XP 5,000; PB +4)",
    ),
    (
        (
            "Monsters A–Z",
            "Bone Devil",
            "Bone Devil",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Bone Devil",
            "Bone Devil",
            "Traits",
        ),
        "**_Diabolical Restoration._** If the devil dies outside the Nine Hells, its body disappears in sulfurous smoke, and it gains a new body instantly, reviving with all its Hit Points somewhere in the Nine Hells.",
    ),
    (
        (
            "Monsters A–Z",
            "Bone Devil",
            "Bone Devil",
            "Traits",
        ),
        "**_Magic Resistance._** The devil has Advantage on saving throws against spells and other magical effects.",
    ),
    (
        (
            "Monsters A–Z",
            "Bone Devil",
            "Bone Devil",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Bone Devil",
            "Bone Devil",
            "Actions",
        ),
        "**_Multiattack._** The devil makes two Claw attacks and one Infernal Sting attack.",
    ),
    (
        (
            "Monsters A–Z",
            "Bone Devil",
            "Bone Devil",
            "Actions",
        ),
        "**_Claw._** _Melee Attack Roll:_ +8, reach 10 ft. _Hit:_ 13 (2d8 + 4) Slashing damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Bone Devil",
            "Bone Devil",
            "Actions",
        ),
        "**_Infernal Sting._** _Melee Attack Roll:_ +8, reach 10 ft. _Hit:_ 15 (2d10 + 4) Piercing damage plus 18 (4d8) Poison damage, and the target has the Poisoned condition until the start of the devil's next turn. While Poisoned, the target can't regain Hit Points.",
    ),
    (
        (
            "Monsters A–Z",
            "Brass Dragons",
        ),
        "## Brass Dragons",
    ),
    (
        (
            "Monsters A–Z",
            "Brass Dragons",
            "Brass Dragon Wyrmling",
        ),
        "### Brass Dragon Wyrmling",
    ),
    (
        (
            "Monsters A–Z",
            "Brass Dragons",
            "Brass Dragon Wyrmling",
        ),
        "_Medium Dragon (Metallic), Chaotic Good_",
    ),
    (
        (
            "Monsters A–Z",
            "Brass Dragons",
            "Brass Dragon Wyrmling",
        ),
        "**AC** 15 **Initiative** +2 (12) <br>\n**HP** 22 (4d8 + 4) <br>\n**Speed** 30 ft., Burrow 15 ft., Fly 60 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Brass Dragons",
            "Brass Dragon Wyrmling",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>DEX</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+2</td>\n      <td><strong>CON</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>WIS</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+2</td>\n      <td><strong>CHA</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Brass Dragons",
            "Brass Dragon Wyrmling",
        ),
        "**Skills** Perception +4, Stealth +2<br>\n**Immunities** Fire<br>\n**Senses** Blindsight 10 ft., Darkvision 60 ft.; Passive Perception 14<br>\n**Languages** Draconic<br>\n**CR** 1 (XP 200; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Brass Dragons",
            "Brass Dragon Wyrmling",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Brass Dragons",
            "Brass Dragon Wyrmling",
            "Actions",
        ),
        "**_Rend._** _Melee Attack Roll:_ +4, reach 5 ft. _Hit:_ 7 (1d10 + 2) Slashing damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Brass Dragons",
            "Brass Dragon Wyrmling",
            "Actions",
        ),
        "**_Fire Breath (Recharge 5–6)._** _Dexterity Saving Throw:_ DC 11, each creature in a 20-foot-long, 5-foot-wide Line. _Failure:_ 14 (4d6) Fire damage. _Success:_ Half damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Brass Dragons",
            "Brass Dragon Wyrmling",
            "Actions",
        ),
        "**_Sleep Breath._** _Constitution Saving Throw:_ DC 11, each creature in a 15-foot Cone. _Failure:_ The target has the Incapacitated condition until the end of its next turn, at which point it repeats the save. _Second Failure:_ The target has the Unconscious condition for 1 minute. This effect ends for the target if it takes damage or a creature within 5 feet of it takes an action to wake it.",
    ),
    (
        (
            "Monsters A–Z",
            "Brass Dragons",
            "Young Brass Dragon",
        ),
        "### Young Brass Dragon",
    ),
    (
        (
            "Monsters A–Z",
            "Brass Dragons",
            "Young Brass Dragon",
        ),
        "_Large Dragon (Metallic), Chaotic Good_",
    ),
    (
        (
            "Monsters A–Z",
            "Brass Dragons",
            "Young Brass Dragon",
        ),
        "**AC** 17 **Initiative** +3 (13) <br>\n**HP** 110 (13d10 + 39) <br>\n**Speed** 40 ft., Burrow 20 ft., Fly 80 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Brass Dragons",
            "Young Brass Dragon",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>19</td>\n      <td>+4</td>\n      <td>+4</td>\n      <td><strong>DEX</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+3</td>\n      <td><strong>CON</strong></td>\n      <td>17</td>\n      <td>+3</td>\n      <td>+3</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>WIS</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+3</td>\n      <td><strong>CHA</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Brass Dragons",
            "Young Brass Dragon",
        ),
        "**Skills** Perception +6, Persuasion +5, Stealth +3<br>\n**Immunities** Fire<br>\n**Senses** Blindsight 30 ft., Darkvision 120 ft.; Passive Perception 16<br>\n**Languages** Common, Draconic<br>\n**CR** 6 (XP 2,300; PB +3)",
    ),
    (
        (
            "Monsters A–Z",
            "Brass Dragons",
            "Young Brass Dragon",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Brass Dragons",
            "Young Brass Dragon",
            "Actions",
        ),
        "**_Multiattack._** The dragon makes three Rend attacks. It can replace two attacks with a use of Sleep Breath.",
    ),
    (
        (
            "Monsters A–Z",
            "Brass Dragons",
            "Young Brass Dragon",
            "Actions",
        ),
        "**_Rend._** _Melee Attack Roll:_ +7, reach 10 ft. _Hit:_ 15 (2d10 + 4) Slashing damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Brass Dragons",
            "Young Brass Dragon",
            "Actions",
        ),
        "**_Fire Breath (Recharge 5–6)._** _Dexterity Saving Throw:_ DC 14, each creature in a 40-foot-long, 5-foot-wide Line. _Failure:_ 38 (11d6) Fire damage. _Success:_ Half damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Brass Dragons",
            "Young Brass Dragon",
            "Actions",
        ),
        "**_Sleep Breath._** _Constitution Saving Throw:_ DC 14, each creature in a 30-foot Cone. _Failure:_ The target has the Incapacitated condition until the end of its next turn, at which point it repeats the save. _Second Failure:_ The target has the Unconscious condition for 1 minute. This effect ends for the target if it takes damage or a creature within 5 feet of it takes an action to wake it.",
    ),
    (
        (
            "Monsters A–Z",
            "Brass Dragons",
            "Adult Brass Dragon",
        ),
        "### Adult Brass Dragon",
    ),
    (
        (
            "Monsters A–Z",
            "Brass Dragons",
            "Adult Brass Dragon",
        ),
        "_Huge Dragon (Metallic), Chaotic Good_",
    ),
    (
        (
            "Monsters A–Z",
            "Brass Dragons",
            "Adult Brass Dragon",
        ),
        "**AC** 18 **Initiative** +10 (20) <br>\n**HP** 172 (15d12 + 75) <br>\n**Speed** 40 ft., Burrow 30 ft., Fly 80 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Brass Dragons",
            "Adult Brass Dragon",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>23</td>\n      <td>+6</td>\n      <td>+6</td>\n      <td><strong>DEX</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+5</td>\n      <td><strong>CON</strong></td>\n      <td>21</td>\n      <td>+5</td>\n      <td>+5</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>WIS</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+6</td>\n      <td><strong>CHA</strong></td>\n      <td>17</td>\n      <td>+3</td>\n      <td>+3</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Brass Dragons",
            "Adult Brass Dragon",
        ),
        "**Skills** History +7, Perception +11, Persuasion +8, Stealth +5<br>\n**Immunities** Fire<br>\n**Senses** Blindsight 60 ft., Darkvision 120 ft.; Passive Perception 21<br>\n**Languages** Common, Draconic<br>\n**CR** 13 (XP 10,000, or 11,500 in lair; PB +5)",
    ),
    (
        (
            "Monsters A–Z",
            "Brass Dragons",
            "Adult Brass Dragon",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Brass Dragons",
            "Adult Brass Dragon",
            "Traits",
        ),
        "**_Legendary Resistance (3/Day, or 4/Day in Lair)._** If the dragon fails a saving throw, it can choose to succeed instead.",
    ),
    (
        (
            "Monsters A–Z",
            "Brass Dragons",
            "Adult Brass Dragon",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Brass Dragons",
            "Adult Brass Dragon",
            "Actions",
        ),
        "**_Multiattack._** The dragon makes three Rend attacks. It can replace one attack with a use of (A) Sleep Breath or (B) Spellcasting to cast _Scorching Ray_.",
    ),
    (
        (
            "Monsters A–Z",
            "Brass Dragons",
            "Adult Brass Dragon",
            "Actions",
        ),
        "**_Rend._** _Melee Attack Roll:_ +11, reach 10 ft. _Hit:_ 17 (2d10 + 6) Slashing damage plus 4 (1d8) Fire damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Brass Dragons",
            "Adult Brass Dragon",
            "Actions",
        ),
        "**_Fire Breath (Recharge 5–6)._** _Dexterity Saving Throw:_ DC 18, each creature in a 60-foot-long, 5-foot-wide Line. _Failure:_ 45 (10d8) Fire damage. _Success:_ Half damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Brass Dragons",
            "Adult Brass Dragon",
            "Actions",
        ),
        "**_Sleep Breath._** _Constitution Saving Throw:_ DC 18, each creature in a 60-foot Cone. _Failure:_ The target has the Incapacitated condition until the end of its next turn, at which point it repeats the save. _Second Failure:_ The target has the Unconscious condition for 10 minutes. This effect ends for the target if it takes damage or a creature within 5 feet of it takes an action to wake it.",
    ),
    (
        (
            "Monsters A–Z",
            "Brass Dragons",
            "Adult Brass Dragon",
            "Actions",
        ),
        "**_Spellcasting._** The dragon casts one of the following spells, requiring no Material components and using Charisma as the spellcasting ability (spell save DC 16): <br>\n&emsp;**At Will:** _Detect Magic_, _Minor Illusion_, _Scorching Ray_, _Shapechange_ (Beast or Humanoid form only, no Temporary Hit Points gained from the spell, and no Concentration or Temporary Hit Points required to maintain the spell), _Speak with Animals_ <br>\n&emsp;**1/Day Each:** _Detect Thoughts_, _Control Weather_",
    ),
    (
        (
            "Monsters A–Z",
            "Brass Dragons",
            "Adult Brass Dragon",
            "Legendary Actions",
        ),
        "#### Legendary Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Brass Dragons",
            "Adult Brass Dragon",
            "Legendary Actions",
        ),
        "_Legendary Action Uses: 3 (4 in Lair). Immediately after another creature's turn, the dragon can expend a use to take one of the following actions. The dragon regains all expended uses at the start of each of its turns._",
    ),
    (
        (
            "Monsters A–Z",
            "Brass Dragons",
            "Adult Brass Dragon",
            "Legendary Actions",
        ),
        "**_Blazing Light._** The dragon uses Spellcasting to cast _Scorching Ray_.",
    ),
    (
        (
            "Monsters A–Z",
            "Brass Dragons",
            "Adult Brass Dragon",
            "Legendary Actions",
        ),
        "**_Pounce._** The dragon moves up to half its Speed, and it makes one Rend attack.",
    ),
    (
        (
            "Monsters A–Z",
            "Brass Dragons",
            "Adult Brass Dragon",
            "Legendary Actions",
        ),
        "**_Scorching Sands._** _Dexterity Saving Throw:_ DC 16, one creature the dragon can see within 120 feet. _Failure:_ 27 (6d8) Fire damage, and the target's Speed is halved until the end of its next turn. _Failure or Success:_ The dragon can't take this action again until the start of its next turn.",
    ),
    (
        (
            "Monsters A–Z",
            "Brass Dragons",
            "Ancient Brass Dragon",
        ),
        "### Ancient Brass Dragon",
    ),
    (
        (
            "Monsters A–Z",
            "Brass Dragons",
            "Ancient Brass Dragon",
        ),
        "_Gargantuan Dragon (Metallic), Chaotic Good_",
    ),
    (
        (
            "Monsters A–Z",
            "Brass Dragons",
            "Ancient Brass Dragon",
        ),
        "**AC** 20 **Initiative** +12 (22) <br>\n**HP** 332 (19d20 + 133) <br>\n**Speed** 40 ft., Burrow 40 ft., Fly 80 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Brass Dragons",
            "Ancient Brass Dragon",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>27</td>\n      <td>+8</td>\n      <td>+8</td>\n      <td><strong>DEX</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+6</td>\n      <td><strong>CON</strong></td>\n      <td>25</td>\n      <td>+7</td>\n      <td>+7</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>WIS</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+8</td>\n      <td><strong>CHA</strong></td>\n      <td>22</td>\n      <td>+6</td>\n      <td>+6</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Brass Dragons",
            "Ancient Brass Dragon",
        ),
        "**Skills** History +9, Perception +14, Persuasion +12, Stealth +6<br>\n**Immunities** Fire<br>\n**Senses** Blindsight 60 ft., Darkvision 120 ft.; Passive Perception 24<br>\n**Languages** Common, Draconic<br>\n**CR** 20 (XP 25,000, or 33,000 in lair; PB +6)",
    ),
    (
        (
            "Monsters A–Z",
            "Brass Dragons",
            "Ancient Brass Dragon",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Brass Dragons",
            "Ancient Brass Dragon",
            "Traits",
        ),
        "**_Legendary Resistance (4/Day, or 5/Day in Lair)._** If the dragon fails a saving throw, it can choose to succeed instead.",
    ),
    (
        (
            "Monsters A–Z",
            "Brass Dragons",
            "Ancient Brass Dragon",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Brass Dragons",
            "Ancient Brass Dragon",
            "Actions",
        ),
        "**_Multiattack._** The dragon makes three Rend attacks. It can replace one attack with a use of (A) Sleep Breath or (B) Spellcasting to cast _Scorching Ray_ (level 3 version).",
    ),
    (
        (
            "Monsters A–Z",
            "Brass Dragons",
            "Ancient Brass Dragon",
            "Actions",
        ),
        "**_Rend._** _Melee Attack Roll:_ +14, reach 15 ft. _Hit:_ 19 (2d10 + 8) Slashing damage plus 7 (2d6) Fire damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Brass Dragons",
            "Ancient Brass Dragon",
            "Actions",
        ),
        "**_Fire Breath (Recharge 5–6)._** _Dexterity Saving Throw:_ DC 21, each creature in a 90-foot-long, 5-foot-wide Line. _Failure:_ 58 (13d8) Fire damage. _Success:_ Half damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Brass Dragons",
            "Ancient Brass Dragon",
            "Actions",
        ),
        "**_Sleep Breath._** _Constitution Saving Throw:_ DC 21, each creature in a 90-foot Cone. _Failure:_ The target has the Incapacitated condition until the end of its next turn, at which point it repeats the save. _Second Failure:_ The target has the Unconscious condition for 10 minutes. This effect ends for the target if it takes damage or a creature within 5 feet of it takes an action to wake it.",
    ),
    (
        (
            "Monsters A–Z",
            "Brass Dragons",
            "Ancient Brass Dragon",
            "Actions",
        ),
        "**_Spellcasting._** The dragon casts one of the following spells, requiring no Material components and using Charisma as the spellcasting ability (spell save DC 20): <br>\n&emsp;**At Will:** _Detect Magic_, _Minor Illusion_, _Scorching Ray_ (level 3 version), _Shapechange_ (Beast or Humanoid form only, no Temporary Hit Points gained from the spell, and no Concentration or Temporary Hit Points required to maintain the spell), _Speak with Animals_ <br>\n&emsp;**1/Day Each:** _Control Weather_, _Detect Thoughts_",
    ),
    (
        (
            "Monsters A–Z",
            "Brass Dragons",
            "Ancient Brass Dragon",
            "Legendary Actions",
        ),
        "#### Legendary Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Brass Dragons",
            "Ancient Brass Dragon",
            "Legendary Actions",
        ),
        "_Legendary Action Uses: 3 (4 in Lair). Immediately after another creature's turn, the dragon can expend a use to take one of the following actions. The dragon regains all expended uses at the start of each of its turns._",
    ),
    (
        (
            "Monsters A–Z",
            "Brass Dragons",
            "Ancient Brass Dragon",
            "Legendary Actions",
        ),
        "**_Blazing Light._** The dragon uses Spellcasting to cast _Scorching Ray_ (level 3 version).",
    ),
    (
        (
            "Monsters A–Z",
            "Brass Dragons",
            "Ancient Brass Dragon",
            "Legendary Actions",
        ),
        "**_Pounce._** The dragon moves up to half its Speed, and it makes one Rend attack.",
    ),
    (
        (
            "Monsters A–Z",
            "Brass Dragons",
            "Ancient Brass Dragon",
            "Legendary Actions",
        ),
        "**_Scorching Sands._** _Dexterity Saving Throw:_ DC 20, one creature the dragon can see within 120 feet. _Failure:_ 36 (8d8) Fire damage, and the target's Speed is halved until the end of its next turn. _Failure or Success:_ The dragon can't take this action again until the start of its next turn.",
    ),
    (
        (
            "Monsters A–Z",
            "Bronze Dragons",
        ),
        "## Bronze Dragons",
    ),
    (
        (
            "Monsters A–Z",
            "Bronze Dragons",
            "Bronze Dragon Wyrmling",
        ),
        "### Bronze Dragon Wyrmling",
    ),
    (
        (
            "Monsters A–Z",
            "Bronze Dragons",
            "Bronze Dragon Wyrmling",
        ),
        "_Medium Dragon (Metallic), Lawful Good_",
    ),
    (
        (
            "Monsters A–Z",
            "Bronze Dragons",
            "Bronze Dragon Wyrmling",
        ),
        "**AC** 15 **Initiative** +2 (12) <br>\n**HP** 39 (6d8 + 12) <br>\n**Speed** 30 ft., Fly 60 ft., Swim 30 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Bronze Dragons",
            "Bronze Dragon Wyrmling",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>17</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>DEX</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+2</td>\n      <td><strong>CON</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>WIS</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+2</td>\n      <td><strong>CHA</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Bronze Dragons",
            "Bronze Dragon Wyrmling",
        ),
        "**Skills** Perception +4, Stealth +2<br>\n**Immunities** Lightning<br>\n**Senses** Blindsight 10 ft., Darkvision 60 ft.; Passive Perception 14<br>\n**Languages** Draconic<br>\n**CR** 2 (XP 450; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Bronze Dragons",
            "Bronze Dragon Wyrmling",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Bronze Dragons",
            "Bronze Dragon Wyrmling",
            "Traits",
        ),
        "**_Amphibious._** The dragon can breathe air and water.",
    ),
    (
        (
            "Monsters A–Z",
            "Bronze Dragons",
            "Bronze Dragon Wyrmling",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Bronze Dragons",
            "Bronze Dragon Wyrmling",
            "Actions",
        ),
        "**_Multiattack._** The dragon makes two Rend attacks.",
    ),
    (
        (
            "Monsters A–Z",
            "Bronze Dragons",
            "Bronze Dragon Wyrmling",
            "Actions",
        ),
        "**_Rend._** _Melee Attack Roll:_ +5, reach 5 ft. _Hit:_ 8 (1d10 + 3) Slashing damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Bronze Dragons",
            "Bronze Dragon Wyrmling",
            "Actions",
        ),
        "**_Lightning Breath (Recharge 5–6)._** _Dexterity Saving Throw:_ DC 12, each creature in a 40-foot-long, 5-foot-wide Line. _Failure:_ 16 (3d10) Lightning damage. _Success:_ Half damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Bronze Dragons",
            "Bronze Dragon Wyrmling",
            "Actions",
        ),
        "**_Repulsion Breath._** _Strength Saving Throw:_ DC 12, each creature in a 30-foot Cone. _Failure:_ The target is pushed up to 30 feet straight away from the dragon and has the Prone condition.",
    ),
    (
        (
            "Monsters A–Z",
            "Bronze Dragons",
            "Young Bronze Dragon",
        ),
        "### Young Bronze Dragon",
    ),
    (
        (
            "Monsters A–Z",
            "Bronze Dragons",
            "Young Bronze Dragon",
        ),
        "_Large Dragon (Metallic), Lawful Good_",
    ),
    (
        (
            "Monsters A–Z",
            "Bronze Dragons",
            "Young Bronze Dragon",
        ),
        "**AC** 17 **Initiative** +3 (13) <br>\n**HP** 142 (15d10 + 60) <br>\n**Speed** 40 ft., Fly 80 ft., Swim 40 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Bronze Dragons",
            "Young Bronze Dragon",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>21</td>\n      <td>+5</td>\n      <td>+5</td>\n      <td><strong>DEX</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+3</td>\n      <td><strong>CON</strong></td>\n      <td>19</td>\n      <td>+4</td>\n      <td>+4</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>WIS</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+4</td>\n      <td><strong>CHA</strong></td>\n      <td>17</td>\n      <td>+3</td>\n      <td>+3</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Bronze Dragons",
            "Young Bronze Dragon",
        ),
        "**Skills** Insight +4, Perception +7, Stealth +3<br>\n**Immunities** Lightning<br>\n**Senses** Blindsight 30 ft., Darkvision 120 ft.; Passive Perception 17<br>\n**Languages** Common, Draconic<br>\n**CR** 8 (XP 3,900; PB +3)",
    ),
    (
        (
            "Monsters A–Z",
            "Bronze Dragons",
            "Young Bronze Dragon",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Bronze Dragons",
            "Young Bronze Dragon",
            "Traits",
        ),
        "**_Amphibious._** The dragon can breathe air and water.",
    ),
    (
        (
            "Monsters A–Z",
            "Bronze Dragons",
            "Young Bronze Dragon",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Bronze Dragons",
            "Young Bronze Dragon",
            "Actions",
        ),
        "**_Multiattack._** The dragon makes three Rend attacks. It can replace one attack with a use of Repulsion Breath.",
    ),
    (
        (
            "Monsters A–Z",
            "Bronze Dragons",
            "Young Bronze Dragon",
            "Actions",
        ),
        "**_Rend._** _Melee Attack Roll:_ +8, reach 10 ft. _Hit:_ 16 (2d10 + 5) Slashing damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Bronze Dragons",
            "Young Bronze Dragon",
            "Actions",
        ),
        "**_Lightning Breath (Recharge 5–6)._** _Dexterity Saving Throw:_ DC 15, each creature in a 60-foot-long, 5-foot-wide Line. _Failure:_ 49 (9d10) Lightning damage. _Success:_ Half damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Bronze Dragons",
            "Young Bronze Dragon",
            "Actions",
        ),
        "**_Repulsion Breath._** _Strength Saving Throw:_ DC 15, each creature in a 30-foot Cone. _Failure:_ The target is pushed up to 40 feet straight away from the dragon and has the Prone condition.",
    ),
    (
        (
            "Monsters A–Z",
            "Bronze Dragons",
            "Adult Bronze Dragon",
        ),
        "### Adult Bronze Dragon",
    ),
    (
        (
            "Monsters A–Z",
            "Bronze Dragons",
            "Adult Bronze Dragon",
        ),
        "_Huge Dragon (Metallic), Lawful Good_",
    ),
    (
        (
            "Monsters A–Z",
            "Bronze Dragons",
            "Adult Bronze Dragon",
        ),
        "**AC** 18 **Initiative** +10 (20) <br>\n**HP** 212 (17d12 + 102) <br>\n**Speed** 40 ft., Fly 80 ft., Swim 40 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Bronze Dragons",
            "Adult Bronze Dragon",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>25</td>\n      <td>+7</td>\n      <td>+7</td>\n      <td><strong>DEX</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+5</td>\n      <td><strong>CON</strong></td>\n      <td>23</td>\n      <td>+6</td>\n      <td>+6</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>WIS</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+7</td>\n      <td><strong>CHA</strong></td>\n      <td>20</td>\n      <td>+5</td>\n      <td>+5</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Bronze Dragons",
            "Adult Bronze Dragon",
        ),
        "**Skills** Insight +7, Perception +12, Stealth +5<br>\n**Immunities** Lightning<br>\n**Senses** Blindsight 60 ft., Darkvision 120 ft.; Passive Perception 22<br>\n**Languages** Common, Draconic<br>\n**CR** 15 (XP 13,000, or 15,000 in lair; PB +5)",
    ),
    (
        (
            "Monsters A–Z",
            "Bronze Dragons",
            "Adult Bronze Dragon",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Bronze Dragons",
            "Adult Bronze Dragon",
            "Traits",
        ),
        "**_Amphibious._** The dragon can breathe air and water.",
    ),
    (
        (
            "Monsters A–Z",
            "Bronze Dragons",
            "Adult Bronze Dragon",
            "Traits",
        ),
        "**_Legendary Resistance (3/Day, or 4/Day in Lair)._** If the dragon fails a saving throw, it can choose to succeed instead.",
    ),
    (
        (
            "Monsters A–Z",
            "Bronze Dragons",
            "Adult Bronze Dragon",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Bronze Dragons",
            "Adult Bronze Dragon",
            "Actions",
        ),
        "**_Multiattack._** The dragon makes three Rend attacks. It can replace one attack with a use of (A) Repulsion Breath or (B) Spellcasting to cast _Guiding Bolt_ (level 2 version).",
    ),
    (
        (
            "Monsters A–Z",
            "Bronze Dragons",
            "Adult Bronze Dragon",
            "Actions",
        ),
        "**_Rend._** _Melee Attack Roll:_ +12, reach 10 ft. _Hit:_ 16 (2d8 + 7) Slashing damage plus 5 (1d10) Lightning damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Bronze Dragons",
            "Adult Bronze Dragon",
            "Actions",
        ),
        "**_Lightning Breath (Recharge 5–6)._** _Dexterity Saving Throw:_ DC 19, each creature in a 90-foot-long, 5-foot-wide Line. _Failure:_ 55 (10d10) Lightning damage. _Success:_ Half damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Bronze Dragons",
            "Adult Bronze Dragon",
            "Actions",
        ),
        "**_Repulsion Breath._** _Strength Saving Throw:_ DC 19, each creature in a 30-foot Cone. _Failure:_ The target is pushed up to 60 feet straight away from the dragon and has the Prone condition.",
    ),
    (
        (
            "Monsters A–Z",
            "Bronze Dragons",
            "Adult Bronze Dragon",
            "Actions",
        ),
        "**_Spellcasting._** The dragon casts one of the following spells, requiring no Material components and using Charisma as the spellcasting ability (spell save DC 17, +10 to hit with spell attacks): <br>\n&emsp;**At Will:** _Detect Magic_, _Guiding Bolt_ (level 2 version), _Shapechange_ (Beast or Humanoid form only, no Temporary Hit Points gained from the spell, and no Concentration or Temporary Hit Points required to maintain the spell), _Speak with Animals_, _Thaumaturgy_ <br>\n&emsp;**1/Day Each:** _Detect Thoughts_, _Water Breathing_",
    ),
    (
        (
            "Monsters A–Z",
            "Bronze Dragons",
            "Adult Bronze Dragon",
            "Legendary Actions",
        ),
        "#### Legendary Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Bronze Dragons",
            "Adult Bronze Dragon",
            "Legendary Actions",
        ),
        "_Legendary Action Uses: 3 (4 in Lair). Immediately after another creature's turn, the dragon can expend a use to take one of the following actions. The dragon regains all expended uses at the start of each of its turns._",
    ),
    (
        (
            "Monsters A–Z",
            "Bronze Dragons",
            "Adult Bronze Dragon",
            "Legendary Actions",
        ),
        "**_Guiding Light._** The dragon uses Spellcasting to cast _Guiding Bolt_ (level 2 version).",
    ),
    (
        (
            "Monsters A–Z",
            "Bronze Dragons",
            "Adult Bronze Dragon",
            "Legendary Actions",
        ),
        "**_Pounce._** The dragon moves up to half its Speed, and it makes one Rend attack.",
    ),
    (
        (
            "Monsters A–Z",
            "Bronze Dragons",
            "Adult Bronze Dragon",
            "Legendary Actions",
        ),
        "**_Thunderclap._** _Constitution Saving Throw:_ DC 17, each creature in a 20-foot-radius Sphere centered on a point the dragon can see within 90 feet. _Failure:_ 10 (3d6)\nThunder damage, and the target has the Deafened condition until the end of its next turn.",
    ),
    (
        (
            "Monsters A–Z",
            "Bronze Dragons",
            "Ancient Bronze Dragon",
        ),
        "### Ancient Bronze Dragon",
    ),
    (
        (
            "Monsters A–Z",
            "Bronze Dragons",
            "Ancient Bronze Dragon",
        ),
        "_Gargantuan Dragon (Metallic), Lawful Good_",
    ),
    (
        (
            "Monsters A–Z",
            "Bronze Dragons",
            "Ancient Bronze Dragon",
        ),
        "**AC** 22 **Initiative** +14 (24) <br>\n**HP** 444 (24d20 + 192) <br>\n**Speed** 40 ft., Fly 80 ft., Swim 40 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Bronze Dragons",
            "Ancient Bronze Dragon",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>29</td>\n      <td>+9</td>\n      <td>+9</td>\n      <td><strong>DEX</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+7</td>\n      <td><strong>CON</strong></td>\n      <td>27</td>\n      <td>+8</td>\n      <td>+8</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+4</td>\n      <td><strong>WIS</strong></td>\n      <td>17</td>\n      <td>+3</td>\n      <td>+10</td>\n      <td><strong>CHA</strong></td>\n      <td>25</td>\n      <td>+7</td>\n      <td>+7</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Bronze Dragons",
            "Ancient Bronze Dragon",
        ),
        "**Skills** Insight +10, Perception +17, Stealth +7<br>\n**Immunities** Lightning<br>\n**Senses** Blindsight 60 ft., Darkvision 120 ft.; Passive Perception 27<br>\n**Languages** Common, Draconic<br>\n**CR** 22 (XP 41,000, or 50,000 in lair; PB +7)",
    ),
    (
        (
            "Monsters A–Z",
            "Bronze Dragons",
            "Ancient Bronze Dragon",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Bronze Dragons",
            "Ancient Bronze Dragon",
            "Traits",
        ),
        "**_Amphibious._** The dragon can breathe air and water.",
    ),
    (
        (
            "Monsters A–Z",
            "Bronze Dragons",
            "Ancient Bronze Dragon",
            "Traits",
        ),
        "**_Legendary Resistance (4/Day, or 5/Day in Lair)._** If the dragon fails a saving throw, it can choose to succeed instead.",
    ),
    (
        (
            "Monsters A–Z",
            "Bronze Dragons",
            "Ancient Bronze Dragon",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Bronze Dragons",
            "Ancient Bronze Dragon",
            "Actions",
        ),
        "**_Multiattack._** The dragon makes three Rend attacks. It can replace one attack with a use of (A) Repulsion Breath or (B) Spellcasting to cast _Guiding Bolt_ (level 2 version).",
    ),
    (
        (
            "Monsters A–Z",
            "Bronze Dragons",
            "Ancient Bronze Dragon",
            "Actions",
        ),
        "**_Rend._** _Melee Attack Roll:_ +16, reach 15 ft. _Hit:_ 18 (2d8 + 9) Slashing damage plus 9 (2d8) Lightning damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Bronze Dragons",
            "Ancient Bronze Dragon",
            "Actions",
        ),
        "**_Lightning Breath (Recharge 5–6)._** _Dexterity Saving Throw:_ DC 23, each creature in a 120-foot-long, 10-foot-wide Line. _Failure:_ 82 (15d10) Lightning damage. _Success:_ Half damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Bronze Dragons",
            "Ancient Bronze Dragon",
            "Actions",
        ),
        "**_Repulsion Breath._** _Strength Saving Throw:_ DC 23, each creature in a 30-foot Cone. _Failure:_ The target is pushed up to 60 feet straight away from the dragon and has the Prone condition.",
    ),
    (
        (
            "Monsters A–Z",
            "Bronze Dragons",
            "Ancient Bronze Dragon",
            "Actions",
        ),
        "**_Spellcasting._** The dragon casts one of the following spells, requiring no Material components and using Charisma as the spellcasting ability (spell save DC 22, +14 to hit with spell attacks): <br>\n&emsp;**At Will:** _Detect Magic_, _Guiding Bolt_ (level 2 version), _Shapechange_ (Beast or Humanoid form only, no Temporary Hit Points gained from the spell, and no Concentration or Temporary Hit Points required to maintain the spell), _Speak with Animals_, _Thaumaturgy_ <br>\n&emsp;**1/Day Each:** _Detect Thoughts_, _Control Water_, _Scrying_, _Water Breathing_",
    ),
    (
        (
            "Monsters A–Z",
            "Bronze Dragons",
            "Ancient Bronze Dragon",
            "Legendary Actions",
        ),
        "#### Legendary Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Bronze Dragons",
            "Ancient Bronze Dragon",
            "Legendary Actions",
        ),
        "_Legendary Action Uses: 3 (4 in Lair). Immediately after another creature's turn, the dragon can expend a use to take one of the following actions. The dragon regains all expended uses at the start of each of its turns._",
    ),
    (
        (
            "Monsters A–Z",
            "Bronze Dragons",
            "Ancient Bronze Dragon",
            "Legendary Actions",
        ),
        "**_Guiding Light._** The dragon uses Spellcasting to cast _Guiding Bolt_ (level 2 version).",
    ),
    (
        (
            "Monsters A–Z",
            "Bronze Dragons",
            "Ancient Bronze Dragon",
            "Legendary Actions",
        ),
        "**_Pounce._** The dragon moves up to half its Speed, and it makes one Rend attack.",
    ),
    (
        (
            "Monsters A–Z",
            "Bronze Dragons",
            "Ancient Bronze Dragon",
            "Legendary Actions",
        ),
        "**_Thunderclap._** _Constitution Saving Throw:_ DC 22, each creature in a 20-foot-radius Sphere centered on a point the dragon can see within 120 feet. _Failure:_ 13 (3d8) Thunder damage, and the target has the Deafened condition until the end of its next turn.",
    ),
    (
        (
            "Monsters A–Z",
            "Bugbears",
        ),
        "## Bugbears",
    ),
    (
        (
            "Monsters A–Z",
            "Bugbears",
            "Bugbear Stalker",
        ),
        "### Bugbear Stalker",
    ),
    (
        (
            "Monsters A–Z",
            "Bugbears",
            "Bugbear Stalker",
        ),
        "_Medium Fey (Goblinoid), Chaotic Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Bugbears",
            "Bugbear Stalker",
        ),
        "**AC** 15 **Initiative** +2 (12) <br>\n**HP** 65 (10d8 + 20) <br>\n**Speed** 30 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Bugbears",
            "Bugbear Stalker",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>17</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>DEX</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CON</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+4</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>WIS</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+3</td>\n      <td><strong>CHA</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Bugbears",
            "Bugbear Stalker",
        ),
        "**Skills** Stealth +6, Survival +3<br>\n**Gear** Chain Shirt, Javelins (6), Morningstar<br>\n**Senses** Darkvision 60 ft.; Passive Perception 11<br>\n**Languages** Common, Goblin<br>\n**CR** 3 (XP 700; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Bugbears",
            "Bugbear Stalker",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Bugbears",
            "Bugbear Stalker",
            "Traits",
        ),
        "**_Abduct._** The bugbear needn't spend extra movement to move a creature it is grappling.",
    ),
    (
        (
            "Monsters A–Z",
            "Bugbears",
            "Bugbear Stalker",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Bugbears",
            "Bugbear Stalker",
            "Actions",
        ),
        "**_Multiattack._** The bugbear makes two Javelin or Morningstar attacks.",
    ),
    (
        (
            "Monsters A–Z",
            "Bugbears",
            "Bugbear Stalker",
            "Actions",
        ),
        "**_Javelin._** _Melee or Ranged Attack Roll:_ +5, reach 10 ft. or range 30/120 ft. _Hit:_ 13 (3d6 + 3) Piercing damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Bugbears",
            "Bugbear Stalker",
            "Actions",
        ),
        "**_Morningstar._** _Melee Attack Roll:_ +5 (with Advantage if the target is Grappled by the bugbear), reach 10 ft. _Hit:_ 12 (2d8 + 3) Piercing damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Bugbears",
            "Bugbear Stalker",
            "Bonus Actions",
        ),
        "#### Bonus Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Bugbears",
            "Bugbear Stalker",
            "Bonus Actions",
        ),
        "**_Quick Grapple._** _Dexterity Saving Throw:_ DC 13, one Medium or smaller creature the bugbear can see within 10 feet. _Failure:_ The target has the Grappled condition (escape DC 13).",
    ),
    (
        (
            "Monsters A–Z",
            "Bugbears",
            "Bugbear Warrior",
        ),
        "### Bugbear Warrior",
    ),
    (
        (
            "Monsters A–Z",
            "Bugbears",
            "Bugbear Warrior",
        ),
        "_Medium Fey (Goblinoid), Chaotic Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Bugbears",
            "Bugbear Warrior",
        ),
        "**AC** 14 **Initiative** +2 (12) <br>\n**HP** 33 (6d8 + 6) <br>\n**Speed** 30 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Bugbears",
            "Bugbear Warrior",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>DEX</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CON</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>8</td>\n      <td>−1</td>\n      <td>−1</td>\n      <td><strong>WIS</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CHA</strong></td>\n      <td>9</td>\n      <td>−1</td>\n      <td>−1</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Bugbears",
            "Bugbear Warrior",
        ),
        "**Skills** Stealth +6, Survival +2<br>\n**Gear** Hide Armor, Light Hammers (3)<br>\n**Senses** Darkvision 60 ft.; Passive Perception 10<br>\n**Languages** Common, Goblin<br>\n**CR** 1 (XP 200; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Bugbears",
            "Bugbear Warrior",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Bugbears",
            "Bugbear Warrior",
            "Traits",
        ),
        "**_Abduct._** The bugbear needn't spend extra movement to move a creature it is grappling.",
    ),
    (
        (
            "Monsters A–Z",
            "Bugbears",
            "Bugbear Warrior",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Bugbears",
            "Bugbear Warrior",
            "Actions",
        ),
        "**_Grab._** _Melee Attack Roll:_ +4, reach 10 ft. _Hit:_ 9 (2d6 + 2) Bludgeoning damage. If the target is a Medium or smaller creature, it has the Grappled condition (escape DC 12).",
    ),
    (
        (
            "Monsters A–Z",
            "Bugbears",
            "Bugbear Warrior",
            "Actions",
        ),
        "**_Light Hammer._** _Melee or Ranged Attack Roll:_ +4 (with Advantage if the target is Grappled by the bugbear), reach 10 ft. or range 20/60 ft. _Hit:_ 9 (3d4 + 2) Bludgeoning damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Bulette",
        ),
        "## Bulette",
    ),
    (
        (
            "Monsters A–Z",
            "Bulette",
            "Bulette",
        ),
        "### Bulette",
    ),
    (
        (
            "Monsters A–Z",
            "Bulette",
            "Bulette",
        ),
        "_Large Monstrosity, Unaligned_",
    ),
    (
        (
            "Monsters A–Z",
            "Bulette",
            "Bulette",
        ),
        "**AC** 17 **Initiative** +0 (10) <br>\n**HP** 94 (9d10 + 45) <br>\n**Speed** 40 ft., Burrow 40 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Bulette",
            "Bulette",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>19</td>\n      <td>+4</td>\n      <td>+4</td>\n      <td><strong>DEX</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CON</strong></td>\n      <td>21</td>\n      <td>+5</td>\n      <td>+5</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>2</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>WIS</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CHA</strong></td>\n      <td>5</td>\n      <td>−3</td>\n      <td>−3</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Bulette",
            "Bulette",
        ),
        "**Skills** Perception +6<br>\n**Senses** Darkvision 60 ft., Tremorsense 120 ft.; Passive Perception 16<br>\n**Languages** None<br>\n**CR** 5 (XP 1,800; PB +3)",
    ),
    (
        (
            "Monsters A–Z",
            "Bulette",
            "Bulette",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Bulette",
            "Bulette",
            "Actions",
        ),
        "**_Multiattack._** The bulette makes two Bite attacks.",
    ),
    (
        (
            "Monsters A–Z",
            "Bulette",
            "Bulette",
            "Actions",
        ),
        "**_Bite._** _Melee Attack Roll:_ +7, reach 5 ft. _Hit:_ 17 (2d12 + 4) Piercing damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Bulette",
            "Bulette",
            "Actions",
        ),
        "**_Deadly Leap._** The bulette spends 5 feet of movement to jump to a space within 15 feet that contains one or more Large or smaller creatures. _Dexterity Saving Throw:_ DC 15, each creature in the bulette's destination space. _Failure:_ 19 (3d12) Bludgeoning damage, and the target has the Prone condition. _Success:_ Half damage, and the target is pushed 5 feet straight away from the bulette.",
    ),
    (
        (
            "Monsters A–Z",
            "Bulette",
            "Bulette",
            "Bonus Actions",
        ),
        "#### Bonus Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Bulette",
            "Bulette",
            "Bonus Actions",
        ),
        "**_Leap._** The bulette jumps up to 30 feet by spending 10 feet of movement.",
    ),
    (
        (
            "Monsters A–Z",
            "Centaur",
        ),
        "## Centaur",
    ),
    (
        (
            "Monsters A–Z",
            "Centaur",
            "Centaur Trooper",
        ),
        "### Centaur Trooper",
    ),
    (
        (
            "Monsters A–Z",
            "Centaur",
            "Centaur Trooper",
        ),
        "_Large Fey, Neutral Good_",
    ),
    (
        (
            "Monsters A–Z",
            "Centaur",
            "Centaur Trooper",
        ),
        "**AC** 16 **Initiative** +2 (12) <br>\n**HP** 45 (6d10 + 12) <br>\n**Speed** 50 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Centaur",
            "Centaur Trooper",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+4</td>\n      <td><strong>DEX</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CON</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>9</td>\n      <td>−1</td>\n      <td>−1</td>\n      <td><strong>WIS</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CHA</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Centaur",
            "Centaur Trooper",
        ),
        "**Skills** Athletics +6, Perception +3<br>\n**Gear** Breastplate, Longbow, Pike<br>\n**Senses** Passive Perception 13<br>\n**Languages** Elvish, Sylvan<br>\n**CR** 2 (XP 450; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Centaur",
            "Centaur Trooper",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Centaur",
            "Centaur Trooper",
            "Actions",
        ),
        "**_Multiattack._** The centaur makes two attacks, using Pike or Longbow in any combination.",
    ),
    (
        (
            "Monsters A–Z",
            "Centaur",
            "Centaur Trooper",
            "Actions",
        ),
        "**_Pike._** _Melee Attack Roll:_ +6, reach 10 ft. _Hit:_ 9 (1d10 + 4) Piercing damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Centaur",
            "Centaur Trooper",
            "Actions",
        ),
        "**_Longbow._** _Ranged Attack Roll:_ +4, range 150/600 ft. _Hit:_ 6 (1d8 + 2) Piercing damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Centaur",
            "Centaur Trooper",
            "Bonus Actions",
        ),
        "#### Bonus Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Centaur",
            "Centaur Trooper",
            "Bonus Actions",
        ),
        "**_Trampling Charge (Recharge 5–6)._** The centaur moves up to its Speed without provoking Opportunity Attacks and can move through the spaces of Medium or smaller creatures. Each creature whose space the centaur enters is targeted once by the following effect. _Strength Saving Throw:_ DC 14. _Failure:_ 7 (1d6 + 4) Bludgeoning damage, and the target has the Prone condition.",
    ),
    (
        (
            "Monsters A–Z",
            "Chain Devil",
        ),
        "## Chain Devil",
    ),
    (
        (
            "Monsters A–Z",
            "Chain Devil",
            "Chain Devil",
        ),
        "### Chain Devil",
    ),
    (
        (
            "Monsters A–Z",
            "Chain Devil",
            "Chain Devil",
        ),
        "_Medium Fiend (Devil), Lawful Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Chain Devil",
            "Chain Devil",
        ),
        "**AC** 15 **Initiative** +5 (15) <br>\n**HP** 85 (10d8 + 40) <br>\n**Speed** 30 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Chain Devil",
            "Chain Devil",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+4</td>\n      <td><strong>DEX</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CON</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+7</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>WIS</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+4</td>\n      <td><strong>CHA</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Chain Devil",
            "Chain Devil",
        ),
        "**Resistances** Bludgeoning, Cold, Piercing, Slashing<br>\n**Immunities** Fire, Poison; Poisoned<br>\n**Senses** Darkvision 120 ft. (unimpeded by magical Darkness); Passive Perception 11<br>\n**Languages** Infernal; telepathy 120 ft.<br>\n**CR** 8 (XP 3,900; PB +3)",
    ),
    (
        (
            "Monsters A–Z",
            "Chain Devil",
            "Chain Devil",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Chain Devil",
            "Chain Devil",
            "Traits",
        ),
        "**_Diabolical Restoration._** If the devil dies outside the Nine Hells, its body disappears in sulfurous smoke, and it gains a new body instantly, reviving with all its Hit Points somewhere in the Nine Hells.",
    ),
    (
        (
            "Monsters A–Z",
            "Chain Devil",
            "Chain Devil",
            "Traits",
        ),
        "**_Magic Resistance._** The devil has Advantage on saving throws against spells and other magical effects.",
    ),
    (
        (
            "Monsters A–Z",
            "Chain Devil",
            "Chain Devil",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Chain Devil",
            "Chain Devil",
            "Actions",
        ),
        "**_Multiattack._** The devil makes two Chain attacks and uses Conjure Infernal Chain.",
    ),
    (
        (
            "Monsters A–Z",
            "Chain Devil",
            "Chain Devil",
            "Actions",
        ),
        "**_Chain._** _Melee Attack Roll:_ +7, reach 10 ft. _Hit:_ 11 (2d6 + 4) Slashing damage. If the target is a Large or smaller creature, it has the Grappled condition (escape DC 14) from one of two chains, and it has the Restrained condition until the grapple ends.",
    ),
    (
        (
            "Monsters A–Z",
            "Chain Devil",
            "Chain Devil",
            "Actions",
        ),
        "**_Conjure Infernal Chain._** The devil conjures a fiery chain to bind a creature. _Dexterity Saving Throw:_ DC 15, one creature the devil can see within 60 feet. _Failure:_ 9 (2d4 + 4) Fire damage, and the target has the Restrained condition until the end of the devil's next turn, at which point the chain disappears. If the target is Large or smaller, the devil moves the target up to 30 feet straight toward itself. _Success:_ The chain disappears.",
    ),
    (
        (
            "Monsters A–Z",
            "Chain Devil",
            "Chain Devil",
            "Reactions",
        ),
        "#### Reactions",
    ),
    (
        (
            "Monsters A–Z",
            "Chain Devil",
            "Chain Devil",
            "Reactions",
        ),
        "**_Unnerving Gaze._** _Trigger:_ A creature the devil can see starts its turn within 30 feet of the devil and can see the devil. _Response—Wisdom Saving Throw:_ DC 15, the triggering creature. _Failure:_ The target has the Frightened condition until the end of its turn. _Success:_ The target is immune to this devil's Unnerving Gaze for 24 hours.",
    ),
    (
        (
            "Monsters A–Z",
            "Chimera",
        ),
        "## Chimera",
    ),
    (
        (
            "Monsters A–Z",
            "Chimera",
            "Chimera",
        ),
        "### Chimera",
    ),
    (
        (
            "Monsters A–Z",
            "Chimera",
            "Chimera",
        ),
        "_Large Monstrosity, Chaotic Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Chimera",
            "Chimera",
        ),
        "**AC** 14 **Initiative** +0 (10) <br>\n**HP** 114 (12d10 + 48) <br>\n**Speed** 30 ft., Fly 60 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Chimera",
            "Chimera",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>19</td>\n      <td>+4</td>\n      <td>+4</td>\n      <td><strong>DEX</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CON</strong></td>\n      <td>19</td>\n      <td>+4</td>\n      <td>+4</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>3</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>WIS</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CHA</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Chimera",
            "Chimera",
        ),
        "**Skills** Perception +8<br>\n**Senses** Darkvision 60 ft.; Passive Perception 18<br>\n**Languages** Understands Draconic but can't speak<br>\n**CR** 6 (XP 2,300; PB +3)",
    ),
    (
        (
            "Monsters A–Z",
            "Chimera",
            "Chimera",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Chimera",
            "Chimera",
            "Actions",
        ),
        "**_Multiattack._** The chimera makes one Ram attack, one Bite attack, and one Claw attack. It can replace the Claw attack with a use of Fire Breath if available.",
    ),
    (
        (
            "Monsters A–Z",
            "Chimera",
            "Chimera",
            "Actions",
        ),
        "**_Bite._** _Melee Attack Roll:_ +7, reach 5 ft. _Hit:_ 11 (2d6 + 4) Piercing damage, or 18 (4d6 + 4) Piercing damage if the chimera had Advantage on the attack roll.",
    ),
    (
        (
            "Monsters A–Z",
            "Chimera",
            "Chimera",
            "Actions",
        ),
        "**_Claw._** _Melee Attack Roll:_ +7, reach 5 ft. _Hit:_ 7 (1d6 + 4) Slashing damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Chimera",
            "Chimera",
            "Actions",
        ),
        "**_Ram._** _Melee Attack Roll:_ +7, reach 5 ft. _Hit:_ 10 (1d12 + 4) Bludgeoning damage. If the target is a Medium or smaller creature, it has the Prone condition.",
    ),
    (
        (
            "Monsters A–Z",
            "Chimera",
            "Chimera",
            "Actions",
        ),
        "**_Fire Breath (Recharge 5–6)._** _Dexterity Saving Throw:_ DC 15, each creature in a 15-foot Cone. _Failure:_ 31 (7d8) Fire damage. _Success:_ Half damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Chuul",
        ),
        "## Chuul",
    ),
    (
        (
            "Monsters A–Z",
            "Chuul",
            "Chuul",
        ),
        "### Chuul",
    ),
    (
        (
            "Monsters A–Z",
            "Chuul",
            "Chuul",
        ),
        "_Large Aberration, Chaotic Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Chuul",
            "Chuul",
        ),
        "**AC** 16 **Initiative** +0 (10) <br>\n**HP** 76 (9d10 + 27) <br>\n**Speed** 30 ft., Swim 30 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Chuul",
            "Chuul",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>19</td>\n      <td>+4</td>\n      <td>+4</td>\n      <td><strong>DEX</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CON</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>5</td>\n      <td>−3</td>\n      <td>−3</td>\n      <td><strong>WIS</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CHA</strong></td>\n      <td>5</td>\n      <td>−3</td>\n      <td>−3</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Chuul",
            "Chuul",
        ),
        "**Skills** Perception +4<br>\n**Immunities** Poison; Poisoned<br>\n**Senses** Darkvision 60 ft.; Passive Perception 14<br>\n**Languages** Understands Deep Speech but can't speak<br>\n**CR** 4 (XP 1,100; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Chuul",
            "Chuul",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Chuul",
            "Chuul",
            "Traits",
        ),
        "**_Amphibious._** The chuul can breathe air and water.",
    ),
    (
        (
            "Monsters A–Z",
            "Chuul",
            "Chuul",
            "Traits",
        ),
        "**_Sense Magic._** The chuul senses magic within 120 feet of itself. This trait otherwise works like the _Detect Magic_ spell but isn't itself magical.",
    ),
    (
        (
            "Monsters A–Z",
            "Chuul",
            "Chuul",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Chuul",
            "Chuul",
            "Actions",
        ),
        "**_Multiattack._** The chuul makes two Pincer attacks and uses Paralyzing Tentacles.",
    ),
    (
        (
            "Monsters A–Z",
            "Chuul",
            "Chuul",
            "Actions",
        ),
        "**_Pincer._** _Melee Attack Roll:_ +6, reach 10 ft. _Hit:_ 9 (1d10 + 4) Bludgeoning damage. If the target is a Large or smaller creature, it has the Grappled condition (escape DC 14) from one of two pincers.",
    ),
    (
        (
            "Monsters A–Z",
            "Chuul",
            "Chuul",
            "Actions",
        ),
        "**_Paralyzing Tentacles._** _Constitution Saving Throw:_ DC 13, one creature Grappled by the chuul. _Failure:_ The target has the Poisoned condition and repeats the save at the end of each of its turns, ending the effect on itself on a success. After 1 minute, it succeeds automatically. While Poisoned, the target has the Paralyzed condition.",
    ),
    (
        (
            "Monsters A–Z",
            "Clay Golem",
        ),
        "## Clay Golem",
    ),
    (
        (
            "Monsters A–Z",
            "Clay Golem",
            "Clay Golem",
        ),
        "### Clay Golem",
    ),
    (
        (
            "Monsters A–Z",
            "Clay Golem",
            "Clay Golem",
        ),
        "_Large Construct, Unaligned_",
    ),
    (
        (
            "Monsters A–Z",
            "Clay Golem",
            "Clay Golem",
        ),
        "**AC** 14 **Initiative** +3 (13) <br>\n**HP** 123 (13d10 + 52) <br>\n**Speed** 30 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Clay Golem",
            "Clay Golem",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>20</td>\n      <td>+5</td>\n      <td>+5</td>\n      <td><strong>DEX</strong></td>\n      <td>9</td>\n      <td>−1</td>\n      <td>−1</td>\n      <td><strong>CON</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+4</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>3</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>WIS</strong></td>\n      <td>8</td>\n      <td>−1</td>\n      <td>−1</td>\n      <td><strong>CHA</strong></td>\n      <td>1</td>\n      <td>−5</td>\n      <td>−5</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Clay Golem",
            "Clay Golem",
        ),
        "**Resistances** Bludgeoning, Piercing, Slashing<br>\n**Immunities** Acid, Poison, Psychic; Charmed, Exhaustion, Frightened, Paralyzed, Petrified, Poisoned<br>\n**Senses** Darkvision 60 ft.; Passive Perception 9<br>\n**Languages** Common plus one other language<br>\n**CR** 9 (XP 5,000; PB +4)",
    ),
    (
        (
            "Monsters A–Z",
            "Clay Golem",
            "Clay Golem",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Clay Golem",
            "Clay Golem",
            "Traits",
        ),
        "**_Acid Absorption._** Whenever the golem is subjected to Acid damage, it takes no damage and instead regains a number of Hit Points equal to the Acid damage dealt.",
    ),
    (
        (
            "Monsters A–Z",
            "Clay Golem",
            "Clay Golem",
            "Traits",
        ),
        "**_Berserk._** Whenever the golem starts its turn Bloodied, roll 1d6. On a 6, the golem goes berserk. On each of its turns while berserk, the golem attacks the nearest creature it can see. If no creature is near enough to move to and attack, the golem attacks an object. Once the golem goes berserk, it continues to be berserk until it is destroyed or it is no longer Bloodied.",
    ),
    (
        (
            "Monsters A–Z",
            "Clay Golem",
            "Clay Golem",
            "Traits",
        ),
        "**_Immutable Form._** The golem can't shape-shift.",
    ),
    (
        (
            "Monsters A–Z",
            "Clay Golem",
            "Clay Golem",
            "Traits",
        ),
        "**_Magic Resistance._** The golem has Advantage on saving throws against spells and other magical effects.",
    ),
    (
        (
            "Monsters A–Z",
            "Clay Golem",
            "Clay Golem",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Clay Golem",
            "Clay Golem",
            "Actions",
        ),
        "**_Multiattack._** The golem makes two Slam attacks, or it makes three Slam attacks if it used Hasten this turn.",
    ),
    (
        (
            "Monsters A–Z",
            "Clay Golem",
            "Clay Golem",
            "Actions",
        ),
        "**_Slam._** _Melee Attack Roll:_ +9, reach 5 ft. _Hit:_ 10 (1d10 + 5) Bludgeoning damage plus 6 (1d12) Acid damage, and the target's Hit Point maximum decreases by an amount equal to the Acid damage taken.",
    ),
    (
        (
            "Monsters A–Z",
            "Clay Golem",
            "Clay Golem",
            "Bonus Actions",
        ),
        "#### Bonus Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Clay Golem",
            "Clay Golem",
            "Bonus Actions",
        ),
        "**_Hasten (Recharge 5–6)._** The golem takes the Dash and Disengage actions.",
    ),
    (
        (
            "Monsters A–Z",
            "Cloaker",
        ),
        "## Cloaker",
    ),
    (
        (
            "Monsters A–Z",
            "Cloaker",
            "Cloaker",
        ),
        "### Cloaker",
    ),
    (
        (
            "Monsters A–Z",
            "Cloaker",
            "Cloaker",
        ),
        "_Large Aberration, Chaotic Neutral_",
    ),
    (
        (
            "Monsters A–Z",
            "Cloaker",
            "Cloaker",
        ),
        "**AC** 14 **Initiative** +5 (15) <br>\n**HP** 91 (14d10 + 14) <br>\n**Speed** 10 ft., Fly 40 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Cloaker",
            "Cloaker",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>17</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>DEX</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CON</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>WIS</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CHA</strong></td>\n      <td>7</td>\n      <td>−2</td>\n      <td>−2</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Cloaker",
            "Cloaker",
        ),
        "**Skills** Stealth +5<br>\n**Immunities** Frightened<br>\n**Senses** Darkvision 120 ft.; Passive Perception 12<br>\n**Languages** Deep Speech, Undercommon<br>\n**CR** 8 (XP 3,900; PB +3)",
    ),
    (
        (
            "Monsters A–Z",
            "Cloaker",
            "Cloaker",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Cloaker",
            "Cloaker",
            "Traits",
        ),
        "**_Light Sensitivity._** While in Bright Light, the cloaker has Disadvantage on attack rolls.",
    ),
    (
        (
            "Monsters A–Z",
            "Cloaker",
            "Cloaker",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Cloaker",
            "Cloaker",
            "Actions",
        ),
        "**_Multiattack._** The cloaker makes one Attach attack and two Tail attacks.",
    ),
    (
        (
            "Monsters A–Z",
            "Cloaker",
            "Cloaker",
            "Actions",
        ),
        "**_Attach._** _Melee Attack Roll:_ +6, reach 5 ft. _Hit:_ 13 (3d6 + 3) Piercing damage. If the target is a Large or smaller creature, the cloaker attaches to it. While the cloaker is attached, the target has the Blinded condition, and the cloaker can't make Attach attacks against other targets. In addition, the cloaker halves the damage it takes (round down), and the target takes the same amount of damage. <br>\n&emsp;The cloaker can detach itself by spending 5 feet of movement. The target or a creature within 5 feet of it can take an action to try to detach the cloaker, doing so by succeeding on a DC 14 Strength (Athletics) check.",
    ),
    (
        (
            "Monsters A–Z",
            "Cloaker",
            "Cloaker",
            "Actions",
        ),
        "**_Tail._** _Melee Attack Roll:_ +6, reach 10 ft. _Hit:_ 8 (1d10 + 3) Slashing damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Cloaker",
            "Cloaker",
            "Bonus Actions",
        ),
        "#### Bonus Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Cloaker",
            "Cloaker",
            "Bonus Actions",
        ),
        "**_Moan._** _Wisdom Saving Throw:_ DC 13, each creature in a 60-foot Emanation originating from the cloaker. _Failure:_ The target has the Frightened condition until the end of the cloaker's next turn. _Success:_ The target is immune to this cloaker's Moan for the next 24 hours.",
    ),
    (
        (
            "Monsters A–Z",
            "Cloaker",
            "Cloaker",
            "Bonus Actions",
        ),
        "**_Phantasms (Recharge after a Short or Long Rest)._** The cloaker casts the _Mirror Image_ spell, requiring no spell components and using Wisdom as the spellcasting ability. The spell ends early if the cloaker starts or ends its turn in Bright Light.",
    ),
    (
        (
            "Monsters A–Z",
            "Cloud Giant",
        ),
        "## Cloud Giant",
    ),
    (
        (
            "Monsters A–Z",
            "Cloud Giant",
            "Cloud Giant",
        ),
        "### Cloud Giant",
    ),
    (
        (
            "Monsters A–Z",
            "Cloud Giant",
            "Cloud Giant",
        ),
        "_Huge Giant, Neutral_",
    ),
    (
        (
            "Monsters A–Z",
            "Cloud Giant",
            "Cloud Giant",
        ),
        "**AC** 14 **Initiative** +4 (14) <br>\n**HP** 200 (16d12 + 96) <br>\n**Speed** 40 ft., Fly 20 ft. (hover) <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Cloud Giant",
            "Cloud Giant",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>27</td>\n      <td>+8</td>\n      <td>+8</td>\n      <td><strong>DEX</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CON</strong></td>\n      <td>22</td>\n      <td>+6</td>\n      <td>+10</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>WIS</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+7</td>\n      <td><strong>CHA</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Cloud Giant",
            "Cloud Giant",
        ),
        "**Skills** Insight +7, Perception +11<br>\n**Senses** Passive Perception 21<br>\n**Languages** Common, Giant<br>\n**CR** 9 (XP 5,000; PB +4)",
    ),
    (
        (
            "Monsters A–Z",
            "Cloud Giant",
            "Cloud Giant",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Cloud Giant",
            "Cloud Giant",
            "Actions",
        ),
        "**_Multiattack._** The giant makes two attacks, using Thunderous Mace or Thundercloud in any combination. It can replace one attack with a use of Spellcasting to cast _Fog Cloud_.",
    ),
    (
        (
            "Monsters A–Z",
            "Cloud Giant",
            "Cloud Giant",
            "Actions",
        ),
        "**_Thunderous Mace._** _Melee Attack Roll:_ +12, reach 10 ft. _Hit:_ 21 (3d8 + 8) Bludgeoning damage plus 7 (2d6) Thunder damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Cloud Giant",
            "Cloud Giant",
            "Actions",
        ),
        "**_Thundercloud._** _Ranged Attack Roll:_ +12, range 240 ft. _Hit:_ 18 (3d6 + 8) Thunder damage, and the target has the Incapacitated condition until the end of its next turn.",
    ),
    (
        (
            "Monsters A–Z",
            "Cloud Giant",
            "Cloud Giant",
            "Actions",
        ),
        "**_Spellcasting._** The giant casts one of the following spells, requiring no Material components and using Charisma as the spellcasting ability (spell save DC 15): <br>\n&emsp;**At Will:** _Detect Magic_, _Fog Cloud_, _Light_ <br>\n&emsp;**1/Day Each:** _Control Weather_, _Gaseous Form_, _Telekinesis_",
    ),
    (
        (
            "Monsters A–Z",
            "Cloud Giant",
            "Cloud Giant",
            "Bonus Actions",
        ),
        "#### Bonus Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Cloud Giant",
            "Cloud Giant",
            "Bonus Actions",
        ),
        "**_Misty Step._** The giant casts the _Misty Step_ spell, using the same spellcasting ability as Spellcasting.",
    ),
    (
        (
            "Monsters A–Z",
            "Cockatrice",
        ),
        "## Cockatrice",
    ),
    (
        (
            "Monsters A–Z",
            "Cockatrice",
            "Cockatrice",
        ),
        "### Cockatrice",
    ),
    (
        (
            "Monsters A–Z",
            "Cockatrice",
            "Cockatrice",
        ),
        "_Small Monstrosity, Unaligned_",
    ),
    (
        (
            "Monsters A–Z",
            "Cockatrice",
            "Cockatrice",
        ),
        "**AC** 11 **Initiative** +1 (11) <br>\n**HP** 22 (5d6 + 5) <br>\n**Speed** 20 ft., Fly 40 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Cockatrice",
            "Cockatrice",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>6</td>\n      <td>−2</td>\n      <td>−2</td>\n      <td><strong>DEX</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CON</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>2</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>WIS</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CHA</strong></td>\n      <td>5</td>\n      <td>−3</td>\n      <td>−3</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Cockatrice",
            "Cockatrice",
        ),
        "**Immunities** Petrified<br>\n**Senses** Darkvision 60 ft.; Passive Perception 11<br>\n**Languages** None<br>\n**CR** 1/2 (XP 100; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Cockatrice",
            "Cockatrice",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Cockatrice",
            "Cockatrice",
            "Actions",
        ),
        "**_Petrifying Bite._** _Melee Attack Roll:_ +3, reach 5 ft. _Hit:_ 3 (1d4 + 1) Piercing damage. If the target is a creature, it is subjected to the following effect. _Constitution Saving Throw:_ DC 11. _First Failure:_ The target has the Restrained condition. The target repeats the save at the end of its next turn if it is still Restrained, ending the effect on itself on a success. _Second Failure:_ The target has the Petrified condition, instead of the Restrained condition, for 24 hours.",
    ),
    (
        (
            "Monsters A–Z",
            "Commoner",
        ),
        "## Commoner",
    ),
    (
        (
            "Monsters A–Z",
            "Commoner",
            "Commoner",
        ),
        "### Commoner",
    ),
    (
        (
            "Monsters A–Z",
            "Commoner",
            "Commoner",
        ),
        "_Medium or Small Humanoid, Neutral_",
    ),
    (
        (
            "Monsters A–Z",
            "Commoner",
            "Commoner",
        ),
        "**AC** 10 **Initiative** +0 (10) <br>\n**HP** 4 (1d8) <br>\n**Speed** 30 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Commoner",
            "Commoner",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>DEX</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CON</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>WIS</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CHA</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Commoner",
            "Commoner",
        ),
        "**Gear** Club<br>\n**Senses** Passive Perception 10<br>\n**Languages** Common<br>\n**CR** 0 (XP 10; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Commoner",
            "Commoner",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Commoner",
            "Commoner",
            "Traits",
        ),
        "**_Training._** The commoner has proficiency in one skill of the GM's choice and has Advantage whenever it makes an ability check using that skill.",
    ),
    (
        (
            "Monsters A–Z",
            "Commoner",
            "Commoner",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Commoner",
            "Commoner",
            "Actions",
        ),
        "**_Club._** _Melee Attack Roll:_ +2, reach 5 ft. _Hit:_ 2 (1d4) Bludgeoning damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Copper Dragons",
        ),
        "## Copper Dragons",
    ),
    (
        (
            "Monsters A–Z",
            "Copper Dragons",
            "Copper Dragon Wyrmling",
        ),
        "### Copper Dragon Wyrmling",
    ),
    (
        (
            "Monsters A–Z",
            "Copper Dragons",
            "Copper Dragon Wyrmling",
        ),
        "_Medium Dragon (Metallic), Chaotic Good_",
    ),
    (
        (
            "Monsters A–Z",
            "Copper Dragons",
            "Copper Dragon Wyrmling",
        ),
        "**AC** 16 **Initiative** +3 (13) <br>\n**HP** 22 (4d8 + 4) <br>\n**Speed** 30 ft., Climb 30 ft., Fly 60 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Copper Dragons",
            "Copper Dragon Wyrmling",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>DEX</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+3</td>\n      <td><strong>CON</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>WIS</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+2</td>\n      <td><strong>CHA</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Copper Dragons",
            "Copper Dragon Wyrmling",
        ),
        "**Skills** Perception +4, Stealth +3<br>\n**Immunities** Acid<br>\n**Senses** Blindsight 10 ft., Darkvision 60 ft.; Passive Perception 14<br>\n**Languages** Draconic<br>\n**CR** 1 (XP 200; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Copper Dragons",
            "Copper Dragon Wyrmling",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Copper Dragons",
            "Copper Dragon Wyrmling",
            "Actions",
        ),
        "**_Rend._** _Melee Attack Roll:_ +4, reach 5 ft. _Hit:_ 7 (1d10 + 2) Slashing damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Copper Dragons",
            "Copper Dragon Wyrmling",
            "Actions",
        ),
        "**_Acid Breath (Recharge 5–6)._** _Dexterity Saving Throw:_ DC 11, each creature in a 20-foot-long, 5-foot-wide Line. _Failure:_ 18 (4d8) Acid damage. _Success:_ Half damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Copper Dragons",
            "Copper Dragon Wyrmling",
            "Actions",
        ),
        "**_Slowing Breath._** _Constitution Saving Throw:_ DC 11, each creature in a 15-foot Cone. _Failure:_ The target can't take Reactions; its Speed is halved; and it can take either an action or a Bonus Action on its turn, not both. This effect lasts until the end of its next turn.",
    ),
    (
        (
            "Monsters A–Z",
            "Copper Dragons",
            "Young Copper Dragon",
        ),
        "### Young Copper Dragon",
    ),
    (
        (
            "Monsters A–Z",
            "Copper Dragons",
            "Young Copper Dragon",
        ),
        "_Large Dragon (Metallic), Chaotic Good_",
    ),
    (
        (
            "Monsters A–Z",
            "Copper Dragons",
            "Young Copper Dragon",
        ),
        "**AC** 17 **Initiative** +4 (14) <br>\n**HP** 119 (14d10 + 42) <br>\n**Speed** 40 ft., Climb 40 ft., Fly 80 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Copper Dragons",
            "Young Copper Dragon",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>19</td>\n      <td>+4</td>\n      <td>+4</td>\n      <td><strong>DEX</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+4</td>\n      <td><strong>CON</strong></td>\n      <td>17</td>\n      <td>+3</td>\n      <td>+3</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>WIS</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+4</td>\n      <td><strong>CHA</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Copper Dragons",
            "Young Copper Dragon",
        ),
        "**Skills** Deception +5, Perception +7, Stealth +4<br>\n**Immunities** Acid<br>\n**Senses** Blindsight 30 ft., Darkvision 120 ft.; Passive Perception 17<br>\n**Languages** Common, Draconic<br>\n**CR** 7 (XP 2,900; PB +3)",
    ),
    (
        (
            "Monsters A–Z",
            "Copper Dragons",
            "Young Copper Dragon",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Copper Dragons",
            "Young Copper Dragon",
            "Actions",
        ),
        "**_Multiattack._** The dragon makes three Rend attacks. It can replace one attack with a use of Slowing Breath.",
    ),
    (
        (
            "Monsters A–Z",
            "Copper Dragons",
            "Young Copper Dragon",
            "Actions",
        ),
        "**_Rend._** _Melee Attack Roll:_ +7, reach 10 ft. _Hit:_ 15 (2d10 + 4) Slashing damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Copper Dragons",
            "Young Copper Dragon",
            "Actions",
        ),
        "**_Acid Breath (Recharge 5–6)._** _Dexterity Saving Throw:_ DC 14, each creature in a 40-foot-long, 5-foot-wide Line. _Failure:_ 40 (9d8) Acid damage. _Success:_ Half damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Copper Dragons",
            "Young Copper Dragon",
            "Actions",
        ),
        "**_Slowing Breath._** _Constitution Saving Throw:_ DC 14, each creature in a 30-foot Cone. _Failure:_ The target can't take Reactions; its Speed is halved; and it can take either an action or a Bonus Action on its turn, not both. This effect lasts until the end of its next turn.",
    ),
    (
        (
            "Monsters A–Z",
            "Copper Dragons",
            "Adult Copper Dragon",
        ),
        "### Adult Copper Dragon",
    ),
    (
        (
            "Monsters A–Z",
            "Copper Dragons",
            "Adult Copper Dragon",
        ),
        "_Huge Dragon (Metallic), Chaotic Good_",
    ),
    (
        (
            "Monsters A–Z",
            "Copper Dragons",
            "Adult Copper Dragon",
        ),
        "**AC** 18 **Initiative** +11 (21) <br>\n**HP** 184 (16d12 + 80) <br>\n**Speed** 40 ft., Climb 40 ft., Fly 80 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Copper Dragons",
            "Adult Copper Dragon",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>23</td>\n      <td>+6</td>\n      <td>+6</td>\n      <td><strong>DEX</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+6</td>\n      <td><strong>CON</strong></td>\n      <td>21</td>\n      <td>+5</td>\n      <td>+5</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+4</td>\n      <td><strong>WIS</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+7</td>\n      <td><strong>CHA</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+4</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Copper Dragons",
            "Adult Copper Dragon",
        ),
        "**Skills** Deception +9, Perception +12, Stealth +6<br>\n**Immunities** Acid<br>\n**Senses** Blindsight 60 ft., Darkvision 120 ft.; Passive Perception 22<br>\n**Languages** Common, Draconic<br>\n**CR** 14 (XP 11,500, or 13,000 in lair; PB +5)",
    ),
    (
        (
            "Monsters A–Z",
            "Copper Dragons",
            "Adult Copper Dragon",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Copper Dragons",
            "Adult Copper Dragon",
            "Traits",
        ),
        "**_Legendary Resistance (3/Day, or 4/Day in Lair)._** If the dragon fails a saving throw, it can choose to succeed instead.",
    ),
    (
        (
            "Monsters A–Z",
            "Copper Dragons",
            "Adult Copper Dragon",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Copper Dragons",
            "Adult Copper Dragon",
            "Actions",
        ),
        "**_Multiattack._** The dragon makes three Rend attacks. It can replace one attack with a use of (A) Slowing Breath or (B) Spellcasting to cast _Mind Spike_ (level 4 version).",
    ),
    (
        (
            "Monsters A–Z",
            "Copper Dragons",
            "Adult Copper Dragon",
            "Actions",
        ),
        "**_Rend._** _Melee Attack Roll:_ +11, reach 10 ft. _Hit:_ 17 (2d10 + 6) Slashing damage plus 4 (1d8) Acid damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Copper Dragons",
            "Adult Copper Dragon",
            "Actions",
        ),
        "**_Acid Breath (Recharge 5–6)._** _Dexterity Saving Throw:_ DC 18, each creature in an 60-foot-long, 5-foot-wide Line. _Failure:_ 54 (12d8) Acid damage. _Success:_ Half damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Copper Dragons",
            "Adult Copper Dragon",
            "Actions",
        ),
        "**_Slowing Breath._** _Constitution Saving Throw:_ DC 18, each creature in a 60-foot Cone. _Failure:_ The target can't take Reactions; its Speed is halved; and it can take either an action or a Bonus Action on its turn, not both. This effect lasts until the end of its next turn.",
    ),
    (
        (
            "Monsters A–Z",
            "Copper Dragons",
            "Adult Copper Dragon",
            "Actions",
        ),
        "**_Spellcasting._** The dragon casts one of the following spells, requiring no Material components and using Charisma as the spellcasting ability (spell save DC 17): <br>\n&emsp;**At Will:** _Detect Magic_, _Mind Spike_ (level 4 version), _Minor Illusion_, _Shapechange_ (Beast or Humanoid form only, no Temporary Hit Points gained from the spell, and no Concentration or Temporary Hit Points required to maintain the spell) <br>\n&emsp;**1/Day Each:** _Greater Restoration_, _Major Image_",
    ),
    (
        (
            "Monsters A–Z",
            "Copper Dragons",
            "Adult Copper Dragon",
            "Legendary Actions",
        ),
        "#### Legendary Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Copper Dragons",
            "Adult Copper Dragon",
            "Legendary Actions",
        ),
        "_Legendary Action Uses: 3 (4 in Lair). Immediately after another creature's turn, the dragon can expend a use to take one of the following actions. The dragon regains all expended uses at the start of each of its turns._",
    ),
    (
        (
            "Monsters A–Z",
            "Copper Dragons",
            "Adult Copper Dragon",
            "Legendary Actions",
        ),
        "**_Giggling Magic._** _Charisma Saving Throw:_ DC 17, one creature the dragon can see within 90 feet. _Failure:_ 24 (7d6) Psychic damage. Until the end of its next turn, the target rolls 1d6 whenever it makes an ability check or attack roll and subtracts the number rolled from the D20 Test. _Failure or Success:_ The dragon can't take this action again until the start of its next turn.",
    ),
    (
        (
            "Monsters A–Z",
            "Copper Dragons",
            "Adult Copper Dragon",
            "Legendary Actions",
        ),
        "**_Mind Jolt._** The dragon uses Spellcasting to cast _Mind Spike_ (level 4 version). The dragon can't take this action again until the start of its next turn.",
    ),
    (
        (
            "Monsters A–Z",
            "Copper Dragons",
            "Adult Copper Dragon",
            "Legendary Actions",
        ),
        "**_Pounce._** The dragon moves up to half its Speed, and it makes one Rend attack.",
    ),
    (
        (
            "Monsters A–Z",
            "Copper Dragons",
            "Ancient Copper Dragon",
        ),
        "### Ancient Copper Dragon",
    ),
    (
        (
            "Monsters A–Z",
            "Copper Dragons",
            "Ancient Copper Dragon",
        ),
        "_Gargantuan Dragon (Metallic), Chaotic Good_",
    ),
    (
        (
            "Monsters A–Z",
            "Copper Dragons",
            "Ancient Copper Dragon",
        ),
        "**AC** 21 **Initiative** +15 (25) <br>\n**HP** 367 (21d20 + 147) <br>\n**Speed** 40 ft., Climb 40 ft., Fly 80 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Copper Dragons",
            "Ancient Copper Dragon",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>27</td>\n      <td>+8</td>\n      <td>+8</td>\n      <td><strong>DEX</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+8</td>\n      <td><strong>CON</strong></td>\n      <td>25</td>\n      <td>+7</td>\n      <td>+7</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>20</td>\n      <td>+5</td>\n      <td>+5</td>\n      <td><strong>WIS</strong></td>\n      <td>17</td>\n      <td>+3</td>\n      <td>+10</td>\n      <td><strong>CHA</strong></td>\n      <td>22</td>\n      <td>+6</td>\n      <td>+6</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Copper Dragons",
            "Ancient Copper Dragon",
        ),
        "**Skills** Deception +13, Perception +17, Stealth +8<br>\n**Immunities** Acid<br>\n**Senses** Blindsight 60 ft., Darkvision 120 ft.; Passive Perception 27<br>\n**Languages** Common, Draconic<br>\n**CR** 21 (XP 33,000, or 41,000 in lair; PB +7)",
    ),
    (
        (
            "Monsters A–Z",
            "Copper Dragons",
            "Ancient Copper Dragon",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Copper Dragons",
            "Ancient Copper Dragon",
            "Traits",
        ),
        "**_Legendary Resistance (4/Day, or 5/Day in Lair)._** If the dragon fails a saving throw, it can choose to succeed instead.",
    ),
    (
        (
            "Monsters A–Z",
            "Copper Dragons",
            "Ancient Copper Dragon",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Copper Dragons",
            "Ancient Copper Dragon",
            "Actions",
        ),
        "**_Multiattack._** The dragon makes three Rend attacks. It can replace one attack with a use of (A) Slowing Breath or (B) Spellcasting to cast _Mind Spike_ (level 5 version).",
    ),
    (
        (
            "Monsters A–Z",
            "Copper Dragons",
            "Ancient Copper Dragon",
            "Actions",
        ),
        "**_Rend._** _Melee Attack Roll:_ +15, reach 15 ft. _Hit:_ 19 (2d10 + 8) Slashing damage plus 9 (2d8) Acid damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Copper Dragons",
            "Ancient Copper Dragon",
            "Actions",
        ),
        "**_Acid Breath (Recharge 5–6)._** _Dexterity Saving Throw:_ DC 22, each creature in an 90-foot-long, 10-foot-wide Line. _Failure:_ 63 (14d8) Acid damage. _Success:_ Half damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Copper Dragons",
            "Ancient Copper Dragon",
            "Actions",
        ),
        "**_Slowing Breath._** _Constitution Saving Throw:_ DC 22, each creature in a 90-foot Cone. _Failure:_ The target can't take Reactions; its Speed is halved; and it can take either an action or a Bonus Action on its turn, not both. This effect lasts until the end of its next turn.",
    ),
    (
        (
            "Monsters A–Z",
            "Copper Dragons",
            "Ancient Copper Dragon",
            "Actions",
        ),
        "**_Spellcasting._** The dragon casts one of the following spells, requiring no Material components and using Charisma as the spellcasting ability (spell save DC 21): <br>\n&emsp;**At Will:** _Detect Magic, Mind Spike_ (level 5 version), _Minor Illusion, Shapechange_ (Beast or Humanoid form only, no Temporary Hit Points gained from the spell, and no Concentration or Temporary Hit Points required to maintain the spell) <br>\n&emsp;**1/Day Each:** _Greater Restoration, Major Image, Project Image_",
    ),
    (
        (
            "Monsters A–Z",
            "Copper Dragons",
            "Ancient Copper Dragon",
            "Legendary Actions",
        ),
        "#### Legendary Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Copper Dragons",
            "Ancient Copper Dragon",
            "Legendary Actions",
        ),
        "_Legendary Action Uses: 3 (4 in Lair). Immediately after another creature's turn, the dragon can expend a use to take one of the following actions. The dragon regains all expended uses at the start of each of its turns._",
    ),
    (
        (
            "Monsters A–Z",
            "Copper Dragons",
            "Ancient Copper Dragon",
            "Legendary Actions",
        ),
        "**_Giggling Magic._** _Charisma Saving Throw:_ DC 21, one creature the dragon can see within 120 feet. _Failure:_ 31 (9d6) Psychic damage. Until the end of its next turn, the target rolls 1d8 whenever it makes an ability check or attack roll and subtracts the number rolled from the D20 Test. _Failure or Success:_ The dragon can't take this action again until the start of its next turn.",
    ),
    (
        (
            "Monsters A–Z",
            "Copper Dragons",
            "Ancient Copper Dragon",
            "Legendary Actions",
        ),
        "**_Mind Jolt._** The dragon uses Spellcasting to cast _Mind Spike_ (level 5 version). The dragon can't take this action again until the start of its next turn.",
    ),
    (
        (
            "Monsters A–Z",
            "Copper Dragons",
            "Ancient Copper Dragon",
            "Legendary Actions",
        ),
        "**_Pounce._** The dragon moves up to half its Speed, and it makes one Rend attack.",
    ),
    (
        (
            "Monsters A–Z",
            "Couatl",
        ),
        "## Couatl",
    ),
    (
        (
            "Monsters A–Z",
            "Couatl",
            "Couatl",
        ),
        "### Couatl",
    ),
    (
        (
            "Monsters A–Z",
            "Couatl",
            "Couatl",
        ),
        "_Medium Celestial, Lawful Good_",
    ),
    (
        (
            "Monsters A–Z",
            "Couatl",
            "Couatl",
        ),
        "**AC** 19 **Initiative** +5 (15) <br>\n**HP** 60 (8d8 + 24) <br>\n**Speed** 30 ft., Fly 90 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Couatl",
            "Couatl",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>DEX</strong></td>\n      <td>20</td>\n      <td>+5</td>\n      <td>+5</td>\n      <td><strong>CON</strong></td>\n      <td>17</td>\n      <td>+3</td>\n      <td>+5</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+4</td>\n      <td><strong>WIS</strong></td>\n      <td>20</td>\n      <td>+5</td>\n      <td>+7</td>\n      <td><strong>CHA</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+4</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Couatl",
            "Couatl",
        ),
        "**Resistances** Bludgeoning, Piercing, Slashing<br>\n**Immunities** Psychic, Radiant<br>\n**Senses** Truesight 120 ft.; Passive Perception 15<br>\n**Languages** All; telepathy 120 ft.<br>\n**CR** 4 (XP 1,100; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Couatl",
            "Couatl",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Couatl",
            "Couatl",
            "Traits",
        ),
        "**_Shielded Mind._** The couatl's thoughts can't be read by any means, and other creatures can communicate with it telepathically only if it allows them.",
    ),
    (
        (
            "Monsters A–Z",
            "Couatl",
            "Couatl",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Couatl",
            "Couatl",
            "Actions",
        ),
        "**_Bite._** _Melee Attack Roll:_ +7, reach 5 ft. _Hit:_ 11 (1d12 + 5) Piercing damage, and the target has the Poisoned condition until the end of the couatl's next turn.",
    ),
    (
        (
            "Monsters A–Z",
            "Couatl",
            "Couatl",
            "Actions",
        ),
        "**_Constrict._** _Strength Saving Throw:_ DC 15, one Medium or smaller creature the couatl can see within 5 feet. _Failure:_ 8 (1d6 + 5) Bludgeoning damage. The target has the Grappled condition (escape DC 13), and it has the Restrained condition until the grapple ends.",
    ),
    (
        (
            "Monsters A–Z",
            "Couatl",
            "Couatl",
            "Actions",
        ),
        "**_Spellcasting._** The couatl casts one of the following spells, requiring no spell components and using Wisdom as the spellcasting ability (spell save DC 15): <br>\n&emsp;**At Will:** _Detect Evil and Good, Detect Magic, Detect Thoughts, Shapechange_ (Beast or Humanoid form only, no Temporary Hit Points gained from the spell, and no Concentration or Temporary Hit Points required to maintain the spell) <br>\n&emsp;**1/Day Each:** _Create Food and Water_, _Dream_, _Greater Restoration_, _Scrying_, _Sleep_",
    ),
    (
        (
            "Monsters A–Z",
            "Couatl",
            "Couatl",
            "Bonus Actions",
        ),
        "#### Bonus Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Couatl",
            "Couatl",
            "Bonus Actions",
        ),
        "**_Divine Aid (2/Day)._** The couatl casts _Bless_, _Lesser Restoration_, or _Sanctuary_, requiring no spell components and using the same spellcasting ability as Spellcasting.",
    ),
    (
        (
            "Monsters A–Z",
            "Crawling Claw",
        ),
        "## Crawling Claw",
    ),
    (
        (
            "Monsters A–Z",
            "Crawling Claw",
            "Swarm of Crawling Claws",
        ),
        "### Swarm of Crawling Claws",
    ),
    (
        (
            "Monsters A–Z",
            "Crawling Claw",
            "Swarm of Crawling Claws",
        ),
        "_Medium Swarm of Tiny Undead, Neutral Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Crawling Claw",
            "Swarm of Crawling Claws",
        ),
        "**AC** 12 **Initiative** +2 (12) <br>\n**HP** 49 (11d8) <br>\n**Speed** 30 ft., Climb 30 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Crawling Claw",
            "Swarm of Crawling Claws",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>DEX</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CON</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>5</td>\n      <td>−3</td>\n      <td>−3</td>\n      <td><strong>WIS</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CHA</strong></td>\n      <td>4</td>\n      <td>−3</td>\n      <td>−3</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Crawling Claw",
            "Swarm of Crawling Claws",
        ),
        "**Resistances** Bludgeoning, Piercing, Slashing<br>\n**Immunities** Necrotic, Poison; Charmed, Exhaustion, Frightened, Grappled, Incapacitated, Paralyzed, Petrified, Poisoned, Prone, Restrained, Stunned<br>\n**Senses** Blindsight 30 ft.; Passive Perception 10<br>\n**Languages** Understands Common but can't speak<br>\n**CR** 3 (XP 700; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Crawling Claw",
            "Swarm of Crawling Claws",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Crawling Claw",
            "Swarm of Crawling Claws",
            "Traits",
        ),
        "**_Swarm._** The swarm can occupy another creature's space and vice versa, and the swarm can move through any opening large enough for a Tiny creature. The swarm can't regain Hit Points or gain Temporary Hit Points.",
    ),
    (
        (
            "Monsters A–Z",
            "Crawling Claw",
            "Swarm of Crawling Claws",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Crawling Claw",
            "Swarm of Crawling Claws",
            "Actions",
        ),
        "**_Swarm of Grasping Hands._** _Melee Attack Roll:_ +4, reach 5 ft. _Hit:_ 20 (4d8 + 2) Necrotic damage, or 11 (2d8 + 2) Necrotic damage if the swarm is Bloodied. If the target is a Medium or smaller creature, it has the Prone condition.",
    ),
    (
        (
            "Monsters A–Z",
            "Cultists",
        ),
        "## Cultists",
    ),
    (
        (
            "Monsters A–Z",
            "Cultists",
            "Cultist",
        ),
        "### Cultist",
    ),
    (
        (
            "Monsters A–Z",
            "Cultists",
            "Cultist",
        ),
        "_Medium or Small Humanoid, Neutral_",
    ),
    (
        (
            "Monsters A–Z",
            "Cultists",
            "Cultist",
        ),
        "**AC** 12 **Initiative** +1 (11) <br>\n**HP** 9 (2d8) <br>\n**Speed** 30 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Cultists",
            "Cultist",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>DEX</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CON</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>WIS</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+2</td>\n      <td><strong>CHA</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Cultists",
            "Cultist",
        ),
        "**Skills** Deception +2, Religion +2<br>\n**Gear** Leather Armor, Sickle<br>\n**Senses** Passive Perception 10<br>\n**Languages** Common<br>\n**CR** 1/8 (XP 25; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Cultists",
            "Cultist",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Cultists",
            "Cultist",
            "Actions",
        ),
        "**_Ritual Sickle._** _Melee Attack Roll:_ +3, reach 5 ft. _Hit:_ 3 (1d4 + 1) Slashing damage plus 1 Necrotic damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Cultists",
            "Cultist Fanatic",
        ),
        "### Cultist Fanatic",
    ),
    (
        (
            "Monsters A–Z",
            "Cultists",
            "Cultist Fanatic",
        ),
        "_Medium or Small Humanoid, Neutral_",
    ),
    (
        (
            "Monsters A–Z",
            "Cultists",
            "Cultist Fanatic",
        ),
        "**AC** 13 **Initiative** +2 (12) <br>\n**HP** 44 (8d8 + 8) <br>\n**Speed** 30 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Cultists",
            "Cultist Fanatic",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>DEX</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CON</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>WIS</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+4</td>\n      <td><strong>CHA</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Cultists",
            "Cultist Fanatic",
        ),
        "**Skills** Deception +3, Persuasion +3, Religion +2<br>\n**Gear** Holy Symbol, Leather Armor<br>\n**Senses** Passive Perception 12<br>\n**Languages** Common<br>\n**CR** 2 (XP 450; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Cultists",
            "Cultist Fanatic",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Cultists",
            "Cultist Fanatic",
            "Actions",
        ),
        "**_Pact Blade._** _Melee Attack Roll:_ +4, reach 5 ft. _Hit:_ 6 (1d8 + 2) Slashing damage plus 7 (2d6) Necrotic damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Cultists",
            "Cultist Fanatic",
            "Actions",
        ),
        "**_Spellcasting._** The cultist casts one of the following spells, using Wisdom as the spellcasting ability (spell save DC 12, +4 to hit with spell attacks): <br>\n&emsp;**At Will:** _Light_, _Thaumaturgy_ <br>\n&emsp;**2/Day:** _Command_ <br>\n&emsp;**1/Day:** _Hold Person_",
    ),
    (
        (
            "Monsters A–Z",
            "Cultists",
            "Cultist Fanatic",
            "Bonus Actions",
        ),
        "#### Bonus Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Cultists",
            "Cultist Fanatic",
            "Bonus Actions",
        ),
        "**_Spiritual Weapon (2/Day)._** The cultist casts the _Spiritual Weapon_ spell, using the same spellcasting ability as Spellcasting.",
    ),
    (
        (
            "Monsters A–Z",
            "Darkmantle",
        ),
        "## Darkmantle",
    ),
    (
        (
            "Monsters A–Z",
            "Darkmantle",
            "Darkmantle",
        ),
        "### Darkmantle",
    ),
    (
        (
            "Monsters A–Z",
            "Darkmantle",
            "Darkmantle",
        ),
        "_Small Aberration, Unaligned_",
    ),
    (
        (
            "Monsters A–Z",
            "Darkmantle",
            "Darkmantle",
        ),
        "**AC** 11 **Initiative** +3 (13) <br>\n**HP** 22 (5d6 + 5) <br>\n**Speed** 10 ft., Fly 30 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Darkmantle",
            "Darkmantle",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>DEX</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CON</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>2</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>WIS</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CHA</strong></td>\n      <td>5</td>\n      <td>−3</td>\n      <td>−3</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Darkmantle",
            "Darkmantle",
        ),
        "**Skills** Stealth +3<br>\n**Senses** Blindsight 60 ft.; Passive Perception 10<br>\n**Languages** None<br>\n**CR** 1/2 (XP 100; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Darkmantle",
            "Darkmantle",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Darkmantle",
            "Darkmantle",
            "Actions",
        ),
        "**_Crush._** _Melee Attack Roll:_ +5, reach 5 ft. _Hit:_ 6 (1d6 + 3) Bludgeoning damage, and the darkmantle attaches to the target. If the target is a Medium or smaller creature and the darkmantle had Advantage on the attack roll, it covers the target, which has the Blinded condition and is suffocating while the darkmantle is attached in this way. <br>\n&emsp;While attached to a target, the darkmantle can attack only the target but has Advantage on its attack rolls. Its Speed becomes 0, it can't benefit from any bonus to its Speed, and it moves with the target. <br>\n&emsp;A creature can take an action to try to detach the darkmantle from itself, doing so with a successful DC 13 Strength (Athletics) check. On its turn, the darkmantle can detach itself by using 5 feet of movement.",
    ),
    (
        (
            "Monsters A–Z",
            "Darkmantle",
            "Darkmantle",
            "Actions",
        ),
        "**_Darkness Aura (1/Day)._** Magical Darkness fills a 15-foot Emanation originating from the darkmantle. This effect lasts while the darkmantle maintains Concentration on it, up to 10 minutes. Darkvision can't penetrate this area, and no light can illuminate it.",
    ),
    (
        (
            "Monsters A–Z",
            "Death Dog",
        ),
        "## Death Dog",
    ),
    (
        (
            "Monsters A–Z",
            "Death Dog",
            "Death Dog",
        ),
        "### Death Dog",
    ),
    (
        (
            "Monsters A–Z",
            "Death Dog",
            "Death Dog",
        ),
        "_Medium Monstrosity, Neutral Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Death Dog",
            "Death Dog",
        ),
        "**AC** 12 **Initiative** +2 (12) <br>\n**HP** 39 (6d8 + 12) <br>\n**Speed** 40 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Death Dog",
            "Death Dog",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>DEX</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CON</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>3</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>WIS</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CHA</strong></td>\n      <td>6</td>\n      <td>−2</td>\n      <td>−2</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Death Dog",
            "Death Dog",
        ),
        "**Skills** Perception +5, Stealth +4<br>\n**Immunities** Blinded, Charmed, Deafened, Frightened, Stunned, Unconscious<br>\n**Senses** Darkvision 120 ft.; Passive Perception 15<br>\n**Languages** None<br>\n**CR** 1 (XP 200; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Death Dog",
            "Death Dog",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Death Dog",
            "Death Dog",
            "Actions",
        ),
        "**_Multiattack._** The death dog makes two Bite attacks.",
    ),
    (
        (
            "Monsters A–Z",
            "Death Dog",
            "Death Dog",
            "Actions",
        ),
        "**_Bite._** _Melee Attack Roll:_ +4, reach 5 ft. _Hit:_ 4 (1d4 + 2) Piercing damage. If the target is a creature, it is subjected to the following effect. _Constitution Saving Throw:_ DC 12. _First Failure:_ The target has the Poisoned condition. While Poisoned, the target's Hit Point maximum doesn't return to normal when finishing a Long Rest, and it repeats the save every 24 hours that elapse, ending the effect on itself on a success. _Subsequent Failures:_ The Poisoned target's Hit Point maximum decreases by 5 (1d10).",
    ),
    (
        (
            "Monsters A–Z",
            "Deva",
        ),
        "## Deva",
    ),
    (
        (
            "Monsters A–Z",
            "Deva",
            "Deva",
        ),
        "### Deva",
    ),
    (
        (
            "Monsters A–Z",
            "Deva",
            "Deva",
        ),
        "_Medium Celestial (Angel), Lawful Good_",
    ),
    (
        (
            "Monsters A–Z",
            "Deva",
            "Deva",
        ),
        "**AC** 17 **Initiative** +4 (14) <br>\n**HP** 229 (27d8 + 108) <br>\n**Speed** 30 ft., Fly 90 ft. (hover) <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Deva",
            "Deva",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+4</td>\n      <td><strong>DEX</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+4</td>\n      <td><strong>CON</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+4</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>17</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>WIS</strong></td>\n      <td>20</td>\n      <td>+5</td>\n      <td>+9</td>\n      <td><strong>CHA</strong></td>\n      <td>20</td>\n      <td>+5</td>\n      <td>+9</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Deva",
            "Deva",
        ),
        "**Skills** Insight +9, Perception +9<br>\n**Resistances** Radiant<br>\n**Immunities** Charmed, Exhaustion, Frightened<br>\n**Senses** Darkvision 120 ft.; Passive Perception 19<br>\n**Languages** All; telepathy 120 ft.<br>\n**CR** 10 (XP 5,900; PB +4)",
    ),
    (
        (
            "Monsters A–Z",
            "Deva",
            "Deva",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Deva",
            "Deva",
            "Traits",
        ),
        "**_Exalted Restoration._** If the deva dies outside Mount Celestia, its body disappears, and it gains a new body instantly, reviving with all its Hit Points somewhere in Mount Celestia.",
    ),
    (
        (
            "Monsters A–Z",
            "Deva",
            "Deva",
            "Traits",
        ),
        "**_Magic Resistance._** The deva has Advantage on saving throws against spells and other magical effects.",
    ),
    (
        (
            "Monsters A–Z",
            "Deva",
            "Deva",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Deva",
            "Deva",
            "Actions",
        ),
        "**_Multiattack._** The deva makes two Holy Mace attacks.",
    ),
    (
        (
            "Monsters A–Z",
            "Deva",
            "Deva",
            "Actions",
        ),
        "**_Holy Mace._** _Melee Attack Roll:_ +8, reach 5 ft. _Hit:_ 7 (1d6 + 4) Bludgeoning damage plus 18 (4d8) Radiant damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Deva",
            "Deva",
            "Actions",
        ),
        "**_Spellcasting._** The deva casts one of the following spells, requiring no Material components and using Charisma as the spellcasting ability (spell save DC 17): <br>\n&emsp;**At Will:** _Detect Evil and Good_, _Shapechange_ (Beast or Humanoid form only, no Temporary Hit Points gained from the spell, and no Concentration or Temporary Hit Points required to maintain the spell) <br>\n&emsp;**1/Day Each:** _Commune_, _Raise Dead_",
    ),
    (
        (
            "Monsters A–Z",
            "Deva",
            "Deva",
            "Bonus Actions",
        ),
        "#### Bonus Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Deva",
            "Deva",
            "Bonus Actions",
        ),
        "**_Divine Aid (2/Day)._** The deva casts _Cure Wounds_, _Lesser Restoration_, or _Remove Curse_, using the same spellcasting ability as Spellcasting.",
    ),
    (
        (
            "Monsters A–Z",
            "Djinni",
        ),
        "## Djinni",
    ),
    (
        (
            "Monsters A–Z",
            "Djinni",
            "Djinni",
        ),
        "### Djinni",
    ),
    (
        (
            "Monsters A–Z",
            "Djinni",
            "Djinni",
        ),
        "_Large Elemental (Genie), Neutral_",
    ),
    (
        (
            "Monsters A–Z",
            "Djinni",
            "Djinni",
        ),
        "**AC** 17 **Initiative** +2 (12) <br>\n**HP** 218 (19d10 + 114) <br>\n**Speed** 30 ft., Fly 90 ft. (hover) <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Djinni",
            "Djinni",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>21</td>\n      <td>+5</td>\n      <td>+5</td>\n      <td><strong>DEX</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+6</td>\n      <td><strong>CON</strong></td>\n      <td>22</td>\n      <td>+6</td>\n      <td>+6</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>WIS</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+7</td>\n      <td><strong>CHA</strong></td>\n      <td>20</td>\n      <td>+5</td>\n      <td>+5</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Djinni",
            "Djinni",
        ),
        "**Immunities** Lightning, Thunder<br>\n**Senses** Darkvision 120 ft.; Passive Perception 13<br>\n**Languages** Primordial (Auran)<br>\n**CR** 11 (XP 7,200; PB +4)",
    ),
    (
        (
            "Monsters A–Z",
            "Djinni",
            "Djinni",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Djinni",
            "Djinni",
            "Traits",
        ),
        "**_Elemental Restoration._** If the djinni dies outside the Elemental Plane of Air, its body dissolves into mist, and it gains a new body in 1d4 days, reviving with all its Hit Points somewhere on the Plane of Air.",
    ),
    (
        (
            "Monsters A–Z",
            "Djinni",
            "Djinni",
            "Traits",
        ),
        "**_Magic Resistance._** The djinni has Advantage on saving throws against spells and other magical effects.",
    ),
    (
        (
            "Monsters A–Z",
            "Djinni",
            "Djinni",
            "Traits",
        ),
        "**_Wishes._** The djinni has a 30 percent chance of knowing the _Wish_ spell. If the djinni knows it, the djinni can cast it only on behalf of a non-genie creature who communicates a wish in a way the djinni can understand. If the djinni casts the spell for the creature, the djinni suffers none of the spell's stress. Once the djinni has cast it three times, the djinni can't do so again for 365 days.",
    ),
    (
        (
            "Monsters A–Z",
            "Djinni",
            "Djinni",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Djinni",
            "Djinni",
            "Actions",
        ),
        "**_Multiattack._** The djinni makes three attacks, using Storm Blade or Storm Bolt in any combination.",
    ),
    (
        (
            "Monsters A–Z",
            "Djinni",
            "Djinni",
            "Actions",
        ),
        "**_Storm Blade._** _Melee Attack Roll:_ +9, reach 5 feet. _Hit:_ 12 (2d6 + 5) Slashing damage plus 7 (2d6) Lightning damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Djinni",
            "Djinni",
            "Actions",
        ),
        "**_Storm Bolt._** _Ranged Attack Roll:_ +9, range 120 feet. _Hit:_ 13 (3d8) Thunder damage. If the target is a Large or smaller creature, it has the Prone condition.",
    ),
    (
        (
            "Monsters A–Z",
            "Djinni",
            "Djinni",
            "Actions",
        ),
        "**_Create Whirlwind._** The djinni conjures a whirlwind at a point it can see within 120 feet. The whirlwind fills a 20-foot-radius, 60-foot-high Cylinder centered on that point. The whirlwind lasts until the djinni's Concentration on it ends. The djinni can move the whirlwind up to 20 feet at the start of each of its turns. <br>\n&emsp;Whenever the whirlwind enters a creature's space or a creature enters the whirlwind, that creature is subjected to the following effect. _Strength Saving Throw:_ DC 17 (a creature makes this save only once per turn, and the djinni is unaffected). _Failure:_ While in the whirlwind, the target has the Restrained condition and moves with the whirlwind. At the start of each of its turns, the Restrained target takes 21 (6d6) Thunder damage. At the end of each of its turns, the target repeats the save, ending the effect on itself on a success.",
    ),
    (
        (
            "Monsters A–Z",
            "Djinni",
            "Djinni",
            "Actions",
        ),
        "**_Spellcasting._** The djinni casts one of the following spells, requiring no Material components and using Charisma as the spellcasting ability (spell save DC 17): <br>\n&emsp;**At Will:** _Detect Evil and Good, Detect Magic_ <br>\n&emsp;**2/Day Each:** _Create Food and Water_ (can create wine instead of water), _Tongues, Wind Walk_ <br>\n&emsp;**1/Day Each:** _Creation, Gaseous Form, Invisibility, Major Image, Plane Shift_",
    ),
    (
        (
            "Monsters A–Z",
            "Doppelganger",
        ),
        "## Doppelganger",
    ),
    (
        (
            "Monsters A–Z",
            "Doppelganger",
            "Doppelganger",
        ),
        "### Doppelganger",
    ),
    (
        (
            "Monsters A–Z",
            "Doppelganger",
            "Doppelganger",
        ),
        "_Medium Monstrosity, Neutral_",
    ),
    (
        (
            "Monsters A–Z",
            "Doppelganger",
            "Doppelganger",
        ),
        "**AC** 14 **Initiative** +4 (14) <br>\n**HP** 52 (8d8 + 16) <br>\n**Speed** 30 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Doppelganger",
            "Doppelganger",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>DEX</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+4</td>\n      <td><strong>CON</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>WIS</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CHA</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Doppelganger",
            "Doppelganger",
        ),
        "**Skills** Deception +6, Insight +3<br>\n**Immunities** Charmed<br>\n**Senses** Darkvision 60 ft.; Passive Perception 11<br>\n**Languages** Common plus three other languages<br>\n**CR** 3 (XP 700; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Doppelganger",
            "Doppelganger",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Doppelganger",
            "Doppelganger",
            "Actions",
        ),
        "**_Multiattack._** The doppelganger makes two Slam attacks and uses Unsettling Visage if available.",
    ),
    (
        (
            "Monsters A–Z",
            "Doppelganger",
            "Doppelganger",
            "Actions",
        ),
        "**_Slam._** _Melee Attack Roll:_ +6 (with Advantage during the first round of each combat), reach 5 ft. _Hit:_ 11 (2d6 + 4) Bludgeoning damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Doppelganger",
            "Doppelganger",
            "Actions",
        ),
        "**_Read Thoughts._** The doppelganger casts _Detect Thoughts_, requiring no spell components and using Charisma as the spellcasting ability (spell save DC 12).",
    ),
    (
        (
            "Monsters A–Z",
            "Doppelganger",
            "Doppelganger",
            "Actions",
        ),
        "**_Unsettling Visage (Recharge 6)._** _Wisdom Saving Throw:_ DC 12, each creature in a 15-foot Emanation originating from the doppelganger that can see the doppelganger. _Failure:_ The target has the Frightened condition and repeats the save at the end of each of its turns, ending the effect on itself on a success. After 1 minute, it succeeds automatically.",
    ),
    (
        (
            "Monsters A–Z",
            "Doppelganger",
            "Doppelganger",
            "Bonus Actions",
        ),
        "#### Bonus Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Doppelganger",
            "Doppelganger",
            "Bonus Actions",
        ),
        "**_Shape-Shift._** The doppelganger shape-shifts into a Medium or Small Humanoid, or it returns to its true form. Its game statistics, other than its size, are the same in each form. Any equipment it is wearing or carrying isn't transformed.",
    ),
    (
        (
            "Monsters A–Z",
            "Dragon Turtle",
        ),
        "## Dragon Turtle",
    ),
    (
        (
            "Monsters A–Z",
            "Dragon Turtle",
            "Dragon Turtle",
        ),
        "### Dragon Turtle",
    ),
    (
        (
            "Monsters A–Z",
            "Dragon Turtle",
            "Dragon Turtle",
        ),
        "_Gargantuan Dragon, Neutral_",
    ),
    (
        (
            "Monsters A–Z",
            "Dragon Turtle",
            "Dragon Turtle",
        ),
        "**AC** 20 **Initiative** +6 (16) <br>\n**HP** 356 (23d20 + 115) <br>\n**Speed** 20 ft., Swim 50 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Dragon Turtle",
            "Dragon Turtle",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>25</td>\n      <td>+7</td>\n      <td>+7</td>\n      <td><strong>DEX</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CON</strong></td>\n      <td>20</td>\n      <td>+5</td>\n      <td>+11</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>WIS</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+7</td>\n      <td><strong>CHA</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Dragon Turtle",
            "Dragon Turtle",
        ),
        "**Resistances** Fire<br>\n**Senses** Darkvision 120 ft.; Passive Perception 11<br>\n**Languages** Draconic, Primordial (Aquan)<br>\n**CR** 17 (XP 18,000; PB +6)",
    ),
    (
        (
            "Monsters A–Z",
            "Dragon Turtle",
            "Dragon Turtle",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Dragon Turtle",
            "Dragon Turtle",
            "Traits",
        ),
        "**_Amphibious._** The dragon can breathe air and water.",
    ),
    (
        (
            "Monsters A–Z",
            "Dragon Turtle",
            "Dragon Turtle",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Dragon Turtle",
            "Dragon Turtle",
            "Actions",
        ),
        "**_Multiattack._** The dragon makes three Bite attacks. It can replace one attack with a Tail attack.",
    ),
    (
        (
            "Monsters A–Z",
            "Dragon Turtle",
            "Dragon Turtle",
            "Actions",
        ),
        "**_Bite._** _Melee Attack Roll:_ +13, reach 15 ft. _Hit:_ 23 (3d10 + 7) Piercing damage plus 7 (2d6) Fire damage. Being underwater doesn't grant Resistance to this Fire damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Dragon Turtle",
            "Dragon Turtle",
            "Actions",
        ),
        "**_Tail._** _Melee Attack Roll:_ +13, reach 15 ft. _Hit:_ 18 (2d10 + 7) Bludgeoning damage. If the target is a Huge or smaller creature, it has the Prone condition.",
    ),
    (
        (
            "Monsters A–Z",
            "Dragon Turtle",
            "Dragon Turtle",
            "Actions",
        ),
        "**_Steam Breath (Recharge 5–6)._** _Constitution Saving Throw:_ DC 19, each creature in a 60-foot Cone. _Failure:_ 56 (16d6) Fire damage. _Success:_ Half damage. _Failure or Success:_ Being underwater doesn't grant Resistance to this Fire damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Dretch",
        ),
        "## Dretch",
    ),
    (
        (
            "Monsters A–Z",
            "Dretch",
            "Dretch",
        ),
        "### Dretch",
    ),
    (
        (
            "Monsters A–Z",
            "Dretch",
            "Dretch",
        ),
        "_Small Fiend (Demon), Chaotic Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Dretch",
            "Dretch",
        ),
        "**AC** 11 **Initiative** +0 (10) <br>\n**HP** 18 (4d6 + 4) <br>\n**Speed** 20 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Dretch",
            "Dretch",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>DEX</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CON</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>5</td>\n      <td>−3</td>\n      <td>−3</td>\n      <td><strong>WIS</strong></td>\n      <td>8</td>\n      <td>−1</td>\n      <td>−1</td>\n      <td><strong>CHA</strong></td>\n      <td>3</td>\n      <td>−4</td>\n      <td>−4</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Dretch",
            "Dretch",
        ),
        "**Resistances** Cold, Fire, Lightning<br>\n**Immunities** Poison; Poisoned<br>\n**Senses** Darkvision 60 ft.; Passive Perception 9<br>\n**Languages** Abyssal; telepathy 60 ft. (works only with creatures that understand Abyssal)<br>\n**CR** 1/4 (XP 50; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Dretch",
            "Dretch",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Dretch",
            "Dretch",
            "Actions",
        ),
        "**_Rend._** _Melee Attack Roll:_ +3, reach 5 ft. _Hit:_ 4 (1d6 + 1) Slashing damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Dretch",
            "Dretch",
            "Actions",
        ),
        "**_Fetid Cloud (1/Day)._** _Constitution Saving Throw:_ DC 11, each creature in a 10-foot Emanation originating from the dretch. _Failure:_ The target has the Poisoned condition until the end of its next turn. While Poisoned, the creature can take either an action or a Bonus Action on its turn, not both, and it can't take Reactions.",
    ),
    (
        (
            "Monsters A–Z",
            "Drider",
        ),
        "## Drider",
    ),
    (
        (
            "Monsters A–Z",
            "Drider",
            "Drider",
        ),
        "### Drider",
    ),
    (
        (
            "Monsters A–Z",
            "Drider",
            "Drider",
        ),
        "_Large Monstrosity, Chaotic Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Drider",
            "Drider",
        ),
        "**AC** 19 **Initiative** +4 (14) <br>\n**HP** 123 (13d10 + 52) <br>\n**Speed** 30 ft., Climb 30 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Drider",
            "Drider",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>DEX</strong></td>\n      <td>19</td>\n      <td>+4</td>\n      <td>+4</td>\n      <td><strong>CON</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+4</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>WIS</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>CHA</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Drider",
            "Drider",
        ),
        "**Skills** Perception +6, Stealth +10<br>\n**Senses** Darkvision 120 ft.; Passive Perception 16<br>\n**Languages** Elvish, Undercommon<br>\n**CR** 6 (XP 2,300; PB +3)",
    ),
    (
        (
            "Monsters A–Z",
            "Drider",
            "Drider",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Drider",
            "Drider",
            "Traits",
        ),
        "**_Spider Climb._** The drider can climb difficult surfaces, including along ceilings, without needing to make an ability check.",
    ),
    (
        (
            "Monsters A–Z",
            "Drider",
            "Drider",
            "Traits",
        ),
        "**_Sunlight Sensitivity._** While in sunlight, the drider has Disadvantage on ability checks and attack rolls.",
    ),
    (
        (
            "Monsters A–Z",
            "Drider",
            "Drider",
            "Traits",
        ),
        "**_Web Walker._** The drider ignores movement restrictions caused by webs, and the drider knows the location of any other creature in contact with the same web.",
    ),
    (
        (
            "Monsters A–Z",
            "Drider",
            "Drider",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Drider",
            "Drider",
            "Actions",
        ),
        "**_Multiattack._** The drider makes three attacks, using Foreleg or Poison Burst in any combination.",
    ),
    (
        (
            "Monsters A–Z",
            "Drider",
            "Drider",
            "Actions",
        ),
        "**_Foreleg._** _Melee Attack Roll:_ +7, reach 10 ft. _Hit:_ 13 (2d8 + 4) Piercing damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Drider",
            "Drider",
            "Actions",
        ),
        "**_Poison Burst._** _Ranged Attack Roll:_ +6, range 120 ft. _Hit:_ 13 (3d6 + 3) Poison damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Drider",
            "Drider",
            "Bonus Actions",
        ),
        "#### Bonus Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Drider",
            "Drider",
            "Bonus Actions",
        ),
        "**_Magic of the Spider Queen (Recharge 5–6)._** The drider casts _Darkness_, _Faerie Fire_, or _Web_, requiring no Material components and using Wisdom as the spellcasting ability (spell save DC 14).",
    ),
    (
        (
            "Monsters A–Z",
            "Druid",
        ),
        "## Druid",
    ),
    (
        (
            "Monsters A–Z",
            "Druid",
            "Druid",
        ),
        "### Druid",
    ),
    (
        (
            "Monsters A–Z",
            "Druid",
            "Druid",
        ),
        "_Medium or Small Humanoid (Druid), Neutral_",
    ),
    (
        (
            "Monsters A–Z",
            "Druid",
            "Druid",
        ),
        "**AC** 13 **Initiative** +1 (11) <br>\n**HP** 44 (8d8 + 8) <br>\n**Speed** 30 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Druid",
            "Druid",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>DEX</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CON</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>WIS</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>CHA</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Druid",
            "Druid",
        ),
        "**Skills** Medicine +5, Nature +3, Perception +5<br>\n**Gear** Studded Leather Armor<br>\n**Senses** Passive Perception 15<br>\n**Languages** Common, Druidic, Sylvan<br>\n**CR** 2 (XP 450; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Druid",
            "Druid",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Druid",
            "Druid",
            "Actions",
        ),
        "**_Multiattack._** The druid makes two attacks, using Vine Staff or Verdant Wisp in any combination.",
    ),
    (
        (
            "Monsters A–Z",
            "Druid",
            "Druid",
            "Actions",
        ),
        "**_Vine Staff._** _Melee Attack Roll:_ +5, reach 5 ft. _Hit:_ 7 (1d8 + 3) Bludgeoning damage plus 2 (1d4) Poison damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Druid",
            "Druid",
            "Actions",
        ),
        "**_Verdant Wisp._** _Ranged Attack Roll:_ +5, range 90 ft. _Hit:_ 10 (3d6) Radiant damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Druid",
            "Druid",
            "Actions",
        ),
        "**_Spellcasting._** The druid casts one of the following spells, using Wisdom as the spellcasting ability (spell save DC 13): <br>\n&emsp;**At Will:** _Druidcraft, Speak with Animals_ <br>\n&emsp;**2/Day Each:** _Entangle, Thunderwave_ <br>\n&emsp;**1/Day Each:** _Animal Messenger, Long-strider, Moonbeam_",
    ),
    (
        (
            "Monsters A–Z",
            "Dryad",
        ),
        "## Dryad",
    ),
    (
        (
            "Monsters A–Z",
            "Dryad",
            "Dryad",
        ),
        "### Dryad",
    ),
    (
        (
            "Monsters A–Z",
            "Dryad",
            "Dryad",
        ),
        "_Medium Fey, Neutral_",
    ),
    (
        (
            "Monsters A–Z",
            "Dryad",
            "Dryad",
        ),
        "**AC** 16 **Initiative** +1 (11) <br>\n**HP** 22 (5d8) <br>\n**Speed** 30 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Dryad",
            "Dryad",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>DEX</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CON</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>WIS</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CHA</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+4</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Dryad",
            "Dryad",
        ),
        "**Skills** Perception +4, Stealth +5<br>\n**Senses** Darkvision 60 ft.; Passive Perception 14<br>\n**Languages** Elvish, Sylvan<br>\n**CR** 1 (XP 200; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Dryad",
            "Dryad",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Dryad",
            "Dryad",
            "Traits",
        ),
        "**_Magic Resistance._** The dryad has Advantage on saving throws against spells and other magical effects.",
    ),
    (
        (
            "Monsters A–Z",
            "Dryad",
            "Dryad",
            "Traits",
        ),
        "**_Speak with Beasts and Plants._** The dryad can communicate with Beasts and Plants as if they shared a language.",
    ),
    (
        (
            "Monsters A–Z",
            "Dryad",
            "Dryad",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Dryad",
            "Dryad",
            "Actions",
        ),
        "**_Multiattack._** The dryad makes one Vine Lash or Thorn Burst attack, and it can use Spellcasting to cast _Charm Monster_.",
    ),
    (
        (
            "Monsters A–Z",
            "Dryad",
            "Dryad",
            "Actions",
        ),
        "**_Vine Lash._** _Melee Attack Roll:_ +6, reach 10 ft. _Hit:_ 8 (1d8 + 4) Slashing damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Dryad",
            "Dryad",
            "Actions",
        ),
        "**_Thorn Burst._** _Ranged Attack Roll:_ +6, range 60 ft. _Hit:_ 7 (1d6 + 4) Piercing damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Dryad",
            "Dryad",
            "Actions",
        ),
        "**_Spellcasting._** The dryad casts one of the following spells, requiring no Material components and using Charisma as the spellcasting ability (spell save DC 14): <br>\n&emsp;**At Will:** _Animal Friendship, Charm Monster_ (lasts 24 hours; ends early if the dryad casts the spell again), _Druidcraft_ <br>\n&emsp;**1/Day Each:** _Entangle, Pass without Trace_",
    ),
    (
        (
            "Monsters A–Z",
            "Dryad",
            "Dryad",
            "Bonus Actions",
        ),
        "#### Bonus Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Dryad",
            "Dryad",
            "Bonus Actions",
        ),
        "**_Tree Stride._** If within 5 feet of a Large or bigger tree, the dryad teleports to an unoccupied space within 5 feet of a second Large or bigger tree that is within 60 feet of the previous tree.",
    ),
    (
        (
            "Monsters A–Z",
            "Earth Elemental",
        ),
        "## Earth Elemental",
    ),
    (
        (
            "Monsters A–Z",
            "Earth Elemental",
            "Earth Elemental",
        ),
        "### Earth Elemental",
    ),
    (
        (
            "Monsters A–Z",
            "Earth Elemental",
            "Earth Elemental",
        ),
        "_Large Elemental, Neutral_",
    ),
    (
        (
            "Monsters A–Z",
            "Earth Elemental",
            "Earth Elemental",
        ),
        "**AC** 17 **Initiative** −1 (9) <br>\n**HP** 147 (14d10 + 70) <br>\n**Speed** 30 ft., Burrow 30 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Earth Elemental",
            "Earth Elemental",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>20</td>\n      <td>+5</td>\n      <td>+5</td>\n      <td><strong>DEX</strong></td>\n      <td>8</td>\n      <td>−1</td>\n      <td>−1</td>\n      <td><strong>CON</strong></td>\n      <td>20</td>\n      <td>+5</td>\n      <td>+5</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>5</td>\n      <td>−3</td>\n      <td>−3</td>\n      <td><strong>WIS</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CHA</strong></td>\n      <td>5</td>\n      <td>−3</td>\n      <td>−3</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Earth Elemental",
            "Earth Elemental",
        ),
        "**Vulnerabilities** Thunder<br>\n**Immunities** Poison; Exhaustion, Paralyzed, Petrified, Poisoned, Unconscious<br>\n**Senses** Darkvision 60 ft., Tremorsense 60 ft.; Passive Perception 10<br>\n**Languages** Primordial (Terran)<br>\n**CR** 5 (XP 1,800; PB +3)",
    ),
    (
        (
            "Monsters A–Z",
            "Earth Elemental",
            "Earth Elemental",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Earth Elemental",
            "Earth Elemental",
            "Traits",
        ),
        "**_Earth Glide._** The elemental can burrow through nonmagical, unworked earth and stone. While doing so, the elemental doesn't disturb the material it moves through.",
    ),
    (
        (
            "Monsters A–Z",
            "Earth Elemental",
            "Earth Elemental",
            "Traits",
        ),
        "**_Siege Monster._** The elemental deals double damage to objects and structures.",
    ),
    (
        (
            "Monsters A–Z",
            "Earth Elemental",
            "Earth Elemental",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Earth Elemental",
            "Earth Elemental",
            "Actions",
        ),
        "**_Multiattack._** The elemental makes two attacks, using Slam or Rock Launch in any combination.",
    ),
    (
        (
            "Monsters A–Z",
            "Earth Elemental",
            "Earth Elemental",
            "Actions",
        ),
        "**_Slam._** _Melee Attack Roll:_ +8, reach 10 ft. _Hit:_ 14 (2d8 + 5) Bludgeoning damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Earth Elemental",
            "Earth Elemental",
            "Actions",
        ),
        "**_Rock Launch._** _Ranged Attack Roll:_ +8, range 60 ft. _Hit:_ 8 (1d6 + 5) Bludgeoning damage. If the target is a Large or smaller creature, it has the Prone condition.",
    ),
    (
        (
            "Monsters A–Z",
            "Efreeti",
        ),
        "## Efreeti",
    ),
    (
        (
            "Monsters A–Z",
            "Efreeti",
            "Efreeti",
        ),
        "### Efreeti",
    ),
    (
        (
            "Monsters A–Z",
            "Efreeti",
            "Efreeti",
        ),
        "_Large Elemental (Genie), Neutral_",
    ),
    (
        (
            "Monsters A–Z",
            "Efreeti",
            "Efreeti",
        ),
        "**AC** 17 **Initiative** +1 (11) <br>\n**HP** 212 (17d10 + 119) <br>\n**Speed** 40 ft., Fly 60 ft. (hover) <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Efreeti",
            "Efreeti",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>22</td>\n      <td>+6</td>\n      <td>+6</td>\n      <td><strong>DEX</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CON</strong></td>\n      <td>24</td>\n      <td>+7</td>\n      <td>+7</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>WIS</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+6</td>\n      <td><strong>CHA</strong></td>\n      <td>19</td>\n      <td>+4</td>\n      <td>+8</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Efreeti",
            "Efreeti",
        ),
        "**Immunities** Fire<br>\n**Senses** Darkvision 120 ft.; Passive Perception 12<br>\n**Languages** Primordial (Ignan)<br>\n**CR** 11 (XP 7,200; PB +4)",
    ),
    (
        (
            "Monsters A–Z",
            "Efreeti",
            "Efreeti",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Efreeti",
            "Efreeti",
            "Traits",
        ),
        "**_Elemental Restoration._** If the efreeti dies outside the Elemental Plane of Fire, its body dissolves into ash, and it gains a new body in 1d4 days, reviving with all its Hit Points somewhere on the Plane of Fire.",
    ),
    (
        (
            "Monsters A–Z",
            "Efreeti",
            "Efreeti",
            "Traits",
        ),
        "**_Magic Resistance._** The efreeti has Advantage on saving throws against spells and other magical effects.",
    ),
    (
        (
            "Monsters A–Z",
            "Efreeti",
            "Efreeti",
            "Traits",
        ),
        "**_Wishes._** The efreeti has a 30 percent chance of knowing the _Wish_ spell. If the efreeti knows it, the efreeti can cast it only on behalf of a non-genie creature who communicates a wish in a way the efreeti can understand. If the efreeti casts the spell for the creature, the efreeti suffers none of the spell's stress. Once the efreeti has cast it three times, the efreeti can't do so again for 365 days.",
    ),
    (
        (
            "Monsters A–Z",
            "Efreeti",
            "Efreeti",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Efreeti",
            "Efreeti",
            "Actions",
        ),
        "**_Multiattack._** The efreeti makes three attacks, using Heated Blade or Hurl Flame in any combination.",
    ),
    (
        (
            "Monsters A–Z",
            "Efreeti",
            "Efreeti",
            "Actions",
        ),
        "**_Heated Blade._** _Melee Attack Roll:_ +10, reach 5 ft. _Hit:_ 13 (2d6 + 6) Slashing damage plus 13 (2d12) Fire damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Efreeti",
            "Efreeti",
            "Actions",
        ),
        "**_Hurl Flame._** _Ranged Attack Roll:_ +8, range 120 ft. _Hit:_ 24 (7d6) Fire damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Efreeti",
            "Efreeti",
            "Actions",
        ),
        "**_Spellcasting._** The efreeti casts one of the following spells, requiring no Material components and using Charisma as the spellcasting ability (spell save DC 16): <br>\n&emsp;**At Will:** _Detect Magic, Elementalism_ <br>\n&emsp;**1/Day Each:** _Gaseous Form, Invisibility, Major Image, Plane Shift, Tongues, Wall of Fire_ (level 7 version)",
    ),
    (
        (
            "Monsters A–Z",
            "Erinyes",
        ),
        "## Erinyes",
    ),
    (
        (
            "Monsters A–Z",
            "Erinyes",
            "Erinyes",
        ),
        "### Erinyes",
    ),
    (
        (
            "Monsters A–Z",
            "Erinyes",
            "Erinyes",
        ),
        "_Medium Fiend (Devil), Lawful Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Erinyes",
            "Erinyes",
        ),
        "**AC** 18 **Initiative** +7 (17) <br>\n**HP** 178 (21d8 + 84) <br>\n**Speed** 30 ft., Fly 60 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Erinyes",
            "Erinyes",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+4</td>\n      <td><strong>DEX</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+7</td>\n      <td><strong>CON</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+8</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>WIS</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CHA</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+8</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Erinyes",
            "Erinyes",
        ),
        "**Skills** Perception +6, Persuasion +8<br>\n**Resistances** Cold<br>\n**Immunities** Fire, Poison; Poisoned<br>\n**Senses** Truesight 120 ft.; Passive Perception 16<br>\n**Languages** Infernal; telepathy 120 ft.<br>\n**CR** 12 (XP 8,400; PB +4)",
    ),
    (
        (
            "Monsters A–Z",
            "Erinyes",
            "Erinyes",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Erinyes",
            "Erinyes",
            "Traits",
        ),
        "**_Diabolical Restoration._** If the erinyes dies outside the Nine Hells, its body disappears in sulfurous smoke, and it gains a new body instantly, reviving with all its Hit Points somewhere in the Nine Hells.",
    ),
    (
        (
            "Monsters A–Z",
            "Erinyes",
            "Erinyes",
            "Traits",
        ),
        "**_Magic Resistance._** The erinyes has Advantage on saving throws against spells and other magical effects.",
    ),
    (
        (
            "Monsters A–Z",
            "Erinyes",
            "Erinyes",
            "Traits",
        ),
        "**_Magic Rope._** The erinyes has a magic rope. While bearing it, the erinyes can use the Entangling Rope action. The rope has AC 20, HP 90, and Immunity to Poison and Psychic damage. The rope turns to dust if reduced to 0 Hit Points, if it is 5+ feet away from the erinyes for 1 hour or more, or if the erinyes dies. If the rope is damaged or destroyed, the erinyes can fully restore it when finishing a Short or Long Rest.",
    ),
    (
        (
            "Monsters A–Z",
            "Erinyes",
            "Erinyes",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Erinyes",
            "Erinyes",
            "Actions",
        ),
        "**_Multiattack._** The erinyes makes three Withering Sword attacks and can use Entangling Rope.",
    ),
    (
        (
            "Monsters A–Z",
            "Erinyes",
            "Erinyes",
            "Actions",
        ),
        "**_Withering Sword._** _Melee Attack Roll:_ +8, reach 5 ft. _Hit:_ 13 (2d8 + 4) Slashing damage plus 11 (2d10) Necrotic damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Erinyes",
            "Erinyes",
            "Actions",
        ),
        "**_Entangling Rope (Requires Magic Rope)._** _Strength Saving Throw:_ DC 16, one creature the erinyes can see within 120 feet. _Failure:_ 14 (4d6) Force damage, and the target has the Restrained condition until the rope is destroyed, the erinyes uses a Bonus Action to release the target, or the erinyes uses Entangling Rope again.",
    ),
    (
        (
            "Monsters A–Z",
            "Erinyes",
            "Erinyes",
            "Reactions",
        ),
        "#### Reactions",
    ),
    (
        (
            "Monsters A–Z",
            "Erinyes",
            "Erinyes",
            "Reactions",
        ),
        "**_Parry._** _Trigger:_ The erinyes is hit by a melee attack roll while holding a weapon. _Response:_ The erinyes adds 4 to its AC against that attack, possibly causing it to miss.",
    ),
    (
        (
            "Monsters A–Z",
            "Ettercap",
        ),
        "## Ettercap",
    ),
    (
        (
            "Monsters A–Z",
            "Ettercap",
            "Ettercap",
        ),
        "### Ettercap",
    ),
    (
        (
            "Monsters A–Z",
            "Ettercap",
            "Ettercap",
        ),
        "_Medium Monstrosity, Neutral Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Ettercap",
            "Ettercap",
        ),
        "**AC** 13 **Initiative** +2 (12) <br>\n**HP** 44 (8d8 + 8) <br>\n**Speed** 30 ft., Climb 30 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Ettercap",
            "Ettercap",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>DEX</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CON</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>7</td>\n      <td>−2</td>\n      <td>−2</td>\n      <td><strong>WIS</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CHA</strong></td>\n      <td>8</td>\n      <td>−1</td>\n      <td>−1</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Ettercap",
            "Ettercap",
        ),
        "**Skills** Perception +3, Stealth +4, Survival +3<br>\n**Senses** Darkvision 60 ft.; Passive Perception 13<br>\n**Languages** None<br>\n**CR** 2 (XP 450; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Ettercap",
            "Ettercap",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Ettercap",
            "Ettercap",
            "Traits",
        ),
        "**_Spider Climb._** The ettercap can climb difficult surfaces, including along ceilings, without needing to make an ability check.",
    ),
    (
        (
            "Monsters A–Z",
            "Ettercap",
            "Ettercap",
            "Traits",
        ),
        "**_Web Walker._** The ettercap ignores movement restrictions caused by webs, and the ettercap knows the location of any other creature in contact with the same web.",
    ),
    (
        (
            "Monsters A–Z",
            "Ettercap",
            "Ettercap",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Ettercap",
            "Ettercap",
            "Actions",
        ),
        "**_Multiattack._** The ettercap makes one Bite attack and one Claw attack.",
    ),
    (
        (
            "Monsters A–Z",
            "Ettercap",
            "Ettercap",
            "Actions",
        ),
        "**_Bite._** _Melee Attack Roll:_ +4, reach 5 ft. _Hit:_ 5 (1d6 + 2) Piercing damage plus 2 (1d4) Poison damage, and the target has the Poisoned condition until the start of the ettercap's next turn.",
    ),
    (
        (
            "Monsters A–Z",
            "Ettercap",
            "Ettercap",
            "Actions",
        ),
        "**_Claw._** _Melee Attack Roll:_ +4, reach 5 ft. _Hit:_ 7 (2d4 + 2) Slashing damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Ettercap",
            "Ettercap",
            "Actions",
        ),
        "**_Web Strand (Recharge 5–6)._** _Dexterity Saving Throw:_ DC 12, one Large or smaller creature the ettercap can see within 30 feet. _Failure:_ The target has the Restrained condition until the web is destroyed (AC 10; HP 5; Vulnerability to Fire damage; Immunity to Bludgeoning, Poison, and Psychic damage).",
    ),
    (
        (
            "Monsters A–Z",
            "Ettercap",
            "Ettercap",
            "Bonus Actions",
        ),
        "#### Bonus Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Ettercap",
            "Ettercap",
            "Bonus Actions",
        ),
        "**_Reel._** The ettercap pulls one creature within 30 feet of itself that is Restrained by its Web Strand up to 25 feet straight toward itself.",
    ),
    (
        (
            "Monsters A–Z",
            "Ettin",
        ),
        "## Ettin",
    ),
    (
        (
            "Monsters A–Z",
            "Ettin",
            "Ettin",
        ),
        "### Ettin",
    ),
    (
        (
            "Monsters A–Z",
            "Ettin",
            "Ettin",
        ),
        "_Large Giant, Chaotic Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Ettin",
            "Ettin",
        ),
        "**AC** 12 **Initiative** −1 (9) <br>\n**HP** 85 (10d10 + 30) <br>\n**Speed** 40 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Ettin",
            "Ettin",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>21</td>\n      <td>+5</td>\n      <td>+5</td>\n      <td><strong>DEX</strong></td>\n      <td>8</td>\n      <td>−1</td>\n      <td>−1</td>\n      <td><strong>CON</strong></td>\n      <td>17</td>\n      <td>+3</td>\n      <td>+3</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>6</td>\n      <td>−2</td>\n      <td>−2</td>\n      <td><strong>WIS</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CHA</strong></td>\n      <td>8</td>\n      <td>−1</td>\n      <td>−1</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Ettin",
            "Ettin",
        ),
        "**Skills** Perception +4<br>\n**Immunities** Blinded, Charmed, Deafened, Frightened, Stunned, Unconscious<br>\n**Gear** Battleaxe, Morningstar<br>\n**Senses** Darkvision 60 ft.; Passive Perception 14<br>\n**Languages** Giant<br>\n**CR** 4 (XP 1,100; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Ettin",
            "Ettin",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Ettin",
            "Ettin",
            "Actions",
        ),
        "**_Multiattack._** The ettin makes one Battleaxe attack and one Morningstar attack.",
    ),
    (
        (
            "Monsters A–Z",
            "Ettin",
            "Ettin",
            "Actions",
        ),
        "**_Battleaxe._** _Melee Attack Roll:_ +7, reach 5 ft. _Hit:_ 14 (2d8 + 5) Slashing damage. If the target is a Large or smaller creature, it has the Prone condition.",
    ),
    (
        (
            "Monsters A–Z",
            "Ettin",
            "Ettin",
            "Actions",
        ),
        "**_Morningstar._** _Melee Attack Roll:_ +7, reach 5 ft. _Hit:_ 14 (2d8 + 5) Piercing damage, and the target has Disadvantage on the next attack roll it makes before the end of its next turn.",
    ),
    (
        (
            "Monsters A–Z",
            "Fire Elemental",
        ),
        "## Fire Elemental",
    ),
    (
        (
            "Monsters A–Z",
            "Fire Elemental",
            "Fire Elemental",
        ),
        "### Fire Elemental",
    ),
    (
        (
            "Monsters A–Z",
            "Fire Elemental",
            "Fire Elemental",
        ),
        "_Large Elemental, Neutral_",
    ),
    (
        (
            "Monsters A–Z",
            "Fire Elemental",
            "Fire Elemental",
        ),
        "**AC** 13 **Initiative** +3 (13) <br>\n**HP** 93 (11d10 + 33) <br>\n**Speed** 50 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Fire Elemental",
            "Fire Elemental",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>DEX</strong></td>\n      <td>17</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>CON</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>6</td>\n      <td>−2</td>\n      <td>−2</td>\n      <td><strong>WIS</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CHA</strong></td>\n      <td>7</td>\n      <td>−2</td>\n      <td>−2</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Fire Elemental",
            "Fire Elemental",
        ),
        "**Resistances** Bludgeoning, Piercing, Slashing<br>\n**Immunities** Fire, Poison; Exhaustion, Grappled, Paralyzed, Petrified, Poisoned, Prone, Restrained, Unconscious<br>\n**Senses** Darkvision 60 ft.; Passive Perception 10<br>\n**Languages** Primordial (Ignan)<br>\n**CR** 5 (XP 1,800; PB +3)",
    ),
    (
        (
            "Monsters A–Z",
            "Fire Elemental",
            "Fire Elemental",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Fire Elemental",
            "Fire Elemental",
            "Traits",
        ),
        "**_Fire Aura._** At the end of each of the elemental's turns, each creature in a 10-foot Emanation originating from the elemental takes 5 (1d10) Fire damage. Creatures and flammable objects in the Emanation start burning.",
    ),
    (
        (
            "Monsters A–Z",
            "Fire Elemental",
            "Fire Elemental",
            "Traits",
        ),
        "**_Fire Form._** The elemental can move through a space as narrow as 1 inch without expending extra movement to do so, and it can enter a creature's space and stop there. The first time it enters a creature's space on a turn, that creature takes 5 (1d10) Fire damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Fire Elemental",
            "Fire Elemental",
            "Traits",
        ),
        "**_Illumination._** The elemental sheds Bright Light in a 30-foot radius and Dim Light for an additional 30 feet.",
    ),
    (
        (
            "Monsters A–Z",
            "Fire Elemental",
            "Fire Elemental",
            "Traits",
        ),
        "**_Water Susceptibility._** The elemental takes 3 (1d6) Cold damage for every 5 feet the elemental moves in water or for every gallon of water splashed on it.",
    ),
    (
        (
            "Monsters A–Z",
            "Fire Elemental",
            "Fire Elemental",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Fire Elemental",
            "Fire Elemental",
            "Actions",
        ),
        "**_Multiattack._** The elemental makes two Burn attacks.",
    ),
    (
        (
            "Monsters A–Z",
            "Fire Elemental",
            "Fire Elemental",
            "Actions",
        ),
        "**_Burn._** _Melee Attack Roll:_ +6, reach 5 ft. _Hit:_ 10 (2d6 + 3) Fire damage. If the target is a creature or a flammable object, it starts burning.",
    ),
    (
        (
            "Monsters A–Z",
            "Fire Giant",
        ),
        "## Fire Giant",
    ),
    (
        (
            "Monsters A–Z",
            "Fire Giant",
            "Fire Giant",
        ),
        "### Fire Giant",
    ),
    (
        (
            "Monsters A–Z",
            "Fire Giant",
            "Fire Giant",
        ),
        "_Huge Giant, Lawful Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Fire Giant",
            "Fire Giant",
        ),
        "**AC** 18 **Initiative** +3 (13) <br>\n**HP** 162 (13d12 + 78) <br>\n**Speed** 30 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Fire Giant",
            "Fire Giant",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>25</td>\n      <td>+7</td>\n      <td>+7</td>\n      <td><strong>DEX</strong></td>\n      <td>9</td>\n      <td>−1</td>\n      <td>+3</td>\n      <td><strong>CON</strong></td>\n      <td>23</td>\n      <td>+6</td>\n      <td>+10</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>WIS</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CHA</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+5</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Fire Giant",
            "Fire Giant",
        ),
        "**Skills** Athletics +11, Perception +6<br>\n**Immunities** Fire<br>\n**Senses** Passive Perception 16<br>\n**Languages** Giant<br>\n**CR** 9 (XP 5,000; PB +4)",
    ),
    (
        (
            "Monsters A–Z",
            "Fire Giant",
            "Fire Giant",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Fire Giant",
            "Fire Giant",
            "Actions",
        ),
        "**_Multiattack._** The giant makes two attacks, using Flame Sword or Hammer Throw in any combination.",
    ),
    (
        (
            "Monsters A–Z",
            "Fire Giant",
            "Fire Giant",
            "Actions",
        ),
        "**_Flame Sword._** _Melee Attack Roll:_ +11, reach 10 ft. _Hit:_ 21 (4d6 + 7) Slashing damage plus 10 (3d6) Fire damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Fire Giant",
            "Fire Giant",
            "Actions",
        ),
        "**_Hammer Throw._** _Ranged Attack Roll:_ +11, range 60/240 ft. _Hit:_ 23 (3d10 + 7) Bludgeoning damage plus 4 (1d8) Fire damage, and the target is pushed up to 15 feet straight away from the giant and has Disadvantage on the next attack roll it makes before the end of its next turn.",
    ),
    (
        (
            "Monsters A–Z",
            "Flesh Golem",
        ),
        "## Flesh Golem",
    ),
    (
        (
            "Monsters A–Z",
            "Flesh Golem",
            "Flesh Golem",
        ),
        "### Flesh Golem",
    ),
    (
        (
            "Monsters A–Z",
            "Flesh Golem",
            "Flesh Golem",
        ),
        "_Medium Construct, Neutral_",
    ),
    (
        (
            "Monsters A–Z",
            "Flesh Golem",
            "Flesh Golem",
        ),
        "**AC** 9 **Initiative** −1 (9) <br>\n**HP** 127 (15d8 + 60) <br>\n**Speed** 30 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Flesh Golem",
            "Flesh Golem",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>19</td>\n      <td>+4</td>\n      <td>+4</td>\n      <td><strong>DEX</strong></td>\n      <td>9</td>\n      <td>−1</td>\n      <td>−1</td>\n      <td><strong>CON</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+4</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>6</td>\n      <td>−2</td>\n      <td>−2</td>\n      <td><strong>WIS</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CHA</strong></td>\n      <td>5</td>\n      <td>−3</td>\n      <td>−3</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Flesh Golem",
            "Flesh Golem",
        ),
        "**Immunities** Lightning, Poison; Charmed, Exhaustion, Frightened, Paralyzed, Petrified, Poisoned<br>\n**Senses** Darkvision 60 ft.; Passive Perception 10<br>\n**Languages** Understands Common plus one other language but can't speak<br>\n**CR** 5 (XP 1,800; PB +3)",
    ),
    (
        (
            "Monsters A–Z",
            "Flesh Golem",
            "Flesh Golem",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Flesh Golem",
            "Flesh Golem",
            "Traits",
        ),
        "**_Aversion to Fire._** If the golem takes Fire damage, it has Disadvantage on attack rolls and ability checks until the end of its next turn.",
    ),
    (
        (
            "Monsters A–Z",
            "Flesh Golem",
            "Flesh Golem",
            "Traits",
        ),
        "**_Berserk._** Whenever the golem starts its turn Bloodied, roll 1d6. On a 6, the golem goes berserk. On each of its turns while berserk, the golem attacks the nearest creature it can see. If no creature is near enough to move to and attack, the golem attacks an object. Once the golem goes berserk, it remains so until it is destroyed or it is no longer Bloodied. <br>\n&emsp;The golem's creator, if within 60 feet of the berserk golem, can try to calm it by taking an action to make a DC 15 Charisma (Persuasion) check; the golem must be able to hear its creator. If this check succeeds, the golem ceases being berserk until the start of its next turn, at which point it resumes rolling for the Berserk trait again if it is still Bloodied.",
    ),
    (
        (
            "Monsters A–Z",
            "Flesh Golem",
            "Flesh Golem",
            "Traits",
        ),
        "**_Immutable Form._** The golem can't shape-shift.",
    ),
    (
        (
            "Monsters A–Z",
            "Flesh Golem",
            "Flesh Golem",
            "Traits",
        ),
        "**_Lightning Absorption._** Whenever the golem is subjected to Lightning damage, it regains a number of Hit Points equal to the Lightning damage dealt.",
    ),
    (
        (
            "Monsters A–Z",
            "Flesh Golem",
            "Flesh Golem",
            "Traits",
        ),
        "**_Magic Resistance._** The golem has Advantage on saving throws against spells and other magical effects.",
    ),
    (
        (
            "Monsters A–Z",
            "Flesh Golem",
            "Flesh Golem",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Flesh Golem",
            "Flesh Golem",
            "Actions",
        ),
        "**_Multiattack._** The golem makes two Slam attacks.",
    ),
    (
        (
            "Monsters A–Z",
            "Flesh Golem",
            "Flesh Golem",
            "Actions",
        ),
        "**_Slam._** _Melee Attack Roll:_ +7, reach 5 ft. _Hit:_ 13 (2d8 + 4) Bludgeoning damage plus 4 (1d8) Lightning damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Frost Giant",
        ),
        "## Frost Giant",
    ),
    (
        (
            "Monsters A–Z",
            "Frost Giant",
            "Frost Giant",
        ),
        "### Frost Giant",
    ),
    (
        (
            "Monsters A–Z",
            "Frost Giant",
            "Frost Giant",
        ),
        "_Huge Giant, Neutral Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Frost Giant",
            "Frost Giant",
        ),
        "**AC** 15 **Initiative** +2 (12) <br>\n**HP** 149 (13d12 + 65) <br>\n**Speed** 40 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Frost Giant",
            "Frost Giant",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>23</td>\n      <td>+6</td>\n      <td>+6</td>\n      <td><strong>DEX</strong></td>\n      <td>9</td>\n      <td>−1</td>\n      <td>−1</td>\n      <td><strong>CON</strong></td>\n      <td>21</td>\n      <td>+5</td>\n      <td>+8</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>9</td>\n      <td>−1</td>\n      <td>−1</td>\n      <td><strong>WIS</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+3</td>\n      <td><strong>CHA</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+4</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Frost Giant",
            "Frost Giant",
        ),
        "**Skills** Athletics +9, Perception +3<br>\n**Immunities** Cold<br>\n**Senses** Passive Perception 13<br>\n**Languages** Giant<br>\n**CR** 8 (XP 3,900; PB +3)",
    ),
    (
        (
            "Monsters A–Z",
            "Frost Giant",
            "Frost Giant",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Frost Giant",
            "Frost Giant",
            "Actions",
        ),
        "**_Multiattack._** The giant makes two attacks, using Frost Axe or Great Bow in any combination.",
    ),
    (
        (
            "Monsters A–Z",
            "Frost Giant",
            "Frost Giant",
            "Actions",
        ),
        "**_Frost Axe._** _Melee Attack Roll:_ +9, reach 10 ft. _Hit:_ 19 (2d12 + 6) Slashing damage plus 9 (2d8) Cold damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Frost Giant",
            "Frost Giant",
            "Actions",
        ),
        "**_Great Bow._** _Ranged Attack Roll:_ +9, range 150/600 ft. _Hit:_ 17 (2d10 + 6) Piercing damage plus 7 (2d6) Cold damage, and the target's Speed decreases by 10 feet until the end of its next turn.",
    ),
    (
        (
            "Monsters A–Z",
            "Frost Giant",
            "Frost Giant",
            "Bonus Actions",
        ),
        "#### Bonus Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Frost Giant",
            "Frost Giant",
            "Bonus Actions",
        ),
        "**_War Cry (Recharge 5–6)._** The giant or one creature of its choice that can see or hear it gains 16 (2d10 + 5) Temporary Hit Points and has Advantage on attack rolls until the start of the giant's next turn.",
    ),
    (
        (
            "Monsters A–Z",
            "Fungi",
        ),
        "## Fungi",
    ),
    (
        (
            "Monsters A–Z",
            "Fungi",
            "Shrieker Fungus",
        ),
        "### Shrieker Fungus",
    ),
    (
        (
            "Monsters A–Z",
            "Fungi",
            "Shrieker Fungus",
        ),
        "_Medium Plant, Unaligned_",
    ),
    (
        (
            "Monsters A–Z",
            "Fungi",
            "Shrieker Fungus",
        ),
        "**AC** 5 **Initiative** −5 (5) <br>\n**HP** 13 (3d8) <br>\n**Speed** 5 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Fungi",
            "Shrieker Fungus",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>1</td>\n      <td>−5</td>\n      <td>−5</td>\n      <td><strong>DEX</strong></td>\n      <td>1</td>\n      <td>−5</td>\n      <td>−5</td>\n      <td><strong>CON</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>1</td>\n      <td>−5</td>\n      <td>−5</td>\n      <td><strong>WIS</strong></td>\n      <td>3</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>CHA</strong></td>\n      <td>1</td>\n      <td>−5</td>\n      <td>−5</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Fungi",
            "Shrieker Fungus",
        ),
        "**Immunities** Blinded, Charmed, Deafened, Frightened<br>\n**Senses** Blindsight 30 ft.; Passive Perception 6<br>\n**Languages** None<br>\n**CR** 0 (XP 0; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Fungi",
            "Shrieker Fungus",
            "Reactions",
        ),
        "#### Reactions",
    ),
    (
        (
            "Monsters A–Z",
            "Fungi",
            "Shrieker Fungus",
            "Reactions",
        ),
        "**_Shriek._** _Trigger:_ A creature or a source of Bright Light moves within 30 feet of the shrieker. _Response:_ The shrieker emits a shriek audible within 300 feet of itself for 1 minute or until the shrieker dies.",
    ),
    (
        (
            "Monsters A–Z",
            "Fungi",
            "Violet Fungus",
        ),
        "### Violet Fungus",
    ),
    (
        (
            "Monsters A–Z",
            "Fungi",
            "Violet Fungus",
        ),
        "_Medium Plant, Unaligned_",
    ),
    (
        (
            "Monsters A–Z",
            "Fungi",
            "Violet Fungus",
        ),
        "**AC** 5 **Initiative** −5 (5) <br>\n**HP** 18 (4d8) <br>\n**Speed** 5 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Fungi",
            "Violet Fungus",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>3</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>DEX</strong></td>\n      <td>1</td>\n      <td>−5</td>\n      <td>−5</td>\n      <td><strong>CON</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>1</td>\n      <td>−5</td>\n      <td>−5</td>\n      <td><strong>WIS</strong></td>\n      <td>3</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>CHA</strong></td>\n      <td>1</td>\n      <td>−5</td>\n      <td>−5</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Fungi",
            "Violet Fungus",
        ),
        "**Immunities** Blinded, Charmed, Deafened, Frightened<br>\n**Senses** Blindsight 30 ft.; Passive Perception 6<br>\n**Languages** None<br>\n**CR** 1/4 (XP 50; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Fungi",
            "Violet Fungus",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Fungi",
            "Violet Fungus",
            "Actions",
        ),
        "**_Multiattack._** The fungus makes two Rotting Touch attacks.",
    ),
    (
        (
            "Monsters A–Z",
            "Fungi",
            "Violet Fungus",
            "Actions",
        ),
        "**_Rotting Touch._** _Melee Attack Roll:_ +2, reach 10 ft. _Hit:_ 4 (1d8) Necrotic damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Gargoyle",
        ),
        "## Gargoyle",
    ),
    (
        (
            "Monsters A–Z",
            "Gargoyle",
            "Gargoyle",
        ),
        "### Gargoyle",
    ),
    (
        (
            "Monsters A–Z",
            "Gargoyle",
            "Gargoyle",
        ),
        "_Medium Elemental, Chaotic Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Gargoyle",
            "Gargoyle",
        ),
        "**AC** 15 **Initiative** +2 (12) <br>\n**HP** 67 (9d8 + 27) <br>\n**Speed** 30 ft., Fly 60 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Gargoyle",
            "Gargoyle",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>DEX</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CON</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>6</td>\n      <td>−2</td>\n      <td>−2</td>\n      <td><strong>WIS</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CHA</strong></td>\n      <td>7</td>\n      <td>−2</td>\n      <td>−2</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Gargoyle",
            "Gargoyle",
        ),
        "**Skills** Stealth +4<br>\n**Immunities** Poison; Exhaustion, Petrified, Poisoned<br>\n**Senses** Darkvision 60 ft.; Passive Perception 10<br>\n**Languages** Primordial (Terran)<br>\n**CR** 2 (XP 450; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Gargoyle",
            "Gargoyle",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Gargoyle",
            "Gargoyle",
            "Traits",
        ),
        "**_Flyby._** The gargoyle doesn't provoke an Opportunity Attack when it flies out of an enemy's reach.",
    ),
    (
        (
            "Monsters A–Z",
            "Gargoyle",
            "Gargoyle",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Gargoyle",
            "Gargoyle",
            "Actions",
        ),
        "**_Multiattack._** The gargoyle makes two Claw attacks.",
    ),
    (
        (
            "Monsters A–Z",
            "Gargoyle",
            "Gargoyle",
            "Actions",
        ),
        "**_Claw._** _Melee Attack Roll:_ +4, reach 5 ft. _Hit:_ 7 (2d4 + 2) Slashing damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Gelatinous Cube",
        ),
        "## Gelatinous Cube",
    ),
    (
        (
            "Monsters A–Z",
            "Gelatinous Cube",
            "Gelatinous Cube",
        ),
        "### Gelatinous Cube",
    ),
    (
        (
            "Monsters A–Z",
            "Gelatinous Cube",
            "Gelatinous Cube",
        ),
        "_Large Ooze, Unaligned_",
    ),
    (
        (
            "Monsters A–Z",
            "Gelatinous Cube",
            "Gelatinous Cube",
        ),
        "**AC** 6 **Initiative** −4 (6) <br>\n**HP** 63 (6d10 + 30) <br>\n**Speed** 15 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Gelatinous Cube",
            "Gelatinous Cube",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>DEX</strong></td>\n      <td>3</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>CON</strong></td>\n      <td>20</td>\n      <td>+5</td>\n      <td>+5</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>1</td>\n      <td>−5</td>\n      <td>−5</td>\n      <td><strong>WIS</strong></td>\n      <td>6</td>\n      <td>−2</td>\n      <td>−2</td>\n      <td><strong>CHA</strong></td>\n      <td>1</td>\n      <td>−5</td>\n      <td>−5</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Gelatinous Cube",
            "Gelatinous Cube",
        ),
        "**Immunities** Acid; Blinded, Charmed, Deafened, Exhaustion, Frightened, Prone<br>\n**Senses** Blindsight 60 ft.; Passive Perception 8<br>\n**Languages** None<br>\n**CR** 2 (XP 450; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Gelatinous Cube",
            "Gelatinous Cube",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Gelatinous Cube",
            "Gelatinous Cube",
            "Traits",
        ),
        "**_Ooze Cube._** The cube fills its entire space and is transparent. Other creatures can enter that space, but a creature that does so is subjected to the cube's Engulf and has Disadvantage on the saving throw. <br>\n&emsp;Creatures inside the cube have Total Cover, and the cube can hold one Large creature or up to four Medium or Small creatures inside itself at a time. <br>\n&emsp;As an action, a creature within 5 feet of the cube can pull a creature or an object out of the cube by succeeding on a DC 12 Strength (Athletics) check, and the puller takes 10 (3d6) Acid damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Gelatinous Cube",
            "Gelatinous Cube",
            "Traits",
        ),
        "**_Transparent._** Even when the cube is in plain sight, a creature must succeed on a DC 15 Wisdom (Perception) check to notice the cube if the creature hasn't witnessed the cube move or otherwise act.",
    ),
    (
        (
            "Monsters A–Z",
            "Gelatinous Cube",
            "Gelatinous Cube",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Gelatinous Cube",
            "Gelatinous Cube",
            "Actions",
        ),
        "**_Pseudopod._** _Melee Attack Roll:_ +4, reach 5 ft. _Hit:_ 12 (3d6 + 2) Acid damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Gelatinous Cube",
            "Gelatinous Cube",
            "Actions",
        ),
        "**_Engulf._** The cube moves up to its Speed without provoking Opportunity Attacks. The cube can move through the spaces of Large or smaller creatures if it has room inside itself to contain them (see the Ooze Cube trait). _Dexterity Saving Throw:_ DC 12, each creature whose space the cube enters for the first time during this move. _Failure:_ 10 (3d6) Acid damage, and the target is engulfed. An engulfed target is suffocating, can't cast spells with a Verbal component, has the Restrained condition, and takes 10 (3d6) Acid damage at the start of each of the cube's turns. When the cube moves, the engulfed target moves with it. An engulfed target can try to escape by taking an action to make a DC 12 Strength (Athletics) check. On a successful check, the target escapes and enters the nearest unoccupied space. _Success:_ Half damage, and the target moves to an unoccupied space within 5 feet of the cube. If there is no unoccupied space, the target fails the save instead.",
    ),
    (
        (
            "Monsters A–Z",
            "Ghast",
        ),
        "## Ghast",
    ),
    (
        (
            "Monsters A–Z",
            "Ghast",
            "Ghast",
        ),
        "### Ghast",
    ),
    (
        (
            "Monsters A–Z",
            "Ghast",
            "Ghast",
        ),
        "_Medium Undead, Chaotic Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Ghast",
            "Ghast",
        ),
        "**AC** 13 **Initiative** +3 (13) <br>\n**HP** 36 (8d8) <br>\n**Speed** 30 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Ghast",
            "Ghast",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>DEX</strong></td>\n      <td>17</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>CON</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>WIS</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+2</td>\n      <td><strong>CHA</strong></td>\n      <td>8</td>\n      <td>−1</td>\n      <td>−1</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Ghast",
            "Ghast",
        ),
        "**Resistances** Necrotic<br>\n**Immunities** Poison; Charmed, Exhaustion, Poisoned<br>\n**Senses** Darkvision 60 ft.; Passive Perception 10<br>\n**Languages** Common<br>\n**CR** 2 (XP 450; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Ghast",
            "Ghast",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Ghast",
            "Ghast",
            "Traits",
        ),
        "**_Stench._** _Constitution Saving Throw:_ DC 10, any creature that starts its turn in a 5-foot Emanation originating from the ghast. _Failure:_ The target has the Poisoned condition until the start of its next turn. _Success:_ The target is immune to this ghast's Stench for 24 hours.",
    ),
    (
        (
            "Monsters A–Z",
            "Ghast",
            "Ghast",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Ghast",
            "Ghast",
            "Actions",
        ),
        "**_Bite._** _Melee Attack Roll:_ +5, reach 5 ft. _Hit:_ 7 (1d8 + 3) Piercing damage plus 9 (2d8) Necrotic damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Ghast",
            "Ghast",
            "Actions",
        ),
        "**_Claw._** _Melee Attack Roll:_ +5, reach 5 ft. _Hit:_ 10 (2d6 + 3) Slashing damage. If the target is a non-Undead creature, it is subjected to the following effect. _Constitution Saving Throw:_ DC 10. _Failure:_ The target has the Paralyzed condition until the end of its next turn.",
    ),
    (
        (
            "Monsters A–Z",
            "Ghost",
        ),
        "## Ghost",
    ),
    (
        (
            "Monsters A–Z",
            "Ghost",
            "Ghost",
        ),
        "### Ghost",
    ),
    (
        (
            "Monsters A–Z",
            "Ghost",
            "Ghost",
        ),
        "_Medium Undead, Neutral_",
    ),
    (
        (
            "Monsters A–Z",
            "Ghost",
            "Ghost",
        ),
        "**AC** 11 **Initiative** +1 (11) <br>\n**HP** 45 (10d8) <br>\n**Speed** 5 ft., Fly 40 ft. (hover) <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Ghost",
            "Ghost",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>7</td>\n      <td>−2</td>\n      <td>−2</td>\n      <td><strong>DEX</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CON</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>WIS</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CHA</strong></td>\n      <td>17</td>\n      <td>+3</td>\n      <td>+3</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Ghost",
            "Ghost",
        ),
        "**Resistances** Acid, Bludgeoning, Cold, Fire, Lightning, Piercing, Slashing, Thunder<br>\n**Immunities** Necrotic, Poison; Charmed, Exhaustion, Frightened, Grappled, Paralyzed, Petrified, Poisoned, Prone, Restrained<br>\n**Senses** Darkvision 60 ft.; Passive Perception 11<br>\n**Languages** Common plus one other language<br>\n**CR** 4 (XP 1,100; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Ghost",
            "Ghost",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Ghost",
            "Ghost",
            "Traits",
        ),
        "**_Ethereal Sight._** The ghost can see 60 feet into the Ethereal Plane when it is on the Material Plane.",
    ),
    (
        (
            "Monsters A–Z",
            "Ghost",
            "Ghost",
            "Traits",
        ),
        "**_Incorporeal Movement._** The ghost can move through other creatures and objects as if they were Difficult Terrain. It takes 5 (1d10) Force damage if it ends its turn inside an object.",
    ),
    (
        (
            "Monsters A–Z",
            "Ghost",
            "Ghost",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Ghost",
            "Ghost",
            "Actions",
        ),
        "**_Multiattack._** The ghost makes two Withering Touch attacks.",
    ),
    (
        (
            "Monsters A–Z",
            "Ghost",
            "Ghost",
            "Actions",
        ),
        "**_Withering Touch._** _Melee Attack Roll:_ +5, reach 5 ft. _Hit:_ 19 (3d10 + 3) Necrotic damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Ghost",
            "Ghost",
            "Actions",
        ),
        "**_Etherealness._** The ghost casts the _Etherealness_ spell, requiring no spell components and using Charisma as the spellcasting ability. The ghost is visible on the Material Plane while on the Border Ethereal and vice versa, but it can't affect or be affected by anything on the other plane.",
    ),
    (
        (
            "Monsters A–Z",
            "Ghost",
            "Ghost",
            "Actions",
        ),
        "**_Horrific Visage._** _Wisdom Saving Throw:_ DC 13, each creature in a 60-foot Cone that can see the ghost and isn't an Undead. _Failure:_ 10 (2d6 + 3) Psychic damage, and the target has the Frightened condition until the start of the ghost's next turn. _Success:_ The target is immune to this ghost's Horrific Visage for 24 hours.",
    ),
    (
        (
            "Monsters A–Z",
            "Ghost",
            "Ghost",
            "Actions",
        ),
        "**_Possession (Recharge 6)._** _Charisma Saving Throw:_ DC 13, one Humanoid the ghost can see within 5 feet. _Failure:_ The target is possessed by the ghost; the ghost disappears, and the target has the Incapacitated condition and loses control of its body. The ghost now controls the body, but the target retains awareness. The ghost can't be targeted by any attack, spell, or other effect, except ones that specifically target Undead. The ghost's game statistics are the same, except it uses the possessed target's Speed, as well as the target's Strength, Dexterity, and Constitution modifiers. <br>\n&emsp;The possession lasts until the body drops to 0 Hit Points or the ghost leaves as a Bonus Action. When the possession ends, the ghost appears in an unoccupied space within 5 feet of the target, and the target is immune to this ghost's Possession for 24 hours. <br>\n&emsp;_Success:_ The target is immune to this ghost's Possession for 24 hours.",
    ),
    (
        (
            "Monsters A–Z",
            "Ghoul",
        ),
        "## Ghoul",
    ),
    (
        (
            "Monsters A–Z",
            "Ghoul",
            "Ghoul",
        ),
        "### Ghoul",
    ),
    (
        (
            "Monsters A–Z",
            "Ghoul",
            "Ghoul",
        ),
        "_Medium Undead, Chaotic Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Ghoul",
            "Ghoul",
        ),
        "**AC** 12 **Initiative** +2 (12) <br>\n**HP** 22 (5d8) <br>\n**Speed** 30 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Ghoul",
            "Ghoul",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>DEX</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CON</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>7</td>\n      <td>−2</td>\n      <td>−2</td>\n      <td><strong>WIS</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CHA</strong></td>\n      <td>6</td>\n      <td>−2</td>\n      <td>−2</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Ghoul",
            "Ghoul",
        ),
        "**Immunities** Poison; Charmed, Exhaustion, Poisoned<br>\n**Senses** Darkvision 60 ft.; Passive Perception 10<br>\n**Languages** Common<br>\n**CR** 1 (XP 200; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Ghoul",
            "Ghoul",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Ghoul",
            "Ghoul",
            "Actions",
        ),
        "**_Multiattack._** The ghoul makes two Bite attacks.",
    ),
    (
        (
            "Monsters A–Z",
            "Ghoul",
            "Ghoul",
            "Actions",
        ),
        "**_Bite._** _Melee Attack Roll:_ +4, reach 5 ft. _Hit:_ 5 (1d6 + 2) Piercing damage plus 3 (1d6) Necrotic damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Ghoul",
            "Ghoul",
            "Actions",
        ),
        "**_Claw._** _Melee Attack Roll:_ +4, reach 5 ft. _Hit:_ 4 (1d4 + 2) Slashing damage. If the target is a creature that isn't an Undead or elf, it is subjected to the following effect. _Constitution Saving Throw:_ DC 10. _Failure:_ The target has the Paralyzed condition until the end of its next turn.",
    ),
    (
        (
            "Monsters A–Z",
            "Gibbering Mouther",
        ),
        "## Gibbering Mouther",
    ),
    (
        (
            "Monsters A–Z",
            "Gibbering Mouther",
            "Gibbering Mouther",
        ),
        "### Gibbering Mouther",
    ),
    (
        (
            "Monsters A–Z",
            "Gibbering Mouther",
            "Gibbering Mouther",
        ),
        "_Medium Aberration, Chaotic Neutral_",
    ),
    (
        (
            "Monsters A–Z",
            "Gibbering Mouther",
            "Gibbering Mouther",
        ),
        "**AC** 9 **Initiative** −1 (9) <br>\n**HP** 52 (7d8 + 21) <br>\n**Speed** 20 ft., Swim 20 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Gibbering Mouther",
            "Gibbering Mouther",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>DEX</strong></td>\n      <td>8</td>\n      <td>−1</td>\n      <td>−1</td>\n      <td><strong>CON</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>3</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>WIS</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CHA</strong></td>\n      <td>6</td>\n      <td>−2</td>\n      <td>−2</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Gibbering Mouther",
            "Gibbering Mouther",
        ),
        "**Immunities** Prone<br>\n**Senses** Darkvision 60 ft.; Passive Perception 10<br>\n**Languages** None<br>\n**CR** 2 (XP 450; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Gibbering Mouther",
            "Gibbering Mouther",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Gibbering Mouther",
            "Gibbering Mouther",
            "Traits",
        ),
        "**_Aberrant Ground._** The ground in a 10-foot Emanation originating from the mouther is Difficult Terrain.",
    ),
    (
        (
            "Monsters A–Z",
            "Gibbering Mouther",
            "Gibbering Mouther",
            "Traits",
        ),
        "**_Gibbering._** The mouther babbles incoherently while it doesn't have the Incapacitated condition. _Wisdom Saving Throw:_ DC 10, any creature that starts its turn within 20 feet of the mouther while it is babbling. _Failure:_ The target rolls 1d8 to determine what it does during the current turn: <br>\n&emsp;**1–4.** The target does nothing.<br>\n&emsp;**5–6.** The target takes no action or Bonus Action and uses all its movement to move in a random direction.<br>\n&emsp;**7–8.** The target makes a melee attack against a randomly determined creature within its reach or does nothing if it can't make such an attack.",
    ),
    (
        (
            "Monsters A–Z",
            "Gibbering Mouther",
            "Gibbering Mouther",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Gibbering Mouther",
            "Gibbering Mouther",
            "Actions",
        ),
        "**_Bite._** _Melee Attack Roll:_ +2, reach 5 ft. _Hit:_ 7 (2d6) Piercing damage. If the target is a Medium or smaller creature, it has the Prone condition. The target dies if it is reduced to 0 Hit Points by this attack. Its body is then absorbed into the mouther, leaving only equipment behind.",
    ),
    (
        (
            "Monsters A–Z",
            "Gibbering Mouther",
            "Gibbering Mouther",
            "Actions",
        ),
        "**_Blinding Spittle (Recharge 5–6)._** _Dexterity Saving Throw:_ DC 10, each creature in a 10-foot-radius Sphere centered on a point within 30 feet. _Failure:_ 7 (2d6) Radiant damage, and the target has the Blinded condition until the end of the mouther's next turn.",
    ),
    (
        (
            "Monsters A–Z",
            "Glabrezu",
        ),
        "## Glabrezu",
    ),
    (
        (
            "Monsters A–Z",
            "Glabrezu",
            "Glabrezu",
        ),
        "### Glabrezu",
    ),
    (
        (
            "Monsters A–Z",
            "Glabrezu",
            "Glabrezu",
        ),
        "_Large Fiend (Demon), Chaotic Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Glabrezu",
            "Glabrezu",
        ),
        "**AC** 17 **Initiative** +6 (16) <br>\n**HP** 189 (18d10 + 90) <br>\n**Speed** 40 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Glabrezu",
            "Glabrezu",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>20</td>\n      <td>+5</td>\n      <td>+9</td>\n      <td><strong>DEX</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CON</strong></td>\n      <td>21</td>\n      <td>+5</td>\n      <td>+9</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>19</td>\n      <td>+4</td>\n      <td>+4</td>\n      <td><strong>WIS</strong></td>\n      <td>17</td>\n      <td>+3</td>\n      <td>+7</td>\n      <td><strong>CHA</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+7</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Glabrezu",
            "Glabrezu",
        ),
        "**Skills** Deception +7, Perception +7<br>\n**Resistances** Cold, Fire, Lightning<br>\n**Immunities** Poison; Poisoned<br>\n**Senses** Truesight 120 ft.; Passive Perception 17<br>\n**Languages** Abyssal; telepathy 120 ft.<br>\n**CR** 9 (XP 5,000; PB +4)",
    ),
    (
        (
            "Monsters A–Z",
            "Glabrezu",
            "Glabrezu",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Glabrezu",
            "Glabrezu",
            "Traits",
        ),
        "**_Demonic Restoration._** If the glabrezu dies outside the Abyss, its body dissolves into ichor, and it gains a new body instantly, reviving with all its Hit Points somewhere in the Abyss.",
    ),
    (
        (
            "Monsters A–Z",
            "Glabrezu",
            "Glabrezu",
            "Traits",
        ),
        "**_Magic Resistance._** The glabrezu has Advantage on saving throws against spells and other magical effects.",
    ),
    (
        (
            "Monsters A–Z",
            "Glabrezu",
            "Glabrezu",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Glabrezu",
            "Glabrezu",
            "Actions",
        ),
        "**_Multiattack._** The glabrezu makes two Pincer attacks and uses Pummel or Spellcasting.",
    ),
    (
        (
            "Monsters A–Z",
            "Glabrezu",
            "Glabrezu",
            "Actions",
        ),
        "**_Pincer._** _Melee Attack Roll:_ +9, reach 10 ft. _Hit:_ 16 (2d10 + 5) Slashing damage. If the target is a Medium or smaller creature, it has the Grappled condition (escape DC 15) from one of two pincers.",
    ),
    (
        (
            "Monsters A–Z",
            "Glabrezu",
            "Glabrezu",
            "Actions",
        ),
        "**_Pummel._** _Dexterity Saving Throw:_ DC 17, one creature Grappled by the glabrezu. _Failure:_ 15 (3d6 + 5) Bludgeoning damage. _Success:_ Half damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Glabrezu",
            "Glabrezu",
            "Actions",
        ),
        "**_Spellcasting._** The glabrezu casts one of the following spells, requiring no Material components and using Intelligence as the spellcasting ability (spell save DC 16): <br>\n&emsp;**At Will:** _Darkness, Detect Magic, Dispel Magic_ <br>\n&emsp;**1/Day Each:** _Confusion, Fly, Power Word Stun_",
    ),
    (
        (
            "Monsters A–Z",
            "Gladiator",
        ),
        "## Gladiator",
    ),
    (
        (
            "Monsters A–Z",
            "Gladiator",
            "Gladiator",
        ),
        "### Gladiator",
    ),
    (
        (
            "Monsters A–Z",
            "Gladiator",
            "Gladiator",
        ),
        "_Medium or Small Humanoid, Neutral_",
    ),
    (
        (
            "Monsters A–Z",
            "Gladiator",
            "Gladiator",
        ),
        "**AC** 16 **Initiative** +5 (15) <br>\n**HP** 112 (15d8 + 45) <br>\n**Speed** 30 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Gladiator",
            "Gladiator",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+7</td>\n      <td><strong>DEX</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+5</td>\n      <td><strong>CON</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+6</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>WIS</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+4</td>\n      <td><strong>CHA</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Gladiator",
            "Gladiator",
        ),
        "**Skills** Athletics +10, Performance +5<br>\n**Gear** Shield, Spears (3), Studded Leather Armor<br>\n**Senses** Passive Perception 11<br>\n**Languages** Common<br>\n**CR** 5 (XP 1,800; PB +3)",
    ),
    (
        (
            "Monsters A–Z",
            "Gladiator",
            "Gladiator",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Gladiator",
            "Gladiator",
            "Actions",
        ),
        "**_Multiattack._** The gladiator makes three Spear attacks. It can replace one attack with a use of Shield Bash.",
    ),
    (
        (
            "Monsters A–Z",
            "Gladiator",
            "Gladiator",
            "Actions",
        ),
        "**_Spear._** _Melee or Ranged Attack Roll:_ +7, reach 5 ft. or range 20/60 ft. _Hit:_ 11 (2d6 + 4) Piercing damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Gladiator",
            "Gladiator",
            "Actions",
        ),
        "**_Shield Bash._** _Strength Saving Throw:_ DC 15, one creature within 5 feet that the gladiator can see. _Failure:_ 9 (2d4 + 4) Bludgeoning damage. If the target is a Medium or smaller creature, it has the Prone condition.",
    ),
    (
        (
            "Monsters A–Z",
            "Gladiator",
            "Gladiator",
            "Reactions",
        ),
        "#### Reactions",
    ),
    (
        (
            "Monsters A–Z",
            "Gladiator",
            "Gladiator",
            "Reactions",
        ),
        "**_Parry._** _Trigger:_ The gladiator is hit by a melee attack roll while holding a weapon. _Response:_ The gladiator adds 3 to its AC against that attack, possibly causing it to miss.",
    ),
    (
        (
            "Monsters A–Z",
            "Gnoll",
        ),
        "## Gnoll",
    ),
    (
        (
            "Monsters A–Z",
            "Gnoll",
            "Gnoll Warrior",
        ),
        "### Gnoll Warrior",
    ),
    (
        (
            "Monsters A–Z",
            "Gnoll",
            "Gnoll Warrior",
        ),
        "_Medium Fiend, Chaotic Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Gnoll",
            "Gnoll Warrior",
        ),
        "**AC** 15 **Initiative** +1 (11) <br>\n**HP** 27 (6d8) <br>\n**Speed** 30 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Gnoll",
            "Gnoll Warrior",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>DEX</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CON</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>6</td>\n      <td>−2</td>\n      <td>−2</td>\n      <td><strong>WIS</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CHA</strong></td>\n      <td>7</td>\n      <td>−2</td>\n      <td>−2</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Gnoll",
            "Gnoll Warrior",
        ),
        "**Senses** Darkvision 60 ft.; Passive Perception 10<br>\n**Languages** Gnoll<br>\n**CR** 1/2 (XP 100; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Gnoll",
            "Gnoll Warrior",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Gnoll",
            "Gnoll Warrior",
            "Actions",
        ),
        "**_Rend._** _Melee Attack Roll:_ +4, reach 5 ft. _Hit:_ 5 (1d6 + 2) Piercing damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Gnoll",
            "Gnoll Warrior",
            "Actions",
        ),
        "**_Bone Bow._** _Ranged Attack Roll:_ +3, range 150/600 ft. _Hit:_ 6 (1d10 + 1) Piercing damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Gnoll",
            "Gnoll Warrior",
            "Bonus Actions",
        ),
        "#### Bonus Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Gnoll",
            "Gnoll Warrior",
            "Bonus Actions",
        ),
        "**_Rampage (1/Day)._** Immediately after dealing damage to a creature that is already Bloodied, the gnoll moves up to half its Speed, and it makes one Rend attack.",
    ),
    (
        (
            "Monsters A–Z",
            "Goblins",
        ),
        "## Goblins",
    ),
    (
        (
            "Monsters A–Z",
            "Goblins",
            "Goblin Minion",
        ),
        "### Goblin Minion",
    ),
    (
        (
            "Monsters A–Z",
            "Goblins",
            "Goblin Minion",
        ),
        "_Small Fey (Goblinoid), Chaotic Neutral_",
    ),
    (
        (
            "Monsters A–Z",
            "Goblins",
            "Goblin Minion",
        ),
        "**AC** 12 **Initiative** +2 (12) <br>\n**HP** 7 (2d6) <br>\n**Speed** 30 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Goblins",
            "Goblin Minion",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>8</td>\n      <td>−1</td>\n      <td>−1</td>\n      <td><strong>DEX</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CON</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>WIS</strong></td>\n      <td>8</td>\n      <td>−1</td>\n      <td>−1</td>\n      <td><strong>CHA</strong></td>\n      <td>8</td>\n      <td>−1</td>\n      <td>−1</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Goblins",
            "Goblin Minion",
        ),
        "**Skills** Stealth +6<br>\n**Gear** Daggers (3)<br>\n**Senses** Darkvision 60 ft.; Passive Perception 9<br>\n**Languages** Common, Goblin<br>\n**CR** 1/8 (XP 25; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Goblins",
            "Goblin Minion",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Goblins",
            "Goblin Minion",
            "Actions",
        ),
        "**_Dagger._** _Melee or Ranged Attack Roll:_ +4, reach 5 ft. or range 20/60 ft. _Hit:_ 4 (1d4 + 2) Piercing damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Goblins",
            "Goblin Minion",
            "Bonus Actions",
        ),
        "#### Bonus Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Goblins",
            "Goblin Minion",
            "Bonus Actions",
        ),
        "**_Nimble Escape._** The goblin takes the Disengage or Hide action.",
    ),
    (
        (
            "Monsters A–Z",
            "Goblins",
            "Goblin Warrior",
        ),
        "### Goblin Warrior",
    ),
    (
        (
            "Monsters A–Z",
            "Goblins",
            "Goblin Warrior",
        ),
        "_Small Fey (Goblinoid), Chaotic Neutral_",
    ),
    (
        (
            "Monsters A–Z",
            "Goblins",
            "Goblin Warrior",
        ),
        "**AC** 15 **Initiative** +2 (12) <br>\n**HP** 10 (3d6) <br>\n**Speed** 30 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Goblins",
            "Goblin Warrior",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>8</td>\n      <td>−1</td>\n      <td>−1</td>\n      <td><strong>DEX</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CON</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>WIS</strong></td>\n      <td>8</td>\n      <td>−1</td>\n      <td>−1</td>\n      <td><strong>CHA</strong></td>\n      <td>8</td>\n      <td>−1</td>\n      <td>−1</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Goblins",
            "Goblin Warrior",
        ),
        "**Skills** Stealth +6<br>\n**Gear** Leather Armor, Scimitar, Shield, Shortbow<br>\n**Senses** Darkvision 60 ft.; Passive Perception 9<br>\n**Languages** Common, Goblin<br>\n**CR** 1/4 (XP 50; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Goblins",
            "Goblin Warrior",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Goblins",
            "Goblin Warrior",
            "Actions",
        ),
        "**_Scimitar._** _Melee Attack Roll:_ +4, reach 5 ft. _Hit:_ 5 (1d6 + 2) Slashing damage, plus 2 (1d4) Slashing damage if the attack roll had Advantage.",
    ),
    (
        (
            "Monsters A–Z",
            "Goblins",
            "Goblin Warrior",
            "Actions",
        ),
        "**_Shortbow._** _Ranged Attack Roll:_ +4, range 80/320 ft. _Hit:_ 5 (1d6 + 2) Piercing damage, plus 2 (1d4) Piercing damage if the attack roll had Advantage.",
    ),
    (
        (
            "Monsters A–Z",
            "Goblins",
            "Goblin Warrior",
            "Bonus Actions",
        ),
        "#### Bonus Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Goblins",
            "Goblin Warrior",
            "Bonus Actions",
        ),
        "**_Nimble Escape._** The goblin takes the Disengage or Hide action.",
    ),
    (
        (
            "Monsters A–Z",
            "Goblins",
            "Goblin Boss",
        ),
        "### Goblin Boss",
    ),
    (
        (
            "Monsters A–Z",
            "Goblins",
            "Goblin Boss",
        ),
        "_Small Fey (Goblinoid), Chaotic Neutral_",
    ),
    (
        (
            "Monsters A–Z",
            "Goblins",
            "Goblin Boss",
        ),
        "**AC** 17 **Initiative** +2 (12) <br>\n**HP** 21 (6d6) <br>\n**Speed** 30 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Goblins",
            "Goblin Boss",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>DEX</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CON</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>WIS</strong></td>\n      <td>8</td>\n      <td>−1</td>\n      <td>−1</td>\n      <td><strong>CHA</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Goblins",
            "Goblin Boss",
        ),
        "**Skills** Stealth +6<br>\n**Gear** Chain Shirt, Scimitar, Shield, Shortbow<br>\n**Senses** Darkvision 60 ft.; Passive Perception 9<br>\n**Languages** Common, Goblin<br>\n**CR** 1 (XP 200; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Goblins",
            "Goblin Boss",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Goblins",
            "Goblin Boss",
            "Actions",
        ),
        "**_Multiattack._** The goblin makes two attacks, using Scimitar or Shortbow in any combination.",
    ),
    (
        (
            "Monsters A–Z",
            "Goblins",
            "Goblin Boss",
            "Actions",
        ),
        "**_Scimitar._** _Melee Attack Roll:_ +4, reach 5 ft. _Hit:_ 5 (1d6 + 2) Slashing damage, plus 2 (1d4) Slashing damage if the attack roll had Advantage.",
    ),
    (
        (
            "Monsters A–Z",
            "Goblins",
            "Goblin Boss",
            "Actions",
        ),
        "**_Shortbow._** _Ranged Attack Roll:_ +4, range 80/320 ft. _Hit:_ 5 (1d6 + 2) Piercing damage, plus 2 (1d4) Piercing damage if the attack roll had Advantage.",
    ),
    (
        (
            "Monsters A–Z",
            "Goblins",
            "Goblin Boss",
            "Bonus Actions",
        ),
        "#### Bonus Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Goblins",
            "Goblin Boss",
            "Bonus Actions",
        ),
        "**_Nimble Escape._** The goblin takes the Disengage or Hide action.",
    ),
    (
        (
            "Monsters A–Z",
            "Goblins",
            "Goblin Boss",
            "Reactions",
        ),
        "#### Reactions",
    ),
    (
        (
            "Monsters A–Z",
            "Goblins",
            "Goblin Boss",
            "Reactions",
        ),
        "**_Redirect Attack._** _Trigger:_ A creature the goblin can see makes an attack roll against it. _Response:_ The goblin chooses a Small or Medium ally within 5 feet of itself. The goblin and that ally swap places, and the ally becomes the target of the attack instead.",
    ),
    (
        (
            "Monsters A–Z",
            "Gold Dragons",
        ),
        "## Gold Dragons",
    ),
    (
        (
            "Monsters A–Z",
            "Gold Dragons",
            "Gold Dragon Wyrmling",
        ),
        "### Gold Dragon Wyrmling",
    ),
    (
        (
            "Monsters A–Z",
            "Gold Dragons",
            "Gold Dragon Wyrmling",
        ),
        "_Medium Dragon (Metallic), Lawful Good_",
    ),
    (
        (
            "Monsters A–Z",
            "Gold Dragons",
            "Gold Dragon Wyrmling",
        ),
        "**AC** 17 **Initiative** +4 (14) <br>\n**HP** 60 (8d8 + 24) <br>\n**Speed** 30 ft., Fly 60 ft., Swim 30 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Gold Dragons",
            "Gold Dragon Wyrmling",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>19</td>\n      <td>+4</td>\n      <td>+4</td>\n      <td><strong>DEX</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+4</td>\n      <td><strong>CON</strong></td>\n      <td>17</td>\n      <td>+3</td>\n      <td>+3</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>WIS</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+2</td>\n      <td><strong>CHA</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Gold Dragons",
            "Gold Dragon Wyrmling",
        ),
        "**Skills** Perception +4, Stealth +4<br>\n**Immunities** Fire<br>\n**Senses** Blindsight 10 ft., Darkvision 60 ft.; Passive Perception 14<br>\n**Languages** Draconic<br>\n**CR** 3 (700 XP; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Gold Dragons",
            "Gold Dragon Wyrmling",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Gold Dragons",
            "Gold Dragon Wyrmling",
            "Traits",
        ),
        "**_Amphibious._** The dragon can breathe air and water.",
    ),
    (
        (
            "Monsters A–Z",
            "Gold Dragons",
            "Gold Dragon Wyrmling",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Gold Dragons",
            "Gold Dragon Wyrmling",
            "Actions",
        ),
        "**_Multiattack._** The dragon makes two Rend attacks.",
    ),
    (
        (
            "Monsters A–Z",
            "Gold Dragons",
            "Gold Dragon Wyrmling",
            "Actions",
        ),
        "**_Rend._** _Melee Attack Roll:_ +6, reach 5 ft. _Hit:_ 9 (1d10 + 4) Slashing damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Gold Dragons",
            "Gold Dragon Wyrmling",
            "Actions",
        ),
        "**_Fire Breath (Recharge 5–6)._** _Dexterity Saving Throw:_ DC 13, each creature in a 15-foot Cone. _Failure:_ 22 (4d10) Fire damage. _Success:_ Half damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Gold Dragons",
            "Gold Dragon Wyrmling",
            "Actions",
        ),
        "**_Weakening Breath._** _Strength Saving Throw:_ DC 13, each creature that isn't currently affected by this breath in a 15-foot Cone. _Failure:_ The target has Disadvantage on Strength-based D20 Tests and subtracts 2 (1d4) from its damage rolls. It repeats the save at the end of each of its turns, ending the effect on itself on a success. After 1 minute, it succeeds automatically.",
    ),
    (
        (
            "Monsters A–Z",
            "Gold Dragons",
            "Young Gold Dragon",
        ),
        "### Young Gold Dragon",
    ),
    (
        (
            "Monsters A–Z",
            "Gold Dragons",
            "Young Gold Dragon",
        ),
        "_Large Dragon (Metallic), Lawful Good_",
    ),
    (
        (
            "Monsters A–Z",
            "Gold Dragons",
            "Young Gold Dragon",
        ),
        "**AC** 18 **Initiative** +6 (16) <br>\n**HP** 178 (17d10 + 85) <br>\n**Speed** 40 ft., Fly 80 ft., Swim 40 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Gold Dragons",
            "Young Gold Dragon",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>23</td>\n      <td>+6</td>\n      <td>+6</td>\n      <td><strong>DEX</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+6</td>\n      <td><strong>CON</strong></td>\n      <td>21</td>\n      <td>+5</td>\n      <td>+5</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>WIS</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+5</td>\n      <td><strong>CHA</strong></td>\n      <td>20</td>\n      <td>+5</td>\n      <td>+5</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Gold Dragons",
            "Young Gold Dragon",
        ),
        "**Skills** Insight +5, Perception +9, Persuasion +9, Stealth +6<br>\n**Immunities** Fire<br>\n**Senses** Blindsight 30 ft., Darkvision 120 ft.; Passive Perception 19<br>\n**Languages** Common, Draconic<br>\n**CR** 10 (XP 5,900; PB +4)",
    ),
    (
        (
            "Monsters A–Z",
            "Gold Dragons",
            "Young Gold Dragon",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Gold Dragons",
            "Young Gold Dragon",
            "Traits",
        ),
        "**_Amphibious._** The dragon can breathe air and water.",
    ),
    (
        (
            "Monsters A–Z",
            "Gold Dragons",
            "Young Gold Dragon",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Gold Dragons",
            "Young Gold Dragon",
            "Actions",
        ),
        "**_Multiattack._** The dragon makes three Rend attacks. It can replace one attack with a use of Weakening Breath.",
    ),
    (
        (
            "Monsters A–Z",
            "Gold Dragons",
            "Young Gold Dragon",
            "Actions",
        ),
        "**_Rend._** _Melee Attack Roll:_ +10, reach 10 ft. _Hit:_ 17 (2d10 + 6) Slashing damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Gold Dragons",
            "Young Gold Dragon",
            "Actions",
        ),
        "**_Fire Breath (Recharge 5–6)._** _Dexterity Saving Throw:_ DC 17, each creature in a 30-foot Cone. _Failure:_ 55 (10d10) Fire damage. _Success:_ Half damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Gold Dragons",
            "Young Gold Dragon",
            "Actions",
        ),
        "**_Weakening Breath._** _Strength Saving Throw:_ DC 17, each creature that isn't currently affected by this breath in a 30-foot Cone. _Failure:_ The target has Disadvantage on Strength-based D20 Tests and subtracts 3 (1d6) from its damage rolls. It repeats the save at the end of each of its turns, ending the effect on itself on a success. After 1 minute, it succeeds automatically.",
    ),
    (
        (
            "Monsters A–Z",
            "Gold Dragons",
            "Adult Gold Dragon",
        ),
        "### Adult Gold Dragon",
    ),
    (
        (
            "Monsters A–Z",
            "Gold Dragons",
            "Adult Gold Dragon",
        ),
        "_Huge Dragon (Metallic), Lawful Good_",
    ),
    (
        (
            "Monsters A–Z",
            "Gold Dragons",
            "Adult Gold Dragon",
        ),
        "**AC** 19 **Initiative** +14 (24) <br>\n**HP** 243 (18d12 + 126) <br>\n**Speed** 40 ft., Fly 80 ft., Swim 40 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Gold Dragons",
            "Adult Gold Dragon",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>27</td>\n      <td>+8</td>\n      <td>+8</td>\n      <td><strong>DEX</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+8</td>\n      <td><strong>CON</strong></td>\n      <td>25</td>\n      <td>+7</td>\n      <td>+7</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>WIS</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+8</td>\n      <td><strong>CHA</strong></td>\n      <td>24</td>\n      <td>+7</td>\n      <td>+7</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Gold Dragons",
            "Adult Gold Dragon",
        ),
        "**Skills** Insight +8, Perception +14, Persuasion +13, Stealth +8<br>\n**Immunities** Fire<br>\n**Senses** Blindsight 60 ft., Darkvision 120 ft.; Passive Perception 24<br>\n**Languages** Common, Draconic<br>\n**CR** 17 (XP 18,000, or 20,000 in lair; PB +6)",
    ),
    (
        (
            "Monsters A–Z",
            "Gold Dragons",
            "Adult Gold Dragon",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Gold Dragons",
            "Adult Gold Dragon",
            "Traits",
        ),
        "**_Amphibious._** The dragon can breathe air and water.",
    ),
    (
        (
            "Monsters A–Z",
            "Gold Dragons",
            "Adult Gold Dragon",
            "Traits",
        ),
        "**_Legendary Resistance (3/Day, or 4/Day in Lair)._** If the dragon fails a saving throw, it can choose to succeed instead.",
    ),
    (
        (
            "Monsters A–Z",
            "Gold Dragons",
            "Adult Gold Dragon",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Gold Dragons",
            "Adult Gold Dragon",
            "Actions",
        ),
        "**_Multiattack._** The dragon makes three Rend attacks. It can replace one attack with a use of (A) Spellcasting to cast _Guiding Bolt_ (level 2 version) or (B) Weakening Breath.",
    ),
    (
        (
            "Monsters A–Z",
            "Gold Dragons",
            "Adult Gold Dragon",
            "Actions",
        ),
        "**_Rend._** _Melee Attack Roll:_ +14, reach 10 ft. _Hit:_ 17 (2d8 + 8) Slashing damage plus 4 (1d8) Fire damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Gold Dragons",
            "Adult Gold Dragon",
            "Actions",
        ),
        "**_Fire Breath (Recharge 5–6)._** _Dexterity Saving Throw:_ DC 21, each creature in a 60-foot Cone. _Failure:_ 66 (12d10) Fire damage. _Success:_ Half damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Gold Dragons",
            "Adult Gold Dragon",
            "Actions",
        ),
        "**_Spellcasting._** The dragon casts one of the following spells, requiring no Material components and using Charisma as the spellcasting ability (spell save DC 21, +13 to hit with spell attacks): <br>\n&emsp;**At Will:** _Detect Magic_, _Guiding Bolt_ (level 2 version), _Shapechange_ (Beast or Humanoid form only, no Temporary Hit Points gained from the spell, and no Concentration or Temporary Hit Points required to maintain the spell) <br>\n&emsp;**1/Day Each:** _Flame Strike_, _Zone of Truth_",
    ),
    (
        (
            "Monsters A–Z",
            "Gold Dragons",
            "Adult Gold Dragon",
            "Actions",
        ),
        "**_Weakening Breath._** _Strength Saving Throw:_ DC 21, each creature that isn't currently affected by this breath in a 60-foot Cone. _Failure:_ The target has Disadvantage on Strength-based D20 Tests and subtracts 3 (1d6) from its damage rolls. It repeats the save at the end of each of its turns, ending the effect on itself on a success. After 1 minute, it succeeds automatically.",
    ),
    (
        (
            "Monsters A–Z",
            "Gold Dragons",
            "Adult Gold Dragon",
            "Legendary Actions",
        ),
        "#### Legendary Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Gold Dragons",
            "Adult Gold Dragon",
            "Legendary Actions",
        ),
        "_Legendary Action Uses: 3 (4 in Lair). Immediately after another creature's turn, the dragon can expend a use to take one of the following actions. The dragon regains all expended uses at the start of each of its turns._",
    ),
    (
        (
            "Monsters A–Z",
            "Gold Dragons",
            "Adult Gold Dragon",
            "Legendary Actions",
        ),
        "**_Banish._** _Charisma Saving Throw:_ DC 21, one creature the dragon can see within 120 feet. _Failure:_ 10 (3d6) Force damage, and the target has the Incapacitated condition and is transported to a harmless demiplane until the start of the dragon's next turn, at which point it reappears in an unoccupied space of the dragon's choice within 120 feet of the dragon. _Failure or Success:_ The dragon can't take this action again until the start of its next turn.",
    ),
    (
        (
            "Monsters A–Z",
            "Gold Dragons",
            "Adult Gold Dragon",
            "Legendary Actions",
        ),
        "**_Guiding Light._** The dragon uses Spellcasting to cast _Guiding Bolt_ (level 2 version).",
    ),
    (
        (
            "Monsters A–Z",
            "Gold Dragons",
            "Adult Gold Dragon",
            "Legendary Actions",
        ),
        "**_Pounce._** The dragon moves up to half its Speed, and it makes one Rend attack.",
    ),
    (
        (
            "Monsters A–Z",
            "Gold Dragons",
            "Ancient Gold Dragon",
        ),
        "### Ancient Gold Dragon",
    ),
    (
        (
            "Monsters A–Z",
            "Gold Dragons",
            "Ancient Gold Dragon",
        ),
        "_Gargantuan Dragon (Metallic), Lawful Good_",
    ),
    (
        (
            "Monsters A–Z",
            "Gold Dragons",
            "Ancient Gold Dragon",
        ),
        "**AC** 22 **Initiative** +16 (26) <br>\n**HP** 546 (28d20 + 252) <br>\n**Speed** 40 ft., Fly 80 ft., Swim 40 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Gold Dragons",
            "Ancient Gold Dragon",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>30</td>\n      <td>+10</td>\n      <td>+10</td>\n      <td><strong>DEX</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+9</td>\n      <td><strong>CON</strong></td>\n      <td>29</td>\n      <td>+9</td>\n      <td>+9</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+4</td>\n      <td><strong>WIS</strong></td>\n      <td>17</td>\n      <td>+3</td>\n      <td>+10</td>\n      <td><strong>CHA</strong></td>\n      <td>28</td>\n      <td>+9</td>\n      <td>+9</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Gold Dragons",
            "Ancient Gold Dragon",
        ),
        "**Skills** Insight +10, Perception +17, Persuasion +16, Stealth +9<br>\n**Immunities** Fire<br>\n**Senses** Blindsight 60 ft., Darkvision 120 ft.; Passive Perception 27<br>\n**Languages** Common, Draconic<br>\n**CR** 24 (XP 62,000, or 75,000 in lair; PB +7)",
    ),
    (
        (
            "Monsters A–Z",
            "Gold Dragons",
            "Ancient Gold Dragon",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Gold Dragons",
            "Ancient Gold Dragon",
            "Traits",
        ),
        "**_Amphibious._** The dragon can breathe air and water.",
    ),
    (
        (
            "Monsters A–Z",
            "Gold Dragons",
            "Ancient Gold Dragon",
            "Traits",
        ),
        "**_Legendary Resistance (4/Day, or 5/Day in Lair)._** If the dragon fails a saving throw, it can choose to succeed instead.",
    ),
    (
        (
            "Monsters A–Z",
            "Gold Dragons",
            "Ancient Gold Dragon",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Gold Dragons",
            "Ancient Gold Dragon",
            "Actions",
        ),
        "**_Multiattack._** The dragon makes three Rend attacks. It can replace one attack with a use of (A) Spellcasting to cast _Guiding Bolt_ (level 4 version) or (B) Weakening Breath.",
    ),
    (
        (
            "Monsters A–Z",
            "Gold Dragons",
            "Ancient Gold Dragon",
            "Actions",
        ),
        "**_Rend._** _Melee Attack Roll:_ +17 to hit, reach 15 ft. _Hit:_ 19 (2d8 + 10) Slashing damage plus 9 (2d8) Fire damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Gold Dragons",
            "Ancient Gold Dragon",
            "Actions",
        ),
        "**_Fire Breath (Recharge 5–6)._** _Dexterity Saving Throw:_ DC 24, each creature in a 90-foot Cone. _Failure:_ 71 (13d10) Fire damage. _Success:_ Half damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Gold Dragons",
            "Ancient Gold Dragon",
            "Actions",
        ),
        "**_Spellcasting._** The dragon casts one of the following spells, requiring no Material components and using Charisma as the spellcasting ability (spell save DC 24, +16 to hit with spell attacks): <br>\n&emsp;**At Will:** _Detect Magic_, _Guiding Bolt_ (level 4 version), _Shapechange_ (Beast or Humanoid form only, no Temporary Hit Points gained from the spell, and no Concentration or Temporary Hit Points required to maintain the spell) <br>\n&emsp;**1/Day Each:** _Flame Strike_ (level 6 version), _Word of Recall_, _Zone of Truth_",
    ),
    (
        (
            "Monsters A–Z",
            "Gold Dragons",
            "Ancient Gold Dragon",
            "Actions",
        ),
        "**_Weakening Breath._** _Strength Saving Throw:_ DC 24, each creature that isn't currently affected by this breath in a 90-foot Cone. _Failure:_ The target has Disadvantage on Strength-based D20 Tests and subtracts 5 (1d10) from its damage rolls. It repeats the save at the end of each of its turns, ending the effect on itself on a success. After 1 minute, it succeeds automatically.",
    ),
    (
        (
            "Monsters A–Z",
            "Gold Dragons",
            "Ancient Gold Dragon",
            "Legendary Actions",
        ),
        "#### Legendary Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Gold Dragons",
            "Ancient Gold Dragon",
            "Legendary Actions",
        ),
        "_Legendary Action Uses: 3 (4 in Lair). Immediately after another creature's turn, the dragon can expend a use to take one of the following actions. The dragon regains all expended uses at the start of each of its turns._",
    ),
    (
        (
            "Monsters A–Z",
            "Gold Dragons",
            "Ancient Gold Dragon",
            "Legendary Actions",
        ),
        "**_Banish._** _Charisma Saving Throw:_ DC 24, one creature the dragon can see within 120 feet. _Failure:_ 24 (7d6) Force damage, and the target has the Incapacitated condition and is transported to a harmless demiplane until the start of the dragon's next turn, at which point it reappears in an unoccupied space of the dragon's choice within 120 feet of the dragon. _Failure or Success:_ The dragon can't take this action again until the start of its next turn.",
    ),
    (
        (
            "Monsters A–Z",
            "Gold Dragons",
            "Ancient Gold Dragon",
            "Legendary Actions",
        ),
        "**_Guiding Light._** The dragon uses Spellcasting to cast _Guiding Bolt_ (level 4 version).",
    ),
    (
        (
            "Monsters A–Z",
            "Gold Dragons",
            "Ancient Gold Dragon",
            "Legendary Actions",
        ),
        "**_Pounce._** The dragon moves up to half its Speed, and it makes one Rend attack.",
    ),
    (
        (
            "Monsters A–Z",
            "Gorgon",
        ),
        "## Gorgon",
    ),
    (
        (
            "Monsters A–Z",
            "Gorgon",
            "Gorgon",
        ),
        "### Gorgon",
    ),
    (
        (
            "Monsters A–Z",
            "Gorgon",
            "Gorgon",
        ),
        "_Large Construct, Unaligned_",
    ),
    (
        (
            "Monsters A–Z",
            "Gorgon",
            "Gorgon",
        ),
        "**AC** 19 **Initiative** +0 (10) <br>\n**HP** 114 (12d10 + 48) <br>\n**Speed** 40 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Gorgon",
            "Gorgon",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>20</td>\n      <td>+5</td>\n      <td>+5</td>\n      <td><strong>DEX</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CON</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+4</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>2</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>WIS</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CHA</strong></td>\n      <td>7</td>\n      <td>−2</td>\n      <td>−2</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Gorgon",
            "Gorgon",
        ),
        "**Skills** Perception +7<br>\n**Immunities** Exhaustion, Petrified<br>\n**Senses** Darkvision 60 ft.; Passive Perception 17<br>\n**Languages** None<br>\n**CR** 5 (XP 1,800; PB +3)",
    ),
    (
        (
            "Monsters A–Z",
            "Gorgon",
            "Gorgon",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Gorgon",
            "Gorgon",
            "Actions",
        ),
        "**_Gore._** _Melee Attack Roll:_ +8, reach 5 ft. _Hit:_ 18 (2d12 + 5) Piercing damage. If the target is a Large or smaller creature and the gorgon moved 20+ feet straight toward it immediately before the hit, the target has the Prone condition.",
    ),
    (
        (
            "Monsters A–Z",
            "Gorgon",
            "Gorgon",
            "Actions",
        ),
        "**_Petrifying Breath (Recharge 5–6)._** _Constitution Saving Throw:_ DC 15, each creature in a 30-foot Cone. _First Failure:_ The target has the Restrained condition and repeats the save at the end of its next turn if it is still Restrained, ending the effect on itself on a success. _Second Failure:_ The target has the Petrified condition instead of the Restrained condition.",
    ),
    (
        (
            "Monsters A–Z",
            "Gorgon",
            "Gorgon",
            "Bonus Actions",
        ),
        "#### Bonus Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Gorgon",
            "Gorgon",
            "Bonus Actions",
        ),
        "**_Trample._** _Dexterity Saving Throw:_ DC 16, one creature within 5 feet that has the Prone condition. _Failure:_ 16 (2d10 + 5) Bludgeoning damage. _Success:_ Half damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Gray Ooze",
        ),
        "## Gray Ooze",
    ),
    (
        (
            "Monsters A–Z",
            "Gray Ooze",
            "Gray Ooze",
        ),
        "### Gray Ooze",
    ),
    (
        (
            "Monsters A–Z",
            "Gray Ooze",
            "Gray Ooze",
        ),
        "_Medium Ooze, Unaligned_",
    ),
    (
        (
            "Monsters A–Z",
            "Gray Ooze",
            "Gray Ooze",
        ),
        "**AC** 9 **Initiative** −2 (13) <br>\n**HP** 22 (3d8 + 9) <br>\n**Speed** 10 ft., Climb 10 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Gray Ooze",
            "Gray Ooze",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>DEX</strong></td>\n      <td>6</td>\n      <td>−2</td>\n      <td>−2</td>\n      <td><strong>CON</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>1</td>\n      <td>−5</td>\n      <td>−5</td>\n      <td><strong>WIS</strong></td>\n      <td>6</td>\n      <td>−2</td>\n      <td>−2</td>\n      <td><strong>CHA</strong></td>\n      <td>2</td>\n      <td>−4</td>\n      <td>−4</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Gray Ooze",
            "Gray Ooze",
        ),
        "**Skills** Stealth +2<br>\n**Resistances** Acid, Cold, Fire<br>\n**Immunities** Blinded, Charmed, Deafened, Exhaustion, Frightened, Grappled, Prone, Restrained<br>\n**Senses** Blindsight 60 ft.; Passive Perception 8<br>\n**Languages** None<br>\n**CR** 1/2 (XP 100; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Gray Ooze",
            "Gray Ooze",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Gray Ooze",
            "Gray Ooze",
            "Traits",
        ),
        "**_Amorphous._** The ooze can move through a space as narrow as 1 inch without expending extra movement to do so.",
    ),
    (
        (
            "Monsters A–Z",
            "Gray Ooze",
            "Gray Ooze",
            "Traits",
        ),
        "**_Corrosive Form._** Nonmagical ammunition is destroyed immediately after hitting the ooze and dealing any damage. Any nonmagical weapon takes a cumulative −1 penalty to attack rolls immediately after dealing damage to the ooze and coming into contact with it. The weapon is destroyed if the penalty reaches −5. The penalty can be removed by casting the _Mending_ spell on the weapon. <br>\n&emsp;The ooze can eat through 2-inch-thick, nonmagical metal or wood in 1 round.",
    ),
    (
        (
            "Monsters A–Z",
            "Gray Ooze",
            "Gray Ooze",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Gray Ooze",
            "Gray Ooze",
            "Actions",
        ),
        "**_Pseudopod._** _Melee Attack Roll:_ +3, reach 5 ft. _Hit:_ 10 (2d8 + 1) Acid damage. Nonmagical armor worn by the target takes a −1 penalty to the AC it offers. The armor is destroyed if the penalty reduces its AC to 10. The penalty can be removed by casting the _Mending_ spell on the armor.",
    ),
    (
        (
            "Monsters A–Z",
            "Green Dragons",
        ),
        "## Green Dragons",
    ),
    (
        (
            "Monsters A–Z",
            "Green Dragons",
            "Green Dragon Wyrmling",
        ),
        "### Green Dragon Wyrmling",
    ),
    (
        (
            "Monsters A–Z",
            "Green Dragons",
            "Green Dragon Wyrmling",
        ),
        "_Medium Dragon (Chromatic), Lawful Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Green Dragons",
            "Green Dragon Wyrmling",
        ),
        "**AC** 17 **Initiative** +3 (13) <br>\n**HP** 38 (7d8 + 7) <br>\n**Speed** 30 ft., Fly 60 ft., Swim 30 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Green Dragons",
            "Green Dragon Wyrmling",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>DEX</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+3</td>\n      <td><strong>CON</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>WIS</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+2</td>\n      <td><strong>CHA</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Green Dragons",
            "Green Dragon Wyrmling",
        ),
        "**Skills** Perception +4, Stealth +3<br>\n**Immunities** Poison; Poisoned<br>\n**Senses** Blindsight 10 ft., Darkvision 60 ft.; Passive Perception 14<br>\n**Languages** Draconic<br>\n**CR** 2 (XP 450; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Green Dragons",
            "Green Dragon Wyrmling",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Green Dragons",
            "Green Dragon Wyrmling",
            "Traits",
        ),
        "**_Amphibious._** The dragon can breathe air and water.",
    ),
    (
        (
            "Monsters A–Z",
            "Green Dragons",
            "Green Dragon Wyrmling",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Green Dragons",
            "Green Dragon Wyrmling",
            "Actions",
        ),
        "**_Multiattack._** The dragon makes two Rend attacks.",
    ),
    (
        (
            "Monsters A–Z",
            "Green Dragons",
            "Green Dragon Wyrmling",
            "Actions",
        ),
        "**_Rend._** _Melee Attack Roll:_ +4, reach 5 ft. _Hit:_ 7 (1d10 + 2) Slashing damage plus 3 (1d6) Poison damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Green Dragons",
            "Green Dragon Wyrmling",
            "Actions",
        ),
        "**_Poison Breath (Recharge 5–6)._** _Constitution Saving Throw:_ DC 11, each creature in a 15-foot Cone. _Failure:_ 21 (6d6) Poison damage. _Success:_ Half damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Green Dragons",
            "Young Green Dragon",
        ),
        "### Young Green Dragon",
    ),
    (
        (
            "Monsters A–Z",
            "Green Dragons",
            "Young Green Dragon",
        ),
        "_Large Dragon (Chromatic), Lawful Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Green Dragons",
            "Young Green Dragon",
        ),
        "**AC** 18 **Initiative** +4 (14) <br>\n**HP** 136 (16d10 + 48) <br>\n**Speed** 40 ft., Fly 80 ft., Swim 40 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Green Dragons",
            "Young Green Dragon",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>19</td>\n      <td>+4</td>\n      <td>+4</td>\n      <td><strong>DEX</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+4</td>\n      <td><strong>CON</strong></td>\n      <td>17</td>\n      <td>+3</td>\n      <td>+3</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>WIS</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+4</td>\n      <td><strong>CHA</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Green Dragons",
            "Young Green Dragon",
        ),
        "**Skills** Deception +5, Perception +7, Stealth +4<br>\n**Immunities** Poison; Poisoned<br>\n**Senses** Blindsight 30 ft., Darkvision 120 ft.; Passive Perception 17<br>\n**Languages** Common, Draconic<br>\n**CR** 8 (XP 3,900; PB +3)",
    ),
    (
        (
            "Monsters A–Z",
            "Green Dragons",
            "Young Green Dragon",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Green Dragons",
            "Young Green Dragon",
            "Traits",
        ),
        "**_Amphibious._** The dragon can breathe air and water.",
    ),
    (
        (
            "Monsters A–Z",
            "Green Dragons",
            "Young Green Dragon",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Green Dragons",
            "Young Green Dragon",
            "Actions",
        ),
        "**_Multiattack._** The dragon makes three Rend attacks.",
    ),
    (
        (
            "Monsters A–Z",
            "Green Dragons",
            "Young Green Dragon",
            "Actions",
        ),
        "**_Rend._** _Melee Attack Roll:_ +7, reach 10 ft. _Hit:_ 11 (2d6 + 4) Slashing damage plus 7 (2d6) Poison damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Green Dragons",
            "Young Green Dragon",
            "Actions",
        ),
        "**_Poison Breath (Recharge 5–6)._** _Constitution Saving Throw:_ DC 14, each creature in a 30-foot Cone. _Failure:_ 42 (12d6) Poison damage. _Success:_ Half damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Green Dragons",
            "Adult Green Dragon",
        ),
        "### Adult Green Dragon",
    ),
    (
        (
            "Monsters A–Z",
            "Green Dragons",
            "Adult Green Dragon",
        ),
        "_Huge Dragon (Chromatic), Lawful Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Green Dragons",
            "Adult Green Dragon",
        ),
        "**AC** 19 **Initiative** +11 (21) <br>\n**HP** 207 (18d12 + 90) <br>\n**Speed** 40 ft., Fly 80 ft., Swim 40 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Green Dragons",
            "Adult Green Dragon",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>23</td>\n      <td>+6</td>\n      <td>+6</td>\n      <td><strong>DEX</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+6</td>\n      <td><strong>CON</strong></td>\n      <td>21</td>\n      <td>+5</td>\n      <td>+5</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+4</td>\n      <td><strong>WIS</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+7</td>\n      <td><strong>CHA</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+4</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Green Dragons",
            "Adult Green Dragon",
        ),
        "**Skills** Deception +9, Perception +12, Persuasion +9, Stealth +6<br>\n**Immunities** Poison; Poisoned<br>\n**Senses** Blindsight 60 ft., Darkvision 120 ft.; Passive Perception 22<br>\n**Languages** Common, Draconic<br>\n**CR** 15 (XP 13,000, or 15,000 in lair; PB +5)",
    ),
    (
        (
            "Monsters A–Z",
            "Green Dragons",
            "Adult Green Dragon",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Green Dragons",
            "Adult Green Dragon",
            "Traits",
        ),
        "**_Amphibious._** The dragon can breathe air and water.",
    ),
    (
        (
            "Monsters A–Z",
            "Green Dragons",
            "Adult Green Dragon",
            "Traits",
        ),
        "**_Legendary Resistance (3/Day, or 4/Day in Lair)._** If the dragon fails a saving throw, it can choose to succeed instead.",
    ),
    (
        (
            "Monsters A–Z",
            "Green Dragons",
            "Adult Green Dragon",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Green Dragons",
            "Adult Green Dragon",
            "Actions",
        ),
        "**_Multiattack._** The dragon makes three Rend attacks. It can replace one attack with a use of Spellcasting to cast _Mind Spike_ (level 3 version).",
    ),
    (
        (
            "Monsters A–Z",
            "Green Dragons",
            "Adult Green Dragon",
            "Actions",
        ),
        "**_Rend._** _Melee Attack Roll:_ +11, reach 10 ft. _Hit:_ 15 (2d8 + 6) Slashing damage plus 7 (2d6) Poison damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Green Dragons",
            "Adult Green Dragon",
            "Actions",
        ),
        "**_Poison Breath (Recharge 5–6)._** _Constitution Saving Throw:_ DC 18, each creature in a 60-foot Cone. _Failure:_ 56 (16d6) Poison damage. _Success:_ Half damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Green Dragons",
            "Adult Green Dragon",
            "Actions",
        ),
        "**_Spellcasting._** The dragon casts one of the following spells, requiring no Material components and using Charisma as the spellcasting ability (spell save DC 17): <br>\n&emsp;**At Will:** _Detect Magic_, _Mind Spike_ (level 3 version) <br>\n&emsp;**1/Day:** _Geas_",
    ),
    (
        (
            "Monsters A–Z",
            "Green Dragons",
            "Adult Green Dragon",
            "Legendary Actions",
        ),
        "#### Legendary Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Green Dragons",
            "Adult Green Dragon",
            "Legendary Actions",
        ),
        "_Legendary Action Uses: 3 (4 in Lair). Immediately after another creature's turn, the dragon can expend a use to take one of the following actions. The dragon regains all expended uses at the start of each of its turns._",
    ),
    (
        (
            "Monsters A–Z",
            "Green Dragons",
            "Adult Green Dragon",
            "Legendary Actions",
        ),
        "**_Mind Invasion._** The dragon uses Spellcasting to cast _Mind Spike_ (level 3 version).",
    ),
    (
        (
            "Monsters A–Z",
            "Green Dragons",
            "Adult Green Dragon",
            "Legendary Actions",
        ),
        "**_Noxious Miasma._** _Constitution Saving Throw:_ DC 17, each creature in a 20-foot-radius Sphere centered on a point the dragon can see within 90 feet. _Failure:_ 7 (2d6) Poison damage, and the target takes a −2 penalty to AC until the end of its next turn. _Failure or Success:_ The dragon can't take this action again until the start of its next turn.",
    ),
    (
        (
            "Monsters A–Z",
            "Green Dragons",
            "Adult Green Dragon",
            "Legendary Actions",
        ),
        "**_Pounce._** The dragon moves up to half its Speed, and it makes one Rend attack.",
    ),
    (
        (
            "Monsters A–Z",
            "Green Dragons",
            "Ancient Green Dragon",
        ),
        "### Ancient Green Dragon",
    ),
    (
        (
            "Monsters A–Z",
            "Green Dragons",
            "Ancient Green Dragon",
        ),
        "_Gargantuan Dragon (Chromatic), Lawful Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Green Dragons",
            "Ancient Green Dragon",
        ),
        "**AC** 21 **Initiative** +15 (25) <br>\n**HP** 402 (23d20 + 161) <br>\n**Speed** 40 ft., Fly 80 ft., Swim 40 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Green Dragons",
            "Ancient Green Dragon",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>27</td>\n      <td>+8</td>\n      <td>+8</td>\n      <td><strong>DEX</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+8</td>\n      <td><strong>CON</strong></td>\n      <td>25</td>\n      <td>+7</td>\n      <td>+7</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>20</td>\n      <td>+5</td>\n      <td>+5</td>\n      <td><strong>WIS</strong></td>\n      <td>17</td>\n      <td>+3</td>\n      <td>+10</td>\n      <td><strong>CHA</strong></td>\n      <td>22</td>\n      <td>+6</td>\n      <td>+6</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Green Dragons",
            "Ancient Green Dragon",
        ),
        "**Skills** Deception +13, Perception +17, Persuasion +13, Stealth +8<br>\n**Immunities** Poison; Poisoned<br>\n**Senses** Blindsight 60 ft., Darkvision 120 ft.; Passive Perception 27<br>\n**Languages** Common, Draconic<br>\n**CR** 22 (XP 41,000, or 50,000 in lair; PB +7)",
    ),
    (
        (
            "Monsters A–Z",
            "Green Dragons",
            "Ancient Green Dragon",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Green Dragons",
            "Ancient Green Dragon",
            "Traits",
        ),
        "**_Amphibious._** The dragon can breathe air and water.",
    ),
    (
        (
            "Monsters A–Z",
            "Green Dragons",
            "Ancient Green Dragon",
            "Traits",
        ),
        "**_Legendary Resistance (4/Day, or 5/Day in Lair)._** If the dragon fails a saving throw, it can choose to succeed instead.",
    ),
    (
        (
            "Monsters A–Z",
            "Green Dragons",
            "Ancient Green Dragon",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Green Dragons",
            "Ancient Green Dragon",
            "Actions",
        ),
        "**_Multiattack._** The dragon makes three Rend attacks. It can replace one attack with a use of Spellcasting to cast _Mind Spike_ (level 5 version).",
    ),
    (
        (
            "Monsters A–Z",
            "Green Dragons",
            "Ancient Green Dragon",
            "Actions",
        ),
        "**_Rend._** _Melee Attack Roll:_ +15, reach 15 ft. _Hit:_ 17 (2d8 + 8) Slashing damage plus 10 (3d6) Poison damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Green Dragons",
            "Ancient Green Dragon",
            "Actions",
        ),
        "**_Poison Breath (Recharge 5–6)._** _Constitution Saving Throw:_ DC 22, each creature in a 90-foot Cone. _Failure:_ 77 (22d6) Poison damage. _Success:_ Half damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Green Dragons",
            "Ancient Green Dragon",
            "Actions",
        ),
        "**_Spellcasting._** The dragon casts one of the following spells, requiring no Material components and using Charisma as the spellcasting ability (spell save DC 21): <br>\n&emsp;**At Will:** _Detect Magic_, _Mind Spike_ (level 5 version) <br>\n&emsp;**1/Day Each:** _Geas_, _Modify Memory_",
    ),
    (
        (
            "Monsters A–Z",
            "Green Dragons",
            "Ancient Green Dragon",
            "Legendary Actions",
        ),
        "#### Legendary Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Green Dragons",
            "Ancient Green Dragon",
            "Legendary Actions",
        ),
        "_Legendary Action Uses: 3 (4 in Lair). Immediately after another creature's turn, the dragon can expend a use to take one of the following actions. The dragon regains all expended uses at the start of each of its turns._",
    ),
    (
        (
            "Monsters A–Z",
            "Green Dragons",
            "Ancient Green Dragon",
            "Legendary Actions",
        ),
        "**_Mind Invasion._** The dragon uses Spellcasting to cast _Mind Spike_ (level 5 version).",
    ),
    (
        (
            "Monsters A–Z",
            "Green Dragons",
            "Ancient Green Dragon",
            "Legendary Actions",
        ),
        "**_Noxious Miasma._** _Constitution Saving Throw:_ DC 21, each creature in a 30-foot-radius Sphere centered on a point the dragon can see within 90 feet. _Failure:_ 17 (5d6) Poison damage, and the target takes a −2 penalty to AC until the end of its next turn. _Failure or Success:_ The dragon can't take this action again until the start of its next turn.",
    ),
    (
        (
            "Monsters A–Z",
            "Green Dragons",
            "Ancient Green Dragon",
            "Legendary Actions",
        ),
        "**_Pounce._** The dragon moves up to half its Speed, and it makes one Rend attack.",
    ),
    (
        (
            "Monsters A–Z",
            "Green Hag",
        ),
        "## Green Hag",
    ),
    (
        (
            "Monsters A–Z",
            "Green Hag",
            "Green Hag",
        ),
        "### Green Hag",
    ),
    (
        (
            "Monsters A–Z",
            "Green Hag",
            "Green Hag",
        ),
        "_Medium Fey, Neutral Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Green Hag",
            "Green Hag",
        ),
        "**AC** 17 **Initiative** +1 (11) <br>\n**HP** 82 (11d8 + 33) <br>\n**Speed** 30 ft., Swim 30 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Green Hag",
            "Green Hag",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+4</td>\n      <td><strong>DEX</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CON</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>WIS</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CHA</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Green Hag",
            "Green Hag",
        ),
        "**Skills** Arcana +5, Deception +4, Perception +4, Stealth +3<br>\n**Senses** Darkvision 60 ft.; Passive Perception 14<br>\n**Languages** Common, Elvish, Sylvan<br>\n**CR** 3 (XP 700; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Green Hag",
            "Green Hag",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Green Hag",
            "Green Hag",
            "Traits",
        ),
        "**_Amphibious._** The hag can breathe air and water.",
    ),
    (
        (
            "Monsters A–Z",
            "Green Hag",
            "Green Hag",
            "Traits",
        ),
        "**_Coven Magic._** While within 30 feet of at least two hag allies, the hag can cast one of the following spells, requiring no Material components, using the spell's normal casting time, and using Intelligence as the spellcasting ability (spell save DC 11): _Augury_, _Find Familiar_, _Identify_, _Locate Object_, _Scrying_, or _Unseen Servant_. The hag must finish a Long Rest before using this trait to cast that spell again.",
    ),
    (
        (
            "Monsters A–Z",
            "Green Hag",
            "Green Hag",
            "Traits",
        ),
        "**_Mimicry._** The hag can mimic animal sounds and humanoid voices. A creature that hears the sounds can tell they are imitations only with a successful DC 14 Wisdom (Insight) check.",
    ),
    (
        (
            "Monsters A–Z",
            "Green Hag",
            "Green Hag",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Green Hag",
            "Green Hag",
            "Actions",
        ),
        "**_Multiattack._** The hag makes two Claw attacks.",
    ),
    (
        (
            "Monsters A–Z",
            "Green Hag",
            "Green Hag",
            "Actions",
        ),
        "**_Claw._** _Melee Attack Roll:_ +6, reach 5 ft. _Hit:_ 8 (1d8 + 4) Slashing damage plus 3 (1d6) Poison damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Green Hag",
            "Green Hag",
            "Actions",
        ),
        "**_Spellcasting._** The hag casts one of the following spells, requiring no Material components and using Wisdom as the spellcasting ability (spell save DC 12, +4 to hit with spell attacks): <br>\n&emsp;**At Will:** _Dancing Lights_, _Disguise Self_ (24-hour duration), _Invisibility_ (self only, and the hag leaves no tracks while Invisible), _Minor Illusion_, _Ray of Sickness_ (level 3 version)",
    ),
    (
        (
            "Monsters A–Z",
            "Grick",
        ),
        "## Grick",
    ),
    (
        (
            "Monsters A–Z",
            "Grick",
            "Grick",
        ),
        "### Grick",
    ),
    (
        (
            "Monsters A–Z",
            "Grick",
            "Grick",
        ),
        "_Medium Aberration, Unaligned_",
    ),
    (
        (
            "Monsters A–Z",
            "Grick",
            "Grick",
        ),
        "**AC** 14 **Initiative** +2 (12) <br>\n**HP** 54 (12d8) <br>\n**Speed** 30 ft., Climb 30 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Grick",
            "Grick",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>DEX</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CON</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>3</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>WIS</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CHA</strong></td>\n      <td>5</td>\n      <td>−3</td>\n      <td>−3</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Grick",
            "Grick",
        ),
        "**Skills** Stealth +4<br>\n**Senses** Darkvision 60 ft.; Passive Perception 12<br>\n**Languages** None<br>\n**CR** 2 (XP 450; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Grick",
            "Grick",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Grick",
            "Grick",
            "Actions",
        ),
        "**_Multiattack._** The grick makes one Beak attack and one Tentacles attack.",
    ),
    (
        (
            "Monsters A–Z",
            "Grick",
            "Grick",
            "Actions",
        ),
        "**_Beak._** _Melee Attack Roll:_ +4, reach 5 ft. _Hit:_ 9 (2d6 + 2) Piercing damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Grick",
            "Grick",
            "Actions",
        ),
        "**_Tentacles._** _Melee Attack Roll:_ +4, reach 5 ft. _Hit:_ 7 (1d10 + 2) Slashing damage. If the target is a Medium or smaller creature, it has the Grappled condition (escape DC 12) from all four tentacles.",
    ),
    (
        (
            "Monsters A–Z",
            "Griffon",
        ),
        "## Griffon",
    ),
    (
        (
            "Monsters A–Z",
            "Griffon",
            "Griffon",
        ),
        "### Griffon",
    ),
    (
        (
            "Monsters A–Z",
            "Griffon",
            "Griffon",
        ),
        "_Large Monstrosity, Unaligned_",
    ),
    (
        (
            "Monsters A–Z",
            "Griffon",
            "Griffon",
        ),
        "**AC** 12 **Initiative** +2 (12) <br>\n**HP** 59 (7d10 + 21) <br>\n**Speed** 30 ft., Fly 80 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Griffon",
            "Griffon",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+4</td>\n      <td><strong>DEX</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CON</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>2</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>WIS</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CHA</strong></td>\n      <td>8</td>\n      <td>−1</td>\n      <td>−1</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Griffon",
            "Griffon",
        ),
        "**Skills** Perception +5<br>\n**Senses** Darkvision 60 ft.; Passive Perception 15<br>\n**Languages** None<br>\n**CR** 2 (XP 450; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Griffon",
            "Griffon",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Griffon",
            "Griffon",
            "Actions",
        ),
        "**_Multiattack._** The griffon makes two Rend attacks.",
    ),
    (
        (
            "Monsters A–Z",
            "Griffon",
            "Griffon",
            "Actions",
        ),
        "**_Rend._** _Melee Attack Roll:_ +6, reach 5 ft. _Hit:_ 8 (1d8 + 4) Piercing damage. If the target is a Medium or smaller creature, it has the Grappled condition (escape DC 14) from both of the griffon's front claws.",
    ),
    (
        (
            "Monsters A–Z",
            "Grimlock",
        ),
        "## Grimlock",
    ),
    (
        (
            "Monsters A–Z",
            "Grimlock",
            "Grimlock",
        ),
        "### Grimlock",
    ),
    (
        (
            "Monsters A–Z",
            "Grimlock",
            "Grimlock",
        ),
        "_Medium Aberration, Neutral Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Grimlock",
            "Grimlock",
        ),
        "**AC** 11 **Initiative** +1 (11) <br>\n**HP** 11 (2d8 + 2) <br>\n**Speed** 30 ft., Climb 30 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Grimlock",
            "Grimlock",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>DEX</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CON</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>9</td>\n      <td>−1</td>\n      <td>−1</td>\n      <td><strong>WIS</strong></td>\n      <td>8</td>\n      <td>−1</td>\n      <td>−1</td>\n      <td><strong>CHA</strong></td>\n      <td>6</td>\n      <td>−2</td>\n      <td>−2</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Grimlock",
            "Grimlock",
        ),
        "**Skills** Athletics +5, Perception +3, Stealth +5<br>\n**Senses** Blindsight 30 ft.; Passive Perception 13<br>\n**Languages** None<br>\n**CR** 1/4 (XP 50; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Grimlock",
            "Grimlock",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Grimlock",
            "Grimlock",
            "Actions",
        ),
        "**_Bone Cudgel._** _Melee Attack Roll:_ +5, reach 5 ft. _Hit:_ 6 (1d6 + 3) Bludgeoning damage plus 2 (1d4) Psychic damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Guardian Naga",
        ),
        "## Guardian Naga",
    ),
    (
        (
            "Monsters A–Z",
            "Guardian Naga",
            "Guardian Naga",
        ),
        "### Guardian Naga",
    ),
    (
        (
            "Monsters A–Z",
            "Guardian Naga",
            "Guardian Naga",
        ),
        "_Large Celestial, Lawful Good_",
    ),
    (
        (
            "Monsters A–Z",
            "Guardian Naga",
            "Guardian Naga",
        ),
        "**AC** 18 **Initiative** +4 (14) <br>\n**HP** 136 (16d10 + 48) <br>\n**Speed** 40 ft., Climb 40 ft., Swim 40 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Guardian Naga",
            "Guardian Naga",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>19</td>\n      <td>+4</td>\n      <td>+4</td>\n      <td><strong>DEX</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+8</td>\n      <td><strong>CON</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+7</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+7</td>\n      <td><strong>WIS</strong></td>\n      <td>19</td>\n      <td>+4</td>\n      <td>+8</td>\n      <td><strong>CHA</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+8</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Guardian Naga",
            "Guardian Naga",
        ),
        "**Skills** Arcana +11, History +11, Religion +11<br>\n**Immunities** Poison; Charmed, Paralyzed, Poisoned, Restrained<br>\n**Senses** Darkvision 60 ft.; Passive Perception 14<br>\n**Languages** Celestial, Common<br>\n**CR** 10 (XP 5,900; PB +4)",
    ),
    (
        (
            "Monsters A–Z",
            "Guardian Naga",
            "Guardian Naga",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Guardian Naga",
            "Guardian Naga",
            "Traits",
        ),
        "**_Celestial Restoration._** If the naga dies, it returns to life in 1d6 days and regains all its Hit Points unless _Dispel Evil and Good_ is cast on its remains.",
    ),
    (
        (
            "Monsters A–Z",
            "Guardian Naga",
            "Guardian Naga",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Guardian Naga",
            "Guardian Naga",
            "Actions",
        ),
        "**_Multiattack._** The naga makes two Bite attacks. It can replace any attack with a use of Poisonous Spittle.",
    ),
    (
        (
            "Monsters A–Z",
            "Guardian Naga",
            "Guardian Naga",
            "Actions",
        ),
        "**_Bite._** _Melee Attack Roll:_ +8, reach 10 ft. _Hit:_ 17 (2d12 + 4) Piercing damage plus 22 (4d10) Poison damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Guardian Naga",
            "Guardian Naga",
            "Actions",
        ),
        "**_Poisonous Spittle._** _Constitution Saving Throw:_ DC 16, one creature the naga can see within 60 feet. _Failure:_ 31 (7d8) Poison damage, and the target has the Blinded condition until the start of the naga's next turn. _Success:_ Half damage only.",
    ),
    (
        (
            "Monsters A–Z",
            "Guardian Naga",
            "Guardian Naga",
            "Actions",
        ),
        "**_Spellcasting._** The naga casts one of the following spells, requiring no Somatic or Material components and using Wisdom as the spellcasting ability (spell save DC 16): <br>\n&emsp;**At Will:** _Thaumaturgy_ <br>\n&emsp;**1/Day Each:** _Clairvoyance_, _Cure Wounds_ (level 6 version), _Flame Strike_ (level 6 version), _Geas_, _True Seeing_",
    ),
    (
        (
            "Monsters A–Z",
            "Guards",
        ),
        "## Guards",
    ),
    (
        (
            "Monsters A–Z",
            "Guards",
            "Guard",
        ),
        "### Guard",
    ),
    (
        (
            "Monsters A–Z",
            "Guards",
            "Guard",
        ),
        "_Medium or Small Humanoid, Neutral_",
    ),
    (
        (
            "Monsters A–Z",
            "Guards",
            "Guard",
        ),
        "**AC** 16 **Initiative** +1 (11) <br>\n**HP** 11 (2d8 + 2) <br>\n**Speed** 30 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Guards",
            "Guard",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>DEX</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CON</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>WIS</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CHA</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Guards",
            "Guard",
        ),
        "**Skills** Perception +2<br>\n**Gear** Chain Shirt, Shield, Spear<br>\n**Senses** Passive Perception 12<br>\n**Languages** Common<br>\n**CR** 1/8 (XP 25; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Guards",
            "Guard",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Guards",
            "Guard",
            "Actions",
        ),
        "**_Spear._** _Melee or Ranged Attack Roll:_ +3, reach 5 ft. or range 20/60 ft. _Hit:_ 4 (1d6 + 1) Piercing damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Guards",
            "Guard Captain",
        ),
        "### Guard Captain",
    ),
    (
        (
            "Monsters A–Z",
            "Guards",
            "Guard Captain",
        ),
        "_Medium or Small Humanoid, Neutral_",
    ),
    (
        (
            "Monsters A–Z",
            "Guards",
            "Guard Captain",
        ),
        "**AC** 18 **Initiative** +4 (14) <br>\n**HP** 75 (10d8 + 30) <br>\n**Speed** 30 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Guards",
            "Guard Captain",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+4</td>\n      <td><strong>DEX</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CON</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>WIS</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CHA</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Guards",
            "Guard Captain",
        ),
        "**Skills** Athletics +6, Perception +4<br>\n**Gear** Breastplate, Javelins (6), Longsword, Shield<br>\n**Senses** Passive Perception 14<br>\n**Languages** Common<br>\n**CR** 4 (XP 1,100; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Guards",
            "Guard Captain",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Guards",
            "Guard Captain",
            "Actions",
        ),
        "**_Multiattack._** The guard makes two attacks, using Javelin or Longsword in any combination.",
    ),
    (
        (
            "Monsters A–Z",
            "Guards",
            "Guard Captain",
            "Actions",
        ),
        "**_Javelin._** _Melee or Ranged Attack Roll:_ +6, reach 5 ft. or range 30/120 ft. _Hit:_ 14 (3d6 + 4) Piercing damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Guards",
            "Guard Captain",
            "Actions",
        ),
        "**_Longsword._** _Melee Attack Roll:_ +6, reach 5 ft. _Hit:_ 15 (2d10 + 4) Slashing damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Half-Dragon",
        ),
        "## Half-Dragon",
    ),
    (
        (
            "Monsters A–Z",
            "Half-Dragon",
            "Half-Dragon",
        ),
        "### Half-Dragon",
    ),
    (
        (
            "Monsters A–Z",
            "Half-Dragon",
            "Half-Dragon",
        ),
        "_Medium Dragon, Neutral_",
    ),
    (
        (
            "Monsters A–Z",
            "Half-Dragon",
            "Half-Dragon",
        ),
        "**AC** 18 **Initiative** +5 (15) <br>\n**HP** 105 (14d8 + 42) <br>\n**Speed** 40 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Half-Dragon",
            "Half-Dragon",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>19</td>\n      <td>+4</td>\n      <td>+4</td>\n      <td><strong>DEX</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+5</td>\n      <td><strong>CON</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>WIS</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+5</td>\n      <td><strong>CHA</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Half-Dragon",
            "Half-Dragon",
        ),
        "**Skills** Athletics +7, Perception +5, Stealth +5<br>\n**Resistances** Damage type chosen for the Draconic Origin trait below<br>\n**Senses** Blindsight 10 ft., Darkvision 60 ft.; Passive Perception 15<br>\n**Languages** Common, Draconic<br>\n**CR** 5 (XP 1,800; PB +3)",
    ),
    (
        (
            "Monsters A–Z",
            "Half-Dragon",
            "Half-Dragon",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Half-Dragon",
            "Half-Dragon",
            "Traits",
        ),
        "**_Draconic Origin._** The half-dragon is related to a type of dragon associated with one of the following damage types (GM's choice): Acid, Cold, Fire, Lightning, or Poison. This choice affects other aspects of the stat block.",
    ),
    (
        (
            "Monsters A–Z",
            "Half-Dragon",
            "Half-Dragon",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Half-Dragon",
            "Half-Dragon",
            "Actions",
        ),
        "**_Multiattack._** The half-dragon makes two Claw attacks.",
    ),
    (
        (
            "Monsters A–Z",
            "Half-Dragon",
            "Half-Dragon",
            "Actions",
        ),
        "**_Claw._** _Melee Attack Roll:_ +7, reach 10 ft. _Hit:_ 6 (1d4 + 4) Slashing damage plus 7 (2d6) damage of the type chosen for the Draconic Origin trait.",
    ),
    (
        (
            "Monsters A–Z",
            "Half-Dragon",
            "Half-Dragon",
            "Actions",
        ),
        "**_Dragon's Breath (Recharge 5–6)._** _Dexterity Saving Throw:_ DC 14, each creature in a 30-foot Cone. _Failure:_ 28 (8d6) damage of the type chosen for the Draconic Origin trait. _Success:_ Half damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Half-Dragon",
            "Half-Dragon",
            "Bonus Actions",
        ),
        "#### Bonus Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Half-Dragon",
            "Half-Dragon",
            "Bonus Actions",
        ),
        "**_Leap._** The half-dragon jumps up to 30 feet by spending 10 feet of movement.",
    ),
    (
        (
            "Monsters A–Z",
            "Harpy",
        ),
        "## Harpy",
    ),
    (
        (
            "Monsters A–Z",
            "Harpy",
            "Harpy",
        ),
        "### Harpy",
    ),
    (
        (
            "Monsters A–Z",
            "Harpy",
            "Harpy",
        ),
        "_Medium Monstrosity, Chaotic Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Harpy",
            "Harpy",
        ),
        "**AC** 11 **Initiative** +1 (11) <br>\n**HP** 38 (7d8 + 7) <br>\n**Speed** 20 ft., Fly 40 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Harpy",
            "Harpy",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>DEX</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CON</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>7</td>\n      <td>−2</td>\n      <td>−2</td>\n      <td><strong>WIS</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CHA</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Harpy",
            "Harpy",
        ),
        "**Senses** Passive Perception 10<br>\n**Languages** Common<br>\n**CR** 1 (XP 200; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Harpy",
            "Harpy",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Harpy",
            "Harpy",
            "Actions",
        ),
        "**_Claw._** _Melee Attack Roll:_ +3, reach 5 ft. _Hit:_ 6 (2d4 + 1) Slashing damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Harpy",
            "Harpy",
            "Actions",
        ),
        "**_Luring Song._** The harpy sings a magical melody, which lasts until the harpy's Concentration ends on it. _Wisdom Saving Throw:_ DC 11, each Humanoid and Giant in a 300-foot Emanation originating from the harpy when the song starts. _Failure:_ The target has the Charmed condition until the song ends and repeats the save at the end of each of its turns. While Charmed, the target has the Incapacitated condition and ignores the Luring Song of other harpies. If the target is more than 5 feet from the harpy, the target moves on its turn toward the harpy by the most direct route, trying to get within 5 feet of the harpy. It doesn't avoid Opportunity Attacks; however, before moving into damaging terrain (such as lava or a pit) and whenever it takes damage from a source other than the harpy, the target repeats the save. _Success:_ The target is immune to this harpy's Luring Song for 24 hours.",
    ),
    (
        (
            "Monsters A–Z",
            "Hell Hound",
        ),
        "## Hell Hound",
    ),
    (
        (
            "Monsters A–Z",
            "Hell Hound",
            "Hell Hound",
        ),
        "### Hell Hound",
    ),
    (
        (
            "Monsters A–Z",
            "Hell Hound",
            "Hell Hound",
        ),
        "_Medium Fiend, Lawful Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Hell Hound",
            "Hell Hound",
        ),
        "**AC** 15 **Initiative** +1 (11) <br>\n**HP** 58 (9d8 + 18) <br>\n**Speed** 50 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Hell Hound",
            "Hell Hound",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>17</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>DEX</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CON</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>6</td>\n      <td>−2</td>\n      <td>−2</td>\n      <td><strong>WIS</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CHA</strong></td>\n      <td>6</td>\n      <td>−2</td>\n      <td>−2</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Hell Hound",
            "Hell Hound",
        ),
        "**Skills** Perception +5<br>\n**Immunities** Fire<br>\n**Senses** Darkvision 60 ft.; Passive Perception 15<br>\n**Languages** Understands Infernal but can't speak<br>\n**CR** 3 (XP 700; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Hell Hound",
            "Hell Hound",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Hell Hound",
            "Hell Hound",
            "Traits",
        ),
        "**_Pack Tactics._** The hound has Advantage on an attack roll against a creature if at least one of the hound's allies is within 5 feet of the creature and the ally doesn't have the Incapacitated condition.",
    ),
    (
        (
            "Monsters A–Z",
            "Hell Hound",
            "Hell Hound",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Hell Hound",
            "Hell Hound",
            "Actions",
        ),
        "**_Multiattack._** The hound makes two Bite attacks.",
    ),
    (
        (
            "Monsters A–Z",
            "Hell Hound",
            "Hell Hound",
            "Actions",
        ),
        "**_Bite._** _Melee Attack Roll:_ +5, reach 5 ft. _Hit:_ 7 (1d8 + 3) Piercing damage plus 3 (1d6) Fire damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Hell Hound",
            "Hell Hound",
            "Actions",
        ),
        "**_Fire Breath (Recharge 5–6)._** _Dexterity Saving Throw:_ DC 12, each creature in a 15-foot Cone. _Failure:_ 17 (5d6) Fire damage. _Success:_ Half damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Hezrou",
        ),
        "## Hezrou",
    ),
    (
        (
            "Monsters A–Z",
            "Hezrou",
            "Hezrou",
        ),
        "### Hezrou",
    ),
    (
        (
            "Monsters A–Z",
            "Hezrou",
            "Hezrou",
        ),
        "_Large Fiend (Demon), Chaotic Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Hezrou",
            "Hezrou",
        ),
        "**AC** 18 **Initiative** +6 (16) <br>\n**HP** 157 (15d10 + 75) <br>\n**Speed** 30 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Hezrou",
            "Hezrou",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>19</td>\n      <td>+4</td>\n      <td>+7</td>\n      <td><strong>DEX</strong></td>\n      <td>17</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>CON</strong></td>\n      <td>20</td>\n      <td>+5</td>\n      <td>+8</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>5</td>\n      <td>−3</td>\n      <td>−3</td>\n      <td><strong>WIS</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+4</td>\n      <td><strong>CHA</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Hezrou",
            "Hezrou",
        ),
        "**Resistances** Cold, Fire, Lightning<br>\n**Immunities** Poison; Poisoned<br>\n**Senses** Darkvision 120 ft.; Passive Perception 11<br>\n**Languages** Abyssal; telepathy 120 ft.<br>\n**CR** 8 (XP 3,900; PB +3)",
    ),
    (
        (
            "Monsters A–Z",
            "Hezrou",
            "Hezrou",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Hezrou",
            "Hezrou",
            "Traits",
        ),
        "**_Demonic Restoration._** If the hezrou dies outside the Abyss, its body dissolves into ichor, and it gains a new body instantly, reviving with all its Hit Points somewhere in the Abyss.",
    ),
    (
        (
            "Monsters A–Z",
            "Hezrou",
            "Hezrou",
            "Traits",
        ),
        "**_Magic Resistance._** The hezrou has Advantage on saving throws against spells and other magical effects.",
    ),
    (
        (
            "Monsters A–Z",
            "Hezrou",
            "Hezrou",
            "Traits",
        ),
        "**_Stench._** _Constitution Saving Throw:_ DC 16, any creature that starts its turn in a 10-foot Emanation originating from the hezrou. _Failure:_ The target has the Poisoned condition until the start of its next turn.",
    ),
    (
        (
            "Monsters A–Z",
            "Hezrou",
            "Hezrou",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Hezrou",
            "Hezrou",
            "Actions",
        ),
        "**_Multiattack._** The hezrou makes three Rend attacks.",
    ),
    (
        (
            "Monsters A–Z",
            "Hezrou",
            "Hezrou",
            "Actions",
        ),
        "**_Rend._** _Melee Attack Roll:_ +7, reach 5 ft. _Hit:_ 6 (1d4 + 4) Slashing damage plus 9 (2d8) Poison damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Hezrou",
            "Hezrou",
            "Bonus Actions",
        ),
        "#### Bonus Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Hezrou",
            "Hezrou",
            "Bonus Actions",
        ),
        "**_Leap._** The hezrou jumps up to 30 feet by spending 10 feet of movement.",
    ),
    (
        (
            "Monsters A–Z",
            "Hill Giant",
        ),
        "## Hill Giant",
    ),
    (
        (
            "Monsters A–Z",
            "Hill Giant",
            "Hill Giant",
        ),
        "### Hill Giant",
    ),
    (
        (
            "Monsters A–Z",
            "Hill Giant",
            "Hill Giant",
        ),
        "_Huge Giant, Chaotic Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Hill Giant",
            "Hill Giant",
        ),
        "**AC** 13 **Initiative** +2 (12) <br>\n**HP** 105 (10d12 + 40) <br>\n**Speed** 40 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Hill Giant",
            "Hill Giant",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>21</td>\n      <td>+5</td>\n      <td>+5</td>\n      <td><strong>DEX</strong></td>\n      <td>8</td>\n      <td>−1</td>\n      <td>−1</td>\n      <td><strong>CON</strong></td>\n      <td>19</td>\n      <td>+4</td>\n      <td>+4</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>5</td>\n      <td>−3</td>\n      <td>−3</td>\n      <td><strong>WIS</strong></td>\n      <td>9</td>\n      <td>−1</td>\n      <td>−1</td>\n      <td><strong>CHA</strong></td>\n      <td>6</td>\n      <td>−2</td>\n      <td>−2</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Hill Giant",
            "Hill Giant",
        ),
        "**Skills** Perception +2<br>\n**Senses** Passive Perception 12<br>\n**Languages** Giant<br>\n**CR** 5 (XP 1,800; PB +3)",
    ),
    (
        (
            "Monsters A–Z",
            "Hill Giant",
            "Hill Giant",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Hill Giant",
            "Hill Giant",
            "Actions",
        ),
        "**_Multiattack._** The giant makes two attacks, using Tree Club or Trash Lob in any combination.",
    ),
    (
        (
            "Monsters A–Z",
            "Hill Giant",
            "Hill Giant",
            "Actions",
        ),
        "**_Tree Club._** _Melee Attack Roll:_ +8, reach 10 ft. _Hit:_ 18 (3d8 + 5) Bludgeoning damage. If the target is a Large or smaller creature, it has the Prone condition.",
    ),
    (
        (
            "Monsters A–Z",
            "Hill Giant",
            "Hill Giant",
            "Actions",
        ),
        "**_Trash Lob._** _Ranged Attack Roll:_ +8, range 60/240 ft. _Hit:_ 16 (2d10 + 5) Bludgeoning damage, and the target has the Poisoned condition until the end of its next turn.",
    ),
    (
        (
            "Monsters A–Z",
            "Hippogriff",
        ),
        "## Hippogriff",
    ),
    (
        (
            "Monsters A–Z",
            "Hippogriff",
            "Hippogriff",
        ),
        "### Hippogriff",
    ),
    (
        (
            "Monsters A–Z",
            "Hippogriff",
            "Hippogriff",
        ),
        "_Large Monstrosity, Unaligned_",
    ),
    (
        (
            "Monsters A–Z",
            "Hippogriff",
            "Hippogriff",
        ),
        "**AC** 11 **Initiative** +1 (11) <br>\n**HP** 26 (4d10 + 4) <br>\n**Speed** 40 ft., Fly 60 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Hippogriff",
            "Hippogriff",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>17</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>DEX</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CON</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>2</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>WIS</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CHA</strong></td>\n      <td>8</td>\n      <td>−1</td>\n      <td>−1</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Hippogriff",
            "Hippogriff",
        ),
        "**Skills** Perception +5<br>\n**Senses** Passive Perception 15<br>\n**Languages** None<br>\n**CR** 1 (XP 200; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Hippogriff",
            "Hippogriff",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Hippogriff",
            "Hippogriff",
            "Traits",
        ),
        "**_Flyby._** The hippogriff doesn't provoke an Opportunity Attack when it flies out of an enemy's reach.",
    ),
    (
        (
            "Monsters A–Z",
            "Hippogriff",
            "Hippogriff",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Hippogriff",
            "Hippogriff",
            "Actions",
        ),
        "**_Multiattack._** The hippogriff makes two Rend attacks.",
    ),
    (
        (
            "Monsters A–Z",
            "Hippogriff",
            "Hippogriff",
            "Actions",
        ),
        "**_Rend._** _Melee Attack Roll:_ +5, reach 5 ft. _Hit:_ 7 (1d8 + 3) Slashing damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Hobgoblins",
        ),
        "## Hobgoblins",
    ),
    (
        (
            "Monsters A–Z",
            "Hobgoblins",
            "Hobgoblin Warrior",
        ),
        "### Hobgoblin Warrior",
    ),
    (
        (
            "Monsters A–Z",
            "Hobgoblins",
            "Hobgoblin Warrior",
        ),
        "_Medium Fey (Goblinoid), Lawful Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Hobgoblins",
            "Hobgoblin Warrior",
        ),
        "**AC** 18 **Initiative** +3 (13) <br>\n**HP** 11 (2d8 + 2) <br>\n**Speed** 30 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Hobgoblins",
            "Hobgoblin Warrior",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>DEX</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CON</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>WIS</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CHA</strong></td>\n      <td>9</td>\n      <td>−1</td>\n      <td>−1</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Hobgoblins",
            "Hobgoblin Warrior",
        ),
        "**Gear** Half Plate Armor, Longbow, Longsword, Shield<br>\n**Senses** Darkvision 60 ft.; Passive Perception 10<br>\n**Languages** Common, Goblin<br>\n**CR** 1/2 (XP 100; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Hobgoblins",
            "Hobgoblin Warrior",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Hobgoblins",
            "Hobgoblin Warrior",
            "Traits",
        ),
        "**_Pack Tactics._** The hobgoblin has Advantage on an attack roll against a creature if at least one of the hobgoblin's allies is within 5 feet of the creature and the ally doesn't have the Incapacitated condition.",
    ),
    (
        (
            "Monsters A–Z",
            "Hobgoblins",
            "Hobgoblin Warrior",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Hobgoblins",
            "Hobgoblin Warrior",
            "Actions",
        ),
        "**_Longsword._** _Melee Attack Roll:_ +3, reach 5 ft. _Hit:_ 12 (2d10 + 1) Slashing damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Hobgoblins",
            "Hobgoblin Warrior",
            "Actions",
        ),
        "**_Longbow._** _Ranged Attack Roll:_ +3, range 150/600 ft. _Hit:_ 5 (1d8 + 1) Piercing damage plus 7 (3d4) Poison damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Hobgoblins",
            "Hobgoblin Captain",
        ),
        "### Hobgoblin Captain",
    ),
    (
        (
            "Monsters A–Z",
            "Hobgoblins",
            "Hobgoblin Captain",
        ),
        "_Medium Fey (Goblinoid), Lawful Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Hobgoblins",
            "Hobgoblin Captain",
        ),
        "**AC** 17 **Initiative** +4 (14) <br>\n**HP** 58 (9d8 + 18) <br>\n**Speed** 30 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Hobgoblins",
            "Hobgoblin Captain",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>DEX</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CON</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>WIS</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CHA</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Hobgoblins",
            "Hobgoblin Captain",
        ),
        "**Gear** Greatsword, Half Plate Armor, Longbow<br>\n**Senses** Darkvision 60 ft.; Passive Perception 10<br>\n**Languages** Common, Goblin<br>\n**CR** 3 (XP 700; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Hobgoblins",
            "Hobgoblin Captain",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Hobgoblins",
            "Hobgoblin Captain",
            "Traits",
        ),
        "**_Aura of Authority._** While in a 10-foot Emanation originating from the hobgoblin, the hobgoblin and its allies have Advantage on attack rolls and saving throws, provided the hobgoblin doesn't have the Incapacitated condition.",
    ),
    (
        (
            "Monsters A–Z",
            "Hobgoblins",
            "Hobgoblin Captain",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Hobgoblins",
            "Hobgoblin Captain",
            "Actions",
        ),
        "**_Multiattack._** The hobgoblin makes two attacks, using Greatsword or Longbow in any combination.",
    ),
    (
        (
            "Monsters A–Z",
            "Hobgoblins",
            "Hobgoblin Captain",
            "Actions",
        ),
        "**_Greatsword._** _Melee Attack Roll:_ +4, reach 5 ft. _Hit:_ 9 (2d6 + 2) Slashing damage plus 3 (1d6) Poison damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Hobgoblins",
            "Hobgoblin Captain",
            "Actions",
        ),
        "**_Longbow._** _Ranged Attack Roll:_ +4, range 150/600 ft. _Hit:_ 6 (1d8 + 2) Piercing damage plus 5 (2d4) Poison damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Homunculus",
        ),
        "## Homunculus",
    ),
    (
        (
            "Monsters A–Z",
            "Homunculus",
            "Homunculus",
        ),
        "### Homunculus",
    ),
    (
        (
            "Monsters A–Z",
            "Homunculus",
            "Homunculus",
        ),
        "_Tiny Construct, Neutral_",
    ),
    (
        (
            "Monsters A–Z",
            "Homunculus",
            "Homunculus",
        ),
        "**AC** 13 **Initiative** +2 (12) <br>\n**HP** 4 (1d4 + 2) <br>\n**Speed** 20 ft., Fly 40 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Homunculus",
            "Homunculus",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>4</td>\n      <td>−3</td>\n      <td>−3</td>\n      <td><strong>DEX</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CON</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>WIS</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+2</td>\n      <td><strong>CHA</strong></td>\n      <td>7</td>\n      <td>−2</td>\n      <td>+0</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Homunculus",
            "Homunculus",
        ),
        "**Immunities** Poison; Charmed, Poisoned<br>\n**Senses** Darkvision 60 ft.; Passive Perception 10<br>\n**Languages** Understands Common plus one other language but can't speak<br>\n**CR** 0 (XP 10; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Homunculus",
            "Homunculus",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Homunculus",
            "Homunculus",
            "Traits",
        ),
        "**_Telepathic Bond._** While the homunculus is on the same plane of existence as its master, the two of them can communicate telepathically with each other.",
    ),
    (
        (
            "Monsters A–Z",
            "Homunculus",
            "Homunculus",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Homunculus",
            "Homunculus",
            "Actions",
        ),
        "**_Bite._** _Melee Attack Roll:_ +4, reach 5 ft. _Hit:_ 1 Piercing damage, and the target is subjected to the following effect. _Constitution Saving Throw:_ DC 12. _Failure:_ The target has the Poisoned condition until the end of the homunculus's next turn. _Failure by 5 or More:_ The target has the Poisoned condition for 1 minute. While Poisoned, the target has the Unconscious condition, which ends early if the target takes any damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Horned Devil",
        ),
        "## Horned Devil",
    ),
    (
        (
            "Monsters A–Z",
            "Horned Devil",
            "Horned Devil",
        ),
        "### Horned Devil",
    ),
    (
        (
            "Monsters A–Z",
            "Horned Devil",
            "Horned Devil",
        ),
        "_Large Fiend (Devil), Lawful Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Horned Devil",
            "Horned Devil",
        ),
        "**AC** 18 **Initiative** +7 (17) <br>\n**HP** 199 (19d10 + 95) <br>\n**Speed** 30 ft., Fly 60 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Horned Devil",
            "Horned Devil",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>22</td>\n      <td>+6</td>\n      <td>+10</td>\n      <td><strong>DEX</strong></td>\n      <td>17</td>\n      <td>+3</td>\n      <td>+7</td>\n      <td><strong>CON</strong></td>\n      <td>21</td>\n      <td>+5</td>\n      <td>+5</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>WIS</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+7</td>\n      <td><strong>CHA</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+8</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Horned Devil",
            "Horned Devil",
        ),
        "**Resistances** Cold<br>\n**Immunities** Fire, Poison; Poisoned<br>\n**Senses** Darkvision 150 ft. (unimpeded by magical Darkness); Passive Perception 13<br>\n**Languages** Infernal; telepathy 120 ft.<br>\n**CR** 11 (XP 7,200; PB +4)",
    ),
    (
        (
            "Monsters A–Z",
            "Horned Devil",
            "Horned Devil",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Horned Devil",
            "Horned Devil",
            "Traits",
        ),
        "**_Diabolical Restoration._** If the devil dies outside the Nine Hells, its body disappears in sulfurous smoke, and it gains a new body instantly, reviving with all its Hit Points somewhere in the Nine Hells.",
    ),
    (
        (
            "Monsters A–Z",
            "Horned Devil",
            "Horned Devil",
            "Traits",
        ),
        "**_Magic Resistance._** The devil has Advantage on saving throws against spells and other magical effects.",
    ),
    (
        (
            "Monsters A–Z",
            "Horned Devil",
            "Horned Devil",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Horned Devil",
            "Horned Devil",
            "Actions",
        ),
        "**_Multiattack._** The devil makes three attacks, using Searing Fork or Hurl Flame in any combination. It can replace one attack with a use of Infernal Tail.",
    ),
    (
        (
            "Monsters A–Z",
            "Horned Devil",
            "Horned Devil",
            "Actions",
        ),
        "**_Searing Fork._** _Melee Attack Roll:_ +10, reach 10 ft. _Hit:_ 15 (2d8 + 6) Piercing damage plus 9 (2d8) Fire damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Horned Devil",
            "Horned Devil",
            "Actions",
        ),
        "**_Hurl Flame._** _Ranged Attack Roll:_ +8, range 150 ft. _Hit:_ 26 (5d8 + 4) Fire damage. If the target is a flammable object that isn't being worn or carried, it starts burning.",
    ),
    (
        (
            "Monsters A–Z",
            "Horned Devil",
            "Horned Devil",
            "Actions",
        ),
        "**_Infernal Tail._** _Dexterity Saving Throw:_ DC 17, one creature the devil can see within 10 feet. _Failure:_ 10 (1d8 + 6) Necrotic damage, and the target receives an infernal wound if it doesn't have one. While wounded, the target loses 10 (3d6) Hit Points at the start of each of its turns. The wound closes after 1 minute, after a spell restores Hit Points to the target, or after the target or a creature within 5 feet of it takes an action to stanch the wound, doing so by succeeding on a DC 17 Wisdom (Medicine) check.",
    ),
    (
        (
            "Monsters A–Z",
            "Hydra",
        ),
        "## Hydra",
    ),
    (
        (
            "Monsters A–Z",
            "Hydra",
            "Hydra",
        ),
        "### Hydra",
    ),
    (
        (
            "Monsters A–Z",
            "Hydra",
            "Hydra",
        ),
        "_Huge Monstrosity, Unaligned_",
    ),
    (
        (
            "Monsters A–Z",
            "Hydra",
            "Hydra",
        ),
        "**AC** 15 **Initiative** +4 (14) <br>\n**HP** 184 (16d12 + 80) <br>\n**Speed** 40 ft., Swim 40 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Hydra",
            "Hydra",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>20</td>\n      <td>+5</td>\n      <td>+5</td>\n      <td><strong>DEX</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CON</strong></td>\n      <td>20</td>\n      <td>+5</td>\n      <td>+5</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>2</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>WIS</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CHA</strong></td>\n      <td>7</td>\n      <td>−2</td>\n      <td>−2</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Hydra",
            "Hydra",
        ),
        "**Skills** Perception +6<br>\n**Immunities** Blinded, Charmed, Deafened, Frightened, Stunned, Unconscious<br>\n**Senses** Darkvision 60 ft.; Passive Perception 16<br>\n**Languages** None<br>\n**CR** 8 (XP 3,900; PB +3)",
    ),
    (
        (
            "Monsters A–Z",
            "Hydra",
            "Hydra",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Hydra",
            "Hydra",
            "Traits",
        ),
        "**_Hold Breath._** The hydra can hold its breath for 1 hour.",
    ),
    (
        (
            "Monsters A–Z",
            "Hydra",
            "Hydra",
            "Traits",
        ),
        "**_Multiple Heads._** The hydra has five heads. Whenever the hydra takes 25 damage or more on a single turn, one of its heads dies. The hydra dies if all its heads are dead. At the end of each of its turns when it has at least one living head, the hydra grows two heads for each of its heads that died since its last turn, unless it has taken Fire damage since its last turn. The hydra regains 20 Hit Points when it grows new heads.",
    ),
    (
        (
            "Monsters A–Z",
            "Hydra",
            "Hydra",
            "Traits",
        ),
        "**_Reactive Heads._** For each head the hydra has beyond one, it gets an extra Reaction that can be used only for Opportunity Attacks.",
    ),
    (
        (
            "Monsters A–Z",
            "Hydra",
            "Hydra",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Hydra",
            "Hydra",
            "Actions",
        ),
        "**_Multiattack._** The hydra makes as many Bite attacks as it has heads.",
    ),
    (
        (
            "Monsters A–Z",
            "Hydra",
            "Hydra",
            "Actions",
        ),
        "**_Bite._** _Melee Attack Roll:_ +8, reach 10 ft. _Hit:_ 10 (1d10 + 5) Piercing damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Ice Devil",
        ),
        "## Ice Devil",
    ),
    (
        (
            "Monsters A–Z",
            "Ice Devil",
            "Ice Devil",
        ),
        "### Ice Devil",
    ),
    (
        (
            "Monsters A–Z",
            "Ice Devil",
            "Ice Devil",
        ),
        "_Large Fiend (Devil), Lawful Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Ice Devil",
            "Ice Devil",
        ),
        "**AC** 18 **Initiative** +7 (17) <br>\n**HP** 228 (24d10 + 96) <br>\n**Speed** 40 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Ice Devil",
            "Ice Devil",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>21</td>\n      <td>+5</td>\n      <td>+5</td>\n      <td><strong>DEX</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+7</td>\n      <td><strong>CON</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+9</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+4</td>\n      <td><strong>WIS</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+7</td>\n      <td><strong>CHA</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+9</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Ice Devil",
            "Ice Devil",
        ),
        "**Skills** Insight +7, Perception +7, Persuasion +9<br>\n**Immunities** Cold, Fire, Poison; Poisoned<br>\n**Senses** Blindsight 120 ft.; Passive Perception 17<br>\n**Languages** Infernal; telepathy 120 ft.<br>\n**CR** 14 (XP 11,500; PB +5)",
    ),
    (
        (
            "Monsters A–Z",
            "Ice Devil",
            "Ice Devil",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Ice Devil",
            "Ice Devil",
            "Traits",
        ),
        "**_Diabolical Restoration._** If the devil dies outside the Nine Hells, its body disappears in sulfurous smoke, and it gains a new body instantly, reviving with all its Hit Points somewhere in the Nine Hells.",
    ),
    (
        (
            "Monsters A–Z",
            "Ice Devil",
            "Ice Devil",
            "Traits",
        ),
        "**_Magic Resistance._** The devil has Advantage on saving throws against spells and other magical effects.",
    ),
    (
        (
            "Monsters A–Z",
            "Ice Devil",
            "Ice Devil",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Ice Devil",
            "Ice Devil",
            "Actions",
        ),
        "**_Multiattack._** The devil makes three Ice Spear attacks. It can replace one attack with a Tail attack.",
    ),
    (
        (
            "Monsters A–Z",
            "Ice Devil",
            "Ice Devil",
            "Actions",
        ),
        "**_Ice Spear._** _Melee or Ranged Attack Roll:_ +10, reach 5 ft. or range 30/120 ft. _Hit:_ 14 (2d8 + 5) Piercing damage plus 10 (3d6) Cold damage. Until the end of its next turn, the target can't take a Bonus Action or Reaction, its Speed decreases by 10 feet, and it can move or take one action on its turn, not both. _Hit or Miss:_ The spear magically returns to the devil's hand immediately after a ranged attack.",
    ),
    (
        (
            "Monsters A–Z",
            "Ice Devil",
            "Ice Devil",
            "Actions",
        ),
        "**_Tail._** _Melee Attack Roll:_ +10, reach 10 ft. _Hit:_ 15 (3d6 + 5) Bludgeoning damage plus 18 (4d8) Cold damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Ice Devil",
            "Ice Devil",
            "Actions",
        ),
        "**_Ice Wall (Recharge 6)._** The devil casts _Wall of Ice_ (level 8 version), requiring no spell components and using Intelligence as the spellcasting ability (spell save DC 17).",
    ),
    (
        (
            "Monsters A–Z",
            "Imp",
        ),
        "## Imp",
    ),
    (
        (
            "Monsters A–Z",
            "Imp",
            "Imp",
        ),
        "### Imp",
    ),
    (
        (
            "Monsters A–Z",
            "Imp",
            "Imp",
        ),
        "_Tiny Fiend (Devil), Lawful Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Imp",
            "Imp",
        ),
        "**AC** 13 **Initiative** +3 (13) <br>\n**HP** 21 (6d4 + 6) <br>\n**Speed** 20 ft., Fly 40 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Imp",
            "Imp",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>6</td>\n      <td>−2</td>\n      <td>−2</td>\n      <td><strong>DEX</strong></td>\n      <td>17</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>CON</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>WIS</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CHA</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Imp",
            "Imp",
        ),
        "**Skills** Deception +4, Insight +3, Stealth +5<br>\n**Resistances** Cold<br>\n**Immunities** Fire, Poison; Poisoned<br>\n**Senses** Darkvision 120 ft. (unimpeded by magical Darkness); Passive Perception 11<br>\n**Languages** Common, Infernal<br>\n**CR** 1 (XP 200; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Imp",
            "Imp",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Imp",
            "Imp",
            "Traits",
        ),
        "**_Magic Resistance._** The imp has Advantage on saving throws against spells and other magical effects.",
    ),
    (
        (
            "Monsters A–Z",
            "Imp",
            "Imp",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Imp",
            "Imp",
            "Actions",
        ),
        "**_Sting._** _Melee Attack Roll:_ +5, reach 5 ft. _Hit:_ 6 (1d6 + 3) Piercing damage plus 7 (2d6) Poison damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Imp",
            "Imp",
            "Actions",
        ),
        "**_Invisibility._** The imp casts _Invisibility_ on itself, requiring no spell components and using Charisma as the spell-casting ability.",
    ),
    (
        (
            "Monsters A–Z",
            "Imp",
            "Imp",
            "Actions",
        ),
        "**_Shape-Shift._** The imp shape-shifts to resemble a rat (Speed 20 ft.), a raven (20 ft., Fly 60 ft.), or a spider (20 ft., Climb 20 ft.), or it returns to its true form. Its game statistics are the same in each form, except for its Speed. Any equipment it is wearing or carrying isn't transformed.",
    ),
    (
        (
            "Monsters A–Z",
            "Incubus",
        ),
        "## Incubus",
    ),
    (
        (
            "Monsters A–Z",
            "Incubus",
            "Incubus",
        ),
        "### Incubus",
    ),
    (
        (
            "Monsters A–Z",
            "Incubus",
            "Incubus",
        ),
        "_Medium Fiend, Neutral Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Incubus",
            "Incubus",
        ),
        "**AC** 15 **Initiative** +3 (13) <br>\n**HP** 66 (12d8 + 12) <br>\n**Speed** 30 ft., Fly 60 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Incubus",
            "Incubus",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>8</td>\n      <td>−1</td>\n      <td>−1</td>\n      <td><strong>DEX</strong></td>\n      <td>17</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>CON</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>WIS</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CHA</strong></td>\n      <td>20</td>\n      <td>+5</td>\n      <td>+5</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Incubus",
            "Incubus",
        ),
        "**Skills** Deception +9, Insight +5, Perception +5, Persuasion +9, Stealth +7<br>\n**Resistances** Cold, Fire, Poison, Psychic<br>\n**Senses** Darkvision 60 ft.; Passive Perception 15<br>\n**Languages** Abyssal, Common, Infernal; telepathy 60 ft.<br>\n**CR** 4 (XP 1,100; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Incubus",
            "Incubus",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Incubus",
            "Incubus",
            "Traits",
        ),
        "**_Succubus Form._** When the incubus finishes a Long Rest, it can shape-shift into a **Succubus**, using that stat block instead of this one. Any equipment it is wearing or carrying isn't transformed.",
    ),
    (
        (
            "Monsters A–Z",
            "Incubus",
            "Incubus",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Incubus",
            "Incubus",
            "Actions",
        ),
        "**_Multiattack._** The incubus makes two Restless Touch attacks.",
    ),
    (
        (
            "Monsters A–Z",
            "Incubus",
            "Incubus",
            "Actions",
        ),
        "**_Restless Touch._** _Melee Attack Roll:_ +7, reach 5 ft. _Hit:_ 15 (3d6 + 5) Psychic damage, and the target is cursed for 24 hours or until the incubus dies. Until the curse ends, the target gains no benefit from finishing Short Rests.",
    ),
    (
        (
            "Monsters A–Z",
            "Incubus",
            "Incubus",
            "Actions",
        ),
        "**_Spellcasting._** The incubus casts one of the following spells, requiring no Material components and using Charisma as the spellcasting ability (spell save DC 15): <br>\n&emsp;**At Will:** _Disguise Self, Etherealness_ <br>\n&emsp;**1/Day Each:** _Dream, Hypnotic Pattern_",
    ),
    (
        (
            "Monsters A–Z",
            "Incubus",
            "Incubus",
            "Bonus Actions",
        ),
        "#### Bonus Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Incubus",
            "Incubus",
            "Bonus Actions",
        ),
        "**_Nightmare (Recharge 6)._** _Wisdom Saving Throw:_ DC 15, one creature the incubus can see within 60 feet. _Failure:_ If the target has 20 Hit Points or fewer, it has the Unconscious condition for 1 hour, until it takes damage, or until a creature within 5 feet of it takes an action to wake it. Otherwise, the target takes 18 (4d8) Psychic damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Invisible Stalker",
        ),
        "## Invisible Stalker",
    ),
    (
        (
            "Monsters A–Z",
            "Invisible Stalker",
            "Invisible Stalker",
        ),
        "### Invisible Stalker",
    ),
    (
        (
            "Monsters A–Z",
            "Invisible Stalker",
            "Invisible Stalker",
        ),
        "_Large Elemental, Neutral_",
    ),
    (
        (
            "Monsters A–Z",
            "Invisible Stalker",
            "Invisible Stalker",
        ),
        "**AC** 14 **Initiative** +7 (22) <br>\n**HP** 97 (13d10 + 26) <br>\n**Speed** 50 ft., Fly 50 ft. (hover) <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Invisible Stalker",
            "Invisible Stalker",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>DEX</strong></td>\n      <td>19</td>\n      <td>+4</td>\n      <td>+4</td>\n      <td><strong>CON</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>WIS</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CHA</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Invisible Stalker",
            "Invisible Stalker",
        ),
        "**Skills** Perception +8, Stealth +10<br>\n**Resistances** Bludgeoning, Piercing, Slashing<br>\n**Immunities** Poison; Exhaustion, Grappled, Paralyzed, Petrified, Poisoned, Prone, Restrained, Unconscious<br>\n**Senses** Darkvision 60 ft.; Passive Perception 18<br>\n**Languages** Common, Primordial (Auran)<br>\n**CR** 6 (XP 2,300; PB +3)",
    ),
    (
        (
            "Monsters A–Z",
            "Invisible Stalker",
            "Invisible Stalker",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Invisible Stalker",
            "Invisible Stalker",
            "Traits",
        ),
        "**_Air Form._** The stalker can enter an enemy's space and stop there. It can move through a space as narrow as 1 inch without expending extra movement to do so.",
    ),
    (
        (
            "Monsters A–Z",
            "Invisible Stalker",
            "Invisible Stalker",
            "Traits",
        ),
        "**_Invisibility._** The stalker has the Invisible condition.",
    ),
    (
        (
            "Monsters A–Z",
            "Invisible Stalker",
            "Invisible Stalker",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Invisible Stalker",
            "Invisible Stalker",
            "Actions",
        ),
        "**_Multiattack._** The stalker makes three Wind Swipe attacks. It can replace one attack with a use of Vortex.",
    ),
    (
        (
            "Monsters A–Z",
            "Invisible Stalker",
            "Invisible Stalker",
            "Actions",
        ),
        "**_Wind Swipe._** _Melee Attack Roll:_ +7, reach 5 ft. _Hit:_ 11 (2d6 + 4) Force damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Invisible Stalker",
            "Invisible Stalker",
            "Actions",
        ),
        "**_Vortex._** _Constitution Saving Throw:_ DC 14, one Large or smaller creature in the stalker's space. _Failure:_ 7 (1d8 + 3) Thunder damage, and the target has the Grappled condition (escape DC 13). Until the grapple ends, the target can't cast spells with a Verbal component and takes 7 (2d6) Thunder damage at the start of each of the stalker's turns.",
    ),
    (
        (
            "Monsters A–Z",
            "Iron Golem",
        ),
        "## Iron Golem",
    ),
    (
        (
            "Monsters A–Z",
            "Iron Golem",
            "Iron Golem",
        ),
        "### Iron Golem",
    ),
    (
        (
            "Monsters A–Z",
            "Iron Golem",
            "Iron Golem",
        ),
        "_Large Construct, Unaligned_",
    ),
    (
        (
            "Monsters A–Z",
            "Iron Golem",
            "Iron Golem",
        ),
        "**AC** 20 **Initiative** +9 (19) <br>\n**HP** 252 (24d10 + 120) <br>\n**Speed** 30 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Iron Golem",
            "Iron Golem",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>24</td>\n      <td>+7</td>\n      <td>+7</td>\n      <td><strong>DEX</strong></td>\n      <td>9</td>\n      <td>−1</td>\n      <td>−1</td>\n      <td><strong>CON</strong></td>\n      <td>20</td>\n      <td>+5</td>\n      <td>+5</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>3</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>WIS</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CHA</strong></td>\n      <td>1</td>\n      <td>−5</td>\n      <td>−5</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Iron Golem",
            "Iron Golem",
        ),
        "**Immunities** Fire, Poison, Psychic; Charmed, Exhaustion, Frightened, Paralyzed, Petrified, Poisoned<br>\n**Senses** Darkvision 120 ft.; Passive Perception 10<br>\n**Languages** Understands Common plus two other languages but can't speak<br>\n**CR** 16 (XP 15,000; PB +5)",
    ),
    (
        (
            "Monsters A–Z",
            "Iron Golem",
            "Iron Golem",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Iron Golem",
            "Iron Golem",
            "Traits",
        ),
        "**_Fire Absorption._** Whenever the golem is subjected to Fire damage, it regains a number of Hit Points equal to the Fire damage dealt.",
    ),
    (
        (
            "Monsters A–Z",
            "Iron Golem",
            "Iron Golem",
            "Traits",
        ),
        "**_Immutable Form._** The golem can't shape-shift.",
    ),
    (
        (
            "Monsters A–Z",
            "Iron Golem",
            "Iron Golem",
            "Traits",
        ),
        "**_Magic Resistance._** The golem has Advantage on saving throws against spells and other magical effects.",
    ),
    (
        (
            "Monsters A–Z",
            "Iron Golem",
            "Iron Golem",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Iron Golem",
            "Iron Golem",
            "Actions",
        ),
        "**_Multiattack._** The golem makes two attacks, using Bladed Arm or Fiery Bolt in any combination.",
    ),
    (
        (
            "Monsters A–Z",
            "Iron Golem",
            "Iron Golem",
            "Actions",
        ),
        "**_Bladed Arm._** _Melee Attack Roll:_ +12, reach 10 ft. _Hit:_ 20 (3d8 + 7) Slashing damage plus 10 (3d6) Fire damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Iron Golem",
            "Iron Golem",
            "Actions",
        ),
        "**_Fiery Bolt._** _Ranged Attack Roll:_ +10, range 120 ft. _Hit:_ 36 (8d8) Fire damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Iron Golem",
            "Iron Golem",
            "Actions",
        ),
        "**_Poison Breath (Recharge 6)._** _Constitution Saving Throw:_ DC 18, each creature in a 60-foot Cone. _Failure:_ 55 (10d10) Poison damage. _Success:_ Half damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Knight",
        ),
        "## Knight",
    ),
    (
        (
            "Monsters A–Z",
            "Knight",
            "Knight",
        ),
        "### Knight",
    ),
    (
        (
            "Monsters A–Z",
            "Knight",
            "Knight",
        ),
        "_Medium or Small Humanoid, Neutral_",
    ),
    (
        (
            "Monsters A–Z",
            "Knight",
            "Knight",
        ),
        "**AC** 18 **Initiative** +0 (10) <br>\n**HP** 52 (8d8 + 16) <br>\n**Speed** 30 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Knight",
            "Knight",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>DEX</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CON</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+4</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>WIS</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+2</td>\n      <td><strong>CHA</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Knight",
            "Knight",
        ),
        "**Immunities** Frightened<br>\n**Gear** Greatsword, Heavy Crossbow, Plate Armor<br>\n**Senses** Passive Perception 10<br>\n**Languages** Common plus one other language<br>\n**CR** 3 (XP 700; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Knight",
            "Knight",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Knight",
            "Knight",
            "Actions",
        ),
        "**_Multiattack._** The knight makes two attacks, using Greatsword or Heavy Crossbow in any combination.",
    ),
    (
        (
            "Monsters A–Z",
            "Knight",
            "Knight",
            "Actions",
        ),
        "**_Greatsword._** _Melee Attack Roll:_ +5, reach 5 ft. _Hit:_ 10 (2d6 + 3) Slashing damage plus 4 (1d8) Radiant damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Knight",
            "Knight",
            "Actions",
        ),
        "**_Heavy Crossbow._** _Ranged Attack Roll:_ +2, range 100/400 ft. _Hit:_ 11 (2d10) Piercing damage plus 4 (1d8) Radiant damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Knight",
            "Knight",
            "Reactions",
        ),
        "#### Reactions",
    ),
    (
        (
            "Monsters A–Z",
            "Knight",
            "Knight",
            "Reactions",
        ),
        "**_Parry._** _Trigger:_ The knight is hit by a melee attack roll while holding a weapon. _Response:_ The knight adds 2 to its AC against that attack, possibly causing it to miss.",
    ),
    (
        (
            "Monsters A–Z",
            "Kobold",
        ),
        "## Kobold",
    ),
    (
        (
            "Monsters A–Z",
            "Kobold",
            "Kobold Warrior",
        ),
        "### Kobold Warrior",
    ),
    (
        (
            "Monsters A–Z",
            "Kobold",
            "Kobold Warrior",
        ),
        "_Small Dragon, Neutral_",
    ),
    (
        (
            "Monsters A–Z",
            "Kobold",
            "Kobold Warrior",
        ),
        "**AC** 14 **Initiative** +2 (12) <br>\n**HP** 7 (3d6 − 3) <br>\n**Speed** 30 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Kobold",
            "Kobold Warrior",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>7</td>\n      <td>−2</td>\n      <td>−2</td>\n      <td><strong>DEX</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CON</strong></td>\n      <td>9</td>\n      <td>−1</td>\n      <td>−1</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>8</td>\n      <td>−1</td>\n      <td>−1</td>\n      <td><strong>WIS</strong></td>\n      <td>7</td>\n      <td>−2</td>\n      <td>−2</td>\n      <td><strong>CHA</strong></td>\n      <td>8</td>\n      <td>−1</td>\n      <td>−1</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Kobold",
            "Kobold Warrior",
        ),
        "**Gear** Daggers (3)<br>\n**Senses** Darkvision 60 ft.; Passive Perception 8<br>\n**Languages** Common, Draconic<br>\n**CR** 1/8 (XP 25; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Kobold",
            "Kobold Warrior",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Kobold",
            "Kobold Warrior",
            "Traits",
        ),
        "**_Pack Tactics._** The kobold has Advantage on an attack roll against a creature if at least one of the kobold's allies is within 5 feet of the creature and the ally doesn't have the Incapacitated condition.",
    ),
    (
        (
            "Monsters A–Z",
            "Kobold",
            "Kobold Warrior",
            "Traits",
        ),
        "**_Sunlight Sensitivity._** While in sunlight, the kobold has Disadvantage on ability checks and attack rolls.",
    ),
    (
        (
            "Monsters A–Z",
            "Kobold",
            "Kobold Warrior",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Kobold",
            "Kobold Warrior",
            "Actions",
        ),
        "**_Dagger._** _Melee or Ranged Attack Roll:_ +4, reach 5 ft. or range 20/60 ft. _Hit:_ 4 (1d4 + 2) Piercing damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Kraken",
        ),
        "## Kraken",
    ),
    (
        (
            "Monsters A–Z",
            "Kraken",
            "Kraken",
        ),
        "### Kraken",
    ),
    (
        (
            "Monsters A–Z",
            "Kraken",
            "Kraken",
        ),
        "_Gargantuan Monstrosity (Titan), Chaotic Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Kraken",
            "Kraken",
        ),
        "**AC** 18 **Initiative** +14 (24) <br>\n**HP** 481 (26d20 + 208) <br>\n**Speed** 30 ft., Swim 120 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Kraken",
            "Kraken",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>30</td>\n      <td>+10</td>\n      <td>+17</td>\n      <td><strong>DEX</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+7</td>\n      <td><strong>CON</strong></td>\n      <td>26</td>\n      <td>+8</td>\n      <td>+15</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>22</td>\n      <td>+6</td>\n      <td>+6</td>\n      <td><strong>WIS</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+11</td>\n      <td><strong>CHA</strong></td>\n      <td>20</td>\n      <td>+5</td>\n      <td>+5</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Kraken",
            "Kraken",
        ),
        "**Skills** History +13, Perception +11<br>\n**Immunities** Cold, Lightning; Frightened, Grappled, Paralyzed, Restrained<br>\n**Senses** Truesight 120 ft.; Passive Perception 21<br>\n**Languages** Understands Abyssal, Celestial, Infernal, and Primordial but can't speak; telepathy 120 ft.<br>\n**CR** 23 (XP 50,000, or 62,000 in lair; PB +7)",
    ),
    (
        (
            "Monsters A–Z",
            "Kraken",
            "Kraken",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Kraken",
            "Kraken",
            "Traits",
        ),
        "**_Amphibious._** The kraken can breathe air and water.",
    ),
    (
        (
            "Monsters A–Z",
            "Kraken",
            "Kraken",
            "Traits",
        ),
        "**_Legendary Resistance (4/Day, or 5/Day in Lair)._** If the kraken fails a saving throw, it can choose to succeed instead.",
    ),
    (
        (
            "Monsters A–Z",
            "Kraken",
            "Kraken",
            "Traits",
        ),
        "**_Siege Monster._** The kraken deals double damage to objects and structures.",
    ),
    (
        (
            "Monsters A–Z",
            "Kraken",
            "Kraken",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Kraken",
            "Kraken",
            "Actions",
        ),
        "**_Multiattack._** The kraken makes two Tentacle attacks and uses Fling, Lightning Strike, or Swallow.",
    ),
    (
        (
            "Monsters A–Z",
            "Kraken",
            "Kraken",
            "Actions",
        ),
        "**_Tentacle._** _Melee Attack Roll:_ +17, reach 30 ft. _Hit:_ 24 (4d6 + 10) Bludgeoning damage. The target has the Grappled condition (escape DC 20) from one of ten tentacles, and it has the Restrained condition until the grapple ends.",
    ),
    (
        (
            "Monsters A–Z",
            "Kraken",
            "Kraken",
            "Actions",
        ),
        "**_Fling._** The kraken throws a Large or smaller creature Grappled by it to a space it can see within 60 feet of itself that isn't in the air. _Dexterity Saving Throw:_ DC 25, the creature thrown and each creature in the destination space. _Failure:_ 18 (4d8) Bludgeoning damage, and the target has the Prone condition. _Success:_ Half damage only.",
    ),
    (
        (
            "Monsters A–Z",
            "Kraken",
            "Kraken",
            "Actions",
        ),
        "**_Lightning Strike._** _Dexterity Saving Throw:_ DC 23, one creature the kraken can see within 120 feet. _Failure:_ 33 (6d10) Lightning damage. _Success:_ Half damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Kraken",
            "Kraken",
            "Actions",
        ),
        "**_Swallow._** _Dexterity Saving Throw:_ DC 25, one creature Grappled by the kraken (it can have up to four creatures swallowed at a time). _Failure:_ 23 (3d8 + 10) Piercing damage. If the target is Large or smaller, it is swallowed and no longer Grappled. A swallowed creature has the Restrained condition, has Total Cover against attacks and other effects outside the kraken, and takes 24 (7d6) Acid damage at the start of each of its turns. <br>\n&emsp;If the kraken takes 50 damage or more on a single turn from a creature inside it, the kraken must succeed on a DC 25 Constitution saving throw at the end of that turn or regurgitate all swallowed creatures, each of which falls in a space within 10 feet of the kraken with the Prone condition. If the kraken dies, any swallowed creature no longer has the Restrained condition and can escape from the corpse using 15 feet of movement, exiting Prone.",
    ),
    (
        (
            "Monsters A–Z",
            "Kraken",
            "Kraken",
            "Legendary Actions",
        ),
        "#### Legendary Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Kraken",
            "Kraken",
            "Legendary Actions",
        ),
        "_Legendary Action Uses: 3 (4 in Lair). Immediately after another creature's turn, the kraken can expend a use to take one of the following actions. The kraken regains all expended uses at the start of each of its turns._",
    ),
    (
        (
            "Monsters A–Z",
            "Kraken",
            "Kraken",
            "Legendary Actions",
        ),
        "**_Storm Bolt._** The kraken uses Lightning Strike.",
    ),
    (
        (
            "Monsters A–Z",
            "Kraken",
            "Kraken",
            "Legendary Actions",
        ),
        "**_Toxic Ink._** _Constitution Saving Throw:_ DC 23, each creature in a 15-foot Emanation originating from the kraken while it is underwater. _Failure:_ The target has the Blinded and Poisoned conditions until the end of the kraken's next turn. The kraken then moves up to its Speed. _Failure or Success:_ The kraken can't take this action again until the start of its next turn.",
    ),
    (
        (
            "Monsters A–Z",
            "Lamia",
        ),
        "## Lamia",
    ),
    (
        (
            "Monsters A–Z",
            "Lamia",
            "Lamia",
        ),
        "### Lamia",
    ),
    (
        (
            "Monsters A–Z",
            "Lamia",
            "Lamia",
        ),
        "_Large Fiend, Chaotic Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Lamia",
            "Lamia",
        ),
        "**AC** 13 **Initiative** +1 (11) <br>\n**HP** 97 (13d10 + 26) <br>\n**Speed** 40 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Lamia",
            "Lamia",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>DEX</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CON</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>WIS</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CHA</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Lamia",
            "Lamia",
        ),
        "**Skills** Deception +7, Insight +4, Stealth +5<br>\n**Senses** Darkvision 60 ft.; Passive Perception 12<br>\n**Languages** Abyssal, Common<br>\n**CR** 4 (XP 1,100; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Lamia",
            "Lamia",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Lamia",
            "Lamia",
            "Actions",
        ),
        "**_Multiattack._** The lamia makes two Claw attacks. It can replace one attack with a use of Corrupting Touch.",
    ),
    (
        (
            "Monsters A–Z",
            "Lamia",
            "Lamia",
            "Actions",
        ),
        "**_Claw._** _Melee Attack Roll:_ +5, reach 5 ft. _Hit:_ 7 (1d8 + 3) Slashing damage plus 7 (2d6) Psychic damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Lamia",
            "Lamia",
            "Actions",
        ),
        "**_Corrupting Touch._** _Wisdom Saving Throw:_ DC 13, one creature the lamia can see within 5 feet. _Failure:_ 13 (3d8) Psychic damage, and the target is cursed for 1 hour. Until the curse ends, the target has the Charmed and Poisoned conditions.",
    ),
    (
        (
            "Monsters A–Z",
            "Lamia",
            "Lamia",
            "Actions",
        ),
        "**_Spellcasting._** The lamia casts one of the following spells, requiring no Material components and using Charisma as the spellcasting ability (spell save DC 13): <br>\n&emsp;**At Will:** _Disguise Self_ (can appear as a Large or Medium biped), _Minor Illusion_<br>\n&emsp;**1/Day Each:** _Geas_, _Major Image_, _Scrying_",
    ),
    (
        (
            "Monsters A–Z",
            "Lamia",
            "Lamia",
            "Bonus Actions",
        ),
        "#### Bonus Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Lamia",
            "Lamia",
            "Bonus Actions",
        ),
        "**_Leap._** The lamia jumps up to 30 feet by spending 10 feet of movement.",
    ),
    (
        (
            "Monsters A–Z",
            "Lemure",
        ),
        "## Lemure",
    ),
    (
        (
            "Monsters A–Z",
            "Lemure",
            "Lemure",
        ),
        "### Lemure",
    ),
    (
        (
            "Monsters A–Z",
            "Lemure",
            "Lemure",
        ),
        "_Medium Fiend (Devil), Lawful Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Lemure",
            "Lemure",
        ),
        "**AC** 9 **Initiative** −3 (7) <br>\n**HP** 9 (2d8) <br>\n**Speed** 20 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Lemure",
            "Lemure",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>DEX</strong></td>\n      <td>5</td>\n      <td>−3</td>\n      <td>−3</td>\n      <td><strong>CON</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>1</td>\n      <td>−5</td>\n      <td>−5</td>\n      <td><strong>WIS</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CHA</strong></td>\n      <td>3</td>\n      <td>−4</td>\n      <td>−4</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Lemure",
            "Lemure",
        ),
        "**Resistances** Cold<br>\n**Immunities** Fire, Poison; Charmed, Frightened, Poisoned<br>\n**Senses** Darkvision 120 ft. (unimpeded by magical Darkness); Passive Perception 10<br>\n**Languages** Understands Infernal but can't speak<br>\n**CR** 0 (XP 10; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Lemure",
            "Lemure",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Lemure",
            "Lemure",
            "Traits",
        ),
        "**_Hellish Restoration._** If the lemure dies in the Nine Hells, it revives with all its Hit Points in 1d10 days unless it is killed by a creature under the effects of a _Bless_ spell or its remains are sprinkled with Holy Water.",
    ),
    (
        (
            "Monsters A–Z",
            "Lemure",
            "Lemure",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Lemure",
            "Lemure",
            "Actions",
        ),
        "**_Vile Slime._** _Melee Attack Roll:_ +2, reach 5 ft. _Hit:_ 2 (1d4) Poison damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Lich",
        ),
        "## Lich",
    ),
    (
        (
            "Monsters A–Z",
            "Lich",
            "Lich",
        ),
        "### Lich",
    ),
    (
        (
            "Monsters A–Z",
            "Lich",
            "Lich",
        ),
        "_Medium Undead (Wizard), Neutral Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Lich",
            "Lich",
        ),
        "**AC** 20 **Initiative** +17 (27) <br>\n**HP** 315 (42d8 + 126) <br>\n**Speed** 30 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Lich",
            "Lich",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>DEX</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+10</td>\n      <td><strong>CON</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+10</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>21</td>\n      <td>+5</td>\n      <td>+12</td>\n      <td><strong>WIS</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+9</td>\n      <td><strong>CHA</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Lich",
            "Lich",
        ),
        "**Skills** Arcana +19, History +12, Insight +9, Perception +9<br>\n**Resistances** Cold, Lightning<br>\n**Immunities** Necrotic, Poison; Charmed, Exhaustion, Frightened, Paralyzed, Poisoned<br>\n**Gear** Component Pouch<br>\n**Senses** Truesight 120 ft.; Passive Perception 19<br>\n**Languages** All<br>\n**CR** 21 (XP 33,000, or 41,000 in lair; PB +7)",
    ),
    (
        (
            "Monsters A–Z",
            "Lich",
            "Lich",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Lich",
            "Lich",
            "Traits",
        ),
        "**_Legendary Resistance (4/Day, or 5/Day in Lair)._** If the lich fails a saving throw, it can choose to succeed instead.",
    ),
    (
        (
            "Monsters A–Z",
            "Lich",
            "Lich",
            "Traits",
        ),
        "**_Spirit Jar._** If destroyed, the lich reforms in 1d10 days if it has a spirit jar, reviving with all its Hit Points. The new body appears in an unoccupied space within the lich's lair.",
    ),
    (
        (
            "Monsters A–Z",
            "Lich",
            "Lich",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Lich",
            "Lich",
            "Actions",
        ),
        "**_Multiattack._** The lich makes three attacks, using Eldritch Burst or Paralyzing Touch in any combination.",
    ),
    (
        (
            "Monsters A–Z",
            "Lich",
            "Lich",
            "Actions",
        ),
        "**_Eldritch Burst._** _Melee or Ranged Attack Roll:_ +12, reach 5 ft. or range 120 ft. _Hit:_ 31 (4d12 + 5) Force damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Lich",
            "Lich",
            "Actions",
        ),
        "**_Paralyzing Touch._** _Melee Attack Roll:_ +12, reach 5 ft. _Hit:_ 15 (3d6 + 5) Cold damage, and the target has the Paralyzed condition until the start of the lich's next turn.",
    ),
    (
        (
            "Monsters A–Z",
            "Lich",
            "Lich",
            "Actions",
        ),
        "**_Spellcasting._** The lich casts one of the following spells, using Intelligence as the spellcasting ability (spell save DC 20): <br>\n&emsp;**At Will:** _Detect Magic, Detect Thoughts, Dispel Magic, Fireball_ (level 5 version), _Invisibility, Lightning Bolt_ (level 5 version), _Mage Hand, Prestidigitation_ <br>\n&emsp;**2/Day Each:** _Animate Dead, Dimension Door, Plane Shift_ <br>\n&emsp;**1/Day Each:** _Chain Lightning, Finger of Death, Power Word Kill, Scrying_",
    ),
    (
        (
            "Monsters A–Z",
            "Lich",
            "Lich",
            "Reactions",
        ),
        "#### Reactions",
    ),
    (
        (
            "Monsters A–Z",
            "Lich",
            "Lich",
            "Reactions",
        ),
        "**_Protective Magic._** The lich casts _Counterspell_ or _Shield_ in response to the spell's trigger, using the same spellcasting ability as Spellcasting.",
    ),
    (
        (
            "Monsters A–Z",
            "Lich",
            "Lich",
            "Legendary Actions",
        ),
        "#### Legendary Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Lich",
            "Lich",
            "Legendary Actions",
        ),
        "_Legendary Action Uses: 3 (4 in Lair). Immediately after another creature's turn, the lich can expend a use to take one of the following actions. The lich regains all expended uses at the start of each of its turns._",
    ),
    (
        (
            "Monsters A–Z",
            "Lich",
            "Lich",
            "Legendary Actions",
        ),
        "**_Deathly Teleport._** The lich teleports up to 60 feet to an unoccupied space it can see, and each creature within 10 feet of the space it left takes 11 (2d10) Necrotic damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Lich",
            "Lich",
            "Legendary Actions",
        ),
        "**_Disrupt Life._** _Constitution Saving Throw:_ DC 20, each creature that isn't an Undead in a 20-foot Emanation originating from the lich. _Failure:_ 31 (9d6) Necrotic damage. _Success:_ Half damage. _Failure or Success:_ The lich can't take this action again until the start of its next turn.",
    ),
    (
        (
            "Monsters A–Z",
            "Lich",
            "Lich",
            "Legendary Actions",
        ),
        "**_Frightening Gaze._** The lich casts _Fear_, using the same spellcasting ability as Spellcasting. The lich can't take this action again until the start of its next turn.",
    ),
    (
        (
            "Monsters A–Z",
            "Mages",
        ),
        "## Mages",
    ),
    (
        (
            "Monsters A–Z",
            "Mages",
            "Mage",
        ),
        "### Mage",
    ),
    (
        (
            "Monsters A–Z",
            "Mages",
            "Mage",
        ),
        "_Medium or Small Humanoid (Wizard), Neutral_",
    ),
    (
        (
            "Monsters A–Z",
            "Mages",
            "Mage",
        ),
        "**AC** 15 **Initiative** +2 (12) <br>\n**HP** 81 (18d8) <br>\n**Speed** 30 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Mages",
            "Mage",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>9</td>\n      <td>−1</td>\n      <td>−1</td>\n      <td><strong>DEX</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CON</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>17</td>\n      <td>+3</td>\n      <td>+6</td>\n      <td><strong>WIS</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+4</td>\n      <td><strong>CHA</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Mages",
            "Mage",
        ),
        "**Skills** Arcana +6, History +6, Perception +4<br>\n**Gear** Wand<br>\n**Senses** Passive Perception 14<br>\n**Languages** Common plus three other languages<br>\n**CR** 6 (XP 2,300; PB +3)",
    ),
    (
        (
            "Monsters A–Z",
            "Mages",
            "Mage",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Mages",
            "Mage",
            "Actions",
        ),
        "**_Multiattack._** The mage makes three Arcane Burst attacks.",
    ),
    (
        (
            "Monsters A–Z",
            "Mages",
            "Mage",
            "Actions",
        ),
        "**_Arcane Burst._** _Melee or Ranged Attack Roll:_ +6, reach 5 ft. or range 120 ft. _Hit:_ 16 (3d8 + 3) Force damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Mages",
            "Mage",
            "Actions",
        ),
        "**_Spellcasting._** The mage casts one of the following spells, using Intelligence as the spellcasting ability (spell save DC 14): <br>\n&emsp;**At Will:** _Detect Magic_, _Light_, _Mage Armor_ (included in AC), _Mage Hand_, _Prestidigitation_ <br>\n&emsp;**2/Day Each:** _Fireball_ (level 4 version), _Invisibility_ <br>\n&emsp;**1/Day Each:** _Cone of Cold_, _Fly_",
    ),
    (
        (
            "Monsters A–Z",
            "Mages",
            "Mage",
            "Bonus Actions",
        ),
        "#### Bonus Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Mages",
            "Mage",
            "Bonus Actions",
        ),
        "**_Misty Step (3/Day)._** The mage casts _Misty Step_, using the same spellcasting ability as Spellcasting.",
    ),
    (
        (
            "Monsters A–Z",
            "Mages",
            "Mage",
            "Reactions",
        ),
        "#### Reactions",
    ),
    (
        (
            "Monsters A–Z",
            "Mages",
            "Mage",
            "Reactions",
        ),
        "**_Protective Magic (3/Day)._** The mage casts _Counterspell_ or _Shield_ in response to the spell's trigger, using the same spellcasting ability as Spellcasting.",
    ),
    (
        (
            "Monsters A–Z",
            "Mages",
            "Archmage",
        ),
        "### Archmage",
    ),
    (
        (
            "Monsters A–Z",
            "Mages",
            "Archmage",
        ),
        "_Medium or Small Humanoid (Wizard), Neutral_",
    ),
    (
        (
            "Monsters A–Z",
            "Mages",
            "Archmage",
        ),
        "**AC** 17 **Initiative** +7 (17) <br>\n**HP** 170 (31d8 + 31) <br>\n**Speed** 30 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Mages",
            "Archmage",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>DEX</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CON</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>20</td>\n      <td>+5</td>\n      <td>+9</td>\n      <td><strong>WIS</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+6</td>\n      <td><strong>CHA</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Mages",
            "Archmage",
        ),
        "**Skills** Arcana +13, History +9, Perception +6<br>\n**Immunities** Psychic; Charmed (with _Mind Blank_)<br>\n**Gear** Wand<br>\n**Senses** Passive Perception 16<br>\n**Languages** Common plus five other languages<br>\n**CR** 12 (XP 8,000; PB +4)",
    ),
    (
        (
            "Monsters A–Z",
            "Mages",
            "Archmage",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Mages",
            "Archmage",
            "Traits",
        ),
        "**_Magic Resistance._** The archmage has Advantage on saving throws against spells and other magical effects.",
    ),
    (
        (
            "Monsters A–Z",
            "Mages",
            "Archmage",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Mages",
            "Archmage",
            "Actions",
        ),
        "**_Multiattack._** The archmage makes four Arcane Burst attacks.",
    ),
    (
        (
            "Monsters A–Z",
            "Mages",
            "Archmage",
            "Actions",
        ),
        "**_Arcane Burst._** _Melee or Ranged Attack Roll:_ +9, reach 5 ft. or range 150 ft. _Hit:_ 27 (4d10 + 5) Force damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Mages",
            "Archmage",
            "Actions",
        ),
        "**_Spellcasting._** The archmage casts one of the following spells, using Intelligence as the spellcasting ability (spell save DC 17): <br>\n&emsp;**At Will:** _Detect Magic_, _Detect Thoughts_, _Disguise Self_, _Invisibility_, _Light_, _Mage Armor_ (included in AC), _Mage Hand_, _Prestidigitation_ <br>\n&emsp;**2/Day Each:** _Fly_, _Lightning Bolt_ (level 7 version) <br>\n&emsp;**1/Day Each:** _Cone of Cold_ (level 9 version), _Mind Blank_ (cast before combat), _Scrying_, _Teleport_",
    ),
    (
        (
            "Monsters A–Z",
            "Mages",
            "Archmage",
            "Bonus Actions",
        ),
        "#### Bonus Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Mages",
            "Archmage",
            "Bonus Actions",
        ),
        "**_Misty Step (3/Day)._** The mage casts _Misty Step_, using the same spellcasting ability as Spellcasting.",
    ),
    (
        (
            "Monsters A–Z",
            "Mages",
            "Archmage",
            "Reactions",
        ),
        "#### Reactions",
    ),
    (
        (
            "Monsters A–Z",
            "Mages",
            "Archmage",
            "Reactions",
        ),
        "**_Protective Magic (3/Day)._** The archmage casts _Counterspell_ or _Shield_ in response to the spell's trigger, using the same spellcasting ability as Spellcasting.",
    ),
    (
        (
            "Monsters A–Z",
            "Magmin",
        ),
        "## Magmin",
    ),
    (
        (
            "Monsters A–Z",
            "Magmin",
            "Magmin",
        ),
        "### Magmin",
    ),
    (
        (
            "Monsters A–Z",
            "Magmin",
            "Magmin",
        ),
        "_Small Elemental, Chaotic Neutral_",
    ),
    (
        (
            "Monsters A–Z",
            "Magmin",
            "Magmin",
        ),
        "**AC** 14 **Initiative** +2 (12) <br>\n**HP** 13 (3d6 + 3) <br>\n**Speed** 30 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Magmin",
            "Magmin",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>7</td>\n      <td>−2</td>\n      <td>−2</td>\n      <td><strong>DEX</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CON</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>8</td>\n      <td>−1</td>\n      <td>−1</td>\n      <td><strong>WIS</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CHA</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Magmin",
            "Magmin",
        ),
        "**Immunities** Fire<br>\n**Senses** Darkvision 60 ft.; Passive Perception 10<br>\n**Languages** Primordial (Ignan)<br>\n**CR** 1/2 (XP 100; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Magmin",
            "Magmin",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Magmin",
            "Magmin",
            "Traits",
        ),
        "**_Death Burst._** The magmin explodes when it dies. _Dexterity Saving Throw:_ DC 11, each creature in a 10-foot Emanation originating from the magmin. _Failure:_ 7 (2d6) Fire damage. _Success:_ Half damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Magmin",
            "Magmin",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Magmin",
            "Magmin",
            "Actions",
        ),
        "**_Touch._** _Melee Attack Roll:_ +4, reach 5 ft. _Hit:_ 7 (2d4 + 2) Fire damage. If the target is a creature or a flammable object that isn't being worn or carried, it starts burning.",
    ),
    (
        (
            "Monsters A–Z",
            "Magmin",
            "Magmin",
            "Bonus Actions",
        ),
        "#### Bonus Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Magmin",
            "Magmin",
            "Bonus Actions",
        ),
        "**_Ignited Illumination._** The magmin sets itself ablaze or extinguishes its flames. While ablaze, the magmin sheds Bright Light in a 10-foot radius and Dim Light for an additional 10 feet.",
    ),
    (
        (
            "Monsters A–Z",
            "Manticore",
        ),
        "## Manticore",
    ),
    (
        (
            "Monsters A–Z",
            "Manticore",
            "Manticore",
        ),
        "### Manticore",
    ),
    (
        (
            "Monsters A–Z",
            "Manticore",
            "Manticore",
        ),
        "_Large Monstrosity, Lawful Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Manticore",
            "Manticore",
        ),
        "**AC** 14 **Initiative** +3 (13) <br>\n**HP** 68 (8d10 + 24) <br>\n**Speed** 30 ft., Fly 50 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Manticore",
            "Manticore",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>17</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>DEX</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>CON</strong></td>\n      <td>17</td>\n      <td>+3</td>\n      <td>+3</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>7</td>\n      <td>−2</td>\n      <td>−2</td>\n      <td><strong>WIS</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CHA</strong></td>\n      <td>8</td>\n      <td>−1</td>\n      <td>−1</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Manticore",
            "Manticore",
        ),
        "**Senses** Darkvision 60 ft.; Passive Perception 11<br>\n**Languages** Common<br>\n**CR** 3 (XP 700; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Manticore",
            "Manticore",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Manticore",
            "Manticore",
            "Actions",
        ),
        "**_Multiattack._** The manticore makes three attacks, using Rend or Tail Spike in any combination.",
    ),
    (
        (
            "Monsters A–Z",
            "Manticore",
            "Manticore",
            "Actions",
        ),
        "**_Rend._** _Melee Attack Roll:_ +5, reach 5 ft. _Hit:_ 7 (1d8 + 3) Slashing damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Manticore",
            "Manticore",
            "Actions",
        ),
        "**_Tail Spike._** _Ranged Attack Roll:_ +5, range 100/200 ft. _Hit:_ 7 (1d8 + 3) Piercing damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Marilith",
        ),
        "## Marilith",
    ),
    (
        (
            "Monsters A–Z",
            "Marilith",
            "Marilith",
        ),
        "### Marilith",
    ),
    (
        (
            "Monsters A–Z",
            "Marilith",
            "Marilith",
        ),
        "_Large Fiend (Demon), Chaotic Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Marilith",
            "Marilith",
        ),
        "**AC** 16 **Initiative** +10 (20) <br>\n**HP** 220 (21d10 + 105) <br>\n**Speed** 40 ft., Climb 40 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Marilith",
            "Marilith",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+9</td>\n      <td><strong>DEX</strong></td>\n      <td>20</td>\n      <td>+5</td>\n      <td>+5</td>\n      <td><strong>CON</strong></td>\n      <td>20</td>\n      <td>+5</td>\n      <td>+10</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+4</td>\n      <td><strong>WIS</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+8</td>\n      <td><strong>CHA</strong></td>\n      <td>20</td>\n      <td>+5</td>\n      <td>+10</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Marilith",
            "Marilith",
        ),
        "**Skills** Perception +8<br>\n**Resistances** Cold, Fire, Lightning<br>\n**Immunities** Poison; Poisoned<br>\n**Senses** Truesight 120 ft.; Passive Perception 18<br>\n**Languages** Abyssal; telepathy 120 ft.<br>\n**CR** 16 (XP 15,000; PB +5)",
    ),
    (
        (
            "Monsters A–Z",
            "Marilith",
            "Marilith",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Marilith",
            "Marilith",
            "Traits",
        ),
        "**_Demonic Restoration._** If the marilith dies outside the Abyss, its body dissolves into ichor, and it gains a new body instantly, reviving with all its Hit Points somewhere in the Abyss.",
    ),
    (
        (
            "Monsters A–Z",
            "Marilith",
            "Marilith",
            "Traits",
        ),
        "**_Magic Resistance._** The marilith has Advantage on saving throws against spells and other magical effects.",
    ),
    (
        (
            "Monsters A–Z",
            "Marilith",
            "Marilith",
            "Traits",
        ),
        "**_Reactive._** The marilith can take one Reaction on every turn of combat.",
    ),
    (
        (
            "Monsters A–Z",
            "Marilith",
            "Marilith",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Marilith",
            "Marilith",
            "Actions",
        ),
        "**_Multiattack._** The marilith makes six Pact Blade attacks and uses Constrict.",
    ),
    (
        (
            "Monsters A–Z",
            "Marilith",
            "Marilith",
            "Actions",
        ),
        "**_Pact Blade._** _Melee Attack Roll:_ +10, reach 5 ft. _Hit:_ 10 (1d10 + 5) Slashing damage plus 7 (2d6) Necrotic damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Marilith",
            "Marilith",
            "Actions",
        ),
        "**_Constrict._** _Strength Saving Throw:_ DC 17, one Medium or smaller creature the marilith can see within 5 feet. _Failure:_ 15 (2d10 + 4) Bludgeoning damage. The target has the Grappled condition (escape DC 14), and it has the Restrained condition until the grapple ends.",
    ),
    (
        (
            "Monsters A–Z",
            "Marilith",
            "Marilith",
            "Bonus Actions",
        ),
        "#### Bonus Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Marilith",
            "Marilith",
            "Bonus Actions",
        ),
        "**_Teleport (Recharge 5–6)._** The marilith teleports up to 120 feet to an unoccupied space it can see.",
    ),
    (
        (
            "Monsters A–Z",
            "Marilith",
            "Marilith",
            "Reactions",
        ),
        "#### Reactions",
    ),
    (
        (
            "Monsters A–Z",
            "Marilith",
            "Marilith",
            "Reactions",
        ),
        "**_Parry._** _Trigger:_ The marilith is hit by a melee attack roll while holding a weapon. _Response:_ The marilith adds 5 to its AC against that attack, possibly causing it to miss.",
    ),
    (
        (
            "Monsters A–Z",
            "Medusa",
        ),
        "## Medusa",
    ),
    (
        (
            "Monsters A–Z",
            "Medusa",
            "Medusa",
        ),
        "### Medusa",
    ),
    (
        (
            "Monsters A–Z",
            "Medusa",
            "Medusa",
        ),
        "_Medium Monstrosity, Lawful Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Medusa",
            "Medusa",
        ),
        "**AC** 15 **Initiative** +6 (16) <br>\n**HP** 127 (17d8 + 51) <br>\n**Speed** 30 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Medusa",
            "Medusa",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>DEX</strong></td>\n      <td>17</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>CON</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>WIS</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+4</td>\n      <td><strong>CHA</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Medusa",
            "Medusa",
        ),
        "**Skills** Deception +5, Perception +4, Stealth +6<br>\n**Senses** Darkvision 150 ft.; Passive Perception 14<br>\n**Languages** Common plus one other language<br>\n**CR** 6 (XP 2,300; PB +3)",
    ),
    (
        (
            "Monsters A–Z",
            "Medusa",
            "Medusa",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Medusa",
            "Medusa",
            "Actions",
        ),
        "**_Multiattack._** The medusa makes two Claw attacks and one Snake Hair attack, or it makes three Poison Ray attacks.",
    ),
    (
        (
            "Monsters A–Z",
            "Medusa",
            "Medusa",
            "Actions",
        ),
        "**_Claw._** _Melee Attack Roll:_ +6, reach 5 ft. _Hit:_ 10 (2d6 + 3) Slashing damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Medusa",
            "Medusa",
            "Actions",
        ),
        "**_Snake Hair._** _Melee Attack Roll:_ +6, reach 5 ft. _Hit:_ 5 (1d4 + 3) Piercing damage plus 14 (4d6) Poison damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Medusa",
            "Medusa",
            "Actions",
        ),
        "**_Poison Ray._** _Ranged Attack Roll:_ +5, range 150 ft. _Hit:_ 11 (2d8 + 2) Poison damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Medusa",
            "Medusa",
            "Actions",
        ),
        "**_Petrifying Gaze (Recharge 5–6)._** _Constitution Saving Throw:_ DC 13, each creature in a 30-foot Cone. If the medusa sees its reflection in the Cone, the medusa must make this save. _First Failure:_ The target has the Restrained condition and repeats the save at the end of its next turn if it is still Restrained, ending the effect on itself on a success. _Second Failure:_ The target has the Petrified condition instead of the Restrained condition.",
    ),
    (
        (
            "Monsters A–Z",
            "Mephits",
        ),
        "## Mephits",
    ),
    (
        (
            "Monsters A–Z",
            "Mephits",
            "Dust Mephit",
        ),
        "### Dust Mephit",
    ),
    (
        (
            "Monsters A–Z",
            "Mephits",
            "Dust Mephit",
        ),
        "_Small Elemental, Neutral Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Mephits",
            "Dust Mephit",
        ),
        "**AC** 12 **Initiative** +2 (12) <br>\n**HP** 17 (5d6) <br>\n**Speed** 30 ft., Fly 30 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Mephits",
            "Dust Mephit",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>5</td>\n      <td>−3</td>\n      <td>−3</td>\n      <td><strong>DEX</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CON</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>9</td>\n      <td>−1</td>\n      <td>−1</td>\n      <td><strong>WIS</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CHA</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Mephits",
            "Dust Mephit",
        ),
        "**Skills** Perception +2, Stealth +4<br>\n**Vulnerabilities** Fire<br>\n**Immunities** Poison; Exhaustion, Poisoned<br>\n**Senses** Darkvision 60 ft.; Passive Perception 12<br>\n**Languages** Primordial (Auran, Terran)<br>\n**CR** 1/2 (XP 100; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Mephits",
            "Dust Mephit",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Mephits",
            "Dust Mephit",
            "Traits",
        ),
        "**_Death Burst._** The mephit explodes when it dies. _Dexterity Saving Throw:_ DC 10, each creature in a 5-foot Emanation originating from the mephit. _Failure:_ 5 (2d4) Bludgeoning damage. _Success:_ Half damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Mephits",
            "Dust Mephit",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Mephits",
            "Dust Mephit",
            "Actions",
        ),
        "**_Claw._** _Melee Attack Roll:_ +4, reach 5 ft. _Hit:_ 4 (1d4 + 2) Slashing damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Mephits",
            "Dust Mephit",
            "Actions",
        ),
        "**_Blinding Breath (Recharge 6)._** _Dexterity Saving Throw:_ DC 10, each creature in a 15-foot Cone. _Failure:_ The target has the Blinded condition until the end of the mephit's next turn.",
    ),
    (
        (
            "Monsters A–Z",
            "Mephits",
            "Dust Mephit",
            "Actions",
        ),
        "**_Sleep (1/Day)._** The mephit casts the _Sleep_ spell, requiring no spell components and using Charisma as the spellcasting ability (spell save DC 10).",
    ),
    (
        (
            "Monsters A–Z",
            "Mephits",
            "Ice Mephit",
        ),
        "### Ice Mephit",
    ),
    (
        (
            "Monsters A–Z",
            "Mephits",
            "Ice Mephit",
        ),
        "_Small Elemental, Neutral Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Mephits",
            "Ice Mephit",
        ),
        "**AC** 11 **Initiative** +1 (11) <br>\n**HP** 21 (6d6) <br>\n**Speed** 30 ft., Fly 30 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Mephits",
            "Ice Mephit",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>7</td>\n      <td>−2</td>\n      <td>−2</td>\n      <td><strong>DEX</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CON</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>9</td>\n      <td>−1</td>\n      <td>−1</td>\n      <td><strong>WIS</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CHA</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Mephits",
            "Ice Mephit",
        ),
        "**Skills** Perception +2, Stealth +3<br>\n**Vulnerabilities** Fire<br>\n**Immunities** Cold, Poison; Exhaustion, Poisoned<br>\n**Senses** Darkvision 60 ft.; Passive Perception 12<br>\n**Languages** Primordial (Aquan, Auran)<br>\n**CR** 1/2 (XP 100; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Mephits",
            "Ice Mephit",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Mephits",
            "Ice Mephit",
            "Traits",
        ),
        "**_Death Burst._** The mephit explodes when it dies. _Constitution Saving Throw:_ DC 10, each creature in a 5-foot Emanation originating from the mephit. _Failure:_ 5 (2d4) Cold damage. _Success:_ Half damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Mephits",
            "Ice Mephit",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Mephits",
            "Ice Mephit",
            "Actions",
        ),
        "**_Claw._** _Melee Attack Roll:_ +3, reach 5 ft. _Hit:_ 3 (1d4 + 1) Slashing damage plus 2 (1d4) Cold damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Mephits",
            "Ice Mephit",
            "Actions",
        ),
        "**_Fog Cloud (1/Day)._** The mephit casts _Fog Cloud_, requiring no spell components and using Charisma as the spellcasting ability.",
    ),
    (
        (
            "Monsters A–Z",
            "Mephits",
            "Ice Mephit",
            "Actions",
        ),
        "**_Frost Breath (Recharge 6)._** _Constitution Saving Throw:_ DC 10, each creature in a 15-foot Cone. _Failure:_ 7 (3d4) Cold damage. _Success:_ Half damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Mephits",
            "Magma Mephit",
        ),
        "### Magma Mephit",
    ),
    (
        (
            "Monsters A–Z",
            "Mephits",
            "Magma Mephit",
        ),
        "_Small Elemental, Neutral Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Mephits",
            "Magma Mephit",
        ),
        "**AC** 11 **Initiative** +1 (11) <br>\n**HP** 18 (4d6 + 4) <br>\n**Speed** 30 ft., Fly 30 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Mephits",
            "Magma Mephit",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>8</td>\n      <td>−1</td>\n      <td>−1</td>\n      <td><strong>DEX</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CON</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>7</td>\n      <td>−2</td>\n      <td>−2</td>\n      <td><strong>WIS</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CHA</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Mephits",
            "Magma Mephit",
        ),
        "**Skills** Stealth +3<br>\n**Vulnerabilities** Cold<br>\n**Immunities** Fire, Poison; Exhaustion, Poisoned<br>\n**Senses** Darkvision 60 ft.; Passive Perception 10<br>\n**Languages** Primordial (Ignan, Terran)<br>\n**CR** 1/2 (XP 100; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Mephits",
            "Magma Mephit",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Mephits",
            "Magma Mephit",
            "Traits",
        ),
        "**_Death Burst._** The mephit explodes when it dies. _Dexterity Saving Throw:_ DC 11, each creature in a 5-foot Emanation originating from the mephit. _Failure:_ 7 (2d6) Fire damage. _Success:_ Half damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Mephits",
            "Magma Mephit",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Mephits",
            "Magma Mephit",
            "Actions",
        ),
        "**_Claw._** _Melee Attack Roll:_ +3, reach 5 ft. _Hit:_ 3 (1d4 + 1) Slashing damage plus 3 (1d6) Fire damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Mephits",
            "Magma Mephit",
            "Actions",
        ),
        "**_Fire Breath (Recharge 6)._** _Dexterity Saving Throw:_ DC 11, each creature in a 15-foot Cone. _Failure:_ 7 (2d6) Fire damage. _Success:_ Half damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Mephits",
            "Steam Mephit",
        ),
        "### Steam Mephit",
    ),
    (
        (
            "Monsters A–Z",
            "Mephits",
            "Steam Mephit",
        ),
        "_Small Elemental, Neutral Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Mephits",
            "Steam Mephit",
        ),
        "**AC** 10 **Initiative** +0 (10) <br>\n**HP** 17 (5d6) <br>  \n**Speed** 30 ft., Fly 30 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Mephits",
            "Steam Mephit",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>5</td>\n      <td>−3</td>\n      <td>−3</td>\n      <td><strong>DEX</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CON</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>WIS</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CHA</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Mephits",
            "Steam Mephit",
        ),
        "**Skills** Stealth +2 <br>\n**Immunities** Fire, Poison; Exhaustion, Poisoned <br>\n**Senses** Darkvision 60 ft.; Passive Perception 10 <br>\n**Languages** Primordial (Aquan, Ignan) <br>\n**CR** 1/4 (XP 50; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Mephits",
            "Steam Mephit",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Mephits",
            "Steam Mephit",
            "Traits",
        ),
        "**_Blurred Form._** Attack rolls against the mephit are made with Disadvantage unless the mephit has the Incapacitated condition.",
    ),
    (
        (
            "Monsters A–Z",
            "Mephits",
            "Steam Mephit",
            "Traits",
        ),
        "**_Death Burst._** The mephit explodes when it dies. _Dexterity Saving Throw:_ DC 10, each creature in a 5-foot Emanation originating from the mephit. _Failure:_ 5 (2d4) Fire damage. _Success:_ Half damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Mephits",
            "Steam Mephit",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Mephits",
            "Steam Mephit",
            "Actions",
        ),
        "**_Claw._** _Melee Attack Roll:_ +2, reach 5 ft. _Hit:_ 2 (1d4) Slashing damage plus 2 (1d4) Fire damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Mephits",
            "Steam Mephit",
            "Actions",
        ),
        "**_Steam Breath (Recharge 6)._** _Constitution Saving Throw:_ DC 10, each creature in a 15-foot Cone. _Failure:_ 5 (2d4) Fire damage, and the target's Speed decreases by 10 feet until the end of the mephit's next turn. _Success:_ Half damage only. _Failure or Success:_ Being underwater doesn't grant Resistance to this Fire damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Merfolk",
        ),
        "## Merfolk",
    ),
    (
        (
            "Monsters A–Z",
            "Merfolk",
            "Merfolk Skirmisher",
        ),
        "### Merfolk Skirmisher",
    ),
    (
        (
            "Monsters A–Z",
            "Merfolk",
            "Merfolk Skirmisher",
        ),
        "_Medium Elemental, Neutral_",
    ),
    (
        (
            "Monsters A–Z",
            "Merfolk",
            "Merfolk Skirmisher",
        ),
        "**AC** 11 **Initiative** +1 (11) <br>\n**HP** 11 (2d8 + 2) <br>  \n**Speed** 10 ft., Swim 40 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Merfolk",
            "Merfolk Skirmisher",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>DEX</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CON</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>WIS</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CHA</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Merfolk",
            "Merfolk Skirmisher",
        ),
        "**Senses** Passive Perception 12 <br>\n**Languages** Common, Primordial (Aquan) <br>\n**CR** 1/8 (XP 25; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Merfolk",
            "Merfolk Skirmisher",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Merfolk",
            "Merfolk Skirmisher",
            "Traits",
        ),
        "**_Amphibious._** The merfolk can breathe air and water.",
    ),
    (
        (
            "Monsters A–Z",
            "Merfolk",
            "Merfolk Skirmisher",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Merfolk",
            "Merfolk Skirmisher",
            "Actions",
        ),
        "**_Ocean Spear._** _Melee or Ranged Attack Roll:_ +2, reach 5 ft. or range 20/60 ft. _Hit:_ 3 (1d6) Piercing damage plus 2 (1d4) Cold damage. If the target is a creature, its Speed decreases by 10 feet until the end of its next turn. _Hit or Miss:_ The spear magically returns to the merfolk's hand immediately after a ranged attack.",
    ),
    (
        (
            "Monsters A–Z",
            "Merrow",
        ),
        "## Merrow",
    ),
    (
        (
            "Monsters A–Z",
            "Merrow",
            "Merrow",
        ),
        "### Merrow",
    ),
    (
        (
            "Monsters A–Z",
            "Merrow",
            "Merrow",
        ),
        "_Large Monstrosity, Chaotic Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Merrow",
            "Merrow",
        ),
        "**AC** 13 **Initiative** +2 (12) <br>\n**HP** 45 (6d10 + 12) <br>  \n**Speed** 10 ft., Swim 40 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Merrow",
            "Merrow",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+4</td>\n      <td><strong>DEX</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CON</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>8</td>\n      <td>−1</td>\n      <td>−1</td>\n      <td><strong>WIS</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CHA</strong></td>\n      <td>9</td>\n      <td>−1</td>\n      <td>−1</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Merrow",
            "Merrow",
        ),
        "**Senses** Darkvision 60 ft.; Passive Perception 10 <br>\n**Languages** Abyssal, Primordial (Aquan) <br>\n**CR** 2 (XP 450; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Merrow",
            "Merrow",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Merrow",
            "Merrow",
            "Traits",
        ),
        "**_Amphibious._** The merrow can breathe air and water.",
    ),
    (
        (
            "Monsters A–Z",
            "Merrow",
            "Merrow",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Merrow",
            "Merrow",
            "Actions",
        ),
        "**_Multiattack._** The merrow makes two attacks, using Bite, Claw, or Harpoon in any combination.",
    ),
    (
        (
            "Monsters A–Z",
            "Merrow",
            "Merrow",
            "Actions",
        ),
        "**_Bite._** _Melee Attack Roll:_ +6, reach 5 ft. _Hit:_ 6 (1d4 + 4) Piercing damage, and the target has the Poisoned condition until the end of the merrow's next turn.",
    ),
    (
        (
            "Monsters A–Z",
            "Merrow",
            "Merrow",
            "Actions",
        ),
        "**_Claw._** _Melee Attack Roll:_ +6, reach 5 ft. _Hit:_ 9 (2d4 + 4) Slashing damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Merrow",
            "Merrow",
            "Actions",
        ),
        "**_Harpoon._** _Melee or Ranged Attack Roll:_ +6, reach 5 ft. or range 20/60 ft. _Hit:_ 11 (2d6 + 4) Piercing damage. If the target is a Large or smaller creature, the merrow pulls the target up to 15 feet straight toward itself.",
    ),
    (
        (
            "Monsters A–Z",
            "Mimic",
        ),
        "## Mimic",
    ),
    (
        (
            "Monsters A–Z",
            "Mimic",
            "Mimic",
        ),
        "### Mimic",
    ),
    (
        (
            "Monsters A–Z",
            "Mimic",
            "Mimic",
        ),
        "_Medium Monstrosity, Neutral_",
    ),
    (
        (
            "Monsters A–Z",
            "Mimic",
            "Mimic",
        ),
        "**AC** 12 **Initiative** +3 (13) <br>\n**HP** 58 (9d8 + 18) <br>  \n**Speed** 20 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Mimic",
            "Mimic",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>17</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>DEX</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CON</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>5</td>\n      <td>−3</td>\n      <td>−3</td>\n      <td><strong>WIS</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CHA</strong></td>\n      <td>8</td>\n      <td>−1</td>\n      <td>−1</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Mimic",
            "Mimic",
        ),
        "**Skills** Stealth +5 <br>\n**Immunities** Acid; Prone <br>\n**Senses** Darkvision 60 ft.; Passive Perception 11 <br>\n**Languages** None <br>\n**CR** 2 (XP 450; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Mimic",
            "Mimic",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Mimic",
            "Mimic",
            "Traits",
        ),
        "**_Adhesive (Object Form Only)._** The mimic adheres to anything that touches it. A Huge or smaller creature adhered to the mimic has the Grappled condition (escape DC 13). Ability checks made to escape this grapple have Disadvantage.",
    ),
    (
        (
            "Monsters A–Z",
            "Mimic",
            "Mimic",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Mimic",
            "Mimic",
            "Actions",
        ),
        "**_Bite._** _Melee Attack Roll:_ +5 (with Advantage if the target is Grappled by the mimic), reach 5 ft. _Hit:_ 7 (1d8 + 3) Piercing damage—or 12 (2d8 + 3) Piercing damage if the target is Grappled by the mimic—plus 4 (1d8) Acid damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Mimic",
            "Mimic",
            "Actions",
        ),
        "**_Pseudopod._** _Melee Attack Roll:_ +5, reach 5 ft. _Hit:_ 7 (1d8 + 3) Bludgeoning damage plus 4 (1d8) Acid damage. If the target is a Large or smaller creature, it has the Grappled condition (escape DC 13). Ability checks made to escape this grapple have Disadvantage.",
    ),
    (
        (
            "Monsters A–Z",
            "Mimic",
            "Mimic",
            "Bonus Actions",
        ),
        "#### Bonus Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Mimic",
            "Mimic",
            "Bonus Actions",
        ),
        "**_Shape-Shift._** The mimic shape-shifts to resemble a Medium or Small object while retaining its game statistics, or it returns to its true blob form. Any equipment it is wearing or carrying isn't transformed.",
    ),
    (
        (
            "Monsters A–Z",
            "Minotaur of Baphomet",
        ),
        "## Minotaur of Baphomet",
    ),
    (
        (
            "Monsters A–Z",
            "Minotaur of Baphomet",
            "Minotaur of Baphomet",
        ),
        "### Minotaur of Baphomet",
    ),
    (
        (
            "Monsters A–Z",
            "Minotaur of Baphomet",
            "Minotaur of Baphomet",
        ),
        "_Large Monstrosity, Chaotic Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Minotaur of Baphomet",
            "Minotaur of Baphomet",
        ),
        "**AC** 14 **Initiative** +0 (10) <br>\n**HP** 85 (10d10 + 30) <br>\n**Speed** 40 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Minotaur of Baphomet",
            "Minotaur of Baphomet",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+4</td>\n      <td><strong>DEX</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CON</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>6</td>\n      <td>−2</td>\n      <td>−2</td>\n      <td><strong>WIS</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>CHA</strong></td>\n      <td>9</td>\n      <td>−1</td>\n      <td>−1</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Minotaur of Baphomet",
            "Minotaur of Baphomet",
        ),
        "**Skills** Perception +7, Survival +7<br>\n**Senses** Darkvision 60 ft.; Passive Perception 17<br>\n**Languages** Abyssal<br>\n**CR** 3 (XP 700; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Minotaur of Baphomet",
            "Minotaur of Baphomet",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Minotaur of Baphomet",
            "Minotaur of Baphomet",
            "Actions",
        ),
        "**_Abyssal Glaive._** _Melee Attack Roll:_ +6, reach 10 ft. _Hit:_ 10 (1d12 + 4) Slashing damage plus 10 (3d6) Necrotic damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Minotaur of Baphomet",
            "Minotaur of Baphomet",
            "Actions",
        ),
        "**_Gore (Recharge 5–6)._** _Melee Attack Roll:_ +6, reach 5 ft. _Hit:_ 18 (4d6 + 4) Piercing damage. If the target is a Large or smaller creature and the minotaur moved 10+ feet straight toward it immediately before the hit, the target takes an extra 10 (3d6) Piercing damage and has the Prone condition.",
    ),
    (
        (
            "Monsters A–Z",
            "Mummies",
        ),
        "## Mummies",
    ),
    (
        (
            "Monsters A–Z",
            "Mummies",
            "Mummy",
        ),
        "### Mummy",
    ),
    (
        (
            "Monsters A–Z",
            "Mummies",
            "Mummy",
        ),
        "_Medium or Small Undead, Lawful Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Mummies",
            "Mummy",
        ),
        "**AC** 11 **Initiative** −1 (9) <br>\n**HP** 58 (9d8 + 18) <br>\n**Speed** 20 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Mummies",
            "Mummy",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>DEX</strong></td>\n      <td>8</td>\n      <td>−1</td>\n      <td>−1</td>\n      <td><strong>CON</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>6</td>\n      <td>−2</td>\n      <td>−2</td>\n      <td><strong>WIS</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+3</td>\n      <td><strong>CHA</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Mummies",
            "Mummy",
        ),
        "**Vulnerabilities** Fire<br>\n**Immunities** Necrotic, Poison; Charmed, Exhaustion, Frightened, Paralyzed, Poisoned<br>\n**Senses** Darkvision 60 ft.; Passive Perception 11<br>\n**Languages** Common plus two other languages<br>\n**CR** 3 (XP 700; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Mummies",
            "Mummy",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Mummies",
            "Mummy",
            "Actions",
        ),
        "**_Multiattack._** The mummy makes two Rotting Fist attacks and uses Dreadful Glare.",
    ),
    (
        (
            "Monsters A–Z",
            "Mummies",
            "Mummy",
            "Actions",
        ),
        "**_Rotting Fist._** _Melee Attack Roll:_ +5, reach 5 ft. _Hit:_ 8 (1d10 + 3) Bludgeoning damage plus 10 (3d6) Necrotic damage. If the target is a creature, it is cursed. While cursed, the target can't regain Hit Points, its Hit Point maximum doesn't return to normal when finishing a Long Rest, and its Hit Point maximum decreases by 10 (3d6) every 24 hours that elapse. A creature dies and turns to dust if reduced to 0 Hit Points by this attack.",
    ),
    (
        (
            "Monsters A–Z",
            "Mummies",
            "Mummy",
            "Actions",
        ),
        "**_Dreadful Glare._** _Wisdom Saving Throw:_ DC 11, one creature the mummy can see within 60 feet. _Failure:_ The target has the Frightened condition until the end of the mummy's next turn. _Success:_ The target is immune to this mummy's Dreadful Glare for 24 hours.",
    ),
    (
        (
            "Monsters A–Z",
            "Mummies",
            "Mummy Lord",
        ),
        "### Mummy Lord",
    ),
    (
        (
            "Monsters A–Z",
            "Mummies",
            "Mummy Lord",
        ),
        "_Medium or Small Undead (Cleric), Lawful Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Mummies",
            "Mummy Lord",
        ),
        "**AC** 17 **Initiative** +10 (20) <br>\n**HP** 187 (25d8 + 75) <br>\n**Speed** 30 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Mummies",
            "Mummy Lord",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+4</td>\n      <td><strong>DEX</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CON</strong></td>\n      <td>17</td>\n      <td>+3</td>\n      <td>+3</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+5</td>\n      <td><strong>WIS</strong></td>\n      <td>19</td>\n      <td>+4</td>\n      <td>+9</td>\n      <td><strong>CHA</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Mummies",
            "Mummy Lord",
        ),
        "**Skills** History +5, Perception +9, Religion +5<br>\n**Vulnerabilities** Fire<br>\n**Immunities** Necrotic, Poison; Charmed, Exhaustion, Frightened, Paralyzed, Poisoned<br>\n**Senses** Truesight 60 ft.; Passive Perception 19<br>\n**Languages** Common plus three other languages<br>\n**CR** 15 (XP 13,000, or 15,000 in lair; PB +5)",
    ),
    (
        (
            "Monsters A–Z",
            "Mummies",
            "Mummy Lord",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Mummies",
            "Mummy Lord",
            "Traits",
        ),
        "**_Legendary Resistance (3/Day, or 4/Day in Lair)._** If the mummy fails a saving throw, it can choose to succeed instead.",
    ),
    (
        (
            "Monsters A–Z",
            "Mummies",
            "Mummy Lord",
            "Traits",
        ),
        "**_Magic Resistance._** The mummy has Advantage on saving throws against spells and other magical effects.",
    ),
    (
        (
            "Monsters A–Z",
            "Mummies",
            "Mummy Lord",
            "Traits",
        ),
        "**_Undead Restoration._** If destroyed, the mummy gains a new body in 24 hours if its heart is intact, reviving with all its Hit Points. The new body appears in an unoccupied space within the mummy's lair. The heart is a Tiny object that has AC 17, HP 10, and Immunity to all damage except Fire.",
    ),
    (
        (
            "Monsters A–Z",
            "Mummies",
            "Mummy Lord",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Mummies",
            "Mummy Lord",
            "Actions",
        ),
        "**_Multiattack._** The mummy makes one Rotting Fist or Channel Negative Energy attack, and it uses Dreadful Glare.",
    ),
    (
        (
            "Monsters A–Z",
            "Mummies",
            "Mummy Lord",
            "Actions",
        ),
        "**_Rotting Fist._** _Melee Attack Roll:_ +9, reach 5 ft. _Hit:_ 15 (2d10 + 4) Bludgeoning damage plus 10 (3d6) Necrotic damage. If the target is a creature, it is cursed. While cursed, the target can't regain Hit Points, it gains no benefit from finishing a Long Rest, and its Hit Point maximum decreases by 10 (3d6) every 24 hours that elapse. A creature dies and turns to dust if reduced to 0 Hit Points by this attack.",
    ),
    (
        (
            "Monsters A–Z",
            "Mummies",
            "Mummy Lord",
            "Actions",
        ),
        "**_Channel Negative Energy._** _Ranged Attack Roll:_ +9, range 60 ft. _Hit:_ 25 (6d6 + 4) Necrotic damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Mummies",
            "Mummy Lord",
            "Actions",
        ),
        "**_Dreadful Glare._** _Wisdom Saving Throw:_ DC 17, one creature the mummy can see within 60 feet. _Failure:_ 25 (6d6 + 4) Psychic damage, and the target has the Paralyzed condition until the end of the mummy's next turn.",
    ),
    (
        (
            "Monsters A–Z",
            "Mummies",
            "Mummy Lord",
            "Actions",
        ),
        "**_Spellcasting._** The mummy casts one of the following spells, requiring no Material components and using Wisdom as the spellcasting ability (spell save DC 17, +9 to hit with spell attacks): <br>\n&emsp;**At Will:** _Dispel Magic_, _Thaumaturgy_ <br>\n&emsp;**1/Day Each:** _Animate Dead_, _Harm_, _Insect Plague_ (level 7 version)",
    ),
    (
        (
            "Monsters A–Z",
            "Mummies",
            "Mummy Lord",
            "Reactions",
        ),
        "#### Reactions",
    ),
    (
        (
            "Monsters A–Z",
            "Mummies",
            "Mummy Lord",
            "Reactions",
        ),
        "**_Whirlwind of Sand._** _Trigger:_ The mummy is hit by an attack roll. _Response:_ The mummy adds 2 to its AC against the attack, possibly causing the attack to miss, and the mummy teleports up to 60 feet to an unoccupied space it can see. Each creature of its choice that it can see within 5 feet of its destination space has the Blinded condition until the end of the mummy's next turn.",
    ),
    (
        (
            "Monsters A–Z",
            "Mummies",
            "Mummy Lord",
            "Legendary Actions",
        ),
        "#### Legendary Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Mummies",
            "Mummy Lord",
            "Legendary Actions",
        ),
        "_Legendary Action Uses: 3 (4 in Lair). Immediately after another creature's turn, the mummy can expend a use to take one of the following actions. The mummy regains all expended uses at the start of each of its turns._",
    ),
    (
        (
            "Monsters A–Z",
            "Mummies",
            "Mummy Lord",
            "Legendary Actions",
        ),
        "**_Dread Command._** The mummy casts _Command_ (level 2 version), using the same spellcasting ability as Spellcasting. The mummy can't take this action again until the start of its next turn.",
    ),
    (
        (
            "Monsters A–Z",
            "Mummies",
            "Mummy Lord",
            "Legendary Actions",
        ),
        "**_Glare._** The mummy uses Dreadful Glare. The mummy can't take this action again until the start of its next turn.",
    ),
    (
        (
            "Monsters A–Z",
            "Mummies",
            "Mummy Lord",
            "Legendary Actions",
        ),
        "**_Necrotic Strike._** The mummy makes one Rotting Fist or Channel Negative Energy attack.",
    ),
    (
        (
            "Monsters A–Z",
            "Nalfeshnee",
        ),
        "## Nalfeshnee",
    ),
    (
        (
            "Monsters A–Z",
            "Nalfeshnee",
            "Nalfeshnee",
        ),
        "### Nalfeshnee",
    ),
    (
        (
            "Monsters A–Z",
            "Nalfeshnee",
            "Nalfeshnee",
        ),
        "_Large Fiend (Demon), Chaotic Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Nalfeshnee",
            "Nalfeshnee",
        ),
        "**AC** 18 **Initiative** +5 (15) <br>\n**HP** 184 (16d10 + 96) <br>\n**Speed** 20 ft., Fly 30 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Nalfeshnee",
            "Nalfeshnee",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>21</td>\n      <td>+5</td>\n      <td>+5</td>\n      <td><strong>DEX</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CON</strong></td>\n      <td>22</td>\n      <td>+6</td>\n      <td>+11</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>19</td>\n      <td>+4</td>\n      <td>+9</td>\n      <td><strong>WIS</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+6</td>\n      <td><strong>CHA</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+7</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Nalfeshnee",
            "Nalfeshnee",
        ),
        "**Resistances** Cold, Fire, Lightning<br>\n**Immunities** Poison; Frightened, Poisoned<br>\n**Senses** Truesight 120 ft.; Passive Perception 11<br>\n**Languages** Abyssal; telepathy 120 ft.<br>\n**CR** 13 (XP 10,000; PB +5)",
    ),
    (
        (
            "Monsters A–Z",
            "Nalfeshnee",
            "Nalfeshnee",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Nalfeshnee",
            "Nalfeshnee",
            "Traits",
        ),
        "**_Demonic Restoration._** If the nalfeshnee dies outside the Abyss, its body dissolves into ichor, and it gains a new body instantly, reviving with all its Hit Points somewhere in the Abyss.",
    ),
    (
        (
            "Monsters A–Z",
            "Nalfeshnee",
            "Nalfeshnee",
            "Traits",
        ),
        "**_Magic Resistance._** The nalfeshnee has Advantage on saving throws against spells and other magical effects.",
    ),
    (
        (
            "Monsters A–Z",
            "Nalfeshnee",
            "Nalfeshnee",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Nalfeshnee",
            "Nalfeshnee",
            "Actions",
        ),
        "**_Multiattack._** The nalfeshnee makes three Rend attacks.",
    ),
    (
        (
            "Monsters A–Z",
            "Nalfeshnee",
            "Nalfeshnee",
            "Actions",
        ),
        "**_Rend._** _Melee Attack Roll:_ +10, reach 10 ft. _Hit:_ 16 (2d10 + 5) Slashing damage plus 11 (2d10) Force damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Nalfeshnee",
            "Nalfeshnee",
            "Actions",
        ),
        "**_Teleport._** The nalfeshnee teleports up to 120 feet to an unoccupied space it can see.",
    ),
    (
        (
            "Monsters A–Z",
            "Nalfeshnee",
            "Nalfeshnee",
            "Bonus Actions",
        ),
        "#### Bonus Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Nalfeshnee",
            "Nalfeshnee",
            "Bonus Actions",
        ),
        "**_Horror Nimbus (Recharge 5–6)._** _Wisdom Saving Throw:_ DC 15, each creature in a 15-foot Emanation originating from the nalfeshnee. _Failure:_ 28 (8d6) Psychic damage, and the target has the Frightened condition for 1 minute, until it takes damage, or until it ends its turn with the nalfeshnee out of line of sight. _Success:_\nThe target is immune to this nalfeshnee's Horror Nimbus for 24 hours.",
    ),
    (
        (
            "Monsters A–Z",
            "Nalfeshnee",
            "Nalfeshnee",
            "Reactions",
        ),
        "#### Reactions",
    ),
    (
        (
            "Monsters A–Z",
            "Nalfeshnee",
            "Nalfeshnee",
            "Reactions",
        ),
        "**_Pursuit._** Trigger: Another creature the nalfeshnee can see ends its move within 120 feet of the nalfeshnee. Response: The nalfeshnee uses Teleport, but its destination space must be within 10 feet of the triggering creature.",
    ),
    (
        (
            "Monsters A–Z",
            "Night Hag",
        ),
        "## Night Hag",
    ),
    (
        (
            "Monsters A–Z",
            "Night Hag",
            "Night Hag",
        ),
        "### Night Hag",
    ),
    (
        (
            "Monsters A–Z",
            "Night Hag",
            "Night Hag",
        ),
        "_Medium Fiend, Neutral Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Night Hag",
            "Night Hag",
        ),
        "**AC** 17 **Initiative** +5 (15) <br>\n**HP** 112 (15d8 + 45) <br>\n**Speed** 30 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Night Hag",
            "Night Hag",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+4</td>\n      <td><strong>DEX</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CON</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>WIS</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CHA</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Night Hag",
            "Night Hag",
        ),
        "**Skills** Deception +6, Insight +5, Perception +5, Stealth +5<br>\n**Resistances** Cold, Fire<br>\n**Immunities** Charmed<br>\n**Senses** Darkvision 120 ft.; Passive Perception 15<br>\n**Languages** Abyssal, Common, Infernal, Primordial<br>\n**CR** 5 (XP 1,800; PB +3)",
    ),
    (
        (
            "Monsters A–Z",
            "Night Hag",
            "Night Hag",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Night Hag",
            "Night Hag",
            "Traits",
        ),
        "**_Coven Magic._** While within 30 feet of at least two hag allies, the hag can cast one of the following spells, requiring no Material components, using the spell's normal casting time, and using Intelligence as the spellcasting ability (spell save DC 14): _Augury_, _Find Familiar_, _Identify_, _Locate Object_, _Scrying_, or _Unseen Servant_. The hag must finish a Long Rest before using this trait to cast that spell again.",
    ),
    (
        (
            "Monsters A–Z",
            "Night Hag",
            "Night Hag",
            "Traits",
        ),
        "**_Magic Resistance._** The hag has Advantage on saving throws against spells and other magical effects.",
    ),
    (
        (
            "Monsters A–Z",
            "Night Hag",
            "Night Hag",
            "Traits",
        ),
        "**_Soul Bag._** The hag has a soul bag. While holding or carrying the bag, the hag can use its Nightmare Haunting action. <br>\n&emsp;The bag has AC 15, HP 20, and Resistance to all damage. The bag turns to dust if reduced to 0 Hit Points. If the bag is destroyed, any souls the bag is holding are released. The hag can create a new bag after 7 days.",
    ),
    (
        (
            "Monsters A–Z",
            "Night Hag",
            "Night Hag",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Night Hag",
            "Night Hag",
            "Actions",
        ),
        "**_Multiattack._** The hag makes two Claw attacks.",
    ),
    (
        (
            "Monsters A–Z",
            "Night Hag",
            "Night Hag",
            "Actions",
        ),
        "**_Claw._** _Melee Attack Roll:_ +7, reach 5 ft. _Hit:_ 13 (2d8 + 4) Slashing damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Night Hag",
            "Night Hag",
            "Actions",
        ),
        "**_Nightmare Haunting (1/Day; Requires Soul Bag)._** While on the Ethereal Plane, the hag casts _Dream_, using the same spellcasting ability as Spellcasting. Only the hag can serve as the spell's messenger, and the target must be a creature the hag can see on the Material Plane. The spell fails and is wasted if the target is under the effect of the _Protection from Evil and Good_ spell or within a _Magic Circle_ spell. <br>\n&emsp;If the target takes damage from the _Dream_ spell, the target's Hit Point maximum decreases by an amount equal to that damage. If the spell kills the target, its soul is trapped in the hag's soul bag, and the target can't be raised from the dead until its soul is released.",
    ),
    (
        (
            "Monsters A–Z",
            "Night Hag",
            "Night Hag",
            "Actions",
        ),
        "**_Spellcasting._** The hag casts one of the following spells, requiring no Material components and using Intelligence as the spellcasting ability (spell save DC 14): <br>\n&emsp;**At Will:** _Detect Magic_, _Etherealness_, _Magic Missile_ (level 4 version) <br>\n&emsp;**2/Day Each:** _Phantasmal Killer_, _Plane Shift_ (self only)",
    ),
    (
        (
            "Monsters A–Z",
            "Night Hag",
            "Night Hag",
            "Bonus Actions",
        ),
        "#### Bonus Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Night Hag",
            "Night Hag",
            "Bonus Actions",
        ),
        "**_Shape-Shift._** The hag shape-shifts into a Small or Medium Humanoid, or it returns to its true form. Other than its size, its game statistics are the same in each form. Any equipment it is wearing or carrying isn't transformed.",
    ),
    (
        (
            "Monsters A–Z",
            "Nightmare",
        ),
        "## Nightmare",
    ),
    (
        (
            "Monsters A–Z",
            "Nightmare",
            "Nightmare",
        ),
        "### Nightmare",
    ),
    (
        (
            "Monsters A–Z",
            "Nightmare",
            "Nightmare",
        ),
        "_Large Fiend, Neutral Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Nightmare",
            "Nightmare",
        ),
        "**AC** 13 **Initiative** +2 (12) <br>\n**HP** 68 (8d10 + 24) <br>\n**Speed** 60 ft., Fly 90 ft. (hover) <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Nightmare",
            "Nightmare",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+4</td>\n      <td><strong>DEX</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CON</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>WIS</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CHA</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Nightmare",
            "Nightmare",
        ),
        "**Immunities** Fire<br>\n**Senses** Passive Perception 11<br>\n**Languages** Understands Abyssal, Common, and Infernal but can't speak<br>\n**CR** 3 (XP 700; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Nightmare",
            "Nightmare",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Nightmare",
            "Nightmare",
            "Traits",
        ),
        "**_Confer Fire Resistance._** The nightmare can grant Resistance to Fire damage to a rider while it is on the nightmare.",
    ),
    (
        (
            "Monsters A–Z",
            "Nightmare",
            "Nightmare",
            "Traits",
        ),
        "**_Illumination._** The nightmare sheds Bright Light in a 10-foot radius and Dim Light for an additional 10 feet.",
    ),
    (
        (
            "Monsters A–Z",
            "Nightmare",
            "Nightmare",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Nightmare",
            "Nightmare",
            "Actions",
        ),
        "**_Hooves._** _Melee Attack Roll:_ +6, reach 5 ft. _Hit:_ 13 (2d8 + 4) Bludgeoning damage plus 10 (3d6) Fire damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Nightmare",
            "Nightmare",
            "Actions",
        ),
        "**_Ethereal Stride._** The nightmare and up to three willing creatures within 5 feet of it teleport to the Ethereal Plane from the Material Plane or vice versa.",
    ),
    (
        (
            "Monsters A–Z",
            "Noble",
        ),
        "## Noble",
    ),
    (
        (
            "Monsters A–Z",
            "Noble",
            "Noble",
        ),
        "### Noble",
    ),
    (
        (
            "Monsters A–Z",
            "Noble",
            "Noble",
        ),
        "_Medium or Small Humanoid, Neutral_",
    ),
    (
        (
            "Monsters A–Z",
            "Noble",
            "Noble",
        ),
        "**AC** 15 **Initiative** +1 (11) <br>\n**HP** 9 (2d8) <br>\n**Speed** 30 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Noble",
            "Noble",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>DEX</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CON</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>WIS</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CHA</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Noble",
            "Noble",
        ),
        "**Skills** Deception +5, Insight +4, Persuasion +5<br>\n**Gear** Breastplate, Rapier<br>\n**Senses** Passive Perception 12<br>\n**Languages** Common plus two other languages<br>\n**CR** 1/8 (XP 25; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Noble",
            "Noble",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Noble",
            "Noble",
            "Actions",
        ),
        "**_Rapier._** _Melee Attack Roll:_ +3, reach 5 ft. _Hit:_ 5 (1d8 + 1) Piercing damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Noble",
            "Noble",
            "Reactions",
        ),
        "#### Reactions",
    ),
    (
        (
            "Monsters A–Z",
            "Noble",
            "Noble",
            "Reactions",
        ),
        "**_Parry._** _Trigger:_ The noble is hit by a melee attack roll while holding a weapon. _Response:_ The noble adds 2 to its AC against that attack, possibly causing it to miss.",
    ),
    (
        (
            "Monsters A–Z",
            "Ochre Jelly",
        ),
        "## Ochre Jelly",
    ),
    (
        (
            "Monsters A–Z",
            "Ochre Jelly",
            "Ochre Jelly",
        ),
        "### Ochre Jelly",
    ),
    (
        (
            "Monsters A–Z",
            "Ochre Jelly",
            "Ochre Jelly",
        ),
        "_Large Ooze, Unaligned_",
    ),
    (
        (
            "Monsters A–Z",
            "Ochre Jelly",
            "Ochre Jelly",
        ),
        "**AC** 8 **Initiative** −2 (8) <br>\n**HP** 52 (7d10 + 14) <br>\n**Speed** 20 ft., Climb 20 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Ochre Jelly",
            "Ochre Jelly",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>DEX</strong></td>\n      <td>6</td>\n      <td>−2</td>\n      <td>−2</td>\n      <td><strong>CON</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>2</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>WIS</strong></td>\n      <td>6</td>\n      <td>−2</td>\n      <td>−2</td>\n      <td><strong>CHA</strong></td>\n      <td>1</td>\n      <td>−5</td>\n      <td>−5</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Ochre Jelly",
            "Ochre Jelly",
        ),
        "**Resistances** Acid<br>\n**Immunities** Lightning, Slashing; Charmed, Deafened, Exhaustion, Frightened, Grappled, Prone, Restrained<br>\n**Senses** Blindsight 60 ft.; Passive Perception 8<br>\n**Languages** None<br>\n**CR** 2 (XP 450; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Ochre Jelly",
            "Ochre Jelly",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Ochre Jelly",
            "Ochre Jelly",
            "Traits",
        ),
        "**_Amorphous._** The jelly can move through a space as narrow as 1 inch without expending extra movement to do so.",
    ),
    (
        (
            "Monsters A–Z",
            "Ochre Jelly",
            "Ochre Jelly",
            "Traits",
        ),
        "**_Spider Climb._** The jelly can climb difficult surfaces, including along ceilings, without needing to make an ability check.",
    ),
    (
        (
            "Monsters A–Z",
            "Ochre Jelly",
            "Ochre Jelly",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Ochre Jelly",
            "Ochre Jelly",
            "Actions",
        ),
        "**_Pseudopod._** _Melee Attack Roll:_ +4, reach 5 ft. _Hit:_ 12 (3d6 + 2) Acid damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Ochre Jelly",
            "Ochre Jelly",
            "Reactions",
        ),
        "#### Reactions",
    ),
    (
        (
            "Monsters A–Z",
            "Ochre Jelly",
            "Ochre Jelly",
            "Reactions",
        ),
        "**_Split._** _Trigger:_ While the jelly is Large or Medium and has 10+ Hit Points, it becomes Bloodied or is subjected to Lightning or Slashing damage. _Response:_ The jelly splits into two new **Ochre Jellies**. Each new jelly is one size smaller than the original jelly and acts on its Initiative. The original jelly's Hit Points are divided evenly between the new jellies (round down).",
    ),
    (
        (
            "Monsters A–Z",
            "Ogre",
        ),
        "## Ogre",
    ),
    (
        (
            "Monsters A–Z",
            "Ogre",
            "Ogre",
        ),
        "### Ogre",
    ),
    (
        (
            "Monsters A–Z",
            "Ogre",
            "Ogre",
        ),
        "_Large Giant, Chaotic Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Ogre",
            "Ogre",
        ),
        "**AC** 11 **Initiative** −1 (9) <br>\n**HP** 68 (8d10 + 24) <br>\n**Speed** 40 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Ogre",
            "Ogre",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>19</td>\n      <td>+4</td>\n      <td>+4</td>\n      <td><strong>DEX</strong></td>\n      <td>8</td>\n      <td>−1</td>\n      <td>−1</td>\n      <td><strong>CON</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>5</td>\n      <td>−3</td>\n      <td>−3</td>\n      <td><strong>WIS</strong></td>\n      <td>7</td>\n      <td>−2</td>\n      <td>−2</td>\n      <td><strong>CHA</strong></td>\n      <td>7</td>\n      <td>−2</td>\n      <td>−2</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Ogre",
            "Ogre",
        ),
        "**Gear** Greatclub, Javelins (3)<br>\n**Senses** Darkvision 60 ft.; Passive Perception 8<br>\n**Languages** Common, Giant<br>\n**CR** 2 (XP 450; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Ogre",
            "Ogre",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Ogre",
            "Ogre",
            "Actions",
        ),
        "**_Greatclub._** _Melee Attack Roll:_ +6, reach 5 ft. _Hit:_ 13 (2d8 + 4) Bludgeoning damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Ogre",
            "Ogre",
            "Actions",
        ),
        "**_Javelin._** _Melee or Ranged Attack Roll:_ +6, reach 5 ft. or range 30/120 ft. _Hit:_ 11 (2d6 + 4) Piercing damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Oni",
        ),
        "## Oni",
    ),
    (
        (
            "Monsters A–Z",
            "Oni",
            "Oni",
        ),
        "### Oni",
    ),
    (
        (
            "Monsters A–Z",
            "Oni",
            "Oni",
        ),
        "_Large Fiend, Lawful Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Oni",
            "Oni",
        ),
        "**AC** 17 **Initiative** +0 (10) <br>\n**HP** 119 (14d10 + 42) <br>\n**Speed** 30 ft., Fly 30 ft. (hover) <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Oni",
            "Oni",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>19</td>\n      <td>+4</td>\n      <td>+4</td>\n      <td><strong>DEX</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+3</td>\n      <td><strong>CON</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+6</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>WIS</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+4</td>\n      <td><strong>CHA</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+5</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Oni",
            "Oni",
        ),
        "**Skills** Arcana +5, Deception +8, Perception +4<br>\n**Resistances** Cold<br>\n**Senses** Darkvision 60 ft.; Passive Perception 14<br>\n**Languages** Common, Giant<br>\n**CR** 7 (XP 2,900; PB +3)",
    ),
    (
        (
            "Monsters A–Z",
            "Oni",
            "Oni",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Oni",
            "Oni",
            "Traits",
        ),
        "**_Regeneration._** The oni regains 10 Hit Points at the start of each of its turns if it has at least 1 Hit Point.",
    ),
    (
        (
            "Monsters A–Z",
            "Oni",
            "Oni",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Oni",
            "Oni",
            "Actions",
        ),
        "**_Multiattack._** The oni makes two Claw or Nightmare Ray attacks. It can replace one attack with a use of Spellcasting.",
    ),
    (
        (
            "Monsters A–Z",
            "Oni",
            "Oni",
            "Actions",
        ),
        "**_Claw._** _Melee Attack Roll:_ +7, reach 10 ft. _Hit:_ 10 (1d12 + 4) Slashing damage plus 9 (2d8) Necrotic damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Oni",
            "Oni",
            "Actions",
        ),
        "**_Nightmare Ray._** _Ranged Attack Roll:_ +5, range 60 ft. _Hit:_ 9 (2d6 + 2) Psychic damage, and the target has the Frightened condition until the start of the oni's next turn.",
    ),
    (
        (
            "Monsters A–Z",
            "Oni",
            "Oni",
            "Actions",
        ),
        "**_Shape-Shift._** The oni shape-shifts into a Small or Medium Humanoid or a Large Giant, or it returns to its true form. Other than its size, its game statistics are the same in each form. Any equipment it is wearing or carrying isn't transformed.",
    ),
    (
        (
            "Monsters A–Z",
            "Oni",
            "Oni",
            "Actions",
        ),
        "**_Spellcasting._** The oni casts one of the following spells, requiring no Material components and using Charisma as the spellcasting ability (spell save DC 13): <br>\n&emsp;**1/Day Each:** _Charm Person_ (level 2 version), _Darkness_, _Gaseous Form_, _Sleep_",
    ),
    (
        (
            "Monsters A–Z",
            "Oni",
            "Oni",
            "Bonus Actions",
        ),
        "#### Bonus Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Oni",
            "Oni",
            "Bonus Actions",
        ),
        "**_Invisibility._** The oni casts _Invisibility_ on itself, requiring no spell components and using the same spellcasting ability as Spellcasting.",
    ),
    (
        (
            "Monsters A–Z",
            "Otyugh",
        ),
        "## Otyugh",
    ),
    (
        (
            "Monsters A–Z",
            "Otyugh",
            "Otyugh",
        ),
        "### Otyugh",
    ),
    (
        (
            "Monsters A–Z",
            "Otyugh",
            "Otyugh",
        ),
        "_Large Aberration, Neutral_",
    ),
    (
        (
            "Monsters A–Z",
            "Otyugh",
            "Otyugh",
        ),
        "**AC** 14 **Initiative** +0 (10) <br>\n**HP** 104 (11d10 + 44) <br>\n**Speed** 30 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Otyugh",
            "Otyugh",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>DEX</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CON</strong></td>\n      <td>19</td>\n      <td>+4</td>\n      <td>+7</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>6</td>\n      <td>−2</td>\n      <td>−2</td>\n      <td><strong>WIS</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CHA</strong></td>\n      <td>6</td>\n      <td>−2</td>\n      <td>−2</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Otyugh",
            "Otyugh",
        ),
        "**Senses** Darkvision 120 ft.; Passive Perception 11<br>\n**Languages** Otyugh; telepathy 120 ft. (doesn't allow the receiving creature to respond telepathically)<br>\n**CR** 5 (XP 1,800; PB +3)",
    ),
    (
        (
            "Monsters A–Z",
            "Otyugh",
            "Otyugh",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Otyugh",
            "Otyugh",
            "Actions",
        ),
        "**_Multiattack._** The otyugh makes one Bite attack and two Tentacle attacks.",
    ),
    (
        (
            "Monsters A–Z",
            "Otyugh",
            "Otyugh",
            "Actions",
        ),
        "**_Bite._** _Melee Attack Roll:_ +6, reach 5 ft. _Hit:_ 12 (2d8 + 3) Piercing damage, and the target has the Poisoned condition. Whenever the Poisoned target finishes a Long Rest, it is subjected to the following effect. _Constitution Saving Throw:_ DC 15. _Failure:_ The target's Hit Point maximum decreases by 5 (1d10) and doesn't return to normal until the Poisoned condition ends on the target. _Success:_ The Poisoned condition ends.",
    ),
    (
        (
            "Monsters A–Z",
            "Otyugh",
            "Otyugh",
            "Actions",
        ),
        "**_Tentacle._** _Melee Attack Roll:_ +6, reach 10 ft. _Hit:_ 12 (2d8 + 3) Piercing damage. If the target is a Medium or smaller creature, it has the Grappled condition (escape DC 13) from one of two tentacles.",
    ),
    (
        (
            "Monsters A–Z",
            "Otyugh",
            "Otyugh",
            "Actions",
        ),
        "**_Tentacle Slam._** _Constitution Saving Throw:_ DC 14, each creature Grappled by the otyugh. _Failure:_ 16 (3d8 + 3) Bludgeoning damage, and the target has the Stunned condition until the start of the otyugh's next turn. _Success:_ Half damage only.",
    ),
    (
        (
            "Monsters A–Z",
            "Owlbear",
        ),
        "## Owlbear",
    ),
    (
        (
            "Monsters A–Z",
            "Owlbear",
            "Owlbear",
        ),
        "### Owlbear",
    ),
    (
        (
            "Monsters A–Z",
            "Owlbear",
            "Owlbear",
        ),
        "_Large Monstrosity, Unaligned_",
    ),
    (
        (
            "Monsters A–Z",
            "Owlbear",
            "Owlbear",
        ),
        "**AC** 13 **Initiative** +1 (11) <br>\n**HP** 59 (7d10 + 21) <br>\n**Speed** 40 ft., Climb 40 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Owlbear",
            "Owlbear",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>20</td>\n      <td>+5</td>\n      <td>+5</td>\n      <td><strong>DEX</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CON</strong></td>\n      <td>17</td>\n      <td>+3</td>\n      <td>+3</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>3</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>WIS</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CHA</strong></td>\n      <td>7</td>\n      <td>−2</td>\n      <td>−2</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Owlbear",
            "Owlbear",
        ),
        "**Skills** Perception +5<br>\n**Senses** Darkvision 60 ft.; Passive Perception 15<br>\n**Languages** None<br>\n**CR** 3 (XP 700; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Owlbear",
            "Owlbear",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Owlbear",
            "Owlbear",
            "Actions",
        ),
        "**_Multiattack._** The owlbear makes two Rend attacks.",
    ),
    (
        (
            "Monsters A–Z",
            "Owlbear",
            "Owlbear",
            "Actions",
        ),
        "**_Rend._** _Melee Attack Roll:_ +7, reach 5 ft. _Hit:_ 14 (2d8 + 5) Slashing damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Pegasus",
        ),
        "## Pegasus",
    ),
    (
        (
            "Monsters A–Z",
            "Pegasus",
            "Pegasus",
        ),
        "### Pegasus",
    ),
    (
        (
            "Monsters A–Z",
            "Pegasus",
            "Pegasus",
        ),
        "_Large Celestial, Chaotic Good_",
    ),
    (
        (
            "Monsters A–Z",
            "Pegasus",
            "Pegasus",
        ),
        "**AC** 12 **Initiative** +2 (12) <br>\n**HP** 59 (7d10 + 21) <br>\n**Speed** 60 ft., Fly 90 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Pegasus",
            "Pegasus",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+4</td>\n      <td><strong>DEX</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+4</td>\n      <td><strong>CON</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+5</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>WIS</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+4</td>\n      <td><strong>CHA</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+3</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Pegasus",
            "Pegasus",
        ),
        "**Skills** Perception +6<br>\n**Senses** Passive Perception 16<br>\n**Languages** Understands Celestial, Common, Elvish, and Sylvan but can't speak<br>\n**CR** 2 (XP 450; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Pegasus",
            "Pegasus",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Pegasus",
            "Pegasus",
            "Actions",
        ),
        "**_Hooves._** _Melee Attack Roll:_ +6, reach 5 ft. _Hit:_ 7 (1d6 + 4) Bludgeoning damage plus 5 (2d4) Radiant damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Phase Spider",
        ),
        "## Phase Spider",
    ),
    (
        (
            "Monsters A–Z",
            "Phase Spider",
            "Phase Spider",
        ),
        "### Phase Spider",
    ),
    (
        (
            "Monsters A–Z",
            "Phase Spider",
            "Phase Spider",
        ),
        "_Large Monstrosity, Unaligned_",
    ),
    (
        (
            "Monsters A–Z",
            "Phase Spider",
            "Phase Spider",
        ),
        "**AC** 14 **Initiative** +3 (13) <br>\n**HP** 45 (7d10 + 7) <br>\n**Speed** 30 ft., Climb 30 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Phase Spider",
            "Phase Spider",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>DEX</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>CON</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>6</td>\n      <td>−2</td>\n      <td>−2</td>\n      <td><strong>WIS</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CHA</strong></td>\n      <td>6</td>\n      <td>−2</td>\n      <td>−2</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Phase Spider",
            "Phase Spider",
        ),
        "**Skills** Stealth +7<br>\n**Senses** Darkvision 60 ft.; Passive Perception 10<br>\n**Languages** None<br>\n**CR** 3 (XP 700; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Phase Spider",
            "Phase Spider",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Phase Spider",
            "Phase Spider",
            "Traits",
        ),
        "**_Ethereal Sight._** The spider can see 60 feet into the Ethereal Plane while on the Material Plane and vice versa.",
    ),
    (
        (
            "Monsters A–Z",
            "Phase Spider",
            "Phase Spider",
            "Traits",
        ),
        "**_Spider Climb._** The spider can climb difficult surfaces, including along ceilings, without needing to make an ability check.",
    ),
    (
        (
            "Monsters A–Z",
            "Phase Spider",
            "Phase Spider",
            "Traits",
        ),
        "**_Web Walker._** The spider ignores movement restrictions caused by webs, and the spider knows the location of any other creature in contact with the same web.",
    ),
    (
        (
            "Monsters A–Z",
            "Phase Spider",
            "Phase Spider",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Phase Spider",
            "Phase Spider",
            "Actions",
        ),
        "**_Multiattack._** The spider makes two Bite attacks.",
    ),
    (
        (
            "Monsters A–Z",
            "Phase Spider",
            "Phase Spider",
            "Actions",
        ),
        "**_Bite._** _Melee Attack Roll:_ +5, reach 5 ft. _Hit:_ 8 (1d10 + 3) Piercing damage plus 9 (2d8) Poison damage. If this damage reduces the target to 0 Hit Points, the target becomes Stable, and it has the Poisoned condition for 1 hour. While Poisoned, the target also has the Paralyzed condition.",
    ),
    (
        (
            "Monsters A–Z",
            "Phase Spider",
            "Phase Spider",
            "Bonus Actions",
        ),
        "#### Bonus Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Phase Spider",
            "Phase Spider",
            "Bonus Actions",
        ),
        "**_Ethereal Jaunt._** The spider teleports from the Material Plane to the Ethereal Plane or vice versa.",
    ),
    (
        (
            "Monsters A–Z",
            "Pirates",
        ),
        "## Pirates",
    ),
    (
        (
            "Monsters A–Z",
            "Pirates",
            "Pirate",
        ),
        "### Pirate",
    ),
    (
        (
            "Monsters A–Z",
            "Pirates",
            "Pirate",
        ),
        "_Medium or Small Humanoid, Neutral_",
    ),
    (
        (
            "Monsters A–Z",
            "Pirates",
            "Pirate",
        ),
        "**AC** 14 **Initiative** +5 (15) <br>\n**HP** 33 (6d8 + 6) <br>\n**Speed** 30 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Pirates",
            "Pirate",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>DEX</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+5</td>\n      <td><strong>CON</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>8</td>\n      <td>−1</td>\n      <td>−1</td>\n      <td><strong>WIS</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CHA</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+4</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Pirates",
            "Pirate",
        ),
        "**Gear** Daggers (6), Leather Armor<br>\n**Senses** Passive Perception 11<br>\n**Languages** Common plus one other language<br>\n**CR** 1 (XP 200; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Pirates",
            "Pirate",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Pirates",
            "Pirate",
            "Actions",
        ),
        "**_Multiattack._** The pirate makes two Dagger attacks. It can replace one attack with a use of Enthralling Panache.",
    ),
    (
        (
            "Monsters A–Z",
            "Pirates",
            "Pirate",
            "Actions",
        ),
        "**_Dagger._** _Melee or Ranged Attack Roll:_ +5, reach 5 ft. or range 20/60 ft. _Hit:_ 5 (1d4 + 3) Piercing damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Pirates",
            "Pirate",
            "Actions",
        ),
        "**_Enthralling Panache._** _Wisdom Saving Throw:_ DC 12, one creature the pirate can see within 30 feet. _Failure:_ The target has the Charmed condition until the start of the pirate's next turn.",
    ),
    (
        (
            "Monsters A–Z",
            "Pirates",
            "Pirate Captain",
        ),
        "### Pirate Captain",
    ),
    (
        (
            "Monsters A–Z",
            "Pirates",
            "Pirate Captain",
        ),
        "_Medium or Small Humanoid, Neutral_",
    ),
    (
        (
            "Monsters A–Z",
            "Pirates",
            "Pirate Captain",
        ),
        "**AC** 17 **Initiative** +7 (17) <br>\n**HP** 84 (13d8 + 26) <br>\n**Speed** 30 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Pirates",
            "Pirate Captain",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+3</td>\n      <td><strong>DEX</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+7</td>\n      <td><strong>CON</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>WIS</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+5</td>\n      <td><strong>CHA</strong></td>\n      <td>17</td>\n      <td>+3</td>\n      <td>+6</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Pirates",
            "Pirate Captain",
        ),
        "**Skills** Acrobatics +7, Perception +5<br>\n**Gear** Pistol, Rapier<br>\n**Senses** Passive Perception 15<br>\n**Languages** Common plus one other language<br>\n**CR** 6 (XP 2,300; PB +3)",
    ),
    (
        (
            "Monsters A–Z",
            "Pirates",
            "Pirate Captain",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Pirates",
            "Pirate Captain",
            "Actions",
        ),
        "**_Multiattack._** The pirate makes three attacks, using Rapier or Pistol in any combination.",
    ),
    (
        (
            "Monsters A–Z",
            "Pirates",
            "Pirate Captain",
            "Actions",
        ),
        "**_Rapier._** _Melee Attack Roll:_ +7, reach 5 ft. _Hit:_ 13 (2d8 + 4) Piercing damage, and the pirate has Advantage on the next attack roll it makes before the end of this turn.",
    ),
    (
        (
            "Monsters A–Z",
            "Pirates",
            "Pirate Captain",
            "Actions",
        ),
        "**_Pistol._** _Ranged Attack Roll:_ +7, range 30/90 ft. _Hit:_ 15 (2d10 + 4) Piercing damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Pirates",
            "Pirate Captain",
            "Bonus Actions",
        ),
        "#### Bonus Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Pirates",
            "Pirate Captain",
            "Bonus Actions",
        ),
        "**_Captain's Charm._** _Wisdom Saving Throw:_ DC 14, one creature the pirate can see within 30 feet. _Failure:_ The target has the Charmed condition until the start of the pirate's next turn.",
    ),
    (
        (
            "Monsters A–Z",
            "Pirates",
            "Pirate Captain",
            "Reactions",
        ),
        "#### Reactions",
    ),
    (
        (
            "Monsters A–Z",
            "Pirates",
            "Pirate Captain",
            "Reactions",
        ),
        "**_Riposte._** _Trigger:_ The pirate is hit by a melee attack roll while holding a weapon. _Response:_ The pirate adds 3 to its AC against that attack, possibly causing it to miss. On a miss, the pirate makes one Rapier attack against the triggering creature if within range.",
    ),
    (
        (
            "Monsters A–Z",
            "Pit Fiend",
        ),
        "## Pit Fiend",
    ),
    (
        (
            "Monsters A–Z",
            "Pit Fiend",
            "Pit Fiend",
        ),
        "### Pit Fiend",
    ),
    (
        (
            "Monsters A–Z",
            "Pit Fiend",
            "Pit Fiend",
        ),
        "_Large Fiend (Devil), Lawful Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Pit Fiend",
            "Pit Fiend",
        ),
        "**AC** 21 **Initiative** +14 (24) <br>\n**HP** 337 (27d10 + 189) <br>\n**Speed** 30 ft., Fly 60 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Pit Fiend",
            "Pit Fiend",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>26</td>\n      <td>+8</td>\n      <td>+8</td>\n      <td><strong>DEX</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+8</td>\n      <td><strong>CON</strong></td>\n      <td>24</td>\n      <td>+7</td>\n      <td>+7</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>22</td>\n      <td>+6</td>\n      <td>+6</td>\n      <td><strong>WIS</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+10</td>\n      <td><strong>CHA</strong></td>\n      <td>24</td>\n      <td>+7</td>\n      <td>+7</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Pit Fiend",
            "Pit Fiend",
        ),
        "**Skills** Perception +10, Persuasion +19<br>\n**Resistances** Cold<br>\n**Immunities** Fire, Poison; Poisoned<br>\n**Senses** Truesight 120 ft.; Passive Perception 20<br>\n**Languages** Infernal; telepathy 120 ft.<br>\n**CR** 20 (XP 25,000; PB +6)",
    ),
    (
        (
            "Monsters A–Z",
            "Pit Fiend",
            "Pit Fiend",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Pit Fiend",
            "Pit Fiend",
            "Traits",
        ),
        "**_Diabolical Restoration._** If the pit fiend dies outside the Nine Hells, its body disappears in sulfurous smoke, and it gains a new body instantly, reviving with all its Hit Points somewhere in the Nine Hells.",
    ),
    (
        (
            "Monsters A–Z",
            "Pit Fiend",
            "Pit Fiend",
            "Traits",
        ),
        "**_Fear Aura._** The pit fiend emanates an aura in a 20-foot Emanation while it doesn't have the Incapacitated condition. _Wisdom Saving Throw:_ DC 21, any enemy that starts its turn in the aura. _Failure:_ The target has the Frightened condition until the start of its next turn. _Success:_ The target is immune to this pit fiend's aura for 24 hours.",
    ),
    (
        (
            "Monsters A–Z",
            "Pit Fiend",
            "Pit Fiend",
            "Traits",
        ),
        "**_Legendary Resistance (4/Day)._** If the pit fiend fails a saving throw, it can choose to succeed instead.",
    ),
    (
        (
            "Monsters A–Z",
            "Pit Fiend",
            "Pit Fiend",
            "Traits",
        ),
        "**_Magic Resistance._** The pit fiend has Advantage on saving throws against spells and other magical effects.",
    ),
    (
        (
            "Monsters A–Z",
            "Pit Fiend",
            "Pit Fiend",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Pit Fiend",
            "Pit Fiend",
            "Actions",
        ),
        "**_Multiattack._** The pit fiend makes one Bite attack, two Devilish Claw attacks, and one Fiery Mace attack.",
    ),
    (
        (
            "Monsters A–Z",
            "Pit Fiend",
            "Pit Fiend",
            "Actions",
        ),
        "**_Bite._** _Melee Attack Roll:_ +14, reach 10 ft. _Hit:_ 18 (3d6 + 8) Piercing damage. If the target is a creature, it must make the following saving throw. _Constitution Saving Throw:_ DC 21. _Failure:_ The target has the Poisoned condition. While Poisoned, the target can't regain Hit Points and takes 21 (6d6) Poison damage at the start of each of its turns, and it repeats the save at the end of each of its turns, ending the effect on itself on a success. After 1 minute, it succeeds automatically.",
    ),
    (
        (
            "Monsters A–Z",
            "Pit Fiend",
            "Pit Fiend",
            "Actions",
        ),
        "**_Devilish Claw._** _Melee Attack Roll:_ +14, reach 10 ft. _Hit:_ 26 (4d8 + 8) Necrotic damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Pit Fiend",
            "Pit Fiend",
            "Actions",
        ),
        "**_Fiery Mace._** _Melee Attack Roll:_ +14, reach 10 ft. _Hit:_ 22 (4d6 + 8) Force damage plus 21 (6d6) Fire damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Pit Fiend",
            "Pit Fiend",
            "Actions",
        ),
        "**_Hellfire Spellcasting (Recharge 4–6)._** The pit fiend casts _Fireball_ (level 5 version) twice, requiring no Material components and using Charisma as the spellcasting ability (spell save DC 21). It can replace one _Fireball_ with _Hold Monster_ (level 7 version) or _Wall of Fire_.",
    ),
    (
        (
            "Monsters A–Z",
            "Planetar",
        ),
        "## Planetar",
    ),
    (
        (
            "Monsters A–Z",
            "Planetar",
            "Planetar",
        ),
        "### Planetar",
    ),
    (
        (
            "Monsters A–Z",
            "Planetar",
            "Planetar",
        ),
        "_Large Celestial (Angel), Lawful Good_",
    ),
    (
        (
            "Monsters A–Z",
            "Planetar",
            "Planetar",
        ),
        "**AC** 19 **Initiative** +10 (20) <br>\n**HP** 262 (21d10 + 147) <br>\n**Speed** 40 ft., Fly 120 ft. (hover) <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Planetar",
            "Planetar",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>24</td>\n      <td>+7</td>\n      <td>+12</td>\n      <td><strong>DEX</strong></td>\n      <td>20</td>\n      <td>+5</td>\n      <td>+5</td>\n      <td><strong>CON</strong></td>\n      <td>24</td>\n      <td>+7</td>\n      <td>+12</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>19</td>\n      <td>+4</td>\n      <td>+4</td>\n      <td><strong>WIS</strong></td>\n      <td>22</td>\n      <td>+6</td>\n      <td>+11</td>\n      <td><strong>CHA</strong></td>\n      <td>25</td>\n      <td>+7</td>\n      <td>+12</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Planetar",
            "Planetar",
        ),
        "**Skills** Perception +11<br>\n**Resistances** Radiant<br>\n**Immunities** Charmed, Exhaustion, Frightened<br>\n**Senses** Truesight 120 ft.; Passive Perception 21<br>\n**Languages** All; telepathy 120 ft.<br>\n**CR** 16 (XP 15,000; PB +5)",
    ),
    (
        (
            "Monsters A–Z",
            "Planetar",
            "Planetar",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Planetar",
            "Planetar",
            "Traits",
        ),
        "**_Divine Awareness._** The planetar knows if it hears a lie.",
    ),
    (
        (
            "Monsters A–Z",
            "Planetar",
            "Planetar",
            "Traits",
        ),
        "**_Exalted Restoration._** If the planetar dies outside Mount Celestia, its body disappears, and it gains a new body instantly, reviving with all its Hit Points somewhere in Mount Celestia.",
    ),
    (
        (
            "Monsters A–Z",
            "Planetar",
            "Planetar",
            "Traits",
        ),
        "**_Magic Resistance._** The planetar has Advantage on saving throws against spells and other magical effects.",
    ),
    (
        (
            "Monsters A–Z",
            "Planetar",
            "Planetar",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Planetar",
            "Planetar",
            "Actions",
        ),
        "**_Multiattack._** The planetar makes three Radiant Sword attacks or uses Holy Burst twice.",
    ),
    (
        (
            "Monsters A–Z",
            "Planetar",
            "Planetar",
            "Actions",
        ),
        "**_Radiant Sword._** _Melee Attack Roll:_ +12, reach 10 ft. _Hit:_ 14 (2d6 + 7) Slashing damage plus 18 (4d8) Radiant damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Planetar",
            "Planetar",
            "Actions",
        ),
        "**_Holy Burst._** _Dexterity Saving Throw:_ DC 20, each enemy in a 20-foot-radius Sphere centered on a point the planetar can see within 120 feet. _Failure:_ 24 (7d6) Radiant damage. _Success:_ Half damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Planetar",
            "Planetar",
            "Actions",
        ),
        "**_Spellcasting._** The planetar casts one of the following spells, requiring no Material components and using Charisma as spellcasting ability (spell save DC 20): <br>\n&emsp;**At Will:** _Detect Evil and Good_ <br>\n&emsp;**1/Day Each:** _Commune_, _Control Weather_, _Dispel Evil and Good_, _Raise Dead_",
    ),
    (
        (
            "Monsters A–Z",
            "Planetar",
            "Planetar",
            "Bonus Actions",
        ),
        "#### Bonus Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Planetar",
            "Planetar",
            "Bonus Actions",
        ),
        "**_Divine Aid (2/Day)._** The planetar casts _Cure Wounds_, _Invisibility_, _Lesser Restoration_, or _Remove Curse_, using the same spellcasting ability as Spellcasting.",
    ),
    (
        (
            "Monsters A–Z",
            "Priests",
        ),
        "## Priests",
    ),
    (
        (
            "Monsters A–Z",
            "Priests",
            "Priest Acolyte",
        ),
        "### Priest Acolyte",
    ),
    (
        (
            "Monsters A–Z",
            "Priests",
            "Priest Acolyte",
        ),
        "_Medium or Small Humanoid (Cleric), Neutral_",
    ),
    (
        (
            "Monsters A–Z",
            "Priests",
            "Priest Acolyte",
        ),
        "**AC** 13 **Initiative** +0 (10) <br>\n**HP** 11 (2d8 + 2) <br>\n**Speed** 30 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Priests",
            "Priest Acolyte",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>DEX</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CON</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>WIS</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CHA</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Priests",
            "Priest Acolyte",
        ),
        "**Skills** Medicine +4, Religion +2<br>\n**Gear** Chain Shirt, Holy Symbol, Mace<br>\n**Senses** Passive Perception 12<br>\n**Languages** Common<br>\n**CR** 1/4 (XP 50; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Priests",
            "Priest Acolyte",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Priests",
            "Priest Acolyte",
            "Actions",
        ),
        "**_Mace._** _Melee Attack Roll:_ +4, reach 5 ft. _Hit:_ 5 (1d6 + 2) Bludgeoning damage plus 2 (1d4) Radiant damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Priests",
            "Priest Acolyte",
            "Actions",
        ),
        "**_Radiant Flame._** _Ranged Attack Roll:_ +4, range 60 ft. _Hit:_ 7 (2d6) Radiant damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Priests",
            "Priest Acolyte",
            "Actions",
        ),
        "**_Spellcasting._** The priest casts one of the following spells, using Wisdom as the spellcasting ability: <br>\n&emsp;**At Will:** _Light, Thaumaturgy_",
    ),
    (
        (
            "Monsters A–Z",
            "Priests",
            "Priest Acolyte",
            "Bonus Actions",
        ),
        "#### Bonus Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Priests",
            "Priest Acolyte",
            "Bonus Actions",
        ),
        "**_Divine Aid (1/Day)._** The priest casts _Bless, Healing Word,_ or _Sanctuary,_ using the same spellcasting ability as Spellcasting.",
    ),
    (
        (
            "Monsters A–Z",
            "Priests",
            "Priest",
        ),
        "### Priest",
    ),
    (
        (
            "Monsters A–Z",
            "Priests",
            "Priest",
        ),
        "_Medium or Small Humanoid (Cleric), Neutral_",
    ),
    (
        (
            "Monsters A–Z",
            "Priests",
            "Priest",
        ),
        "**AC** 13 **Initiative** +0 (10) <br>\n**HP** 38 (7d8 + 7) <br>\n**Speed** 30 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Priests",
            "Priest",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>DEX</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CON</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>WIS</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>CHA</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Priests",
            "Priest",
        ),
        "**Skills** Medicine +7, Perception +5, Religion +5<br>\n**Gear** Chain Shirt, Holy Symbol, Mace<br>\n**Senses** Passive Perception 15<br>\n**Languages** Common plus one other language<br>\n**CR** 2 (XP 450; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Priests",
            "Priest",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Priests",
            "Priest",
            "Actions",
        ),
        "**_Multiattack._** The priest makes two attacks, using Mace or Radiant Flame in any combination.",
    ),
    (
        (
            "Monsters A–Z",
            "Priests",
            "Priest",
            "Actions",
        ),
        "**_Mace._** _Melee Attack Roll:_ +5, reach 5 ft. _Hit:_ 6 (1d6 + 3) Bludgeoning damage plus 5 (2d4) Radiant damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Priests",
            "Priest",
            "Actions",
        ),
        "**_Radiant Flame._** _Ranged Attack Roll:_ +5, range 60 ft. _Hit:_ 11 (2d10) Radiant damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Priests",
            "Priest",
            "Actions",
        ),
        "**_Spellcasting._** The priest casts one of the following spells, using Wisdom as the spellcasting ability (spell save DC 13): <br>\n&emsp;**At Will:** _Light, Thaumaturgy_ <br>\n&emsp;**1/Day:** _Spirit Guardians_",
    ),
    (
        (
            "Monsters A–Z",
            "Priests",
            "Priest",
            "Bonus Actions",
        ),
        "#### Bonus Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Priests",
            "Priest",
            "Bonus Actions",
        ),
        "**_Divine Aid (3/Day)._** The priest casts _Bless, Dispel Magic, Healing Word,_ or _Lesser Restoration,_ using the same spellcasting ability as Spellcasting.",
    ),
    (
        (
            "Monsters A–Z",
            "Pseudodragon",
        ),
        "## Pseudodragon",
    ),
    (
        (
            "Monsters A–Z",
            "Pseudodragon",
            "Pseudodragon",
        ),
        "### Pseudodragon",
    ),
    (
        (
            "Monsters A–Z",
            "Pseudodragon",
            "Pseudodragon",
        ),
        "_Tiny Dragon, Neutral Good_",
    ),
    (
        (
            "Monsters A–Z",
            "Pseudodragon",
            "Pseudodragon",
        ),
        "**AC** 14 **Initiative** +2 (12) <br>\n**HP** 10 (3d4 + 3) <br>\n**Speed** 15 ft., Fly 60 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Pseudodragon",
            "Pseudodragon",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>6</td>\n      <td>−2</td>\n      <td>−2</td>\n      <td><strong>DEX</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CON</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>WIS</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CHA</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Pseudodragon",
            "Pseudodragon",
        ),
        "**Skills** Perception +5, Stealth +4<br>\n**Senses** Blindsight 10 ft., Darkvision 60 ft.; Passive Perception 15<br>\n**Languages** Understands Common and Draconic but can't speak<br>\n**CR** 1/4 (XP 50; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Pseudodragon",
            "Pseudodragon",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Pseudodragon",
            "Pseudodragon",
            "Traits",
        ),
        "**_Magic Resistance._** The pseudodragon has Advantage on saving throws against spells and other magical effects.",
    ),
    (
        (
            "Monsters A–Z",
            "Pseudodragon",
            "Pseudodragon",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Pseudodragon",
            "Pseudodragon",
            "Actions",
        ),
        "**_Multiattack._** The pseudodragon makes two Bite attacks.",
    ),
    (
        (
            "Monsters A–Z",
            "Pseudodragon",
            "Pseudodragon",
            "Actions",
        ),
        "**_Bite._** _Melee Attack Roll:_ +4, reach 5 ft. _Hit:_ 4 (1d4 + 2) Piercing damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Pseudodragon",
            "Pseudodragon",
            "Actions",
        ),
        "**_Sting._** _Constitution Saving Throw:_ DC 12, one creature the pseudodragon can see within 5 feet. _Failure:_ 5 (2d4) Poison damage, and the target has the Poisoned condition for 1 hour. _Failure by 5 or More:_ While Poisoned, the target also has the Unconscious condition, which ends early if the target takes damage or a creature within 5 feet of it takes an action to wake it.",
    ),
    (
        (
            "Monsters A–Z",
            "Purple Worm",
        ),
        "## Purple Worm",
    ),
    (
        (
            "Monsters A–Z",
            "Purple Worm",
            "Purple Worm",
        ),
        "### Purple Worm",
    ),
    (
        (
            "Monsters A–Z",
            "Purple Worm",
            "Purple Worm",
        ),
        "_Gargantuan Monstrosity, Unaligned_",
    ),
    (
        (
            "Monsters A–Z",
            "Purple Worm",
            "Purple Worm",
        ),
        "**AC** 18 **Initiative** +3 (13) <br>\n**HP** 247 (15d20 + 90) <br>\n**Speed** 50 ft., Burrow 50 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Purple Worm",
            "Purple Worm",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>28</td>\n      <td>+9</td>\n      <td>+9</td>\n      <td><strong>DEX</strong></td>\n      <td>7</td>\n      <td>−2</td>\n      <td>−2</td>\n      <td><strong>CON</strong></td>\n      <td>22</td>\n      <td>+6</td>\n      <td>+11</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>1</td>\n      <td>−5</td>\n      <td>−5</td>\n      <td><strong>WIS</strong></td>\n      <td>8</td>\n      <td>−1</td>\n      <td>+4</td>\n      <td><strong>CHA</strong></td>\n      <td>4</td>\n      <td>−3</td>\n      <td>−3</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Purple Worm",
            "Purple Worm",
        ),
        "**Senses** Blindsight 30 ft., Tremorsense 60 ft.; Passive Perception 9<br>\n**Languages** None<br>\n**CR** 15 (XP 13,000; PB +5)",
    ),
    (
        (
            "Monsters A–Z",
            "Purple Worm",
            "Purple Worm",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Purple Worm",
            "Purple Worm",
            "Traits",
        ),
        "**_Tunneler._** The worm can burrow through solid rock at half its Burrow Speed and leaves a 10-foot-diameter tunnel in its wake.",
    ),
    (
        (
            "Monsters A–Z",
            "Purple Worm",
            "Purple Worm",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Purple Worm",
            "Purple Worm",
            "Actions",
        ),
        "**_Multiattack._** The worm makes one Bite attack and one Tail Stinger attack.",
    ),
    (
        (
            "Monsters A–Z",
            "Purple Worm",
            "Purple Worm",
            "Actions",
        ),
        "**_Bite._** _Melee Attack Roll:_ +14, reach 10 ft. _Hit:_ 22 (3d8 + 9) Piercing damage. If the target is a Large or smaller creature, it has the Grappled condition (escape DC 19), and it has the Restrained condition until the grapple ends.",
    ),
    (
        (
            "Monsters A–Z",
            "Purple Worm",
            "Purple Worm",
            "Actions",
        ),
        "**_Tail Stinger._** _Melee Attack Roll:_ +14, reach 10 ft. _Hit:_ 16 (2d6 + 9) Piercing damage plus 35 (10d6) Poison damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Purple Worm",
            "Purple Worm",
            "Bonus Actions",
        ),
        "#### Bonus Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Purple Worm",
            "Purple Worm",
            "Bonus Actions",
        ),
        "**_Swallow._** _Strength Saving Throw:_ DC 19, one Large or smaller creature Grappled by the worm (it can have up to three creatures swallowed at a time). _Failure:_ The target is swallowed by the worm, and the Grappled condition ends. A swallowed creature has the Blinded and Restrained conditions, has Total Cover against attacks and other effects outside the worm, and takes 17 (5d6) Acid damage at the start of each of the worm's turns. <br>\n&emsp;If the worm takes 30 damage or more on a single turn from a creature inside it, the worm must succeed on a DC 21 Constitution saving throw at the end of that turn or regurgitate all swallowed creatures, each of which falls in a space within 5 feet of the worm and has the Prone condition. If the worm dies, any swallowed creature no longer has the Restrained condition and can escape from the corpse using 20 feet of movement, exiting Prone.",
    ),
    (
        (
            "Monsters A–Z",
            "Quasit",
        ),
        "## Quasit",
    ),
    (
        (
            "Monsters A–Z",
            "Quasit",
            "Quasit",
        ),
        "### Quasit",
    ),
    (
        (
            "Monsters A–Z",
            "Quasit",
            "Quasit",
        ),
        "_Tiny Fiend (Demon), Chaotic Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Quasit",
            "Quasit",
        ),
        "**AC** 13 **Initiative** +3 (13) <br>\n**HP** 25 (10d4) <br>\n**Speed** 40 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Quasit",
            "Quasit",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>5</td>\n      <td>−3</td>\n      <td>−3</td>\n      <td><strong>DEX</strong></td>\n      <td>17</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>CON</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>7</td>\n      <td>−2</td>\n      <td>−2</td>\n      <td><strong>WIS</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CHA</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Quasit",
            "Quasit",
        ),
        "**Skills** Stealth +5<br>\n**Resistances** Cold, Fire, Lightning<br>\n**Immunities** Poison; Poisoned<br>\n**Senses** Darkvision 120 ft.; Passive Perception 10<br>\n**Languages** Abyssal, Common<br>\n**CR** 1 (XP 200; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Quasit",
            "Quasit",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Quasit",
            "Quasit",
            "Traits",
        ),
        "**_Magic Resistance._** The quasit has Advantage on saving throws against spells and other magical effects.",
    ),
    (
        (
            "Monsters A–Z",
            "Quasit",
            "Quasit",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Quasit",
            "Quasit",
            "Actions",
        ),
        "**_Rend._** _Melee Attack Roll:_ +5, reach 5 ft. _Hit:_ 5 (1d4 + 3) Slashing damage, and the target has the Poisoned condition until the start of the quasit's next turn.",
    ),
    (
        (
            "Monsters A–Z",
            "Quasit",
            "Quasit",
            "Actions",
        ),
        "**_Invisibility._** The quasit casts _Invisibility_ on itself, requiring no spell components and using Charisma as the spellcasting ability.",
    ),
    (
        (
            "Monsters A–Z",
            "Quasit",
            "Quasit",
            "Actions",
        ),
        "**_Scare (1/Day)._** _Wisdom Saving Throw:_ DC 10, one creature within 20 feet. _Failure:_ The target has the Frightened condition. At the end of each of its turns, the target repeats the save, ending the effect on itself on a success. After 1 minute, it succeeds automatically.",
    ),
    (
        (
            "Monsters A–Z",
            "Quasit",
            "Quasit",
            "Actions",
        ),
        "**_Shape-Shift._** The quasit shape-shifts to resemble a bat (Speed 10 ft., Fly 40 ft.), a centipede (40 ft., Climb 40 ft.), or a toad (40 ft., Swim 40 ft.), or it returns to its true form. Its game statistics are the same in each form, except for its Speed. Any equipment it is wearing or carrying isn't transformed.",
    ),
    (
        (
            "Monsters A–Z",
            "Rakshasa",
        ),
        "## Rakshasa",
    ),
    (
        (
            "Monsters A–Z",
            "Rakshasa",
            "Rakshasa",
        ),
        "### Rakshasa",
    ),
    (
        (
            "Monsters A–Z",
            "Rakshasa",
            "Rakshasa",
        ),
        "_Medium Fiend, Lawful Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Rakshasa",
            "Rakshasa",
        ),
        "**AC** 17 **Initiative** +8 (18) <br>\n**HP** 221 (26d8 + 104) <br>\n**Speed** 40 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Rakshasa",
            "Rakshasa",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>DEX</strong></td>\n      <td>17</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>CON</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+4</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>WIS</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>CHA</strong></td>\n      <td>20</td>\n      <td>+5</td>\n      <td>+5</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Rakshasa",
            "Rakshasa",
        ),
        "**Skills** Deception +10, Insight +8, Perception +8<br>\n**Vulnerabilities** Piercing damage from weapons wielded by creatures under the effect of a _Bless_ spell<br>\n**Immunities** Charmed, Frightened<br>\n**Senses** Truesight 60 ft.; Passive Perception 18<br>\n**Languages** Common, Infernal<br>\n**CR** 13 (XP 10,000; PB +5)",
    ),
    (
        (
            "Monsters A–Z",
            "Rakshasa",
            "Rakshasa",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Rakshasa",
            "Rakshasa",
            "Traits",
        ),
        "**_Greater Magic Resistance._** The rakshasa automatically succeeds on saving throws against spells and other magical effects, and the attack rolls of spells automatically miss it. Without the rakshasa's permission, no spell can observe the rakshasa remotely or detect its thoughts, creature type, or alignment.",
    ),
    (
        (
            "Monsters A–Z",
            "Rakshasa",
            "Rakshasa",
            "Traits",
        ),
        "**_Fiendish Restoration._** If the rakshasa dies outside the Nine Hells, its body turns to ichor, and it gains a new body instantly, reviving with all its Hit Points somewhere in the Nine Hells.",
    ),
    (
        (
            "Monsters A–Z",
            "Rakshasa",
            "Rakshasa",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Rakshasa",
            "Rakshasa",
            "Actions",
        ),
        "**_Multiattack._** The rakshasa makes three Cursed Touch attacks.",
    ),
    (
        (
            "Monsters A–Z",
            "Rakshasa",
            "Rakshasa",
            "Actions",
        ),
        "**_Cursed Touch._** _Melee Attack Roll:_ +10, reach 5 ft. _Hit:_ 12 (2d6 + 5) Slashing damage plus 19 (3d12) Necrotic damage. If the target is a creature, it is cursed. While cursed, the target gains no benefit from finishing a Short or Long Rest.",
    ),
    (
        (
            "Monsters A–Z",
            "Rakshasa",
            "Rakshasa",
            "Actions",
        ),
        "**_Baleful Command (Recharge 5–6)._** _Wisdom Saving Throw:_ DC 18, each enemy in a 30-foot Emanation originating from the rakshasa. _Failure:_ 28 (8d6) Psychic damage, and the target has the Frightened and Incapacitated conditions until the start of the rakshasa's next turn.",
    ),
    (
        (
            "Monsters A–Z",
            "Rakshasa",
            "Rakshasa",
            "Actions",
        ),
        "**_Spellcasting._** The rakshasa casts one of the following spells, requiring no Material components and using Charisma as the spellcasting ability (spell save DC 18): <br>\n&emsp;**At Will:** _Detect Magic, Detect Thoughts, Disguise Self, Mage Hand, Minor Illusion_ <br>\n&emsp;**1/Day Each:** _Fly, Invisibility, Major Image, Plane Shift_",
    ),
    (
        (
            "Monsters A–Z",
            "Red Dragons",
        ),
        "## Red Dragons",
    ),
    (
        (
            "Monsters A–Z",
            "Red Dragons",
            "Red Dragon Wyrmling",
        ),
        "### Red Dragon Wyrmling",
    ),
    (
        (
            "Monsters A–Z",
            "Red Dragons",
            "Red Dragon Wyrmling",
        ),
        "_Medium Dragon (Chromatic), Chaotic Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Red Dragons",
            "Red Dragon Wyrmling",
        ),
        "**AC** 17 **Initiative** +2 (12) <br>\n**HP** 75 (10d8 + 30) <br>\n**Speed** 30 ft., Climb 30 ft., Fly 60 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Red Dragons",
            "Red Dragon Wyrmling",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>19</td>\n      <td>+4</td>\n      <td>+4</td>\n      <td><strong>DEX</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+2</td>\n      <td><strong>CON</strong></td>\n      <td>17</td>\n      <td>+3</td>\n      <td>+3</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>WIS</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+2</td>\n      <td><strong>CHA</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Red Dragons",
            "Red Dragon Wyrmling",
        ),
        "**Skills** Perception +4, Stealth +2<br>\n**Immunities** Fire<br>\n**Senses** Blindsight 10 ft., Darkvision 60 ft.; Passive Perception 14<br>\n**Languages** Draconic<br>\n**CR** 4 (XP 1,100; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Red Dragons",
            "Red Dragon Wyrmling",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Red Dragons",
            "Red Dragon Wyrmling",
            "Actions",
        ),
        "**_Multiattack._** The dragon makes two Rend attacks.",
    ),
    (
        (
            "Monsters A–Z",
            "Red Dragons",
            "Red Dragon Wyrmling",
            "Actions",
        ),
        "**_Rend._** _Melee Attack Roll:_ +6, reach 5 ft. _Hit:_ 9 (1d10 + 4) Slashing damage plus 3 (1d6) Fire damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Red Dragons",
            "Red Dragon Wyrmling",
            "Actions",
        ),
        "**_Fire Breath (Recharge 5–6)._** _Dexterity Saving Throw:_ DC 13, each creature in a 15-foot Cone. _Failure:_ 24 (7d6) Fire damage. _Success:_ Half damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Red Dragons",
            "Young Red Dragon",
        ),
        "### Young Red Dragon",
    ),
    (
        (
            "Monsters A–Z",
            "Red Dragons",
            "Young Red Dragon",
        ),
        "_Large Dragon (Chromatic), Chaotic Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Red Dragons",
            "Young Red Dragon",
        ),
        "**AC** 18 **Initiative** +4 (14) <br>\n**HP** 178 (17d10 + 85) <br>\n**Speed** 40 ft., Climb 40 ft., Fly 80 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Red Dragons",
            "Young Red Dragon",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>23</td>\n      <td>+6</td>\n      <td>+6</td>\n      <td><strong>DEX</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+4</td>\n      <td><strong>CON</strong></td>\n      <td>21</td>\n      <td>+5</td>\n      <td>+5</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>WIS</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+4</td>\n      <td><strong>CHA</strong></td>\n      <td>19</td>\n      <td>+4</td>\n      <td>+4</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Red Dragons",
            "Young Red Dragon",
        ),
        "**Skills** Perception +8, Stealth +4<br>\n**Immunities** Fire<br>\n**Senses** Blindsight 30 ft., Darkvision 120 ft.; Passive Perception 18<br>\n**Languages** Common, Draconic<br>\n**CR** 10 (XP 5,900; PB +4)",
    ),
    (
        (
            "Monsters A–Z",
            "Red Dragons",
            "Young Red Dragon",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Red Dragons",
            "Young Red Dragon",
            "Actions",
        ),
        "**_Multiattack._** The dragon makes three Rend attacks.",
    ),
    (
        (
            "Monsters A–Z",
            "Red Dragons",
            "Young Red Dragon",
            "Actions",
        ),
        "**_Rend._** _Melee Attack Roll:_ +10, reach 10 ft. _Hit:_ 13 (2d6 + 6) Slashing damage plus 3 (1d6) Fire damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Red Dragons",
            "Young Red Dragon",
            "Actions",
        ),
        "**_Fire Breath (Recharge 5–6)._** _Dexterity Saving Throw:_ DC 17, each creature in a 30-foot Cone. _Failure:_ 56 (16d6) Fire damage. _Success:_ Half damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Red Dragons",
            "Adult Red Dragon",
        ),
        "### Adult Red Dragon",
    ),
    (
        (
            "Monsters A–Z",
            "Red Dragons",
            "Adult Red Dragon",
        ),
        "_Huge Dragon (Chromatic), Chaotic Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Red Dragons",
            "Adult Red Dragon",
        ),
        "**AC** 19 **Initiative** +12 (22) <br>\n**HP** 256 (19d12 + 133) <br>\n**Speed** 40 ft., Climb 40 ft., Fly 80 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Red Dragons",
            "Adult Red Dragon",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>27</td>\n      <td>+8</td>\n      <td>+8</td>\n      <td><strong>DEX</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+6</td>\n      <td><strong>CON</strong></td>\n      <td>25</td>\n      <td>+7</td>\n      <td>+7</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>WIS</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+7</td>\n      <td><strong>CHA</strong></td>\n      <td>23</td>\n      <td>+6</td>\n      <td>+6</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Red Dragons",
            "Adult Red Dragon",
        ),
        "**Skills** Perception +13, Stealth +6<br>\n**Immunities** Fire<br>\n**Senses** Blindsight 60 ft., Darkvision 120 ft.; Passive Perception 23<br>\n**Languages** Common, Draconic<br>\n**CR** 17 (XP 18,000, or 20,000 in lair; PB +6)",
    ),
    (
        (
            "Monsters A–Z",
            "Red Dragons",
            "Adult Red Dragon",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Red Dragons",
            "Adult Red Dragon",
            "Traits",
        ),
        "**_Legendary Resistance (3/Day, or 4/Day in Lair)._** If the dragon fails a saving throw, it can choose to succeed instead.",
    ),
    (
        (
            "Monsters A–Z",
            "Red Dragons",
            "Adult Red Dragon",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Red Dragons",
            "Adult Red Dragon",
            "Actions",
        ),
        "**_Multiattack._** The dragon makes three Rend attacks. It can replace one attack with a use of Spellcasting to cast _Scorching Ray_.",
    ),
    (
        (
            "Monsters A–Z",
            "Red Dragons",
            "Adult Red Dragon",
            "Actions",
        ),
        "**_Rend._** _Melee Attack Roll:_ +14, reach 10 ft. _Hit:_ 13 (1d10 + 8) Slashing damage plus 5 (2d4) Fire damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Red Dragons",
            "Adult Red Dragon",
            "Actions",
        ),
        "**_Fire Breath (Recharge 5–6)._** _Dexterity Saving Throw:_ DC 21, each creature in a 60-foot Cone. _Failure:_ 59 (17d6) Fire damage. _Success:_ Half damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Red Dragons",
            "Adult Red Dragon",
            "Actions",
        ),
        "**_Spellcasting._** The dragon casts one of the following spells, requiring no Material components and using Charisma as the spellcasting ability (spell save DC 20, +12 to hit with spell attacks): <br>\n&emsp;**At Will:** _Command_ (level 2 version), _Detect Magic_, _Scorching Ray_ <br>\n&emsp;**1/Day:** _Fireball_",
    ),
    (
        (
            "Monsters A–Z",
            "Red Dragons",
            "Adult Red Dragon",
            "Legendary Actions",
        ),
        "#### Legendary Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Red Dragons",
            "Adult Red Dragon",
            "Legendary Actions",
        ),
        "_Legendary Action Uses: 3 (4 in Lair). Immediately after another creature's turn, the dragon can expend a use to take one of the following actions. The dragon regains all expended uses at the start of each of its turns._",
    ),
    (
        (
            "Monsters A–Z",
            "Red Dragons",
            "Adult Red Dragon",
            "Legendary Actions",
        ),
        "**_Commanding Presence._** The dragon uses Spellcasting to cast _Command_ (level 2 version). The dragon can't take this action again until the start of its next turn.",
    ),
    (
        (
            "Monsters A–Z",
            "Red Dragons",
            "Adult Red Dragon",
            "Legendary Actions",
        ),
        "**_Fiery Rays._** The dragon uses Spellcasting to cast _Scorching Ray_. The dragon can't take this action again until the start of its next turn.",
    ),
    (
        (
            "Monsters A–Z",
            "Red Dragons",
            "Adult Red Dragon",
            "Legendary Actions",
        ),
        "**_Pounce._** The dragon moves up to half its Speed, and it makes one Rend attack.",
    ),
    (
        (
            "Monsters A–Z",
            "Red Dragons",
            "Ancient Red Dragon",
        ),
        "### Ancient Red Dragon",
    ),
    (
        (
            "Monsters A–Z",
            "Red Dragons",
            "Ancient Red Dragon",
        ),
        "_Gargantuan Dragon (Chromatic), Chaotic Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Red Dragons",
            "Ancient Red Dragon",
        ),
        "**AC** 22 **Initiative** +14 (24) <br>\n**HP** 507 (26d20 + 234) <br>\n**Speed** 40 ft., Climb 40 ft., Fly 80 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Red Dragons",
            "Ancient Red Dragon",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>30</td>\n      <td>+10</td>\n      <td>+10</td>\n      <td><strong>DEX</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+7</td>\n      <td><strong>CON</strong></td>\n      <td>29</td>\n      <td>+9</td>\n      <td>+9</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+4</td>\n      <td><strong>WIS</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+9</td>\n      <td><strong>CHA</strong></td>\n      <td>27</td>\n      <td>+8</td>\n      <td>+8</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Red Dragons",
            "Ancient Red Dragon",
        ),
        "**Skills** Perception +16, Stealth +7<br>\n**Immunities** Fire<br>\n**Senses** Blindsight 60 ft., Darkvision 120 ft.; Passive Perception 26<br>\n**Languages** Common, Draconic<br>\n**CR** 24 (XP 62,000, or 75,000 in lair; PB +7)",
    ),
    (
        (
            "Monsters A–Z",
            "Red Dragons",
            "Ancient Red Dragon",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Red Dragons",
            "Ancient Red Dragon",
            "Traits",
        ),
        "**_Legendary Resistance (4/Day, or 5/Day in Lair)._** If the dragon fails a saving throw, it can choose to succeed instead.",
    ),
    (
        (
            "Monsters A–Z",
            "Red Dragons",
            "Ancient Red Dragon",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Red Dragons",
            "Ancient Red Dragon",
            "Actions",
        ),
        "**_Multiattack._** The dragon makes three Rend attacks. It can replace one attack with a use of Spellcasting to cast _Scorching Ray_ (level 3 version).",
    ),
    (
        (
            "Monsters A–Z",
            "Red Dragons",
            "Ancient Red Dragon",
            "Actions",
        ),
        "**_Rend._** _Melee Attack Roll:_ +17, reach 15 ft. _Hit:_ 19 (2d8 + 10) Slashing damage plus 10 (3d6) Fire damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Red Dragons",
            "Ancient Red Dragon",
            "Actions",
        ),
        "**_Fire Breath (Recharge 5–6)._** _Dexterity Saving Throw:_ DC 24, each creature in a 90-foot Cone. _Failure:_ 91 (26d6) Fire damage. _Success:_ Half damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Red Dragons",
            "Ancient Red Dragon",
            "Actions",
        ),
        "**_Spellcasting._** The dragon casts one of the following spells, requiring no Material components and using Charisma as the spellcasting ability (spell save DC 23, +15 to hit with spell attacks): <br>\n&emsp;**At Will:** _Command_ (level 2 version), _Detect Magic_, _Scorching Ray_ (level 3 version) <br>\n&emsp;**1/Day Each:** _Fireball_ (level 6 version), _Scrying_",
    ),
    (
        (
            "Monsters A–Z",
            "Red Dragons",
            "Ancient Red Dragon",
            "Legendary Actions",
        ),
        "#### Legendary Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Red Dragons",
            "Ancient Red Dragon",
            "Legendary Actions",
        ),
        "_Legendary Action Uses: 3 (4 in Lair). Immediately after another creature's turn, the dragon can expend a use to take one of the following actions. The dragon regains all expended uses at the start of each of its turns._",
    ),
    (
        (
            "Monsters A–Z",
            "Red Dragons",
            "Ancient Red Dragon",
            "Legendary Actions",
        ),
        "**_Commanding Presence._** The dragon uses Spellcasting to cast _Command_ (level 2 version). The dragon can't take this action again until the start of its next turn.",
    ),
    (
        (
            "Monsters A–Z",
            "Red Dragons",
            "Ancient Red Dragon",
            "Legendary Actions",
        ),
        "**_Fiery Rays._** The dragon uses Spellcasting to cast _Scorching Ray_ (level 3 version). The dragon can't take this action again until the start of its next turn.",
    ),
    (
        (
            "Monsters A–Z",
            "Red Dragons",
            "Ancient Red Dragon",
            "Legendary Actions",
        ),
        "**_Pounce._** The dragon moves up to half its Speed, and it makes one Rend attack.",
    ),
    (
        (
            "Monsters A–Z",
            "Remorhaz",
        ),
        "## Remorhaz",
    ),
    (
        (
            "Monsters A–Z",
            "Remorhaz",
            "Remorhaz",
        ),
        "### Remorhaz",
    ),
    (
        (
            "Monsters A–Z",
            "Remorhaz",
            "Remorhaz",
        ),
        "_Huge Monstrosity, Unaligned_",
    ),
    (
        (
            "Monsters A–Z",
            "Remorhaz",
            "Remorhaz",
        ),
        "**AC** 17 **Initiative** +5 (15) <br>\n**HP** 195 (17d12 + 85) <br>\n**Speed** 40 ft., Burrow 30 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Remorhaz",
            "Remorhaz",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>24</td>\n      <td>+7</td>\n      <td>+7</td>\n      <td><strong>DEX</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CON</strong></td>\n      <td>21</td>\n      <td>+5</td>\n      <td>+5</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>4</td>\n      <td>−3</td>\n      <td>−3</td>\n      <td><strong>WIS</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CHA</strong></td>\n      <td>5</td>\n      <td>−3</td>\n      <td>−3</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Remorhaz",
            "Remorhaz",
        ),
        "**Immunities** Cold, Fire<br>\n**Senses** Darkvision 60 ft., Tremorsense 60 ft.; Passive Perception 10<br>\n**Languages** None<br>\n**CR** 11 (XP 7,200; PB +4)",
    ),
    (
        (
            "Monsters A–Z",
            "Remorhaz",
            "Remorhaz",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Remorhaz",
            "Remorhaz",
            "Traits",
        ),
        "**_Heat Aura._** At the end of each of the remorhaz's turns, each creature in a 5-foot Emanation originating from the remorhaz takes 16 (3d10) Fire damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Remorhaz",
            "Remorhaz",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Remorhaz",
            "Remorhaz",
            "Actions",
        ),
        "**_Bite._** _Melee Attack Roll:_ +11, reach 10 ft. _Hit:_ 18 (2d10 + 7) Piercing damage plus 14 (4d6) Fire damage. If the target is a Large or smaller creature, it has the Grappled condition (escape DC 17), and it has the Restrained condition until the grapple ends.",
    ),
    (
        (
            "Monsters A–Z",
            "Remorhaz",
            "Remorhaz",
            "Bonus Actions",
        ),
        "#### Bonus Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Remorhaz",
            "Remorhaz",
            "Bonus Actions",
        ),
        "**_Swallow._** _Strength Saving Throw:_ DC 19, one Large or smaller creature Grappled by the remorhaz (it can have up to two creatures swallowed at a time). _Failure:_ The target is swallowed by the remorhaz, and the Grappled condition ends. A swallowed creature has the Blinded and Restrained conditions, it has Total Cover against attacks and other effects outside the remorhaz, and it takes 10 (3d6) Acid damage plus 10 (3d6) Fire damage at the start of each of the remorhaz's turns. <br>\n&emsp;If the remorhaz takes 30 damage or more on a single turn from a creature inside it, the remorhaz must succeed on a DC 15 Constitution saving throw at the end of that turn or regurgitate all swallowed creatures, each of which falls in a space within 5 feet of the remorhaz and has the Prone condition. If the remorhaz dies, any swallowed creature no longer has the Restrained condition and can escape from the corpse by using 15 feet of movement, exiting Prone.",
    ),
    (
        (
            "Monsters A–Z",
            "Roc",
        ),
        "## Roc",
    ),
    (
        (
            "Monsters A–Z",
            "Roc",
            "Roc",
        ),
        "### Roc",
    ),
    (
        (
            "Monsters A–Z",
            "Roc",
            "Roc",
        ),
        "_Gargantuan Monstrosity, Unaligned_",
    ),
    (
        (
            "Monsters A–Z",
            "Roc",
            "Roc",
        ),
        "**AC** 15 **Initiative** +8 (18) <br>\n**HP** 248 (16d20 + 80) <br>\n**Speed** 20 ft., Fly 120 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Roc",
            "Roc",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>28</td>\n      <td>+9</td>\n      <td>+9</td>\n      <td><strong>DEX</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+4</td>\n      <td><strong>CON</strong></td>\n      <td>20</td>\n      <td>+5</td>\n      <td>+5</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>3</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>WIS</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+4</td>\n      <td><strong>CHA</strong></td>\n      <td>9</td>\n      <td>−1</td>\n      <td>−1</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Roc",
            "Roc",
        ),
        "**Skills** Perception +8<br>\n**Senses** Passive Perception 18<br>\n**Languages** None<br>\n**CR** 11 (XP 7,200; PB +4)",
    ),
    (
        (
            "Monsters A–Z",
            "Roc",
            "Roc",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Roc",
            "Roc",
            "Actions",
        ),
        "**_Multiattack._** The roc makes two Beak attacks. It can replace one attack with a Talons attack.",
    ),
    (
        (
            "Monsters A–Z",
            "Roc",
            "Roc",
            "Actions",
        ),
        "**_Beak._** _Melee Attack Roll:_ +13, reach 10 ft. _Hit:_ 28 (3d12 + 9) Piercing damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Roc",
            "Roc",
            "Actions",
        ),
        "**_Talons._** _Melee Attack Roll:_ +13, reach 5 ft. _Hit:_ 23 (4d6 + 9) Slashing damage. If the target is a Huge or smaller creature, it has the Grappled condition (escape DC 19) from both talons, and it has the Restrained condition until the grapple ends.",
    ),
    (
        (
            "Monsters A–Z",
            "Roc",
            "Roc",
            "Bonus Actions",
        ),
        "#### Bonus Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Roc",
            "Roc",
            "Bonus Actions",
        ),
        "**_Swoop (Recharge 5–6)._** If the roc has a creature Grappled, the roc flies up to half its Fly Speed without provoking Opportunity Attacks and drops that creature.",
    ),
    (
        (
            "Monsters A–Z",
            "Roper",
        ),
        "## Roper",
    ),
    (
        (
            "Monsters A–Z",
            "Roper",
            "Roper",
        ),
        "### Roper",
    ),
    (
        (
            "Monsters A–Z",
            "Roper",
            "Roper",
        ),
        "_Large Aberration, Neutral Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Roper",
            "Roper",
        ),
        "**AC** 20 **Initiative** +5 (15) <br>\n**HP** 93 (11d10 + 33) <br>\n**Speed** 10 ft., Climb 20 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Roper",
            "Roper",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+4</td>\n      <td><strong>DEX</strong></td>\n      <td>8</td>\n      <td>−1</td>\n      <td>−1</td>\n      <td><strong>CON</strong></td>\n      <td>17</td>\n      <td>+3</td>\n      <td>+3</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>7</td>\n      <td>−2</td>\n      <td>−2</td>\n      <td><strong>WIS</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>CHA</strong></td>\n      <td>6</td>\n      <td>−2</td>\n      <td>−2</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Roper",
            "Roper",
        ),
        "**Skills** Perception +6, Stealth +5<br>\n**Senses** Darkvision 60 ft.; Passive Perception 16<br>\n**Languages** None<br>\n**CR** 5 (XP 1,800; PB +3)",
    ),
    (
        (
            "Monsters A–Z",
            "Roper",
            "Roper",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Roper",
            "Roper",
            "Traits",
        ),
        "**_Spider Climb._** The roper can climb difficult surfaces, including along ceilings, without needing to make an ability check.",
    ),
    (
        (
            "Monsters A–Z",
            "Roper",
            "Roper",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Roper",
            "Roper",
            "Actions",
        ),
        "**_Multiattack._** The roper makes two Tentacle attacks, uses Reel, and makes two Bite attacks.",
    ),
    (
        (
            "Monsters A–Z",
            "Roper",
            "Roper",
            "Actions",
        ),
        "**_Bite._** _Melee Attack Roll:_ +7, reach 5 ft. _Hit:_ 17 (3d8 + 4) Piercing damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Roper",
            "Roper",
            "Actions",
        ),
        "**_Tentacle._** _Melee Attack Roll:_ +7, reach 60 ft. _Hit:_ The target has the Grappled condition (escape DC 14) from one of six tentacles, and the target has the Poisoned condition until the grapple ends. <br>\n&emsp;The tentacle can be damaged, freeing a creature it has Grappled when destroyed (AC 20, HP 10, Immunity to Poison and Psychic damage). Damaging the tentacle deals no damage to the roper, and a destroyed tentacle regrows at the start of the roper's next turn.",
    ),
    (
        (
            "Monsters A–Z",
            "Roper",
            "Roper",
            "Actions",
        ),
        "**_Reel._** The roper pulls each creature Grappled by it up to 30 feet straight toward it.",
    ),
    (
        (
            "Monsters A–Z",
            "Rust Monster",
        ),
        "## Rust Monster",
    ),
    (
        (
            "Monsters A–Z",
            "Rust Monster",
            "Rust Monster",
        ),
        "### Rust Monster",
    ),
    (
        (
            "Monsters A–Z",
            "Rust Monster",
            "Rust Monster",
        ),
        "_Medium Monstrosity, Unaligned_",
    ),
    (
        (
            "Monsters A–Z",
            "Rust Monster",
            "Rust Monster",
        ),
        "**AC** 14 **Initiative** +1 (11) <br>\n**HP** 33 (6d8 + 6) <br>\n**Speed** 40 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Rust Monster",
            "Rust Monster",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>DEX</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CON</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>2</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>WIS</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CHA</strong></td>\n      <td>6</td>\n      <td>−2</td>\n      <td>−2</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Rust Monster",
            "Rust Monster",
        ),
        "**Senses** Darkvision 60 ft.; Passive Perception 11<br>\n**Languages** None<br>\n**CR** 1/2 (XP 100; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Rust Monster",
            "Rust Monster",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Rust Monster",
            "Rust Monster",
            "Traits",
        ),
        "**_Iron Scent._** The rust monster can pinpoint the location of ferrous metal within 30 feet of itself.",
    ),
    (
        (
            "Monsters A–Z",
            "Rust Monster",
            "Rust Monster",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Rust Monster",
            "Rust Monster",
            "Actions",
        ),
        "**_Multiattack._** The rust monster makes one Bite attack and uses Antennae twice.",
    ),
    (
        (
            "Monsters A–Z",
            "Rust Monster",
            "Rust Monster",
            "Actions",
        ),
        "**_Bite._** _Melee Attack Roll:_ +3, reach 5 ft. _Hit:_ 5 (1d8 + 1) Piercing damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Rust Monster",
            "Rust Monster",
            "Actions",
        ),
        "**_Antennae._** The rust monster targets one nonmagical metal object—armor or a weapon—worn or carried by a creature within 5 feet of itself. _Dexterity Saving Throw:_ DC 11, the creature with the object. _Failure:_ The object takes a −1 penalty to the AC it offers (armor) or to its attack rolls (weapon). Armor is destroyed if the penalty reduces its AC to 10, and a weapon is destroyed if its penalty reaches −5. The penalty can be removed by casting the _Mending_ spell on the armor or weapon.",
    ),
    (
        (
            "Monsters A–Z",
            "Rust Monster",
            "Rust Monster",
            "Actions",
        ),
        "**_Destroy Metal._** The rust monster touches a nonmagical metal object within 5 feet of itself that isn't being worn or carried. The touch destroys a 1-foot Cube of the object.",
    ),
    (
        (
            "Monsters A–Z",
            "Rust Monster",
            "Rust Monster",
            "Reactions",
        ),
        "#### Reactions",
    ),
    (
        (
            "Monsters A–Z",
            "Rust Monster",
            "Rust Monster",
            "Reactions",
        ),
        "**_Reflexive Antennae._** _Trigger:_ An attack roll hits the rust monster. _Response:_ The rust monster uses Antennae.",
    ),
    (
        (
            "Monsters A–Z",
            "Sahuagin",
        ),
        "## Sahuagin",
    ),
    (
        (
            "Monsters A–Z",
            "Sahuagin",
            "Sahuagin Warrior",
        ),
        "### Sahuagin Warrior",
    ),
    (
        (
            "Monsters A–Z",
            "Sahuagin",
            "Sahuagin Warrior",
        ),
        "_Medium Fiend, Lawful Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Sahuagin",
            "Sahuagin Warrior",
        ),
        "**AC** 12 **Initiative** +0 (10) <br>\n**HP** 22 (4d8 + 4) <br>\n**Speed** 30 ft., Swim 40 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Sahuagin",
            "Sahuagin Warrior",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>DEX</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CON</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>WIS</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CHA</strong></td>\n      <td>9</td>\n      <td>−1</td>\n      <td>−1</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Sahuagin",
            "Sahuagin Warrior",
        ),
        "**Skills** Perception +5<br>\n**Resistances** Acid, Cold<br>\n**Senses** Darkvision 120 ft.; Passive Perception 15<br>\n**Languages** Sahuagin<br>\n**CR** 1/2 (XP 100; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Sahuagin",
            "Sahuagin Warrior",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Sahuagin",
            "Sahuagin Warrior",
            "Traits",
        ),
        "**_Blood Frenzy._** The sahuagin has Advantage on attack rolls against any creature that doesn't have all its Hit Points.",
    ),
    (
        (
            "Monsters A–Z",
            "Sahuagin",
            "Sahuagin Warrior",
            "Traits",
        ),
        "**_Limited Amphibiousness._** The sahuagin can breathe air and water, but it must be submerged at least once every 4 hours to avoid suffocating outside water.",
    ),
    (
        (
            "Monsters A–Z",
            "Sahuagin",
            "Sahuagin Warrior",
            "Traits",
        ),
        "**_Shark Telepathy._** The sahuagin can magically control sharks within 120 feet of itself, using a special telepathy.",
    ),
    (
        (
            "Monsters A–Z",
            "Sahuagin",
            "Sahuagin Warrior",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Sahuagin",
            "Sahuagin Warrior",
            "Actions",
        ),
        "**_Multiattack._** The sahuagin makes two Claw attacks.",
    ),
    (
        (
            "Monsters A–Z",
            "Sahuagin",
            "Sahuagin Warrior",
            "Actions",
        ),
        "**_Claw._** _Melee Attack Roll:_ +3, reach 5 ft. _Hit:_ 4 (1d6 + 1) Slashing damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Sahuagin",
            "Sahuagin Warrior",
            "Bonus Actions",
        ),
        "#### Bonus Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Sahuagin",
            "Sahuagin Warrior",
            "Bonus Actions",
        ),
        "**_Aquatic Charge._** The sahuagin swims up to its Swim Speed straight toward an enemy it can see.",
    ),
    (
        (
            "Monsters A–Z",
            "Salamander",
        ),
        "## Salamander",
    ),
    (
        (
            "Monsters A–Z",
            "Salamander",
            "Salamander",
        ),
        "### Salamander",
    ),
    (
        (
            "Monsters A–Z",
            "Salamander",
            "Salamander",
        ),
        "_Large Elemental, Neutral Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Salamander",
            "Salamander",
        ),
        "**AC** 15 **Initiative** +2 (12) <br>\n**HP** 90 (12d10 + 24) <br>\n**Speed** 30 ft., Climb 30 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Salamander",
            "Salamander",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+4</td>\n      <td><strong>DEX</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CON</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>WIS</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CHA</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Salamander",
            "Salamander",
        ),
        "**Vulnerabilities** Cold<br>\n**Immunities** Fire<br>\n**Senses** Darkvision 60 ft.; Passive Perception 10<br>\n**Languages** Primordial (Ignan)<br>\n**CR** 5 (XP 1,800; PB +3)",
    ),
    (
        (
            "Monsters A–Z",
            "Salamander",
            "Salamander",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Salamander",
            "Salamander",
            "Traits",
        ),
        "**_Fire Aura._** At the end of each of the salamander's turns, each creature of the salamander's choice in a 5-foot Emanation originating from the salamander takes 7 (2d6) Fire damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Salamander",
            "Salamander",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Salamander",
            "Salamander",
            "Actions",
        ),
        "**_Multiattack._** The salamander makes two Flame Spear attacks. It can replace one attack with a use of Constrict.",
    ),
    (
        (
            "Monsters A–Z",
            "Salamander",
            "Salamander",
            "Actions",
        ),
        "**_Flame Spear._** _Melee or Ranged Attack Roll:_ +7, reach 5 ft. or range 20/60 ft. _Hit:_ 13 (2d8 + 4) Piercing damage plus 7 (2d6) Fire damage. _Hit or Miss:_ The spear magically returns to the salamander's hand immediately after a ranged attack.",
    ),
    (
        (
            "Monsters A–Z",
            "Salamander",
            "Salamander",
            "Actions",
        ),
        "**_Constrict._** _Strength Saving Throw:_ DC 15, one Large or smaller creature the salamander can see within 10 feet. _Failure:_ 11 (2d6 + 4) Bludgeoning damage plus 7 (2d6) Fire damage. The target has the Grappled condition (escape DC 14), and it has the Restrained condition until the grapple ends.",
    ),
    (
        (
            "Monsters A–Z",
            "Satyr",
        ),
        "## Satyr",
    ),
    (
        (
            "Monsters A–Z",
            "Satyr",
            "Satyr",
        ),
        "### Satyr",
    ),
    (
        (
            "Monsters A–Z",
            "Satyr",
            "Satyr",
        ),
        "_Medium Fey, Chaotic Neutral_",
    ),
    (
        (
            "Monsters A–Z",
            "Satyr",
            "Satyr",
        ),
        "**AC** 13 **Initiative** +3 (13) <br>\n**HP** 31 (7d8) <br>\n**Speed** 40 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Satyr",
            "Satyr",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>DEX</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>CON</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>WIS</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CHA</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Satyr",
            "Satyr",
        ),
        "**Skills** Perception +2, Performance +6, Stealth +5<br>\n**Senses** Passive Perception 12<br>\n**Languages** Common, Elvish, Sylvan<br>\n**CR** 1/2 (XP 100; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Satyr",
            "Satyr",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Satyr",
            "Satyr",
            "Traits",
        ),
        "**_Magic Resistance._** The satyr has Advantage on saving throws against spells and other magical effects.",
    ),
    (
        (
            "Monsters A–Z",
            "Satyr",
            "Satyr",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Satyr",
            "Satyr",
            "Actions",
        ),
        "**_Hooves._** _Melee Attack Roll:_ +5, reach 5 ft. _Hit:_ 5 (1d4 + 3) Bludgeoning damage. If the target is a Medium or smaller creature, the satyr pushes the target up to 10 feet straight away from itself.",
    ),
    (
        (
            "Monsters A–Z",
            "Satyr",
            "Satyr",
            "Actions",
        ),
        "**_Mockery._** _Wisdom Saving Throw:_ DC 12, one creature the satyr can see within 90 feet. _Failure:_ 5 (1d6 + 2) Psychic damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Scout",
        ),
        "## Scout",
    ),
    (
        (
            "Monsters A–Z",
            "Scout",
            "Scout",
        ),
        "### Scout",
    ),
    (
        (
            "Monsters A–Z",
            "Scout",
            "Scout",
        ),
        "_Medium or Small Humanoid, Neutral_",
    ),
    (
        (
            "Monsters A–Z",
            "Scout",
            "Scout",
        ),
        "**AC** 13 **Initiative** +2 (12) <br>\n**HP** 16 (3d8 + 3) <br>\n**Speed** 30 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Scout",
            "Scout",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>DEX</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CON</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>WIS</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CHA</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Scout",
            "Scout",
        ),
        "**Skills** Nature +4, Perception +5, Stealth +6, Survival +5<br>\n**Gear** Leather Armor, Longbow, Shortsword<br>\n**Senses** Passive Perception 15<br>\n**Languages** Common plus one other language<br>\n**CR** 1/2 (XP 100; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Scout",
            "Scout",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Scout",
            "Scout",
            "Actions",
        ),
        "**_Multiattack._** The scout makes two attacks, using Shortsword and Longbow in any combination.",
    ),
    (
        (
            "Monsters A–Z",
            "Scout",
            "Scout",
            "Actions",
        ),
        "**_Shortsword._** _Melee Attack Roll:_ +4, reach 5 ft. _Hit:_ 5 (1d6 + 2) Piercing damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Scout",
            "Scout",
            "Actions",
        ),
        "**_Longbow._** _Ranged Attack Roll:_ +4, range 150/600 ft. _Hit:_ 6 (1d8 + 2) Piercing damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Sea Hag",
        ),
        "## Sea Hag",
    ),
    (
        (
            "Monsters A–Z",
            "Sea Hag",
            "Sea Hag",
        ),
        "### Sea Hag",
    ),
    (
        (
            "Monsters A–Z",
            "Sea Hag",
            "Sea Hag",
        ),
        "_Medium Fey, Chaotic Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Sea Hag",
            "Sea Hag",
        ),
        "**AC** 14 **Initiative** +1 (11) <br>\n**HP** 52 (7d8 + 21) <br>\n**Speed** 30 ft., Swim 40 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Sea Hag",
            "Sea Hag",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>DEX</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CON</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>WIS</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CHA</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Sea Hag",
            "Sea Hag",
        ),
        "**Senses** Darkvision 60 ft.; Passive Perception 11<br>\n**Languages** Common, Giant, Primordial (Aquan)<br>\n**CR** 2 (XP 450; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Sea Hag",
            "Sea Hag",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Sea Hag",
            "Sea Hag",
            "Traits",
        ),
        "**_Amphibious._** The hag can breathe air and water.",
    ),
    (
        (
            "Monsters A–Z",
            "Sea Hag",
            "Sea Hag",
            "Traits",
        ),
        "**_Coven Magic._** While within 30 feet of at least two hag allies, the hag can cast one of the following spells, requiring no Material components, using the spell's normal casting time, and using Intelligence as the spellcasting ability (spell save DC 11): _Augury, Find Familiar, Identify, Locate Object, Scrying,_ or _Unseen Servant_. The hag must finish a Long Rest before using this trait to cast that spell again.",
    ),
    (
        (
            "Monsters A–Z",
            "Sea Hag",
            "Sea Hag",
            "Traits",
        ),
        "**_Vile Appearance._** _Wisdom Saving Throw:_ DC 11, any Beast or Humanoid that starts its turn within 30 feet of the hag and can see the hag's true form. _Failure:_ The target has the Frightened condition until the start of its next turn. _Success:_ The target is immune to this hag's Vile Appearance for 24 hours.",
    ),
    (
        (
            "Monsters A–Z",
            "Sea Hag",
            "Sea Hag",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Sea Hag",
            "Sea Hag",
            "Actions",
        ),
        "**_Claw._** _Melee Attack Roll:_ +5, reach 5 ft. _Hit:_ 10 (2d6 + 3) Slashing damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Sea Hag",
            "Sea Hag",
            "Actions",
        ),
        "**_Death Glare (Recharge 5–6)._** _Wisdom Saving Throw:_ DC 11, one Frightened creature the hag can see within 30 feet. _Failure:_ If the target has 20 Hit Points or fewer, it drops to 0 Hit Points. Otherwise, the target takes 13 (3d8) Psychic damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Sea Hag",
            "Sea Hag",
            "Actions",
        ),
        "**_Illusory Appearance._** The hag casts _Disguise Self_, using Constitution as the spellcasting ability (spell save DC 13). The spell's duration is 24 hours.",
    ),
    (
        (
            "Monsters A–Z",
            "Shadow",
        ),
        "## Shadow",
    ),
    (
        (
            "Monsters A–Z",
            "Shadow",
            "Shadow",
        ),
        "### Shadow",
    ),
    (
        (
            "Monsters A–Z",
            "Shadow",
            "Shadow",
        ),
        "_Medium Undead, Chaotic Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Shadow",
            "Shadow",
        ),
        "**AC** 12 **Initiative** +2 (12) <br>\n**HP** 27 (5d8 + 5) <br>\n**Speed** 40 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Shadow",
            "Shadow",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>6</td>\n      <td>−2</td>\n      <td>−2</td>\n      <td><strong>DEX</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CON</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>6</td>\n      <td>−2</td>\n      <td>−2</td>\n      <td><strong>WIS</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CHA</strong></td>\n      <td>8</td>\n      <td>−1</td>\n      <td>−1</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Shadow",
            "Shadow",
        ),
        "**Skills** Stealth +6<br>\n**Vulnerabilities** Radiant<br>\n**Resistances** Acid, Cold, Fire, Lightning, Thunder<br>\n**Immunities** Necrotic, Poison; Exhaustion, Frightened, Grappled, Paralyzed, Petrified, Poisoned, Prone, Restrained, Unconscious<br>\n**Senses** Darkvision 60 ft.; Passive Perception 10<br>\n**Languages** None<br>\n**CR** 1/2 (XP 100; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Shadow",
            "Shadow",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Shadow",
            "Shadow",
            "Traits",
        ),
        "**_Amorphous._** The shadow can move through a space as narrow as 1 inch without expending extra movement to do so.",
    ),
    (
        (
            "Monsters A–Z",
            "Shadow",
            "Shadow",
            "Traits",
        ),
        "**_Sunlight Weakness._** While in sunlight, the shadow has Disadvantage on D20 Tests.",
    ),
    (
        (
            "Monsters A–Z",
            "Shadow",
            "Shadow",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Shadow",
            "Shadow",
            "Actions",
        ),
        "**_Draining Swipe._** _Melee Attack Roll:_ +4, reach 5 ft. _Hit:_ 5 (1d6 + 2) Necrotic damage, and the target's Strength score decreases by 1d4. The target dies if this reduces that score to 0. If a Humanoid is slain by this attack, a **Shadow** rises from the corpse 1d4 hours later.",
    ),
    (
        (
            "Monsters A–Z",
            "Shadow",
            "Shadow",
            "Bonus Actions",
        ),
        "#### Bonus Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Shadow",
            "Shadow",
            "Bonus Actions",
        ),
        "**_Shadow Stealth._** While in Dim Light or Darkness, the shadow takes the Hide action.",
    ),
    (
        (
            "Monsters A–Z",
            "Shambling Mound",
        ),
        "## Shambling Mound",
    ),
    (
        (
            "Monsters A–Z",
            "Shambling Mound",
            "Shambling Mound",
        ),
        "### Shambling Mound",
    ),
    (
        (
            "Monsters A–Z",
            "Shambling Mound",
            "Shambling Mound",
        ),
        "_Large Plant, Unaligned_",
    ),
    (
        (
            "Monsters A–Z",
            "Shambling Mound",
            "Shambling Mound",
        ),
        "**AC** 15 **Initiative** −1 (9) <br>\n**HP** 110 (13d10 + 39) <br>\n**Speed** 30 ft., Swim 20 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Shambling Mound",
            "Shambling Mound",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+4</td>\n      <td><strong>DEX</strong></td>\n      <td>8</td>\n      <td>−1</td>\n      <td>−1</td>\n      <td><strong>CON</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>5</td>\n      <td>−3</td>\n      <td>−3</td>\n      <td><strong>WIS</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CHA</strong></td>\n      <td>5</td>\n      <td>−3</td>\n      <td>−3</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Shambling Mound",
            "Shambling Mound",
        ),
        "**Skills** Stealth +3<br>\n**Resistances** Cold, Fire<br>\n**Immunities** Lightning; Deafened, Exhaustion<br>\n**Senses** Blindsight 60 ft.; Passive Perception 10<br>\n**Languages** None<br>\n**CR** 5 (XP 1,800; PB +3)",
    ),
    (
        (
            "Monsters A–Z",
            "Shambling Mound",
            "Shambling Mound",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Shambling Mound",
            "Shambling Mound",
            "Traits",
        ),
        "**_Lightning Absorption._** Whenever the shambling mound is subjected to Lightning damage, it regains a number of Hit Points equal to the Lightning damage dealt.",
    ),
    (
        (
            "Monsters A–Z",
            "Shambling Mound",
            "Shambling Mound",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Shambling Mound",
            "Shambling Mound",
            "Actions",
        ),
        "**_Multiattack._** The shambling mound makes three Charged Tendril attacks. It can replace one attack with a use of Engulf.",
    ),
    (
        (
            "Monsters A–Z",
            "Shambling Mound",
            "Shambling Mound",
            "Actions",
        ),
        "**_Charged Tendril._** _Melee Attack Roll:_ +7, reach 10 ft. _Hit:_ 7 (1d6 + 4) Bludgeoning damage plus 5 (2d4) Lightning damage. If the target is a Medium or smaller creature, the shambling mound pulls the target 5 feet straight toward itself.",
    ),
    (
        (
            "Monsters A–Z",
            "Shambling Mound",
            "Shambling Mound",
            "Actions",
        ),
        "**_Engulf._** _Strength Saving Throw:_ DC 15, one Medium or smaller creature within 5 feet. _Failure:_ The target is pulled into the shambling mound's space and has the Grappled condition (escape DC 14). Until the grapple ends, the target has the Blinded and Restrained conditions, and it takes 10 (3d6) Lightning damage at the start of each of its turns. When the shambling mound moves, the Grappled target moves with it, costing it no extra movement. The shambling mound can have only one creature Grappled by this action at a time.",
    ),
    (
        (
            "Monsters A–Z",
            "Shield Guardian",
        ),
        "## Shield Guardian",
    ),
    (
        (
            "Monsters A–Z",
            "Shield Guardian",
            "Shield Guardian",
        ),
        "### Shield Guardian",
    ),
    (
        (
            "Monsters A–Z",
            "Shield Guardian",
            "Shield Guardian",
        ),
        "_Large Construct, Unaligned_",
    ),
    (
        (
            "Monsters A–Z",
            "Shield Guardian",
            "Shield Guardian",
        ),
        "**AC** 17 **Initiative** −1 (9) <br>\n**HP** 142 (15d10 + 60) <br>\n**Speed** 30 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Shield Guardian",
            "Shield Guardian",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+4</td>\n      <td><strong>DEX</strong></td>\n      <td>8</td>\n      <td>−1</td>\n      <td>−1</td>\n      <td><strong>CON</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+4</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>7</td>\n      <td>−2</td>\n      <td>−2</td>\n      <td><strong>WIS</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CHA</strong></td>\n      <td>3</td>\n      <td>−4</td>\n      <td>−4</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Shield Guardian",
            "Shield Guardian",
        ),
        "**Immunities** Poison; Charmed, Exhaustion, Frightened, Paralyzed, Petrified, Poisoned<br>\n**Senses** Blindsight 10 ft., Darkvision 60 ft.; Passive Perception 10<br>\n**Languages** Understands commands given in any language but can't speak<br>\n**CR** 7 (XP 2,900; PB +3)",
    ),
    (
        (
            "Monsters A–Z",
            "Shield Guardian",
            "Shield Guardian",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Shield Guardian",
            "Shield Guardian",
            "Traits",
        ),
        "**_Bound._** The guardian is magically bound to an amulet. While the guardian and its amulet are on the same plane of existence, the amulet's wearer can telepathically call the guardian to travel to it, and the guardian knows the distance and direction to the amulet. If the guardian is within 60 feet of the amulet's wearer, half of any damage the wearer takes (round up) is transferred to the guardian.",
    ),
    (
        (
            "Monsters A–Z",
            "Shield Guardian",
            "Shield Guardian",
            "Traits",
        ),
        "**_Regeneration._** The guardian regains 10 Hit Points at the start of each of its turns if it has at least 1 Hit Point.",
    ),
    (
        (
            "Monsters A–Z",
            "Shield Guardian",
            "Shield Guardian",
            "Traits",
        ),
        "**_Spell Storing._** A spellcaster who wears the guardian's amulet can cause the guardian to store one spell of level 4 or lower. To do so, the wearer must cast the spell on the guardian while within 5 feet of it. The spell has no effect but is stored within the guardian. Any previously stored spell is lost when a new spell is stored. The guardian can cast the spell stored with any parameters set by the original caster, requiring no spell components and using the caster's spellcasting ability. The stored spell is then lost.",
    ),
    (
        (
            "Monsters A–Z",
            "Shield Guardian",
            "Shield Guardian",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Shield Guardian",
            "Shield Guardian",
            "Actions",
        ),
        "**_Multiattack._** The guardian makes two Fist attacks.",
    ),
    (
        (
            "Monsters A–Z",
            "Shield Guardian",
            "Shield Guardian",
            "Actions",
        ),
        "**_Fist._** _Melee Attack Roll:_ +7, reach 10 ft. _Hit:_ 11 (2d6 + 4) Bludgeoning damage plus 7 (2d6) Force damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Shield Guardian",
            "Shield Guardian",
            "Reactions",
        ),
        "#### Reactions",
    ),
    (
        (
            "Monsters A–Z",
            "Shield Guardian",
            "Shield Guardian",
            "Reactions",
        ),
        "**_Protection._** _Trigger:_ An attack roll hits the wearer of the guardian's amulet while the wearer is within 5 feet of the guardian. _Response:_ The wearer gains a +5 bonus to AC, including against the triggering attack and possibly causing it to miss, until the start of the guardian's next turn.",
    ),
    (
        (
            "Monsters A–Z",
            "Silver Dragons",
        ),
        "## Silver Dragons",
    ),
    (
        (
            "Monsters A–Z",
            "Silver Dragons",
            "Silver Dragon Wyrmling",
        ),
        "### Silver Dragon Wyrmling",
    ),
    (
        (
            "Monsters A–Z",
            "Silver Dragons",
            "Silver Dragon Wyrmling",
        ),
        "_Medium Dragon (Metallic), Lawful Good_",
    ),
    (
        (
            "Monsters A–Z",
            "Silver Dragons",
            "Silver Dragon Wyrmling",
        ),
        "**AC** 17 **Initiative** +2 (12) <br>\n**HP** 45 (6d8 + 18) <br>  \n**Speed** 30 ft., Fly 60 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Silver Dragons",
            "Silver Dragon Wyrmling",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>19</td>\n      <td>+4</td>\n      <td>+4</td>\n      <td><strong>DEX</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+2</td>\n      <td><strong>CON</strong></td>\n      <td>17</td>\n      <td>+3</td>\n      <td>+3</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>WIS</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+2</td>\n      <td><strong>CHA</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Silver Dragons",
            "Silver Dragon Wyrmling",
        ),
        "**Skills** Perception +4, Stealth +2 <br>\n**Immunities** Cold <br>\n**Senses** Blindsight 10 ft., Darkvision 60 ft.; Passive Perception 14<br>  \n**Languages** Draconic <br>\n**CR** 2 (450 XP; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Silver Dragons",
            "Silver Dragon Wyrmling",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Silver Dragons",
            "Silver Dragon Wyrmling",
            "Actions",
        ),
        "**_Multiattack._** The dragon makes two Rend attacks.",
    ),
    (
        (
            "Monsters A–Z",
            "Silver Dragons",
            "Silver Dragon Wyrmling",
            "Actions",
        ),
        "**_Rend._** _Melee Attack Roll:_ +6, reach 5 ft. _Hit:_ 9 (1d10 + 4) Piercing damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Silver Dragons",
            "Silver Dragon Wyrmling",
            "Actions",
        ),
        "**_Cold Breath (Recharge 5–6)._** _Constitution Saving Throw:_ DC 13, each creature in a 15-foot Cone. _Failure:_ 18 (4d8) Cold damage. _Success:_ Half damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Silver Dragons",
            "Silver Dragon Wyrmling",
            "Actions",
        ),
        "**_Paralyzing Breath._** _Constitution Saving Throw:_ DC 13, each creature in a 15-foot Cone. _First Failure:_ The target has the Incapacitated condition until the end of its next turn, when it repeats the save. _Second Failure:_ The target has the Paralyzed condition, and it repeats the save at the end of each of its turns, ending the effect on itself on a success. After 1 minute, it succeeds automatically.",
    ),
    (
        (
            "Monsters A–Z",
            "Silver Dragons",
            "Young Silver Dragon",
        ),
        "### Young Silver Dragon",
    ),
    (
        (
            "Monsters A–Z",
            "Silver Dragons",
            "Young Silver Dragon",
        ),
        "_Large Dragon (Metallic), Lawful Good_",
    ),
    (
        (
            "Monsters A–Z",
            "Silver Dragons",
            "Young Silver Dragon",
        ),
        "**AC** 18 **Initiative** +4 (14) <br>\n**HP** 168 (16d10 + 80) <br>  \n**Speed** 40 ft., Fly 80 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Silver Dragons",
            "Young Silver Dragon",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>23</td>\n      <td>+6</td>\n      <td>+6</td>\n      <td><strong>DEX</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+4</td>\n      <td><strong>CON</strong></td>\n      <td>21</td>\n      <td>+5</td>\n      <td>+5</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>WIS</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+4</td>\n      <td><strong>CHA</strong></td>\n      <td>19</td>\n      <td>+4</td>\n      <td>+4</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Silver Dragons",
            "Young Silver Dragon",
        ),
        "**Skills** History +6, Perception +8, Stealth +4 <br>\n**Immunities** Cold <br>\n**Senses** Blindsight 30 ft., Darkvision 120 ft.; Passive Perception 18<br>  \n**Languages** Common, Draconic <br>\n**CR** 9 (XP 5,000; PB +4)",
    ),
    (
        (
            "Monsters A–Z",
            "Silver Dragons",
            "Young Silver Dragon",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Silver Dragons",
            "Young Silver Dragon",
            "Actions",
        ),
        "**_Multiattack._** The dragon makes three Rend attacks. It can replace one attack with a use of Paralyzing Breath.",
    ),
    (
        (
            "Monsters A–Z",
            "Silver Dragons",
            "Young Silver Dragon",
            "Actions",
        ),
        "**_Rend._** _Melee Attack Roll:_ +10, reach 10 ft. _Hit:_ 15 (2d8 + 6) Slashing damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Silver Dragons",
            "Young Silver Dragon",
            "Actions",
        ),
        "**_Cold Breath (Recharge 5–6)._** _Constitution Saving Throw:_ DC 17, each creature in a 30-foot Cone. _Failure:_ 49 (11d8) Cold damage. _Success:_ Half damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Silver Dragons",
            "Young Silver Dragon",
            "Actions",
        ),
        "**_Paralyzing Breath._** _Constitution Saving Throw:_ DC 17, each creature in a 30-foot Cone. _First Failure:_ The target has the Incapacitated condition until the end of its next turn, when it repeats the save. _Second Failure:_ The target has the Paralyzed condition, and it repeats the save at the end of each of its turns, ending the effect on itself on a success. After 1 minute, it succeeds automatically.",
    ),
    (
        (
            "Monsters A–Z",
            "Silver Dragons",
            "Adult Silver Dragon",
        ),
        "### Adult Silver Dragon",
    ),
    (
        (
            "Monsters A–Z",
            "Silver Dragons",
            "Adult Silver Dragon",
        ),
        "_Huge Dragon (Metallic), Lawful Good_",
    ),
    (
        (
            "Monsters A–Z",
            "Silver Dragons",
            "Adult Silver Dragon",
        ),
        "**AC** 19 **Initiative** +10 (20) <br>\n**HP** 216 (16d12 + 112) <br>  \n**Speed** 40 ft., Fly 80 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Silver Dragons",
            "Adult Silver Dragon",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>27</td>\n      <td>+8</td>\n      <td>+8</td>\n      <td><strong>DEX</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+5</td>\n      <td><strong>CON</strong></td>\n      <td>25</td>\n      <td>+7</td>\n      <td>+7</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>WIS</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+6</td>\n      <td><strong>CHA</strong></td>\n      <td>22</td>\n      <td>+6</td>\n      <td>+6</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Silver Dragons",
            "Adult Silver Dragon",
        ),
        "**Skills** History +8, Perception +11, Stealth +5 <br>\n**Immunities** Cold <br>\n**Senses** Blindsight 60 ft., Darkvision 120 ft.; Passive Perception 21<br>  \n**Languages** Common, Draconic <br>\n**CR** 16 (XP 15,000, or 18,000 in lair; PB +5)",
    ),
    (
        (
            "Monsters A–Z",
            "Silver Dragons",
            "Adult Silver Dragon",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Silver Dragons",
            "Adult Silver Dragon",
            "Traits",
        ),
        "**_Legendary Resistance (3/Day, or 4/Day in Lair)._** If the dragon fails a saving throw, it can choose to succeed instead.",
    ),
    (
        (
            "Monsters A–Z",
            "Silver Dragons",
            "Adult Silver Dragon",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Silver Dragons",
            "Adult Silver Dragon",
            "Actions",
        ),
        "**_Multiattack._** The dragon makes three Rend attacks. It can replace one attack with a use of (A) Paralyzing Breath or (B) Spellcasting to cast _Ice Knife_.",
    ),
    (
        (
            "Monsters A–Z",
            "Silver Dragons",
            "Adult Silver Dragon",
            "Actions",
        ),
        "**_Rend._** _Melee Attack Roll:_ +13, reach 10 ft. _Hit:_ 17 (2d8 + 8) Slashing damage plus 4 (1d8) Cold damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Silver Dragons",
            "Adult Silver Dragon",
            "Actions",
        ),
        "**_Cold Breath (Recharge 5–6)._** _Constitution Saving Throw:_ DC 20, each creature in a 60-foot Cone. _Failure:_ 54 (12d8) Cold damage. _Success:_ Half damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Silver Dragons",
            "Adult Silver Dragon",
            "Actions",
        ),
        "**_Paralyzing Breath._** _Constitution Saving Throw:_ DC 20, each creature in a 60-foot Cone. _First Failure:_ The target has the Incapacitated condition until the end of its next turn, when it repeats the save. _Second Failure:_ The target has the Paralyzed condition, and it repeats the save at the end of each of its turns, ending the effect on itself on a success. After 1 minute, it succeeds automatically.",
    ),
    (
        (
            "Monsters A–Z",
            "Silver Dragons",
            "Adult Silver Dragon",
            "Actions",
        ),
        "**_Spellcasting._** The dragon casts one of the following spells, requiring no Material components and using Charisma as the spellcasting ability (spell save DC 19, +11 to hit with spell attacks):<br>\n&emsp;**At Will:** _Detect Magic_, _Hold Monster_, _Ice Knife_, _Shapechange_ (Beast or Humanoid form only, no Temporary Hit Points gained from the spell, and no Concentration or Temporary Hit Points required to maintain the spell) <br>\n&emsp;**1/Day Each:** _Ice Storm_ (level 5 version), _Zone of Truth_",
    ),
    (
        (
            "Monsters A–Z",
            "Silver Dragons",
            "Adult Silver Dragon",
            "Legendary Actions",
        ),
        "#### Legendary Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Silver Dragons",
            "Adult Silver Dragon",
            "Legendary Actions",
        ),
        "_Legendary Action Uses: 3 (4 in Lair). Immediately after another creature's turn, the dragon can expend a use to take one of the following actions. The dragon regains all expended uses at the start of each of its turns._",
    ),
    (
        (
            "Monsters A–Z",
            "Silver Dragons",
            "Adult Silver Dragon",
            "Legendary Actions",
        ),
        "**_Chill._** The dragon uses Spellcasting to cast _Hold Monster_. The dragon can't take this action again until the start of its next turn.",
    ),
    (
        (
            "Monsters A–Z",
            "Silver Dragons",
            "Adult Silver Dragon",
            "Legendary Actions",
        ),
        "**_Cold Gale._** _Dexterity Saving Throw:_ DC 19, each creature in a 60-foot-long, 10-foot-wide Line. _Failure:_ 14 (4d6) Cold damage, and the target is pushed up to 30 feet straight away from the dragon. _Success:_ Half damage only. _Failure or Success:_ The dragon can't take this action again until the start of its next turn.",
    ),
    (
        (
            "Monsters A–Z",
            "Silver Dragons",
            "Adult Silver Dragon",
            "Legendary Actions",
        ),
        "**_Pounce._** The dragon moves up to half its Speed, and it makes one Rend attack.",
    ),
    (
        (
            "Monsters A–Z",
            "Silver Dragons",
            "Ancient Silver Dragon",
        ),
        "### Ancient Silver Dragon",
    ),
    (
        (
            "Monsters A–Z",
            "Silver Dragons",
            "Ancient Silver Dragon",
        ),
        "_Gargantuan Dragon (Metallic), Lawful Good_",
    ),
    (
        (
            "Monsters A–Z",
            "Silver Dragons",
            "Ancient Silver Dragon",
        ),
        "**AC** 22 **Initiative** +14 (24) <br>\n**HP** 468 (24d20 + 216) <br>\n**Speed** 40 ft., Fly 80 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Silver Dragons",
            "Ancient Silver Dragon",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>30</td>\n      <td>+10</td>\n      <td>+10</td>\n      <td><strong>DEX</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+7</td>\n      <td><strong>CON</strong></td>\n      <td>29</td>\n      <td>+9</td>\n      <td>+9</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+4</td>\n      <td><strong>WIS</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+9</td>\n      <td><strong>CHA</strong></td>\n      <td>26</td>\n      <td>+8</td>\n      <td>+8</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Silver Dragons",
            "Ancient Silver Dragon",
        ),
        "**Skills** History +11, Perception +16, Stealth +7<br>\n**Immunities** Cold<br>\n**Senses** Blindsight 60 ft., Darkvision 120 ft.; Passive Perception 26<br>\n**Languages** Common, Draconic<br>\n**CR** 23 (XP 50,000, or 62,000 in lair; PB +7)",
    ),
    (
        (
            "Monsters A–Z",
            "Silver Dragons",
            "Ancient Silver Dragon",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Silver Dragons",
            "Ancient Silver Dragon",
            "Traits",
        ),
        "**_Legendary Resistance (4/Day, or 5/Day in Lair)._** If the dragon fails a saving throw, it can choose to succeed instead.",
    ),
    (
        (
            "Monsters A–Z",
            "Silver Dragons",
            "Ancient Silver Dragon",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Silver Dragons",
            "Ancient Silver Dragon",
            "Actions",
        ),
        "**_Multiattack._** The dragon makes three Rend attacks. It can replace one attack with a use of (A) Paralyzing Breath or (B) Spellcasting to cast _Ice Knife_ (level 2 version).",
    ),
    (
        (
            "Monsters A–Z",
            "Silver Dragons",
            "Ancient Silver Dragon",
            "Actions",
        ),
        "**_Rend._** _Melee Attack Roll:_ +17, reach 15 ft. _Hit:_ 19 (2d8 + 10) Slashing damage plus 9 (2d8) Cold damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Silver Dragons",
            "Ancient Silver Dragon",
            "Actions",
        ),
        "**_Cold Breath (Recharge 5–6)._** _Constitution Saving Throw:_ DC 24, each creature in a 90-foot Cone. _Failure:_ 67 (15d8) Cold damage. _Success:_ Half damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Silver Dragons",
            "Ancient Silver Dragon",
            "Actions",
        ),
        "**_Paralyzing Breath._** _Constitution Saving Throw:_ DC 24, each creature in a 90-foot Cone. _First Failure:_ The target has the Incapacitated condition until the end of its next turn, when it repeats the save. _Second Failure:_ The target has the Paralyzed condition, and it repeats the save at the end of each of its turns, ending the effect on itself on a success. After 1 minute, it succeeds automatically.",
    ),
    (
        (
            "Monsters A–Z",
            "Silver Dragons",
            "Ancient Silver Dragon",
            "Actions",
        ),
        "**_Spellcasting._** The dragon casts one of the following spells, requiring no Material components and using Charisma as the spellcasting ability (spell save DC 23, +15 to hit with spell attacks): <br>\n&emsp;**At Will:** _Detect Magic_, _Hold Monster_, _Ice Knife_ (level 2 version), _Shapechange_ (Beast or Humanoid form only, no Temporary Hit Points gained from the spell, and no Concentration or Temporary Hit Points required to maintain the spell) <br>\n&emsp;**1/Day Each:** _Control Weather_, _Ice Storm_ (level 7 version), _Teleport_, _Zone of Truth_",
    ),
    (
        (
            "Monsters A–Z",
            "Silver Dragons",
            "Ancient Silver Dragon",
            "Legendary Actions",
        ),
        "#### Legendary Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Silver Dragons",
            "Ancient Silver Dragon",
            "Legendary Actions",
        ),
        "_Legendary Action Uses: 3 (4 in Lair). Immediately after another creature's turn, the dragon can expend a use to take one of the following actions. The dragon regains all expended uses at the start of each of its turns._",
    ),
    (
        (
            "Monsters A–Z",
            "Silver Dragons",
            "Ancient Silver Dragon",
            "Legendary Actions",
        ),
        "**_Chill._** The dragon uses Spellcasting to cast _Hold Monster_. The dragon can't take this action again until the start of its next turn.",
    ),
    (
        (
            "Monsters A–Z",
            "Silver Dragons",
            "Ancient Silver Dragon",
            "Legendary Actions",
        ),
        "**_Cold Gale._** _Dexterity Saving Throw:_ DC 23, each creature in a 60-foot-long, 10-foot-wide Line. _Failure:_ 14 (4d6) Cold damage, and the target is pushed up to 30 feet straight away from the dragon. _Success:_ Half damage only. _Failure or Success:_ The dragon can't take this action again until the start of its next turn.",
    ),
    (
        (
            "Monsters A–Z",
            "Silver Dragons",
            "Ancient Silver Dragon",
            "Legendary Actions",
        ),
        "**_Pounce._** The dragon moves up to half its Speed, and it makes one Rend attack.",
    ),
    (
        (
            "Monsters A–Z",
            "Skeletons",
        ),
        "## Skeletons",
    ),
    (
        (
            "Monsters A–Z",
            "Skeletons",
            "Skeleton",
        ),
        "### Skeleton",
    ),
    (
        (
            "Monsters A–Z",
            "Skeletons",
            "Skeleton",
        ),
        "_Medium Undead, Lawful Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Skeletons",
            "Skeleton",
        ),
        "**AC** 14 **Initiative** +3 (13) <br>\n**HP** 13 (2d8 + 4) <br>\n**Speed** 30 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Skeletons",
            "Skeleton",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>DEX</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>CON</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>6</td>\n      <td>−2</td>\n      <td>−2</td>\n      <td><strong>WIS</strong></td>\n      <td>8</td>\n      <td>−1</td>\n      <td>−1</td>\n      <td><strong>CHA</strong></td>\n      <td>5</td>\n      <td>−3</td>\n      <td>−3</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Skeletons",
            "Skeleton",
        ),
        "**Vulnerabilities** Bludgeoning<br>\n**Immunities** Poison; Exhaustion, Poisoned<br>\n**Gear** Shortbow, Shortsword<br>\n**Senses** Darkvision 60 ft.; Passive Perception 9<br>\n**Languages** Understands Common plus one other language but can't speak<br>\n**CR** 1/4 (XP 50; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Skeletons",
            "Skeleton",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Skeletons",
            "Skeleton",
            "Actions",
        ),
        "**_Shortsword._** _Melee Attack Roll:_ +5, reach 5 ft. _Hit:_ 6 (1d6 + 3) Piercing damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Skeletons",
            "Skeleton",
            "Actions",
        ),
        "**_Shortbow._** _Ranged Attack Roll:_ +5, range 80/320 ft. _Hit:_ 6 (1d6 + 3) Piercing damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Skeletons",
            "Warhorse Skeleton",
        ),
        "### Warhorse Skeleton",
    ),
    (
        (
            "Monsters A–Z",
            "Skeletons",
            "Warhorse Skeleton",
        ),
        "_Large Undead, Lawful Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Skeletons",
            "Warhorse Skeleton",
        ),
        "**AC** 13 **Initiative** +1 (11) <br>\n**HP** 22 (3d10 + 6) <br>\n**Speed** 60 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Skeletons",
            "Warhorse Skeleton",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+4</td>\n      <td><strong>DEX</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CON</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>2</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>WIS</strong></td>\n      <td>8</td>\n      <td>−1</td>\n      <td>−1</td>\n      <td><strong>CHA</strong></td>\n      <td>5</td>\n      <td>−3</td>\n      <td>−3</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Skeletons",
            "Warhorse Skeleton",
        ),
        "**Vulnerabilities** Bludgeoning<br>\n**Immunities** Poison; Exhaustion, Poisoned<br>\n**Senses** Darkvision 60 ft.; Passive Perception 9<br>\n**Languages** None<br>\n**CR** 1/2 (XP 100; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Skeletons",
            "Warhorse Skeleton",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Skeletons",
            "Warhorse Skeleton",
            "Actions",
        ),
        "**_Hooves._** _Melee Attack Roll:_ +6, reach 5 ft. _Hit:_ 7 (1d6 + 4) Bludgeoning damage. If the target is a Large or smaller creature and the skeleton moved 20+ feet straight toward it immediately before the hit, the target has the Prone condition.",
    ),
    (
        (
            "Monsters A–Z",
            "Skeletons",
            "Minotaur Skeleton",
        ),
        "### Minotaur Skeleton",
    ),
    (
        (
            "Monsters A–Z",
            "Skeletons",
            "Minotaur Skeleton",
        ),
        "_Large Undead, Lawful Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Skeletons",
            "Minotaur Skeleton",
        ),
        "**AC** 12 **Initiative** +0 (10) <br>\n**HP** 45 (6d10 + 12) <br>\n**Speed** 40 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Skeletons",
            "Minotaur Skeleton",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+4</td>\n      <td><strong>DEX</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CON</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>6</td>\n      <td>−2</td>\n      <td>−2</td>\n      <td><strong>WIS</strong></td>\n      <td>8</td>\n      <td>−1</td>\n      <td>−1</td>\n      <td><strong>CHA</strong></td>\n      <td>5</td>\n      <td>−3</td>\n      <td>−3</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Skeletons",
            "Minotaur Skeleton",
        ),
        "**Vulnerabilities** Bludgeoning<br>\n**Immunities** Poison; Exhaustion, Poisoned<br>\n**Senses** Darkvision 60 ft.; Passive Perception 9<br>\n**Languages** Understands Abyssal but can't speak<br>\n**CR** 2 (XP 450; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Skeletons",
            "Minotaur Skeleton",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Skeletons",
            "Minotaur Skeleton",
            "Actions",
        ),
        "**_Gore._** _Melee Attack Roll:_ +6, reach 5 ft. _Hit:_ 11 (2d6 + 4) Piercing damage. If the target is a Large or smaller creature and the skeleton moved 20+ feet straight toward it immediately before the hit, the target takes an extra 9 (2d8) Piercing damage and has the Prone condition.",
    ),
    (
        (
            "Monsters A–Z",
            "Skeletons",
            "Minotaur Skeleton",
            "Actions",
        ),
        "**_Slam._** _Melee Attack Roll:_ +6, reach 5 ft. _Hit:_ 15 (2d10 + 4) Bludgeoning damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Solar",
        ),
        "## Solar",
    ),
    (
        (
            "Monsters A–Z",
            "Solar",
            "Solar",
        ),
        "### Solar",
    ),
    (
        (
            "Monsters A–Z",
            "Solar",
            "Solar",
        ),
        "_Large Celestial (Angel), Lawful Good_",
    ),
    (
        (
            "Monsters A–Z",
            "Solar",
            "Solar",
        ),
        "**AC** 21 **Initiative** +20 (30) <br>\n**HP** 297 (22d10 + 176) <br>\n**Speed** 50 ft., Fly 150 ft. (hover) <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Solar",
            "Solar",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>26</td>\n      <td>+8</td>\n      <td>+8</td>\n      <td><strong>DEX</strong></td>\n      <td>22</td>\n      <td>+6</td>\n      <td>+6</td>\n      <td><strong>CON</strong></td>\n      <td>26</td>\n      <td>+8</td>\n      <td>+8</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>25</td>\n      <td>+7</td>\n      <td>+7</td>\n      <td><strong>WIS</strong></td>\n      <td>25</td>\n      <td>+7</td>\n      <td>+7</td>\n      <td><strong>CHA</strong></td>\n      <td>30</td>\n      <td>+10</td>\n      <td>+10</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Solar",
            "Solar",
        ),
        "**Skills** Perception +14<br>\n**Immunities** Poison, Radiant; Charmed, Exhaustion, Frightened, Poisoned<br>\n**Senses** Truesight 120 ft.; Passive Perception 24<br>\n**Languages** All; telepathy 120 ft.<br>\n**CR** 21 (XP 33,000; PB +7)",
    ),
    (
        (
            "Monsters A–Z",
            "Solar",
            "Solar",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Solar",
            "Solar",
            "Traits",
        ),
        "**_Divine Awareness._** The solar knows if it hears a lie.",
    ),
    (
        (
            "Monsters A–Z",
            "Solar",
            "Solar",
            "Traits",
        ),
        "**_Exalted Restoration._** If the solar dies outside Mount Celestia, its body disappears, and it gains a new body instantly, reviving with all its Hit Points somewhere in Mount Celestia.",
    ),
    (
        (
            "Monsters A–Z",
            "Solar",
            "Solar",
            "Traits",
        ),
        "**_Legendary Resistance (4/Day)._** If the solar fails a saving throw, it can choose to succeed instead.",
    ),
    (
        (
            "Monsters A–Z",
            "Solar",
            "Solar",
            "Traits",
        ),
        "**_Magic Resistance._** The solar has Advantage on saving throws against spells and other magical effects.",
    ),
    (
        (
            "Monsters A–Z",
            "Solar",
            "Solar",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Solar",
            "Solar",
            "Actions",
        ),
        "**_Multiattack._** The solar makes two Flying Sword attacks. It can replace one attack with a use of Slaying Bow.",
    ),
    (
        (
            "Monsters A–Z",
            "Solar",
            "Solar",
            "Actions",
        ),
        "**_Flying Sword._** _Melee or Ranged Attack Roll:_ +15, reach 10 ft. or range 120 ft. _Hit:_ 22 (4d6 + 8) Slashing damage plus 36 (8d8) Radiant damage. _Hit or Miss:_ The sword magically returns to the solar's hand or hovers within 5 feet of the solar immediately after a ranged attack.",
    ),
    (
        (
            "Monsters A–Z",
            "Solar",
            "Solar",
            "Actions",
        ),
        "**_Slaying Bow._** _Dexterity Saving Throw:_ DC 21, one creature the solar can see within 600 feet. _Failure:_ If the creature has 100 Hit Points or fewer, it dies. It otherwise takes 24 (4d8 + 6) Piercing damage plus 36 (8d8) Radiant damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Solar",
            "Solar",
            "Actions",
        ),
        "**_Spellcasting._** The solar casts one of the following spells, requiring no Material components and using Charisma as the spellcasting ability (spell save DC 25): <br>\n&emsp;**At Will:** _Detect Evil and Good_ <br>\n&emsp;**1/Day Each:** _Commune, Control Weather, Dispel Evil and Good, Resurrection_",
    ),
    (
        (
            "Monsters A–Z",
            "Solar",
            "Solar",
            "Bonus Actions",
        ),
        "#### Bonus Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Solar",
            "Solar",
            "Bonus Actions",
        ),
        "**_Divine Aid (3/Day)._** The solar casts _Cure Wounds_ (level 2 version), _Lesser Restoration_, or _Remove Curse_, using the same spellcasting ability as Spellcasting.",
    ),
    (
        (
            "Monsters A–Z",
            "Solar",
            "Solar",
            "Legendary Actions",
        ),
        "#### Legendary Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Solar",
            "Solar",
            "Legendary Actions",
        ),
        "_Legendary Action Uses: 3. Immediately after another creature's turn, the solar can expend a use to take one of the following actions. The solar regains all expended uses at the start of each of its turns._",
    ),
    (
        (
            "Monsters A–Z",
            "Solar",
            "Solar",
            "Legendary Actions",
        ),
        "**_Blinding Gaze._** _Constitution Saving Throw:_ DC 25, one creature the solar can see within 120 feet. _Failure:_ The target has the Blinded condition for 1 minute. _Failure or Success:_ The solar can't take this action again until the start of its next turn.",
    ),
    (
        (
            "Monsters A–Z",
            "Solar",
            "Solar",
            "Legendary Actions",
        ),
        "**_Radiant Teleport._** The solar teleports up to 60 feet to an unoccupied space it can see. _Dexterity Saving Throw:_ DC 25, each creature in a 10-foot Emanation originating from the solar at its destination space. _Failure:_ 11 (2d10) Radiant damage. _Success:_ Half damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Specter",
        ),
        "## Specter",
    ),
    (
        (
            "Monsters A–Z",
            "Specter",
            "Specter",
        ),
        "### Specter",
    ),
    (
        (
            "Monsters A–Z",
            "Specter",
            "Specter",
        ),
        "_Medium Undead, Chaotic Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Specter",
            "Specter",
        ),
        "**AC** 12 **Initiative** +2 (12) <br>\n**HP** 22 (5d8) <br>\n**Speed** 30 ft., Fly 50 ft. (hover) <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Specter",
            "Specter",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>1</td>\n      <td>−5</td>\n      <td>−5</td>\n      <td><strong>DEX</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CON</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>WIS</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CHA</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Specter",
            "Specter",
        ),
        "**Resistances** Acid, Bludgeoning, Cold, Fire, Lightning, Piercing, Slashing, Thunder<br>\n**Immunities** Necrotic, Poison; Charmed, Exhaustion, Grappled, Paralyzed, Petrified, Poisoned, Prone, Restrained, Unconscious<br>\n**Senses** Darkvision 60 ft.; Passive Perception 10<br>\n**Languages** Understands Common plus one other language but can't speak<br>\n**CR** 1 (XP 200; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Specter",
            "Specter",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Specter",
            "Specter",
            "Traits",
        ),
        "**_Incorporeal Movement._** The specter can move through other creatures and objects as if they were Difficult Terrain. It takes 5 (1d10) Force damage if it ends its turn inside an object.",
    ),
    (
        (
            "Monsters A–Z",
            "Specter",
            "Specter",
            "Traits",
        ),
        "**_Sunlight Sensitivity._** While in sunlight, the specter has Disadvantage on ability checks and attack rolls.",
    ),
    (
        (
            "Monsters A–Z",
            "Specter",
            "Specter",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Specter",
            "Specter",
            "Actions",
        ),
        "**_Life Drain._** _Melee Attack Roll:_ +4, reach 5 ft. _Hit:_ 7 (2d6) Necrotic damage. If the target is a creature, its Hit Point maximum decreases by an amount equal to the damage taken.",
    ),
    (
        (
            "Monsters A–Z",
            "Sphinxes",
        ),
        "## Sphinxes",
    ),
    (
        (
            "Monsters A–Z",
            "Sphinxes",
            "Sphinx of Wonder",
        ),
        "### Sphinx of Wonder",
    ),
    (
        (
            "Monsters A–Z",
            "Sphinxes",
            "Sphinx of Wonder",
        ),
        "_Tiny Celestial, Lawful Good_",
    ),
    (
        (
            "Monsters A–Z",
            "Sphinxes",
            "Sphinx of Wonder",
        ),
        "**AC** 13 **Initiative** +3 (13) <br>\n**HP** 24 (7d4 + 7) <br>\n**Speed** 20 ft., Fly 40 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Sphinxes",
            "Sphinx of Wonder",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>6</td>\n      <td>−2</td>\n      <td>−2</td>\n      <td><strong>DEX</strong></td>\n      <td>17</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>CON</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>WIS</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CHA</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Sphinxes",
            "Sphinx of Wonder",
        ),
        "**Skills** Arcana +4, Religion +4, Stealth +5<br>\n**Resistances** Necrotic, Psychic, Radiant<br>\n**Senses** Darkvision 60 ft.; Passive Perception 11<br>\n**Languages** Celestial, Common<br>\n**CR** 1 (XP 200; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Sphinxes",
            "Sphinx of Wonder",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Sphinxes",
            "Sphinx of Wonder",
            "Traits",
        ),
        "**_Magic Resistance._** The sphinx has Advantage on saving throws against spells and other magical effects.",
    ),
    (
        (
            "Monsters A–Z",
            "Sphinxes",
            "Sphinx of Wonder",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Sphinxes",
            "Sphinx of Wonder",
            "Actions",
        ),
        "**_Rend._** _Melee Attack Roll:_ +5, reach 5 ft. _Hit:_ 5 (1d4 + 3) Slashing damage plus 7 (2d6) Radiant damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Sphinxes",
            "Sphinx of Wonder",
            "Reactions",
        ),
        "#### Reactions",
    ),
    (
        (
            "Monsters A–Z",
            "Sphinxes",
            "Sphinx of Wonder",
            "Reactions",
        ),
        "**_Burst of Ingenuity (2/Day)._** _Trigger:_ The sphinx or another creature within 30 feet makes an ability check or a saving throw. _Response:_ The sphinx adds 2 to the roll.",
    ),
    (
        (
            "Monsters A–Z",
            "Sphinxes",
            "Sphinx of Lore",
        ),
        "### Sphinx of Lore",
    ),
    (
        (
            "Monsters A–Z",
            "Sphinxes",
            "Sphinx of Lore",
        ),
        "_Large Celestial, Lawful Neutral_",
    ),
    (
        (
            "Monsters A–Z",
            "Sphinxes",
            "Sphinx of Lore",
        ),
        "**AC** 17 **Initiative** +10 (20) <br>\n**HP** 170 (20d10 + 60) <br>\n**Speed** 40 ft., Fly 60 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Sphinxes",
            "Sphinx of Lore",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+4</td>\n      <td><strong>DEX</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CON</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+4</td>\n      <td><strong>WIS</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+4</td>\n      <td><strong>CHA</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+4</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Sphinxes",
            "Sphinx of Lore",
        ),
        "**Skills** Arcana +12, History +12, Perception +8, Religion +12<br>\n**Resistances** Necrotic, Radiant<br>\n**Immunities** Psychic; Charmed, Frightened<br>\n**Senses** Truesight 120 ft.; Passive Perception 18<br>\n**Languages** Celestial, Common<br>\n**CR** 11 (XP 7,200, or 8,400 in lair; PB +4)",
    ),
    (
        (
            "Monsters A–Z",
            "Sphinxes",
            "Sphinx of Lore",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Sphinxes",
            "Sphinx of Lore",
            "Traits",
        ),
        "**_Inscrutable._** No magic can observe the sphinx remotely or detect its thoughts without its permission. Wisdom (Insight) checks made to ascertain its intentions or sincerity are made with Disadvantage.",
    ),
    (
        (
            "Monsters A–Z",
            "Sphinxes",
            "Sphinx of Lore",
            "Traits",
        ),
        "**_Legendary Resistance (3/Day, or 4/Day in Lair)._** If the sphinx fails a saving throw, it can choose to succeed instead.",
    ),
    (
        (
            "Monsters A–Z",
            "Sphinxes",
            "Sphinx of Lore",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Sphinxes",
            "Sphinx of Lore",
            "Actions",
        ),
        "**_Multiattack._** The sphinx makes three Claw attacks.",
    ),
    (
        (
            "Monsters A–Z",
            "Sphinxes",
            "Sphinx of Lore",
            "Actions",
        ),
        "**_Claw._** _Melee Attack Roll:_ +8, reach 5 ft. _Hit:_ 14 (3d6 + 4) Slashing damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Sphinxes",
            "Sphinx of Lore",
            "Actions",
        ),
        "**_Mind-Rending Roar (Recharge 5–6)._** _Wisdom Saving Throw:_ DC 16, each enemy in a 300-foot Emanation originating from the sphinx. _Failure:_ 35 (10d6) Psychic damage, and the target has the Incapacitated condition until the start of the sphinx's next turn.",
    ),
    (
        (
            "Monsters A–Z",
            "Sphinxes",
            "Sphinx of Lore",
            "Actions",
        ),
        "**_Spellcasting._** The sphinx casts one of the following spells, requiring no Material components and using Intelligence as the spellcasting ability (spell save DC 16): <br>\n&emsp;**At Will:** _Detect Magic_, _Identify_, _Mage Hand_, _Minor Illusion_, _Prestidigitation_ <br>\n&emsp;**1/Day Each:** _Dispel Magic_, _Legend Lore_, _Locate Object_, _Plane Shift_, _Remove Curse_, _Tongues_",
    ),
    (
        (
            "Monsters A–Z",
            "Sphinxes",
            "Sphinx of Lore",
            "Legendary Actions",
        ),
        "#### Legendary Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Sphinxes",
            "Sphinx of Lore",
            "Legendary Actions",
        ),
        "_Legendary Action Uses: 3 (4 in Lair). Immediately after another creature's turn, the sphinx can expend a use to take one of the following actions. The sphinx regains all expended uses at the start of each of its turns._",
    ),
    (
        (
            "Monsters A–Z",
            "Sphinxes",
            "Sphinx of Lore",
            "Legendary Actions",
        ),
        "**_Arcane Prowl._** The sphinx can teleport up to 30 feet to an unoccupied space it can see, and it makes one Claw attack.",
    ),
    (
        (
            "Monsters A–Z",
            "Sphinxes",
            "Sphinx of Lore",
            "Legendary Actions",
        ),
        "**_Weight of Years._** _Constitution Saving Throw:_ DC 16, one creature the sphinx can see within 120 feet. _Failure:_ The target gains 1 Exhaustion level. While the target has any Exhaustion levels, it appears 3d10 years older. _Failure or Success:_ The sphinx can't take this action again until the start of its next turn.",
    ),
    (
        (
            "Monsters A–Z",
            "Sphinxes",
            "Sphinx of Valor",
        ),
        "### Sphinx of Valor",
    ),
    (
        (
            "Monsters A–Z",
            "Sphinxes",
            "Sphinx of Valor",
        ),
        "_Large Celestial, Lawful Neutral_",
    ),
    (
        (
            "Monsters A–Z",
            "Sphinxes",
            "Sphinx of Valor",
        ),
        "**AC** 17 **Initiative** +12 (22) <br>\n**HP** 199 (19d10 + 95) <br>\n**Speed** 40 ft., Fly 60 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Sphinxes",
            "Sphinx of Valor",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>22</td>\n      <td>+6</td>\n      <td>+6</td>\n      <td><strong>DEX</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+6</td>\n      <td><strong>CON</strong></td>\n      <td>20</td>\n      <td>+5</td>\n      <td>+11</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+9</td>\n      <td><strong>WIS</strong></td>\n      <td>23</td>\n      <td>+6</td>\n      <td>+12</td>\n      <td><strong>CHA</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+4</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Sphinxes",
            "Sphinx of Valor",
        ),
        "**Skills** Arcana +9, Perception +12, Religion +15<br>\n**Resistances** Necrotic, Radiant<br>\n**Immunities** Psychic; Charmed, Frightened<br>\n**Senses** Truesight 120 ft.; Passive Perception 22<br>\n**Languages** Celestial, Common<br>\n**CR** 17 (XP 18,000, or 20,000 in lair; PB +6)",
    ),
    (
        (
            "Monsters A–Z",
            "Sphinxes",
            "Sphinx of Valor",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Sphinxes",
            "Sphinx of Valor",
            "Traits",
        ),
        "**_Inscrutable._** No magic can observe the sphinx remotely or detect its thoughts without its permission. Wisdom (Insight) checks made to ascertain its intentions or sincerity are made with Disadvantage.",
    ),
    (
        (
            "Monsters A–Z",
            "Sphinxes",
            "Sphinx of Valor",
            "Traits",
        ),
        "**_Legendary Resistance (3/Day, or 4/Day in Lair)._** If the sphinx fails a saving throw, it can choose to succeed instead.",
    ),
    (
        (
            "Monsters A–Z",
            "Sphinxes",
            "Sphinx of Valor",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Sphinxes",
            "Sphinx of Valor",
            "Actions",
        ),
        "**_Multiattack._** The sphinx makes two Claw attacks and uses Roar.",
    ),
    (
        (
            "Monsters A–Z",
            "Sphinxes",
            "Sphinx of Valor",
            "Actions",
        ),
        "**_Claw._** _Melee Attack Roll:_ +12, reach 5 ft. _Hit:_ 20 (4d6 + 6) Slashing damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Sphinxes",
            "Sphinx of Valor",
            "Actions",
        ),
        "**_Roar (3/Day)._** The sphinx emits a magical roar. Whenever it roars, the roar has a different effect, as detailed below (the sequence resets when it takes a Long Rest):",
    ),
    (
        (
            "Monsters A–Z",
            "Sphinxes",
            "Sphinx of Valor",
            "Actions",
        ),
        "**_First Roar._** _Wisdom Saving Throw:_ DC 20, each enemy in a 500-foot Emanation originating from the sphinx. _Failure:_ The target has the Frightened condition for 1 minute.",
    ),
    (
        (
            "Monsters A–Z",
            "Sphinxes",
            "Sphinx of Valor",
            "Actions",
        ),
        "**_Second Roar._** _Wisdom Saving Throw:_ DC 20, each enemy in a 500-foot Emanation originating from the sphinx. _Failure:_ The target has the Paralyzed condition, and it repeats the save at the end of each of its turns, ending the effect on itself on a success. After 1 minute, it succeeds automatically.",
    ),
    (
        (
            "Monsters A–Z",
            "Sphinxes",
            "Sphinx of Valor",
            "Actions",
        ),
        "**_Third Roar._** _Constitution Saving Throw:_ DC 20, each enemy in a 500-foot Emanation originating from the sphinx. _Failure:_ 44 (8d10) Thunder damage, and the target has the Prone condition. _Success:_ Half damage only.",
    ),
    (
        (
            "Monsters A–Z",
            "Sphinxes",
            "Sphinx of Valor",
            "Actions",
        ),
        "**_Spellcasting._** The sphinx casts one of the following spells, requiring no Material components and using Wisdom as the spellcasting ability (spell save DC 20): <br>\n&emsp;**At Will:** _Detect Evil and Good_, _Thaumaturgy_ <br>\n&emsp;**1/Day Each:** _Detect Magic_, _Dispel Magic_, _Greater Restoration_, _Heroes' Feast_, _Zone of Truth_",
    ),
    (
        (
            "Monsters A–Z",
            "Sphinxes",
            "Sphinx of Valor",
            "Legendary Actions",
        ),
        "#### Legendary Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Sphinxes",
            "Sphinx of Valor",
            "Legendary Actions",
        ),
        "_Legendary Action Uses: 3 (4 in Lair). Immediately after another creature's turn, the sphinx can expend a use to take one of the following actions. The sphinx regains all expended uses at the start of each of its turns._",
    ),
    (
        (
            "Monsters A–Z",
            "Sphinxes",
            "Sphinx of Valor",
            "Legendary Actions",
        ),
        "**_Arcane Prowl._** The sphinx can teleport up to 30 feet to an unoccupied space it can see, and it makes one Claw attack.",
    ),
    (
        (
            "Monsters A–Z",
            "Sphinxes",
            "Sphinx of Valor",
            "Legendary Actions",
        ),
        "**_Weight of Years._** _Constitution Saving Throw:_ DC 16, one creature the sphinx can see within 120 feet. _Failure:_ The target gains 1 Exhaustion level. While the target has any Exhaustion levels, it appears 3d10 years older. _Failure or Success:_ The sphinx can't take this action again until the start of its next turn.",
    ),
    (
        (
            "Monsters A–Z",
            "Spirit Naga",
        ),
        "## Spirit Naga",
    ),
    (
        (
            "Monsters A–Z",
            "Spirit Naga",
            "Spirit Naga",
        ),
        "### Spirit Naga",
    ),
    (
        (
            "Monsters A–Z",
            "Spirit Naga",
            "Spirit Naga",
        ),
        "_Large Fiend, Chaotic Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Spirit Naga",
            "Spirit Naga",
        ),
        "**AC** 17 **Initiative** +3 (13) <br>\n**HP** 135 (18d10 + 36) <br>\n**Speed** 40 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Spirit Naga",
            "Spirit Naga",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+4</td>\n      <td><strong>DEX</strong></td>\n      <td>17</td>\n      <td>+3</td>\n      <td>+6</td>\n      <td><strong>CON</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+5</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>WIS</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+5</td>\n      <td><strong>CHA</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+6</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Spirit Naga",
            "Spirit Naga",
        ),
        "**Immunities** Poison; Charmed, Poisoned<br>\n**Senses** Darkvision 60 ft.; Passive Perception 12<br>\n**Languages** Abyssal, Common<br>\n**CR** 8 (XP 3,900; PB +3)",
    ),
    (
        (
            "Monsters A–Z",
            "Spirit Naga",
            "Spirit Naga",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Spirit Naga",
            "Spirit Naga",
            "Traits",
        ),
        "**_Fiendish Restoration._** If it dies, the naga returns to life in 1d6 days and regains all its Hit Points. Only a _Wish_ spell can prevent this trait from functioning.",
    ),
    (
        (
            "Monsters A–Z",
            "Spirit Naga",
            "Spirit Naga",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Spirit Naga",
            "Spirit Naga",
            "Actions",
        ),
        "**_Multiattack._** The naga makes three attacks, using Bite or Necrotic Ray in any combination.",
    ),
    (
        (
            "Monsters A–Z",
            "Spirit Naga",
            "Spirit Naga",
            "Actions",
        ),
        "**_Bite._** _Melee Attack Roll:_ +7, reach 10 ft. _Hit:_ 7 (1d6 + 4) Piercing damage plus 14 (4d6) Poison damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Spirit Naga",
            "Spirit Naga",
            "Actions",
        ),
        "**_Necrotic Ray._** _Ranged Attack Roll:_ +6, range 60 ft. _Hit:_ 21 (6d6) Necrotic damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Spirit Naga",
            "Spirit Naga",
            "Actions",
        ),
        "**_Spellcasting._** The naga casts one of the following spells, requiring no Somatic or Material components and using Intelligence as the spellcasting ability (spell save DC 14): <br>\n&emsp;**At Will:** _Detect Magic_, _Mage Hand_, _Minor Illusion_, _Water Breathing_ <br>\n&emsp;**2/Day Each:** _Detect Thoughts_, _Dimension Door_, _Hold Person_ (level 3 version), _Lightning Bolt_ (level 4 version)",
    ),
    (
        (
            "Monsters A–Z",
            "Sprite",
        ),
        "## Sprite",
    ),
    (
        (
            "Monsters A–Z",
            "Sprite",
            "Sprite",
        ),
        "### Sprite",
    ),
    (
        (
            "Monsters A–Z",
            "Sprite",
            "Sprite",
        ),
        "_Tiny Fey, Neutral Good_",
    ),
    (
        (
            "Monsters A–Z",
            "Sprite",
            "Sprite",
        ),
        "**AC** 15 **Initiative** +4 (14) <br>\n**HP** 10 (4d4) <br>\n**Speed** 10 ft., Fly 40 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Sprite",
            "Sprite",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>3</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>DEX</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+4</td>\n      <td><strong>CON</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>WIS</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CHA</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Sprite",
            "Sprite",
        ),
        "**Skills** Perception +3, Stealth +8<br>\n**Senses** Passive Perception 13<br>\n**Languages** Common, Elvish, Sylvan<br>\n**CR** 1/4 (XP 50; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Sprite",
            "Sprite",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Sprite",
            "Sprite",
            "Actions",
        ),
        "**_Needle Sword._** _Melee Attack Roll:_ +6, reach 5 ft. _Hit:_ 6 (1d4 + 4) Piercing damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Sprite",
            "Sprite",
            "Actions",
        ),
        "**_Enchanting Bow._** _Ranged Attack Roll:_ +6, range 40/160 ft. _Hit:_ 1 Piercing damage, and the target has the Charmed condition until the start of the sprite's next turn.",
    ),
    (
        (
            "Monsters A–Z",
            "Sprite",
            "Sprite",
            "Actions",
        ),
        "**_Heart Sight._** _Charisma Saving Throw:_ DC 10, one creature within 5 feet the sprite can see (Celestials, Fiends, and Undead automatically fail the save). _Failure:_ The sprite knows the target's emotions and alignment.",
    ),
    (
        (
            "Monsters A–Z",
            "Sprite",
            "Sprite",
            "Actions",
        ),
        "**_Invisibility._** The sprite casts _Invisibility_ on itself, requiring no spell components and using Charisma as the spellcasting ability.",
    ),
    (
        (
            "Monsters A–Z",
            "Spy",
        ),
        "## Spy",
    ),
    (
        (
            "Monsters A–Z",
            "Spy",
            "Spy",
        ),
        "### Spy",
    ),
    (
        (
            "Monsters A–Z",
            "Spy",
            "Spy",
        ),
        "_Medium or Small Humanoid, Neutral_",
    ),
    (
        (
            "Monsters A–Z",
            "Spy",
            "Spy",
        ),
        "**AC** 12 **Initiative** +4 (14) <br>\n**HP** 27 (6d8) <br>\n**Speed** 30 ft., Climb 30 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Spy",
            "Spy",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>DEX</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CON</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>WIS</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CHA</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Spy",
            "Spy",
        ),
        "**Skills** Deception +5, Insight +4, Investigation +5, Perception +6, Sleight of Hand +4, Stealth +6<br>\n**Gear** Hand Crossbow, Shortsword, Thieves' Tools<br>\n**Senses** Passive Perception 16<br>\n**Languages** Common plus one other language<br>\n**CR** 1 (XP 200; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Spy",
            "Spy",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Spy",
            "Spy",
            "Actions",
        ),
        "**_Shortsword._** _Melee Attack Roll:_ +4, reach 5 ft. _Hit:_ 5 (1d6 + 2) Piercing damage plus 7 (2d6) Poison damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Spy",
            "Spy",
            "Actions",
        ),
        "**_Hand Crossbow._** _Ranged Attack Roll:_ +4, range 30/120 ft. _Hit:_ 5 (1d6 + 2) Piercing damage plus 7 (2d6) Poison damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Spy",
            "Spy",
            "Bonus Actions",
        ),
        "#### Bonus Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Spy",
            "Spy",
            "Bonus Actions",
        ),
        "**_Cunning Action._** The spy takes the Dash, Disengage, or Hide action.",
    ),
    (
        (
            "Monsters A–Z",
            "Stirge",
        ),
        "## Stirge",
    ),
    (
        (
            "Monsters A–Z",
            "Stirge",
            "Stirge",
        ),
        "### Stirge",
    ),
    (
        (
            "Monsters A–Z",
            "Stirge",
            "Stirge",
        ),
        "_Tiny Monstrosity, Unaligned_",
    ),
    (
        (
            "Monsters A–Z",
            "Stirge",
            "Stirge",
        ),
        "**AC** 13 **Initiative** +3 (13) <br>\n**HP** 5 (2d4) <br>\n**Speed** 10 ft., Fly 40 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Stirge",
            "Stirge",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>4</td>\n      <td>−3</td>\n      <td>−3</td>\n      <td><strong>DEX</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>CON</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>2</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>WIS</strong></td>\n      <td>8</td>\n      <td>−1</td>\n      <td>−1</td>\n      <td><strong>CHA</strong></td>\n      <td>6</td>\n      <td>−2</td>\n      <td>−2</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Stirge",
            "Stirge",
        ),
        "**Senses** Darkvision 60 ft.; Passive Perception 9<br>\n**Languages** None<br>\n**CR** 1/8 (XP 25; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Stirge",
            "Stirge",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Stirge",
            "Stirge",
            "Actions",
        ),
        "**_Proboscis._** _Melee Attack Roll:_ +5, reach 5 ft. _Hit:_ 6 (1d6 + 3) Piercing damage, and the stirge attaches to the target. While attached, the stirge can't make Proboscis attacks, and the target takes 5 (2d4) Necrotic damage at the start of each of the stirge's turns. <br>\n&emsp;The stirge can detach itself by spending 5 feet of its movement. The target or a creature within 5 feet of it can detach the stirge as an action.",
    ),
    (
        (
            "Monsters A–Z",
            "Stone Giant",
        ),
        "## Stone Giant",
    ),
    (
        (
            "Monsters A–Z",
            "Stone Giant",
            "Stone Giant",
        ),
        "### Stone Giant",
    ),
    (
        (
            "Monsters A–Z",
            "Stone Giant",
            "Stone Giant",
        ),
        "_Huge Giant, Neutral_",
    ),
    (
        (
            "Monsters A–Z",
            "Stone Giant",
            "Stone Giant",
        ),
        "**AC** 17 **Initiative** +5 (15) <br>\n**HP** 126 (11d12 + 55) <br>\n**Speed** 40 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Stone Giant",
            "Stone Giant",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>23</td>\n      <td>+6</td>\n      <td>+6</td>\n      <td><strong>DEX</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+5</td>\n      <td><strong>CON</strong></td>\n      <td>20</td>\n      <td>+5</td>\n      <td>+8</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>WIS</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+4</td>\n      <td><strong>CHA</strong></td>\n      <td>9</td>\n      <td>-1</td>\n      <td>-1</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Stone Giant",
            "Stone Giant",
        ),
        "**Skills** Athletics +12, Perception +4, Stealth +5<br>\n**Senses** Darkvision 60 ft.; Passive Perception 14<br>\n**Languages** Giant<br>\n**CR** 7 (XP 2,900; PB +3)",
    ),
    (
        (
            "Monsters A–Z",
            "Stone Giant",
            "Stone Giant",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Stone Giant",
            "Stone Giant",
            "Actions",
        ),
        "**_Multiattack._** The giant makes two attacks, using Stone Club or Boulder in any combination.",
    ),
    (
        (
            "Monsters A–Z",
            "Stone Giant",
            "Stone Giant",
            "Actions",
        ),
        "**_Stone Club._** _Melee Attack Roll:_ +9, reach 15 ft. _Hit:_ 22 (3d10 + 6) Bludgeoning damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Stone Giant",
            "Stone Giant",
            "Actions",
        ),
        "**_Boulder._** _Ranged Attack Roll:_ +9, range 60/240 ft. _Hit:_ 15 (2d8 + 6) Bludgeoning damage. If the target is a Large or smaller creature, it has the Prone condition.",
    ),
    (
        (
            "Monsters A–Z",
            "Stone Giant",
            "Stone Giant",
            "Reactions",
        ),
        "#### Reactions",
    ),
    (
        (
            "Monsters A–Z",
            "Stone Giant",
            "Stone Giant",
            "Reactions",
        ),
        "**_Deflect Missile (Recharge 5–6)._** _Trigger:_ The giant is hit by a ranged attack roll and takes Bludgeoning, Piercing, or Slashing damage from it. _Response:_ The giant reduces the damage it takes from the attack by 11 (1d10 + 6), and if that damage is reduced to 0, the giant can redirect some of the attack's force. _Dexterity Saving Throw:_ DC 17, one creature the giant can see within 60 feet. _Failure:_ 11 (1d10 + 6) Force damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Stone Golem",
        ),
        "## Stone Golem",
    ),
    (
        (
            "Monsters A–Z",
            "Stone Golem",
            "Stone Golem",
        ),
        "### Stone Golem",
    ),
    (
        (
            "Monsters A–Z",
            "Stone Golem",
            "Stone Golem",
        ),
        "_Large Construct, Unaligned_",
    ),
    (
        (
            "Monsters A–Z",
            "Stone Golem",
            "Stone Golem",
        ),
        "**AC** 18 **Initiative** +3 (13) <br>\n**HP** 220 (21d10 + 105) <br>\n**Speed** 30 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Stone Golem",
            "Stone Golem",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>22</td>\n      <td>+6</td>\n      <td>+6</td>\n      <td><strong>DEX</strong></td>\n      <td>9</td>\n      <td>-1</td>\n      <td>-1</td>\n      <td><strong>CON</strong></td>\n      <td>20</td>\n      <td>+5</td>\n      <td>+5</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>3</td>\n      <td>-4</td>\n      <td>-4</td>\n      <td><strong>WIS</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CHA</strong></td>\n      <td>1</td>\n      <td>-5</td>\n      <td>-5</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Stone Golem",
            "Stone Golem",
        ),
        "**Immunities** Poison, Psychic; Charmed, Exhaustion, Frightened, Paralyzed, Petrified, Poisoned<br>\n**Senses** Darkvision 120 ft.; Passive Perception 10<br>\n**Languages** Understands Common plus two other languages but can't speak<br>\n**CR** 10 (XP 5,900; PB +4)",
    ),
    (
        (
            "Monsters A–Z",
            "Stone Golem",
            "Stone Golem",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Stone Golem",
            "Stone Golem",
            "Traits",
        ),
        "**_Immutable Form._** The golem can't shape-shift.",
    ),
    (
        (
            "Monsters A–Z",
            "Stone Golem",
            "Stone Golem",
            "Traits",
        ),
        "**_Magic Resistance._** The golem has Advantage on saving throws against spells and other magical effects.",
    ),
    (
        (
            "Monsters A–Z",
            "Stone Golem",
            "Stone Golem",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Stone Golem",
            "Stone Golem",
            "Actions",
        ),
        "**_Multiattack._** The golem makes two attacks, using Slam or Force Bolt in any combination.",
    ),
    (
        (
            "Monsters A–Z",
            "Stone Golem",
            "Stone Golem",
            "Actions",
        ),
        "**_Slam._** _Melee Attack Roll:_ +10, reach 5 ft. _Hit:_ 15 (2d8 + 6) Bludgeoning damage plus 9 (2d8) Force damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Stone Golem",
            "Stone Golem",
            "Actions",
        ),
        "**_Force Bolt._** _Ranged Attack Roll:_ +9, range 120 ft. _Hit:_ 22 (4d10) Force damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Stone Golem",
            "Stone Golem",
            "Bonus Actions",
        ),
        "#### Bonus Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Stone Golem",
            "Stone Golem",
            "Bonus Actions",
        ),
        "**_Slow (Recharge 5–6)._** The golem casts the _Slow_ spell, requiring no spell components and using Constitution as the spellcasting ability (spell save DC 17).",
    ),
    (
        (
            "Monsters A–Z",
            "Storm Giant",
        ),
        "## Storm Giant",
    ),
    (
        (
            "Monsters A–Z",
            "Storm Giant",
            "Storm Giant",
        ),
        "### Storm Giant",
    ),
    (
        (
            "Monsters A–Z",
            "Storm Giant",
            "Storm Giant",
        ),
        "_Huge Giant, Chaotic Good_",
    ),
    (
        (
            "Monsters A–Z",
            "Storm Giant",
            "Storm Giant",
        ),
        "**AC** 16 **Initiative** +7 (17) <br>\n**HP** 230 (20d12 + 100) <br>\n**Speed** 50 ft., Fly 25 ft. (hover), Swim 50 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Storm Giant",
            "Storm Giant",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>29</td>\n      <td>+9</td>\n      <td>+14</td>\n      <td><strong>DEX</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CON</strong></td>\n      <td>20</td>\n      <td>+5</td>\n      <td>+10</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>WIS</strong></td>\n      <td>20</td>\n      <td>+5</td>\n      <td>+10</td>\n      <td><strong>CHA</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+9</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Storm Giant",
            "Storm Giant",
        ),
        "**Skills** Arcana +8, Athletics +14, History +8, Perception +10<br>\n**Resistances** Cold<br>\n**Immunities** Lightning, Thunder<br>\n**Senses** Darkvision 120 ft., Truesight 30 ft.; Passive Perception 20<br>\n**Languages** Common, Giant<br>\n**CR** 13 (XP 10,000; PB +5)",
    ),
    (
        (
            "Monsters A–Z",
            "Storm Giant",
            "Storm Giant",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Storm Giant",
            "Storm Giant",
            "Traits",
        ),
        "**_Amphibious._** The giant can breathe air and water.",
    ),
    (
        (
            "Monsters A–Z",
            "Storm Giant",
            "Storm Giant",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Storm Giant",
            "Storm Giant",
            "Actions",
        ),
        "**_Multiattack._** The giant makes two attacks, using Storm Sword or Thunderbolt in any combination.",
    ),
    (
        (
            "Monsters A–Z",
            "Storm Giant",
            "Storm Giant",
            "Actions",
        ),
        "**_Storm Sword._** _Melee Attack Roll:_ +14, reach 10 ft. _Hit:_ 23 (4d6 + 9) Slashing damage plus 13 (3d8) Lightning damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Storm Giant",
            "Storm Giant",
            "Actions",
        ),
        "**_Thunderbolt._** _Ranged Attack Roll:_ +14, range 500 ft. _Hit:_ 22 (2d12 + 9) Lightning damage, and the target has the Blinded and Deafened conditions until the start of the giant's next turn.",
    ),
    (
        (
            "Monsters A–Z",
            "Storm Giant",
            "Storm Giant",
            "Actions",
        ),
        "**_Lightning Storm (Recharge 5–6)._** _Dexterity Saving Throw:_ DC 18, each creature in a 10-foot-radius, 40-foot-high Cylinder originating from a point the giant can see within 500 feet. _Failure:_ 55 (10d10) Lightning damage. _Success:_ Half damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Storm Giant",
            "Storm Giant",
            "Actions",
        ),
        "**_Spellcasting._** The giant casts one of the following spells, requiring no Material components and using Wisdom as the spellcasting ability (spell save DC 18): <br>\n&emsp;**At Will:** Detect Magic, Light <br>\n&emsp;**1/Day:** Control Weather",
    ),
    (
        (
            "Monsters A–Z",
            "Succubus",
        ),
        "## Succubus",
    ),
    (
        (
            "Monsters A–Z",
            "Succubus",
            "Succubus",
        ),
        "### Succubus",
    ),
    (
        (
            "Monsters A–Z",
            "Succubus",
            "Succubus",
        ),
        "_Medium Fiend, Neutral Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Succubus",
            "Succubus",
        ),
        "**AC** 15 **Initiative** +3 (13) <br>\n**HP** 71 (13d8 + 13) <br>\n**Speed** 30 ft., Fly 60 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Succubus",
            "Succubus",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>8</td>\n      <td>−1</td>\n      <td>−1</td>\n      <td><strong>DEX</strong></td>\n      <td>17</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>CON</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>WIS</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CHA</strong></td>\n      <td>20</td>\n      <td>+5</td>\n      <td>+5</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Succubus",
            "Succubus",
        ),
        "**Skills** Deception +9, Insight +5, Perception +5, Persuasion +9, Stealth +7<br>\n**Resistances** Cold, Fire, Poison, Psychic<br>\n**Senses** Darkvision 60 ft.; Passive Perception 15<br>\n**Languages** Abyssal, Common, Infernal; telepathy 60 ft.<br>\n**CR** 4 (XP 1,100; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Succubus",
            "Succubus",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Succubus",
            "Succubus",
            "Traits",
        ),
        "**_Incubus Form._** When the succubus finishes a Long Rest, it can shape-shift into an **Incubus**, using that stat block instead of this one.",
    ),
    (
        (
            "Monsters A–Z",
            "Succubus",
            "Succubus",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Succubus",
            "Succubus",
            "Actions",
        ),
        "**_Multiattack._** The succubus makes one Fiendish Touch attack and uses Charm or Draining Kiss.",
    ),
    (
        (
            "Monsters A–Z",
            "Succubus",
            "Succubus",
            "Actions",
        ),
        "**_Fiendish Touch._** _Melee Attack Roll:_ +7, reach 5 ft. _Hit:_ 16 (2d10 + 5) Psychic damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Succubus",
            "Succubus",
            "Actions",
        ),
        "**_Charm._** The succubus casts Dominate Person (level 8 version), requiring no spell components and using Charisma as the spellcasting ability (spell save DC 15).",
    ),
    (
        (
            "Monsters A–Z",
            "Succubus",
            "Succubus",
            "Actions",
        ),
        "**_Draining Kiss._** _Constitution Saving Throw:_ DC 15, one creature Charmed by the succubus within 5 feet. _Failure:_ 13 (3d8) Psychic damage. _Success:_ Half damage. _Failure or Success:_ The target's Hit Point maximum decreases by an amount equal to the damage taken.",
    ),
    (
        (
            "Monsters A–Z",
            "Succubus",
            "Succubus",
            "Bonus Actions",
        ),
        "#### Bonus Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Succubus",
            "Succubus",
            "Bonus Actions",
        ),
        "**_Shape-Shift._** The succubus shape-shifts into a Medium or Small Humanoid, or it returns to its true form. Its game statistics are the same in each form, except its Fly Speed is available only in its true form. Any equipment it is wearing or carrying isn't transformed.",
    ),
    (
        (
            "Monsters A–Z",
            "Tarrasque",
        ),
        "## Tarrasque",
    ),
    (
        (
            "Monsters A–Z",
            "Tarrasque",
            "Tarrasque",
        ),
        "### Tarrasque",
    ),
    (
        (
            "Monsters A–Z",
            "Tarrasque",
            "Tarrasque",
        ),
        "_Gargantuan Monstrosity (Titan), Unaligned_",
    ),
    (
        (
            "Monsters A–Z",
            "Tarrasque",
            "Tarrasque",
        ),
        "**AC** 25 **Initiative** +18 (28) <br>\n**HP** 697 (34d20 + 340) <br>\n**Speed** 60 ft., Burrow 40 ft., Climb 60 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Tarrasque",
            "Tarrasque",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>30</td>\n      <td>+10</td>\n      <td>+10</td>\n      <td><strong>DEX</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+9</td>\n      <td><strong>CON</strong></td>\n      <td>30</td>\n      <td>+10</td>\n      <td>+10</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>3</td>\n      <td>−4</td>\n      <td>+5</td>\n      <td><strong>WIS</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+9</td>\n      <td><strong>CHA</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+9</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Tarrasque",
            "Tarrasque",
        ),
        "**Skills** Perception +9<br>\n**Resistances** Bludgeoning, Piercing, Slashing<br>\n**Immunities** Fire, Poison; Charmed, Deafened, Frightened, Paralyzed, Poisoned<br>\n**Senses** Blindsight 120 ft.; Passive Perception 19<br>\n**Languages** None<br>\n**CR** 30 (XP 155,000; PB +9)",
    ),
    (
        (
            "Monsters A–Z",
            "Tarrasque",
            "Tarrasque",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Tarrasque",
            "Tarrasque",
            "Traits",
        ),
        "**_Legendary Resistance (6/Day)._** If the tarrasque fails a saving throw, it can choose to succeed instead.",
    ),
    (
        (
            "Monsters A–Z",
            "Tarrasque",
            "Tarrasque",
            "Traits",
        ),
        "**_Magic Resistance._** The tarrasque has Advantage on saving throws against spells and other magical effects.",
    ),
    (
        (
            "Monsters A–Z",
            "Tarrasque",
            "Tarrasque",
            "Traits",
        ),
        "**_Reflective Carapace._** If the tarrasque is targeted by a Magic Missile spell or a spell that requires a ranged attack roll, roll 1d6. On a **1–5**, the tarrasque is unaffected. On a **6**, the tarrasque is unaffected and reflects the spell, turning the caster into the target.",
    ),
    (
        (
            "Monsters A–Z",
            "Tarrasque",
            "Tarrasque",
            "Traits",
        ),
        "**_Siege Monster._** The tarrasque deals double damage to objects and structures.",
    ),
    (
        (
            "Monsters A–Z",
            "Tarrasque",
            "Tarrasque",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Tarrasque",
            "Tarrasque",
            "Actions",
        ),
        "**_Multiattack._** The tarrasque makes one Bite attack and three other attacks, using Claw or Tail in any combination.",
    ),
    (
        (
            "Monsters A–Z",
            "Tarrasque",
            "Tarrasque",
            "Actions",
        ),
        "**_Bite._** _Melee Attack Roll:_ +19, reach 15 ft. _Hit:_ 36 (4d12 + 10) Piercing damage, and the target has the Grappled condition (escape DC 20). Until the grapple ends, the target has the Restrained condition and can't teleport.",
    ),
    (
        (
            "Monsters A–Z",
            "Tarrasque",
            "Tarrasque",
            "Actions",
        ),
        "**_Claw._** _Melee Attack Roll:_ +19, reach 15 ft. _Hit:_ 28 (4d8 + 10) Slashing damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Tarrasque",
            "Tarrasque",
            "Actions",
        ),
        "**_Tail._** _Melee Attack Roll:_ +19, reach 30 ft. _Hit:_ 23 (3d8 + 10) Bludgeoning damage. If the target is a Huge or smaller creature, it has the Prone condition.",
    ),
    (
        (
            "Monsters A–Z",
            "Tarrasque",
            "Tarrasque",
            "Actions",
        ),
        "**_Thunderous Bellow (Recharge 5–6)._** _Constitution Saving Throw:_ DC 27, each creature and each object that isn't being worn or carried in a 150-foot Cone. _Failure:_ 78 (12d12) Thunder damage, and the target has the Deafened and Frightened conditions until the end of its next turn. _Success:_ Half damage only.",
    ),
    (
        (
            "Monsters A–Z",
            "Tarrasque",
            "Tarrasque",
            "Bonus Actions",
        ),
        "#### Bonus Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Tarrasque",
            "Tarrasque",
            "Bonus Actions",
        ),
        "**_Swallow._** _Strength Saving Throw:_ DC 27, one Large or smaller creature Grappled by the tarrasque (it can have up to six creatures swallowed at a time). _Failure:_ The target is swallowed, and the Grappled condition ends. A swallowed creature has the Blinded and Restrained conditions and can't teleport, it has Total Cover against attacks and other effects outside the tarrasque, and it takes 56 (16d6) Acid damage at the start of each of the tarrasque's turns. <br>\n&emsp;If the tarrasque takes 60 damage or more on a single turn from a creature inside it, the tarrasque must succeed on a DC 20 Constitution saving throw at the end of that turn or regurgitate all swallowed creatures, each of which falls in a space within 10 feet of the tarrasque and has the Prone condition. If the tarrasque dies, any swallowed creature no longer has the Restrained condition and can escape from the corpse using 20 feet of movement, exiting Prone.",
    ),
    (
        (
            "Monsters A–Z",
            "Tarrasque",
            "Tarrasque",
            "Legendary Actions",
        ),
        "#### Legendary Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Tarrasque",
            "Tarrasque",
            "Legendary Actions",
        ),
        "_Legendary Action Uses: 3. Immediately after another creature's turn, the tarrasque can expend a use to take one of the following actions. The tarrasque regains all expended uses at the start of each of its turns._",
    ),
    (
        (
            "Monsters A–Z",
            "Tarrasque",
            "Tarrasque",
            "Legendary Actions",
        ),
        "**_Onslaught._** The tarrasque moves up to half its Speed, and it makes one Claw or Tail attack.",
    ),
    (
        (
            "Monsters A–Z",
            "Tarrasque",
            "Tarrasque",
            "Legendary Actions",
        ),
        "**_World-Shaking Movement._** The tarrasque moves up to its Speed. At the end of this movement, the tarrasque creates an instantaneous shock wave in a 60-foot Emanation originating from itself. Creatures in that area lose Concentration and, if Medium or smaller, have the Prone condition. The tarrasque can't take this action again until the start of its next turn.",
    ),
    (
        (
            "Monsters A–Z",
            "Toughs",
        ),
        "## Toughs",
    ),
    (
        (
            "Monsters A–Z",
            "Toughs",
            "Tough",
        ),
        "### Tough",
    ),
    (
        (
            "Monsters A–Z",
            "Toughs",
            "Tough",
        ),
        "_Medium or Small Humanoid, Neutral_",
    ),
    (
        (
            "Monsters A–Z",
            "Toughs",
            "Tough",
        ),
        "**AC** 12 **Initiative** +1 (11) <br>\n**HP** 32 (5d8 + 10) <br>\n**Speed** 30 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Toughs",
            "Tough",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>DEX</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CON</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>WIS</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CHA</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Toughs",
            "Tough",
        ),
        "**Gear** Heavy Crossbow, Leather Armor, Mace<br>\n**Senses** Passive Perception 10<br>\n**Languages** Common<br>\n**CR** 1/2 (XP 100; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Toughs",
            "Tough",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Toughs",
            "Tough",
            "Traits",
        ),
        "**_Pack Tactics._** The tough has Advantage on an attack roll against a creature if at least one of the tough's allies is within 5 feet of the creature and the ally doesn't have the Incapacitated condition.",
    ),
    (
        (
            "Monsters A–Z",
            "Toughs",
            "Tough",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Toughs",
            "Tough",
            "Actions",
        ),
        "**_Mace._** _Melee Attack Roll:_ +4, reach 5 ft. _Hit:_ 5 (1d6 + 2) Bludgeoning damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Toughs",
            "Tough",
            "Actions",
        ),
        "**_Heavy Crossbow._** _Ranged Attack Roll:_ +3, range 100/400 ft. _Hit:_ 6 (1d10 + 1) Piercing damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Toughs",
            "Tough Boss",
        ),
        "### Tough Boss",
    ),
    (
        (
            "Monsters A–Z",
            "Toughs",
            "Tough Boss",
        ),
        "_Medium or Small Humanoid, Neutral_",
    ),
    (
        (
            "Monsters A–Z",
            "Toughs",
            "Tough Boss",
        ),
        "**AC** 16 **Initiative** +2 (12) <br>\n**HP** 82 (11d8 + 33) <br>\n**Speed** 30 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Toughs",
            "Tough Boss",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>17</td>\n      <td>+3</td>\n      <td>+5</td>\n      <td><strong>DEX</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CON</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+5</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>WIS</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CHA</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+2</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Toughs",
            "Tough Boss",
        ),
        "**Gear** Chain Mail, Heavy Crossbow, Warhammer<br>\n**Senses** Passive Perception 10<br>\n**Languages** Common plus one other language<br>\n**CR** 4 (XP 1,100; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Toughs",
            "Tough Boss",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Toughs",
            "Tough Boss",
            "Traits",
        ),
        "**_Pack Tactics._** The tough has Advantage on an attack roll against a creature if at least one of the tough's allies is within 5 feet of the creature and the ally doesn't have the Incapacitated condition.",
    ),
    (
        (
            "Monsters A–Z",
            "Toughs",
            "Tough Boss",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Toughs",
            "Tough Boss",
            "Actions",
        ),
        "**_Multiattack._** The tough makes two attacks, using Warhammer or Heavy Crossbow in any combination.",
    ),
    (
        (
            "Monsters A–Z",
            "Toughs",
            "Tough Boss",
            "Actions",
        ),
        "**_Warhammer._** _Melee Attack Roll:_ +5, reach 5 ft. _Hit:_ 12 (2d8 + 3) Bludgeoning damage. If the target is a Large or smaller creature, the tough pushes the target up to 10 feet straight away from itself.",
    ),
    (
        (
            "Monsters A–Z",
            "Toughs",
            "Tough Boss",
            "Actions",
        ),
        "**_Heavy Crossbow._** _Ranged Attack Roll:_ +4, range 100/400 ft. _Hit:_ 13 (2d10 + 2) Piercing damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Treant",
        ),
        "## Treant",
    ),
    (
        (
            "Monsters A–Z",
            "Treant",
            "Treant",
        ),
        "### Treant",
    ),
    (
        (
            "Monsters A–Z",
            "Treant",
            "Treant",
        ),
        "_Huge Plant, Chaotic Good_",
    ),
    (
        (
            "Monsters A–Z",
            "Treant",
            "Treant",
        ),
        "**AC** 16 **Initiative** +3 (13) <br>\n**HP** 138 (12d12 + 60) <br>\n**Speed** 30 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Treant",
            "Treant",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>23</td>\n      <td>+6</td>\n      <td>+6</td>\n      <td><strong>DEX</strong></td>\n      <td>8</td>\n      <td>−1</td>\n      <td>−1</td>\n      <td><strong>CON</strong></td>\n      <td>21</td>\n      <td>+5</td>\n      <td>+5</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>WIS</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>CHA</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Treant",
            "Treant",
        ),
        "**Vulnerabilities** Fire<br>\n**Resistances** Bludgeoning, Piercing<br>\n**Senses** Passive Perception 13<br>\n**Languages** Common, Druidic, Elvish, Sylvan<br>\n**CR** 9 (XP 5,000; PB +4)",
    ),
    (
        (
            "Monsters A–Z",
            "Treant",
            "Treant",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Treant",
            "Treant",
            "Traits",
        ),
        "**_Siege Monster._** The treant deals double damage to objects and structures.",
    ),
    (
        (
            "Monsters A–Z",
            "Treant",
            "Treant",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Treant",
            "Treant",
            "Actions",
        ),
        "**_Multiattack._** The treant makes two Slam attacks.",
    ),
    (
        (
            "Monsters A–Z",
            "Treant",
            "Treant",
            "Actions",
        ),
        "**_Slam._** _Melee Attack Roll:_ +10, reach 5 ft. _Hit:_ 16 (3d6 + 6) Bludgeoning damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Treant",
            "Treant",
            "Actions",
        ),
        "**_Hail of Bark._** _Ranged Attack Roll:_ +10, range 180 ft. _Hit:_ 28 (4d10 + 6) Piercing damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Treant",
            "Treant",
            "Actions",
        ),
        "**_Animate Trees (1/Day)._** The treant magically animates up to two trees it can see within 60 feet of itself. Each tree uses the Treant stat block, except it has Intelligence and Charisma scores of 1, it can't speak, and it lacks this action. The tree takes its turn immediately after the treant on the same Initiative count, and it obeys the treant. A tree remains animate for 1 day or until it dies, the treant dies, or it is more than 120 feet from the treant. The tree then takes root if possible.",
    ),
    (
        (
            "Monsters A–Z",
            "Troll",
        ),
        "## Troll",
    ),
    (
        (
            "Monsters A–Z",
            "Troll",
            "Troll",
        ),
        "### Troll",
    ),
    (
        (
            "Monsters A–Z",
            "Troll",
            "Troll",
        ),
        "_Large Giant, Chaotic Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Troll",
            "Troll",
        ),
        "**AC** 15 **Initiative** +1 (11) <br>\n**HP** 94 (9d10 + 45) <br>\n**Speed** 30 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Troll",
            "Troll",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+4</td>\n      <td><strong>DEX</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CON</strong></td>\n      <td>20</td>\n      <td>+5</td>\n      <td>+5</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>7</td>\n      <td>−2</td>\n      <td>−2</td>\n      <td><strong>WIS</strong></td>\n      <td>9</td>\n      <td>−1</td>\n      <td>−1</td>\n      <td><strong>CHA</strong></td>\n      <td>7</td>\n      <td>−2</td>\n      <td>−2</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Troll",
            "Troll",
        ),
        "**Skills** Perception +5<br>\n**Senses** Darkvision 60 ft.; Passive Perception 15<br>\n**Languages** Giant<br>\n**CR** 5 (XP 1,800; PB +3)",
    ),
    (
        (
            "Monsters A–Z",
            "Troll",
            "Troll",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Troll",
            "Troll",
            "Traits",
        ),
        "**_Loathsome Limbs (4/Day)._** If the troll ends any turn Bloodied and took 15+ Slashing damage during that turn, one of the troll's limbs is severed, falls into the troll's space, and becomes a **Troll Limb**. The limb acts immediately after the troll's turn. The troll has 1 Exhaustion level for each missing limb, and it grows replacement limbs the next time it regains Hit Points.",
    ),
    (
        (
            "Monsters A–Z",
            "Troll",
            "Troll",
            "Traits",
        ),
        "**_Regeneration._** The troll regains 15 Hit Points at the start of each of its turns. If the troll takes Acid or Fire damage, this trait doesn't function on the troll's next turn. The troll dies only if it starts its turn with 0 Hit Points and doesn't regenerate.",
    ),
    (
        (
            "Monsters A–Z",
            "Troll",
            "Troll",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Troll",
            "Troll",
            "Actions",
        ),
        "**_Multiattack._** The troll makes three Rend attacks.",
    ),
    (
        (
            "Monsters A–Z",
            "Troll",
            "Troll",
            "Actions",
        ),
        "**_Rend._** _Melee Attack Roll:_ +7, reach 10 ft. _Hit:_ 11 (2d6 + 4) Slashing damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Troll",
            "Troll",
            "Bonus Actions",
        ),
        "#### Bonus Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Troll",
            "Troll",
            "Bonus Actions",
        ),
        "**_Charge._** The troll moves up to half its Speed straight toward an enemy it can see.",
    ),
    (
        (
            "Monsters A–Z",
            "Troll",
            "Troll Limb",
        ),
        "### Troll Limb",
    ),
    (
        (
            "Monsters A–Z",
            "Troll",
            "Troll Limb",
        ),
        "_Small Giant, Chaotic Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Troll",
            "Troll Limb",
        ),
        "**AC** 13 **Initiative** +1 (11) <br>\n**HP** 14 (4d6) <br>\n**Speed** 20 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Troll",
            "Troll Limb",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+4</td>\n      <td><strong>DEX</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CON</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>1</td>\n      <td>−5</td>\n      <td>−5</td>\n      <td><strong>WIS</strong></td>\n      <td>9</td>\n      <td>−1</td>\n      <td>−1</td>\n      <td><strong>CHA</strong></td>\n      <td>1</td>\n      <td>−5</td>\n      <td>−5</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Troll",
            "Troll Limb",
        ),
        "**Senses** Darkvision 60 ft.; Passive Perception 9<br>\n**Languages** None<br>\n**CR** 1/2 (XP 100; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Troll",
            "Troll Limb",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Troll",
            "Troll Limb",
            "Traits",
        ),
        "**_Regeneration._** The limb regains 5 Hit Points at the start of each of its turns. If the limb takes Acid or Fire damage, this trait doesn't function on the limb's next turn. The limb dies only if it starts its turn with 0 Hit Points and doesn't regenerate.",
    ),
    (
        (
            "Monsters A–Z",
            "Troll",
            "Troll Limb",
            "Traits",
        ),
        "**_Troll Spawn._** The limb uncannily has the same senses as a whole troll. If the limb isn't destroyed within 24 hours, roll 1d12. On a 12, the limb turns into a **Troll**. Otherwise, the limb withers away.",
    ),
    (
        (
            "Monsters A–Z",
            "Troll",
            "Troll Limb",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Troll",
            "Troll Limb",
            "Actions",
        ),
        "**_Rend._** _Melee Attack Roll:_ +6, reach 5 ft. _Hit:_ 9 (2d4 + 4) Slashing damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Unicorn",
        ),
        "## Unicorn",
    ),
    (
        (
            "Monsters A–Z",
            "Unicorn",
            "Unicorn",
        ),
        "### Unicorn",
    ),
    (
        (
            "Monsters A–Z",
            "Unicorn",
            "Unicorn",
        ),
        "_Large Celestial, Lawful Good_",
    ),
    (
        (
            "Monsters A–Z",
            "Unicorn",
            "Unicorn",
        ),
        "**AC** 12 **Initiative** +8 (18) <br>\n**HP** 97 (13d10 + 26) <br>  \n**Speed** 50 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Unicorn",
            "Unicorn",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+4</td>\n      <td><strong>DEX</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CON</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>WIS</strong></td>\n      <td>17</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>CHA</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Unicorn",
            "Unicorn",
        ),
        "**Immunities** Poison; Charmed, Paralyzed, Poisoned <br>\n**Senses** Darkvision 60 ft.; Passive Perception 13 <br>\n**Languages** Celestial, Elvish, Sylvan; telepathy 120 ft. <br>\n**CR** 5 (XP 1,800; PB +3)",
    ),
    (
        (
            "Monsters A–Z",
            "Unicorn",
            "Unicorn",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Unicorn",
            "Unicorn",
            "Traits",
        ),
        "**_Legendary Resistance (3/Day)._** If the unicorn fails a saving throw, it can choose to succeed instead.",
    ),
    (
        (
            "Monsters A–Z",
            "Unicorn",
            "Unicorn",
            "Traits",
        ),
        "**_Magic Resistance._** The unicorn has Advantage on saving throws against spells and other magical effects.",
    ),
    (
        (
            "Monsters A–Z",
            "Unicorn",
            "Unicorn",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Unicorn",
            "Unicorn",
            "Actions",
        ),
        "**_Multiattack._** The unicorn makes one Hooves attack and one Radiant Horn attack.",
    ),
    (
        (
            "Monsters A–Z",
            "Unicorn",
            "Unicorn",
            "Actions",
        ),
        "**_Hooves._** _Melee Attack Roll:_ +7, reach 5 ft. _Hit:_ 11 (2d6 + 4) Bludgeoning damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Unicorn",
            "Unicorn",
            "Actions",
        ),
        "**_Radiant Horn._** _Melee Attack Roll:_ +7, reach 5 ft. _Hit:_ 9 (1d10 + 4) Radiant damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Unicorn",
            "Unicorn",
            "Actions",
        ),
        "**_Spellcasting._** The unicorn casts one of the following spells, requiring no spell components and using Charisma as the spellcasting ability (spell save DC 14): <br>\n&emsp;**At Will:** _Detect Evil and Good, Druidcraft_ <br>\n&emsp;**1/Day Each:** _Calm Emotions, Dispel Evil and Good, Entangle, Pass without Trace, Word of Recall_",
    ),
    (
        (
            "Monsters A–Z",
            "Unicorn",
            "Unicorn",
            "Bonus Actions",
        ),
        "#### Bonus Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Unicorn",
            "Unicorn",
            "Bonus Actions",
        ),
        "**_Unicorn's Blessing (3/Day)._** The unicorn touches another creature with its horn and casts _Cure Wounds_ or _Lesser Restoration_ on that creature, using the same spellcasting ability as Spellcasting.",
    ),
    (
        (
            "Monsters A–Z",
            "Unicorn",
            "Unicorn",
            "Legendary Actions",
        ),
        "#### Legendary Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Unicorn",
            "Unicorn",
            "Legendary Actions",
        ),
        "_Legendary Action Uses: 3. Immediately after another creature's turn, the unicorn can expend a use to take one of the following actions. The unicorn regains all expended uses at the start of each of its turns._",
    ),
    (
        (
            "Monsters A–Z",
            "Unicorn",
            "Unicorn",
            "Legendary Actions",
        ),
        "**_Charging Horn._** The unicorn moves up to half its Speed without provoking Opportunity Attacks, and it makes one Radiant Horn attack.",
    ),
    (
        (
            "Monsters A–Z",
            "Unicorn",
            "Unicorn",
            "Legendary Actions",
        ),
        "**_Shimmering Shield._** The unicorn targets itself or one creature it can see within 60 feet of itself. The target gains 10 (3d6) Temporary Hit Points, and its AC increases by 2 until the end of the unicorn's next turn. <br>\n&emsp;The unicorn can't take this action again until the start of its next turn.",
    ),
    (
        (
            "Monsters A–Z",
            "Vampires",
        ),
        "## Vampires",
    ),
    (
        (
            "Monsters A–Z",
            "Vampires",
            "Vampire Familiar",
        ),
        "### Vampire Familiar",
    ),
    (
        (
            "Monsters A–Z",
            "Vampires",
            "Vampire Familiar",
        ),
        "_Medium or Small Humanoid, Neutral Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Vampires",
            "Vampire Familiar",
        ),
        "**AC** 15 **Initiative** +5 (15) <br>\n**HP** 65 (10d8 + 20) <br>  \n**Speed** 30 ft., Climb 30 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Vampires",
            "Vampire Familiar",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>17</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>DEX</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+5</td>\n      <td><strong>CON</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>WIS</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+2</td>\n      <td><strong>CHA</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Vampires",
            "Vampire Familiar",
        ),
        "**Skills** Perception +4, Persuasion +4, Stealth +7 <br>\n**Resistances** Necrotic <br>\n**Immunities** Charmed (except from its vampire master) <br>\n**Gear** Daggers (10) <br>\n**Senses** Darkvision 60 ft.; Passive Perception 14 <br>\n**Languages** Common plus one other language <br>\n**CR** 3 (XP 700; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Vampires",
            "Vampire Familiar",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Vampires",
            "Vampire Familiar",
            "Traits",
        ),
        "**_Vampiric Connection._** While the familiar and its vampire master are on the same plane of existence, the vampire can communicate with the familiar telepathically, and the vampire can perceive through the familiar's senses.",
    ),
    (
        (
            "Monsters A–Z",
            "Vampires",
            "Vampire Familiar",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Vampires",
            "Vampire Familiar",
            "Actions",
        ),
        "**_Multiattack._** The familiar makes two Umbral Dagger attacks.",
    ),
    (
        (
            "Monsters A–Z",
            "Vampires",
            "Vampire Familiar",
            "Actions",
        ),
        "**_Umbral Dagger._** _Melee or Ranged Attack Roll:_ +5, reach 5 ft. or range 20/60 ft. _Hit:_ 5 (1d4 + 3) Piercing damage plus 7 (3d4) Necrotic damage. If the target is reduced to 0 Hit Points by this attack, the target becomes Stable but has the Poisoned condition for 1 hour. While it has the Poisoned condition, the target has the Paralyzed condition.",
    ),
    (
        (
            "Monsters A–Z",
            "Vampires",
            "Vampire Familiar",
            "Bonus Actions",
        ),
        "#### Bonus Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Vampires",
            "Vampire Familiar",
            "Bonus Actions",
        ),
        "**_Deathless Agility._** The familiar takes the Dash or Disengage action.",
    ),
    (
        (
            "Monsters A–Z",
            "Vampires",
            "Vampire Spawn",
        ),
        "### Vampire Spawn",
    ),
    (
        (
            "Monsters A–Z",
            "Vampires",
            "Vampire Spawn",
        ),
        "_Medium or Small Undead, Neutral Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Vampires",
            "Vampire Spawn",
        ),
        "**AC** 16 **Initiative** +3 (13) <br>\n**HP** 90 (12d8 + 36) <br>  \n**Speed** 30 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Vampires",
            "Vampire Spawn",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>DEX</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+6</td>\n      <td><strong>CON</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>WIS</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+3</td>\n      <td><strong>CHA</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Vampires",
            "Vampire Spawn",
        ),
        "**Skills** Perception +3, Stealth +6<br>\n**Resistances** Necrotic<br>\n**Senses** Darkvision 60 ft.; Passive Perception 13<br>\n**Languages** Common plus one other language<br>\n**CR** 5 (XP 1,800; PB +3)",
    ),
    (
        (
            "Monsters A–Z",
            "Vampires",
            "Vampire Spawn",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Vampires",
            "Vampire Spawn",
            "Traits",
        ),
        "**_Spider Climb._** The vampire can climb difficult surfaces, including along ceilings, without needing to make an ability check.",
    ),
    (
        (
            "Monsters A–Z",
            "Vampires",
            "Vampire Spawn",
            "Traits",
        ),
        "**_Vampire Weakness._** The vampire has these weaknesses:",
    ),
    (
        (
            "Monsters A–Z",
            "Vampires",
            "Vampire Spawn",
            "Traits",
        ),
        "**_Forbiddance._** The vampire can't enter a residence without an invitation from an occupant.",
    ),
    (
        (
            "Monsters A–Z",
            "Vampires",
            "Vampire Spawn",
            "Traits",
        ),
        "**_Running Water._** The vampire takes 20 Acid damage if it ends its turn in running water.",
    ),
    (
        (
            "Monsters A–Z",
            "Vampires",
            "Vampire Spawn",
            "Traits",
        ),
        "**_Stake to the Heart._** The vampire is destroyed if a weapon that deals Piercing damage is driven into the vampire's heart while the vampire has the Incapacitated condition.",
    ),
    (
        (
            "Monsters A–Z",
            "Vampires",
            "Vampire Spawn",
            "Traits",
        ),
        "**_Sunlight._** The vampire takes 20 Radiant damage if it starts its turn in sunlight. While in sunlight, it has Disadvantage on attack rolls and ability checks.",
    ),
    (
        (
            "Monsters A–Z",
            "Vampires",
            "Vampire Spawn",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Vampires",
            "Vampire Spawn",
            "Actions",
        ),
        "**_Multiattack._** The vampire makes two Claw attacks and uses Bite.",
    ),
    (
        (
            "Monsters A–Z",
            "Vampires",
            "Vampire Spawn",
            "Actions",
        ),
        "**_Claw._** _Melee Attack Roll:_ +6, reach 5 ft. _Hit:_ 8 (2d4 + 3) Slashing damage. If the target is a Medium or smaller creature, it has the Grappled condition (escape DC 13) from one of two claws.",
    ),
    (
        (
            "Monsters A–Z",
            "Vampires",
            "Vampire Spawn",
            "Actions",
        ),
        "**_Bite._** _Constitution Saving Throw:_ DC 14, one creature within 5 feet that is willing or that has the Grappled, Incapacitated, or Restrained condition. _Failure:_ 5 (1d4 + 3) Piercing damage plus 10 (3d6) Necrotic damage. The target's Hit Point maximum decreases by an amount equal to the Necrotic damage taken, and the vampire regains Hit Points equal to that amount.",
    ),
    (
        (
            "Monsters A–Z",
            "Vampires",
            "Vampire Spawn",
            "Bonus Actions",
        ),
        "#### Bonus Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Vampires",
            "Vampire Spawn",
            "Bonus Actions",
        ),
        "**_Deathless Agility._** The vampire takes the Dash or Disengage action.",
    ),
    (
        (
            "Monsters A–Z",
            "Vampires",
            "Vampire",
        ),
        "### Vampire",
    ),
    (
        (
            "Monsters A–Z",
            "Vampires",
            "Vampire",
        ),
        "_Medium or Small Undead, Lawful Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Vampires",
            "Vampire",
        ),
        "**AC** 16 **Initiative** +14 (24) <br>\n**HP** 195 (23d8 + 92) <br>\n**Speed** 40 ft., Climb 40 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Vampires",
            "Vampire",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+4</td>\n      <td><strong>DEX</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+9</td>\n      <td><strong>CON</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+9</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>17</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>WIS</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+7</td>\n      <td><strong>CHA</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+9</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Vampires",
            "Vampire",
        ),
        "**Skills** Perception +7, Stealth +9<br>\n**Resistances** Necrotic<br>\n**Senses** Darkvision 120 ft.; Passive Perception 17<br>\n**Languages** Common plus two other languages<br>\n**CR** 13 (XP 10,000, or 11,500 in lair; PB +5)",
    ),
    (
        (
            "Monsters A–Z",
            "Vampires",
            "Vampire",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Vampires",
            "Vampire",
            "Traits",
        ),
        "**_Legendary Resistance (3/Day, or 4/Day in Lair)._** If the vampire fails a saving throw, it can choose to succeed instead.",
    ),
    (
        (
            "Monsters A–Z",
            "Vampires",
            "Vampire",
            "Traits",
        ),
        "**_Misty Escape._** If the vampire drops to 0 Hit Points outside its resting place, the vampire uses Shape-Shift to become mist (no action required). If it can't use Shape-Shift, it is destroyed. <br>\n&emsp;While it has 0 Hit Points in mist form, it can't return to its vampire form, and it must reach its resting place within 2 hours or be destroyed. Once in its resting place, it returns to its vampire form and has the Paralyzed condition until it regains any Hit Points, and it regains 1 Hit Point after spending 1 hour there.",
    ),
    (
        (
            "Monsters A–Z",
            "Vampires",
            "Vampire",
            "Traits",
        ),
        "**_Spider Climb._** The vampire can climb difficult surfaces, including along ceilings, without needing to make an ability check.",
    ),
    (
        (
            "Monsters A–Z",
            "Vampires",
            "Vampire",
            "Traits",
        ),
        "**_Vampire Weakness._** The vampire has these weaknesses:",
    ),
    (
        (
            "Monsters A–Z",
            "Vampires",
            "Vampire",
            "Traits",
        ),
        "**_Forbiddance._** The vampire can't enter a residence without an invitation from an occupant.",
    ),
    (
        (
            "Monsters A–Z",
            "Vampires",
            "Vampire",
            "Traits",
        ),
        "**_Running Water._** The vampire takes 20 Acid damage if it ends its turn in running water.",
    ),
    (
        (
            "Monsters A–Z",
            "Vampires",
            "Vampire",
            "Traits",
        ),
        "**_Stake to the Heart._** If a weapon that deals Piercing damage is driven into the vampire's heart while the vampire has the Incapacitated condition in its resting place, the vampire has the Paralyzed condition until the weapon is removed.",
    ),
    (
        (
            "Monsters A–Z",
            "Vampires",
            "Vampire",
            "Traits",
        ),
        "**_Sunlight._** The vampire takes 20 Radiant damage if it starts its turn in sunlight. While in sunlight, it has Disadvantage on attack rolls and ability checks.",
    ),
    (
        (
            "Monsters A–Z",
            "Vampires",
            "Vampire",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Vampires",
            "Vampire",
            "Actions",
        ),
        "**_Multiattack (Vampire Form Only)._** The vampire makes two Grave Strike attacks and uses Bite.",
    ),
    (
        (
            "Monsters A–Z",
            "Vampires",
            "Vampire",
            "Actions",
        ),
        "**_Grave Strike (Vampire Form Only)._** _Melee Attack Roll:_ +9, reach 5 ft. _Hit:_ 8 (1d8 + 4) Bludgeoning damage plus 7 (2d6) Necrotic damage. If the target is a Large or smaller creature, it has the Grappled condition (escape DC 14) from one of two hands.",
    ),
    (
        (
            "Monsters A–Z",
            "Vampires",
            "Vampire",
            "Actions",
        ),
        "**_Bite (Bat or Vampire Form Only)._** _Constitution Saving Throw:_ DC 17, one creature within 5 feet that is willing or that has the Grappled, Incapacitated, or Restrained condition. _Failure:_ 6 (1d4 + 4) Piercing damage plus 13 (3d8) Necrotic damage. The target's Hit Point maximum decreases by an amount equal to the Necrotic damage taken, and the vampire regains Hit Points equal to that amount. A Humanoid reduced to 0 Hit Points by this damage and then buried rises the following sunset as a **Vampire Spawn** under the vampire's control.",
    ),
    (
        (
            "Monsters A–Z",
            "Vampires",
            "Vampire",
            "Bonus Actions",
        ),
        "#### Bonus Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Vampires",
            "Vampire",
            "Bonus Actions",
        ),
        "**_Charm (Recharge 5–6)._** The vampire casts _Charm Person_, requiring no spell components and using Charisma as the spellcasting ability (spell save DC 17), and the duration is 24 hours. The Charmed target is a willing recipient of the vampire's Bite, the damage of which doesn't end the spell. When the spell ends, the target is unaware it was Charmed by the vampire.",
    ),
    (
        (
            "Monsters A–Z",
            "Vampires",
            "Vampire",
            "Bonus Actions",
        ),
        "**_Shape-Shift._** If the vampire isn't in sunlight or running water, it shape-shifts into a Tiny bat (Speed 5 ft., Fly Speed 30 ft.) or a Medium cloud of mist (Speed 5 ft., Fly Speed 20 ft. [hover]), or it returns to its vampire form. Anything it is wearing transforms with it. <br>\n&emsp;While in bat form, the vampire can't speak. Its game statistics, other than its size and Speed, are unchanged. <br>\n&emsp;While in mist form, the vampire can't take any actions, speak, or manipulate objects. It is weightless and can enter an enemy's space and stop there. If air can pass through a space, the mist can do so, but it can't pass through liquid. It has Resistance to all damage, except the damage it takes from sunlight.",
    ),
    (
        (
            "Monsters A–Z",
            "Vampires",
            "Vampire",
            "Legendary Actions",
        ),
        "#### Legendary Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Vampires",
            "Vampire",
            "Legendary Actions",
        ),
        "_Legendary Action Uses: 3 (4 in Lair). Immediately after another creature's turn, the vampire can expend a use to take one of the following actions. The vampire regains all expended uses at the start of each of its turns._",
    ),
    (
        (
            "Monsters A–Z",
            "Vampires",
            "Vampire",
            "Legendary Actions",
        ),
        "**_Beguile._** The vampire casts _Command_, requiring no spell components and using Charisma as the spellcasting ability (spell save DC 17). The vampire can't take this action again until the start of its next turn.",
    ),
    (
        (
            "Monsters A–Z",
            "Vampires",
            "Vampire",
            "Legendary Actions",
        ),
        "**_Deathless Strike._** The vampire moves up to half its Speed, and it makes one Grave Strike attack.",
    ),
    (
        (
            "Monsters A–Z",
            "Vrock",
        ),
        "## Vrock",
    ),
    (
        (
            "Monsters A–Z",
            "Vrock",
            "Vrock",
        ),
        "### Vrock",
    ),
    (
        (
            "Monsters A–Z",
            "Vrock",
            "Vrock",
        ),
        "_Large Fiend (Demon), Chaotic Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Vrock",
            "Vrock",
        ),
        "**AC** 15 **Initiative** +2 (12) <br>\n**HP** 152 (16d10 + 64) <br>\n**Speed** 40 ft., Fly 60 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Vrock",
            "Vrock",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>17</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>DEX</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+5</td>\n      <td><strong>CON</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+4</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>8</td>\n      <td>−1</td>\n      <td>−1</td>\n      <td><strong>WIS</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+4</td>\n      <td><strong>CHA</strong></td>\n      <td>8</td>\n      <td>−1</td>\n      <td>+2</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Vrock",
            "Vrock",
        ),
        "**Resistances** Cold, Fire, Lightning<br>\n**Immunities** Poison; Poisoned<br>\n**Senses** Darkvision 120 ft.; Passive Perception 11<br>\n**Languages** Abyssal; telepathy 120 ft.<br>\n**CR** 6 (XP 2,300; PB +3)",
    ),
    (
        (
            "Monsters A–Z",
            "Vrock",
            "Vrock",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Vrock",
            "Vrock",
            "Traits",
        ),
        "**_Demonic Restoration._** If the vrock dies outside the Abyss, its body dissolves into ichor, and it gains a new body instantly, reviving with all its Hit Points somewhere in the Abyss.",
    ),
    (
        (
            "Monsters A–Z",
            "Vrock",
            "Vrock",
            "Traits",
        ),
        "**_Magic Resistance._** The vrock has Advantage on saving throws against spells and other magical effects.",
    ),
    (
        (
            "Monsters A–Z",
            "Vrock",
            "Vrock",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Vrock",
            "Vrock",
            "Actions",
        ),
        "**_Multiattack._** The vrock makes two Shred attacks.",
    ),
    (
        (
            "Monsters A–Z",
            "Vrock",
            "Vrock",
            "Actions",
        ),
        "**_Shred._** _Melee Attack Roll:_ +6, reach 5 ft. _Hit:_ 10 (2d6 + 3) Piercing damage plus 10 (3d6) Poison damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Vrock",
            "Vrock",
            "Actions",
        ),
        "**_Spores (Recharge 6)._** _Constitution Saving Throw:_ DC 15, each creature in a 20-foot Emanation originating from the vrock. _Failure:_ The target has the Poisoned condition and repeats the save at the end of each of its turns, ending the effect on itself on a success. While Poisoned, the target takes 5 (1d10) Poison damage at the start of each of its turns. Emptying a flask of Holy Water on the target ends the effect early.",
    ),
    (
        (
            "Monsters A–Z",
            "Vrock",
            "Vrock",
            "Actions",
        ),
        "**_Stunning Screech (1/Day)._** _Constitution Saving Throw:_ DC 15, each creature in a 20-foot Emanation originating from the vrock (demons succeed automatically). _Failure:_ 10 (3d6) Thunder damage, and the target has the Stunned condition until the end of the vrock's next turn.",
    ),
    (
        (
            "Monsters A–Z",
            "Warriors",
        ),
        "## Warriors",
    ),
    (
        (
            "Monsters A–Z",
            "Warriors",
            "Warrior Infantry",
        ),
        "### Warrior Infantry",
    ),
    (
        (
            "Monsters A–Z",
            "Warriors",
            "Warrior Infantry",
        ),
        "_Medium or Small Humanoid, Neutral_",
    ),
    (
        (
            "Monsters A–Z",
            "Warriors",
            "Warrior Infantry",
        ),
        "**AC** 13 **Initiative** +0 (10) <br>\n**HP** 9 (2d8) <br>\n**Speed** 30 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Warriors",
            "Warrior Infantry",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>DEX</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CON</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>8</td>\n      <td>−1</td>\n      <td>−1</td>\n      <td><strong>WIS</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CHA</strong></td>\n      <td>8</td>\n      <td>−1</td>\n      <td>−1</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Warriors",
            "Warrior Infantry",
        ),
        "**Gear** Chain Shirt, Spear<br>\n**Senses** Passive Perception 10<br>\n**Languages** Common<br>\n**CR** 1/8 (XP 25; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Warriors",
            "Warrior Infantry",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Warriors",
            "Warrior Infantry",
            "Traits",
        ),
        "**_Pack Tactics._** The warrior has Advantage on an attack roll against a creature if at least one of the warrior's allies is within 5 feet of the creature and the ally doesn't have the Incapacitated condition.",
    ),
    (
        (
            "Monsters A–Z",
            "Warriors",
            "Warrior Infantry",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Warriors",
            "Warrior Infantry",
            "Actions",
        ),
        "**_Spear._** _Melee or Ranged Attack Roll:_ +3, reach 5 ft. or range 20/60 ft. _Hit:_ 4 (1d6 + 1) Piercing damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Warriors",
            "Veteran Warrior",
        ),
        "### Veteran Warrior",
    ),
    (
        (
            "Monsters A–Z",
            "Warriors",
            "Veteran Warrior",
        ),
        "_Medium or Small Humanoid, Neutral_",
    ),
    (
        (
            "Monsters A–Z",
            "Warriors",
            "Veteran Warrior",
        ),
        "**AC** 17 **Initiative** +3 (13) <br>\n**HP** 65 (10d8 + 20) <br>\n**Speed** 30 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Warriors",
            "Veteran Warrior",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>DEX</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CON</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>WIS</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CHA</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Warriors",
            "Veteran Warrior",
        ),
        "**Skills** Athletics +5, Perception +2<br>\n**Gear** Greatsword, Heavy Crossbow, Splint Armor<br>\n**Senses** Passive Perception 12<br>\n**Languages** Common plus one other language<br>\n**CR** 3 (XP 700; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Warriors",
            "Veteran Warrior",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Warriors",
            "Veteran Warrior",
            "Actions",
        ),
        "**_Multiattack._** The warrior makes two Greatsword or Heavy Crossbow attacks.",
    ),
    (
        (
            "Monsters A–Z",
            "Warriors",
            "Veteran Warrior",
            "Actions",
        ),
        "**_Greatsword._** _Melee Attack Roll:_ +5, reach 5 ft. _Hit:_ 10 (2d6 + 3) Slashing damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Warriors",
            "Veteran Warrior",
            "Actions",
        ),
        "**_Heavy Crossbow._** _Ranged Attack Roll:_ +3, range 100/400 ft. _Hit:_ 12 (2d10 + 1) Piercing damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Warriors",
            "Veteran Warrior",
            "Reactions",
        ),
        "#### Reactions",
    ),
    (
        (
            "Monsters A–Z",
            "Warriors",
            "Veteran Warrior",
            "Reactions",
        ),
        "**_Parry._** _Trigger:_ The warrior is hit by a melee attack roll while holding a weapon. _Response:_ The warrior adds 2 to its AC against that attack, possibly causing it to miss.",
    ),
    (
        (
            "Monsters A–Z",
            "Water Elemental",
        ),
        "## Water Elemental",
    ),
    (
        (
            "Monsters A–Z",
            "Water Elemental",
            "Water Elemental",
        ),
        "### Water Elemental",
    ),
    (
        (
            "Monsters A–Z",
            "Water Elemental",
            "Water Elemental",
        ),
        "_Large Elemental, Neutral_",
    ),
    (
        (
            "Monsters A–Z",
            "Water Elemental",
            "Water Elemental",
        ),
        "**AC** 14 **Initiative** +2 (12) <br>\n**HP** 114 (12d10 + 48) <br>\n**Speed** 30 ft., Swim 90 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Water Elemental",
            "Water Elemental",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+4</td>\n      <td><strong>DEX</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CON</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+4</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>5</td>\n      <td>−3</td>\n      <td>−3</td>\n      <td><strong>WIS</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CHA</strong></td>\n      <td>8</td>\n      <td>−1</td>\n      <td>−1</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Water Elemental",
            "Water Elemental",
        ),
        "**Resistances** Acid, Fire<br>\n**Immunities** Poison; Exhaustion, Grappled, Paralyzed, Petrified, Poisoned, Prone, Restrained, Unconscious<br>\n**Senses** Darkvision 60 ft.; Passive Perception 10<br>\n**Languages** Primordial (Aquan)<br>\n**CR** 5 (XP 1,800; PB +3)",
    ),
    (
        (
            "Monsters A–Z",
            "Water Elemental",
            "Water Elemental",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Water Elemental",
            "Water Elemental",
            "Traits",
        ),
        "**_Freeze._** If the elemental takes Cold damage, its Speed decreases by 20 feet until the end of its next turn.",
    ),
    (
        (
            "Monsters A–Z",
            "Water Elemental",
            "Water Elemental",
            "Traits",
        ),
        "**_Water Form._** The elemental can enter an enemy's space and stop there. It can move through a space as narrow as 1 inch without expending extra movement to do so.",
    ),
    (
        (
            "Monsters A–Z",
            "Water Elemental",
            "Water Elemental",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Water Elemental",
            "Water Elemental",
            "Actions",
        ),
        "**_Multiattack._** The elemental makes two Slam attacks.",
    ),
    (
        (
            "Monsters A–Z",
            "Water Elemental",
            "Water Elemental",
            "Actions",
        ),
        "**_Slam._** _Melee Attack Roll:_ +7, reach 5 ft. _Hit:_ 13 (2d8 + 4) Bludgeoning damage. If the target is a Medium or smaller creature, it has the Prone condition.",
    ),
    (
        (
            "Monsters A–Z",
            "Water Elemental",
            "Water Elemental",
            "Actions",
        ),
        "**_Whelm (Recharge 4–6)._** _Strength Saving Throw:_ DC 15, each creature in the elemental's space. _Failure:_ 22 (4d8 + 4) Bludgeoning damage. If the target is a Large or smaller creature, it has the Grappled condition (escape DC 14). Until the grapple ends, the target has the Restrained condition, is suffocating unless it can breathe water, and takes 9 (2d8) Bludgeoning damage at the start of each of the elemental's turns. The elemental can grapple one Large creature or up to two Medium or smaller creatures at a time with Whelm. As an action, a creature within 5 feet of the elemental can pull a creature out of it by succeeding on a DC 14 Strength (Athletics) check. _Success:_ Half damage only.",
    ),
    (
        (
            "Monsters A–Z",
            "Werebear",
        ),
        "## Werebear",
    ),
    (
        (
            "Monsters A–Z",
            "Werebear",
            "Werebear",
        ),
        "### Werebear",
    ),
    (
        (
            "Monsters A–Z",
            "Werebear",
            "Werebear",
        ),
        "_Medium or Small Monstrosity (Lycanthrope), Neutral Good_",
    ),
    (
        (
            "Monsters A–Z",
            "Werebear",
            "Werebear",
        ),
        "**AC** 15 **Initiative** +3 (13) <br>\n**HP** 135 (18d8 + 54) <br>\n**Speed** 30 ft., 40 ft. (bear form only), Climb 30 ft. (bear form only) <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Werebear",
            "Werebear",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>19</td>\n      <td>+4</td>\n      <td>+4</td>\n      <td><strong>DEX</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CON</strong></td>\n      <td>17</td>\n      <td>+3</td>\n      <td>+3</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>WIS</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CHA</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Werebear",
            "Werebear",
        ),
        "**Skills** Perception +7<br>\n**Gear** Handaxes (4)<br>\n**Senses** Darkvision 60 ft.; Passive Perception 17<br>\n**Languages** Common (can't speak in bear form)<br>\n**CR** 5 (XP 1,800; PB +3)",
    ),
    (
        (
            "Monsters A–Z",
            "Werebear",
            "Werebear",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Werebear",
            "Werebear",
            "Actions",
        ),
        "**_Multiattack._** The werebear makes two attacks, using Handaxe or Rend in any combination. It can replace one attack with a Bite attack.",
    ),
    (
        (
            "Monsters A–Z",
            "Werebear",
            "Werebear",
            "Actions",
        ),
        "**_Bite (Bear or Hybrid Form Only)._** _Melee Attack Roll:_ +7, reach 5 ft. _Hit:_ 17 (2d12 + 4) Piercing damage. If the target is a Humanoid, it is subjected to the following effect. _Constitution Saving Throw:_ DC 14. _Failure:_ The target is cursed. If the cursed target drops to 0 Hit Points, it instead becomes a **Werebear** under the GM's control and has 10 Hit Points. _Success:_ The target is immune to this werebear's curse for 24 hours.",
    ),
    (
        (
            "Monsters A–Z",
            "Werebear",
            "Werebear",
            "Actions",
        ),
        "**_Handaxe (Humanoid or Hybrid Form Only)._** Melee or _Ranged Attack Roll:_ +7, reach 5 ft or range 20/60 ft. _Hit:_ 14 (3d6 + 4) Slashing damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Werebear",
            "Werebear",
            "Actions",
        ),
        "**_Rend (Bear or Hybrid Form Only)._** _Melee Attack Roll:_ +7, reach 5 ft. _Hit:_ 13 (2d8 + 4) Slashing damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Werebear",
            "Werebear",
            "Bonus Actions",
        ),
        "#### Bonus Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Werebear",
            "Werebear",
            "Bonus Actions",
        ),
        "**_Shape-Shift._** The werebear shape-shifts into a Large bear-humanoid hybrid form or a Large bear, or it returns to its true humanoid form. Its game statistics, other than its size, are the same in each form. Any equipment it is wearing or carrying isn't transformed.",
    ),
    (
        (
            "Monsters A–Z",
            "Wereboar",
        ),
        "## Wereboar",
    ),
    (
        (
            "Monsters A–Z",
            "Wereboar",
            "Wereboar",
        ),
        "### Wereboar",
    ),
    (
        (
            "Monsters A–Z",
            "Wereboar",
            "Wereboar",
        ),
        "_Medium or Small Monstrosity (Lycanthrope), Neutral Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Wereboar",
            "Wereboar",
        ),
        "**AC** 15 **Initiative** +2 (12) <br>\n**HP** 97 (15d8 + 30) <br>\n**Speed** 30 ft., 40 ft. (boar form only) <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Wereboar",
            "Wereboar",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>17</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>DEX</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CON</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>WIS</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CHA</strong></td>\n      <td>8</td>\n      <td>−1</td>\n      <td>−1</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Wereboar",
            "Wereboar",
        ),
        "**Skills** Perception +2<br>\n**Gear** Javelins (6)<br>\n**Senses** Passive Perception 12<br>\n**Languages** Common (can't speak in boar form)<br>\n**CR** 4 (XP 1,100; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Wereboar",
            "Wereboar",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Wereboar",
            "Wereboar",
            "Actions",
        ),
        "**_Multiattack._** The wereboar makes two attacks, using Javelin or Tusk in any combination. It can replace one attack with a Gore attack.",
    ),
    (
        (
            "Monsters A–Z",
            "Wereboar",
            "Wereboar",
            "Actions",
        ),
        "**_Gore (Boar or Hybrid Form Only)._** _Melee Attack Roll:_ +5, reach 5 ft. _Hit:_ 12 (2d8 + 3) Piercing damage. If the target is a Humanoid, it is subjected to the following effect. _Constitution Saving Throw:_ DC 12. _Failure:_ The target is cursed. If the cursed target drops to 0 Hit Points, it instead becomes a **Wereboar** under the GM's control and has 10 Hit Points. _Success:_ The target is immune to this wereboar's curse for 24 hours.",
    ),
    (
        (
            "Monsters A–Z",
            "Wereboar",
            "Wereboar",
            "Actions",
        ),
        "**_Javelin (Humanoid or Hybrid Form Only)._** Melee or _Ranged Attack Roll:_ +5, reach 5 ft. or range 30/120 ft. _Hit:_ 13 (3d6 + 3) Piercing damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Wereboar",
            "Wereboar",
            "Actions",
        ),
        "**_Tusk (Boar or Hybrid Form Only)._** _Melee Attack Roll:_ +5, reach 5 ft. _Hit:_ 10 (2d6 + 3) Piercing damage. If the target is a Medium or smaller creature and the wereboar moved 20+ feet straight toward it immediately before the hit, the target takes an extra 7 (2d6) Piercing damage and has the Prone condition.",
    ),
    (
        (
            "Monsters A–Z",
            "Wereboar",
            "Wereboar",
            "Bonus Actions",
        ),
        "#### Bonus Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Wereboar",
            "Wereboar",
            "Bonus Actions",
        ),
        "**_Shape-Shift._** The wereboar shape-shifts into a Medium boar-humanoid hybrid or a Small boar, or it returns to its true humanoid form. Its game statistics, other than its size, are the same in each form. Any equipment it is wearing or carrying isn't transformed.",
    ),
    (
        (
            "Monsters A–Z",
            "Wererat",
        ),
        "## Wererat",
    ),
    (
        (
            "Monsters A–Z",
            "Wererat",
            "Wererat",
        ),
        "### Wererat",
    ),
    (
        (
            "Monsters A–Z",
            "Wererat",
            "Wererat",
        ),
        "_Medium or Small Monstrosity (Lycanthrope), Lawful Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Wererat",
            "Wererat",
        ),
        "**AC** 13 **Initiative** +3 (13) <br>\n**HP** 60 (11d8 + 11) <br>\n**Speed** 30 ft., Climb 30 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Wererat",
            "Wererat",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>DEX</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>CON</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>WIS</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CHA</strong></td>\n      <td>8</td>\n      <td>−1</td>\n      <td>−1</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Wererat",
            "Wererat",
        ),
        "**Skills** Perception +4, Stealth +5<br>\n**Gear** Hand Crossbow<br>\n**Senses** Darkvision 60 ft.; Passive Perception 14<br>\n**Languages** Common (can't speak in rat form)<br>\n**CR** 2 (XP 450; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Wererat",
            "Wererat",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Wererat",
            "Wererat",
            "Actions",
        ),
        "**_Multiattack._** The wererat makes two attacks, using Scratch or Hand Crossbow in any combination. It can replace one attack with a Bite attack.",
    ),
    (
        (
            "Monsters A–Z",
            "Wererat",
            "Wererat",
            "Actions",
        ),
        "**_Bite (Rat or Hybrid Form Only)._** _Melee Attack Roll:_ +5, reach 5 ft. _Hit:_ 8 (2d4 + 3) Piercing damage. If the target is a Humanoid, it is subjected to the following effect. _Constitution Saving Throw:_ DC 11. _Failure:_ The target is cursed. If the cursed target drops to 0 Hit Points, it instead becomes a **Wererat** under the GM's control and has 10 Hit Points. _Success:_ The target is immune to this wererat's curse for 24 hours.",
    ),
    (
        (
            "Monsters A–Z",
            "Wererat",
            "Wererat",
            "Actions",
        ),
        "**_Scratch._** _Melee Attack Roll:_ +5, reach 5 ft. _Hit:_ 6 (1d6 + 3) Slashing damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Wererat",
            "Wererat",
            "Actions",
        ),
        "**_Hand Crossbow (Humanoid or Hybrid Form Only)._** _Ranged Attack Roll:_ +5, range 30/120 ft. _Hit:_ 6 (1d6 + 3) Piercing damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Wererat",
            "Wererat",
            "Bonus Actions",
        ),
        "#### Bonus Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Wererat",
            "Wererat",
            "Bonus Actions",
        ),
        "**_Shape-Shift._** The wererat shape-shifts into a Medium rat-humanoid hybrid or a Small rat, or it returns to its true humanoid form. Its game statistics, other than its size, are the same in each form. Any equipment it is wearing or carrying isn't transformed.",
    ),
    (
        (
            "Monsters A–Z",
            "Weretiger",
        ),
        "## Weretiger",
    ),
    (
        (
            "Monsters A–Z",
            "Weretiger",
            "Weretiger",
        ),
        "### Weretiger",
    ),
    (
        (
            "Monsters A–Z",
            "Weretiger",
            "Weretiger",
        ),
        "_Medium or Small Monstrosity (Lycanthrope), Neutral_",
    ),
    (
        (
            "Monsters A–Z",
            "Weretiger",
            "Weretiger",
        ),
        "**AC** 12 **Initiative** +2 (12) <br>\n**HP** 120 (16d8 + 48) <br>\n**Speed** 30 ft., 40 ft. (tiger form only) <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Weretiger",
            "Weretiger",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>17</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>DEX</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CON</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>WIS</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CHA</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Weretiger",
            "Weretiger",
        ),
        "**Skills** Perception +5, Stealth +4<br>\n**Gear** Longbow<br>\n**Senses** Darkvision 60 ft.; Passive Perception 15<br>\n**Languages** Common (can't speak in tiger form)<br>\n**CR** 4 (XP 1,100; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Weretiger",
            "Weretiger",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Weretiger",
            "Weretiger",
            "Actions",
        ),
        "**_Multiattack._** The weretiger makes two attacks, using Scratch or Longbow in any combination. It can replace one attack with a Bite attack.",
    ),
    (
        (
            "Monsters A–Z",
            "Weretiger",
            "Weretiger",
            "Actions",
        ),
        "**_Bite (Tiger or Hybrid Form Only)._** _Melee Attack Roll:_ +5, reach 5 ft. _Hit:_ 12 (2d8 + 3) Piercing damage. If the target is a Humanoid, it is subjected to the following effect. _Constitution Saving Throw:_ DC 13. _Failure:_ The target is cursed. If the cursed target drops to 0 Hit Points, it instead becomes a **Weretiger** under the GM's control and has 10 Hit Points. _Success:_ The target is immune to this weretiger's curse for 24 hours.",
    ),
    (
        (
            "Monsters A–Z",
            "Weretiger",
            "Weretiger",
            "Actions",
        ),
        "**_Scratch._** _Melee Attack Roll:_ +5, reach 5 ft. _Hit:_ 10 (2d6 + 3) Slashing damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Weretiger",
            "Weretiger",
            "Actions",
        ),
        "**_Longbow (Humanoid or Hybrid Form Only)._** _Ranged Attack Roll:_ +4, range 150/600 ft. _Hit:_ 11 (2d8 + 2) Piercing damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Weretiger",
            "Weretiger",
            "Bonus Actions",
        ),
        "#### Bonus Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Weretiger",
            "Weretiger",
            "Bonus Actions",
        ),
        "**_Prowl (Tiger or Hybrid Form Only)._** The weretiger moves up to its Speed without provoking Opportunity Attacks. At the end of this movement, the weretiger can take the Hide action.",
    ),
    (
        (
            "Monsters A–Z",
            "Weretiger",
            "Weretiger",
            "Bonus Actions",
        ),
        "**_Shape-Shift._** The weretiger shape-shifts into a Large tiger-humanoid hybrid or a Large tiger, or it returns to its true humanoid form. Its game statistics, other than its size, are the same in each form. Any equipment it is wearing or carrying isn't transformed.",
    ),
    (
        (
            "Monsters A–Z",
            "Werewolf",
        ),
        "## Werewolf",
    ),
    (
        (
            "Monsters A–Z",
            "Werewolf",
            "Werewolf",
        ),
        "### Werewolf",
    ),
    (
        (
            "Monsters A–Z",
            "Werewolf",
            "Werewolf",
        ),
        "_Medium or Small Monstrosity (Lycanthrope), Chaotic Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Werewolf",
            "Werewolf",
        ),
        "**AC** 15 **Initiative** +4 (14) <br>\n**HP** 71 (11d8 + 22) <br>\n**Speed** 30 ft., 40 ft. (wolf form only) <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Werewolf",
            "Werewolf",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>DEX</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CON</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>WIS</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CHA</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Werewolf",
            "Werewolf",
        ),
        "**Skills** Perception +4, Stealth +4<br>\n**Gear** Longbow<br>\n**Senses** Darkvision 60 ft.; Passive Perception 14<br>\n**Languages** Common (can't speak in wolf form)<br>\n**CR** 3 (XP 700; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Werewolf",
            "Werewolf",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Werewolf",
            "Werewolf",
            "Traits",
        ),
        "**_Pack Tactics._** The werewolf has Advantage on an attack roll against a creature if at least one of the werewolf's allies is within 5 feet of the creature and the ally doesn't have the Incapacitated condition.",
    ),
    (
        (
            "Monsters A–Z",
            "Werewolf",
            "Werewolf",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Werewolf",
            "Werewolf",
            "Actions",
        ),
        "**_Multiattack._** The werewolf makes two attacks, using Scratch or Longbow in any combination. It can replace one attack with a Bite attack.",
    ),
    (
        (
            "Monsters A–Z",
            "Werewolf",
            "Werewolf",
            "Actions",
        ),
        "**_Bite (Wolf or Hybrid Form Only)._** _Melee Attack Roll:_ +5, reach 5 ft. _Hit:_ 12 (2d8 + 3) Piercing damage. If the target is a Humanoid, it is subjected to the following effect. _Constitution Saving Throw:_ DC 12. _Failure:_ The target is cursed. If the cursed target drops to 0 Hit Points, it instead becomes a **Werewolf** under the GM's control and has 10 Hit Points. _Success:_ The target is immune to this werewolf's curse for 24 hours.",
    ),
    (
        (
            "Monsters A–Z",
            "Werewolf",
            "Werewolf",
            "Actions",
        ),
        "**_Scratch._** _Melee Attack Roll:_ +5, reach 5 ft. _Hit:_ 10 (2d6 + 3) Slashing damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Werewolf",
            "Werewolf",
            "Actions",
        ),
        "**_Longbow (Humanoid or Hybrid Form Only)._** _Ranged Attack Roll:_ +4, range 150/600 ft. _Hit:_ 11 (2d8 + 2) Piercing damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Werewolf",
            "Werewolf",
            "Bonus Actions",
        ),
        "#### Bonus Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Werewolf",
            "Werewolf",
            "Bonus Actions",
        ),
        "**_Shape-Shift._** The werewolf shape-shifts into a Large wolf-humanoid hybrid or a Medium wolf, or it returns to its true humanoid form. Its game statistics, other than its size, are the same in each form. Any equipment it is wearing or carrying isn't transformed.",
    ),
    (
        (
            "Monsters A–Z",
            "White Dragons",
        ),
        "## White Dragons",
    ),
    (
        (
            "Monsters A–Z",
            "White Dragons",
            "White Dragon Wyrmling",
        ),
        "### White Dragon Wyrmling",
    ),
    (
        (
            "Monsters A–Z",
            "White Dragons",
            "White Dragon Wyrmling",
        ),
        "_Medium Dragon (Chromatic), Chaotic Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "White Dragons",
            "White Dragon Wyrmling",
        ),
        "**AC** 16 **Initiative** +2 (12) <br>\n**HP** 32 (5d8 + 10) <br>\n**Speed** 30 ft., Burrow 15 ft., Fly 60 ft., Swim 30 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "White Dragons",
            "White Dragon Wyrmling",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>DEX</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+2</td>\n      <td><strong>CON</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>5</td>\n      <td>−3</td>\n      <td>−3</td>\n      <td><strong>WIS</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+2</td>\n      <td><strong>CHA</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "White Dragons",
            "White Dragon Wyrmling",
        ),
        "**Skills** Perception +4, Stealth +2<br>\n**Immunities** Cold<br>\n**Senses** Blindsight 10 ft., Darkvision 60 ft.; Passive Perception 14<br>\n**Languages** Draconic<br>\n**CR** 2 (450 XP; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "White Dragons",
            "White Dragon Wyrmling",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "White Dragons",
            "White Dragon Wyrmling",
            "Traits",
        ),
        "**_Ice Walk._** The dragon can move across and climb icy surfaces without needing to make an ability check. Additionally, Difficult Terrain composed of ice or snow doesn't cost it extra movement.",
    ),
    (
        (
            "Monsters A–Z",
            "White Dragons",
            "White Dragon Wyrmling",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "White Dragons",
            "White Dragon Wyrmling",
            "Actions",
        ),
        "**_Multiattack._** The dragon makes two Rend attacks.",
    ),
    (
        (
            "Monsters A–Z",
            "White Dragons",
            "White Dragon Wyrmling",
            "Actions",
        ),
        "**_Rend._** _Melee Attack Roll:_ +4, reach 5 ft. _Hit:_ 6 (1d8 + 2) Slashing damage plus 2 (1d4) Cold damage.",
    ),
    (
        (
            "Monsters A–Z",
            "White Dragons",
            "White Dragon Wyrmling",
            "Actions",
        ),
        "**_Cold Breath (Recharge 5–6)._** _Constitution Saving Throw:_ DC 12, each creature in a 15-foot Cone. _Failure:_ 22 (5d8) Cold damage. _Success:_ Half damage.",
    ),
    (
        (
            "Monsters A–Z",
            "White Dragons",
            "Young White Dragon",
        ),
        "### Young White Dragon",
    ),
    (
        (
            "Monsters A–Z",
            "White Dragons",
            "Young White Dragon",
        ),
        "_Large Dragon (Chromatic), Chaotic Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "White Dragons",
            "Young White Dragon",
        ),
        "**AC** 17 **Initiative** +3 (13) <br>\n**HP** 123 (13d10 + 52) <br>\n**Speed** 40 ft., Burrow 20 ft., Fly 80 ft., Swim 40 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "White Dragons",
            "Young White Dragon",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+4</td>\n      <td><strong>DEX</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+3</td>\n      <td><strong>CON</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+4</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>6</td>\n      <td>−2</td>\n      <td>−2</td>\n      <td><strong>WIS</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+3</td>\n      <td><strong>CHA</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "White Dragons",
            "Young White Dragon",
        ),
        "**Skills** Perception +6, Stealth +3<br>\n**Immunities** Cold<br>\n**Senses** Blindsight 30 ft., Darkvision 120 ft.; Passive Perception 16<br>\n**Languages** Common, Draconic<br>\n**CR** 6 (2,300 XP; PB +3)",
    ),
    (
        (
            "Monsters A–Z",
            "White Dragons",
            "Young White Dragon",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "White Dragons",
            "Young White Dragon",
            "Traits",
        ),
        "**_Ice Walk._** The dragon can move across and climb icy surfaces without needing to make an ability check. Additionally, Difficult Terrain composed of ice or snow doesn't cost it extra movement.",
    ),
    (
        (
            "Monsters A–Z",
            "White Dragons",
            "Young White Dragon",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "White Dragons",
            "Young White Dragon",
            "Actions",
        ),
        "**_Multiattack._** The dragon makes three Rend attacks.",
    ),
    (
        (
            "Monsters A–Z",
            "White Dragons",
            "Young White Dragon",
            "Actions",
        ),
        "**_Rend._** _Melee Attack Roll:_ +7, reach 10 ft. _Hit:_ 9 (2d4 + 4) Slashing damage plus 2 (1d4) Cold damage.",
    ),
    (
        (
            "Monsters A–Z",
            "White Dragons",
            "Young White Dragon",
            "Actions",
        ),
        "**_Cold Breath (Recharge 5–6)._** _Constitution Saving Throw:_ DC 15, each creature in a 30-foot Cone. _Failure:_ 40 (9d8) Cold damage. _Success:_ Half damage.",
    ),
    (
        (
            "Monsters A–Z",
            "White Dragons",
            "Adult White Dragon",
        ),
        "### Adult White Dragon",
    ),
    (
        (
            "Monsters A–Z",
            "White Dragons",
            "Adult White Dragon",
        ),
        "_Huge Dragon (Chromatic), Chaotic Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "White Dragons",
            "Adult White Dragon",
        ),
        "**AC** 18 **Initiative** +10 (20) <br>\n**HP** 200 (16d12 + 96) <br>\n**Speed** 40 ft., Burrow 30 ft., Fly 80 ft., Swim 40 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "White Dragons",
            "Adult White Dragon",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>22</td>\n      <td>+6</td>\n      <td>+6</td>\n      <td><strong>DEX</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+5</td>\n      <td><strong>CON</strong></td>\n      <td>22</td>\n      <td>+6</td>\n      <td>+6</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>8</td>\n      <td>−1</td>\n      <td>−1</td>\n      <td><strong>WIS</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+6</td>\n      <td><strong>CHA</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "White Dragons",
            "Adult White Dragon",
        ),
        "**Skills** Perception +11, Stealth +5<br>\n**Immunities** Cold<br>\n**Senses** Blindsight 60 ft., Darkvision 120 ft.; Passive Perception 21<br>\n**Languages** Common, Draconic<br>\n**CR** 13 (XP 10,000, or 11,500 in lair; PB +5)",
    ),
    (
        (
            "Monsters A–Z",
            "White Dragons",
            "Adult White Dragon",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "White Dragons",
            "Adult White Dragon",
            "Traits",
        ),
        "**_Ice Walk._** The dragon can move across and climb icy surfaces without needing to make an ability check. Additionally, Difficult Terrain composed of ice or snow doesn't cost it extra movement.",
    ),
    (
        (
            "Monsters A–Z",
            "White Dragons",
            "Adult White Dragon",
            "Traits",
        ),
        "**_Legendary Resistance (3/Day, or 4/Day in Lair)._** If the dragon fails a saving throw, it can choose to succeed instead.",
    ),
    (
        (
            "Monsters A–Z",
            "White Dragons",
            "Adult White Dragon",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "White Dragons",
            "Adult White Dragon",
            "Actions",
        ),
        "**_Multiattack._** The dragon makes three Rend attacks.",
    ),
    (
        (
            "Monsters A–Z",
            "White Dragons",
            "Adult White Dragon",
            "Actions",
        ),
        "**_Rend._** _Melee Attack Roll:_ +11, reach 10 ft. _Hit:_ 13 (2d6 + 6) Slashing damage plus 4 (1d8) Cold damage.",
    ),
    (
        (
            "Monsters A–Z",
            "White Dragons",
            "Adult White Dragon",
            "Actions",
        ),
        "**_Cold Breath (Recharge 5–6)._** _Constitution Saving Throw:_ DC 19, each creature in a 60-foot Cone. _Failure:_ 54 (12d8) Cold damage. _Success:_ Half damage.",
    ),
    (
        (
            "Monsters A–Z",
            "White Dragons",
            "Adult White Dragon",
            "Legendary Actions",
        ),
        "#### Legendary Actions",
    ),
    (
        (
            "Monsters A–Z",
            "White Dragons",
            "Adult White Dragon",
            "Legendary Actions",
        ),
        "_Legendary Action Uses: 3 (4 in Lair). Immediately after another creature's turn, the dragon can expend a use to take one of the following actions. The dragon regains all expended uses at the start of each of its turns._",
    ),
    (
        (
            "Monsters A–Z",
            "White Dragons",
            "Adult White Dragon",
            "Legendary Actions",
        ),
        "**_Freezing Burst._** _Constitution Saving Throw:_ DC 14, each creature in a 30-foot-radius Sphere centered on a point the dragon can see within 120 feet. _Failure:_ 7 (2d6) Cold damage, and the target's Speed is 0 until the end of the target's next turn. _Failure or Success:_ The dragon can't take this action again until the start of its next turn.",
    ),
    (
        (
            "Monsters A–Z",
            "White Dragons",
            "Adult White Dragon",
            "Legendary Actions",
        ),
        "**_Frightful Presence._** The dragon casts _Fear_, requiring no Material components and using Charisma as the spellcasting ability (spell save DC 14). The dragon can't take this action again until the start of its next turn.",
    ),
    (
        (
            "Monsters A–Z",
            "White Dragons",
            "Adult White Dragon",
            "Legendary Actions",
        ),
        "**_Pounce._** The dragon moves up to half its Speed, and it makes one Rend attack.",
    ),
    (
        (
            "Monsters A–Z",
            "White Dragons",
            "Ancient White Dragon",
        ),
        "### Ancient White Dragon",
    ),
    (
        (
            "Monsters A–Z",
            "White Dragons",
            "Ancient White Dragon",
        ),
        "_Gargantuan Dragon (Chromatic), Chaotic Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "White Dragons",
            "Ancient White Dragon",
        ),
        "**AC** 20 **Initiative** +12 (22) <br>\n**HP** 333 (18d20 + 144) <br>\n**Speed** 40 ft., Burrow 40 ft., Fly 80 ft., Swim 40 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "White Dragons",
            "Ancient White Dragon",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>26</td>\n      <td>+8</td>\n      <td>+8</td>\n      <td><strong>DEX</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+6</td>\n      <td><strong>CON</strong></td>\n      <td>26</td>\n      <td>+8</td>\n      <td>+8</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>WIS</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+7</td>\n      <td><strong>CHA</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+4</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "White Dragons",
            "Ancient White Dragon",
        ),
        "**Skills** Perception +13, Stealth +6<br>\n**Immunities** Cold<br>\n**Senses** Blindsight 60 ft., Darkvision 120 ft.; Passive Perception 23<br>\n**Languages** Common, Draconic<br>\n**CR** 20 (XP 25,000, or 33,000 in lair; PB +6)",
    ),
    (
        (
            "Monsters A–Z",
            "White Dragons",
            "Ancient White Dragon",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "White Dragons",
            "Ancient White Dragon",
            "Traits",
        ),
        "**_Ice Walk._** The dragon can move across and climb icy surfaces without needing to make an ability check. Additionally, Difficult Terrain composed of ice or snow doesn't cost it extra movement.",
    ),
    (
        (
            "Monsters A–Z",
            "White Dragons",
            "Ancient White Dragon",
            "Traits",
        ),
        "**_Legendary Resistance (4/Day, or 5/Day in Lair)._** If the dragon fails a saving throw, it can choose to succeed instead.",
    ),
    (
        (
            "Monsters A–Z",
            "White Dragons",
            "Ancient White Dragon",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "White Dragons",
            "Ancient White Dragon",
            "Actions",
        ),
        "**_Multiattack._** The dragon makes three Rend attacks.",
    ),
    (
        (
            "Monsters A–Z",
            "White Dragons",
            "Ancient White Dragon",
            "Actions",
        ),
        "**_Rend._** _Melee Attack Roll:_ +14, reach 15 ft. _Hit:_ 17 (2d8 + 8) Slashing damage plus 7 (2d6) Cold damage.",
    ),
    (
        (
            "Monsters A–Z",
            "White Dragons",
            "Ancient White Dragon",
            "Actions",
        ),
        "**_Cold Breath (Recharge 5–6)._** _Constitution Saving Throw:_ DC 22, each creature in a 90-foot Cone. _Failure:_ 63 (14d8) Cold damage. _Success:_ Half damage.",
    ),
    (
        (
            "Monsters A–Z",
            "White Dragons",
            "Ancient White Dragon",
            "Legendary Actions",
        ),
        "#### Legendary Actions",
    ),
    (
        (
            "Monsters A–Z",
            "White Dragons",
            "Ancient White Dragon",
            "Legendary Actions",
        ),
        "_Legendary Action Uses: 3 (4 in Lair). Immediately after another creature's turn, the dragon can expend a use to take one of the following actions. The dragon regains all expended uses at the start of each of its turns._",
    ),
    (
        (
            "Monsters A–Z",
            "White Dragons",
            "Ancient White Dragon",
            "Legendary Actions",
        ),
        "**_Freezing Burst._** _Constitution Saving Throw:_ DC 20, each creature in a 30-foot-radius Sphere centered on a point the dragon can see within 120 feet. _Failure:_ 14 (4d6) Cold damage, and the target's Speed is 0 until the end of the target's next turn. _Failure or Success:_ The dragon can't take this action again until the start of its next turn.",
    ),
    (
        (
            "Monsters A–Z",
            "White Dragons",
            "Ancient White Dragon",
            "Legendary Actions",
        ),
        "**_Frightful Presence._** The dragon casts _Fear_, requiring no Material components and using Charisma as the spellcasting ability (spell save DC 18). The dragon can't take this action again until the start of its next turn.",
    ),
    (
        (
            "Monsters A–Z",
            "White Dragons",
            "Ancient White Dragon",
            "Legendary Actions",
        ),
        "**_Pounce._** The dragon moves up to half its Speed, and it makes one Rend attack.",
    ),
    (
        (
            "Monsters A–Z",
            "Wight",
        ),
        "## Wight",
    ),
    (
        (
            "Monsters A–Z",
            "Wight",
            "Wight",
        ),
        "### Wight",
    ),
    (
        (
            "Monsters A–Z",
            "Wight",
            "Wight",
        ),
        "_Medium Undead, Neutral Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Wight",
            "Wight",
        ),
        "**AC** 14 **Initiative** +4 (14) <br>\n**HP** 82 (11d8 + 33) <br>\n**Speed** 30 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Wight",
            "Wight",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>DEX</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CON</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>WIS</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CHA</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Wight",
            "Wight",
        ),
        "**Skills** Perception +3, Stealth +4<br>\n**Resistances** Necrotic<br>\n**Immunities** Poison; Exhaustion, Poisoned<br>\n**Gear** Studded Leather Armor<br>\n**Senses** Darkvision 60 ft.; Passive Perception 13<br>\n**Languages** Common plus one other language<br>\n**CR** 3 (XP 700; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Wight",
            "Wight",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Wight",
            "Wight",
            "Traits",
        ),
        "**_Sunlight Sensitivity._** While in sunlight, the wight has Disadvantage on ability checks and attack rolls.",
    ),
    (
        (
            "Monsters A–Z",
            "Wight",
            "Wight",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Wight",
            "Wight",
            "Actions",
        ),
        "**_Multiattack._** The wight makes two attacks, using Necrotic Sword or Necrotic Bow in any combination. It can replace one attack with a use of Life Drain.",
    ),
    (
        (
            "Monsters A–Z",
            "Wight",
            "Wight",
            "Actions",
        ),
        "**_Necrotic Sword._** _Melee Attack Roll:_ +4, reach 5 ft. _Hit:_ 6 (1d8 + 2) Slashing damage plus 4 (1d8) Necrotic damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Wight",
            "Wight",
            "Actions",
        ),
        "**_Necrotic Bow._** _Ranged Attack Roll:_ +4, range 150/600 ft. _Hit:_ 6 (1d8 + 2) Piercing damage plus 4 (1d8) Necrotic damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Wight",
            "Wight",
            "Actions",
        ),
        "**_Life Drain._** _Constitution Saving Throw:_ DC 13, one creature within 5 feet. _Failure:_ 6 (1d8 + 2) Necrotic damage, and the target's Hit Point maximum decreases by an amount equal to the damage taken. <br>\n&emsp;A Humanoid slain by this attack rises 24 hours later as a **Zombie** under the wight's control, unless the Humanoid is restored to life or its body is destroyed. The wight can have no more than twelve zombies under its control at a time.",
    ),
    (
        (
            "Monsters A–Z",
            "Will-o'-Wisp",
        ),
        "## Will-o'-Wisp",
    ),
    (
        (
            "Monsters A–Z",
            "Will-o'-Wisp",
            "Will-o'-Wisp",
        ),
        "### Will-o'-Wisp",
    ),
    (
        (
            "Monsters A–Z",
            "Will-o'-Wisp",
            "Will-o'-Wisp",
        ),
        "_Tiny Undead, Chaotic Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Will-o'-Wisp",
            "Will-o'-Wisp",
        ),
        "**AC** 19 **Initiative** +9 (19) <br>\n**HP** 27 (11d4) <br>\n**Speed** 5 ft., Fly 50 ft. (hover) <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Will-o'-Wisp",
            "Will-o'-Wisp",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>1</td>\n      <td>-5</td>\n      <td>-5</td>\n      <td><strong>DEX</strong></td>\n      <td>28</td>\n      <td>+9</td>\n      <td>+9</td>\n      <td><strong>CON</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>WIS</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CHA</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Will-o'-Wisp",
            "Will-o'-Wisp",
        ),
        "**Resistances** Acid, Bludgeoning, Cold, Fire, Necrotic, Piercing, Slashing<br>",
    ),
    (
        (
            "Monsters A–Z",
            "Will-o'-Wisp",
            "Will-o'-Wisp",
        ),
        "**Immunities** Lightning, Poison; Exhaustion, Grappled, Paralyzed, Petrified, Poisoned, Prone, Restrained, Unconscious<br>",
    ),
    (
        (
            "Monsters A–Z",
            "Will-o'-Wisp",
            "Will-o'-Wisp",
        ),
        "**Senses** Darkvision 120 ft.; Passive Perception 12<br>",
    ),
    (
        (
            "Monsters A–Z",
            "Will-o'-Wisp",
            "Will-o'-Wisp",
        ),
        "**Languages** Common plus one other language<br>",
    ),
    (
        (
            "Monsters A–Z",
            "Will-o'-Wisp",
            "Will-o'-Wisp",
        ),
        "**CR** 2 (XP 450; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Will-o'-Wisp",
            "Will-o'-Wisp",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Will-o'-Wisp",
            "Will-o'-Wisp",
            "Traits",
        ),
        "**_Ephemeral._** The wisp can't wear or carry anything.",
    ),
    (
        (
            "Monsters A–Z",
            "Will-o'-Wisp",
            "Will-o'-Wisp",
            "Traits",
        ),
        "**_Illumination._** The wisp sheds Bright Light in a 20-foot radius and Dim Light for an additional 20 feet.",
    ),
    (
        (
            "Monsters A–Z",
            "Will-o'-Wisp",
            "Will-o'-Wisp",
            "Traits",
        ),
        "**_Incorporeal Movement._** The wisp can move through other creatures and objects as if they were Difficult Terrain. It takes 5 (1d10) Force damage if it ends its turn inside an object.",
    ),
    (
        (
            "Monsters A–Z",
            "Will-o'-Wisp",
            "Will-o'-Wisp",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Will-o'-Wisp",
            "Will-o'-Wisp",
            "Actions",
        ),
        "**_Shock._** _Melee Attack Roll:_ +4, reach 5 ft. _Hit:_ 11 (2d8 + 2) Lightning damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Will-o'-Wisp",
            "Will-o'-Wisp",
            "Bonus Actions",
        ),
        "#### Bonus Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Will-o'-Wisp",
            "Will-o'-Wisp",
            "Bonus Actions",
        ),
        "**_Consume Life._** _Constitution Saving Throw:_ DC 10, one living creature the wisp can see within 5 feet that has 0 Hit Points. _Failure:_ The target dies, and the wisp regains 10 (3d6) Hit Points.",
    ),
    (
        (
            "Monsters A–Z",
            "Will-o'-Wisp",
            "Will-o'-Wisp",
            "Bonus Actions",
        ),
        "**_Vanish._** The wisp and its light have the Invisible condition until the wisp's Concentration ends on this effect, which ends early immediately after the wisp makes an attack roll or uses Consume Life.",
    ),
    (
        (
            "Monsters A–Z",
            "Winter Wolf",
        ),
        "## Winter Wolf",
    ),
    (
        (
            "Monsters A–Z",
            "Winter Wolf",
            "Winter Wolf",
        ),
        "### Winter Wolf",
    ),
    (
        (
            "Monsters A–Z",
            "Winter Wolf",
            "Winter Wolf",
        ),
        "_Large Monstrosity, Neutral Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Winter Wolf",
            "Winter Wolf",
        ),
        "**AC** 13 **Initiative** +1 (11) <br>\n**HP** 75 (10d10 + 20) <br>\n**Speed** 50 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Winter Wolf",
            "Winter Wolf",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+4</td>\n      <td><strong>DEX</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CON</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>7</td>\n      <td>-2</td>\n      <td>-2</td>\n      <td><strong>WIS</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CHA</strong></td>\n      <td>8</td>\n      <td>-1</td>\n      <td>-1</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Winter Wolf",
            "Winter Wolf",
        ),
        "**Skills** Perception +5, Stealth +5<br>",
    ),
    (
        (
            "Monsters A–Z",
            "Winter Wolf",
            "Winter Wolf",
        ),
        "**Immunities** Cold<br>",
    ),
    (
        (
            "Monsters A–Z",
            "Winter Wolf",
            "Winter Wolf",
        ),
        "**Senses** Passive Perception 15<br>",
    ),
    (
        (
            "Monsters A–Z",
            "Winter Wolf",
            "Winter Wolf",
        ),
        "**Languages** Common, Giant<br>",
    ),
    (
        (
            "Monsters A–Z",
            "Winter Wolf",
            "Winter Wolf",
        ),
        "**CR** 3 (XP 700; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Winter Wolf",
            "Winter Wolf",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Winter Wolf",
            "Winter Wolf",
            "Traits",
        ),
        "**_Pack Tactics._** The wolf has Advantage on an attack roll against a creature if at least one of the wolf's allies is within 5 feet of the creature and the ally doesn't have the Incapacitated condition.",
    ),
    (
        (
            "Monsters A–Z",
            "Winter Wolf",
            "Winter Wolf",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Winter Wolf",
            "Winter Wolf",
            "Actions",
        ),
        "**_Bite._** _Melee Attack Roll:_ +6, reach 5 ft. _Hit:_ 11 (2d6 + 4) Piercing damage. If the target is a Large or smaller creature, it has the Prone condition.",
    ),
    (
        (
            "Monsters A–Z",
            "Winter Wolf",
            "Winter Wolf",
            "Actions",
        ),
        "**_Cold Breath (Recharge 5–6)._** _Constitution Saving Throw:_ DC 12, each creature in a 15-foot Cone. _Failure:_ 18 (4d8) Cold damage. _Success:_ Half damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Worg",
        ),
        "## Worg",
    ),
    (
        (
            "Monsters A–Z",
            "Worg",
            "Worg",
        ),
        "### Worg",
    ),
    (
        (
            "Monsters A–Z",
            "Worg",
            "Worg",
        ),
        "_Large Fey, Neutral Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Worg",
            "Worg",
        ),
        "**AC** 13 **Initiative** +1 (11) <br>\n**HP** 26 (4d10 + 4) <br>\n**Speed** 50 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Worg",
            "Worg",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>DEX</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CON</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>7</td>\n      <td>-2</td>\n      <td>-2</td>\n      <td><strong>WIS</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CHA</strong></td>\n      <td>8</td>\n      <td>-1</td>\n      <td>-1</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Worg",
            "Worg",
        ),
        "**Skills** Perception +4<br>",
    ),
    (
        (
            "Monsters A–Z",
            "Worg",
            "Worg",
        ),
        "**Senses** Darkvision 60 ft.; Passive Perception 14<br>",
    ),
    (
        (
            "Monsters A–Z",
            "Worg",
            "Worg",
        ),
        "**Languages** Goblin, Worg<br>",
    ),
    (
        (
            "Monsters A–Z",
            "Worg",
            "Worg",
        ),
        "**CR** 1/2 (XP 100; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Worg",
            "Worg",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Worg",
            "Worg",
            "Actions",
        ),
        "**_Bite._** _Melee Attack Roll:_ +5, reach 5 ft. _Hit:_ 7 (1d8 + 3) Piercing damage, and the next attack roll made against the target before the start of the worg's next turn has Advantage.",
    ),
    (
        (
            "Monsters A–Z",
            "Wraith",
        ),
        "## Wraith",
    ),
    (
        (
            "Monsters A–Z",
            "Wraith",
            "Wraith",
        ),
        "### Wraith",
    ),
    (
        (
            "Monsters A–Z",
            "Wraith",
            "Wraith",
        ),
        "_Medium or Small Undead, Neutral Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Wraith",
            "Wraith",
        ),
        "**AC** 13 **Initiative** +3 (13) <br>\n**HP** 67 (9d8 + 27) <br>\n**Speed** 5 ft., Fly 60 ft. (hover) <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Wraith",
            "Wraith",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>6</td>\n      <td>-2</td>\n      <td>-2</td>\n      <td><strong>DEX</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>CON</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>WIS</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CHA</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Wraith",
            "Wraith",
        ),
        "**Resistances** Acid, Bludgeoning, Cold, Fire, Piercing, Slashing<br>",
    ),
    (
        (
            "Monsters A–Z",
            "Wraith",
            "Wraith",
        ),
        "**Immunities** Necrotic, Poison; Charmed, Exhaustion, Grappled, Paralyzed, Petrified, Poisoned, Prone, Restrained, Unconscious<br>",
    ),
    (
        (
            "Monsters A–Z",
            "Wraith",
            "Wraith",
        ),
        "**Senses** Darkvision 60 ft.; Passive Perception 12<br>",
    ),
    (
        (
            "Monsters A–Z",
            "Wraith",
            "Wraith",
        ),
        "**Languages** Common plus two other languages<br>",
    ),
    (
        (
            "Monsters A–Z",
            "Wraith",
            "Wraith",
        ),
        "**CR** 5 (XP 1,800; PB +3)",
    ),
    (
        (
            "Monsters A–Z",
            "Wraith",
            "Wraith",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Wraith",
            "Wraith",
            "Traits",
        ),
        "**_Incorporeal Movement._** The wraith can move through other creatures and objects as if they were Difficult Terrain. It takes 5 (1d10) Force damage if it ends its turn inside an object.",
    ),
    (
        (
            "Monsters A–Z",
            "Wraith",
            "Wraith",
            "Traits",
        ),
        "**_Sunlight Sensitivity._** While in sunlight, the wraith has Disadvantage on ability checks and attack rolls.",
    ),
    (
        (
            "Monsters A–Z",
            "Wraith",
            "Wraith",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Wraith",
            "Wraith",
            "Actions",
        ),
        "**_Life Drain._** _Melee Attack Roll:_ +6, reach 5 ft. _Hit:_ 21 (4d8 + 3) Necrotic damage. If the target is a creature, its Hit Point maximum decreases by an amount equal to the damage taken.",
    ),
    (
        (
            "Monsters A–Z",
            "Wraith",
            "Wraith",
            "Actions",
        ),
        "**_Create Specter._** The wraith targets a Humanoid corpse within 10 feet of itself that has been dead for no longer than 1 minute. The target's spirit rises as a **Specter** in the space of its corpse or in the nearest unoccupied space. The specter is under the wraith's control. The wraith can have no more than seven specters under its control at a time.",
    ),
    (
        (
            "Monsters A–Z",
            "Wyvern",
        ),
        "## Wyvern",
    ),
    (
        (
            "Monsters A–Z",
            "Wyvern",
            "Wyvern",
        ),
        "### Wyvern",
    ),
    (
        (
            "Monsters A–Z",
            "Wyvern",
            "Wyvern",
        ),
        "_Large Dragon, Unaligned_",
    ),
    (
        (
            "Monsters A–Z",
            "Wyvern",
            "Wyvern",
        ),
        "**AC** 14 **Initiative** +0 (10) <br>\n**HP** 127 (15d10 + 45) <br>\n**Speed** 30 ft., Fly 80 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Wyvern",
            "Wyvern",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>19</td>\n      <td>+4</td>\n      <td>+4</td>\n      <td><strong>DEX</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CON</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>5</td>\n      <td>−3</td>\n      <td>−3</td>\n      <td><strong>WIS</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CHA</strong></td>\n      <td>6</td>\n      <td>−2</td>\n      <td>−2</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Wyvern",
            "Wyvern",
        ),
        "**Skills** Perception +4<br>\n**Senses** Darkvision 120 ft.; Passive Perception 14<br>\n**Languages** None<br>\n**CR** 6 (XP 2,300; PB +3)",
    ),
    (
        (
            "Monsters A–Z",
            "Wyvern",
            "Wyvern",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Wyvern",
            "Wyvern",
            "Actions",
        ),
        "**_Multiattack._** The wyvern makes one Bite attack and one Sting attack.",
    ),
    (
        (
            "Monsters A–Z",
            "Wyvern",
            "Wyvern",
            "Actions",
        ),
        "**_Bite._** _Melee Attack Roll:_ +7, reach 5 ft. _Hit:_ 13 (2d8 + 4) Piercing damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Wyvern",
            "Wyvern",
            "Actions",
        ),
        "**_Sting._** _Melee Attack Roll:_ +7, reach 10 ft. _Hit:_ 11 (2d6 + 4) Piercing damage plus 24 (7d6) Poison damage, and the target has the Poisoned condition until the start of the wyvern's next turn.",
    ),
    (
        (
            "Monsters A–Z",
            "Xorn",
        ),
        "## Xorn",
    ),
    (
        (
            "Monsters A–Z",
            "Xorn",
            "Xorn",
        ),
        "### Xorn",
    ),
    (
        (
            "Monsters A–Z",
            "Xorn",
            "Xorn",
        ),
        "_Medium Elemental, Neutral_",
    ),
    (
        (
            "Monsters A–Z",
            "Xorn",
            "Xorn",
        ),
        "**AC** 19 **Initiative** +0 (10) <br>\n**HP** 84 (8d8 + 48) <br>\n**Speed** 20 ft., Burrow 20 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Xorn",
            "Xorn",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>17</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>DEX</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CON</strong></td>\n      <td>22</td>\n      <td>+6</td>\n      <td>+6</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>WIS</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CHA</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Xorn",
            "Xorn",
        ),
        "**Skills** Perception +6, Stealth +6<br>\n**Immunities** Poison; Paralyzed, Petrified, Poisoned<br>\n**Senses** Darkvision 60 ft., Tremorsense 60 ft.; Passive Perception 16<br>\n**Languages** Primordial (Terran)<br>\n**CR** 5 (XP 1,800; PB +3)",
    ),
    (
        (
            "Monsters A–Z",
            "Xorn",
            "Xorn",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Xorn",
            "Xorn",
            "Traits",
        ),
        "**_Earth Glide._** The xorn can burrow through nonmagical, unworked earth and stone. While doing so, the xorn doesn't disturb the material it moves through.",
    ),
    (
        (
            "Monsters A–Z",
            "Xorn",
            "Xorn",
            "Traits",
        ),
        "**_Treasure Sense._** The xorn can pinpoint the location of precious metals and stones within 60 feet of itself.",
    ),
    (
        (
            "Monsters A–Z",
            "Xorn",
            "Xorn",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Xorn",
            "Xorn",
            "Actions",
        ),
        "**_Multiattack._** The xorn makes one Bite attack and three Claw attacks.",
    ),
    (
        (
            "Monsters A–Z",
            "Xorn",
            "Xorn",
            "Actions",
        ),
        "**_Bite._** _Melee Attack Roll:_ +6, reach 5 ft. _Hit:_ 17 (4d6 + 3) Piercing damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Xorn",
            "Xorn",
            "Actions",
        ),
        "**_Claw._** _Melee Attack Roll:_ +6, reach 5 ft. _Hit:_ 8 (1d10 + 3) Slashing damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Xorn",
            "Xorn",
            "Bonus Actions",
        ),
        "#### Bonus Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Xorn",
            "Xorn",
            "Bonus Actions",
        ),
        "**_Charge._** The xorn moves up to its Speed or Burrow Speed straight toward an enemy it can sense.",
    ),
    (
        (
            "Monsters A–Z",
            "Zombies",
        ),
        "## Zombies",
    ),
    (
        (
            "Monsters A–Z",
            "Zombies",
            "Zombie",
        ),
        "### Zombie",
    ),
    (
        (
            "Monsters A–Z",
            "Zombies",
            "Zombie",
        ),
        "_Medium Undead, Neutral Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Zombies",
            "Zombie",
        ),
        "**AC** 8 **Initiative** −2 (8) <br>\n**HP** 15 (2d8 + 6) <br>\n**Speed** 20 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Zombies",
            "Zombie",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>DEX</strong></td>\n      <td>6</td>\n      <td>−2</td>\n      <td>−2</td>\n      <td><strong>CON</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>3</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>WIS</strong></td>\n      <td>6</td>\n      <td>−2</td>\n      <td>+0</td>\n      <td><strong>CHA</strong></td>\n      <td>5</td>\n      <td>−3</td>\n      <td>−3</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Zombies",
            "Zombie",
        ),
        "**Immunities** Poison; Exhaustion, Poisoned<br>\n**Senses** Darkvision 60 ft.; Passive Perception 8<br>\n**Languages** Understands Common plus one other language but can't speak<br>\n**CR** 1/4 (XP 50; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Zombies",
            "Zombie",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Zombies",
            "Zombie",
            "Traits",
        ),
        "**_Undead Fortitude._** If damage reduces the zombie to 0 Hit Points, it makes a Constitution saving throw (DC 5 plus the damage taken) unless the damage is Radiant or from a Critical Hit. On a successful save, the zombie drops to 1 Hit Point instead.",
    ),
    (
        (
            "Monsters A–Z",
            "Zombies",
            "Zombie",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Zombies",
            "Zombie",
            "Actions",
        ),
        "**_Slam._** _Melee Attack Roll:_ +3, reach 5 ft. _Hit:_ 5 (1d8 + 1) Bludgeoning damage.",
    ),
    (
        (
            "Monsters A–Z",
            "Zombies",
            "Ogre Zombie",
        ),
        "### Ogre Zombie",
    ),
    (
        (
            "Monsters A–Z",
            "Zombies",
            "Ogre Zombie",
        ),
        "_Large Undead, Neutral Evil_",
    ),
    (
        (
            "Monsters A–Z",
            "Zombies",
            "Ogre Zombie",
        ),
        "**AC** 8 **Initiative** −2 (8) <br>\n**HP** 85 (9d10 + 36) <br>\n**Speed** 30 ft. <br>",
    ),
    (
        (
            "Monsters A–Z",
            "Zombies",
            "Ogre Zombie",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>19</td>\n      <td>+4</td>\n      <td>+4</td>\n      <td><strong>DEX</strong></td>\n      <td>6</td>\n      <td>−2</td>\n      <td>−2</td>\n      <td><strong>CON</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+4</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>3</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>WIS</strong></td>\n      <td>6</td>\n      <td>−2</td>\n      <td>+0</td>\n      <td><strong>CHA</strong></td>\n      <td>5</td>\n      <td>−3</td>\n      <td>−3</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Monsters A–Z",
            "Zombies",
            "Ogre Zombie",
        ),
        "**Immunities** Poison; Exhaustion, Poisoned<br>\n**Senses** Darkvision 60 ft.; Passive Perception 8<br>\n**Languages** Understands Common and Giant but can't speak<br>\n**CR** 2 (XP 450; PB +2)",
    ),
    (
        (
            "Monsters A–Z",
            "Zombies",
            "Ogre Zombie",
            "Traits",
        ),
        "#### Traits",
    ),
    (
        (
            "Monsters A–Z",
            "Zombies",
            "Ogre Zombie",
            "Traits",
        ),
        "**_Undead Fortitude._** If damage reduces the zombie to 0 Hit Points, it makes a Constitution saving throw (DC 5 plus the damage taken) unless the damage is Radiant or from a Critical Hit. On a successful save, the zombie drops to 1 Hit Point instead.",
    ),
    (
        (
            "Monsters A–Z",
            "Zombies",
            "Ogre Zombie",
            "Actions",
        ),
        "#### Actions",
    ),
    (
        (
            "Monsters A–Z",
            "Zombies",
            "Ogre Zombie",
            "Actions",
        ),
        "**_Slam._** _Melee Attack Roll:_ +6, reach 5 ft. _Hit:_ 13 (2d8 + 4) Bludgeoning damage.",
    ),
)
