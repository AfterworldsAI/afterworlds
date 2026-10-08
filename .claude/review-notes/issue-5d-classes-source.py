# ruff: noqa: E501
"""The *Classes* part of the SRD 5.2.1 as the release prints it -- CRD Issue 5d.

Every leaf of the part but its ``# Classes`` heading, in printed order (pp.
28-82), as (container label path below *Classes*, exact leaf text). Each text
was qualified against the official PDF (``docs/sources/DnD5_5e_SRD_CC_v5_2_1.pdf``)
before it was written here: prose word for word, every table row cell for
cell (see the classes review packet). The generator names its spans from
these texts; a text the release prints differently fails to locate, loudly.
"""

from __future__ import annotations

LEAVES: tuple[tuple[tuple[str, ...], str], ...] = (
    (("Barbarian",), "## Barbarian"),
    (
        ("Barbarian",),
        "**Core Barbarian Traits**\n\n<table>\n  <tbody>\n    <tr>\n      <td>Primary Ability</td>\n      <td>Strength</td>\n    </tr>\n    <tr>\n      <td>Hit Point Die</td>\n      <td>D12 per Barbarian level</td>\n    </tr>\n    <tr>\n      <td>Saving Throw Proficiencies</td>\n      <td>Strength and Constitution</td>\n    </tr>\n    <tr>\n      <td>Skill Proficiencies</td>\n      <td>Choose 2: Animal Handling, Athletics, Intimidation, Nature, Perception, or Survival</td>\n    </tr>\n    <tr>\n      <td>Weapon Proficiencies</td>\n      <td>Simple and Martial weapons</td>\n    </tr>\n    <tr>\n      <td>Armor Training</td>\n      <td>Light and Medium armor and Shields</td>\n    </tr>\n    <tr>\n      <td>Starting Equipment</td>\n      <td>Choose A or B: (A) Greataxe, 4 Handaxes, Explorer's Pack, and 15 GP; or (B) 75 GP</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (("Barbarian", "Becoming a Barbarian …"), "### Becoming a Barbarian …"),
    (
        ("Barbarian", "Becoming a Barbarian …", "As a Level 1 Character"),
        "#### As a Level 1 Character",
    ),
    (
        ("Barbarian", "Becoming a Barbarian …", "As a Level 1 Character"),
        "• Gain all the traits in the Core Barbarian Traits table.",
    ),
    (
        ("Barbarian", "Becoming a Barbarian …", "As a Level 1 Character"),
        "• Gain the Barbarian's level 1 features, which are listed in the Barbarian Features table.",
    ),
    (
        ("Barbarian", "Becoming a Barbarian …", "As a Multiclass Character"),
        "#### As a Multiclass Character",
    ),
    (
        ("Barbarian", "Becoming a Barbarian …", "As a Multiclass Character"),
        "• Gain the following traits from the Core Barbarian Traits table: Hit Point Die, proficiency with Martial weapons, and training with Shields.\n• Gain the Barbarian's level 1 features, which are listed in the Barbarian Features table.",
    ),
    (("Barbarian", "Barbarian Class Features"), "### Barbarian Class Features"),
    (
        ("Barbarian", "Barbarian Class Features"),
        "As a Barbarian, you gain the following class features when you reach the specified Barbarian levels. These features are listed in the Barbarian Features table.",
    ),
    (
        ("Barbarian", "Barbarian Class Features"),
        "**Barbarian Features**\n\n<table>\n  <thead>\n    <tr>\n      <th>Level</th>\n      <th>Proficiency Bonus</th>\n      <th>Class Features</th>\n      <th>Rages</th>\n      <th>Rage Damage</th>\n      <th>Weapon Mastery</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>1</td>\n      <td>+2</td>\n      <td>Rage, Unarmored Defense, Weapon Mastery</td>\n      <td>2</td>\n      <td>+2</td>\n      <td>2</td>\n    </tr>\n    <tr>\n      <td>2</td>\n      <td>+2</td>\n      <td>Danger Sense, Reckless Attack</td>\n      <td>2</td>\n      <td>+2</td>\n      <td>2</td>\n    </tr>\n    <tr>\n      <td>3</td>\n      <td>+2</td>\n      <td>Barbarian Subclass, Primal Knowledge</td>\n      <td>3</td>\n      <td>+2</td>\n      <td>2</td>\n    </tr>\n    <tr>\n      <td>4</td>\n      <td>+2</td>\n      <td>Ability Score Improvement</td>\n      <td>3</td>\n      <td>+2</td>\n      <td>3</td>\n    </tr>\n    <tr>\n      <td>5</td>\n      <td>+3</td>\n      <td>Extra Attack, Fast Movement</td>\n      <td>3</td>\n      <td>+2</td>\n      <td>3</td>\n    </tr>\n    <tr>\n      <td>6</td>\n      <td>+3</td>\n      <td>Subclass feature</td>\n      <td>4</td>\n      <td>+2</td>\n      <td>3</td>\n    </tr>\n    <tr>\n      <td>7</td>\n      <td>+3</td>\n      <td>Feral Instinct, Instinctive Pounce</td>\n      <td>4</td>\n      <td>+2</td>\n      <td>3</td>\n    </tr>\n    <tr>\n      <td>8</td>\n      <td>+3</td>\n      <td>Ability Score Improvement</td>\n      <td>4</td>\n      <td>+2</td>\n      <td>3</td>\n    </tr>\n    <tr>\n      <td>9</td>\n      <td>+4</td>\n      <td>Brutal Strike</td>\n      <td>4</td>\n      <td>+3</td>\n      <td>3</td>\n    </tr>\n    <tr>\n      <td>10</td>\n      <td>+4</td>\n      <td>Subclass feature</td>\n      <td>4</td>\n      <td>+3</td>\n      <td>4</td>\n    </tr>\n    <tr>\n      <td>11</td>\n      <td>+4</td>\n      <td>Relentless Rage</td>\n      <td>4</td>\n      <td>+3</td>\n      <td>4</td>\n    </tr>\n    <tr>\n      <td>12</td>\n      <td>+4</td>\n      <td>Ability Score Improvement</td>\n      <td>5</td>\n      <td>+3</td>\n      <td>4</td>\n    </tr>\n    <tr>\n      <td>13</td>\n      <td>+5</td>\n      <td>Improved Brutal Strike</td>\n      <td>5</td>\n      <td>+3</td>\n      <td>4</td>\n    </tr>\n    <tr>\n      <td>14</td>\n      <td>+5</td>\n      <td>Subclass feature</td>\n      <td>5</td>\n      <td>+3</td>\n      <td>4</td>\n    </tr>\n    <tr>\n      <td>15</td>\n      <td>+5</td>\n      <td>Persistent Rage</td>\n      <td>5</td>\n      <td>+3</td>\n      <td>4</td>\n    </tr>\n    <tr>\n      <td>16</td>\n      <td>+5</td>\n      <td>Ability Score Improvement</td>\n      <td>5</td>\n      <td>+4</td>\n      <td>4</td>\n    </tr>\n    <tr>\n      <td>17</td>\n      <td>+6</td>\n      <td>Improved Brutal Strike</td>\n      <td>6</td>\n      <td>+4</td>\n      <td>4</td>\n    </tr>\n    <tr>\n      <td>18</td>\n      <td>+6</td>\n      <td>Indomitable Might</td>\n      <td>6</td>\n      <td>+4</td>\n      <td>4</td>\n    </tr>\n    <tr>\n      <td>19</td>\n      <td>+6</td>\n      <td>Epic Boon</td>\n      <td>6</td>\n      <td>+4</td>\n      <td>4</td>\n    </tr>\n    <tr>\n      <td>20</td>\n      <td>+6</td>\n      <td>Primal Champion</td>\n      <td>6</td>\n      <td>+4</td>\n      <td>4</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (("Barbarian", "Barbarian Class Features", "Level 1: Rage"), "#### Level 1: Rage"),
    (
        ("Barbarian", "Barbarian Class Features", "Level 1: Rage"),
        "You can imbue yourself with a primal power called Rage, a force that grants you extraordinary might and resilience. You can enter it as a Bonus Action if you aren't wearing Heavy armor.",
    ),
    (
        ("Barbarian", "Barbarian Class Features", "Level 1: Rage"),
        "You can enter your Rage the number of times shown for your Barbarian level in the Rages column of the Barbarian Features table. You regain one expended use when you finish a Short Rest, and you regain all expended uses when you finish a Long Rest.",
    ),
    (
        ("Barbarian", "Barbarian Class Features", "Level 1: Rage"),
        "While active, your Rage follows the rules below.",
    ),
    (
        ("Barbarian", "Barbarian Class Features", "Level 1: Rage"),
        "_Damage Resistance._ You have Resistance to Bludgeoning, Piercing, and Slashing damage.",
    ),
    (
        ("Barbarian", "Barbarian Class Features", "Level 1: Rage"),
        "_Rage Damage._ When you make an attack using Strength—with either a weapon or an Unarmed Strike—and deal damage to the target, you gain a bonus to the damage that increases as you gain levels as a Barbarian, as shown in the Rage Damage column of the Barbarian Features table.",
    ),
    (
        ("Barbarian", "Barbarian Class Features", "Level 1: Rage"),
        "_Strength Advantage._ You have Advantage on Strength checks and Strength saving throws.",
    ),
    (
        ("Barbarian", "Barbarian Class Features", "Level 1: Rage"),
        "_No Concentration or Spells._ You can't maintain Concentration, and you can't cast spells.",
    ),
    (
        ("Barbarian", "Barbarian Class Features", "Level 1: Rage"),
        "_Duration._ The Rage lasts until the end of your next turn, and it ends early if you don Heavy armor or have the Incapacitated condition. If your Rage is still active on your next turn, you can extend the Rage for another round by doing one of the following:",
    ),
    (
        ("Barbarian", "Barbarian Class Features", "Level 1: Rage"),
        "- Make an attack roll against an enemy.\n- Force an enemy to make a saving throw.\n- Take a Bonus Action to extend your Rage.",
    ),
    (
        ("Barbarian", "Barbarian Class Features", "Level 1: Rage"),
        "Each time the Rage is extended, it lasts until the end of your next turn. You can maintain a Rage for up to 10 minutes.",
    ),
    (
        ("Barbarian", "Barbarian Class Features", "Level 1: Unarmored Defense"),
        "#### Level 1: Unarmored Defense",
    ),
    (
        ("Barbarian", "Barbarian Class Features", "Level 1: Unarmored Defense"),
        "While you aren't wearing any armor, your base Armor Class equals 10 plus your Dexterity and Constitution modifiers. You can use a Shield and still gain this benefit.",
    ),
    (
        ("Barbarian", "Barbarian Class Features", "Level 1: Weapon Mastery"),
        "#### Level 1: Weapon Mastery",
    ),
    (
        ("Barbarian", "Barbarian Class Features", "Level 1: Weapon Mastery"),
        "Your training with weapons allows you to use the mastery properties of two kinds of Simple or Martial Melee weapons of your choice, such as Greataxes and Handaxes. Whenever you finish a Long Rest, you can practice weapon drills and change one of those weapon choices.",
    ),
    (
        ("Barbarian", "Barbarian Class Features", "Level 1: Weapon Mastery"),
        "When you reach certain Barbarian levels, you gain the ability to use the mastery properties of more kinds of weapons, as shown in the Weapon Mastery column of the Barbarian Features table.",
    ),
    (
        ("Barbarian", "Barbarian Class Features", "Level 2: Danger Sense"),
        "#### Level 2: Danger Sense",
    ),
    (
        ("Barbarian", "Barbarian Class Features", "Level 2: Danger Sense"),
        "You gain an uncanny sense of when things aren't as they should be, giving you an edge when you dodge perils. You have Advantage on Dexterity saving throws unless you have the Incapacitated condition.",
    ),
    (
        ("Barbarian", "Barbarian Class Features", "Level 2: Reckless Attack"),
        "#### Level 2: Reckless Attack",
    ),
    (
        ("Barbarian", "Barbarian Class Features", "Level 2: Reckless Attack"),
        "You can throw aside all concern for defense to attack with increased ferocity. When you make your first attack roll on your turn, you can decide to attack recklessly. Doing so gives you Advantage on attack rolls using Strength until the start of your next turn, but attack rolls against you have Advantage during that time.",
    ),
    (
        ("Barbarian", "Barbarian Class Features", "Level 3: Barbarian Subclass"),
        "#### Level 3: Barbarian Subclass",
    ),
    (
        ("Barbarian", "Barbarian Class Features", "Level 3: Barbarian Subclass"),
        "You gain a Barbarian subclass of your choice. The Path of the Berserker subclass is detailed after this class's description. A subclass is a specialization that grants you features at certain Barbarian levels. For the rest of your career, you gain each of your subclass's features that are of your Barbarian level or lower.",
    ),
    (
        ("Barbarian", "Barbarian Class Features", "Level 3: Primal Knowledge"),
        "#### Level 3: Primal Knowledge",
    ),
    (
        ("Barbarian", "Barbarian Class Features", "Level 3: Primal Knowledge"),
        "You gain proficiency in another skill of your choice from the skill list available to Barbarians at level 1.",
    ),
    (
        ("Barbarian", "Barbarian Class Features", "Level 3: Primal Knowledge"),
        "In addition, while your Rage is active, you can channel primal power when you attempt certain tasks; whenever you make an ability check using one of the following skills, you can make it as a Strength check even if it normally uses a different ability: Acrobatics, Intimidation, Perception, Stealth, or Survival. When you use this ability, your Strength represents primal power coursing through you, honing your agility, bearing, and senses.",
    ),
    (
        ("Barbarian", "Barbarian Class Features", "Level 4: Ability Score Improvement"),
        "#### Level 4: Ability Score Improvement",
    ),
    (
        ("Barbarian", "Barbarian Class Features", "Level 4: Ability Score Improvement"),
        'You gain the Ability Score Improvement feat (see "Feats") or another feat of your choice for which you qualify. You gain this feature again at Barbarian levels 8, 12, and 16.',
    ),
    (
        ("Barbarian", "Barbarian Class Features", "Level 5: Extra Attack"),
        "#### Level 5: Extra Attack",
    ),
    (
        ("Barbarian", "Barbarian Class Features", "Level 5: Extra Attack"),
        "You can attack twice instead of once whenever you take the Attack action on your turn.",
    ),
    (
        ("Barbarian", "Barbarian Class Features", "Level 5: Fast Movement"),
        "#### Level 5: Fast Movement",
    ),
    (
        ("Barbarian", "Barbarian Class Features", "Level 5: Fast Movement"),
        "Your speed increases by 10 feet while you aren't wearing Heavy armor.",
    ),
    (
        ("Barbarian", "Barbarian Class Features", "Level 7: Feral Instinct"),
        "#### Level 7: Feral Instinct",
    ),
    (
        ("Barbarian", "Barbarian Class Features", "Level 7: Feral Instinct"),
        "Your instincts are so honed that you have Advantage on Initiative rolls.",
    ),
    (
        ("Barbarian", "Barbarian Class Features", "Level 7: Instinctive Pounce"),
        "#### Level 7: Instinctive Pounce",
    ),
    (
        ("Barbarian", "Barbarian Class Features", "Level 7: Instinctive Pounce"),
        "As part of the Bonus Action you take to enter your Rage, you can move up to half your Speed.",
    ),
    (
        ("Barbarian", "Barbarian Class Features", "Level 9: Brutal Strike"),
        "#### Level 9: Brutal Strike",
    ),
    (
        ("Barbarian", "Barbarian Class Features", "Level 9: Brutal Strike"),
        "If you use Reckless Attack, you can forgo any Advantage on one Strength-based attack roll of your choice on your turn. The chosen attack roll mustn't have Disadvantage. If the chosen attack roll hits, the target takes an extra 1d10 damage of the same type dealt by the weapon or Unarmed Strike, and you can cause one Brutal Strike effect of your choice. You have the following effect options.",
    ),
    (
        ("Barbarian", "Barbarian Class Features", "Level 9: Brutal Strike"),
        "_Forceful Blow._ The target is pushed 15 feet straight away from you. You can then move up to half your Speed straight toward the target without provoking Opportunity Attacks.\n_Hamstring Blow._ The target's Speed is reduced by 15 feet until the start of your next turn. A target can be affected by only one Hamstring Blow at a time—the most recent one.",
    ),
    (
        ("Barbarian", "Barbarian Class Features", "Level 11: Relentless Rage"),
        "#### Level 11: Relentless Rage",
    ),
    (
        ("Barbarian", "Barbarian Class Features", "Level 11: Relentless Rage"),
        "Your Rage can keep you fighting despite grievous wounds. If you drop to 0 Hit Points while your Rage is active and don't die outright, you can make a DC 10 Constitution saving throw. If you succeed, your Hit Points instead change to a number equal to twice your Barbarian level.",
    ),
    (
        ("Barbarian", "Barbarian Class Features", "Level 11: Relentless Rage"),
        "Each time you use this feature after the first, the DC increases by 5. When you finish a Short or Long Rest, the DC resets to 10.",
    ),
    (
        ("Barbarian", "Barbarian Class Features", "Level 13: Improved Brutal Strike"),
        "#### Level 13: Improved Brutal Strike",
    ),
    (
        ("Barbarian", "Barbarian Class Features", "Level 13: Improved Brutal Strike"),
        "You have honed new ways to attack furiously. The following effects are now among your Brutal Strike options.",
    ),
    (
        ("Barbarian", "Barbarian Class Features", "Level 13: Improved Brutal Strike"),
        "_Staggering Blow._ The target has Disadvantage on the next saving throw it makes, and it can't make Opportunity Attacks until the start of your next turn.",
    ),
    (
        ("Barbarian", "Barbarian Class Features", "Level 13: Improved Brutal Strike"),
        "_Sundering Blow._ Before the start of your next turn, the next attack roll made by another creature against the target gains a +5 bonus to the roll. An attack roll can gain only one Sundering Blow bonus.",
    ),
    (
        ("Barbarian", "Barbarian Class Features", "Level 15: Persistent Rage"),
        "#### Level 15: Persistent Rage",
    ),
    (
        ("Barbarian", "Barbarian Class Features", "Level 15: Persistent Rage"),
        "When you roll Initiative, you can regain all expended uses of Rage. After you regain uses of Rage in this way, you can't do so again until you finish a Long Rest.",
    ),
    (
        ("Barbarian", "Barbarian Class Features", "Level 15: Persistent Rage"),
        "In addition, your Rage is so fierce that it now lasts for 10 minutes without you needing to do anything to extend it from round to round. Your Rage ends early if you have the Unconscious condition (not just the Incapacitated condition) or don Heavy armor.",
    ),
    (
        ("Barbarian", "Barbarian Class Features", "Level 17: Improved Brutal Strike"),
        "#### Level 17: Improved Brutal Strike",
    ),
    (
        ("Barbarian", "Barbarian Class Features", "Level 17: Improved Brutal Strike"),
        "The extra damage of your Brutal Strike increases to 2d10. In addition, you can use two different Brutal Strike effects whenever you use your Brutal Strike feature.",
    ),
    (
        ("Barbarian", "Barbarian Class Features", "Level 18: Indomitable Might"),
        "#### Level 18: Indomitable Might",
    ),
    (
        ("Barbarian", "Barbarian Class Features", "Level 18: Indomitable Might"),
        "If your total for a Strength check or Strength saving throw is less than your Strength score, you can use that score in place of the total.",
    ),
    (
        ("Barbarian", "Barbarian Class Features", "Level 19: Epic Boon"),
        "#### Level 19: Epic Boon",
    ),
    (
        ("Barbarian", "Barbarian Class Features", "Level 19: Epic Boon"),
        'You gain an Epic Boon feat (see "Feats") or another feat of your choice for which you qualify. Boon of Irresistible Offense is recommended.',
    ),
    (
        ("Barbarian", "Barbarian Class Features", "Level 20: Primal Champion"),
        "#### Level 20: Primal Champion",
    ),
    (
        ("Barbarian", "Barbarian Class Features", "Level 20: Primal Champion"),
        "You embody primal power. Your Strength and Constitution scores increase by 4, to a maximum of 25.",
    ),
    (
        ("Barbarian", "Barbarian Subclass: Path of the Berserker"),
        "### Barbarian Subclass: Path of the Berserker",
    ),
    (
        ("Barbarian", "Barbarian Subclass: Path of the Berserker"),
        "_Channel Rage into Violent Fury_",
    ),
    (
        ("Barbarian", "Barbarian Subclass: Path of the Berserker"),
        "Barbarians who walk the Path of the Berserker direct their Rage primarily toward violence. Their path is one of untrammeled fury, and they thrill in the chaos of battle as they allow their Rage to seize and empower them.",
    ),
    (
        ("Barbarian", "Barbarian Subclass: Path of the Berserker", "Level 3: Frenzy"),
        "#### Level 3: Frenzy",
    ),
    (
        ("Barbarian", "Barbarian Subclass: Path of the Berserker", "Level 3: Frenzy"),
        "If you use Reckless Attack while your Rage is active, you deal extra damage to the first target you hit on your turn with a Strength-based attack. To determine the extra damage, roll a number of d6s equal to your Rage Damage bonus, and add them together. The damage has the same type as the weapon or Unarmed Strike used for the attack.",
    ),
    (
        (
            "Barbarian",
            "Barbarian Subclass: Path of the Berserker",
            "Level 6: Mindless Rage",
        ),
        "#### Level 6: Mindless Rage",
    ),
    (
        (
            "Barbarian",
            "Barbarian Subclass: Path of the Berserker",
            "Level 6: Mindless Rage",
        ),
        "You have Immunity to the Charmed and Frightened conditions while your Rage is active. If you're Charmed or Frightened when you enter your Rage, the condition ends on you.",
    ),
    (
        (
            "Barbarian",
            "Barbarian Subclass: Path of the Berserker",
            "Level 10: Retaliation",
        ),
        "#### Level 10: Retaliation",
    ),
    (
        (
            "Barbarian",
            "Barbarian Subclass: Path of the Berserker",
            "Level 10: Retaliation",
        ),
        "When you take damage from a creature that is within 5 feet of you, you can take a Reaction to make one melee attack against that creature, using a weapon or an Unarmed Strike.",
    ),
    (
        (
            "Barbarian",
            "Barbarian Subclass: Path of the Berserker",
            "Level 14: Intimidating Presence",
        ),
        "#### Level 14: Intimidating Presence",
    ),
    (
        (
            "Barbarian",
            "Barbarian Subclass: Path of the Berserker",
            "Level 14: Intimidating Presence",
        ),
        "As a Bonus Action, you can strike terror into others with your menacing presence and primal power. When you do so, each creature of your choice in a 30-foot Emanation originating from you must make a Wisdom saving throw (DC 8 plus your Strength modifier and Proficiency Bonus). On a failed save, a creature has the Frightened condition for 1 minute. At the end of each of the Frightened creature's turns, the creature repeats the save, ending the effect on itself on a success.",
    ),
    (
        (
            "Barbarian",
            "Barbarian Subclass: Path of the Berserker",
            "Level 14: Intimidating Presence",
        ),
        "Once you use this feature, you can't use it again until you finish a Long Rest unless you expend a use of your Rage (no action required) to restore your use of it.",
    ),
    (("Bard",), "## Bard"),
    (
        ("Bard",),
        "**Core Bard Traits**\n\n<table>\n  <tbody>\n    <tr>\n      <td>Primary Ability</td>\n      <td>Charisma</td>\n    </tr>\n    <tr>\n      <td>Hit Point Die</td>\n      <td>D8 per Bard level</td>\n    </tr>\n    <tr>\n      <td>Saving Throw Proficiencies</td>\n      <td>Dexterity and Charisma</td>\n    </tr>\n    <tr>\n      <td>Skill Proficiencies</td>\n      <td>Choose any 3 skills (see Playing the Game)</td>\n    </tr>\n    <tr>\n      <td>Weapon Proficiencies</td>\n      <td>Simple weapons</td>\n    </tr>\n    <tr>\n      <td>Tool Proficiencies</td>\n      <td>Choose 3 Musical Instruments (see Equipment)</td>\n    </tr>\n    <tr>\n      <td>Armor Training</td>\n      <td>Light armor</td>\n    </tr>\n    <tr>\n      <td>Starting Equipment</td>\n      <td>Choose A or B: (A) Leather Armor, 2 Daggers, Musical Instrument of your choice, Entertainer's Pack, and 19 GP; or (B) 90 GP</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (("Bard", "Becoming a Bard …"), "### Becoming a Bard …"),
    (
        ("Bard", "Becoming a Bard …", "As a Level 1 Character"),
        "#### As a Level 1 Character",
    ),
    (
        ("Bard", "Becoming a Bard …", "As a Level 1 Character"),
        "• Gain all the traits in the Core Bard Traits table.",
    ),
    (
        ("Bard", "Becoming a Bard …", "As a Level 1 Character"),
        "• Gain the Bard's level 1 features, which are listed in the Bard Features table.",
    ),
    (
        ("Bard", "Becoming a Bard …", "As a Multiclass Character"),
        "#### As a Multiclass Character",
    ),
    (
        ("Bard", "Becoming a Bard …", "As a Multiclass Character"),
        '• Gain the following traits from the Core Bard Traits table: Hit Point Die, proficiency in one skill of your choice, proficiency with one Musical Instrument of your choice, and training with Light armor.\n• Gain the Bard\'s level 1 features, which are listed in the Bard Features table. See the multiclassing rules in "Character Creation" to determine your available spell slots.',
    ),
    (("Bard", "Bard Class Features"), "### Bard Class Features"),
    (
        ("Bard", "Bard Class Features"),
        "As a Bard, you gain the following class features when you reach the specified Bard levels. These features are listed in the Bard Features table.",
    ),
    (
        ("Bard", "Bard Class Features"),
        '**Bard Features**\n\n<table>\n  <thead>\n    <tr>\n      <th>Level</th>\n      <th>Proficiency Bonus</th>\n      <th>Class Features</th>\n      <th>Bardic Die</th>\n      <th>Cantrips</th>\n      <th>Prepared Spells</th>\n      <th colspan="9">——Spell Slots per Spell Level——</th>\n    </tr>\n    <tr>\n      <th>\n      </th>\n      <th>\n      </th>\n      <th>\n      </th>\n      <th>\n      </th>\n      <th>\n      </th>\n      <th>\n      </th>\n      <th>1</th>\n      <th>2</th>\n      <th>3</th>\n      <th>4</th>\n      <th>5</th>\n      <th>6</th>\n      <th>7</th>\n      <th>8</th>\n      <th>9</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>1</td>\n      <td>+2</td>\n      <td>Bardic Inspiration, Spellcasting</td>\n      <td>D6</td>\n      <td>2</td>\n      <td>4</td>\n      <td>2</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>2</td>\n      <td>+2</td>\n      <td>Expertise, Jack of All Trades</td>\n      <td>D6</td>\n      <td>2</td>\n      <td>5</td>\n      <td>3</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>3</td>\n      <td>+2</td>\n      <td>Bard Subclass</td>\n      <td>D6</td>\n      <td>2</td>\n      <td>6</td>\n      <td>4</td>\n      <td>2</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>4</td>\n      <td>+2</td>\n      <td>Ability Score Improvement</td>\n      <td>D6</td>\n      <td>3</td>\n      <td>7</td>\n      <td>4</td>\n      <td>3</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>5</td>\n      <td>+3</td>\n      <td>Font of Inspiration</td>\n      <td>D8</td>\n      <td>3</td>\n      <td>9</td>\n      <td>4</td>\n      <td>3</td>\n      <td>2</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>6</td>\n      <td>+3</td>\n      <td>Subclass feature</td>\n      <td>D8</td>\n      <td>3</td>\n      <td>10</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>7</td>\n      <td>+3</td>\n      <td>Countercharm</td>\n      <td>D8</td>\n      <td>3</td>\n      <td>11</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>1</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>8</td>\n      <td>+3</td>\n      <td>Ability Score Improvement</td>\n      <td>D8</td>\n      <td>3</td>\n      <td>12</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>2</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>9</td>\n      <td>+4</td>\n      <td>Expertise</td>\n      <td>D8</td>\n      <td>3</td>\n      <td>14</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>3</td>\n      <td>1</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>10</td>\n      <td>+4</td>\n      <td>Magical Secrets</td>\n      <td>D10</td>\n      <td>4</td>\n      <td>15</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>3</td>\n      <td>2</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>11</td>\n      <td>+4</td>\n      <td>—</td>\n      <td>D10</td>\n      <td>4</td>\n      <td>16</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>3</td>\n      <td>2</td>\n      <td>1</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>12</td>\n      <td>+4</td>\n      <td>Ability Score Improvement</td>\n      <td>D10</td>\n      <td>4</td>\n      <td>16</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>3</td>\n      <td>2</td>\n      <td>1</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>13</td>\n      <td>+5</td>\n      <td>—</td>\n      <td>D10</td>\n      <td>4</td>\n      <td>17</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>3</td>\n      <td>2</td>\n      <td>1</td>\n      <td>1</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>14</td>\n      <td>+5</td>\n      <td>Subclass feature</td>\n      <td>D10</td>\n      <td>4</td>\n      <td>17</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>3</td>\n      <td>2</td>\n      <td>1</td>\n      <td>1</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>15</td>\n      <td>+5</td>\n      <td>—</td>\n      <td>D12</td>\n      <td>4</td>\n      <td>18</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>3</td>\n      <td>2</td>\n      <td>1</td>\n      <td>1</td>\n      <td>1</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>16</td>\n      <td>+5</td>\n      <td>Ability Score Improvement</td>\n      <td>D12</td>\n      <td>4</td>\n      <td>18</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>3</td>\n      <td>2</td>\n      <td>1</td>\n      <td>1</td>\n      <td>1</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>17</td>\n      <td>+6</td>\n      <td>—</td>\n      <td>D12</td>\n      <td>4</td>\n      <td>19</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>3</td>\n      <td>2</td>\n      <td>1</td>\n      <td>1</td>\n      <td>1</td>\n      <td>1</td>\n    </tr>\n    <tr>\n      <td>18</td>\n      <td>+6</td>\n      <td>Superior Inspiration</td>\n      <td>D12</td>\n      <td>4</td>\n      <td>20</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>3</td>\n      <td>3</td>\n      <td>1</td>\n      <td>1</td>\n      <td>1</td>\n      <td>1</td>\n    </tr>\n    <tr>\n      <td>19</td>\n      <td>+6</td>\n      <td>Epic Boon</td>\n      <td>D12</td>\n      <td>4</td>\n      <td>21</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>3</td>\n      <td>3</td>\n      <td>2</td>\n      <td>1</td>\n      <td>1</td>\n      <td>1</td>\n    </tr>\n    <tr>\n      <td>20</td>\n      <td>+6</td>\n      <td>Words of Creation</td>\n      <td>D12</td>\n      <td>4</td>\n      <td>22</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>3</td>\n      <td>3</td>\n      <td>2</td>\n      <td>2</td>\n      <td>1</td>\n      <td>1</td>\n    </tr>\n  </tbody>\n</table>',
    ),
    (
        ("Bard", "Bard Class Features", "Level 1: Bardic Inspiration"),
        "#### Level 1: Bardic Inspiration",
    ),
    (
        ("Bard", "Bard Class Features", "Level 1: Bardic Inspiration"),
        "You can supernaturally inspire others through words, music, or dance. This inspiration is represented by your Bardic Inspiration die, which is a d6.",
    ),
    (
        ("Bard", "Bard Class Features", "Level 1: Bardic Inspiration"),
        "_Using Bardic Inspiration._ As a Bonus Action, you can inspire another creature within 60 feet of yourself who can see or hear you. That creature gains one of your Bardic Inspiration dice. A creature can have only one Bardic Inspiration die at a time.",
    ),
    (
        ("Bard", "Bard Class Features", "Level 1: Bardic Inspiration"),
        "Once within the next hour when the creature fails a D20 Test, the creature can roll the Bardic Inspiration die and add the number rolled to the d20, potentially turning the failure into a success. A Bardic Inspiration die is expended when it's rolled.",
    ),
    (
        ("Bard", "Bard Class Features", "Level 1: Bardic Inspiration"),
        "_Number of Uses._ You can confer a Bardic Inspiration die a number of times equal to your Charisma modifier (minimum of once), and you regain all expended uses when you finish a Long Rest.",
    ),
    (
        ("Bard", "Bard Class Features", "Level 1: Bardic Inspiration"),
        "_At Higher Levels._ Your Bardic Inspiration die changes when you reach certain Bard levels, as shown in the Bardic Die column of the Bard Features table. The die becomes a d8 at level 5, a d10 at level 10, and a d12 at level 15.",
    ),
    (
        ("Bard", "Bard Class Features", "Level 1: Spellcasting"),
        "#### Level 1: Spellcasting",
    ),
    (
        ("Bard", "Bard Class Features", "Level 1: Spellcasting"),
        'You have learned to cast spells through your bardic arts. See "Spells" for the rules on spellcasting. The information below details how you use those rules with Bard spells, which appear in the Bard spell list later in the class\'s description.',
    ),
    (
        ("Bard", "Bard Class Features", "Level 1: Spellcasting"),
        "_Cantrips._ You know two cantrips of your choice from the Bard spell list. _Dancing Lights_ and _Vicious Mockery_ are recommended.",
    ),
    (
        ("Bard", "Bard Class Features", "Level 1: Spellcasting"),
        "Whenever you gain a Bard level, you can replace one of your cantrips with another cantrip of your choice from the Bard spell list.",
    ),
    (
        ("Bard", "Bard Class Features", "Level 1: Spellcasting"),
        "When you reach Bard levels 4 and 10, you learn another cantrip of your choice from the Bard spell list, as shown in the Cantrips column of the Bard Features table.",
    ),
    (
        ("Bard", "Bard Class Features", "Level 1: Spellcasting"),
        "_Spell Slots._ The Bard Features table shows how many spell slots you have to cast your level 1+ spells. You regain all expended slots when you finish a Long Rest.",
    ),
    (
        ("Bard", "Bard Class Features", "Level 1: Spellcasting"),
        "_Prepared Spells of Level 1+._ You prepare the list of level 1+ spells that are available for you to cast with this feature. To start, choose four level 1 spells from the Bard spell list. _Charm Person_, _Color Spray_, _Dissonant Whispers_, and _Healing Word_ are recommended.",
    ),
    (
        ("Bard", "Bard Class Features", "Level 1: Spellcasting"),
        "The number of spells on your list increases as you gain Bard levels, as shown in the Prepared Spells column of the Bard Features table. Whenever that number increases, choose additional spells from the Bard spell list until the number of spells on your list matches the number on the table. The chosen spells must be of a level for which you have spell slots. For example, if you're a level 3 Bard, your list of prepared spells can include six spells of levels 1 and 2 in any combination.",
    ),
    (
        ("Bard", "Bard Class Features", "Level 1: Spellcasting"),
        "If another Bard feature gives you spells that you always have prepared, those spells don't count against the number of spells you can prepare with this feature, but those spells otherwise count as Bard spells for you.",
    ),
    (
        ("Bard", "Bard Class Features", "Level 1: Spellcasting"),
        "_Changing Your Prepared Spells._ Whenever you gain a Bard level, you can replace one spell on your list with another Bard spell for which you have spell slots.",
    ),
    (
        ("Bard", "Bard Class Features", "Level 1: Spellcasting"),
        "_Spellcasting Ability._ Charisma is your spellcasting ability for your Bard spells.",
    ),
    (
        ("Bard", "Bard Class Features", "Level 1: Spellcasting"),
        "_Spellcasting Focus._ You can use a Musical Instrument as a Spellcasting Focus for your Bard spells.",
    ),
    (("Bard", "Bard Class Features", "Level 2: Expertise"), "#### Level 2: Expertise"),
    (
        ("Bard", "Bard Class Features", "Level 2: Expertise"),
        'You gain Expertise (see "Rules Glossary") in two of your skill proficiencies of your choice. Performance and Persuasion are recommended if you have proficiency in them.',
    ),
    (
        ("Bard", "Bard Class Features", "Level 2: Expertise"),
        "At Bard level 9, you gain Expertise in two more of your skill proficiencies of your choice.",
    ),
    (
        ("Bard", "Bard Class Features", "Level 2: Jack of All Trades"),
        "#### Level 2: Jack of All Trades",
    ),
    (
        ("Bard", "Bard Class Features", "Level 2: Jack of All Trades"),
        "You can add half your Proficiency Bonus (round down) to any ability check you make that uses a skill proficiency you lack and that doesn't otherwise use your Proficiency Bonus.",
    ),
    (
        ("Bard", "Bard Class Features", "Level 2: Jack of All Trades"),
        "For example, if you make a Strength (Athletics) check and lack Athletics proficiency, you can add half your Proficiency Bonus to the check.",
    ),
    (
        ("Bard", "Bard Class Features", "Level 3: Bard Subclass"),
        "#### Level 3: Bard Subclass",
    ),
    (
        ("Bard", "Bard Class Features", "Level 3: Bard Subclass"),
        "You gain a Bard subclass of your choice. The College of Lore subclass is detailed after this class's description. A subclass is a specialization that grants you features at certain Bard levels. For the rest of your career, you gain each of your subclass's features that are of your Bard level or lower.",
    ),
    (
        ("Bard", "Bard Class Features", "Level 4: Ability Score Improvement"),
        "#### Level 4: Ability Score Improvement",
    ),
    (
        ("Bard", "Bard Class Features", "Level 4: Ability Score Improvement"),
        'You gain the Ability Score Improvement feat (see "Feats") or another feat of your choice for which you qualify. You gain this feature again at Bard levels 8, 12, and 16.',
    ),
    (
        ("Bard", "Bard Class Features", "Level 5: Font of Inspiration"),
        "#### Level 5: Font of Inspiration",
    ),
    (
        ("Bard", "Bard Class Features", "Level 5: Font of Inspiration"),
        "You now regain all your expended uses of Bardic Inspiration when you finish a Short or Long Rest.",
    ),
    (
        ("Bard", "Bard Class Features", "Level 5: Font of Inspiration"),
        "In addition, you can expend a spell slot (no action required) to regain one expended use of Bardic Inspiration.",
    ),
    (
        ("Bard", "Bard Class Features", "Level 7: Countercharm"),
        "#### Level 7: Countercharm",
    ),
    (
        ("Bard", "Bard Class Features", "Level 7: Countercharm"),
        "You can use musical notes or words of power to disrupt mind-influencing effects. If you or a creature within 30 feet of you fails a saving throw against an effect that applies the Charmed or Frightened condition, you can take a Reaction to cause the save to be rerolled, and the new roll has Advantage.",
    ),
    (
        ("Bard", "Bard Class Features", "Level 10: Magical Secrets"),
        "#### Level 10: Magical Secrets",
    ),
    (
        ("Bard", "Bard Class Features", "Level 10: Magical Secrets"),
        "You've learned secrets from various magical traditions. Whenever you reach a Bard level (including this level) and the Prepared Spells number in the Bard Features table increases, you can choose any of your new prepared spells from the Bard, Cleric, Druid, and Wizard spell lists, and the chosen spells count as Bard spells for you (see a class's section for its spell list). In addition, whenever you replace a spell prepared for this class, you can replace it with a spell from those lists.",
    ),
    (
        ("Bard", "Bard Class Features", "Level 18: Superior Inspiration"),
        "#### Level 18: Superior Inspiration",
    ),
    (
        ("Bard", "Bard Class Features", "Level 18: Superior Inspiration"),
        "When you roll Initiative, you regain expended uses of Bardic Inspiration until you have two if you have fewer than that.",
    ),
    (
        ("Bard", "Bard Class Features", "Level 19: Epic Boon"),
        "#### Level 19: Epic Boon",
    ),
    (
        ("Bard", "Bard Class Features", "Level 19: Epic Boon"),
        'You gain an Epic Boon feat (see "Feats") or another feat of your choice for which you qualify. Boon of Spell Recall is recommended.',
    ),
    (
        ("Bard", "Bard Class Features", "Level 20: Words of Creation"),
        "#### Level 20: Words of Creation",
    ),
    (
        ("Bard", "Bard Class Features", "Level 20: Words of Creation"),
        "You have mastered two of the Words of Creation: the words of life and death. You therefore always have the _Power Word Heal_ and _Power Word Kill_ spells prepared. When you cast either spell, you can target a second creature with it if that creature is within 10 feet of the first target.",
    ),
    (("Bard", "Bard Spell List"), "### Bard Spell List"),
    (
        ("Bard", "Bard Spell List"),
        "This section presents the Bard spell list. The spells are organized by spell level and then alphabetized, and each spell's school of magic is listed. In the Special column, _C_ means the spell requires Concentration, _R_ means it's a Ritual, and _M_ means it requires a specific Material component.",
    ),
    (
        ("Bard", "Bard Spell List", "Cantrips (Level 0 Bard Spells)"),
        "#### Cantrips (Level 0 Bard Spells)",
    ),
    (
        ("Bard", "Bard Spell List", "Cantrips (Level 0 Bard Spells)"),
        "<table>\n  <thead>\n    <tr>\n      <th>Spell</th>\n      <th>School</th>\n      <th>Special</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>Dancing Lights</td>\n      <td>Illusion</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Light</td>\n      <td>Evocation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Mage Hand</td>\n      <td>Conjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Mending</td>\n      <td>Transmutation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Message</td>\n      <td>Transmutation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Minor Illusion</td>\n      <td>Illusion</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Prestidigitation</td>\n      <td>Transmutation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Starry Wisp</td>\n      <td>Evocation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>True Strike</td>\n      <td>Divination</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Vicious Mockery</td>\n      <td>Enchantment</td>\n      <td>—</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (("Bard", "Bard Spell List", "Level 1 Bard Spells"), "#### Level 1 Bard Spells"),
    (
        ("Bard", "Bard Spell List", "Level 1 Bard Spells"),
        "<table>\n  <thead>\n    <tr>\n      <th>Spell</th>\n      <th>School</th>\n      <th>Special</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>Animal Friendship</td>\n      <td>Enchantment</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Bane</td>\n      <td>Enchantment</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Charm Person</td>\n      <td>Enchantment</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Color Spray</td>\n      <td>Illusion</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Command</td>\n      <td>Enchantment</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Comprehend Languages</td>\n      <td>Divination</td>\n      <td>R</td>\n    </tr>\n    <tr>\n      <td>Cure Wounds</td>\n      <td>Abjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Detect Magic</td>\n      <td>Divination</td>\n      <td>C, R</td>\n    </tr>\n    <tr>\n      <td>Disguise Self</td>\n      <td>Illusion</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Dissonant Whispers</td>\n      <td>Enchantment</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Faerie Fire</td>\n      <td>Evocation</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Feather Fall</td>\n      <td>Transmutation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Healing Word</td>\n      <td>Abjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Heroism</td>\n      <td>Enchantment</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Hideous Laughter</td>\n      <td>Enchantment</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Identify</td>\n      <td>Divination</td>\n      <td>R, M</td>\n    </tr>\n    <tr>\n      <td>Illusory Script</td>\n      <td>Illusion</td>\n      <td>R, M</td>\n    </tr>\n    <tr>\n      <td>Longstrider</td>\n      <td>Transmutation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Silent Image</td>\n      <td>Illusion</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Sleep</td>\n      <td>Enchantment</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Speak with Animals</td>\n      <td>Divination</td>\n      <td>R</td>\n    </tr>\n    <tr>\n      <td>Thunderwave</td>\n      <td>Evocation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Unseen Servant</td>\n      <td>Conjuration</td>\n      <td>R</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (("Bard", "Bard Spell List", "Level 2 Bard Spells"), "#### Level 2 Bard Spells"),
    (
        ("Bard", "Bard Spell List", "Level 2 Bard Spells"),
        "<table>\n  <thead>\n    <tr>\n      <th>Spell</th>\n      <th>School</th>\n      <th>Special</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>Aid</td>\n      <td>Abjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Animal Messenger</td>\n      <td>Enchantment</td>\n      <td>R</td>\n    </tr>\n    <tr>\n      <td>Blindness/Deafness</td>\n      <td>Transmutation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Calm Emotions</td>\n      <td>Enchantment</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Detect Thoughts</td>\n      <td>Divination</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Enhance Ability</td>\n      <td>Transmutation</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Enlarge/Reduce</td>\n      <td>Transmutation</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Enthrall</td>\n      <td>Enchantment</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Heat Metal</td>\n      <td>Transmutation</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Hold Person</td>\n      <td>Enchantment</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Invisibility</td>\n      <td>Illusion</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Knock</td>\n      <td>Transmutation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Lesser Restoration</td>\n      <td>Abjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Locate Animals or Plants</td>\n      <td>Divination</td>\n      <td>R</td>\n    </tr>\n    <tr>\n      <td>Locate Object</td>\n      <td>Divination</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Magic Mouth</td>\n      <td>Illusion</td>\n      <td>R, M</td>\n    </tr>\n    <tr>\n      <td>Mirror Image</td>\n      <td>Illusion</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Phantasmal Force</td>\n      <td>Illusion</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>See Invisibility</td>\n      <td>Divination</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Shatter</td>\n      <td>Evocation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Silence</td>\n      <td>Illusion</td>\n      <td>C, R</td>\n    </tr>\n    <tr>\n      <td>Suggestion</td>\n      <td>Enchantment</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Zone of Truth</td>\n      <td>Enchantment</td>\n      <td>—</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (("Bard", "Bard Spell List", "Level 3 Bard Spells"), "#### Level 3 Bard Spells"),
    (
        ("Bard", "Bard Spell List", "Level 3 Bard Spells"),
        "<table>\n  <thead>\n    <tr>\n      <th>Spell</th>\n      <th>School</th>\n      <th>Special</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>Bestow Curse</td>\n      <td>Necromancy</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Clairvoyance</td>\n      <td>Divination</td>\n      <td>C, M</td>\n    </tr>\n    <tr>\n      <td>Dispel Magic</td>\n      <td>Abjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Fear</td>\n      <td>Illusion</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Glyph of Warding</td>\n      <td>Abjuration</td>\n      <td>M</td>\n    </tr>\n    <tr>\n      <td>Hypnotic Pattern</td>\n      <td>Illusion</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Major Image</td>\n      <td>Illusion</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Mass Healing Word</td>\n      <td>Abjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Nondetection</td>\n      <td>Abjuration</td>\n      <td>M</td>\n    </tr>\n    <tr>\n      <td>Plant Growth</td>\n      <td>Transmutation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Sending</td>\n      <td>Divination</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Slow</td>\n      <td>Transmutation</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Speak with Dead</td>\n      <td>Necromancy</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Speak with Plants</td>\n      <td>Transmutation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Stinking Cloud</td>\n      <td>Conjuration</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Tiny Hut</td>\n      <td>Evocation</td>\n      <td>R</td>\n    </tr>\n    <tr>\n      <td>Tongues</td>\n      <td>Divination</td>\n      <td>—</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (("Bard", "Bard Spell List", "Level 4 Bard Spells"), "#### Level 4 Bard Spells"),
    (
        ("Bard", "Bard Spell List", "Level 4 Bard Spells"),
        "<table>\n  <thead>\n    <tr>\n      <th>Spell</th>\n      <th>School</th>\n      <th>Special</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>Charm Monster</td>\n      <td>Enchantment</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Compulsion</td>\n      <td>Enchantment</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Confusion</td>\n      <td>Enchantment</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Dimension Door</td>\n      <td>Conjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Freedom of Movement</td>\n      <td>Abjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Greater Invisibility</td>\n      <td>Illusion</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Hallucinatory Terrain</td>\n      <td>Illusion</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Locate Creature</td>\n      <td>Divination</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Phantasmal Killer</td>\n      <td>Illusion</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Polymorph</td>\n      <td>Transmutation</td>\n      <td>C</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (("Bard", "Bard Spell List", "Level 5 Bard Spells"), "#### Level 5 Bard Spells"),
    (
        ("Bard", "Bard Spell List", "Level 5 Bard Spells"),
        "<table>\n  <thead>\n    <tr>\n      <th>Spell</th>\n      <th>School</th>\n      <th>Special</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>Animate Objects</td>\n      <td>Transmutation</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Awaken</td>\n      <td>Transmutation</td>\n      <td>M</td>\n    </tr>\n    <tr>\n      <td>Dominate Person</td>\n      <td>Enchantment</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Dream</td>\n      <td>Illusion</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Geas</td>\n      <td>Enchantment</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Greater Restoration</td>\n      <td>Abjuration</td>\n      <td>M</td>\n    </tr>\n    <tr>\n      <td>Hold Monster</td>\n      <td>Enchantment</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Legend Lore</td>\n      <td>Divination</td>\n      <td>M</td>\n    </tr>\n    <tr>\n      <td>Mass Cure Wounds</td>\n      <td>Abjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Mislead</td>\n      <td>Illusion</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Modify Memory</td>\n      <td>Enchantment</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Planar Binding</td>\n      <td>Abjuration</td>\n      <td>M</td>\n    </tr>\n    <tr>\n      <td>Raise Dead</td>\n      <td>Necromancy</td>\n      <td>M</td>\n    </tr>\n    <tr>\n      <td>Scrying</td>\n      <td>Divination</td>\n      <td>C, M</td>\n    </tr>\n    <tr>\n      <td>Seeming</td>\n      <td>Illusion</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Telepathic Bond</td>\n      <td>Divination</td>\n      <td>R</td>\n    </tr>\n    <tr>\n      <td>Teleportation Circle</td>\n      <td>Conjuration</td>\n      <td>M</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (("Bard", "Bard Spell List", "Level 6 Bard Spells"), "#### Level 6 Bard Spells"),
    (
        ("Bard", "Bard Spell List", "Level 6 Bard Spells"),
        "<table>\n  <thead>\n    <tr>\n      <th>Spell</th>\n      <th>School</th>\n      <th>Special</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>Eyebite</td>\n      <td>Necromancy</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Find the Path</td>\n      <td>Divination</td>\n      <td>C, M</td>\n    </tr>\n    <tr>\n      <td>Guards and Wards</td>\n      <td>Abjuration</td>\n      <td>M</td>\n    </tr>\n    <tr>\n      <td>Heroes' Feast</td>\n      <td>Conjuration</td>\n      <td>M</td>\n    </tr>\n    <tr>\n      <td>Irresistible Dance</td>\n      <td>Enchantment</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Mass Suggestion</td>\n      <td>Enchantment</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Programmed Illusion</td>\n      <td>Illusion</td>\n      <td>M</td>\n    </tr>\n    <tr>\n      <td>True Seeing</td>\n      <td>Divination</td>\n      <td>M</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (("Bard", "Bard Spell List", "Level 7 Bard Spells"), "#### Level 7 Bard Spells"),
    (
        ("Bard", "Bard Spell List", "Level 7 Bard Spells"),
        "<table>\n  <thead>\n    <tr>\n      <th>Spell</th>\n      <th>School</th>\n      <th>Special</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>Arcane Sword</td>\n      <td>Evocation</td>\n      <td>C, M</td>\n    </tr>\n    <tr>\n      <td>Etherealness</td>\n      <td>Conjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Forcecage</td>\n      <td>Evocation</td>\n      <td>C, M</td>\n    </tr>\n    <tr>\n      <td>Magnificent Mansion</td>\n      <td>Conjuration</td>\n      <td>M</td>\n    </tr>\n    <tr>\n      <td>Mirage Arcane</td>\n      <td>Illusion</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Prismatic Spray</td>\n      <td>Evocation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Project Image</td>\n      <td>Illusion</td>\n      <td>C, M</td>\n    </tr>\n    <tr>\n      <td>Regenerate</td>\n      <td>Transmutation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Resurrection</td>\n      <td>Necromancy</td>\n      <td>M</td>\n    </tr>\n    <tr>\n      <td>Symbol</td>\n      <td>Abjuration</td>\n      <td>M</td>\n    </tr>\n    <tr>\n      <td>Teleport</td>\n      <td>Conjuration</td>\n      <td>—</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (("Bard", "Bard Spell List", "Level 8 Bard Spells"), "#### Level 8 Bard Spells"),
    (
        ("Bard", "Bard Spell List", "Level 8 Bard Spells"),
        "<table>\n  <thead>\n    <tr>\n      <th>Spell</th>\n      <th>School</th>\n      <th>Special</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>Antipathy/Sympathy</td>\n      <td>Enchantment</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Befuddlement</td>\n      <td>Enchantment</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Dominate Monster</td>\n      <td>Enchantment</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Glibness</td>\n      <td>Enchantment</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Mind Blank</td>\n      <td>Abjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Power Word Stun</td>\n      <td>Enchantment</td>\n      <td>—</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (("Bard", "Bard Spell List", "Level 9 Bard Spells"), "#### Level 9 Bard Spells"),
    (
        ("Bard", "Bard Spell List", "Level 9 Bard Spells"),
        "<table>\n  <thead>\n    <tr>\n      <th>Spell</th>\n      <th>School</th>\n      <th>Special</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>Foresight</td>\n      <td>Divination</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Power Word Heal</td>\n      <td>Enchantment</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Power Word Kill</td>\n      <td>Enchantment</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Prismatic Wall</td>\n      <td>Abjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>True Polymorph</td>\n      <td>Transmutation</td>\n      <td>C</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (("Bard", "Bard Subclass: College of Lore"), "### Bard Subclass: College of Lore"),
    (
        ("Bard", "Bard Subclass: College of Lore"),
        "_Plumb the Depths of Magical Knowledge_",
    ),
    (
        ("Bard", "Bard Subclass: College of Lore"),
        "Bards of the College of Lore collect spells and secrets from diverse sources, such as scholarly tomes, mystical rites, and peasant tales. The college's members gather in libraries and universities to share their lore with one another. They also meet at festivals or affairs of state, where they can expose corruption, unravel lies, and poke fun at self-important figures of authority.",
    ),
    (
        ("Bard", "Bard Subclass: College of Lore", "Level 3: Bonus Proficiencies"),
        "#### Level 3: Bonus Proficiencies",
    ),
    (
        ("Bard", "Bard Subclass: College of Lore", "Level 3: Bonus Proficiencies"),
        "You gain proficiency with three skills of your choice.",
    ),
    (
        ("Bard", "Bard Subclass: College of Lore", "Level 3: Cutting Words"),
        "#### Level 3: Cutting Words",
    ),
    (
        ("Bard", "Bard Subclass: College of Lore", "Level 3: Cutting Words"),
        "You learn to use your wit to supernaturally distract, confuse, and otherwise sap the confidence and competence of others. When a creature that you can see within 60 feet of yourself makes a damage roll or succeeds on an ability check or attack roll, you can take a Reaction to expend one use of your Bardic Inspiration; roll your Bardic Inspiration die, and subtract the number rolled from the creature's roll, reducing the damage or potentially turning the success into a failure.",
    ),
    (
        ("Bard", "Bard Subclass: College of Lore", "Level 6: Magical Discoveries"),
        "#### Level 6: Magical Discoveries",
    ),
    (
        ("Bard", "Bard Subclass: College of Lore", "Level 6: Magical Discoveries"),
        "You learn two spells of your choice. These spells can come from the Cleric, Druid, or Wizard spell list or any combination thereof (see a class's section for its spell list). A spell you choose must be a cantrip or a spell for which you have spell slots, as shown in the Bard Features table.",
    ),
    (
        ("Bard", "Bard Subclass: College of Lore", "Level 6: Magical Discoveries"),
        "You always have the chosen spells prepared, and whenever you gain a Bard level, you can replace one of the spells with another spell that meets these requirements.",
    ),
    (
        ("Bard", "Bard Subclass: College of Lore", "Level 14: Peerless Skill"),
        "#### Level 14: Peerless Skill",
    ),
    (
        ("Bard", "Bard Subclass: College of Lore", "Level 14: Peerless Skill"),
        "When you make an ability check or attack roll and fail, you can expend one use of Bardic Inspiration; roll the Bardic Inspiration die, and add the number rolled to the d20, potentially turning a failure into a success. On a failure, the Bardic Inspiration isn't expended.",
    ),
    (("Cleric",), "## Cleric"),
    (
        ("Cleric",),
        "**Core Cleric Traits**\n\n<table>\n  <tbody>\n    <tr>\n      <td>Primary Ability</td>\n      <td>Wisdom</td>\n    </tr>\n    <tr>\n      <td>Hit Point Die</td>\n      <td>D8 per Cleric level</td>\n    </tr>\n    <tr>\n      <td>Saving Throw Proficiencies</td>\n      <td>Wisdom and Charisma</td>\n    </tr>\n    <tr>\n      <td>Skill Proficiencies</td>\n      <td>Choose 2: History, Insight, Medicine, Persuasion, or Religion</td>\n    </tr>\n    <tr>\n      <td>Weapon Proficiencies</td>\n      <td>Simple weapons</td>\n    </tr>\n    <tr>\n      <td>Armor Training</td>\n      <td>Light and Medium armor and Shields</td>\n    </tr>\n    <tr>\n      <td>Starting Equipment</td>\n      <td>Choose A or B: (A) Chain Shirt, Shield, Mace, Holy Symbol, Priest's Pack, and 7 GP; or (B) 110 GP</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (("Cleric", "Becoming a Cleric …"), "### Becoming a Cleric …"),
    (
        ("Cleric", "Becoming a Cleric …", "As a Level 1 Character"),
        "#### As a Level 1 Character",
    ),
    (
        ("Cleric", "Becoming a Cleric …", "As a Level 1 Character"),
        "- Gain all the traits in the Core Cleric Traits table.\n- Gain the Cleric's level 1 features, which are listed in the Cleric Features table.",
    ),
    (
        ("Cleric", "Becoming a Cleric …", "As a Multiclass Character"),
        "#### As a Multiclass Character",
    ),
    (
        ("Cleric", "Becoming a Cleric …", "As a Multiclass Character"),
        '- Gain the following traits from the Core Cleric Traits table: Hit Point Die and training with Light and Medium armor and Shields.\n- Gain the Cleric\'s level 1 features, which are listed in the Cleric Features table. See the multiclassing rules in "Character Creation" to determine your available spell slots.',
    ),
    (("Cleric", "Cleric Class Features"), "### Cleric Class Features"),
    (
        ("Cleric", "Cleric Class Features"),
        "As a Cleric, you gain the following class features when you reach the specified Cleric levels. These features are listed in the Cleric Features table.",
    ),
    (
        ("Cleric", "Cleric Class Features"),
        '**Cleric Features**\n\n<table>\n  <thead>\n    <tr>\n      <th>Level</th>\n      <th>Proficiency Bonus</th>\n      <th>Class Features</th>\n      <th>Channel Divinity</th>\n      <th>Cantrips</th>\n      <th>Prepared Spells</th>\n      <th colspan="9">——Spell Slots per Spell Level——</th>\n    </tr>\n    <tr>\n      <th>\n      </th>\n      <th>\n      </th>\n      <th>\n      </th>\n      <th>\n      </th>\n      <th>\n      </th>\n      <th>\n      </th>\n      <th>1</th>\n      <th>2</th>\n      <th>3</th>\n      <th>4</th>\n      <th>5</th>\n      <th>6</th>\n      <th>7</th>\n      <th>8</th>\n      <th>9</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>1</td>\n      <td>+2</td>\n      <td>Spellcasting, Divine Order</td>\n      <td>—</td>\n      <td>3</td>\n      <td>4</td>\n      <td>2</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>2</td>\n      <td>+2</td>\n      <td>Channel Divinity</td>\n      <td>2</td>\n      <td>3</td>\n      <td>5</td>\n      <td>3</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>3</td>\n      <td>+2</td>\n      <td>Cleric Subclass</td>\n      <td>2</td>\n      <td>3</td>\n      <td>6</td>\n      <td>4</td>\n      <td>2</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>4</td>\n      <td>+2</td>\n      <td>Ability Score Improvement</td>\n      <td>2</td>\n      <td>4</td>\n      <td>7</td>\n      <td>4</td>\n      <td>3</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>5</td>\n      <td>+3</td>\n      <td>Sear Undead</td>\n      <td>2</td>\n      <td>4</td>\n      <td>9</td>\n      <td>4</td>\n      <td>3</td>\n      <td>2</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>6</td>\n      <td>+3</td>\n      <td>Subclass feature</td>\n      <td>3</td>\n      <td>4</td>\n      <td>10</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>7</td>\n      <td>+3</td>\n      <td>Blessed Strikes</td>\n      <td>3</td>\n      <td>4</td>\n      <td>11</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>1</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>8</td>\n      <td>+3</td>\n      <td>Ability Score Improvement</td>\n      <td>3</td>\n      <td>4</td>\n      <td>12</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>2</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>9</td>\n      <td>+4</td>\n      <td>—</td>\n      <td>3</td>\n      <td>4</td>\n      <td>14</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>3</td>\n      <td>1</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>10</td>\n      <td>+4</td>\n      <td>Divine Intervention</td>\n      <td>3</td>\n      <td>5</td>\n      <td>15</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>3</td>\n      <td>2</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>11</td>\n      <td>+4</td>\n      <td>—</td>\n      <td>3</td>\n      <td>5</td>\n      <td>16</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>3</td>\n      <td>2</td>\n      <td>1</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>12</td>\n      <td>+4</td>\n      <td>Ability Score Improvement</td>\n      <td>3</td>\n      <td>5</td>\n      <td>16</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>3</td>\n      <td>2</td>\n      <td>1</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>13</td>\n      <td>+5</td>\n      <td>—</td>\n      <td>3</td>\n      <td>5</td>\n      <td>17</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>3</td>\n      <td>2</td>\n      <td>1</td>\n      <td>1</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>14</td>\n      <td>+5</td>\n      <td>Improved Blessed Strikes</td>\n      <td>3</td>\n      <td>5</td>\n      <td>17</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>3</td>\n      <td>2</td>\n      <td>1</td>\n      <td>1</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>15</td>\n      <td>+5</td>\n      <td>—</td>\n      <td>3</td>\n      <td>5</td>\n      <td>18</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>3</td>\n      <td>2</td>\n      <td>1</td>\n      <td>1</td>\n      <td>1</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>16</td>\n      <td>+5</td>\n      <td>Ability Score Improvement</td>\n      <td>3</td>\n      <td>5</td>\n      <td>18</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>3</td>\n      <td>2</td>\n      <td>1</td>\n      <td>1</td>\n      <td>1</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>17</td>\n      <td>+6</td>\n      <td>Subclass feature</td>\n      <td>3</td>\n      <td>5</td>\n      <td>19</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>3</td>\n      <td>2</td>\n      <td>1</td>\n      <td>1</td>\n      <td>1</td>\n      <td>1</td>\n    </tr>\n    <tr>\n      <td>18</td>\n      <td>+6</td>\n      <td>—</td>\n      <td>4</td>\n      <td>5</td>\n      <td>20</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>3</td>\n      <td>3</td>\n      <td>1</td>\n      <td>1</td>\n      <td>1</td>\n      <td>1</td>\n    </tr>\n    <tr>\n      <td>19</td>\n      <td>+6</td>\n      <td>Epic Boon</td>\n      <td>4</td>\n      <td>5</td>\n      <td>21</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>3</td>\n      <td>3</td>\n      <td>2</td>\n      <td>1</td>\n      <td>1</td>\n      <td>1</td>\n    </tr>\n    <tr>\n      <td>20</td>\n      <td>+6</td>\n      <td>Greater Divine Intervention</td>\n      <td>4</td>\n      <td>5</td>\n      <td>22</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>3</td>\n      <td>3</td>\n      <td>2</td>\n      <td>2</td>\n      <td>1</td>\n      <td>1</td>\n    </tr>\n  </tbody>\n</table>',
    ),
    (
        ("Cleric", "Cleric Class Features", "Level 1: Spellcasting"),
        "#### Level 1: Spellcasting",
    ),
    (
        ("Cleric", "Cleric Class Features", "Level 1: Spellcasting"),
        'You have learned to cast spells through prayer and meditation. See "Spells" for the rules on spellcasting. The information below details how you use those rules with Cleric spells, which appear on the Cleric spell list later in the class\'s description.',
    ),
    (
        ("Cleric", "Cleric Class Features", "Level 1: Spellcasting"),
        "_Cantrips._ You know three cantrips of your choice from the Cleric spell list. _Guidance_, _Sacred Flame_, and _Thaumaturgy_ are recommended.",
    ),
    (
        ("Cleric", "Cleric Class Features", "Level 1: Spellcasting"),
        "Whenever you gain a Cleric level, you can replace one of your cantrips with another cantrip of your choice from the Cleric spell list.",
    ),
    (
        ("Cleric", "Cleric Class Features", "Level 1: Spellcasting"),
        "When you reach Cleric levels 4 and 10, you learn another cantrip of your choice from the Cleric spell list, as shown in the Cantrips column of the Cleric Features table.",
    ),
    (
        ("Cleric", "Cleric Class Features", "Level 1: Spellcasting"),
        "_Spell Slots._ The Cleric Features table shows how many spell slots you have to cast your level 1+ spells. You regain all expended slots when you finish a Long Rest.",
    ),
    (
        ("Cleric", "Cleric Class Features", "Level 1: Spellcasting"),
        "_Prepared Spells of Level 1+._ You prepare the list of level 1+ spells that are available for you to cast with this feature. To start, choose four level 1 spells from the Cleric spell list. _Bless_, _Cure Wounds_, _Guiding Bolt_, and _Shield of Faith_ are recommended.",
    ),
    (
        ("Cleric", "Cleric Class Features", "Level 1: Spellcasting"),
        "The number of spells on your list increases as you gain Cleric levels, as shown in the Prepared Spells column of the Cleric Features table. Whenever that number increases, choose additional spells from the Cleric spell list until the number of spells on your list matches the number on the table. The chosen spells must be of a level for which you have spell slots. For example, if you're a level 3 Cleric, your list of prepared spells can include six spells of levels 1 and 2 in any combination.",
    ),
    (
        ("Cleric", "Cleric Class Features", "Level 1: Spellcasting"),
        "If another Cleric feature gives you spells that you always have prepared, those spells don't count against the number of spells you can prepare with this feature, but those spells otherwise count as Cleric spells for you.",
    ),
    (
        ("Cleric", "Cleric Class Features", "Level 1: Spellcasting"),
        "_Changing Your Prepared Spells._ Whenever you finish a Long Rest, you can change your list of prepared spells, replacing any of the spells there with other Cleric spells for which you have spell slots.",
    ),
    (
        ("Cleric", "Cleric Class Features", "Level 1: Spellcasting"),
        "_Spellcasting Ability._ Wisdom is your spellcasting ability for your Cleric spells.",
    ),
    (
        ("Cleric", "Cleric Class Features", "Level 1: Spellcasting"),
        "_Spellcasting Focus._ You can use a Holy Symbol as a Spellcasting Focus for your Cleric spells.",
    ),
    (
        ("Cleric", "Cleric Class Features", "Level 1: Divine Order"),
        "#### Level 1: Divine Order",
    ),
    (
        ("Cleric", "Cleric Class Features", "Level 1: Divine Order"),
        "You have dedicated yourself to one of the following sacred roles of your choice.",
    ),
    (
        ("Cleric", "Cleric Class Features", "Level 1: Divine Order"),
        "_Protector._ Trained for battle, you gain proficiency with Martial weapons and training with Heavy armor.",
    ),
    (
        ("Cleric", "Cleric Class Features", "Level 1: Divine Order"),
        "_Thaumaturge._ You know one extra cantrip from the Cleric spell list. In addition, your mystical connection to the divine gives you a bonus to your Intelligence (Arcana or Religion) checks. The bonus equals your Wisdom modifier (minimum of +1).",
    ),
    (
        ("Cleric", "Cleric Class Features", "Level 2: Channel Divinity"),
        "#### Level 2: Channel Divinity",
    ),
    (
        ("Cleric", "Cleric Class Features", "Level 2: Channel Divinity"),
        "You can channel divine energy directly from the Outer Planes to fuel magical effects. You start with two such effects: Divine Spark and Turn Undead, each of which is described below. Each time you use this class's Channel Divinity, choose which Channel Divinity effect from this class to create. You gain additional effect options at higher Cleric levels.",
    ),
    (
        ("Cleric", "Cleric Class Features", "Level 2: Channel Divinity"),
        "You can use this class's Channel Divinity twice. You regain one of its expended uses when you finish a Short Rest, and you regain all expended uses when you finish a Long Rest. You gain additional uses when you reach certain Cleric levels, as shown in the Channel Divinity column of the Cleric Features table.",
    ),
    (
        ("Cleric", "Cleric Class Features", "Level 2: Channel Divinity"),
        "If a Channel Divinity effect requires a saving throw, the DC equals the spell save DC from this class's Spellcasting feature.",
    ),
    (
        ("Cleric", "Cleric Class Features", "Level 2: Channel Divinity"),
        "_Divine Spark._ As a Magic action, you point your Holy Symbol at another creature you can see within 30 feet of yourself and focus divine energy at it. Roll 1d8 and add your Wisdom modifier. You either restore Hit Points to the creature equal to that total or force the creature to make a Constitution saving throw. On a failed save, the creature takes Necrotic or Radiant damage (your choice) equal to that total. On a successful save, the creature takes half as much damage (round down).",
    ),
    (
        ("Cleric", "Cleric Class Features", "Level 2: Channel Divinity"),
        "You roll an additional d8 when you reach Cleric levels 7 (2d8), 13 (3d8), and 18 (4d8).",
    ),
    (
        ("Cleric", "Cleric Class Features", "Level 2: Channel Divinity"),
        "_Turn Undead._ As a Magic action, you present your Holy Symbol and censure Undead creatures. Each Undead of your choice within 30 feet of you must make a Wisdom saving throw. If the creature fails its save, it has the Frightened and Incapacitated conditions for 1 minute. For that duration, it tries to move as far from you as it can on its turns. This effect ends early on the creature if it takes any damage, if you have the Incapacitated condition, or if you die.",
    ),
    (
        ("Cleric", "Cleric Class Features", "Level 3: Cleric Subclass"),
        "#### Level 3: Cleric Subclass",
    ),
    (
        ("Cleric", "Cleric Class Features", "Level 3: Cleric Subclass"),
        "You gain a Cleric subclass of your choice. The Life Domain subclass is detailed after this class's description. A subclass is a specialization that grants you features at certain Cleric levels. For the rest of your career, you gain each of your subclass's features that are of your Cleric level or lower.",
    ),
    (
        ("Cleric", "Cleric Class Features", "Level 4: Ability Score Improvement"),
        "#### Level 4: Ability Score Improvement",
    ),
    (
        ("Cleric", "Cleric Class Features", "Level 4: Ability Score Improvement"),
        'You gain the Ability Score Improvement feat (see "Feats") or another feat of your choice for which you qualify. You gain this feature again at Cleric levels 8, 12, and 16.',
    ),
    (
        ("Cleric", "Cleric Class Features", "Level 5: Sear Undead"),
        "#### Level 5: Sear Undead",
    ),
    (
        ("Cleric", "Cleric Class Features", "Level 5: Sear Undead"),
        "Whenever you use Turn Undead, you can roll a number of d8s equal to your Wisdom modifier (minimum of 1d8) and add the rolls together. Each Undead that fails its saving throw against that use of Turn Undead takes Radiant damage equal to the roll's total. This damage doesn't end the turn effect.",
    ),
    (
        ("Cleric", "Cleric Class Features", "Level 7: Blessed Strikes"),
        "#### Level 7: Blessed Strikes",
    ),
    (
        ("Cleric", "Cleric Class Features", "Level 7: Blessed Strikes"),
        "Divine power infuses you in battle. You gain one of the following options of your choice (if you get either option from a Cleric subclass in an older book, use only the option you choose for this feature).",
    ),
    (
        ("Cleric", "Cleric Class Features", "Level 7: Blessed Strikes"),
        "_Divine Strike._ Once on each of your turns when you hit a creature with an attack roll using a weapon, you can cause the target to take an extra 1d8 Necrotic or Radiant damage (your choice).",
    ),
    (
        ("Cleric", "Cleric Class Features", "Level 7: Blessed Strikes"),
        "_Potent Spellcasting._ Add your Wisdom modifier to the damage you deal with any Cleric cantrip.",
    ),
    (
        ("Cleric", "Cleric Class Features", "Level 10: Divine Intervention"),
        "#### Level 10: Divine Intervention",
    ),
    (
        ("Cleric", "Cleric Class Features", "Level 10: Divine Intervention"),
        "You can call on your deity or pantheon to intervene on your behalf. As a Magic action, choose any Cleric spell of level 5 or lower that doesn't require a Reaction to cast. As part of the same action, you cast that spell without expending a spell slot or needing Material components. You can't use this feature again until you finish a Long Rest.",
    ),
    (
        ("Cleric", "Cleric Class Features", "Level 14: Improved Blessed Strikes"),
        "#### Level 14: Improved Blessed Strikes",
    ),
    (
        ("Cleric", "Cleric Class Features", "Level 14: Improved Blessed Strikes"),
        "The option you chose for Blessed Strikes grows more powerful.",
    ),
    (
        ("Cleric", "Cleric Class Features", "Level 14: Improved Blessed Strikes"),
        "_Divine Strike._ The extra damage of your Divine Strike increases to 2d8.",
    ),
    (
        ("Cleric", "Cleric Class Features", "Level 14: Improved Blessed Strikes"),
        "_Potent Spellcasting._ When you cast a Cleric cantrip and deal damage to a creature with it, you can give vitality to yourself or another creature within 60 feet of yourself, granting a number of Temporary Hit Points equal to twice your Wisdom modifier.",
    ),
    (
        ("Cleric", "Cleric Class Features", "Level 19: Epic Boon"),
        "#### Level 19: Epic Boon",
    ),
    (
        ("Cleric", "Cleric Class Features", "Level 19: Epic Boon"),
        'You gain an Epic Boon feat (see "Feats") or another feat of your choice for which you qualify. Boon of Fate is recommended.',
    ),
    (
        ("Cleric", "Cleric Class Features", "Level 20: Greater Divine Intervention"),
        "#### Level 20: Greater Divine Intervention",
    ),
    (
        ("Cleric", "Cleric Class Features", "Level 20: Greater Divine Intervention"),
        "You can call on even more powerful divine intervention. When you use your Divine Intervention feature, you can choose _Wish_ when you select a spell. If you do so, you can't use Divine Intervention again until you finish 2d4 Long Rests.",
    ),
    (("Cleric", "Cleric Spell List"), "### Cleric Spell List"),
    (
        ("Cleric", "Cleric Spell List"),
        "This section presents the Cleric spell list. The spells are organized by spell level and then alphabetized, and each spell's school of magic is listed. In the Special column, _C_ means the spell requires Concentration, _R_ means it's a Ritual, and _M_ means it requires a specific Material component.",
    ),
    (
        ("Cleric", "Cleric Spell List", "Cantrips (Level 0 Cleric Spells)"),
        "#### Cantrips (Level 0 Cleric Spells)",
    ),
    (
        ("Cleric", "Cleric Spell List", "Cantrips (Level 0 Cleric Spells)"),
        "<table>\n  <thead>\n    <tr>\n      <th>Spell</th>\n      <th>School</th>\n      <th>Special</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>Guidance</td>\n      <td>Divination</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Light</td>\n      <td>Evocation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Mending</td>\n      <td>Transmutation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Resistance</td>\n      <td>Abjuration</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Sacred Flame</td>\n      <td>Evocation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Spare the Dying</td>\n      <td>Necromancy</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Thaumaturgy</td>\n      <td>Transmutation</td>\n      <td>—</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        ("Cleric", "Cleric Spell List", "Level 1 Cleric Spells"),
        "#### Level 1 Cleric Spells",
    ),
    (
        ("Cleric", "Cleric Spell List", "Level 1 Cleric Spells"),
        "<table>\n  <thead>\n    <tr>\n      <th>Spell</th>\n      <th>School</th>\n      <th>Special</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>Bane</td>\n      <td>Enchantment</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Bless</td>\n      <td>Enchantment</td>\n      <td>C, M</td>\n    </tr>\n    <tr>\n      <td>Command</td>\n      <td>Enchantment</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Create or Destroy Water</td>\n      <td>Transmutation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Cure Wounds</td>\n      <td>Abjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Detect Evil and Good</td>\n      <td>Divination</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Detect Magic</td>\n      <td>Divination</td>\n      <td>C, R</td>\n    </tr>\n    <tr>\n      <td>Detect Poison and Disease</td>\n      <td>Divination</td>\n      <td>C, R</td>\n    </tr>\n    <tr>\n      <td>Guiding Bolt</td>\n      <td>Evocation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Healing Word</td>\n      <td>Abjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Inflict Wounds</td>\n      <td>Necromancy</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Protection from Evil and Good</td>\n      <td>Abjuration</td>\n      <td>C, M</td>\n    </tr>\n    <tr>\n      <td>Purify Food and Drink</td>\n      <td>Transmutation</td>\n      <td>R</td>\n    </tr>\n    <tr>\n      <td>Sanctuary</td>\n      <td>Abjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Shield of Faith</td>\n      <td>Abjuration</td>\n      <td>C</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        ("Cleric", "Cleric Spell List", "Level 2 Cleric Spells"),
        "#### Level 2 Cleric Spells",
    ),
    (
        ("Cleric", "Cleric Spell List", "Level 2 Cleric Spells"),
        "<table>\n  <thead>\n    <tr>\n      <th>Spell</th>\n      <th>School</th>\n      <th>Special</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>Aid</td>\n      <td>Abjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Augury</td>\n      <td>Divination</td>\n      <td>R, M</td>\n    </tr>\n    <tr>\n      <td>Blindness/Deafness</td>\n      <td>Transmutation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Calm Emotions</td>\n      <td>Enchantment</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Continual Flame</td>\n      <td>Evocation</td>\n      <td>M</td>\n    </tr>\n    <tr>\n      <td>Enhance Ability</td>\n      <td>Transmutation</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Find Traps</td>\n      <td>Divination</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Gentle Repose</td>\n      <td>Necromancy</td>\n      <td>R, M</td>\n    </tr>\n    <tr>\n      <td>Hold Person</td>\n      <td>Enchantment</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Lesser Restoration</td>\n      <td>Abjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Locate Object</td>\n      <td>Divination</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Prayer of Healing</td>\n      <td>Abjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Protection from Poison</td>\n      <td>Abjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Silence</td>\n      <td>Illusion</td>\n      <td>C, R</td>\n    </tr>\n    <tr>\n      <td>Spiritual Weapon</td>\n      <td>Evocation</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Warding Bond</td>\n      <td>Abjuration</td>\n      <td>M</td>\n    </tr>\n    <tr>\n      <td>Zone of Truth</td>\n      <td>Enchantment</td>\n      <td>—</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        ("Cleric", "Cleric Spell List", "Level 3 Cleric Spells"),
        "#### Level 3 Cleric Spells",
    ),
    (
        ("Cleric", "Cleric Spell List", "Level 3 Cleric Spells"),
        "<table>\n  <thead>\n    <tr>\n      <th>Spell</th>\n      <th>School</th>\n      <th>Special</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>Animate Dead</td>\n      <td>Necromancy</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Beacon of Hope</td>\n      <td>Abjuration</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Bestow Curse</td>\n      <td>Necromancy</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Clairvoyance</td>\n      <td>Divination</td>\n      <td>C, M</td>\n    </tr>\n    <tr>\n      <td>Create Food and Water</td>\n      <td>Conjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Daylight</td>\n      <td>Evocation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Dispel Magic</td>\n      <td>Abjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Glyph of Warding</td>\n      <td>Abjuration</td>\n      <td>M</td>\n    </tr>\n    <tr>\n      <td>Magic Circle</td>\n      <td>Abjuration</td>\n      <td>M</td>\n    </tr>\n    <tr>\n      <td>Mass Healing Word</td>\n      <td>Abjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Meld into Stone</td>\n      <td>Transmutation</td>\n      <td>R</td>\n    </tr>\n    <tr>\n      <td>Protection from Energy</td>\n      <td>Abjuration</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Remove Curse</td>\n      <td>Abjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Revivify</td>\n      <td>Necromancy</td>\n      <td>M</td>\n    </tr>\n    <tr>\n      <td>Sending</td>\n      <td>Divination</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Speak with Dead</td>\n      <td>Necromancy</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Spirit Guardians</td>\n      <td>Conjuration</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Tongues</td>\n      <td>Divination</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Water Walk</td>\n      <td>Transmutation</td>\n      <td>R</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        ("Cleric", "Cleric Spell List", "Level 4 Cleric Spells"),
        "#### Level 4 Cleric Spells",
    ),
    (
        ("Cleric", "Cleric Spell List", "Level 4 Cleric Spells"),
        "<table>\n  <thead>\n    <tr>\n      <th>Spell</th>\n      <th>School</th>\n      <th>Special</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>Aura of Life</td>\n      <td>Abjuration</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Banishment</td>\n      <td>Abjuration</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Control Water</td>\n      <td>Transmutation</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Death Ward</td>\n      <td>Abjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Divination</td>\n      <td>Divination</td>\n      <td>R, M</td>\n    </tr>\n    <tr>\n      <td>Freedom of Movement</td>\n      <td>Abjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Guardian of Faith</td>\n      <td>Conjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Locate Creature</td>\n      <td>Divination</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Stone Shape</td>\n      <td>Transmutation</td>\n      <td>—</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        ("Cleric", "Cleric Spell List", "Level 5 Cleric Spells"),
        "#### Level 5 Cleric Spells",
    ),
    (
        ("Cleric", "Cleric Spell List", "Level 5 Cleric Spells"),
        "<table>\n  <thead>\n    <tr>\n      <th>Spell</th>\n      <th>School</th>\n      <th>Special</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>Commune</td>\n      <td>Divination</td>\n      <td>R</td>\n    </tr>\n    <tr>\n      <td>Contagion</td>\n      <td>Necromancy</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Dispel Evil and Good</td>\n      <td>Abjuration</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Flame Strike</td>\n      <td>Evocation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Geas</td>\n      <td>Enchantment</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Greater Restoration</td>\n      <td>Abjuration</td>\n      <td>M</td>\n    </tr>\n    <tr>\n      <td>Hallow</td>\n      <td>Abjuration</td>\n      <td>M</td>\n    </tr>\n    <tr>\n      <td>Insect Plague</td>\n      <td>Conjuration</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Legend Lore</td>\n      <td>Divination</td>\n      <td>M</td>\n    </tr>\n    <tr>\n      <td>Mass Cure Wounds</td>\n      <td>Abjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Planar Binding</td>\n      <td>Abjuration</td>\n      <td>M</td>\n    </tr>\n    <tr>\n      <td>Raise Dead</td>\n      <td>Necromancy</td>\n      <td>M</td>\n    </tr>\n    <tr>\n      <td>Scrying</td>\n      <td>Divination</td>\n      <td>C, M</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        ("Cleric", "Cleric Spell List", "Level 6 Cleric Spells"),
        "#### Level 6 Cleric Spells",
    ),
    (
        ("Cleric", "Cleric Spell List", "Level 6 Cleric Spells"),
        "<table>\n  <thead>\n    <tr>\n      <th>Spell</th>\n      <th>School</th>\n      <th>Special</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>Blade Barrier</td>\n      <td>Evocation</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Create Undead</td>\n      <td>Necromancy</td>\n      <td>M</td>\n    </tr>\n    <tr>\n      <td>Find the Path</td>\n      <td>Divination</td>\n      <td>C, M</td>\n    </tr>\n    <tr>\n      <td>Forbiddance</td>\n      <td>Abjuration</td>\n      <td>R, M</td>\n    </tr>\n    <tr>\n      <td>Harm</td>\n      <td>Necromancy</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Heal</td>\n      <td>Abjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Heroes' Feast</td>\n      <td>Conjuration</td>\n      <td>M</td>\n    </tr>\n    <tr>\n      <td>Planar Ally</td>\n      <td>Conjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Sunbeam</td>\n      <td>Evocation</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>True Seeing</td>\n      <td>Divination</td>\n      <td>M</td>\n    </tr>\n    <tr>\n      <td>Word of Recall</td>\n      <td>Conjuration</td>\n      <td>—</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        ("Cleric", "Cleric Spell List", "Level 7 Cleric Spells"),
        "#### Level 7 Cleric Spells",
    ),
    (
        ("Cleric", "Cleric Spell List", "Level 7 Cleric Spells"),
        "<table>\n  <thead>\n    <tr>\n      <th>Spell</th>\n      <th>School</th>\n      <th>Special</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>Conjure Celestial</td>\n      <td>Conjuration</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Divine Word</td>\n      <td>Evocation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Etherealness</td>\n      <td>Conjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Fire Storm</td>\n      <td>Evocation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Plane Shift</td>\n      <td>Conjuration</td>\n      <td>M</td>\n    </tr>\n    <tr>\n      <td>Regenerate</td>\n      <td>Transmutation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Resurrection</td>\n      <td>Necromancy</td>\n      <td>M</td>\n    </tr>\n    <tr>\n      <td>Symbol</td>\n      <td>Abjuration</td>\n      <td>M</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        ("Cleric", "Cleric Spell List", "Level 8 Cleric Spells"),
        "#### Level 8 Cleric Spells",
    ),
    (
        ("Cleric", "Cleric Spell List", "Level 8 Cleric Spells"),
        "<table>\n  <thead>\n    <tr>\n      <th>Spell</th>\n      <th>School</th>\n      <th>Special</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>Antimagic Field</td>\n      <td>Abjuration</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Control Weather</td>\n      <td>Transmutation</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Earthquake</td>\n      <td>Transmutation</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Holy Aura</td>\n      <td>Abjuration</td>\n      <td>C, M</td>\n    </tr>\n    <tr>\n      <td>Sunburst</td>\n      <td>Evocation</td>\n      <td>—</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        ("Cleric", "Cleric Spell List", "Level 9 Cleric Spells"),
        "#### Level 9 Cleric Spells",
    ),
    (
        ("Cleric", "Cleric Spell List", "Level 9 Cleric Spells"),
        "<table>\n  <thead>\n    <tr>\n      <th>Spell</th>\n      <th>School</th>\n      <th>Special</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>Astral Projection</td>\n      <td>Necromancy</td>\n      <td>M</td>\n    </tr>\n    <tr>\n      <td>Gate</td>\n      <td>Conjuration</td>\n      <td>C, M</td>\n    </tr>\n    <tr>\n      <td>Mass Heal</td>\n      <td>Abjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Power Word Heal</td>\n      <td>Enchantment</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>True Resurrection</td>\n      <td>Necromancy</td>\n      <td>M</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (("Cleric", "Cleric Subclass: Life Domain"), "### Cleric Subclass: Life Domain"),
    (("Cleric", "Cleric Subclass: Life Domain"), "_Soothe the Hurts of the World_"),
    (
        ("Cleric", "Cleric Subclass: Life Domain"),
        "The Life Domain focuses on the positive energy that helps sustain all life in the multiverse. Clerics who tap into this domain are masters of healing, using that life force to cure many hurts.",
    ),
    (
        ("Cleric", "Cleric Subclass: Life Domain"),
        "Existence itself relies on the positive energy associated with this domain, so a Cleric of almost any religious tradition might choose it. This domain is particularly associated with agricultural deities, gods of healing or endurance, and gods of home and community. Religious orders of healing also seek the magic of this domain.",
    ),
    (
        ("Cleric", "Cleric Subclass: Life Domain", "Level 3: Disciple of Life"),
        "#### Level 3: Disciple of Life",
    ),
    (
        ("Cleric", "Cleric Subclass: Life Domain", "Level 3: Disciple of Life"),
        "When a spell you cast with a spell slot restores Hit Points to a creature, that creature regains additional Hit Points on the turn you cast the spell. The additional Hit Points equal 2 plus the spell slot's level.",
    ),
    (
        ("Cleric", "Cleric Subclass: Life Domain", "Level 3: Life Domain Spells"),
        "#### Level 3: Life Domain Spells",
    ),
    (
        ("Cleric", "Cleric Subclass: Life Domain", "Level 3: Life Domain Spells"),
        "Your connection to this divine domain ensures you always have certain spells ready. When you reach a Cleric level specified in the Life Domain Spells table, you thereafter always have the listed spells prepared.",
    ),
    (
        ("Cleric", "Cleric Subclass: Life Domain", "Level 3: Life Domain Spells"),
        "**Life Domain Spells**\n\n<table>\n  <thead>\n    <tr>\n      <th>Cleric Level</th>\n      <th>Prepared Spells</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>3</td>\n      <td>Aid, Bless, Cure Wounds, Lesser Restoration</td>\n    </tr>\n    <tr>\n      <td>5</td>\n      <td>Mass Healing Word, Revivify</td>\n    </tr>\n    <tr>\n      <td>7</td>\n      <td>Aura of Life, Death Ward</td>\n    </tr>\n    <tr>\n      <td>9</td>\n      <td>Greater Restoration, Mass Cure Wounds</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        ("Cleric", "Cleric Subclass: Life Domain", "Level 3: Preserve Life"),
        "#### Level 3: Preserve Life",
    ),
    (
        ("Cleric", "Cleric Subclass: Life Domain", "Level 3: Preserve Life"),
        "As a Magic action, you present your Holy Symbol and expend a use of your Channel Divinity to evoke healing energy that can restore a number of Hit Points equal to five times your Cleric level. Choose Bloodied creatures within 30 feet of yourself (which can include you), and divide those Hit Points among them. This feature can restore a creature to no more than half its Hit Point maximum.",
    ),
    (
        ("Cleric", "Cleric Subclass: Life Domain", "Level 6: Blessed Healer"),
        "#### Level 6: Blessed Healer",
    ),
    (
        ("Cleric", "Cleric Subclass: Life Domain", "Level 6: Blessed Healer"),
        "The healing spells you cast on others heal you as well. Immediately after you cast a spell with a spell slot that restores Hit Points to one or more creatures other than yourself, you regain Hit Points equal to 2 plus the spell slot's level.",
    ),
    (
        ("Cleric", "Cleric Subclass: Life Domain", "Level 17: Supreme Healing"),
        "#### Level 17: Supreme Healing",
    ),
    (
        ("Cleric", "Cleric Subclass: Life Domain", "Level 17: Supreme Healing"),
        "When you would normally roll one or more dice to restore Hit Points to a creature with a spell or Channel Divinity, don't roll those dice for the healing; instead use the highest number possible for each die. For example, instead of restoring 2d6 Hit Points to a creature with a spell, you restore 12.",
    ),
    (("Druid",), "## Druid"),
    (
        ("Druid",),
        "**Core Druid Traits**\n\n<table>\n  <tbody>\n    <tr>\n      <td>Primary Ability</td>\n      <td>Wisdom</td>\n    </tr>\n    <tr>\n      <td>Hit Point Die</td>\n      <td>D8 per Druid level</td>\n    </tr>\n    <tr>\n      <td>Saving Throw Proficiencies</td>\n      <td>Intelligence and Wisdom</td>\n    </tr>\n    <tr>\n      <td>Skill Proficiencies</td>\n      <td>Choose 2: Animal Handling, Arcana, Insight, Medicine, Nature, Perception, Religion, or Survival</td>\n    </tr>\n    <tr>\n      <td>Weapon Proficiencies</td>\n      <td>Simple weapons</td>\n    </tr>\n    <tr>\n      <td>Tool Proficiencies</td>\n      <td>Herbalism Kit</td>\n    </tr>\n    <tr>\n      <td>Armor Training</td>\n      <td>Light armor and Shields</td>\n    </tr>\n    <tr>\n      <td>Starting Equipment</td>\n      <td>Choose A or B: (A) Leather Armor, Shield, Sickle, Druidic Focus (Quarterstaff), Explorer's Pack, Herbalism Kit, and 9 GP; or (B) 50 GP</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (("Druid", "Becoming a Druid …"), "### Becoming a Druid …"),
    (
        ("Druid", "Becoming a Druid …", "As a Level 1 Character"),
        "#### As a Level 1 Character",
    ),
    (
        ("Druid", "Becoming a Druid …", "As a Level 1 Character"),
        "• Gain all the traits in the Core Druid Traits table.\n• Gain the Druid's level 1 features, which are listed in the Druid Features table.",
    ),
    (
        ("Druid", "Becoming a Druid …", "As a Multiclass Character"),
        "#### As a Multiclass Character",
    ),
    (
        ("Druid", "Becoming a Druid …", "As a Multiclass Character"),
        '• Gain the following traits from the Core Druid Traits table: Hit Point Die and training with Light armor and Shields.\n• Gain the Druid\'s level 1 features, which are listed in the Druid Features table. See the multiclassing rules in "Character Creation" to determine your available spell slots.',
    ),
    (("Druid", "Druid Class Features"), "### Druid Class Features"),
    (
        ("Druid", "Druid Class Features"),
        "As a Druid, you gain the following class features when you reach the specified Druid levels. These features are listed in the Druid Features table.",
    ),
    (
        ("Druid", "Druid Class Features"),
        '**Druid Features**\n\n<table>\n  <thead>\n    <tr>\n      <th>Level</th>\n      <th>Proficiency Bonus</th>\n      <th>Class Features</th>\n      <th>Wild Shape</th>\n      <th>Cantrips</th>\n      <th>Prepared Spells</th>\n      <th colspan="9">——Spell Slots per Spell Level——</th>\n    </tr>\n    <tr>\n      <th>\n      </th>\n      <th>\n      </th>\n      <th>\n      </th>\n      <th>\n      </th>\n      <th>\n      </th>\n      <th>\n      </th>\n      <th>1</th>\n      <th>2</th>\n      <th>3</th>\n      <th>4</th>\n      <th>5</th>\n      <th>6</th>\n      <th>7</th>\n      <th>8</th>\n      <th>9</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>1</td>\n      <td>+2</td>\n      <td>Spellcasting, Druidic, Primal Order</td>\n      <td>—</td>\n      <td>2</td>\n      <td>4</td>\n      <td>2</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>2</td>\n      <td>+2</td>\n      <td>Wild Shape, Wild Companion</td>\n      <td>2</td>\n      <td>2</td>\n      <td>5</td>\n      <td>3</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>3</td>\n      <td>+2</td>\n      <td>Druid Subclass</td>\n      <td>2</td>\n      <td>2</td>\n      <td>6</td>\n      <td>4</td>\n      <td>2</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>4</td>\n      <td>+2</td>\n      <td>Ability Score Improvement</td>\n      <td>2</td>\n      <td>3</td>\n      <td>7</td>\n      <td>4</td>\n      <td>3</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>5</td>\n      <td>+3</td>\n      <td>Wild Resurgence</td>\n      <td>2</td>\n      <td>3</td>\n      <td>9</td>\n      <td>4</td>\n      <td>3</td>\n      <td>2</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>6</td>\n      <td>+3</td>\n      <td>Subclass feature</td>\n      <td>3</td>\n      <td>3</td>\n      <td>10</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>7</td>\n      <td>+3</td>\n      <td>Elemental Fury</td>\n      <td>3</td>\n      <td>3</td>\n      <td>11</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>1</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>8</td>\n      <td>+3</td>\n      <td>Ability Score Improvement</td>\n      <td>3</td>\n      <td>3</td>\n      <td>12</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>2</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>9</td>\n      <td>+4</td>\n      <td>—</td>\n      <td>3</td>\n      <td>3</td>\n      <td>14</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>3</td>\n      <td>1</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>10</td>\n      <td>+4</td>\n      <td>Subclass feature</td>\n      <td>3</td>\n      <td>4</td>\n      <td>15</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>3</td>\n      <td>2</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>11</td>\n      <td>+4</td>\n      <td>—</td>\n      <td>3</td>\n      <td>4</td>\n      <td>16</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>3</td>\n      <td>2</td>\n      <td>1</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>12</td>\n      <td>+4</td>\n      <td>Ability Score Improvement</td>\n      <td>3</td>\n      <td>4</td>\n      <td>16</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>3</td>\n      <td>2</td>\n      <td>1</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>13</td>\n      <td>+5</td>\n      <td>—</td>\n      <td>3</td>\n      <td>4</td>\n      <td>17</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>3</td>\n      <td>2</td>\n      <td>1</td>\n      <td>1</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>14</td>\n      <td>+5</td>\n      <td>Subclass feature</td>\n      <td>3</td>\n      <td>4</td>\n      <td>17</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>3</td>\n      <td>2</td>\n      <td>1</td>\n      <td>1</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>15</td>\n      <td>+5</td>\n      <td>Improved Elemental Fury</td>\n      <td>3</td>\n      <td>4</td>\n      <td>18</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>3</td>\n      <td>2</td>\n      <td>1</td>\n      <td>1</td>\n      <td>1</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>16</td>\n      <td>+5</td>\n      <td>Ability Score Improvement</td>\n      <td>3</td>\n      <td>4</td>\n      <td>18</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>3</td>\n      <td>2</td>\n      <td>1</td>\n      <td>1</td>\n      <td>1</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>17</td>\n      <td>+6</td>\n      <td>—</td>\n      <td>4</td>\n      <td>4</td>\n      <td>19</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>3</td>\n      <td>2</td>\n      <td>1</td>\n      <td>1</td>\n      <td>1</td>\n      <td>1</td>\n    </tr>\n    <tr>\n      <td>18</td>\n      <td>+6</td>\n      <td>Beast Spells</td>\n      <td>4</td>\n      <td>4</td>\n      <td>20</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>3</td>\n      <td>3</td>\n      <td>1</td>\n      <td>1</td>\n      <td>1</td>\n      <td>1</td>\n    </tr>\n    <tr>\n      <td>19</td>\n      <td>+6</td>\n      <td>Epic Boon</td>\n      <td>4</td>\n      <td>4</td>\n      <td>21</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>3</td>\n      <td>3</td>\n      <td>2</td>\n      <td>1</td>\n      <td>1</td>\n      <td>1</td>\n    </tr>\n    <tr>\n      <td>20</td>\n      <td>+6</td>\n      <td>Archdruid</td>\n      <td>4</td>\n      <td>4</td>\n      <td>22</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>3</td>\n      <td>3</td>\n      <td>2</td>\n      <td>2</td>\n      <td>1</td>\n      <td>1</td>\n    </tr>\n  </tbody>\n</table>',
    ),
    (
        ("Druid", "Druid Class Features", "Level 1: Spellcasting"),
        "#### Level 1: Spellcasting",
    ),
    (
        ("Druid", "Druid Class Features", "Level 1: Spellcasting"),
        'You have learned to cast spells through studying the mystical forces of nature. See "Spells" for the rules on spellcasting. The information below details how you use those rules with Druid spells, which appear on the Druid spell list later in the class\'s description.',
    ),
    (
        ("Druid", "Druid Class Features", "Level 1: Spellcasting"),
        "_Cantrips._ You know two cantrips of your choice from the Druid spell list. _Druidcraft_ and _Produce Flame_ are recommended.",
    ),
    (
        ("Druid", "Druid Class Features", "Level 1: Spellcasting"),
        "Whenever you gain a Druid level, you can replace one of your cantrips with another cantrip of your choice from the Druid spell list.",
    ),
    (
        ("Druid", "Druid Class Features", "Level 1: Spellcasting"),
        "When you reach Druid levels 4 and 10, you learn another cantrip of your choice from the Druid spell list, as shown in the Cantrips column of the Druid Features table.",
    ),
    (
        ("Druid", "Druid Class Features", "Level 1: Spellcasting"),
        "_Spell Slots._ The Druid Features table shows how many spell slots you have to cast your level 1+ spells. You regain all expended slots when you finish a Long Rest.",
    ),
    (
        ("Druid", "Druid Class Features", "Level 1: Spellcasting"),
        "_Prepared Spells of Level 1+._ You prepare the list of level 1+ spells that are available for you to cast with this feature. To start, choose four level 1 spells from the Druid spell list. _Animal Friendship, Cure Wounds, Faerie Fire,_ and _Thunderwave_ are recommended.",
    ),
    (
        ("Druid", "Druid Class Features", "Level 1: Spellcasting"),
        "The number of spells on your list increases as you gain Druid levels, as shown in the Prepared Spells column of the Druid Features table. Whenever that number increases, choose additional spells from the Druid spell list until the number of spells on your list matches the number on the table. The chosen spells must be of a level for which you have spell slots. For example, if you're a level 3 Druid, your list of prepared spells can include six spells of levels 1 and 2 in any combination.",
    ),
    (
        ("Druid", "Druid Class Features", "Level 1: Spellcasting"),
        "If another Druid feature gives you spells that you always have prepared, those spells don't count against the number of spells you can prepare with this feature, but those spells otherwise count as Druid spells for you.",
    ),
    (
        ("Druid", "Druid Class Features", "Level 1: Spellcasting"),
        "_Changing Your Prepared Spells._ Whenever you finish a Long Rest, you can change your list of prepared spells, replacing any of the spells with other Druid spells for which you have spell slots.",
    ),
    (
        ("Druid", "Druid Class Features", "Level 1: Spellcasting"),
        "_Spellcasting Ability._ Wisdom is your spellcasting ability for your Druid spells.",
    ),
    (
        ("Druid", "Druid Class Features", "Level 1: Spellcasting"),
        "_Spellcasting Focus._ You can use a Druidic Focus as a Spellcasting Focus for your Druid spells.",
    ),
    (("Druid", "Druid Class Features", "Level 1: Druidic"), "#### Level 1: Druidic"),
    (
        ("Druid", "Druid Class Features", "Level 1: Druidic"),
        "You know Druidic, the secret language of Druids. While learning this ancient tongue, you also unlocked the magic of communicating with animals; you always have the _Speak with Animals_ spell prepared.",
    ),
    (
        ("Druid", "Druid Class Features", "Level 1: Druidic"),
        "You can use Druidic to leave hidden messages. You and others who know Druidic automatically spot such a message. Others spot the message's presence with a successful DC 15 Intelligence (Investigation) check but can't decipher it without magic.",
    ),
    (
        ("Druid", "Druid Class Features", "Level 1: Primal Order"),
        "#### Level 1: Primal Order",
    ),
    (
        ("Druid", "Druid Class Features", "Level 1: Primal Order"),
        "You have dedicated yourself to one of the following sacred roles of your choice.",
    ),
    (
        ("Druid", "Druid Class Features", "Level 1: Primal Order"),
        "_Magician._ You know one extra cantrip from the Druid spell list. In addition, your mystical connection to nature gives you a bonus to your Intelligence (Arcana or Nature) checks. The bonus equals your Wisdom modifier (minimum bonus of +1).",
    ),
    (
        ("Druid", "Druid Class Features", "Level 1: Primal Order"),
        "_Warden._ Trained for battle, you gain proficiency with Martial weapons and training with Medium armor.",
    ),
    (
        ("Druid", "Druid Class Features", "Level 2: Wild Shape"),
        "#### Level 2: Wild Shape",
    ),
    (
        ("Druid", "Druid Class Features", "Level 2: Wild Shape"),
        'The power of nature allows you to assume the form of an animal. As a Bonus Action, you shape-shift into a Beast form that you have learned for this feature (see "Known Forms" below). You stay in that form for a number of hours equal to half your Druid level or until you use Wild Shape again, have the Incapacitated condition, or die. You can also leave the form early as a Bonus Action.',
    ),
    (
        ("Druid", "Druid Class Features", "Level 2: Wild Shape"),
        "_Number of Uses._ You can use Wild Shape twice. You regain one expended use when you finish a Short Rest, and you regain all expended uses when you finish a Long Rest.",
    ),
    (
        ("Druid", "Druid Class Features", "Level 2: Wild Shape"),
        "You gain additional uses when you reach certain Druid levels, as shown in the Wild Shape column of the Druid Features table.",
    ),
    (
        ("Druid", "Druid Class Features", "Level 2: Wild Shape"),
        '_Known Forms._ You know four Beast forms for this feature, chosen from among Beast stat blocks that have a maximum Challenge Rating of 1/4 and that lack a Fly Speed (see "Animals" in "Monsters" for stat block options). The **Rat**, **Riding Horse**, **Spider**, and **Wolf** are recommended. Whenever you finish a Long Rest, you can replace one of your known forms with another eligible form.',
    ),
    (
        ("Druid", "Druid Class Features", "Level 2: Wild Shape"),
        "When you reach certain Druid levels, your number of known forms and the maximum Challenge Rating for those forms increases, as shown in the Beast Shapes table. In addition, starting at level 8, you can adopt a form that has a Fly Speed.",
    ),
    (
        ("Druid", "Druid Class Features", "Level 2: Wild Shape"),
        "When choosing known forms, you may look in other sources for eligible Beasts if the Game Master permits you to do so.",
    ),
    (
        ("Druid", "Druid Class Features", "Level 2: Wild Shape"),
        "**Beast Shapes**\n\n<table>\n  <thead>\n    <tr>\n      <th>Druid Level</th>\n      <th>Known Forms</th>\n      <th>Max CR</th>\n      <th>Fly Speed</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>2</td>\n      <td>4</td>\n      <td>1/4</td>\n      <td>No</td>\n    </tr>\n    <tr>\n      <td>4</td>\n      <td>6</td>\n      <td>1/2</td>\n      <td>No</td>\n    </tr>\n    <tr>\n      <td>8</td>\n      <td>8</td>\n      <td>1</td>\n      <td>Yes</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        ("Druid", "Druid Class Features", "Level 2: Wild Shape"),
        "**Rules While Shape-Shifted.** While in a form, you retain your personality, memories, and ability to speak, and the following rules apply:",
    ),
    (
        ("Druid", "Druid Class Features", "Level 2: Wild Shape"),
        "**Temporary Hit Points.** When you assume a Wild Shape form, you gain a number of Temporary Hit Points equal to your Druid level.",
    ),
    (
        ("Druid", "Druid Class Features", "Level 2: Wild Shape"),
        "**Game Statistics.** Your game statistics are replaced by the Beast's stat block, but you retain your creature type; Hit Points; Hit Point Dice; Intelligence, Wisdom, and Charisma scores; class features; languages; and feats. You also retain your skill and saving throw proficiencies and use your Proficiency Bonus for them, in addition to gaining the proficiencies of the creature. If a skill or saving throw modifier in the Beast's stat block is higher than yours, use the one in the stat block.",
    ),
    (
        ("Druid", "Druid Class Features", "Level 2: Wild Shape"),
        "**No Spellcasting.** You can't cast spells, but shapeshifting doesn't break your Concentration or otherwise interfere with a spell you've already cast.",
    ),
    (
        ("Druid", "Druid Class Features", "Level 2: Wild Shape"),
        "**Objects.** Your ability to handle objects is determined by the form's limbs rather than your own. In addition, you choose whether your equipment falls in your space, merges into your new form, or is worn by it. Worn equipment functions as normal, but the GM decides whether it's practical for the new form to wear a piece of equipment based on the creature's size and shape. Your equipment doesn't change size or shape to match the new form, and any equipment that the new form can't wear must either fall to the ground or merge with the form. Equipment that merges with the form has no effect while you're in that form.",
    ),
    (
        ("Druid", "Druid Class Features", "Level 2: Wild Companion"),
        "#### Level 2: Wild Companion",
    ),
    (
        ("Druid", "Druid Class Features", "Level 2: Wild Companion"),
        "You can summon a nature spirit that assumes an animal form to aid you. As a Magic action, you can expend a spell slot or a use of Wild Shape to cast the _Find Familiar_ spell without Material components.",
    ),
    (
        ("Druid", "Druid Class Features", "Level 2: Wild Companion"),
        "When you cast the spell in this way, the familiar is Fey and disappears when you finish a Long Rest.",
    ),
    (
        ("Druid", "Druid Class Features", "Level 3: Druid Subclass"),
        "#### Level 3: Druid Subclass",
    ),
    (
        ("Druid", "Druid Class Features", "Level 3: Druid Subclass"),
        "You gain a Druid subclass of your choice. The Circle of the Land subclass is detailed after this class's description. A subclass is a specialization that grants you features at certain Druid levels. For the rest of your career, you gain each of your subclass's features that are of your Druid level or lower.",
    ),
    (
        ("Druid", "Druid Class Features", "Level 4: Ability Score Improvement"),
        "#### Level 4: Ability Score Improvement",
    ),
    (
        ("Druid", "Druid Class Features", "Level 4: Ability Score Improvement"),
        'You gain the Ability Score Improvement feat (see "Feats") or another feat of your choice for which you qualify. You gain this feature again at Druid levels 8, 12, and 16.',
    ),
    (
        ("Druid", "Druid Class Features", "Level 5: Wild Resurgence"),
        "#### Level 5: Wild Resurgence",
    ),
    (
        ("Druid", "Druid Class Features", "Level 5: Wild Resurgence"),
        "Once on each of your turns, if you have no uses of Wild Shape left, you can give yourself one use by expending a spell slot (no action required).",
    ),
    (
        ("Druid", "Druid Class Features", "Level 5: Wild Resurgence"),
        "In addition, you can expend one use of Wild Shape (no action required) to give yourself a level 1 spell slot, but you can't do so again until you finish a Long Rest.",
    ),
    (
        ("Druid", "Druid Class Features", "Level 7: Elemental Fury"),
        "#### Level 7: Elemental Fury",
    ),
    (
        ("Druid", "Druid Class Features", "Level 7: Elemental Fury"),
        "The might of the elements flows through you. You gain one of the following options of your choice.",
    ),
    (
        ("Druid", "Druid Class Features", "Level 7: Elemental Fury"),
        "_Potent Spellcasting._ Add your Wisdom modifier to the damage you deal with any Druid cantrip.",
    ),
    (
        ("Druid", "Druid Class Features", "Level 7: Elemental Fury"),
        "_Primal Strike._ Once on each of your turns when you hit a creature with an attack roll using a weapon or a Beast form's attack in Wild Shape, you can cause the target to take an extra 1d8 Cold, Fire, Lightning, or Thunder damage (choose when you hit).",
    ),
    (
        ("Druid", "Druid Class Features", "Level 15: Improved Elemental Fury"),
        "#### Level 15: Improved Elemental Fury",
    ),
    (
        ("Druid", "Druid Class Features", "Level 15: Improved Elemental Fury"),
        "The option you chose for Elemental Fury grows more powerful, as detailed below.",
    ),
    (
        ("Druid", "Druid Class Features", "Level 15: Improved Elemental Fury"),
        "_Potent Spellcasting._ When you cast a Druid cantrip with a range of 10 feet or greater, the spell's range increases by 300 feet.",
    ),
    (
        ("Druid", "Druid Class Features", "Level 15: Improved Elemental Fury"),
        "_Primal Strike._ The extra damage of your Primal Strike increases to 2d8.",
    ),
    (
        ("Druid", "Druid Class Features", "Level 18: Beast Spells"),
        "#### Level 18: Beast Spells",
    ),
    (
        ("Druid", "Druid Class Features", "Level 18: Beast Spells"),
        "While using Wild Shape, you can cast spells in Beast form, except for any spell that has a Material component with a cost specified or that consumes its Material component.",
    ),
    (
        ("Druid", "Druid Class Features", "Level 19: Epic Boon"),
        "#### Level 19: Epic Boon",
    ),
    (
        ("Druid", "Druid Class Features", "Level 19: Epic Boon"),
        'You gain an Epic Boon feat (see "Feats") or another feat of your choice for which you qualify. Boon of Dimensional Travel is recommended.',
    ),
    (
        ("Druid", "Druid Class Features", "Level 20: Archdruid"),
        "#### Level 20: Archdruid",
    ),
    (
        ("Druid", "Druid Class Features", "Level 20: Archdruid"),
        "The vitality of nature constantly blooms within you, granting you the following benefits.",
    ),
    (
        ("Druid", "Druid Class Features", "Level 20: Archdruid"),
        "_Evergreen Wild Shape._ Whenever you roll Initiative and have no uses of Wild Shape left, you regain one expended use of it.",
    ),
    (
        ("Druid", "Druid Class Features", "Level 20: Archdruid"),
        "_Nature Magician._ You can convert uses of Wild Shape into a spell slot (no action required). Choose a number of your unexpended uses of Wild Shape and convert them into a single spell slot, with each use contributing 2 spell levels. For example, if you convert two uses of Wild Shape, you produce a level 4 spell slot. Once you use this benefit, you can't do so again until you finish a Long Rest.",
    ),
    (
        ("Druid", "Druid Class Features", "Level 20: Archdruid"),
        "_Longevity._ The primal magic that you wield causes you to age more slowly. For every ten years that pass, your body ages only one year.",
    ),
    (("Druid", "Druid Spell List"), "### Druid Spell List"),
    (
        ("Druid", "Druid Spell List"),
        "This section presents the Druid spell list. The spells are organized by spell level and then alphabetized, and each spell's school of magic is listed. In the Special column, _C_ means the spell requires Concentration, _R_ means it's a Ritual, and _M_ means it requires a specific Material component.",
    ),
    (
        ("Druid", "Druid Spell List", "Cantrips (Level 0 Druid Spells)"),
        "#### Cantrips (Level 0 Druid Spells)",
    ),
    (
        ("Druid", "Druid Spell List", "Cantrips (Level 0 Druid Spells)"),
        "<table>\n  <thead>\n    <tr>\n      <th>Spell</th>\n      <th>School</th>\n      <th>Special</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>Druidcraft</td>\n      <td>Transmutation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Elementalism</td>\n      <td>Transmutation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Guidance</td>\n      <td>Divination</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Mending</td>\n      <td>Transmutation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Message</td>\n      <td>Transmutation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Poison Spray</td>\n      <td>Necromancy</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Produce Flame</td>\n      <td>Conjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Resistance</td>\n      <td>Abjuration</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Shillelagh</td>\n      <td>Transmutation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Spare the Dying</td>\n      <td>Necromancy</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Starry Wisp</td>\n      <td>Evocation</td>\n      <td>—</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        ("Druid", "Druid Spell List", "Level 1 Druid Spells"),
        "#### Level 1 Druid Spells",
    ),
    (
        ("Druid", "Druid Spell List", "Level 1 Druid Spells"),
        "<table>\n  <thead>\n    <tr>\n      <th>Spell</th>\n      <th>School</th>\n      <th>Special</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>Animal Friendship</td>\n      <td>Enchantment</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Charm Person</td>\n      <td>Enchantment</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Create or Destroy Water</td>\n      <td>Transmutation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Cure Wounds</td>\n      <td>Abjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Detect Magic</td>\n      <td>Divination</td>\n      <td>C, R</td>\n    </tr>\n    <tr>\n      <td>Detect Poison and Disease</td>\n      <td>Divination</td>\n      <td>C, R</td>\n    </tr>\n    <tr>\n      <td>Entangle</td>\n      <td>Conjuration</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Faerie Fire</td>\n      <td>Evocation</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Fog Cloud</td>\n      <td>Conjuration</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Goodberry</td>\n      <td>Conjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Healing Word</td>\n      <td>Abjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Ice Knife</td>\n      <td>Conjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Jump</td>\n      <td>Transmutation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Longstrider</td>\n      <td>Transmutation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Protection from Evil and Good</td>\n      <td>Abjuration</td>\n      <td>C, M</td>\n    </tr>\n    <tr>\n      <td>Purify Food and Drink</td>\n      <td>Transmutation</td>\n      <td>R</td>\n    </tr>\n    <tr>\n      <td>Speak with Animals</td>\n      <td>Divination</td>\n      <td>R</td>\n    </tr>\n    <tr>\n      <td>Thunderwave</td>\n      <td>Evocation</td>\n      <td>—</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        ("Druid", "Druid Spell List", "Level 2 Druid Spells"),
        "#### Level 2 Druid Spells",
    ),
    (
        ("Druid", "Druid Spell List", "Level 2 Druid Spells"),
        "<table>\n  <thead>\n    <tr>\n      <th>Spell</th>\n      <th>School</th>\n      <th>Special</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>Aid</td>\n      <td>Abjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Animal Messenger</td>\n      <td>Enchantment</td>\n      <td>R</td>\n    </tr>\n    <tr>\n      <td>Augury</td>\n      <td>Divination</td>\n      <td>R, M</td>\n    </tr>\n    <tr>\n      <td>Barkskin</td>\n      <td>Transmutation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Continual Flame</td>\n      <td>Evocation</td>\n      <td>M</td>\n    </tr>\n    <tr>\n      <td>Darkvision</td>\n      <td>Transmutation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Enhance Ability</td>\n      <td>Transmutation</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Enlarge/Reduce</td>\n      <td>Transmutation</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Find Traps</td>\n      <td>Divination</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Flame Blade</td>\n      <td>Evocation</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Flaming Sphere</td>\n      <td>Conjuration</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Gust of Wind</td>\n      <td>Evocation</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Heat Metal</td>\n      <td>Transmutation</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Hold Person</td>\n      <td>Enchantment</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Lesser Restoration</td>\n      <td>Abjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Locate Animals or Plants</td>\n      <td>Divination</td>\n      <td>R</td>\n    </tr>\n    <tr>\n      <td>Locate Object</td>\n      <td>Divination</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Moonbeam</td>\n      <td>Evocation</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Pass without Trace</td>\n      <td>Abjuration</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Protection from Poison</td>\n      <td>Abjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Spike Growth</td>\n      <td>Transmutation</td>\n      <td>C</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        ("Druid", "Druid Spell List", "Level 3 Druid Spells"),
        "#### Level 3 Druid Spells",
    ),
    (
        ("Druid", "Druid Spell List", "Level 3 Druid Spells"),
        "<table>\n  <thead>\n    <tr>\n      <th>Spell</th>\n      <th>School</th>\n      <th>Special</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>Call Lightning</td>\n      <td>Conjuration</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Conjure Animals</td>\n      <td>Conjuration</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Daylight</td>\n      <td>Evocation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Dispel Magic</td>\n      <td>Abjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Meld into Stone</td>\n      <td>Transmutation</td>\n      <td>R</td>\n    </tr>\n    <tr>\n      <td>Plant Growth</td>\n      <td>Transmutation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Protection from Energy</td>\n      <td>Abjuration</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Revivify</td>\n      <td>Necromancy</td>\n      <td>M</td>\n    </tr>\n    <tr>\n      <td>Sleet Storm</td>\n      <td>Conjuration</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Speak with Plants</td>\n      <td>Transmutation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Water Breathing</td>\n      <td>Transmutation</td>\n      <td>R</td>\n    </tr>\n    <tr>\n      <td>Water Walk</td>\n      <td>Transmutation</td>\n      <td>R</td>\n    </tr>\n    <tr>\n      <td>Wind Wall</td>\n      <td>Evocation</td>\n      <td>C</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        ("Druid", "Druid Spell List", "Level 4 Druid Spells"),
        "#### Level 4 Druid Spells",
    ),
    (
        ("Druid", "Druid Spell List", "Level 4 Druid Spells"),
        "<table>\n  <thead>\n    <tr>\n      <th>Spell</th>\n      <th>School</th>\n      <th>Special</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>Blight</td>\n      <td>Necromancy</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Charm Monster</td>\n      <td>Enchantment</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Confusion</td>\n      <td>Enchantment</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Conjure Minor Elementals</td>\n      <td>Conjuration</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Conjure Woodland Beings</td>\n      <td>Conjuration</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Control Water</td>\n      <td>Transmutation</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Divination</td>\n      <td>Divination</td>\n      <td>R, M</td>\n    </tr>\n    <tr>\n      <td>Dominate Beast</td>\n      <td>Enchantment</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Fire Shield</td>\n      <td>Evocation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Freedom of Movement</td>\n      <td>Abjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Giant Insect</td>\n      <td>Conjuration</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Hallucinatory Terrain</td>\n      <td>Illusion</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Ice Storm</td>\n      <td>Evocation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Locate Creature</td>\n      <td>Divination</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Polymorph</td>\n      <td>Transmutation</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Stone Shape</td>\n      <td>Transmutation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Stoneskin</td>\n      <td>Transmutation</td>\n      <td>C, M</td>\n    </tr>\n    <tr>\n      <td>Wall of Fire</td>\n      <td>Evocation</td>\n      <td>C</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        ("Druid", "Druid Spell List", "Level 5 Druid Spells"),
        "#### Level 5 Druid Spells",
    ),
    (
        ("Druid", "Druid Spell List", "Level 5 Druid Spells"),
        "<table>\n  <thead>\n    <tr>\n      <th>Spell</th>\n      <th>School</th>\n      <th>Special</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>Antilife Shell</td>\n      <td>Abjuration</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Awaken</td>\n      <td>Transmutation</td>\n      <td>M</td>\n    </tr>\n    <tr>\n      <td>Commune with Nature</td>\n      <td>Divination</td>\n      <td>R</td>\n    </tr>\n    <tr>\n      <td>Cone of Cold</td>\n      <td>Evocation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Conjure Elemental</td>\n      <td>Conjuration</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Contagion</td>\n      <td>Necromancy</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Geas</td>\n      <td>Enchantment</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Greater Restoration</td>\n      <td>Abjuration</td>\n      <td>M</td>\n    </tr>\n    <tr>\n      <td>Insect Plague</td>\n      <td>Conjuration</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Mass Cure Wounds</td>\n      <td>Abjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Planar Binding</td>\n      <td>Abjuration</td>\n      <td>M</td>\n    </tr>\n    <tr>\n      <td>Reincarnate</td>\n      <td>Necromancy</td>\n      <td>M</td>\n    </tr>\n    <tr>\n      <td>Scrying</td>\n      <td>Divination</td>\n      <td>C, M</td>\n    </tr>\n    <tr>\n      <td>Tree Stride</td>\n      <td>Conjuration</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Wall of Stone</td>\n      <td>Evocation</td>\n      <td>C</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        ("Druid", "Druid Spell List", "Level 6 Druid Spells"),
        "#### Level 6 Druid Spells",
    ),
    (
        ("Druid", "Druid Spell List", "Level 6 Druid Spells"),
        "<table>\n  <thead>\n    <tr>\n      <th>Spell</th>\n      <th>School</th>\n      <th>Special</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>Conjure Fey</td>\n      <td>Conjuration</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Find the Path</td>\n      <td>Divination</td>\n      <td>C, M</td>\n    </tr>\n    <tr>\n      <td>Flesh to Stone</td>\n      <td>Transmutation</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Heal</td>\n      <td>Abjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Heroes' Feast</td>\n      <td>Conjuration</td>\n      <td>M</td>\n    </tr>\n    <tr>\n      <td>Move Earth</td>\n      <td>Transmutation</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Sunbeam</td>\n      <td>Evocation</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Transport via Plants</td>\n      <td>Conjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Wall of Thorns</td>\n      <td>Conjuration</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Wind Walk</td>\n      <td>Transmutation</td>\n      <td>—</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        ("Druid", "Druid Spell List", "Level 7 Druid Spells"),
        "#### Level 7 Druid Spells",
    ),
    (
        ("Druid", "Druid Spell List", "Level 7 Druid Spells"),
        "<table>\n  <thead>\n    <tr>\n      <th>Spell</th>\n      <th>School</th>\n      <th>Special</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>Fire Storm</td>\n      <td>Evocation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Mirage Arcane</td>\n      <td>Illusion</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Plane Shift</td>\n      <td>Conjuration</td>\n      <td>M</td>\n    </tr>\n    <tr>\n      <td>Regenerate</td>\n      <td>Transmutation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Reverse Gravity</td>\n      <td>Transmutation</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Symbol</td>\n      <td>Abjuration</td>\n      <td>M</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        ("Druid", "Druid Spell List", "Level 8 Druid Spells"),
        "#### Level 8 Druid Spells",
    ),
    (
        ("Druid", "Druid Spell List", "Level 8 Druid Spells"),
        "<table>\n  <thead>\n    <tr>\n      <th>Spell</th>\n      <th>School</th>\n      <th>Special</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>Animal Shapes</td>\n      <td>Transmutation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Antipathy/Sympathy</td>\n      <td>Enchantment</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Befuddlement</td>\n      <td>Enchantment</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Control Weather</td>\n      <td>Transmutation</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Earthquake</td>\n      <td>Transmutation</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Incendiary Cloud</td>\n      <td>Conjuration</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Sunburst</td>\n      <td>Evocation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Tsunami</td>\n      <td>Conjuration</td>\n      <td>C</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        ("Druid", "Druid Spell List", "Level 9 Druid Spells"),
        "#### Level 9 Druid Spells",
    ),
    (
        ("Druid", "Druid Spell List", "Level 9 Druid Spells"),
        "<table>\n  <thead>\n    <tr>\n      <th>Spell</th>\n      <th>School</th>\n      <th>Special</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>Foresight</td>\n      <td>Divination</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Shapechange</td>\n      <td>Transmutation</td>\n      <td>C, M</td>\n    </tr>\n    <tr>\n      <td>Storm of Vengeance</td>\n      <td>Conjuration</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>True Resurrection</td>\n      <td>Necromancy</td>\n      <td>M</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        ("Druid", "Druid Subclass: Circle of the Land"),
        "### Druid Subclass: Circle of the Land",
    ),
    (
        ("Druid", "Druid Subclass: Circle of the Land"),
        "_Celebrate Connection to the Natural World_",
    ),
    (
        ("Druid", "Druid Subclass: Circle of the Land"),
        "The Circle of the Land comprises mystics and sages who safeguard ancient knowledge and rites. These Druids meet within sacred circles of trees or standing stones to whisper primal secrets in Druidic. The circle's wisest members preside as the chief priests of their communities.",
    ),
    (
        (
            "Druid",
            "Druid Subclass: Circle of the Land",
            "Level 3: Circle of the Land Spells",
        ),
        "#### Level 3: Circle of the Land Spells",
    ),
    (
        (
            "Druid",
            "Druid Subclass: Circle of the Land",
            "Level 3: Circle of the Land Spells",
        ),
        "Whenever you finish a Long Rest, choose one type of land: arid, polar, temperate, or tropical. Consult the table below that corresponds to the chosen type; you have the spells listed for your Druid level and lower prepared.",
    ),
    (
        (
            "Druid",
            "Druid Subclass: Circle of the Land",
            "Level 3: Circle of the Land Spells",
        ),
        "**Arid Land**\n\n<table>\n  <thead>\n    <tr>\n      <th>Druid Level</th>\n      <th>Circle Spells</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>3</td>\n      <td>Blur, Burning Hands, Fire Bolt</td>\n    </tr>\n    <tr>\n      <td>5</td>\n      <td>Fireball</td>\n    </tr>\n    <tr>\n      <td>7</td>\n      <td>Blight</td>\n    </tr>\n    <tr>\n      <td>9</td>\n      <td>Wall of Stone</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Druid",
            "Druid Subclass: Circle of the Land",
            "Level 3: Circle of the Land Spells",
        ),
        "**Polar Land**\n\n<table>\n  <thead>\n    <tr>\n      <th>Druid Level</th>\n      <th>Circle Spells</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>3</td>\n      <td>Fog Cloud, Hold Person, Ray of Frost</td>\n    </tr>\n    <tr>\n      <td>5</td>\n      <td>Sleet Storm</td>\n    </tr>\n    <tr>\n      <td>7</td>\n      <td>Ice Storm</td>\n    </tr>\n    <tr>\n      <td>9</td>\n      <td>Cone of Cold</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Druid",
            "Druid Subclass: Circle of the Land",
            "Level 3: Circle of the Land Spells",
        ),
        "**Temperate Land**\n\n<table>\n  <thead>\n    <tr>\n      <th>Druid Level</th>\n      <th>Circle Spells</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>3</td>\n      <td>Misty Step, Shocking Grasp, Sleep</td>\n    </tr>\n    <tr>\n      <td>5</td>\n      <td>Lightning Bolt</td>\n    </tr>\n    <tr>\n      <td>7</td>\n      <td>Freedom of Movement</td>\n    </tr>\n    <tr>\n      <td>9</td>\n      <td>Tree Stride</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Druid",
            "Druid Subclass: Circle of the Land",
            "Level 3: Circle of the Land Spells",
        ),
        "**Tropical Land**\n\n<table>\n  <thead>\n    <tr>\n      <th>Druid Level</th>\n      <th>Circle Spells</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>3</td>\n      <td>Acid Splash, Ray of Sickness, Web</td>\n    </tr>\n    <tr>\n      <td>5</td>\n      <td>Stinking Cloud</td>\n    </tr>\n    <tr>\n      <td>7</td>\n      <td>Polymorph</td>\n    </tr>\n    <tr>\n      <td>9</td>\n      <td>Insect Plague</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        ("Druid", "Druid Subclass: Circle of the Land", "Level 3: Land's Aid"),
        "#### Level 3: Land's Aid",
    ),
    (
        ("Druid", "Druid Subclass: Circle of the Land", "Level 3: Land's Aid"),
        "As a Magic action, you can expend a use of your Wild Shape and choose a point within 60 feet of yourself. Vitality-giving flowers and life-draining thorns appear for a moment in a 10-foot-radius Sphere centered on that point. Each creature of your choice in the Sphere must make a Constitution saving throw against your spell save DC, taking 2d6 Necrotic damage on a failed save or half as much damage on a successful one. One creature of your choice in that area regains 2d6 Hit Points.",
    ),
    (
        ("Druid", "Druid Subclass: Circle of the Land", "Level 3: Land's Aid"),
        "The damage and healing increase by 1d6 when you reach Druid levels 10 (3d6) and 14 (4d6).",
    ),
    (
        ("Druid", "Druid Subclass: Circle of the Land", "Level 6: Natural Recovery"),
        "#### Level 6: Natural Recovery",
    ),
    (
        ("Druid", "Druid Subclass: Circle of the Land", "Level 6: Natural Recovery"),
        "You can cast one of the level 1+ spells that you have prepared from your Circle Spells feature without expending a spell slot, and you must finish a Long Rest before you do so again.",
    ),
    (
        ("Druid", "Druid Subclass: Circle of the Land", "Level 6: Natural Recovery"),
        "In addition, when you finish a Short Rest, you can choose expended spell slots to recover. The spell slots can have a combined level that is equal to or less than half your Druid level (round up), and none of them can be level 6+. For example, if you're a level 6 Druid, you can recover up to three levels' worth of spell slots. You can recover a level 3 spell slot, a level 2 and a level 1 spell slot, or three level 1 spell slots. Once you recover spell slots with this feature, you can't do so again until you finish a Long Rest.",
    ),
    (
        ("Druid", "Druid Subclass: Circle of the Land", "Level 10: Nature's Ward"),
        "#### Level 10: Nature's Ward",
    ),
    (
        ("Druid", "Druid Subclass: Circle of the Land", "Level 10: Nature's Ward"),
        "You are immune to the Poisoned condition, and you have Resistance to a damage type associated with your current land choice in the Circle Spells feature, as shown in the Nature's Ward table.",
    ),
    (
        ("Druid", "Druid Subclass: Circle of the Land", "Level 10: Nature's Ward"),
        "**Nature's Ward**\n\n<table>\n  <thead>\n    <tr>\n      <th>Land Type</th>\n      <th>Resistance</th>\n      <th>Land Type</th>\n      <th>Resistance</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>Arid</td>\n      <td>Fire</td>\n      <td>Temperate</td>\n      <td>Lightning</td>\n    </tr>\n    <tr>\n      <td>Polar</td>\n      <td>Cold</td>\n      <td>Tropical</td>\n      <td>Poison</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        ("Druid", "Druid Subclass: Circle of the Land", "Level 14: Nature's Sanctuary"),
        "#### Level 14: Nature's Sanctuary",
    ),
    (
        ("Druid", "Druid Subclass: Circle of the Land", "Level 14: Nature's Sanctuary"),
        "As a Magic action, you can expend a use of your Wild Shape and cause spectral trees and vines to appear in a 15-foot Cube on the ground within 120 feet of yourself. They last there for 1 minute or until you have the Incapacitated condition or die. You and your allies have Half Cover while in that area, and your allies gain the current Resistance of your Nature's Ward while there.",
    ),
    (
        ("Druid", "Druid Subclass: Circle of the Land", "Level 14: Nature's Sanctuary"),
        "As a Bonus Action, you can move the Cube up to 60 feet to ground within 120 feet of yourself.",
    ),
    (("Fighter",), "## Fighter"),
    (
        ("Fighter",),
        "**Core Fighter Traits**\n\n<table>\n  <tbody>\n    <tr>\n      <td>Primary Ability</td>\n      <td>Strength or Dexterity</td>\n    </tr>\n    <tr>\n      <td>Hit Point Die</td>\n      <td>D10 per Fighter level</td>\n    </tr>\n    <tr>\n      <td>Saving Throw Proficiencies</td>\n      <td>Strength and Constitution</td>\n    </tr>\n    <tr>\n      <td>Skill Proficiencies</td>\n      <td>Choose 2: Acrobatics, Animal Handling, Athletics, History, Insight, Intimidation, Persuasion, Perception, or Survival</td>\n    </tr>\n    <tr>\n      <td>Weapon Proficiencies</td>\n      <td>Simple and Martial weapons</td>\n    </tr>\n    <tr>\n      <td>Armor Training</td>\n      <td>Light, Medium, and Heavy armor and Shields</td>\n    </tr>\n    <tr>\n      <td>Starting Equipment</td>\n      <td>Choose A, B, or C: (A) Chain Mail, Greatsword, Flail, 8 Javelins, Dungeoneer's Pack, and 4 GP; (B) Studded Leather Armor, Scimitar, Shortsword, Longbow, 20 Arrows, Quiver, Dungeoneer's Pack, and 11 GP; or (C) 155 GP</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (("Fighter", "Becoming a Fighter …"), "### Becoming a Fighter …"),
    (
        ("Fighter", "Becoming a Fighter …", "As a Level 1 Character"),
        "#### As a Level 1 Character",
    ),
    (
        ("Fighter", "Becoming a Fighter …", "As a Level 1 Character"),
        "- Gain all the traits in the Core Fighter Traits table.\n- Gain the Fighter's level 1 features, which are listed in the Fighter Features table.",
    ),
    (
        ("Fighter", "Becoming a Fighter …", "As a Multiclass Character"),
        "#### As a Multiclass Character",
    ),
    (
        ("Fighter", "Becoming a Fighter …", "As a Multiclass Character"),
        "- Gain the following traits from the Core Fighter Traits table: Hit Point Die, proficiency with Martial weapons, and training with Light and Medium armor and Shields.\n- Gain the Fighter's level 1 features, which are listed in the Fighter Features table.",
    ),
    (("Fighter", "Fighter Class Features"), "### Fighter Class Features"),
    (
        ("Fighter", "Fighter Class Features"),
        "As a Fighter, you gain the following class features when you reach the specified Fighter levels. These features are listed on the Fighter Features table.",
    ),
    (
        ("Fighter", "Fighter Class Features"),
        "**Fighter Features**\n\n<table>\n  <thead>\n    <tr>\n      <th>Level</th>\n      <th>Proficiency Bonus</th>\n      <th>Class Features</th>\n      <th>Second Wind</th>\n      <th>Weapon Mastery</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>1</td>\n      <td>+2</td>\n      <td>Fighting Style, Second Wind, Weapon Mastery</td>\n      <td>2</td>\n      <td>3</td>\n    </tr>\n    <tr>\n      <td>2</td>\n      <td>+2</td>\n      <td>Action Surge (one use), Tactical Mind</td>\n      <td>2</td>\n      <td>3</td>\n    </tr>\n    <tr>\n      <td>3</td>\n      <td>+2</td>\n      <td>Fighter Subclass</td>\n      <td>2</td>\n      <td>3</td>\n    </tr>\n    <tr>\n      <td>4</td>\n      <td>+2</td>\n      <td>Ability Score Improvement</td>\n      <td>3</td>\n      <td>4</td>\n    </tr>\n    <tr>\n      <td>5</td>\n      <td>+3</td>\n      <td>Extra Attack, Tactical Shift</td>\n      <td>3</td>\n      <td>4</td>\n    </tr>\n    <tr>\n      <td>6</td>\n      <td>+3</td>\n      <td>Ability Score Improvement</td>\n      <td>3</td>\n      <td>4</td>\n    </tr>\n    <tr>\n      <td>7</td>\n      <td>+3</td>\n      <td>Subclass feature</td>\n      <td>3</td>\n      <td>4</td>\n    </tr>\n    <tr>\n      <td>8</td>\n      <td>+3</td>\n      <td>Ability Score Improvement</td>\n      <td>3</td>\n      <td>4</td>\n    </tr>\n    <tr>\n      <td>9</td>\n      <td>+4</td>\n      <td>Indomitable (one use), Tactical Master</td>\n      <td>3</td>\n      <td>4</td>\n    </tr>\n    <tr>\n      <td>10</td>\n      <td>+4</td>\n      <td>Subclass feature</td>\n      <td>4</td>\n      <td>5</td>\n    </tr>\n    <tr>\n      <td>11</td>\n      <td>+4</td>\n      <td>Two Extra Attacks</td>\n      <td>4</td>\n      <td>5</td>\n    </tr>\n    <tr>\n      <td>12</td>\n      <td>+4</td>\n      <td>Ability Score Improvement</td>\n      <td>4</td>\n      <td>5</td>\n    </tr>\n    <tr>\n      <td>13</td>\n      <td>+5</td>\n      <td>Indomitable (two uses), Studied Attacks</td>\n      <td>4</td>\n      <td>5</td>\n    </tr>\n    <tr>\n      <td>14</td>\n      <td>+5</td>\n      <td>Ability Score Improvement</td>\n      <td>4</td>\n      <td>5</td>\n    </tr>\n    <tr>\n      <td>15</td>\n      <td>+5</td>\n      <td>Subclass feature</td>\n      <td>4</td>\n      <td>5</td>\n    </tr>\n    <tr>\n      <td>16</td>\n      <td>+5</td>\n      <td>Ability Score Improvement</td>\n      <td>4</td>\n      <td>6</td>\n    </tr>\n    <tr>\n      <td>17</td>\n      <td>+6</td>\n      <td>Action Surge (two uses), Indomitable (three uses)</td>\n      <td>4</td>\n      <td>6</td>\n    </tr>\n    <tr>\n      <td>18</td>\n      <td>+6</td>\n      <td>Subclass feature</td>\n      <td>4</td>\n      <td>6</td>\n    </tr>\n    <tr>\n      <td>19</td>\n      <td>+6</td>\n      <td>Epic Boon</td>\n      <td>4</td>\n      <td>6</td>\n    </tr>\n    <tr>\n      <td>20</td>\n      <td>+6</td>\n      <td>Three Extra Attacks</td>\n      <td>4</td>\n      <td>6</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        ("Fighter", "Fighter Class Features", "Level 1: Fighting Style"),
        "#### Level 1: Fighting Style",
    ),
    (
        ("Fighter", "Fighter Class Features", "Level 1: Fighting Style"),
        'You have honed your martial prowess and gain a Fighting Style feat of your choice (see "Feats"). Defense is recommended.',
    ),
    (
        ("Fighter", "Fighter Class Features", "Level 1: Fighting Style"),
        "Whenever you gain a Fighter level, you can replace the feat you chose with a different Fighting Style feat.",
    ),
    (
        ("Fighter", "Fighter Class Features", "Level 1: Second Wind"),
        "#### Level 1: Second Wind",
    ),
    (
        ("Fighter", "Fighter Class Features", "Level 1: Second Wind"),
        "You have a limited well of physical and mental stamina that you can draw on. As a Bonus Action, you can use it to regain Hit Points equal to 1d10 plus your Fighter level.",
    ),
    (
        ("Fighter", "Fighter Class Features", "Level 1: Second Wind"),
        "You can use this feature twice. You regain one expended use when you finish a Short Rest, and you regain all expended uses when you finish a Long Rest.",
    ),
    (
        ("Fighter", "Fighter Class Features", "Level 1: Second Wind"),
        "When you reach certain Fighter levels, you gain more uses of this feature, as shown in the Second Wind column of the Fighter Features table.",
    ),
    (
        ("Fighter", "Fighter Class Features", "Level 1: Weapon Mastery"),
        "#### Level 1: Weapon Mastery",
    ),
    (
        ("Fighter", "Fighter Class Features", "Level 1: Weapon Mastery"),
        "Your training with weapons allows you to use the mastery properties of three kinds of Simple or Martial weapons of your choice. Whenever you finish a Long Rest, you can practice weapon drills and change one of those weapon choices.",
    ),
    (
        ("Fighter", "Fighter Class Features", "Level 1: Weapon Mastery"),
        "When you reach certain Fighter levels, you gain the ability to use the mastery properties of more kinds of weapons, as shown in the Weapon Mastery column of the Fighter Features table.",
    ),
    (
        ("Fighter", "Fighter Class Features", "Level 2: Action Surge"),
        "#### Level 2: Action Surge",
    ),
    (
        ("Fighter", "Fighter Class Features", "Level 2: Action Surge"),
        "You can push yourself beyond your normal limits for a moment. On your turn, you can take one additional action, except the Magic action.",
    ),
    (
        ("Fighter", "Fighter Class Features", "Level 2: Action Surge"),
        "Once you use this feature, you can't do so again until you finish a Short or Long Rest. Starting at level 17, you can use it twice before a rest but only once on a turn.",
    ),
    (
        ("Fighter", "Fighter Class Features", "Level 2: Tactical Mind"),
        "#### Level 2: Tactical Mind",
    ),
    (
        ("Fighter", "Fighter Class Features", "Level 2: Tactical Mind"),
        "You have a mind for tactics on and off the battlefield. When you fail an ability check, you can expend a use of your Second Wind to push yourself toward success. Rather than regaining Hit Points, you roll 1d10 and add the number rolled to the ability check, potentially turning it into a success. If the check still fails, this use of Second Wind isn't expended.",
    ),
    (
        ("Fighter", "Fighter Class Features", "Level 3: Fighter Subclass"),
        "#### Level 3: Fighter Subclass",
    ),
    (
        ("Fighter", "Fighter Class Features", "Level 3: Fighter Subclass"),
        "You gain a Fighter subclass of your choice. The Champion subclass is detailed after this class's description. A subclass is a specialization that grants you features at certain Fighter levels. For the rest of your career, you gain each of your subclass's features that are of your Fighter level or lower.",
    ),
    (
        ("Fighter", "Fighter Class Features", "Level 4: Ability Score Improvement"),
        "#### Level 4: Ability Score Improvement",
    ),
    (
        ("Fighter", "Fighter Class Features", "Level 4: Ability Score Improvement"),
        'You gain the Ability Score Improvement feat (see "Feats") or another feat of your choice for which you qualify. You gain this feature again at Fighter levels 6, 8, 12, 14, and 16.',
    ),
    (
        ("Fighter", "Fighter Class Features", "Level 5: Extra Attack"),
        "#### Level 5: Extra Attack",
    ),
    (
        ("Fighter", "Fighter Class Features", "Level 5: Extra Attack"),
        "You can attack twice instead of once whenever you take the Attack action on your turn.",
    ),
    (
        ("Fighter", "Fighter Class Features", "Level 5: Tactical Shift"),
        "#### Level 5: Tactical Shift",
    ),
    (
        ("Fighter", "Fighter Class Features", "Level 5: Tactical Shift"),
        "Whenever you activate your Second Wind with a Bonus Action, you can move up to half your Speed without provoking Opportunity Attacks.",
    ),
    (
        ("Fighter", "Fighter Class Features", "Level 9: Indomitable"),
        "#### Level 9: Indomitable",
    ),
    (
        ("Fighter", "Fighter Class Features", "Level 9: Indomitable"),
        "If you fail a saving throw, you can reroll it with a bonus equal to your Fighter level. You must use the new roll, and you can't use this feature again until you finish a Long Rest.",
    ),
    (
        ("Fighter", "Fighter Class Features", "Level 9: Indomitable"),
        "You can use this feature twice before a Long Rest starting at level 13 and three times before a Long Rest starting at level 17.",
    ),
    (
        ("Fighter", "Fighter Class Features", "Level 9: Tactical Master"),
        "#### Level 9: Tactical Master",
    ),
    (
        ("Fighter", "Fighter Class Features", "Level 9: Tactical Master"),
        "When you attack with a weapon whose mastery property you can use, you can replace that property with the Push, Sap, or Slow property for that attack.",
    ),
    (
        ("Fighter", "Fighter Class Features", "Level 11: Two Extra Attacks"),
        "#### Level 11: Two Extra Attacks",
    ),
    (
        ("Fighter", "Fighter Class Features", "Level 11: Two Extra Attacks"),
        "You can attack three times instead of once whenever you take the Attack action on your turn.",
    ),
    (
        ("Fighter", "Fighter Class Features", "Level 13: Studied Attacks"),
        "#### Level 13: Studied Attacks",
    ),
    (
        ("Fighter", "Fighter Class Features", "Level 13: Studied Attacks"),
        "You study your opponents and learn from each attack you make. If you make an attack roll against a creature and miss, you have Advantage on your next attack roll against that creature before the end of your next turn.",
    ),
    (
        ("Fighter", "Fighter Class Features", "Level 19: Epic Boon"),
        "#### Level 19: Epic Boon",
    ),
    (
        ("Fighter", "Fighter Class Features", "Level 19: Epic Boon"),
        'You gain an Epic Boon feat (see "Feats") or another feat of your choice for which you qualify. Boon of Combat Prowess is recommended.',
    ),
    (
        ("Fighter", "Fighter Class Features", "Level 20: Three Extra Attacks"),
        "#### Level 20: Three Extra Attacks",
    ),
    (
        ("Fighter", "Fighter Class Features", "Level 20: Three Extra Attacks"),
        "You can attack four times instead of once whenever you take the Attack action on your turn.",
    ),
    (("Fighter", "Fighter Subclass: Champion"), "### Fighter Subclass: Champion"),
    (
        ("Fighter", "Fighter Subclass: Champion"),
        "_Pursue Physical Excellence in Combat_",
    ),
    (
        ("Fighter", "Fighter Subclass: Champion"),
        "A Champion focuses on the development of martial prowess in a relentless pursuit of victory. Champions combine rigorous training with physical excellence to deal devastating blows, withstand peril, and garner glory. Whether in athletic contests or bloody battle, Champions strive for the crown of the victor.",
    ),
    (
        ("Fighter", "Fighter Subclass: Champion", "Level 3: Improved Critical"),
        "#### Level 3: Improved Critical",
    ),
    (
        ("Fighter", "Fighter Subclass: Champion", "Level 3: Improved Critical"),
        "Your attack rolls with weapons and Unarmed Strikes can score a Critical Hit on a roll of 19 or 20 on the d20.",
    ),
    (
        ("Fighter", "Fighter Subclass: Champion", "Level 3: Remarkable Athlete"),
        "#### Level 3: Remarkable Athlete",
    ),
    (
        ("Fighter", "Fighter Subclass: Champion", "Level 3: Remarkable Athlete"),
        "Thanks to your athleticism, you have Advantage on Initiative rolls and Strength (Athletics) checks.",
    ),
    (
        ("Fighter", "Fighter Subclass: Champion", "Level 3: Remarkable Athlete"),
        "In addition, immediately after you score a Critical Hit, you can move up to half your Speed without provoking Opportunity Attacks.",
    ),
    (
        ("Fighter", "Fighter Subclass: Champion", "Level 7: Additional Fighting Style"),
        "#### Level 7: Additional Fighting Style",
    ),
    (
        ("Fighter", "Fighter Subclass: Champion", "Level 7: Additional Fighting Style"),
        "You gain another Fighting Style feat of your choice.",
    ),
    (
        ("Fighter", "Fighter Subclass: Champion", "Level 10: Heroic Warrior"),
        "#### Level 10: Heroic Warrior",
    ),
    (
        ("Fighter", "Fighter Subclass: Champion", "Level 10: Heroic Warrior"),
        "The thrill of battle drives you toward victory. During combat, you can give yourself Heroic Inspiration whenever you start your turn without it.",
    ),
    (
        ("Fighter", "Fighter Subclass: Champion", "Level 15: Superior Critical"),
        "#### Level 15: Superior Critical",
    ),
    (
        ("Fighter", "Fighter Subclass: Champion", "Level 15: Superior Critical"),
        "Your attack rolls with weapons and Unarmed Strikes can now score a Critical Hit on a roll of 18–20 on the d20.",
    ),
    (
        ("Fighter", "Fighter Subclass: Champion", "Level 18: Survivor"),
        "#### Level 18: Survivor",
    ),
    (
        ("Fighter", "Fighter Subclass: Champion", "Level 18: Survivor"),
        "You attain the pinnacle of resilience in battle, giving you these benefits.",
    ),
    (
        ("Fighter", "Fighter Subclass: Champion", "Level 18: Survivor"),
        "_Defy Death._ You have Advantage on Death Saving Throws. Moreover, when you roll 18–20 on a Death Saving Throw, you gain the benefit of rolling a 20 on it.",
    ),
    (
        ("Fighter", "Fighter Subclass: Champion", "Level 18: Survivor"),
        "_Heroic Rally._ At the start of each of your turns, you regain Hit Points equal to 5 plus your Constitution modifier if you are Bloodied and have at least 1 Hit Point.",
    ),
    (("Monk",), "## Monk"),
    (
        ("Monk",),
        "**Core Monk Traits**\n\n<table>\n  <tbody>\n    <tr>\n      <td>Primary Ability</td>\n      <td>Dexterity and Wisdom</td>\n    </tr>\n    <tr>\n      <td>Hit Point Die</td>\n      <td>D8 per Monk level</td>\n    </tr>\n    <tr>\n      <td>Saving Throw Proficiencies</td>\n      <td>Strength and Dexterity</td>\n    </tr>\n    <tr>\n      <td>Skill Proficiencies</td>\n      <td>Choose 2: Acrobatics, Athletics, History, Insight, Religion, or Stealth</td>\n    </tr>\n    <tr>\n      <td>Weapon Proficiencies</td>\n      <td>Simple weapons and Martial weapons that have the Light property</td>\n    </tr>\n    <tr>\n      <td>Tool Proficiencies</td>\n      <td>Choose one type of Artisan's Tools or Musical Instrument (see Equipment)</td>\n    </tr>\n    <tr>\n      <td>Armor Training</td>\n      <td>None</td>\n    </tr>\n    <tr>\n      <td>Starting Equipment</td>\n      <td>Choose A or B: (A) Spear, 5 Daggers, Artisan's Tools or Musical Instrument chosen for the tool proficiency above, Explorer's Pack, and 11 GP; or (B) 50 GP</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (("Monk", "Becoming a Monk …"), "### Becoming a Monk …"),
    (
        ("Monk", "Becoming a Monk …", "As a Level 1 Character"),
        "#### As a Level 1 Character",
    ),
    (
        ("Monk", "Becoming a Monk …", "As a Level 1 Character"),
        "- Gain all the traits in the Core Monk Traits table.\n- Gain the Monk's level 1 features, which are listed in the Monk Features table.",
    ),
    (
        ("Monk", "Becoming a Monk …", "As a Multiclass Character"),
        "#### As a Multiclass Character",
    ),
    (
        ("Monk", "Becoming a Monk …", "As a Multiclass Character"),
        "- Gain the Hit Point Die trait from the Core Monk Traits table.\n- Gain the Monk's level 1 features, which are listed in the Monk Features table.",
    ),
    (("Monk", "Monk Class Features"), "### Monk Class Features"),
    (
        ("Monk", "Monk Class Features"),
        "As a Monk, you gain the following class features when you reach the specified Monk levels. These features are listed in the Monk Features table.",
    ),
    (
        ("Monk", "Monk Class Features"),
        "**Monk Features**\n\n<table>\n  <thead>\n    <tr>\n      <th>Level</th>\n      <th>Proficiency Bonus</th>\n      <th>Class Features</th>\n      <th>Martial Arts</th>\n      <th>Focus Points</th>\n      <th>Unarmored Movement</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>1</td>\n      <td>+2</td>\n      <td>Martial Arts, Unarmored Defense</td>\n      <td>1d6</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>2</td>\n      <td>+2</td>\n      <td>Monk's Focus, Unarmored Movement, Uncanny Metabolism</td>\n      <td>1d6</td>\n      <td>2</td>\n      <td>+10 ft.</td>\n    </tr>\n    <tr>\n      <td>3</td>\n      <td>+2</td>\n      <td>Deflect Attacks, Monk Subclass</td>\n      <td>1d6</td>\n      <td>3</td>\n      <td>+10 ft.</td>\n    </tr>\n    <tr>\n      <td>4</td>\n      <td>+2</td>\n      <td>Ability Score Improvement, Slow Fall</td>\n      <td>1d6</td>\n      <td>4</td>\n      <td>+10 ft.</td>\n    </tr>\n    <tr>\n      <td>5</td>\n      <td>+3</td>\n      <td>Extra Attack, Stunning Strike</td>\n      <td>1d8</td>\n      <td>5</td>\n      <td>+10 ft.</td>\n    </tr>\n    <tr>\n      <td>6</td>\n      <td>+3</td>\n      <td>Empowered Strikes, Subclass feature</td>\n      <td>1d8</td>\n      <td>6</td>\n      <td>+15 ft.</td>\n    </tr>\n    <tr>\n      <td>7</td>\n      <td>+3</td>\n      <td>Evasion</td>\n      <td>1d8</td>\n      <td>7</td>\n      <td>+15 ft.</td>\n    </tr>\n    <tr>\n      <td>8</td>\n      <td>+3</td>\n      <td>Ability Score Improvement</td>\n      <td>1d8</td>\n      <td>8</td>\n      <td>+15 ft.</td>\n    </tr>\n    <tr>\n      <td>9</td>\n      <td>+4</td>\n      <td>Acrobatic Movement</td>\n      <td>1d8</td>\n      <td>9</td>\n      <td>+15 ft.</td>\n    </tr>\n    <tr>\n      <td>10</td>\n      <td>+4</td>\n      <td>Heightened Focus, Self-Restoration</td>\n      <td>1d8</td>\n      <td>10</td>\n      <td>+20 ft.</td>\n    </tr>\n    <tr>\n      <td>11</td>\n      <td>+4</td>\n      <td>Subclass feature</td>\n      <td>1d10</td>\n      <td>11</td>\n      <td>+20 ft.</td>\n    </tr>\n    <tr>\n      <td>12</td>\n      <td>+4</td>\n      <td>Ability Score Improvement</td>\n      <td>1d10</td>\n      <td>12</td>\n      <td>+20 ft.</td>\n    </tr>\n    <tr>\n      <td>13</td>\n      <td>+5</td>\n      <td>Deflect Energy</td>\n      <td>1d10</td>\n      <td>13</td>\n      <td>+20 ft.</td>\n    </tr>\n    <tr>\n      <td>14</td>\n      <td>+5</td>\n      <td>Disciplined Survivor</td>\n      <td>1d10</td>\n      <td>14</td>\n      <td>+25 ft.</td>\n    </tr>\n    <tr>\n      <td>15</td>\n      <td>+5</td>\n      <td>Perfect Focus</td>\n      <td>1d10</td>\n      <td>15</td>\n      <td>+25 ft.</td>\n    </tr>\n    <tr>\n      <td>16</td>\n      <td>+5</td>\n      <td>Ability Score Improvement</td>\n      <td>1d10</td>\n      <td>16</td>\n      <td>+25 ft.</td>\n    </tr>\n    <tr>\n      <td>17</td>\n      <td>+6</td>\n      <td>Subclass feature</td>\n      <td>1d12</td>\n      <td>17</td>\n      <td>+25 ft.</td>\n    </tr>\n    <tr>\n      <td>18</td>\n      <td>+6</td>\n      <td>Superior Defense</td>\n      <td>1d12</td>\n      <td>18</td>\n      <td>+30 ft.</td>\n    </tr>\n    <tr>\n      <td>19</td>\n      <td>+6</td>\n      <td>Epic Boon</td>\n      <td>1d12</td>\n      <td>19</td>\n      <td>+30 ft.</td>\n    </tr>\n    <tr>\n      <td>20</td>\n      <td>+6</td>\n      <td>Body and Mind</td>\n      <td>1d12</td>\n      <td>20</td>\n      <td>+30 ft.</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        ("Monk", "Monk Class Features", "Level 1: Martial Arts"),
        "#### Level 1: Martial Arts",
    ),
    (
        ("Monk", "Monk Class Features", "Level 1: Martial Arts"),
        "Your practice of martial arts gives you mastery of combat styles that use your Unarmed Strike and Monk weapons, which are the following:",
    ),
    (
        ("Monk", "Monk Class Features", "Level 1: Martial Arts"),
        "- Simple Melee weapons\n- Martial Melee weapons that have the Light property",
    ),
    (
        ("Monk", "Monk Class Features", "Level 1: Martial Arts"),
        "You gain the following benefits while you are unarmed or wielding only Monk weapons and you aren't wearing armor or wielding a Shield.",
    ),
    (
        ("Monk", "Monk Class Features", "Level 1: Martial Arts"),
        "_Bonus Unarmed Strike._ You can make an Unarmed Strike as a Bonus Action.",
    ),
    (
        ("Monk", "Monk Class Features", "Level 1: Martial Arts"),
        "_Martial Arts Die._ You can roll 1d6 in place of the normal damage of your Unarmed Strike or Monk weapons. This die changes as you gain Monk levels, as shown in the Martial Arts column of the Monk Features table.",
    ),
    (
        ("Monk", "Monk Class Features", "Level 1: Martial Arts"),
        "_Dexterous Attacks._ You can use your Dexterity modifier instead of your Strength modifier for the attack and damage rolls of your Unarmed Strikes and Monk weapons. In addition, when you use the Grapple or Shove option of your Unarmed Strike, you can use your Dexterity modifier instead of your Strength modifier to determine the save DC.",
    ),
    (
        ("Monk", "Monk Class Features", "Level 1: Unarmored Defense"),
        "#### Level 1: Unarmored Defense",
    ),
    (
        ("Monk", "Monk Class Features", "Level 1: Unarmored Defense"),
        "While you aren't wearing armor or wielding a Shield, your base Armor Class equals 10 plus your Dexterity and Wisdom modifiers.",
    ),
    (
        ("Monk", "Monk Class Features", "Level 2: Monk's Focus"),
        "#### Level 2: Monk's Focus",
    ),
    (
        ("Monk", "Monk Class Features", "Level 2: Monk's Focus"),
        "Your focus and martial training allow you to harness a well of extraordinary energy within yourself. This energy is represented by Focus Points. Your Monk level determines the number of points you have, as shown in the Focus Points column of the Monk Features table.",
    ),
    (
        ("Monk", "Monk Class Features", "Level 2: Monk's Focus"),
        "You can expend these points to enhance or fuel certain Monk features. You start knowing three such features: Flurry of Blows, Patient Defense, and Step of the Wind, each of which is detailed below.",
    ),
    (
        ("Monk", "Monk Class Features", "Level 2: Monk's Focus"),
        "When you expend a Focus Point, it is unavailable until you finish a Short or Long Rest, at the end of which you regain all your expended points.",
    ),
    (
        ("Monk", "Monk Class Features", "Level 2: Monk's Focus"),
        "Some features that use Focus Points require your target to make a saving throw. The save DC equals 8 plus your Wisdom modifier and Proficiency Bonus.",
    ),
    (
        ("Monk", "Monk Class Features", "Level 2: Monk's Focus"),
        "**_Flurry of Blows._** You can expend 1 Focus Point to make two Unarmed Strikes as a Bonus Action.",
    ),
    (
        ("Monk", "Monk Class Features", "Level 2: Monk's Focus"),
        "**_Patient Defense._** You can take the Disengage action as a Bonus Action. Alternatively, you can\nexpend 1 Focus Point to take both the Disengage and the Dodge actions as a Bonus Action.",
    ),
    (
        ("Monk", "Monk Class Features", "Level 2: Monk's Focus"),
        "**_Step of the Wind._** You can take the Dash action as a Bonus Action. Alternatively, you can expend 1 Focus Point to take both the Disengage and Dash actions as a Bonus Action, and your jump distance is doubled for the turn.",
    ),
    (
        ("Monk", "Monk Class Features", "Level 2: Unarmored Movement"),
        "#### Level 2: Unarmored Movement",
    ),
    (
        ("Monk", "Monk Class Features", "Level 2: Unarmored Movement"),
        "Your speed increases by 10 feet while you aren't wearing armor or wielding a Shield. This bonus increases when you reach certain Monk levels, as shown on the Monk Features table.",
    ),
    (
        ("Monk", "Monk Class Features", "Level 2: Uncanny Metabolism"),
        "#### Level 2: Uncanny Metabolism",
    ),
    (
        ("Monk", "Monk Class Features", "Level 2: Uncanny Metabolism"),
        "When you roll Initiative, you can regain all expended Focus Points. When you do so, roll your Martial Arts die, and regain a number of Hit Points equal to your Monk level plus the number rolled.",
    ),
    (
        ("Monk", "Monk Class Features", "Level 2: Uncanny Metabolism"),
        "Once you use this feature, you can't use it again until you finish a Long Rest.",
    ),
    (
        ("Monk", "Monk Class Features", "Level 3: Deflect Attacks"),
        "#### Level 3: Deflect Attacks",
    ),
    (
        ("Monk", "Monk Class Features", "Level 3: Deflect Attacks"),
        "When an attack roll hits you and its damage includes Bludgeoning, Piercing, or Slashing damage, you can take a Reaction to reduce the attack's total damage against you. The reduction equals 1d10 plus your Dexterity modifier and Monk level.",
    ),
    (
        ("Monk", "Monk Class Features", "Level 3: Deflect Attacks"),
        "If you reduce the damage to 0, you can expend 1 Focus Point to redirect some of the attack's force. If you do so, choose a creature you can see within 5 feet of yourself if the attack was a melee attack or a creature you can see within 60 feet of yourself that isn't behind Total Cover if the attack was a ranged attack. That creature must succeed on a Dexterity saving throw or take damage equal to two rolls of your Martial Arts die plus your Dexterity modifier. The damage is the same type dealt by the attack.",
    ),
    (
        ("Monk", "Monk Class Features", "Level 3: Monk Subclass"),
        "#### Level 3: Monk Subclass",
    ),
    (
        ("Monk", "Monk Class Features", "Level 3: Monk Subclass"),
        "You gain a Monk subclass of your choice. The Warrior of the Open Hand subclass is detailed after this class's description. A subclass is a specialization that grants you features at certain Monk levels. For the rest of your career, you gain each of your subclass's features that are of your Monk level or lower.",
    ),
    (
        ("Monk", "Monk Class Features", "Level 4: Ability Score Improvement"),
        "#### Level 4: Ability Score Improvement",
    ),
    (
        ("Monk", "Monk Class Features", "Level 4: Ability Score Improvement"),
        'You gain the Ability Score Improvement feat (see "Feats") or another feat of your choice for which you qualify. You gain this feature again at Monk levels 8, 12, and 16.',
    ),
    (("Monk", "Monk Class Features", "Level 4: Slow Fall"), "#### Level 4: Slow Fall"),
    (
        ("Monk", "Monk Class Features", "Level 4: Slow Fall"),
        "You can take a Reaction when you fall to reduce any damage you take from the fall by an amount equal to five times your Monk level.",
    ),
    (
        ("Monk", "Monk Class Features", "Level 5: Extra Attack"),
        "#### Level 5: Extra Attack",
    ),
    (
        ("Monk", "Monk Class Features", "Level 5: Extra Attack"),
        "You can attack twice instead of once whenever you take the Attack action on your turn.",
    ),
    (
        ("Monk", "Monk Class Features", "Level 5: Stunning Strike"),
        "#### Level 5: Stunning Strike",
    ),
    (
        ("Monk", "Monk Class Features", "Level 5: Stunning Strike"),
        "Once per turn when you hit a creature with a Monk weapon or an Unarmed Strike, you can expend 1 Focus Point to attempt a stunning strike. The target must make a Constitution saving throw. On a failed save, the target has the Stunned condition until the start of your next turn. On a successful save, the target's Speed is halved until the start of your next turn, and the next attack roll made against the target before then has Advantage.",
    ),
    (
        ("Monk", "Monk Class Features", "Level 6: Empowered Strikes"),
        "#### Level 6: Empowered Strikes",
    ),
    (
        ("Monk", "Monk Class Features", "Level 6: Empowered Strikes"),
        "Whenever you deal damage with your Unarmed Strike, it can deal your choice of Force damage or its normal damage type.",
    ),
    (("Monk", "Monk Class Features", "Level 7: Evasion"), "#### Level 7: Evasion"),
    (
        ("Monk", "Monk Class Features", "Level 7: Evasion"),
        "When you're subjected to an effect that allows you to make a Dexterity saving throw to take only half damage, you instead take no damage if you succeed on the saving throw and only half damage if you fail.",
    ),
    (
        ("Monk", "Monk Class Features", "Level 7: Evasion"),
        "You don't benefit from this feature if you have the Incapacitated condition.",
    ),
    (
        ("Monk", "Monk Class Features", "Level 9: Acrobatic Movement"),
        "#### Level 9: Acrobatic Movement",
    ),
    (
        ("Monk", "Monk Class Features", "Level 9: Acrobatic Movement"),
        "While you aren't wearing armor or wielding a Shield, you gain the ability to move along vertical surfaces and across liquids on your turn without falling during the movement.",
    ),
    (
        ("Monk", "Monk Class Features", "Level 10: Heightened Focus"),
        "#### Level 10: Heightened Focus",
    ),
    (
        ("Monk", "Monk Class Features", "Level 10: Heightened Focus"),
        "Your Flurry of Blows, Patient Defense, and Step of the Wind gain the following benefits.",
    ),
    (
        ("Monk", "Monk Class Features", "Level 10: Heightened Focus"),
        "**_Flurry of Blows._** You can expend 1 Focus Point to use Flurry of Blows and make three Unarmed Strikes with it instead of two.",
    ),
    (
        ("Monk", "Monk Class Features", "Level 10: Heightened Focus"),
        "**_Patient Defense._** When you expend a Focus Point to use Patient Defense, you gain a number of Temporary Hit Points equal to two rolls of your Martial Arts die.",
    ),
    (
        ("Monk", "Monk Class Features", "Level 10: Heightened Focus"),
        "**_Step of the Wind._** When you expend a Focus Point to use Step of the Wind, you can choose a willing creature within 5 feet of yourself that is Large or smaller. You move the creature with you until the end of your turn. The creature's movement doesn't provoke Opportunity Attacks.",
    ),
    (
        ("Monk", "Monk Class Features", "Level 10: Self-Restoration"),
        "#### Level 10: Self-Restoration",
    ),
    (
        ("Monk", "Monk Class Features", "Level 10: Self-Restoration"),
        "Through sheer force of will, you can remove one of the following conditions from yourself at the end of each of your turns: Charmed, Frightened, or Poisoned.",
    ),
    (
        ("Monk", "Monk Class Features", "Level 10: Self-Restoration"),
        "In addition, forgoing food and drink doesn't give you levels of Exhaustion.",
    ),
    (
        ("Monk", "Monk Class Features", "Level 13: Deflect Energy"),
        "#### Level 13: Deflect Energy",
    ),
    (
        ("Monk", "Monk Class Features", "Level 13: Deflect Energy"),
        "You can now use your Deflect Attacks feature against attacks that deal any damage type, not just Bludgeoning, Piercing, or Slashing.",
    ),
    (
        ("Monk", "Monk Class Features", "Level 14: Disciplined Survivor"),
        "#### Level 14: Disciplined Survivor",
    ),
    (
        ("Monk", "Monk Class Features", "Level 14: Disciplined Survivor"),
        "Your physical and mental discipline grant you proficiency in all saving throws.",
    ),
    (
        ("Monk", "Monk Class Features", "Level 14: Disciplined Survivor"),
        "Additionally, whenever you make a saving throw and fail, you can expend 1 Focus Point to reroll it, and you must use the new roll.",
    ),
    (
        ("Monk", "Monk Class Features", "Level 15: Perfect Focus"),
        "#### Level 15: Perfect Focus",
    ),
    (
        ("Monk", "Monk Class Features", "Level 15: Perfect Focus"),
        "When you roll Initiative and don't use Uncanny Metabolism, you regain expended Focus Points until you have 4 if you have 3 or fewer.",
    ),
    (
        ("Monk", "Monk Class Features", "Level 18: Superior Defense"),
        "#### Level 18: Superior Defense",
    ),
    (
        ("Monk", "Monk Class Features", "Level 18: Superior Defense"),
        "At the start of your turn, you can expend 3 Focus Points to bolster yourself against harm for 1 minute or until you have the Incapacitated condition. During that time, you have Resistance to all damage except Force damage.",
    ),
    (
        ("Monk", "Monk Class Features", "Level 19: Epic Boon"),
        "#### Level 19: Epic Boon",
    ),
    (
        ("Monk", "Monk Class Features", "Level 19: Epic Boon"),
        'You gain an Epic Boon feat (see "Feats") or another feat of your choice for which you qualify. Boon of Irresistible Offense is recommended.',
    ),
    (
        ("Monk", "Monk Class Features", "Level 20: Body and Mind"),
        "#### Level 20: Body and Mind",
    ),
    (
        ("Monk", "Monk Class Features", "Level 20: Body and Mind"),
        "You have developed your body and mind to new heights. Your Dexterity and Wisdom scores increase by 4, to a maximum of 25.",
    ),
    (
        ("Monk", "Monk Subclass: Warrior of the Open Hand"),
        "### Monk Subclass: Warrior of the Open Hand",
    ),
    (
        ("Monk", "Monk Subclass: Warrior of the Open Hand"),
        "_Master Unarmed Combat Techniques_",
    ),
    (
        ("Monk", "Monk Subclass: Warrior of the Open Hand"),
        "Warriors of the Open Hand are masters of unarmed combat. They learn techniques to push and trip their opponents and manipulate their own energy to protect themselves from harm.",
    ),
    (
        (
            "Monk",
            "Monk Subclass: Warrior of the Open Hand",
            "Level 3: Open Hand Technique",
        ),
        "#### Level 3: Open Hand Technique",
    ),
    (
        (
            "Monk",
            "Monk Subclass: Warrior of the Open Hand",
            "Level 3: Open Hand Technique",
        ),
        "Whenever you hit a creature with an attack granted by your Flurry of Blows, you can impose one of the following effects on that target.",
    ),
    (
        (
            "Monk",
            "Monk Subclass: Warrior of the Open Hand",
            "Level 3: Open Hand Technique",
        ),
        "**Addle.** The target can't make Opportunity Attacks until the start of its next turn.",
    ),
    (
        (
            "Monk",
            "Monk Subclass: Warrior of the Open Hand",
            "Level 3: Open Hand Technique",
        ),
        "**Push.** The target must succeed on a Strength saving throw or be pushed up to 15 feet away from you.",
    ),
    (
        (
            "Monk",
            "Monk Subclass: Warrior of the Open Hand",
            "Level 3: Open Hand Technique",
        ),
        "**Topple.** The target must succeed on a Dexterity saving throw or have the Prone condition.",
    ),
    (
        (
            "Monk",
            "Monk Subclass: Warrior of the Open Hand",
            "Level 6: Wholeness of Body",
        ),
        "#### Level 6: Wholeness of Body",
    ),
    (
        (
            "Monk",
            "Monk Subclass: Warrior of the Open Hand",
            "Level 6: Wholeness of Body",
        ),
        "You gain the ability to heal yourself. As a Bonus Action, you can roll your Martial Arts die. You regain a number of Hit Points equal to the number rolled plus your Wisdom modifier (minimum of 1 Hit Point regained).",
    ),
    (
        (
            "Monk",
            "Monk Subclass: Warrior of the Open Hand",
            "Level 6: Wholeness of Body",
        ),
        "You can use this feature a number of times equal to your Wisdom modifier (minimum of once), and you regain all expended uses when you finish a Long Rest.",
    ),
    (
        ("Monk", "Monk Subclass: Warrior of the Open Hand", "Level 11: Fleet Step"),
        "#### Level 11: Fleet Step",
    ),
    (
        ("Monk", "Monk Subclass: Warrior of the Open Hand", "Level 11: Fleet Step"),
        "When you take a Bonus Action other than Step of the Wind, you can also use Step of the Wind immediately after that Bonus Action.",
    ),
    (
        ("Monk", "Monk Subclass: Warrior of the Open Hand", "Level 17: Quivering Palm"),
        "#### Level 17: Quivering Palm",
    ),
    (
        ("Monk", "Monk Subclass: Warrior of the Open Hand", "Level 17: Quivering Palm"),
        "You gain the ability to set up lethal vibrations in someone's body. When you hit a creature with an Unarmed Strike, you can expend 4 Focus Points to start these imperceptible vibrations, which last for a number of days equal to your Monk level. The vibrations are harmless unless you take an action to end them. Alternatively, when you take the Attack action on your turn, you can forgo one of the attacks to end the vibrations. To end them, you and the target must be on the same plane of existence. When you end them, the target must make a Constitution saving throw, taking 10d12 Force damage on a failed save or half as much damage on a successful one.",
    ),
    (
        ("Monk", "Monk Subclass: Warrior of the Open Hand", "Level 17: Quivering Palm"),
        "You can have only one creature under the effect of this feature at a time. You can end the vibrations harmlessly (no action required).",
    ),
    (("Paladin",), "## Paladin"),
    (
        ("Paladin",),
        "**Core Paladin Traits**\n\n<table>\n  <tbody>\n    <tr>\n      <td>Primary Ability</td>\n      <td>Strength and Charisma</td>\n    </tr>\n    <tr>\n      <td>Hit Point Die</td>\n      <td>D10 per Paladin level</td>\n    </tr>\n    <tr>\n      <td>Saving Throw Proficiencies</td>\n      <td>Wisdom and Charisma</td>\n    </tr>\n    <tr>\n      <td>Skill Proficiencies</td>\n      <td>Choose 2: Athletics, Insight, Intimidation, Medicine, Persuasion, or Religion</td>\n    </tr>\n    <tr>\n      <td>Weapon Proficiencies</td>\n      <td>Simple and Martial weapons</td>\n    </tr>\n    <tr>\n      <td>Armor Training</td>\n      <td>Light, Medium, and Heavy armor and Shields</td>\n    </tr>\n    <tr>\n      <td>Starting Equipment</td>\n      <td>Choose A or B: (A) Chain Mail, Shield, Longsword, 6 Javelins, Holy Symbol, Priest's Pack, and 9 GP; or (B) 150 GP</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (("Paladin", "Becoming a Paladin …"), "### Becoming a Paladin …"),
    (
        ("Paladin", "Becoming a Paladin …", "As a Level 1 Character"),
        "#### As a Level 1 Character",
    ),
    (
        ("Paladin", "Becoming a Paladin …", "As a Level 1 Character"),
        "• Gain all the traits in the Core Paladin Traits table.",
    ),
    (
        ("Paladin", "Becoming a Paladin …", "As a Level 1 Character"),
        "• Gain the Paladin's level 1 features, which are listed in the Paladin Features table.",
    ),
    (
        ("Paladin", "Becoming a Paladin …", "As a Multiclass Character"),
        "#### As a Multiclass Character",
    ),
    (
        ("Paladin", "Becoming a Paladin …", "As a Multiclass Character"),
        "• Gain the following traits from the Core Paladin Traits table: Hit Point Die, proficiency with Martial weapons, and training with Light and Medium armor and Shields.",
    ),
    (
        ("Paladin", "Becoming a Paladin …", "As a Multiclass Character"),
        '• Gain the Paladin\'s level 1 features, which are listed in the Paladin Features table. See the multiclassing rules in "Character Creation" to determine your available spell slots.',
    ),
    (("Paladin", "Paladin Class Features"), "### Paladin Class Features"),
    (
        ("Paladin", "Paladin Class Features"),
        "As a Paladin, you gain the following class features when you reach the specified Paladin levels. These features are listed in the Paladin Features table.",
    ),
    (
        ("Paladin", "Paladin Class Features"),
        '**Paladin Features**\n\n<table>\n  <thead>\n    <tr>\n      <th>Level</th>\n      <th>Proficiency Bonus</th>\n      <th>Class Features</th>\n      <th>Channel Divinity</th>\n      <th>Prepared Spells</th>\n      <th colspan="5">——Spell Slots per Spell Level——</th>\n    </tr>\n    <tr>\n      <th>\n      </th>\n      <th>\n      </th>\n      <th>\n      </th>\n      <th>\n      </th>\n      <th>\n      </th>\n      <th>1</th>\n      <th>2</th>\n      <th>3</th>\n      <th>4</th>\n      <th>5</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>1</td>\n      <td>+2</td>\n      <td>Lay On Hands, Spellcasting, Weapon Mastery</td>\n      <td>—</td>\n      <td>2</td>\n      <td>2</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>2</td>\n      <td>+2</td>\n      <td>Fighting Style, Paladin\'s Smite</td>\n      <td>—</td>\n      <td>3</td>\n      <td>2</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>3</td>\n      <td>+2</td>\n      <td>Channel Divinity, Paladin Subclass</td>\n      <td>2</td>\n      <td>4</td>\n      <td>3</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>4</td>\n      <td>+2</td>\n      <td>Ability Score Improvement</td>\n      <td>2</td>\n      <td>5</td>\n      <td>3</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>5</td>\n      <td>+3</td>\n      <td>Extra Attack, Faithful Steed</td>\n      <td>2</td>\n      <td>6</td>\n      <td>4</td>\n      <td>2</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>6</td>\n      <td>+3</td>\n      <td>Aura of Protection</td>\n      <td>2</td>\n      <td>6</td>\n      <td>4</td>\n      <td>2</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>7</td>\n      <td>+3</td>\n      <td>Subclass feature</td>\n      <td>2</td>\n      <td>7</td>\n      <td>4</td>\n      <td>3</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>8</td>\n      <td>+3</td>\n      <td>Ability Score Improvement</td>\n      <td>2</td>\n      <td>7</td>\n      <td>4</td>\n      <td>3</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>9</td>\n      <td>+4</td>\n      <td>Abjure Foes</td>\n      <td>2</td>\n      <td>9</td>\n      <td>4</td>\n      <td>3</td>\n      <td>2</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>10</td>\n      <td>+4</td>\n      <td>Aura of Courage</td>\n      <td>2</td>\n      <td>9</td>\n      <td>4</td>\n      <td>3</td>\n      <td>2</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>11</td>\n      <td>+4</td>\n      <td>Radiant Strikes</td>\n      <td>3</td>\n      <td>10</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>12</td>\n      <td>+4</td>\n      <td>Ability Score Improvement</td>\n      <td>3</td>\n      <td>10</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>13</td>\n      <td>+5</td>\n      <td>—</td>\n      <td>3</td>\n      <td>11</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>1</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>14</td>\n      <td>+5</td>\n      <td>Restoring Touch</td>\n      <td>3</td>\n      <td>11</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>1</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>15</td>\n      <td>+5</td>\n      <td>Subclass feature</td>\n      <td>3</td>\n      <td>12</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>2</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>16</td>\n      <td>+5</td>\n      <td>Ability Score Improvement</td>\n      <td>3</td>\n      <td>12</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>2</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>17</td>\n      <td>+6</td>\n      <td>—</td>\n      <td>3</td>\n      <td>14</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>3</td>\n      <td>1</td>\n    </tr>\n    <tr>\n      <td>18</td>\n      <td>+6</td>\n      <td>Aura Expansion</td>\n      <td>3</td>\n      <td>14</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>3</td>\n      <td>1</td>\n    </tr>\n    <tr>\n      <td>19</td>\n      <td>+6</td>\n      <td>Epic Boon</td>\n      <td>3</td>\n      <td>15</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>3</td>\n      <td>2</td>\n    </tr>\n    <tr>\n      <td>20</td>\n      <td>+6</td>\n      <td>Subclass feature</td>\n      <td>3</td>\n      <td>15</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>3</td>\n      <td>2</td>\n    </tr>\n  </tbody>\n</table>',
    ),
    (
        ("Paladin", "Paladin Class Features", "Level 1: Lay On Hands"),
        "#### Level 1: Lay On Hands",
    ),
    (
        ("Paladin", "Paladin Class Features", "Level 1: Lay On Hands"),
        "Your blessed touch can heal wounds. You have a pool of healing power that replenishes when you finish a Long Rest. With that pool, you can restore a total number of Hit Points equal to five times your Paladin level.",
    ),
    (
        ("Paladin", "Paladin Class Features", "Level 1: Lay On Hands"),
        "As a Bonus Action, you can touch a creature (which could be yourself) and draw power from the pool of healing to restore a number of Hit Points to that creature, up to the maximum amount remaining in the pool.",
    ),
    (
        ("Paladin", "Paladin Class Features", "Level 1: Lay On Hands"),
        "You can also expend 5 Hit Points from the pool of healing power to remove the Poisoned condition from the creature; those points don't also restore Hit Points to the creature.",
    ),
    (
        ("Paladin", "Paladin Class Features", "Level 1: Spellcasting"),
        "#### Level 1: Spellcasting",
    ),
    (
        ("Paladin", "Paladin Class Features", "Level 1: Spellcasting"),
        'You have learned to cast spells through prayer and meditation. See "Spells" for the rules on spellcasting. The information below details how you use those rules with Paladin spells, which appear in the Paladin spell list later in the class\'s description.',
    ),
    (
        ("Paladin", "Paladin Class Features", "Level 1: Spellcasting"),
        "**Spell Slots.** The Paladin Features table shows how many spell slots you have to cast your level 1+ spells. You regain all expended slots when you finish a Long Rest.",
    ),
    (
        ("Paladin", "Paladin Class Features", "Level 1: Spellcasting"),
        "**Prepared Spells of Level 1+.** You prepare the list of level 1+ spells that are available for you to cast with this feature. To start, choose two level 1 Paladin spells. _Heroism_ and _Searing Smite_ are recommended.",
    ),
    (
        ("Paladin", "Paladin Class Features", "Level 1: Spellcasting"),
        "The number of spells on your list increases as you gain Paladin levels, as shown in the Prepared Spells column of the Paladin Features table. Whenever that number increases, choose additional Paladin spells until the number of spells on your list matches the number in the Paladin Features table. The chosen spells must be of a level for which you have spell slots. For example, if you're a level 5 Paladin, your list of prepared spells can include six Paladin spells of level 1 or 2 in any combination.",
    ),
    (
        ("Paladin", "Paladin Class Features", "Level 1: Spellcasting"),
        "If another Paladin feature gives you spells that you always have prepared, those spells don't count against the number of spells you can prepare with this feature, but those spells otherwise count as Paladin spells for you.",
    ),
    (
        ("Paladin", "Paladin Class Features", "Level 1: Spellcasting"),
        "**Changing Your Prepared Spells.** Whenever you finish a Long Rest, you can replace one spell on your list with another Paladin spell for which you have spell slots.",
    ),
    (
        ("Paladin", "Paladin Class Features", "Level 1: Spellcasting"),
        "**Spellcasting Ability.** Charisma is your spellcasting ability for your Paladin spells.",
    ),
    (
        ("Paladin", "Paladin Class Features", "Level 1: Spellcasting"),
        "**Spellcasting Focus.** You can use a Holy Symbol as a Spellcasting Focus for your Paladin spells.",
    ),
    (
        ("Paladin", "Paladin Class Features", "Level 1: Weapon Mastery"),
        "#### Level 1: Weapon Mastery",
    ),
    (
        ("Paladin", "Paladin Class Features", "Level 1: Weapon Mastery"),
        "Your training with weapons allows you to use the mastery properties of two kinds of weapons of your choice with which you have proficiency, such as Longswords and Javelins.",
    ),
    (
        ("Paladin", "Paladin Class Features", "Level 1: Weapon Mastery"),
        "Whenever you finish a Long Rest, you can change the kinds of weapons you chose. For example, you could switch to using the mastery properties of Halberds and Flails.",
    ),
    (
        ("Paladin", "Paladin Class Features", "Level 2: Fighting Style"),
        "#### Level 2: Fighting Style",
    ),
    (
        ("Paladin", "Paladin Class Features", "Level 2: Fighting Style"),
        'You gain a Fighting Style feat of your choice (see "Feats" for feats). Instead of choosing one of those feats, you can choose the option below.',
    ),
    (
        ("Paladin", "Paladin Class Features", "Level 2: Fighting Style"),
        "**Blessed Warrior.** You learn two Cleric cantrips of your choice (see the Cleric class's section for a list of Cleric spells). _Guidance_ and _Sacred Flame_ are recommended. The chosen cantrips count as Paladin spells for you, and Charisma is your spellcasting ability for them. Whenever you gain a Paladin level, you can replace one of these cantrips with another Cleric cantrip.",
    ),
    (
        ("Paladin", "Paladin Class Features", "Level 2: Paladin's Smite"),
        "#### Level 2: Paladin's Smite",
    ),
    (
        ("Paladin", "Paladin Class Features", "Level 2: Paladin's Smite"),
        "You always have the _Divine Smite_ spell prepared. In addition, you can cast it without expending a spell slot, but you must finish a Long Rest before you can cast it in this way again.",
    ),
    (
        ("Paladin", "Paladin Class Features", "Level 3: Channel Divinity"),
        "#### Level 3: Channel Divinity",
    ),
    (
        ("Paladin", "Paladin Class Features", "Level 3: Channel Divinity"),
        "You can channel divine energy directly from the Outer Planes, using it to fuel magical effects. You start with one such effect: Divine Sense, which is described below. Other Paladin features give additional Channel Divinity effect options. Each time you use this class's Channel Divinity, you choose which effect from this class to create.",
    ),
    (
        ("Paladin", "Paladin Class Features", "Level 3: Channel Divinity"),
        "You can use this class's Channel Divinity twice. You regain one of its expended uses when you finish a Short Rest, and you regain all expended uses when you finish a Long Rest. You gain an additional use when you reach Paladin level 11.",
    ),
    (
        ("Paladin", "Paladin Class Features", "Level 3: Channel Divinity"),
        "> ### Breaking Your Oath\n>\n> A Paladin tries to hold to the highest standards of conduct, but even the most dedicated are fallible. Sometimes a Paladin transgresses their oath.\n>\n> A Paladin who has broken a vow typically seeks absolution, spending an all-night vigil as a sign of penitence or undertaking a fast. After a rite of forgiveness, the Paladin starts fresh.\n>\n> If your Paladin unrepentantly violates their oath, talk to your GM. Your Paladin should probably take a more appropriate subclass or even abandon the class and adopt another one.\n> If a Channel Divinity effect requires a saving throw, the DC equals the spell save DC from this class's Spellcasting feature.",
    ),
    (
        ("Paladin", "Paladin Class Features", "Level 3: Channel Divinity"),
        "_Divine Sense._ As a Bonus Action, you can open your awareness to detect Celestials, Fiends, and Undead. For the next 10 minutes or until you have the Incapacitated condition, you know the location of any creature of those types within 60 feet of yourself, and you know its creature type. Within the same radius, you also detect the presence of any place or object that has been consecrated or desecrated, as with the _Hallow_ spell.",
    ),
    (
        ("Paladin", "Paladin Class Features", "Level 3: Paladin Subclass"),
        "#### Level 3: Paladin Subclass",
    ),
    (
        ("Paladin", "Paladin Class Features", "Level 3: Paladin Subclass"),
        "You gain a Paladin subclass of your choice. The Oath of Devotion subclass is detailed after this class's description. A subclass is a specialization that grants you features at certain Paladin levels. For the rest of your career, you gain each of your subclass's features that are of your Paladin level or lower.",
    ),
    (
        ("Paladin", "Paladin Class Features", "Level 4: Ability Score Improvement"),
        "#### Level 4: Ability Score Improvement",
    ),
    (
        ("Paladin", "Paladin Class Features", "Level 4: Ability Score Improvement"),
        'You gain the Ability Score Improvement feat (see "Feats") or another feat of your choice for which you qualify. You gain this feature again at Paladin levels 8, 12, and 16.',
    ),
    (
        ("Paladin", "Paladin Class Features", "Level 5: Extra Attack"),
        "#### Level 5: Extra Attack",
    ),
    (
        ("Paladin", "Paladin Class Features", "Level 5: Extra Attack"),
        "You can attack twice instead of once whenever you take the Attack action on your turn.",
    ),
    (
        ("Paladin", "Paladin Class Features", "Level 5: Faithful Steed"),
        "#### Level 5: Faithful Steed",
    ),
    (
        ("Paladin", "Paladin Class Features", "Level 5: Faithful Steed"),
        "You can call on the aid of an otherworldly steed. You always have the _Find Steed_ spell prepared.",
    ),
    (
        ("Paladin", "Paladin Class Features", "Level 5: Faithful Steed"),
        "You can also cast the spell once without expending a spell slot, and you regain the ability to do so when you finish a Long Rest.",
    ),
    (
        ("Paladin", "Paladin Class Features", "Level 6: Aura of Protection"),
        "#### Level 6: Aura of Protection",
    ),
    (
        ("Paladin", "Paladin Class Features", "Level 6: Aura of Protection"),
        "You radiate a protective, unseeable aura in a 10-foot Emanation that originates from you. The aura is inactive while you have the Incapacitated condition.",
    ),
    (
        ("Paladin", "Paladin Class Features", "Level 6: Aura of Protection"),
        "You and your allies in the aura gain a bonus to saving throws equal to your Charisma modifier (minimum bonus of +1).",
    ),
    (
        ("Paladin", "Paladin Class Features", "Level 6: Aura of Protection"),
        "If another Paladin is present, a creature can benefit from only one Aura of Protection at a time; the creature chooses which aura while in them.",
    ),
    (
        ("Paladin", "Paladin Class Features", "Level 9: Abjure Foes"),
        "#### Level 9: Abjure Foes",
    ),
    (
        ("Paladin", "Paladin Class Features", "Level 9: Abjure Foes"),
        "As a Magic action, you can expend one use of this class's Channel Divinity to overwhelm foes with awe. As you present your Holy Symbol or weapon, you can target a number of creatures equal to your Charisma modifier (minimum of one creature) that you can see within 60 feet of yourself. Each target must succeed on a Wisdom saving throw or have the Frightened condition for 1 minute or until it takes any damage. While Frightened in this way, a target can do only one of the following on its turns: move, take an action, or take a Bonus Action.",
    ),
    (
        ("Paladin", "Paladin Class Features", "Level 10: Aura of Courage"),
        "#### Level 10: Aura of Courage",
    ),
    (
        ("Paladin", "Paladin Class Features", "Level 10: Aura of Courage"),
        "You and your allies have Immunity to the Frightened condition while in your Aura of Protection. If a Frightened ally enters the aura, that condition has no effect on that ally while there.",
    ),
    (
        ("Paladin", "Paladin Class Features", "Level 11: Radiant Strikes"),
        "#### Level 11: Radiant Strikes",
    ),
    (
        ("Paladin", "Paladin Class Features", "Level 11: Radiant Strikes"),
        "Your strikes now carry supernatural power. When you hit a target with an attack roll using a Melee weapon or an Unarmed Strike, the target takes an extra 1d8 Radiant damage.",
    ),
    (
        ("Paladin", "Paladin Class Features", "Level 14: Restoring Touch"),
        "#### Level 14: Restoring Touch",
    ),
    (
        ("Paladin", "Paladin Class Features", "Level 14: Restoring Touch"),
        "When you use Lay On Hands on a creature, you can also remove one or more of the following conditions from the creature: Blinded, Charmed, Deafened, Frightened, Paralyzed, or Stunned. You must expend 5 Hit Points from the healing pool of Lay On Hands for each of these conditions you remove; those points don't also restore Hit Points to the creature.",
    ),
    (
        ("Paladin", "Paladin Class Features", "Level 18: Aura Expansion"),
        "#### Level 18: Aura Expansion",
    ),
    (
        ("Paladin", "Paladin Class Features", "Level 18: Aura Expansion"),
        "Your Aura of Protection is now a 30-foot Emanation.",
    ),
    (
        ("Paladin", "Paladin Class Features", "Level 19: Epic Boon"),
        "#### Level 19: Epic Boon",
    ),
    (
        ("Paladin", "Paladin Class Features", "Level 19: Epic Boon"),
        'You gain an Epic Boon feat (see "Feats") or another feat of your choice for which you qualify. Boon of Truesight is recommended.',
    ),
    (("Paladin", "Paladin Spell List"), "### Paladin Spell List"),
    (
        ("Paladin", "Paladin Spell List"),
        "This section presents the Paladin spell list. The spells are organized by spell level and then alphabetized, and each spell's school of magic is listed. In the Special column, _C_ means the spell requires Concentration, _R_ means it's a Ritual, and _M_ means it requires a specific Material component.",
    ),
    (
        ("Paladin", "Paladin Spell List", "Level 1 Paladin Spells"),
        "#### Level 1 Paladin Spells",
    ),
    (
        ("Paladin", "Paladin Spell List", "Level 1 Paladin Spells"),
        "<table>\n  <thead>\n    <tr>\n      <th>Spell</th>\n      <th>School</th>\n      <th>Special</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>Bless</td>\n      <td>Enchantment</td>\n      <td>C, M</td>\n    </tr>\n    <tr>\n      <td>Command</td>\n      <td>Enchantment</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Cure Wounds</td>\n      <td>Abjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Detect Evil and Good</td>\n      <td>Divination</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Detect Magic</td>\n      <td>Divination</td>\n      <td>C, R</td>\n    </tr>\n    <tr>\n      <td>Detect Poison and Disease</td>\n      <td>Divination</td>\n      <td>C, R</td>\n    </tr>\n    <tr>\n      <td>Divine Favor</td>\n      <td>Transmutation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Divine Smite</td>\n      <td>Evocation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Heroism</td>\n      <td>Enchantment</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Protection from Evil and Good</td>\n      <td>Abjuration</td>\n      <td>C, M</td>\n    </tr>\n    <tr>\n      <td>Purify Food and Drink</td>\n      <td>Transmutation</td>\n      <td>R</td>\n    </tr>\n    <tr>\n      <td>Searing Smite</td>\n      <td>Evocation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Shield of Faith</td>\n      <td>Abjuration</td>\n      <td>C</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        ("Paladin", "Paladin Spell List", "Level 2 Paladin Spells"),
        "#### Level 2 Paladin Spells",
    ),
    (
        ("Paladin", "Paladin Spell List", "Level 2 Paladin Spells"),
        "<table>\n  <thead>\n    <tr>\n      <th>Spell</th>\n      <th>School</th>\n      <th>Special</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>Aid</td>\n      <td>Abjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Find Steed</td>\n      <td>Conjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Gentle Repose</td>\n      <td>Necromancy</td>\n      <td>R, M</td>\n    </tr>\n    <tr>\n      <td>Lesser Restoration</td>\n      <td>Abjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Locate Object</td>\n      <td>Divination</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Magic Weapon</td>\n      <td>Transmutation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Prayer of Healing</td>\n      <td>Abjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Protection from Poison</td>\n      <td>Abjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Shining Smite</td>\n      <td>Transmutation</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Warding Bond</td>\n      <td>Abjuration</td>\n      <td>M</td>\n    </tr>\n    <tr>\n      <td>Zone of Truth</td>\n      <td>Enchantment</td>\n      <td>—</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        ("Paladin", "Paladin Spell List", "Level 3 Paladin Spells"),
        "#### Level 3 Paladin Spells",
    ),
    (
        ("Paladin", "Paladin Spell List", "Level 3 Paladin Spells"),
        "<table>\n  <thead>\n    <tr>\n      <th>Spell</th>\n      <th>School</th>\n      <th>Special</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>Create Food and Water</td>\n      <td>Conjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Daylight</td>\n      <td>Evocation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Dispel Magic</td>\n      <td>Abjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Magic Circle</td>\n      <td>Abjuration</td>\n      <td>M</td>\n    </tr>\n    <tr>\n      <td>Remove Curse</td>\n      <td>Abjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Revivify</td>\n      <td>Necromancy</td>\n      <td>M</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        ("Paladin", "Paladin Spell List", "Level 4 Paladin Spells"),
        "#### Level 4 Paladin Spells",
    ),
    (
        ("Paladin", "Paladin Spell List", "Level 4 Paladin Spells"),
        "<table>\n  <thead>\n    <tr>\n      <th>Spell</th>\n      <th>School</th>\n      <th>Special</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>Aura of Life</td>\n      <td>Abjuration</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Banishment</td>\n      <td>Abjuration</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Death Ward</td>\n      <td>Abjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Locate Creature</td>\n      <td>Divination</td>\n      <td>C</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        ("Paladin", "Paladin Spell List", "Level 5 Paladin Spells"),
        "#### Level 5 Paladin Spells",
    ),
    (
        ("Paladin", "Paladin Spell List", "Level 5 Paladin Spells"),
        "<table>\n  <thead>\n    <tr>\n      <th>Spell</th>\n      <th>School</th>\n      <th>Special</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>Dispel Evil and Good</td>\n      <td>Abjuration</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Geas</td>\n      <td>Enchantment</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Greater Restoration</td>\n      <td>Abjuration</td>\n      <td>M</td>\n    </tr>\n    <tr>\n      <td>Raise Dead</td>\n      <td>Necromancy</td>\n      <td>M</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        ("Paladin", "Paladin Subclass: Oath of Devotion"),
        "### Paladin Subclass: Oath of Devotion",
    ),
    (
        ("Paladin", "Paladin Subclass: Oath of Devotion"),
        "_Uphold the Ideals of Justice and Order_",
    ),
    (
        ("Paladin", "Paladin Subclass: Oath of Devotion"),
        "The Oath of Devotion binds Paladins to the ideals of justice and order. These Paladins meet the archetype of the knight in shining armor. They hold themselves to the highest standards of conduct, and some—for better or worse—hold the rest of the world to the same standards.",
    ),
    (
        ("Paladin", "Paladin Subclass: Oath of Devotion"),
        "Many who swear this oath are devoted to gods of law and good and use their gods' tenets as the measure of personal devotion. Others hold angels as their ideals and incorporate images of angelic wings into their helmets or coats of arms.",
    ),
    (
        ("Paladin", "Paladin Subclass: Oath of Devotion"),
        "These paladins share the following tenets:",
    ),
    (
        ("Paladin", "Paladin Subclass: Oath of Devotion"),
        "- Let your word be your promise.\n- Protect the weak and never fear to act.\n- Let your honorable deeds be an example.",
    ),
    (
        (
            "Paladin",
            "Paladin Subclass: Oath of Devotion",
            "Level 3: Oath of Devotion Spells",
        ),
        "#### Level 3: Oath of Devotion Spells",
    ),
    (
        (
            "Paladin",
            "Paladin Subclass: Oath of Devotion",
            "Level 3: Oath of Devotion Spells",
        ),
        "The magic of your oath ensures you always have certain spells ready; when you reach a Paladin level specified in the Oath of Devotion Spells table, you thereafter always have the listed spells prepared.",
    ),
    (
        (
            "Paladin",
            "Paladin Subclass: Oath of Devotion",
            "Level 3: Oath of Devotion Spells",
        ),
        "**Oath of Devotion Spells**\n\n<table>\n  <thead>\n    <tr>\n      <th>Paladin Level</th>\n      <th>Spells</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>3</td>\n      <td>Protection from Evil and Good, Shield of Faith</td>\n    </tr>\n    <tr>\n      <td>5</td>\n      <td>Aid, Zone of Truth</td>\n    </tr>\n    <tr>\n      <td>9</td>\n      <td>Beacon of Hope, Dispel Magic</td>\n    </tr>\n    <tr>\n      <td>13</td>\n      <td>Freedom of Movement, Guardian of Faith</td>\n    </tr>\n    <tr>\n      <td>17</td>\n      <td>Commune, Flame Strike</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        ("Paladin", "Paladin Subclass: Oath of Devotion", "Level 3: Sacred Weapon"),
        "#### Level 3: Sacred Weapon",
    ),
    (
        ("Paladin", "Paladin Subclass: Oath of Devotion", "Level 3: Sacred Weapon"),
        "When you take the Attack action, you can expend one use of your Channel Divinity to imbue one Melee weapon that you are holding with positive energy. For 10 minutes or until you use this feature again, you add your Charisma modifier to attack rolls you make with that weapon (minimum bonus of +1), and each time you hit with it, you cause it to deal its normal damage type or Radiant damage.",
    ),
    (
        ("Paladin", "Paladin Subclass: Oath of Devotion", "Level 3: Sacred Weapon"),
        "The weapon also emits Bright Light in a 20-foot radius and Dim Light 20 feet beyond that.",
    ),
    (
        ("Paladin", "Paladin Subclass: Oath of Devotion", "Level 3: Sacred Weapon"),
        "You can end this effect early (no action required). This effect also ends if you aren't carrying the weapon.",
    ),
    (
        ("Paladin", "Paladin Subclass: Oath of Devotion", "Level 7: Aura of Devotion"),
        "#### Level 7: Aura of Devotion",
    ),
    (
        ("Paladin", "Paladin Subclass: Oath of Devotion", "Level 7: Aura of Devotion"),
        "You and your allies have Immunity to the Charmed condition while in your Aura of Protection. If a Charmed ally enters the aura, that condition has no effect on that ally while there.",
    ),
    (
        (
            "Paladin",
            "Paladin Subclass: Oath of Devotion",
            "Level 15: Smite of Protection",
        ),
        "#### Level 15: Smite of Protection",
    ),
    (
        (
            "Paladin",
            "Paladin Subclass: Oath of Devotion",
            "Level 15: Smite of Protection",
        ),
        "Your magical smite now radiates protective energy. Whenever you cast _Divine Smite_, you and your allies have Half Cover while in your Aura of Protection. The aura has this benefit until the start of your next turn.",
    ),
    (
        ("Paladin", "Paladin Subclass: Oath of Devotion", "Level 20: Holy Nimbus"),
        "#### Level 20: Holy Nimbus",
    ),
    (
        ("Paladin", "Paladin Subclass: Oath of Devotion", "Level 20: Holy Nimbus"),
        "As a Bonus Action, you can imbue your Aura of Protection with holy power, granting the benefits below for 10 minutes or until you end them (no action required). Once you use this feature, you can't use it again until you finish a Long Rest. You can also restore your use of it by expending a level 5 spell slot (no action required).",
    ),
    (
        ("Paladin", "Paladin Subclass: Oath of Devotion", "Level 20: Holy Nimbus"),
        "_Holy Ward._ You have Advantage on any saving throw you are forced to make by a Fiend or an Undead.",
    ),
    (
        ("Paladin", "Paladin Subclass: Oath of Devotion", "Level 20: Holy Nimbus"),
        "_Radiant Damage._ Whenever an enemy starts its turn in the aura, that creature takes Radiant damage equal to your Charisma modifier plus your Proficiency Bonus.",
    ),
    (
        ("Paladin", "Paladin Subclass: Oath of Devotion", "Level 20: Holy Nimbus"),
        "_Sunlight._ The aura is filled with Bright Light that is sunlight.",
    ),
    (("Ranger",), "## Ranger"),
    (
        ("Ranger",),
        "**Core Ranger Traits**\n\n<table>\n  <tbody>\n    <tr>\n      <td>Primary Ability</td>\n      <td>Dexterity and Wisdom</td>\n    </tr>\n    <tr>\n      <td>Hit Point Die</td>\n      <td>D10 per Ranger level</td>\n    </tr>\n    <tr>\n      <td>Saving Throw Proficiencies</td>\n      <td>Strength and Dexterity</td>\n    </tr>\n    <tr>\n      <td>Skill Proficiencies</td>\n      <td>Choose 3: Animal Handling, Athletics, Insight, Investigation, Nature, Perception, Stealth, or Survival</td>\n    </tr>\n    <tr>\n      <td>Weapon Proficiencies</td>\n      <td>Simple and Martial weapons</td>\n    </tr>\n    <tr>\n      <td>Armor Training</td>\n      <td>Light and Medium armor and Shields</td>\n    </tr>\n    <tr>\n      <td>Starting Equipment</td>\n      <td>Choose A or B: (A) Studded Leather Armor, Scimitar, Shortsword, Longbow, 20 Arrows, Quiver, Druidic Focus (sprig of mistletoe), Explorer's Pack, and 7 GP; or (B) 150 GP</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (("Ranger", "Becoming a Ranger …"), "### Becoming a Ranger …"),
    (
        ("Ranger", "Becoming a Ranger …", "As a Level 1 Character"),
        "#### As a Level 1 Character",
    ),
    (
        ("Ranger", "Becoming a Ranger …", "As a Level 1 Character"),
        "- Gain all the traits in the Core Ranger Traits table.\n- Gain the Ranger's level 1 features, which are listed in the Ranger Features table.",
    ),
    (
        ("Ranger", "Becoming a Ranger …", "As a Multiclass Character"),
        "#### As a Multiclass Character",
    ),
    (
        ("Ranger", "Becoming a Ranger …", "As a Multiclass Character"),
        "- Gain the following traits from the Core Ranger Traits table: Hit Point Die, proficiency with Martial weapons, proficiency in one skill of your choice from the Ranger's skill list, and training with Light and Medium armor and Shields.\n- Gain the Ranger's level 1 features, which are listed in the Ranger Features table. See the multiclassing rules in \"Character Creation\" to determine your available spell slots.",
    ),
    (("Ranger", "Ranger Class Features"), "### Ranger Class Features"),
    (
        ("Ranger", "Ranger Class Features"),
        "As a Ranger, you gain the following class features when you reach the specified Ranger levels. These features are listed in the Ranger Features table.",
    ),
    (
        ("Ranger", "Ranger Class Features"),
        '**Ranger Features**\n\n<table>\n  <thead>\n    <tr>\n      <th>Level</th>\n      <th>Proficiency Bonus</th>\n      <th>Class Features</th>\n      <th>Favored Enemy</th>\n      <th>Prepared Spells</th>\n      <th colspan="5">——Spell Slots per Spell Level——</th>\n    </tr>\n    <tr>\n      <th>\n      </th>\n      <th>\n      </th>\n      <th>\n      </th>\n      <th>\n      </th>\n      <th>\n      </th>\n      <th>1</th>\n      <th>2</th>\n      <th>3</th>\n      <th>4</th>\n      <th>5</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>1</td>\n      <td>+2</td>\n      <td>Spellcasting, Favored Enemy, Weapon Mastery</td>\n      <td>2</td>\n      <td>2</td>\n      <td>2</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>2</td>\n      <td>+2</td>\n      <td>Deft Explorer, Fighting Style</td>\n      <td>2</td>\n      <td>3</td>\n      <td>2</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>3</td>\n      <td>+2</td>\n      <td>Ranger Subclass</td>\n      <td>2</td>\n      <td>4</td>\n      <td>3</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>4</td>\n      <td>+2</td>\n      <td>Ability Score Improvement</td>\n      <td>2</td>\n      <td>5</td>\n      <td>3</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>5</td>\n      <td>+3</td>\n      <td>Extra Attack</td>\n      <td>3</td>\n      <td>6</td>\n      <td>4</td>\n      <td>2</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>6</td>\n      <td>+3</td>\n      <td>Roving</td>\n      <td>3</td>\n      <td>6</td>\n      <td>4</td>\n      <td>2</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>7</td>\n      <td>+3</td>\n      <td>Subclass feature</td>\n      <td>3</td>\n      <td>7</td>\n      <td>4</td>\n      <td>3</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>8</td>\n      <td>+3</td>\n      <td>Ability Score Improvement</td>\n      <td>3</td>\n      <td>7</td>\n      <td>4</td>\n      <td>3</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>9</td>\n      <td>+4</td>\n      <td>Expertise</td>\n      <td>4</td>\n      <td>9</td>\n      <td>4</td>\n      <td>3</td>\n      <td>2</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>10</td>\n      <td>+4</td>\n      <td>Tireless</td>\n      <td>4</td>\n      <td>9</td>\n      <td>4</td>\n      <td>3</td>\n      <td>2</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>11</td>\n      <td>+4</td>\n      <td>Subclass feature</td>\n      <td>4</td>\n      <td>10</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>12</td>\n      <td>+4</td>\n      <td>Ability Score Improvement</td>\n      <td>4</td>\n      <td>10</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>13</td>\n      <td>+5</td>\n      <td>Relentless Hunter</td>\n      <td>5</td>\n      <td>11</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>1</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>14</td>\n      <td>+5</td>\n      <td>Nature’s Veil</td>\n      <td>5</td>\n      <td>11</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>1</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>15</td>\n      <td>+5</td>\n      <td>Subclass feature</td>\n      <td>5</td>\n      <td>12</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>2</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>16</td>\n      <td>+5</td>\n      <td>Ability Score Improvement</td>\n      <td>5</td>\n      <td>12</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>2</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>17</td>\n      <td>+6</td>\n      <td>Precise Hunter</td>\n      <td>6</td>\n      <td>14</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>3</td>\n      <td>1</td>\n    </tr>\n    <tr>\n      <td>18</td>\n      <td>+6</td>\n      <td>Feral Senses</td>\n      <td>6</td>\n      <td>14</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>3</td>\n      <td>1</td>\n    </tr>\n    <tr>\n      <td>19</td>\n      <td>+6</td>\n      <td>Epic Boon</td>\n      <td>6</td>\n      <td>15</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>3</td>\n      <td>2</td>\n    </tr>\n    <tr>\n      <td>20</td>\n      <td>+6</td>\n      <td>Foe Slayer</td>\n      <td>6</td>\n      <td>15</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>3</td>\n      <td>2</td>\n    </tr>\n  </tbody>\n</table>',
    ),
    (
        ("Ranger", "Ranger Class Features", "Level 1: Spellcasting"),
        "#### Level 1: Spellcasting",
    ),
    (
        ("Ranger", "Ranger Class Features", "Level 1: Spellcasting"),
        'You have learned to channel the magical essence of nature to cast spells. See "Spells" for the rules on spellcasting. The information below details how you use those rules with Ranger spells, which appear in the Ranger spell list later in the class\'s description.',
    ),
    (
        ("Ranger", "Ranger Class Features", "Level 1: Spellcasting"),
        "_Spell Slots._ The Ranger Features table shows how many spell slots you have to cast your level 1+ spells. You regain all expended slots when you finish a Long Rest.",
    ),
    (
        ("Ranger", "Ranger Class Features", "Level 1: Spellcasting"),
        "_Prepared Spells of Level 1+._ You prepare the list of level 1+ spells that are available for you to cast with this feature. To start, choose two level 1 Ranger spells. _Cure Wounds_ and _Ensnaring Strike_ are recommended.",
    ),
    (
        ("Ranger", "Ranger Class Features", "Level 1: Spellcasting"),
        "The number of spells on your list increases as you gain Ranger levels, as shown in the Prepared Spells column of the Ranger Features table. Whenever that number increases, choose additional Ranger spells until the number of spells on your list matches the number in the Ranger Features table. The chosen spells must be of a level for which you have spell slots. For example, if you're a level 5 Ranger, your list of prepared spells can include six Ranger spells of level 1 or 2 in any combination.",
    ),
    (
        ("Ranger", "Ranger Class Features", "Level 1: Spellcasting"),
        "If another Ranger feature gives you spells that you always have prepared, those spells don't count against the number of spells you can prepare with this feature, but those spells otherwise count as Ranger spells for you.",
    ),
    (
        ("Ranger", "Ranger Class Features", "Level 1: Spellcasting"),
        "_Changing Your Prepared Spells._ Whenever you finish a Long Rest, you can replace one spell on your list with another Ranger spell for which you have spell slots.",
    ),
    (
        ("Ranger", "Ranger Class Features", "Level 1: Spellcasting"),
        "_Spellcasting Ability._ Wisdom is your spellcasting ability for your Ranger spells.",
    ),
    (
        ("Ranger", "Ranger Class Features", "Level 1: Spellcasting"),
        "_Spellcasting Focus._ You can use a Druidic Focus as a Spellcasting Focus for your Ranger spells.",
    ),
    (
        ("Ranger", "Ranger Class Features", "Level 1: Favored Enemy"),
        "#### Level 1: Favored Enemy",
    ),
    (
        ("Ranger", "Ranger Class Features", "Level 1: Favored Enemy"),
        "You always have the _Hunter's Mark_ spell prepared. You can cast it twice without expending a spell slot, and you regain all expended uses of this ability when you finish a Long Rest.",
    ),
    (
        ("Ranger", "Ranger Class Features", "Level 1: Favored Enemy"),
        "The number of times you can cast the spell without a spell slot increases when you reach certain Ranger levels, as shown in the Favored Enemy column of the Ranger Features table.",
    ),
    (
        ("Ranger", "Ranger Class Features", "Level 1: Weapon Mastery"),
        "#### Level 1: Weapon Mastery",
    ),
    (
        ("Ranger", "Ranger Class Features", "Level 1: Weapon Mastery"),
        "Your training with weapons allows you to use the mastery properties of two kinds of weapons of your\nchoice with which you have proficiency, such as Longbows and Shortswords.",
    ),
    (
        ("Ranger", "Ranger Class Features", "Level 1: Weapon Mastery"),
        "Whenever you finish a Long Rest, you can change the kinds of weapons you chose. For example, you could switch to using the mastery properties of Scimitars and Longswords.",
    ),
    (
        ("Ranger", "Ranger Class Features", "Level 2: Deft Explorer"),
        "#### Level 2: Deft Explorer",
    ),
    (
        ("Ranger", "Ranger Class Features", "Level 2: Deft Explorer"),
        "Thanks to your travels, you gain the following benefits.",
    ),
    (
        ("Ranger", "Ranger Class Features", "Level 2: Deft Explorer"),
        "_Expertise._ Choose one of your skill proficiencies with which you lack Expertise. You gain Expertise in that skill.",
    ),
    (
        ("Ranger", "Ranger Class Features", "Level 2: Deft Explorer"),
        '_Languages._ You know two languages of your choice from the language tables in "Character Creation."',
    ),
    (
        ("Ranger", "Ranger Class Features", "Level 2: Fighting Style"),
        "#### Level 2: Fighting Style",
    ),
    (
        ("Ranger", "Ranger Class Features", "Level 2: Fighting Style"),
        'You gain a Fighting Style feat of your choice (see "Feats"). Instead of choosing one of those feats, you can choose the option below.',
    ),
    (
        ("Ranger", "Ranger Class Features", "Level 2: Fighting Style"),
        "_Druidic Warrior._ You learn two Druid cantrips of your choice (see the Druid class's section for a list of Druid spells). _Guidance_ and _Starry Wisp_ are recommended. The chosen cantrips count as Ranger spells for you, and Wisdom is your spellcasting ability for them. Whenever you gain a Ranger level, you can replace one of these cantrips with another Druid cantrip.",
    ),
    (
        ("Ranger", "Ranger Class Features", "Level 3: Ranger Subclass"),
        "#### Level 3: Ranger Subclass",
    ),
    (
        ("Ranger", "Ranger Class Features", "Level 3: Ranger Subclass"),
        "You gain a Ranger subclass of your choice. The Hunter subclass is detailed after this class's description. A subclass is a specialization that grants you features at certain Ranger levels. For the rest of your career, you gain each of your subclass's features that are of your Ranger level or lower.",
    ),
    (
        ("Ranger", "Ranger Class Features", "Level 4: Ability Score Improvement"),
        "#### Level 4: Ability Score Improvement",
    ),
    (
        ("Ranger", "Ranger Class Features", "Level 4: Ability Score Improvement"),
        'You gain the Ability Score Improvement feat (see "Feats") or another feat of your choice for which you qualify. You gain this feature again at Ranger levels 8, 12, and 16.',
    ),
    (
        ("Ranger", "Ranger Class Features", "Level 5: Extra Attack"),
        "#### Level 5: Extra Attack",
    ),
    (
        ("Ranger", "Ranger Class Features", "Level 5: Extra Attack"),
        "You can attack twice instead of once whenever you take the Attack action on your turn.",
    ),
    (("Ranger", "Ranger Class Features", "Level 6: Roving"), "#### Level 6: Roving"),
    (
        ("Ranger", "Ranger Class Features", "Level 6: Roving"),
        "Your Speed increases by 10 feet while you aren't wearing Heavy armor. You also have a Climb Speed and a Swim Speed equal to your Speed.",
    ),
    (
        ("Ranger", "Ranger Class Features", "Level 9: Expertise"),
        "#### Level 9: Expertise",
    ),
    (
        ("Ranger", "Ranger Class Features", "Level 9: Expertise"),
        "Choose two of your skill proficiencies with which you lack Expertise. You gain Expertise in those skills.",
    ),
    (
        ("Ranger", "Ranger Class Features", "Level 10: Tireless"),
        "#### Level 10: Tireless",
    ),
    (
        ("Ranger", "Ranger Class Features", "Level 10: Tireless"),
        "Primal forces now help fuel you on your journeys, granting you the following benefits.",
    ),
    (
        ("Ranger", "Ranger Class Features", "Level 10: Tireless"),
        "_Temporary Hit Points._ As a Magic action, you can give yourself a number of Temporary Hit Points equal to 1d8 plus your Wisdom modifier (minimum of 1). You can use this action a number of times equal to your Wisdom modifier (minimum of once), and you regain all expended uses when you finish a Long Rest.",
    ),
    (
        ("Ranger", "Ranger Class Features", "Level 10: Tireless"),
        "_Decrease Exhaustion._ Whenever you finish a Short Rest, your Exhaustion level, if any, decreases by 1.",
    ),
    (
        ("Ranger", "Ranger Class Features", "Level 13: Relentless Hunter"),
        "#### Level 13: Relentless Hunter",
    ),
    (
        ("Ranger", "Ranger Class Features", "Level 13: Relentless Hunter"),
        "Taking damage can't break your Concentration on _Hunter's Mark_.",
    ),
    (
        ("Ranger", "Ranger Class Features", "Level 14: Nature's Veil"),
        "#### Level 14: Nature's Veil",
    ),
    (
        ("Ranger", "Ranger Class Features", "Level 14: Nature's Veil"),
        "You invoke spirits of nature to magically hide yourself. As a Bonus Action, you can give yourself the Invisible condition until the end of your next turn. You can use this feature a number of times equal to your Wisdom modifier (minimum of once), and you regain all expended uses when you finish a Long Rest.",
    ),
    (
        ("Ranger", "Ranger Class Features", "Level 17: Precise Hunter"),
        "#### Level 17: Precise Hunter",
    ),
    (
        ("Ranger", "Ranger Class Features", "Level 17: Precise Hunter"),
        "You have Advantage on attack rolls against the creature currently marked by your _Hunter's Mark_.",
    ),
    (
        ("Ranger", "Ranger Class Features", "Level 18: Feral Senses"),
        "#### Level 18: Feral Senses",
    ),
    (
        ("Ranger", "Ranger Class Features", "Level 18: Feral Senses"),
        "Your connection to the forces of nature grants you Blindsight with a range of 30 feet.",
    ),
    (
        ("Ranger", "Ranger Class Features", "Level 19: Epic Boon"),
        "#### Level 19: Epic Boon",
    ),
    (
        ("Ranger", "Ranger Class Features", "Level 19: Epic Boon"),
        'You gain an Epic Boon feat (see "Feats") or another feat of your choice for which you qualify. Boon of Dimensional Travel is recommended.',
    ),
    (
        ("Ranger", "Ranger Class Features", "Level 20: Foe Slayer"),
        "#### Level 20: Foe Slayer",
    ),
    (
        ("Ranger", "Ranger Class Features", "Level 20: Foe Slayer"),
        "The damage die of your _Hunter's Mark_ is a d10 rather than a d6.",
    ),
    (("Ranger", "Ranger Spell List"), "### Ranger Spell List"),
    (
        ("Ranger", "Ranger Spell List"),
        "This section presents the Ranger spell list. The spells are organized by spell level and then alphabetized, and each spell's school of magic is listed. In the Special column, _C_ means the spell requires Concentration, _R_ means it's a Ritual, and _M_ means it requires a specific Material component.",
    ),
    (
        ("Ranger", "Ranger Spell List", "Level 1 Ranger Spells"),
        "#### Level 1 Ranger Spells",
    ),
    (
        ("Ranger", "Ranger Spell List", "Level 1 Ranger Spells"),
        "<table>\n  <thead>\n    <tr>\n      <th>Spell</th>\n      <th>School</th>\n      <th>Special</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>Alarm</td>\n      <td>Abjuration</td>\n      <td>R</td>\n    </tr>\n    <tr>\n      <td>Animal Friendship</td>\n      <td>Enchantment</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Cure Wounds</td>\n      <td>Abjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Detect Magic</td>\n      <td>Divination</td>\n      <td>C, R</td>\n    </tr>\n    <tr>\n      <td>Detect Poison and Disease</td>\n      <td>Divination</td>\n      <td>C, R</td>\n    </tr>\n    <tr>\n      <td>Ensnaring Strike</td>\n      <td>Conjuration</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Entangle</td>\n      <td>Conjuration</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Fog Cloud</td>\n      <td>Conjuration</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Goodberry</td>\n      <td>Conjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Hunter's Mark</td>\n      <td>Divination</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Jump</td>\n      <td>Transmutation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Longstrider</td>\n      <td>Transmutation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Speak with Animals</td>\n      <td>Divination</td>\n      <td>R</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        ("Ranger", "Ranger Spell List", "Level 2 Ranger Spells"),
        "#### Level 2 Ranger Spells",
    ),
    (
        ("Ranger", "Ranger Spell List", "Level 2 Ranger Spells"),
        "<table>\n  <thead>\n    <tr>\n      <th>Spell</th>\n      <th>School</th>\n      <th>Special</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>Aid</td>\n      <td>Abjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Animal Messenger</td>\n      <td>Enchantment</td>\n      <td>R</td>\n    </tr>\n    <tr>\n      <td>Barkskin</td>\n      <td>Transmutation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Darkvision</td>\n      <td>Transmutation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Enhance Ability</td>\n      <td>Transmutation</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Find Traps</td>\n      <td>Divination</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Gust of Wind</td>\n      <td>Evocation</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Lesser Restoration</td>\n      <td>Abjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Locate Animals or Plants</td>\n      <td>Divination</td>\n      <td>R</td>\n    </tr>\n    <tr>\n      <td>Locate Object</td>\n      <td>Divination</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Magic Weapon</td>\n      <td>Transmutation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Pass without Trace</td>\n      <td>Abjuration</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Protection from Poison</td>\n      <td>Abjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Silence</td>\n      <td>Illusion</td>\n      <td>C, R</td>\n    </tr>\n    <tr>\n      <td>Spike Growth</td>\n      <td>Transmutation</td>\n      <td>C</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        ("Ranger", "Ranger Spell List", "Level 3 Ranger Spells"),
        "#### Level 3 Ranger Spells",
    ),
    (
        ("Ranger", "Ranger Spell List", "Level 3 Ranger Spells"),
        "<table>\n  <thead>\n    <tr>\n      <th>Spell</th>\n      <th>School</th>\n      <th>Special</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>Conjure Animals</td>\n      <td>Conjuration</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Daylight</td>\n      <td>Evocation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Dispel Magic</td>\n      <td>Abjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Meld into Stone</td>\n      <td>Transmutation</td>\n      <td>R</td>\n    </tr>\n    <tr>\n      <td>Nondetection</td>\n      <td>Abjuration</td>\n      <td>M</td>\n    </tr>\n    <tr>\n      <td>Plant Growth</td>\n      <td>Transmutation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Protection from Energy</td>\n      <td>Abjuration</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Revivify</td>\n      <td>Necromancy</td>\n      <td>M</td>\n    </tr>\n    <tr>\n      <td>Speak with Plants</td>\n      <td>Transmutation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Water Breathing</td>\n      <td>Transmutation</td>\n      <td>R</td>\n    </tr>\n    <tr>\n      <td>Water Walk</td>\n      <td>Transmutation</td>\n      <td>R</td>\n    </tr>\n    <tr>\n      <td>Wind Wall</td>\n      <td>Evocation</td>\n      <td>C</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        ("Ranger", "Ranger Spell List", "Level 4 Ranger Spells"),
        "#### Level 4 Ranger Spells",
    ),
    (
        ("Ranger", "Ranger Spell List", "Level 4 Ranger Spells"),
        "<table>\n  <thead>\n    <tr>\n      <th>Spell</th>\n      <th>School</th>\n      <th>Special</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>Conjure Woodland Beings</td>\n      <td>Conjuration</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Dominate Beast</td>\n      <td>Enchantment</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Freedom of Movement</td>\n      <td>Abjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Locate Creature</td>\n      <td>Divination</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Stoneskin</td>\n      <td>Transmutation</td>\n      <td>C, M</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        ("Ranger", "Ranger Spell List", "Level 5 Ranger Spells"),
        "#### Level 5 Ranger Spells",
    ),
    (
        ("Ranger", "Ranger Spell List", "Level 5 Ranger Spells"),
        "<table>\n  <thead>\n    <tr>\n      <th>Spell</th>\n      <th>School</th>\n      <th>Special</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>Commune with Nature</td>\n      <td>Divination</td>\n      <td>R</td>\n    </tr>\n    <tr>\n      <td>Greater Restoration</td>\n      <td>Abjuration</td>\n      <td>M</td>\n    </tr>\n    <tr>\n      <td>Tree Stride</td>\n      <td>Conjuration</td>\n      <td>C</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (("Ranger", "Ranger Subclass: Hunter"), "### Ranger Subclass: Hunter"),
    (
        ("Ranger", "Ranger Subclass: Hunter"),
        "_Protect Nature and People from Destruction_",
    ),
    (
        ("Ranger", "Ranger Subclass: Hunter"),
        "You stalk prey in the wilds and elsewhere, using your abilities as a Hunter to protect nature and people everywhere from forces that would destroy them.",
    ),
    (
        ("Ranger", "Ranger Subclass: Hunter", "Level 3: Hunter's Lore"),
        "#### Level 3: Hunter's Lore",
    ),
    (
        ("Ranger", "Ranger Subclass: Hunter", "Level 3: Hunter's Lore"),
        "You can call on the forces of nature to reveal certain strengths and weaknesses of your prey. While a creature is marked by your _Hunter's Mark_, you know whether that creature has any Immunities, Resistances, or Vulnerabilities, and if the creature has any, you know what they are.",
    ),
    (
        ("Ranger", "Ranger Subclass: Hunter", "Level 3: Hunter's Prey"),
        "#### Level 3: Hunter's Prey",
    ),
    (
        ("Ranger", "Ranger Subclass: Hunter", "Level 3: Hunter's Prey"),
        "You gain one of the following feature options of your choice. Whenever you finish a Short or Long Rest, you can replace the chosen option with the other one.",
    ),
    (
        ("Ranger", "Ranger Subclass: Hunter", "Level 3: Hunter's Prey"),
        "_Colossus Slayer._ Your tenacity can wear down even the most resilient foes. When you hit a creature with a weapon, the weapon deals an extra 1d8 damage to the target if it's missing any of its Hit Points. You can deal this extra damage only once per turn.",
    ),
    (
        ("Ranger", "Ranger Subclass: Hunter", "Level 3: Hunter's Prey"),
        "_Horde Breaker._ Once on each of your turns when you make an attack with a weapon, you can make another attack with the same weapon against a different creature that is within 5 feet of the original target, that is within the weapon's range, and that you haven't attacked this turn.",
    ),
    (
        ("Ranger", "Ranger Subclass: Hunter", "Level 7: Defensive Tactics"),
        "#### Level 7: Defensive Tactics",
    ),
    (
        ("Ranger", "Ranger Subclass: Hunter", "Level 7: Defensive Tactics"),
        "You gain one of the following feature options of your choice. Whenever you finish a Short or Long Rest, you can replace the chosen option with the other one.",
    ),
    (
        ("Ranger", "Ranger Subclass: Hunter", "Level 7: Defensive Tactics"),
        "_Escape the Horde._ Opportunity Attacks have Disadvantage against you.",
    ),
    (
        ("Ranger", "Ranger Subclass: Hunter", "Level 7: Defensive Tactics"),
        "_Multiattack Defense._ When a creature hits you with an attack roll, that creature has Disadvantage on all other attack rolls against you this turn.",
    ),
    (
        ("Ranger", "Ranger Subclass: Hunter", "Level 11: Superior Hunter's Prey"),
        "#### Level 11: Superior Hunter's Prey",
    ),
    (
        ("Ranger", "Ranger Subclass: Hunter", "Level 11: Superior Hunter's Prey"),
        "Once per turn when you deal damage to a creature marked by your _Hunter's Mark_, you can also deal that spell's extra damage to a different creature that you can see within 30 feet of the first creature.",
    ),
    (
        ("Ranger", "Ranger Subclass: Hunter", "Level 15: Superior Hunter's Defense"),
        "#### Level 15: Superior Hunter's Defense",
    ),
    (
        ("Ranger", "Ranger Subclass: Hunter", "Level 15: Superior Hunter's Defense"),
        "When you take damage, you can take a Reaction to give yourself Resistance to that damage and any other damage of the same type until the end of the current turn.",
    ),
    (("Rogue",), "## Rogue"),
    (
        ("Rogue",),
        "**Core Rogue Traits**\n\n<table>\n  <tbody>\n    <tr>\n      <td>Primary Ability</td>\n      <td>Dexterity</td>\n    </tr>\n    <tr>\n      <td>Hit Point Die</td>\n      <td>D8 per Rogue level</td>\n    </tr>\n    <tr>\n      <td>Saving Throw Proficiencies</td>\n      <td>Dexterity and Intelligence</td>\n    </tr>\n    <tr>\n      <td>Skill Proficiencies</td>\n      <td>Choose 4: Acrobatics, Athletics, Deception, Insight, Intimidation, Investigation, Perception, Persuasion, Sleight of Hand, or Stealth</td>\n    </tr>\n    <tr>\n      <td>Weapon Proficiencies</td>\n      <td>Simple weapons and Martial weapons that have the Finesse or Light property</td>\n    </tr>\n    <tr>\n      <td>Tool Proficiencies</td>\n      <td>Thieves' Tools</td>\n    </tr>\n    <tr>\n      <td>Armor Training</td>\n      <td>Light armor</td>\n    </tr>\n    <tr>\n      <td>Starting Equipment</td>\n      <td>Choose A or B: (A) Leather Armor, 2 Daggers, Shortsword, Shortbow, 20 Arrows, Quiver, Thieves' Tools, Burglar's Pack, and 8 GP; or (B) 100 GP</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (("Rogue", "Becoming a Rogue …"), "### Becoming a Rogue …"),
    (
        ("Rogue", "Becoming a Rogue …", "As a Level 1 Character"),
        "#### As a Level 1 Character",
    ),
    (
        ("Rogue", "Becoming a Rogue …", "As a Level 1 Character"),
        "- Gain all the traits in the Core Rogue Traits table.\n- Gain the Rogue's level 1 features, which are listed in the Rogue Features table.",
    ),
    (
        ("Rogue", "Becoming a Rogue …", "As a Multiclass Character"),
        "#### As a Multiclass Character",
    ),
    (
        ("Rogue", "Becoming a Rogue …", "As a Multiclass Character"),
        "- Gain the following traits from the Core Rogue Traits table: Hit Point Die, proficiency in one skill of your choice from the Rogue's skill list, proficiency with Thieves' Tools, and training with Light armor.\n- Gain the Rogue's level 1 features, which are listed in the Rogue Features table.",
    ),
    (("Rogue", "Rogue Class Features"), "### Rogue Class Features"),
    (
        ("Rogue", "Rogue Class Features"),
        "As a Rogue, you gain the following class features when you reach the specified Rogue levels. These features are listed in the Rogue Features table.",
    ),
    (
        ("Rogue", "Rogue Class Features"),
        "**Rogue Features**\n\n<table>\n  <thead>\n    <tr>\n      <th>Level</th>\n      <th>Proficiency Bonus</th>\n      <th>Class Features</th>\n      <th>Sneak Attack</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>1</td>\n      <td>+2</td>\n      <td>Expertise, Sneak Attack, Thieves' Cant, Weapon Mastery</td>\n      <td>1d6</td>\n    </tr>\n    <tr>\n      <td>2</td>\n      <td>+2</td>\n      <td>Cunning Action</td>\n      <td>1d6</td>\n    </tr>\n    <tr>\n      <td>3</td>\n      <td>+2</td>\n      <td>Rogue Subclass, Steady Aim</td>\n      <td>2d6</td>\n    </tr>\n    <tr>\n      <td>4</td>\n      <td>+2</td>\n      <td>Ability Score Improvement</td>\n      <td>2d6</td>\n    </tr>\n    <tr>\n      <td>5</td>\n      <td>+3</td>\n      <td>Cunning Strike, Uncanny Dodge</td>\n      <td>3d6</td>\n    </tr>\n    <tr>\n      <td>6</td>\n      <td>+3</td>\n      <td>Expertise</td>\n      <td>3d6</td>\n    </tr>\n    <tr>\n      <td>7</td>\n      <td>+3</td>\n      <td>Evasion, Reliable Talent</td>\n      <td>4d6</td>\n    </tr>\n    <tr>\n      <td>8</td>\n      <td>+3</td>\n      <td>Ability Score Improvement</td>\n      <td>4d6</td>\n    </tr>\n    <tr>\n      <td>9</td>\n      <td>+4</td>\n      <td>Subclass feature</td>\n      <td>5d6</td>\n    </tr>\n    <tr>\n      <td>10</td>\n      <td>+4</td>\n      <td>Ability Score Improvement</td>\n      <td>5d6</td>\n    </tr>\n    <tr>\n      <td>11</td>\n      <td>+4</td>\n      <td>Improved Cunning Strike</td>\n      <td>6d6</td>\n    </tr>\n    <tr>\n      <td>12</td>\n      <td>+4</td>\n      <td>Ability Score Improvement</td>\n      <td>6d6</td>\n    </tr>\n    <tr>\n      <td>13</td>\n      <td>+5</td>\n      <td>Subclass feature</td>\n      <td>7d6</td>\n    </tr>\n    <tr>\n      <td>14</td>\n      <td>+5</td>\n      <td>Devious Strikes</td>\n      <td>7d6</td>\n    </tr>\n    <tr>\n      <td>15</td>\n      <td>+5</td>\n      <td>Slippery Mind</td>\n      <td>8d6</td>\n    </tr>\n    <tr>\n      <td>16</td>\n      <td>+5</td>\n      <td>Ability Score Improvement</td>\n      <td>8d6</td>\n    </tr>\n    <tr>\n      <td>17</td>\n      <td>+6</td>\n      <td>Subclass feature</td>\n      <td>9d6</td>\n    </tr>\n    <tr>\n      <td>18</td>\n      <td>+6</td>\n      <td>Elusive</td>\n      <td>9d6</td>\n    </tr>\n    <tr>\n      <td>19</td>\n      <td>+6</td>\n      <td>Epic Boon</td>\n      <td>10d6</td>\n    </tr>\n    <tr>\n      <td>20</td>\n      <td>+6</td>\n      <td>Stroke of Luck</td>\n      <td>10d6</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        ("Rogue", "Rogue Class Features", "Level 1: Expertise"),
        "#### Level 1: Expertise",
    ),
    (
        ("Rogue", "Rogue Class Features", "Level 1: Expertise"),
        "You gain Expertise in two of your skill proficiencies of your choice. Sleight of Hand and Stealth are recommended if you have proficiency in them.",
    ),
    (
        ("Rogue", "Rogue Class Features", "Level 1: Expertise"),
        "At Rogue level 6, you gain Expertise in two more of your skill proficiencies of your choice.",
    ),
    (
        ("Rogue", "Rogue Class Features", "Level 1: Sneak Attack"),
        "#### Level 1: Sneak Attack",
    ),
    (
        ("Rogue", "Rogue Class Features", "Level 1: Sneak Attack"),
        "You know how to strike subtly and exploit a foe's distraction. Once per turn, you can deal an extra 1d6 damage to one creature you hit with an attack roll if you have Advantage on the roll and the attack uses a Finesse or a Ranged weapon. The extra damage's type is the same as the weapon's type.",
    ),
    (
        ("Rogue", "Rogue Class Features", "Level 1: Sneak Attack"),
        "You don't need Advantage on the attack roll if at least one of your allies is within 5 feet of the target, the ally doesn't have the Incapacitated condition, and you don't have Disadvantage on the attack roll. The extra damage increases as you gain Rogue levels, as shown in the Sneak Attack column of the Rogue Features table.",
    ),
    (
        ("Rogue", "Rogue Class Features", "Level 1: Thieves' Cant"),
        "#### Level 1: Thieves' Cant",
    ),
    (
        ("Rogue", "Rogue Class Features", "Level 1: Thieves' Cant"),
        'You picked up various languages in the communities where you plied your roguish talents. You know Thieves\' Cant and one other language of your choice, which you choose from the language tables in "Character Creation."',
    ),
    (
        ("Rogue", "Rogue Class Features", "Level 1: Weapon Mastery"),
        "#### Level 1: Weapon Mastery",
    ),
    (
        ("Rogue", "Rogue Class Features", "Level 1: Weapon Mastery"),
        "Your training with weapons allows you to use the mastery properties of two kinds of weapons of your choice with which you have proficiency, such as Daggers and Shortbows.",
    ),
    (
        ("Rogue", "Rogue Class Features", "Level 1: Weapon Mastery"),
        "Whenever you finish a Long Rest, you can change the kinds of weapons you chose. For example, you could switch to using the mastery properties of Scimitars and Shortswords.",
    ),
    (
        ("Rogue", "Rogue Class Features", "Level 2: Cunning Action"),
        "#### Level 2: Cunning Action",
    ),
    (
        ("Rogue", "Rogue Class Features", "Level 2: Cunning Action"),
        "Your quick thinking and agility allow you to move and act quickly. On your turn, you can take one of the following actions as a Bonus Action: Dash, Disengage, or Hide.",
    ),
    (
        ("Rogue", "Rogue Class Features", "Level 3: Rogue Subclass"),
        "#### Level 3: Rogue Subclass",
    ),
    (
        ("Rogue", "Rogue Class Features", "Level 3: Rogue Subclass"),
        "You gain a Rogue subclass of your choice. The Thief subclass is detailed after this class's description. A subclass is a specialization that grants you features at certain Rogue levels. For the rest of your career, you gain each of your subclass's features that are of your Rogue level or lower.",
    ),
    (
        ("Rogue", "Rogue Class Features", "Level 3: Steady Aim"),
        "#### Level 3: Steady Aim",
    ),
    (
        ("Rogue", "Rogue Class Features", "Level 3: Steady Aim"),
        "As a Bonus Action, you give yourself Advantage on your next attack roll on the current turn. You can use this feature only if you haven't moved during this turn, and after you use it, your Speed is 0 until the end of the current turn.",
    ),
    (
        ("Rogue", "Rogue Class Features", "Level 4: Ability Score Improvement"),
        "#### Level 4: Ability Score Improvement",
    ),
    (
        ("Rogue", "Rogue Class Features", "Level 4: Ability Score Improvement"),
        'You gain the Ability Score Improvement feat (see "Feats") or another feat of your choice for which you qualify. You gain this feature again at Rogue levels 8, 10, 12, and 16.',
    ),
    (
        ("Rogue", "Rogue Class Features", "Level 5: Cunning Strike"),
        "#### Level 5: Cunning Strike",
    ),
    (
        ("Rogue", "Rogue Class Features", "Level 5: Cunning Strike"),
        "You've developed cunning ways to use your Sneak Attack. When you deal Sneak Attack damage, you can add one of the following Cunning Strike effects. Each effect has a die cost, which is the number of Sneak Attack damage dice you must forgo to add the effect. You remove the die before rolling, and the effect occurs immediately after the attack's damage is dealt. For example, if you add the Poison effect, remove 1d6 from the Sneak Attack's damage before rolling.",
    ),
    (
        ("Rogue", "Rogue Class Features", "Level 5: Cunning Strike"),
        "If a Cunning Strike effect requires a saving throw, the DC equals 8 plus your Dexterity modifier and Proficiency Bonus.",
    ),
    (
        ("Rogue", "Rogue Class Features", "Level 5: Cunning Strike"),
        "_Poison (Cost: 1d6)._ You add a toxin to your strike, forcing the target to make a Constitution saving throw. On a failed save, the target has the Poisoned condition for 1 minute. At the end of each of its turns, the Poisoned target repeats the save, ending the effect on itself on a success.",
    ),
    (
        ("Rogue", "Rogue Class Features", "Level 5: Cunning Strike"),
        "To use this effect, you must have a Poisoner's Kit on your person.",
    ),
    (
        ("Rogue", "Rogue Class Features", "Level 5: Cunning Strike"),
        "_Trip (Cost: 1d6)._ If the target is Large or smaller, it must succeed on a Dexterity saving throw or have the Prone condition.",
    ),
    (
        ("Rogue", "Rogue Class Features", "Level 5: Cunning Strike"),
        "_Withdraw (Cost: 1d6)._ Immediately after the attack, you move up to half your Speed without provoking Opportunity Attacks.",
    ),
    (
        ("Rogue", "Rogue Class Features", "Level 5: Uncanny Dodge"),
        "#### Level 5: Uncanny Dodge",
    ),
    (
        ("Rogue", "Rogue Class Features", "Level 5: Uncanny Dodge"),
        "When an attacker that you can see hits you with an attack roll, you can take a Reaction to halve the attack's damage against you (round down).",
    ),
    (("Rogue", "Rogue Class Features", "Level 7: Evasion"), "#### Level 7: Evasion"),
    (
        ("Rogue", "Rogue Class Features", "Level 7: Evasion"),
        "You can nimbly dodge out of the way of certain dangers. When you're subjected to an effect that allows you to make a Dexterity saving throw to take only half damage, you instead take no damage if you succeed on the saving throw and only half damage if you fail. You can't use this feature if you have the Incapacitated condition.",
    ),
    (
        ("Rogue", "Rogue Class Features", "Level 7: Reliable Talent"),
        "#### Level 7: Reliable Talent",
    ),
    (
        ("Rogue", "Rogue Class Features", "Level 7: Reliable Talent"),
        "Whenever you make an ability check that uses one of your skill or tool proficiencies, you can treat a d20 roll of 9 or lower as a 10.",
    ),
    (
        ("Rogue", "Rogue Class Features", "Level 11: Improved Cunning Strike"),
        "#### Level 11: Improved Cunning Strike",
    ),
    (
        ("Rogue", "Rogue Class Features", "Level 11: Improved Cunning Strike"),
        "You can use up to two Cunning Strike effects when you deal Sneak Attack damage, paying the die cost for each effect.",
    ),
    (
        ("Rogue", "Rogue Class Features", "Level 14: Devious Strikes"),
        "#### Level 14: Devious Strikes",
    ),
    (
        ("Rogue", "Rogue Class Features", "Level 14: Devious Strikes"),
        "You've practiced new ways to use your Sneak Attack deviously. The following effects are now among your Cunning Strike options.",
    ),
    (
        ("Rogue", "Rogue Class Features", "Level 14: Devious Strikes"),
        "_Daze (Cost: 2d6)._ The target must succeed on a Constitution saving throw, or on its next turn, it can do only one of the following: move or take an action or a Bonus Action.",
    ),
    (
        ("Rogue", "Rogue Class Features", "Level 14: Devious Strikes"),
        "_Knock Out (Cost: 6d6)._ The target must succeed on a Constitution saving throw, or it has the Unconscious condition for 1 minute or until it takes any damage. The Unconscious target repeats the save at the end of each of its turns, ending the effect on itself on a success.",
    ),
    (
        ("Rogue", "Rogue Class Features", "Level 14: Devious Strikes"),
        "_Obscure (Cost: 3d6)._ The target must succeed on a Dexterity saving throw, or it has the Blinded condition until the end of its next turn.",
    ),
    (
        ("Rogue", "Rogue Class Features", "Level 15: Slippery Mind"),
        "#### Level 15: Slippery Mind",
    ),
    (
        ("Rogue", "Rogue Class Features", "Level 15: Slippery Mind"),
        "Your cunning mind is exceptionally difficult to control. You gain proficiency in Wisdom and Charisma saving throws.",
    ),
    (("Rogue", "Rogue Class Features", "Level 18: Elusive"), "#### Level 18: Elusive"),
    (
        ("Rogue", "Rogue Class Features", "Level 18: Elusive"),
        "You're so evasive that attackers rarely gain the upper hand against you. No attack roll can have Advantage against you unless you have the Incapacitated condition.",
    ),
    (
        ("Rogue", "Rogue Class Features", "Level 19: Epic Boon"),
        "#### Level 19: Epic Boon",
    ),
    (
        ("Rogue", "Rogue Class Features", "Level 19: Epic Boon"),
        'You gain an Epic Boon feat (see "Feats") or another feat of your choice for which you qualify. Boon of the Night Spirit is recommended.',
    ),
    (
        ("Rogue", "Rogue Class Features", "Level 20: Stroke of Luck"),
        "#### Level 20: Stroke of Luck",
    ),
    (
        ("Rogue", "Rogue Class Features", "Level 20: Stroke of Luck"),
        "You have a marvelous knack for succeeding when you need to. If you fail a D20 Test, you can turn the roll into a 20.",
    ),
    (
        ("Rogue", "Rogue Class Features", "Level 20: Stroke of Luck"),
        "Once you use this feature, you can't use it again until you finish a Short or Long Rest.",
    ),
    (("Rogue", "Rogue Subclass: Thief"), "### Rogue Subclass: Thief"),
    (("Rogue", "Rogue Subclass: Thief"), "_Hunt for Treasure as a Classic Adventurer_"),
    (
        ("Rogue", "Rogue Subclass: Thief"),
        "A mix of burglar, treasure hunter, and explorer, you are the epitome of an adventurer. In addition to improving your agility and stealth, you gain abilities useful for delving into ruins and getting maximum benefit from the magic items you find there.",
    ),
    (
        ("Rogue", "Rogue Subclass: Thief", "Level 3: Fast Hands"),
        "#### Level 3: Fast Hands",
    ),
    (
        ("Rogue", "Rogue Subclass: Thief", "Level 3: Fast Hands"),
        "As a Bonus Action, you can do one of the following.",
    ),
    (
        ("Rogue", "Rogue Subclass: Thief", "Level 3: Fast Hands"),
        "_Sleight of Hand._ Make a Dexterity (Sleight of Hand) check to pick a lock or disarm a trap with Thieves' Tools or to pick a pocket.",
    ),
    (
        ("Rogue", "Rogue Subclass: Thief", "Level 3: Fast Hands"),
        "_Use an Object._ Take the Utilize action, or take the Magic action to use a magic item that requires that action.",
    ),
    (
        ("Rogue", "Rogue Subclass: Thief", "Level 3: Second-Story Work"),
        "#### Level 3: Second-Story Work",
    ),
    (
        ("Rogue", "Rogue Subclass: Thief", "Level 3: Second-Story Work"),
        "You've trained to get into especially hard-to-reach places, granting you these benefits.",
    ),
    (
        ("Rogue", "Rogue Subclass: Thief", "Level 3: Second-Story Work"),
        "_Climber._ You gain a Climb Speed equal to your Speed.",
    ),
    (
        ("Rogue", "Rogue Subclass: Thief", "Level 3: Second-Story Work"),
        "_Jumper._ You can determine your jump distance using your Dexterity rather than your Strength.",
    ),
    (
        ("Rogue", "Rogue Subclass: Thief", "Level 9: Supreme Sneak"),
        "#### Level 9: Supreme Sneak",
    ),
    (
        ("Rogue", "Rogue Subclass: Thief", "Level 9: Supreme Sneak"),
        "You gain the following Cunning Strike option.",
    ),
    (
        ("Rogue", "Rogue Subclass: Thief", "Level 9: Supreme Sneak"),
        "_Stealth Attack (Cost: 1d6)._ If you have the Hide action's Invisible condition, this attack doesn't end that condition on you if you end the turn behind Three-Quarters Cover or Total Cover.",
    ),
    (
        ("Rogue", "Rogue Subclass: Thief", "Level 13: Use Magic Device"),
        "#### Level 13: Use Magic Device",
    ),
    (
        ("Rogue", "Rogue Subclass: Thief", "Level 13: Use Magic Device"),
        "You've learned how to maximize use of magic items, granting you the following benefits.",
    ),
    (
        ("Rogue", "Rogue Subclass: Thief", "Level 13: Use Magic Device"),
        "_Attunement._ You can attune to up to four magic items at once.",
    ),
    (
        ("Rogue", "Rogue Subclass: Thief", "Level 13: Use Magic Device"),
        "_Charges._ Whenever you use a magic item property that expends charges, roll 1d6. On a roll of 6, you use the property without expending the charges.",
    ),
    (
        ("Rogue", "Rogue Subclass: Thief", "Level 13: Use Magic Device"),
        "_Scrolls._ You can use any _Spell Scroll_, using Intelligence as your spellcasting ability for the spell. If the spell is a cantrip or a level 1 spell, you can cast it reliably. If the scroll contains a higher-level spell, you must first succeed on an Intelligence (Arcana) check (DC 10 plus the spell's level). On a successful check, you cast the spell from the scroll. On a failed check, the scroll disintegrates.",
    ),
    (
        ("Rogue", "Rogue Subclass: Thief", "Level 17: Thief's Reflexes"),
        "#### Level 17: Thief's Reflexes",
    ),
    (
        ("Rogue", "Rogue Subclass: Thief", "Level 17: Thief's Reflexes"),
        "You are adept at laying ambushes and quickly escaping danger. You can take two turns during the first round of any combat. You take your first turn at your normal Initiative and your second turn at your Initiative minus 10.",
    ),
    (("Sorcerer",), "## Sorcerer"),
    (
        ("Sorcerer",),
        "**Core Sorcerer Traits**\n\n<table>\n  <tbody>\n    <tr>\n      <td>Primary Ability</td>\n      <td>Charisma</td>\n    </tr>\n    <tr>\n      <td>Hit Point Die</td>\n      <td>D6 per Sorcerer level</td>\n    </tr>\n    <tr>\n      <td>Saving Throw Proficiencies</td>\n      <td>Constitution and Charisma</td>\n    </tr>\n    <tr>\n      <td>Skill Proficiencies</td>\n      <td>Choose 2: Arcana, Deception, Insight, Intimidation, Persuasion, or Religion</td>\n    </tr>\n    <tr>\n      <td>Weapon Proficiencies</td>\n      <td>Simple weapons</td>\n    </tr>\n    <tr>\n      <td>Armor Training</td>\n      <td>None</td>\n    </tr>\n    <tr>\n      <td>Starting Equipment</td>\n      <td>Choose A or B: (A) Spear, 2 Daggers, Arcane Focus (crystal), Dungeoneer's Pack, and 28 GP; or (B) 50 GP</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (("Sorcerer", "Becoming a Sorcerer …"), "### Becoming a Sorcerer …"),
    (
        ("Sorcerer", "Becoming a Sorcerer …", "As a Level 1 Character"),
        "#### As a Level 1 Character",
    ),
    (
        ("Sorcerer", "Becoming a Sorcerer …", "As a Level 1 Character"),
        "- Gain all the traits in the Core Sorcerer Traits table.\n- Gain the Sorcerer's level 1 features, which are listed in the Sorcerer Features table.",
    ),
    (
        ("Sorcerer", "Becoming a Sorcerer …", "As a Multiclass Character"),
        "#### As a Multiclass Character",
    ),
    (
        ("Sorcerer", "Becoming a Sorcerer …", "As a Multiclass Character"),
        '- Gain the Hit Point Die from the Core Sorcerer Traits table.\n- Gain the Sorcerer\'s level 1 features, which are listed in the Sorcerer Features table. See the multiclassing rules in "Character Creation" to determine your available spell slots.',
    ),
    (("Sorcerer", "Sorcerer Class Features"), "### Sorcerer Class Features"),
    (
        ("Sorcerer", "Sorcerer Class Features"),
        "As a Sorcerer, you gain the following class features when you reach the specified Sorcerer levels. These features are listed in the Sorcerer Features table.",
    ),
    (
        ("Sorcerer", "Sorcerer Class Features"),
        '**Sorcerer Features**\n\n<table>\n  <thead>\n    <tr>\n      <th>Level</th>\n      <th>Proficiency Bonus</th>\n      <th>Class Features</th>\n      <th>Sorcery Points</th>\n      <th>Cantrips</th>\n      <th>Prepared Spells</th>\n      <th colspan="9">——Spell Slots per Spell Level——</th>\n    </tr>\n    <tr>\n      <th>\n      </th>\n      <th>\n      </th>\n      <th>\n      </th>\n      <th>\n      </th>\n      <th>\n      </th>\n      <th>\n      </th>\n      <th>1</th>\n      <th>2</th>\n      <th>3</th>\n      <th>4</th>\n      <th>5</th>\n      <th>6</th>\n      <th>7</th>\n      <th>8</th>\n      <th>9</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>1</td>\n      <td>+2</td>\n      <td>Spellcasting, Innate Sorcery</td>\n      <td>—</td>\n      <td>4</td>\n      <td>2</td>\n      <td>2</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>2</td>\n      <td>+2</td>\n      <td>Font of Magic, Metamagic</td>\n      <td>2</td>\n      <td>4</td>\n      <td>4</td>\n      <td>3</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>3</td>\n      <td>+2</td>\n      <td>Sorcerer Subclass</td>\n      <td>3</td>\n      <td>4</td>\n      <td>6</td>\n      <td>4</td>\n      <td>2</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>4</td>\n      <td>+2</td>\n      <td>Ability Score Improvement</td>\n      <td>4</td>\n      <td>5</td>\n      <td>7</td>\n      <td>4</td>\n      <td>3</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>5</td>\n      <td>+3</td>\n      <td>Sorcerous Restoration</td>\n      <td>5</td>\n      <td>5</td>\n      <td>9</td>\n      <td>4</td>\n      <td>3</td>\n      <td>2</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>6</td>\n      <td>+3</td>\n      <td>Subclass feature</td>\n      <td>6</td>\n      <td>5</td>\n      <td>10</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>7</td>\n      <td>+3</td>\n      <td>Sorcery Incarnate</td>\n      <td>7</td>\n      <td>5</td>\n      <td>11</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>1</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>8</td>\n      <td>+3</td>\n      <td>Ability Score Improvement</td>\n      <td>8</td>\n      <td>5</td>\n      <td>12</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>2</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>9</td>\n      <td>+4</td>\n      <td>—</td>\n      <td>9</td>\n      <td>5</td>\n      <td>14</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>3</td>\n      <td>1</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>10</td>\n      <td>+4</td>\n      <td>Metamagic</td>\n      <td>10</td>\n      <td>6</td>\n      <td>15</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>3</td>\n      <td>2</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>11</td>\n      <td>+4</td>\n      <td>—</td>\n      <td>11</td>\n      <td>6</td>\n      <td>16</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>3</td>\n      <td>2</td>\n      <td>1</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>12</td>\n      <td>+4</td>\n      <td>Ability Score Improvement</td>\n      <td>12</td>\n      <td>6</td>\n      <td>16</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>3</td>\n      <td>2</td>\n      <td>1</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>13</td>\n      <td>+5</td>\n      <td>—</td>\n      <td>13</td>\n      <td>6</td>\n      <td>17</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>3</td>\n      <td>2</td>\n      <td>1</td>\n      <td>1</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>14</td>\n      <td>+5</td>\n      <td>Subclass feature</td>\n      <td>14</td>\n      <td>6</td>\n      <td>17</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>3</td>\n      <td>2</td>\n      <td>1</td>\n      <td>1</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>15</td>\n      <td>+5</td>\n      <td>—</td>\n      <td>15</td>\n      <td>6</td>\n      <td>18</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>3</td>\n      <td>2</td>\n      <td>1</td>\n      <td>1</td>\n      <td>1</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>16</td>\n      <td>+5</td>\n      <td>Ability Score Improvement</td>\n      <td>16</td>\n      <td>6</td>\n      <td>18</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>3</td>\n      <td>2</td>\n      <td>1</td>\n      <td>1</td>\n      <td>1</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>17</td>\n      <td>+6</td>\n      <td>Metamagic</td>\n      <td>17</td>\n      <td>6</td>\n      <td>19</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>3</td>\n      <td>2</td>\n      <td>1</td>\n      <td>1</td>\n      <td>1</td>\n      <td>1</td>\n    </tr>\n    <tr>\n      <td>18</td>\n      <td>+6</td>\n      <td>Subclass feature</td>\n      <td>18</td>\n      <td>6</td>\n      <td>20</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>3</td>\n      <td>3</td>\n      <td>1</td>\n      <td>1</td>\n      <td>1</td>\n      <td>1</td>\n    </tr>\n    <tr>\n      <td>19</td>\n      <td>+6</td>\n      <td>Epic Boon</td>\n      <td>19</td>\n      <td>6</td>\n      <td>21</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>3</td>\n      <td>3</td>\n      <td>2</td>\n      <td>1</td>\n      <td>1</td>\n      <td>1</td>\n    </tr>\n    <tr>\n      <td>20</td>\n      <td>+6</td>\n      <td>Arcane Apotheosis</td>\n      <td>20</td>\n      <td>6</td>\n      <td>22</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>3</td>\n      <td>3</td>\n      <td>2</td>\n      <td>2</td>\n      <td>1</td>\n      <td>1</td>\n    </tr>\n  </tbody>\n</table>',
    ),
    (
        ("Sorcerer", "Sorcerer Class Features", "Level 1: Spellcasting"),
        "#### Level 1: Spellcasting",
    ),
    (
        ("Sorcerer", "Sorcerer Class Features", "Level 1: Spellcasting"),
        'Drawing from your innate magic, you can cast spells. See "Spells" for the rules on spellcasting. The information below details how you use those rules with Sorcerer spells, which appear in the Sorcerer spell list later in the class\'s description.',
    ),
    (
        ("Sorcerer", "Sorcerer Class Features", "Level 1: Spellcasting"),
        "_Cantrips._ You know four Sorcerer cantrips of your choice. _Light_, _Prestidigitation_, _Shocking Grasp_, and _Sorcerous Burst_ are recommended. Whenever you gain a Sorcerer level, you can replace one of your cantrips from this feature with another Sorcerer cantrip of your choice.",
    ),
    (
        ("Sorcerer", "Sorcerer Class Features", "Level 1: Spellcasting"),
        "When you reach Sorcerer levels 4 and 10, you learn another Sorcerer cantrip of your choice, as shown in the Cantrips column of the Sorcerer Features table.",
    ),
    (
        ("Sorcerer", "Sorcerer Class Features", "Level 1: Spellcasting"),
        "_Spell Slots._ The Sorcerer Features table shows how many spell slots you have to cast your level 1+ spells. You regain all expended slots when you finish a Long Rest.",
    ),
    (
        ("Sorcerer", "Sorcerer Class Features", "Level 1: Spellcasting"),
        "_Prepared Spells of Level 1+._ You prepare the list of level 1+ spells that are available for you to cast with this feature. To start, choose two level 1 Sorcerer spells. _Burning Hands_ and _Detect Magic_ are recommended.",
    ),
    (
        ("Sorcerer", "Sorcerer Class Features", "Level 1: Spellcasting"),
        "The number of spells on your list increases as you gain Sorcerer levels, as shown in the Prepared Spells column of the Sorcerer Features table. Whenever that number increases, choose additional Sorcerer spells until the number of spells on your list matches the number in the Sorcerer Features table. The chosen spells must be of a level for which you have spell slots. For example, if you're a level 3 Sorcerer, your list of prepared spells can include six Sorcerer spells of level 1 or 2 in any combination.",
    ),
    (
        ("Sorcerer", "Sorcerer Class Features", "Level 1: Spellcasting"),
        "If another Sorcerer feature gives you spells that you always have prepared, those spells don't count against the number of spells you can prepare with this feature, but those spells otherwise count as Sorcerer spells for you.",
    ),
    (
        ("Sorcerer", "Sorcerer Class Features", "Level 1: Spellcasting"),
        "_Changing Your Prepared Spells._ Whenever you gain a Sorcerer level, you can replace one spell on your list with another Sorcerer spell for which you have spell slots.",
    ),
    (
        ("Sorcerer", "Sorcerer Class Features", "Level 1: Spellcasting"),
        "_Spellcasting Ability._ Charisma is your spellcasting ability for your Sorcerer spells.",
    ),
    (
        ("Sorcerer", "Sorcerer Class Features", "Level 1: Spellcasting"),
        "_Spellcasting Focus._ You can use an Arcane Focus as a Spellcasting Focus for your Sorcerer spells.",
    ),
    (
        ("Sorcerer", "Sorcerer Class Features", "Level 1: Innate Sorcery"),
        "#### Level 1: Innate Sorcery",
    ),
    (
        ("Sorcerer", "Sorcerer Class Features", "Level 1: Innate Sorcery"),
        "An event in your past left an indelible mark on you, infusing you with simmering magic. As a Bonus Action, you can unleash that magic for 1 minute, during which you gain the following benefits:\n• The spell save DC of your Sorcerer spells increases by 1.\n• You have Advantage on the attack rolls of Sorcerer spells you cast.",
    ),
    (
        ("Sorcerer", "Sorcerer Class Features", "Level 1: Innate Sorcery"),
        "You can use this feature twice, and you regain all expended uses of it when you finish a Long Rest.",
    ),
    (
        ("Sorcerer", "Sorcerer Class Features", "Level 2: Font of Magic"),
        "#### Level 2: Font of Magic",
    ),
    (
        ("Sorcerer", "Sorcerer Class Features", "Level 2: Font of Magic"),
        "You can tap into the wellspring of magic within yourself. This wellspring is represented by Sorcery Points, which allow you to create a variety of magical effects.",
    ),
    (
        ("Sorcerer", "Sorcerer Class Features", "Level 2: Font of Magic"),
        "You have 2 Sorcery Points, and you gain more as you reach higher levels, as shown in the Sorcery Points column of the Sorcerer Features table. You can't have more Sorcery Points than the number shown in the table for your level. You regain all expended Sorcery Points when you finish a Long Rest.",
    ),
    (
        ("Sorcerer", "Sorcerer Class Features", "Level 2: Font of Magic"),
        "You can use your Sorcery Points to fuel the options below, along with other features, such as Metamagic, that use those points.",
    ),
    (
        ("Sorcerer", "Sorcerer Class Features", "Level 2: Font of Magic"),
        "_Converting Spell Slots to Sorcery Points._ You can expend a spell slot to gain a number of Sorcery Points equal to the slot's level (no action required).",
    ),
    (
        ("Sorcerer", "Sorcerer Class Features", "Level 2: Font of Magic"),
        "_Creating Spell Slots._ As a Bonus Action, you can transform unexpended Sorcery Points into one spell slot. The Creating Spell Slots table shows the cost of creating a spell slot of a given level, and it lists the minimum Sorcerer level you must be to create a slot. You can create a spell slot no higher than level 5.",
    ),
    (
        ("Sorcerer", "Sorcerer Class Features", "Level 2: Font of Magic"),
        "Any spell slot you create with this feature vanishes when you finish a Long Rest.",
    ),
    (
        ("Sorcerer", "Sorcerer Class Features", "Level 2: Font of Magic"),
        "**Creating Spell Slots**\n\n<table>\n  <thead>\n    <tr>\n      <th>Spell Slot Level</th>\n      <th>Sorcery Point Cost</th>\n      <th>Min. Sorcerer Level</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>1</td>\n      <td>2</td>\n      <td>2</td>\n    </tr>\n    <tr>\n      <td>2</td>\n      <td>3</td>\n      <td>3</td>\n    </tr>\n    <tr>\n      <td>3</td>\n      <td>5</td>\n      <td>5</td>\n    </tr>\n    <tr>\n      <td>4</td>\n      <td>6</td>\n      <td>7</td>\n    </tr>\n    <tr>\n      <td>5</td>\n      <td>7</td>\n      <td>9</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        ("Sorcerer", "Sorcerer Class Features", "Level 2: Metamagic"),
        "#### Level 2: Metamagic",
    ),
    (
        ("Sorcerer", "Sorcerer Class Features", "Level 2: Metamagic"),
        'Because your magic flows from within, you can alter your spells to suit your needs; you gain two Metamagic options of your choice from "Metamagic Options" later in this class\'s description. You use the chosen options to temporarily modify spells you cast. To use an option, you must spend the number of Sorcery Points that it costs.',
    ),
    (
        ("Sorcerer", "Sorcerer Class Features", "Level 2: Metamagic"),
        "You can use only one Metamagic option on a spell when you cast it unless otherwise noted in one of those options.",
    ),
    (
        ("Sorcerer", "Sorcerer Class Features", "Level 2: Metamagic"),
        "Whenever you gain a Sorcerer level, you can replace one of your Metamagic options with one you don't know. You gain two more options at Sorcerer level 10 and two more at Sorcerer level 17.",
    ),
    (
        ("Sorcerer", "Sorcerer Class Features", "Level 3: Sorcerer Subclass"),
        "#### Level 3: Sorcerer Subclass",
    ),
    (
        ("Sorcerer", "Sorcerer Class Features", "Level 3: Sorcerer Subclass"),
        "You gain a Sorcerer subclass of your choice. The Draconic Sorcery subclass is detailed after this class's description. A subclass is a specialization that grants you features at certain Sorcerer levels. For the rest of your career, you gain each of your subclass's features that are of your Sorcerer level or lower.",
    ),
    (
        ("Sorcerer", "Sorcerer Class Features", "Level 4: Ability Score Improvement"),
        "#### Level 4: Ability Score Improvement",
    ),
    (
        ("Sorcerer", "Sorcerer Class Features", "Level 4: Ability Score Improvement"),
        'You gain the Ability Score Improvement feat (see "Feats") or another feat of your choice for which you qualify. You gain this feature again at Sorcerer levels 8, 12, and 16.',
    ),
    (
        ("Sorcerer", "Sorcerer Class Features", "Level 5: Sorcerous Restoration"),
        "#### Level 5: Sorcerous Restoration",
    ),
    (
        ("Sorcerer", "Sorcerer Class Features", "Level 5: Sorcerous Restoration"),
        "When you finish a Short Rest, you can regain expended Sorcery Points, but no more than a number equal to half your Sorcerer level (round down). Once you use this feature, you can't do so again until you finish a Long Rest.",
    ),
    (
        ("Sorcerer", "Sorcerer Class Features", "Level 7: Sorcery Incarnate"),
        "#### Level 7: Sorcery Incarnate",
    ),
    (
        ("Sorcerer", "Sorcerer Class Features", "Level 7: Sorcery Incarnate"),
        "If you have no uses of Innate Sorcery left, you can use it if you spend 2 Sorcery Points when you take the Bonus Action to activate it.",
    ),
    (
        ("Sorcerer", "Sorcerer Class Features", "Level 7: Sorcery Incarnate"),
        "In addition, while your Innate Sorcery feature is active, you can use up to two of your Metamagic options on each spell you cast.",
    ),
    (
        ("Sorcerer", "Sorcerer Class Features", "Level 19: Epic Boon"),
        "#### Level 19: Epic Boon",
    ),
    (
        ("Sorcerer", "Sorcerer Class Features", "Level 19: Epic Boon"),
        'You gain an Epic Boon feat (see "Feats") or another feat of your choice for which you qualify. Boon of Dimensional Travel is recommended.',
    ),
    (
        ("Sorcerer", "Sorcerer Class Features", "Level 20: Arcane Apotheosis"),
        "#### Level 20: Arcane Apotheosis",
    ),
    (
        ("Sorcerer", "Sorcerer Class Features", "Level 20: Arcane Apotheosis"),
        "While your Innate Sorcery feature is active, you can use one Metamagic option on each of your turns without spending Sorcery Points on it.",
    ),
    (("Sorcerer", "Metamagic Options"), "### Metamagic Options"),
    (
        ("Sorcerer", "Metamagic Options"),
        "The following options are available to your Metamagic feature. The options are presented in alphabetical order.",
    ),
    (("Sorcerer", "Metamagic Options", "Careful Spell"), "#### Careful Spell"),
    (("Sorcerer", "Metamagic Options", "Careful Spell"), "_Cost: 1 Sorcery Point_"),
    (
        ("Sorcerer", "Metamagic Options", "Careful Spell"),
        "When you cast a spell that forces other creatures to make a saving throw, you can protect some of those creatures from the spell's full force. To do so, spend 1 Sorcery Point and choose a number of those creatures up to your Charisma modifier (minimum of one creature). A chosen creature automatically succeeds on its saving throw against the spell, and\nit takes no damage if it would normally take half damage on a successful save.",
    ),
    (("Sorcerer", "Metamagic Options", "Distant Spell"), "#### Distant Spell"),
    (("Sorcerer", "Metamagic Options", "Distant Spell"), "_Cost: 1 Sorcery Point_"),
    (
        ("Sorcerer", "Metamagic Options", "Distant Spell"),
        "When you cast a spell that has a range of at least 5 feet, you can spend 1 Sorcery Point to double the spell's range. Or when you cast a spell that has a range of Touch, you can spend 1 Sorcery Point to make the spell's range 30 feet.",
    ),
    (("Sorcerer", "Metamagic Options", "Empowered Spell"), "#### Empowered Spell"),
    (("Sorcerer", "Metamagic Options", "Empowered Spell"), "_Cost: 1 Sorcery Point_"),
    (
        ("Sorcerer", "Metamagic Options", "Empowered Spell"),
        "When you roll damage for a spell, you can spend 1 Sorcery Point to reroll a number of the damage dice up to your Charisma modifier (minimum of one), and you must use the new rolls.",
    ),
    (
        ("Sorcerer", "Metamagic Options", "Empowered Spell"),
        "You can use Empowered Spell even if you've already used a different Metamagic option during the casting of the spell.",
    ),
    (("Sorcerer", "Metamagic Options", "Extended Spell"), "#### Extended Spell"),
    (("Sorcerer", "Metamagic Options", "Extended Spell"), "_Cost: 1 Sorcery Point_"),
    (
        ("Sorcerer", "Metamagic Options", "Extended Spell"),
        "When you cast a spell that has a duration of 1 minute or longer, you can spend 1 Sorcery Point to double its duration to a maximum duration of 24 hours.",
    ),
    (
        ("Sorcerer", "Metamagic Options", "Extended Spell"),
        "If the affected spell requires Concentration, you have Advantage on any saving throw you make to maintain that Concentration.",
    ),
    (("Sorcerer", "Metamagic Options", "Heightened Spell"), "#### Heightened Spell"),
    (("Sorcerer", "Metamagic Options", "Heightened Spell"), "_Cost: 2 Sorcery Points_"),
    (
        ("Sorcerer", "Metamagic Options", "Heightened Spell"),
        "When you cast a spell that forces a creature to make a saving throw, you can spend 2 Sorcery Points to give one target of the spell Disadvantage on saves against the spell.",
    ),
    (("Sorcerer", "Metamagic Options", "Quickened Spell"), "#### Quickened Spell"),
    (("Sorcerer", "Metamagic Options", "Quickened Spell"), "_Cost: 2 Sorcery Points_"),
    (
        ("Sorcerer", "Metamagic Options", "Quickened Spell"),
        "When you cast a spell that has a casting time of an action, you can spend 2 Sorcery Points to change the casting time to a Bonus Action for this casting. You can't modify a spell in this way if you've already cast a level 1+ spell on the current turn, nor can you cast a level 1+ spell on this turn after modifying a spell in this way.",
    ),
    (("Sorcerer", "Metamagic Options", "Seeking Spell"), "#### Seeking Spell"),
    (("Sorcerer", "Metamagic Options", "Seeking Spell"), "_Cost: 1 Sorcery Point_"),
    (
        ("Sorcerer", "Metamagic Options", "Seeking Spell"),
        "If you make an attack roll for a spell and miss, you can spend 1 Sorcery Point to reroll the d20, and you must use the new roll.",
    ),
    (
        ("Sorcerer", "Metamagic Options", "Seeking Spell"),
        "You can use Seeking Spell even if you've already used a different Metamagic option during the casting of the spell.",
    ),
    (("Sorcerer", "Metamagic Options", "Subtle Spell"), "#### Subtle Spell"),
    (("Sorcerer", "Metamagic Options", "Subtle Spell"), "_Cost: 1 Sorcery Point_"),
    (
        ("Sorcerer", "Metamagic Options", "Subtle Spell"),
        "When you cast a spell, you can spend 1 Sorcery Point to cast it without any Verbal, Somatic, or Material components, except Material components that are consumed by the spell or that have a cost specified in the spell.",
    ),
    (("Sorcerer", "Metamagic Options", "Transmuted Spell"), "#### Transmuted Spell"),
    (("Sorcerer", "Metamagic Options", "Transmuted Spell"), "_Cost: 1 Sorcery Point_"),
    (
        ("Sorcerer", "Metamagic Options", "Transmuted Spell"),
        "When you cast a spell that deals a type of damage from the following list, you can spend 1 Sorcery Point to change that damage type to one of the other listed types: Acid, Cold, Fire, Lightning, Poison, Thunder.",
    ),
    (("Sorcerer", "Metamagic Options", "Twinned Spell"), "#### Twinned Spell"),
    (("Sorcerer", "Metamagic Options", "Twinned Spell"), "_Cost: 1 Sorcery Point_"),
    (
        ("Sorcerer", "Metamagic Options", "Twinned Spell"),
        "When you cast a spell, such as _Charm Person_, that can be cast with a higher-level spell slot to target an additional creature, you can spend 1 Sorcery Point to increase the spell's effective level by 1.",
    ),
    (("Sorcerer", "Sorcerer Spell List"), "### Sorcerer Spell List"),
    (
        ("Sorcerer", "Sorcerer Spell List"),
        "This section presents the Sorcerer spell list. The spells are organized by spell level and then alphabetized, and each spell's school of magic is listed. In the Special column, _C_ means the spell requires Concentration, _R_ means it's a Ritual, and _M_ means it requires a specific Material component.",
    ),
    (
        ("Sorcerer", "Sorcerer Spell List", "Cantrips (Level 0 Sorcerer Spells)"),
        "#### Cantrips (Level 0 Sorcerer Spells)",
    ),
    (
        ("Sorcerer", "Sorcerer Spell List", "Cantrips (Level 0 Sorcerer Spells)"),
        "<table>\n  <thead>\n    <tr>\n      <th>Spell</th>\n      <th>School</th>\n      <th>Special</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>Acid Splash</td>\n      <td>Evocation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Chill Touch</td>\n      <td>Necromancy</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Dancing Lights</td>\n      <td>Illusion</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Elementalism</td>\n      <td>Transmutation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Fire Bolt</td>\n      <td>Evocation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Light</td>\n      <td>Evocation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Mage Hand</td>\n      <td>Conjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Mending</td>\n      <td>Transmutation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Message</td>\n      <td>Transmutation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Minor Illusion</td>\n      <td>Illusion</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Poison Spray</td>\n      <td>Necromancy</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Prestidigitation</td>\n      <td>Transmutation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Ray of Frost</td>\n      <td>Evocation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Shocking Grasp</td>\n      <td>Evocation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Sorcerous Burst</td>\n      <td>Evocation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>True Strike</td>\n      <td>Divination</td>\n      <td>—</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        ("Sorcerer", "Sorcerer Spell List", "Level 1 Sorcerer Spells"),
        "#### Level 1 Sorcerer Spells",
    ),
    (
        ("Sorcerer", "Sorcerer Spell List", "Level 1 Sorcerer Spells"),
        "<table>\n  <thead>\n    <tr>\n      <th>Spell</th>\n      <th>School</th>\n      <th>Special</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>Burning Hands</td>\n      <td>Evocation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Charm Person</td>\n      <td>Enchantment</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Chromatic Orb</td>\n      <td>Evocation</td>\n      <td>M</td>\n    </tr>\n    <tr>\n      <td>Color Spray</td>\n      <td>Illusion</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Comprehend Languages</td>\n      <td>Divination</td>\n      <td>R</td>\n    </tr>\n    <tr>\n      <td>Detect Magic</td>\n      <td>Divination</td>\n      <td>C, R</td>\n    </tr>\n    <tr>\n      <td>Disguise Self</td>\n      <td>Illusion</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Expeditious Retreat</td>\n      <td>Transmutation</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>False Life</td>\n      <td>Necromancy</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Feather Fall</td>\n      <td>Transmutation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Fog Cloud</td>\n      <td>Conjuration</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Grease</td>\n      <td>Conjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Ice Knife</td>\n      <td>Conjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Jump</td>\n      <td>Transmutation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Mage Armor</td>\n      <td>Abjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Magic Missile</td>\n      <td>Evocation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Ray of Sickness</td>\n      <td>Necromancy</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Shield</td>\n      <td>Abjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Silent Image</td>\n      <td>Illusion</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Sleep</td>\n      <td>Enchantment</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Thunderwave</td>\n      <td>Evocation</td>\n      <td>—</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        ("Sorcerer", "Sorcerer Spell List", "Level 2 Sorcerer Spells"),
        "#### Level 2 Sorcerer Spells",
    ),
    (
        ("Sorcerer", "Sorcerer Spell List", "Level 2 Sorcerer Spells"),
        "<table>\n  <thead>\n    <tr>\n      <th>Spell</th>\n      <th>School</th>\n      <th>Special</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>Alter Self</td>\n      <td>Transmutation</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Blindness/Deafness</td>\n      <td>Transmutation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Blur</td>\n      <td>Illusion</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Darkness</td>\n      <td>Evocation</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Darkvision</td>\n      <td>Transmutation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Detect Thoughts</td>\n      <td>Divination</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Dragon's Breath</td>\n      <td>Transmutation</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Enhance Ability</td>\n      <td>Transmutation</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Enlarge/Reduce</td>\n      <td>Transmutation</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Flame Blade</td>\n      <td>Evocation</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Flaming Sphere</td>\n      <td>Conjuration</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Gust of Wind</td>\n      <td>Evocation</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Hold Person</td>\n      <td>Enchantment</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Invisibility</td>\n      <td>Illusion</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Knock</td>\n      <td>Transmutation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Levitate</td>\n      <td>Transmutation</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Magic Weapon</td>\n      <td>Transmutation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Mind Spike</td>\n      <td>Divination</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Mirror Image</td>\n      <td>Illusion</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Misty Step</td>\n      <td>Conjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Phantasmal Force</td>\n      <td>Illusion</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Scorching Ray</td>\n      <td>Evocation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>See Invisibility</td>\n      <td>Divination</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Shatter</td>\n      <td>Evocation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Spider Climb</td>\n      <td>Transmutation</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Suggestion</td>\n      <td>Enchantment</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Web</td>\n      <td>Conjuration</td>\n      <td>C</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        ("Sorcerer", "Sorcerer Spell List", "Level 3 Sorcerer Spells"),
        "#### Level 3 Sorcerer Spells",
    ),
    (
        ("Sorcerer", "Sorcerer Spell List", "Level 3 Sorcerer Spells"),
        "<table>\n  <thead>\n    <tr>\n      <th>Spell</th>\n      <th>School</th>\n      <th>Special</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>Blink</td>\n      <td>Transmutation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Clairvoyance</td>\n      <td>Divination</td>\n      <td>C, M</td>\n    </tr>\n    <tr>\n      <td>Counterspell</td>\n      <td>Abjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Daylight</td>\n      <td>Evocation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Dispel Magic</td>\n      <td>Abjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Fear</td>\n      <td>Illusion</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Fireball</td>\n      <td>Evocation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Fly</td>\n      <td>Transmutation</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Gaseous Form</td>\n      <td>Transmutation</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Haste</td>\n      <td>Transmutation</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Hypnotic Pattern</td>\n      <td>Illusion</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Lightning Bolt</td>\n      <td>Evocation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Major Image</td>\n      <td>Illusion</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Protection from Energy</td>\n      <td>Abjuration</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Sleet Storm</td>\n      <td>Conjuration</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Slow</td>\n      <td>Transmutation</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Stinking Cloud</td>\n      <td>Conjuration</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Tongues</td>\n      <td>Divination</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Vampiric Touch</td>\n      <td>Necromancy</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Water Breathing</td>\n      <td>Transmutation</td>\n      <td>R</td>\n    </tr>\n    <tr>\n      <td>Water Walk</td>\n      <td>Transmutation</td>\n      <td>R</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        ("Sorcerer", "Sorcerer Spell List", "Level 4 Sorcerer Spells"),
        "#### Level 4 Sorcerer Spells",
    ),
    (
        ("Sorcerer", "Sorcerer Spell List", "Level 4 Sorcerer Spells"),
        "<table>\n  <thead>\n    <tr>\n      <th>Spell</th>\n      <th>School</th>\n      <th>Special</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>Banishment</td>\n      <td>Abjuration</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Blight</td>\n      <td>Necromancy</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Charm Monster</td>\n      <td>Enchantment</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Confusion</td>\n      <td>Enchantment</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Dimension Door</td>\n      <td>Conjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Dominate Beast</td>\n      <td>Enchantment</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Fire Shield</td>\n      <td>Evocation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Greater Invisibility</td>\n      <td>Illusion</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Ice Storm</td>\n      <td>Evocation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Polymorph</td>\n      <td>Transmutation</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Stoneskin</td>\n      <td>Transmutation</td>\n      <td>C, M</td>\n    </tr>\n    <tr>\n      <td>Vitriolic Sphere</td>\n      <td>Evocation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Wall of Fire</td>\n      <td>Evocation</td>\n      <td>C</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        ("Sorcerer", "Sorcerer Spell List", "Level 5 Sorcerer Spells"),
        "#### Level 5 Sorcerer Spells",
    ),
    (
        ("Sorcerer", "Sorcerer Spell List", "Level 5 Sorcerer Spells"),
        "<table>\n  <thead>\n    <tr>\n      <th>Spell</th>\n      <th>School</th>\n      <th>Special</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>Animate Objects</td>\n      <td>Transmutation</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Arcane Hand</td>\n      <td>Evocation</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Cloudkill</td>\n      <td>Conjuration</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Cone of Cold</td>\n      <td>Evocation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Creation</td>\n      <td>Illusion</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Dominate Person</td>\n      <td>Enchantment</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Hold Monster</td>\n      <td>Enchantment</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Insect Plague</td>\n      <td>Conjuration</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Seeming</td>\n      <td>Illusion</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Telekinesis</td>\n      <td>Transmutation</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Teleportation Circle</td>\n      <td>Conjuration</td>\n      <td>M</td>\n    </tr>\n    <tr>\n      <td>Wall of Stone</td>\n      <td>Evocation</td>\n      <td>C</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        ("Sorcerer", "Sorcerer Spell List", "Level 6 Sorcerer Spells"),
        "#### Level 6 Sorcerer Spells",
    ),
    (
        ("Sorcerer", "Sorcerer Spell List", "Level 6 Sorcerer Spells"),
        "<table>\n  <thead>\n    <tr>\n      <th>Spell</th>\n      <th>School</th>\n      <th>Special</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>Chain Lightning</td>\n      <td>Evocation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Circle of Death</td>\n      <td>Necromancy</td>\n      <td>M</td>\n    </tr>\n    <tr>\n      <td>Disintegrate</td>\n      <td>Transmutation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Eyebite</td>\n      <td>Necromancy</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Flesh to Stone</td>\n      <td>Transmutation</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Freezing Sphere</td>\n      <td>Evocation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Globe of Invulnerability</td>\n      <td>Abjuration</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Mass Suggestion</td>\n      <td>Enchantment</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Move Earth</td>\n      <td>Transmutation</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Sunbeam</td>\n      <td>Evocation</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>True Seeing</td>\n      <td>Divination</td>\n      <td>M</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        ("Sorcerer", "Sorcerer Spell List", "Level 7 Sorcerer Spells"),
        "#### Level 7 Sorcerer Spells",
    ),
    (
        ("Sorcerer", "Sorcerer Spell List", "Level 7 Sorcerer Spells"),
        "<table>\n  <thead>\n    <tr>\n      <th>Spell</th>\n      <th>School</th>\n      <th>Special</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>Delayed Blast Fireball</td>\n      <td>Evocation</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Etherealness</td>\n      <td>Conjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Finger of Death</td>\n      <td>Necromancy</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Fire Storm</td>\n      <td>Evocation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Plane Shift</td>\n      <td>Conjuration</td>\n      <td>M</td>\n    </tr>\n    <tr>\n      <td>Prismatic Spray</td>\n      <td>Evocation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Reverse Gravity</td>\n      <td>Transmutation</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Teleport</td>\n      <td>Conjuration</td>\n      <td>—</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        ("Sorcerer", "Sorcerer Spell List", "Level 8 Sorcerer Spells"),
        "#### Level 8 Sorcerer Spells",
    ),
    (
        ("Sorcerer", "Sorcerer Spell List", "Level 8 Sorcerer Spells"),
        "<table>\n  <thead>\n    <tr>\n      <th>Spell</th>\n      <th>School</th>\n      <th>Special</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>Demiplane</td>\n      <td>Conjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Dominate Monster</td>\n      <td>Enchantment</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Earthquake</td>\n      <td>Transmutation</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Incendiary Cloud</td>\n      <td>Conjuration</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Power Word Stun</td>\n      <td>Enchantment</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Sunburst</td>\n      <td>Evocation</td>\n      <td>—</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        ("Sorcerer", "Sorcerer Spell List", "Level 9 Sorcerer Spells"),
        "#### Level 9 Sorcerer Spells",
    ),
    (
        ("Sorcerer", "Sorcerer Spell List", "Level 9 Sorcerer Spells"),
        "<table>\n  <thead>\n    <tr>\n      <th>Spell</th>\n      <th>School</th>\n      <th>Special</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>Gate</td>\n      <td>Conjuration</td>\n      <td>C, M</td>\n    </tr>\n    <tr>\n      <td>Meteor Swarm</td>\n      <td>Evocation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Power Word Kill</td>\n      <td>Enchantment</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Time Stop</td>\n      <td>Transmutation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Wish</td>\n      <td>Conjuration</td>\n      <td>—</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        ("Sorcerer", "Sorcerer Subclass: Draconic Sorcery"),
        "### Sorcerer Subclass: Draconic Sorcery",
    ),
    (
        ("Sorcerer", "Sorcerer Subclass: Draconic Sorcery"),
        "_Breathe the Magic of Dragons_",
    ),
    (
        ("Sorcerer", "Sorcerer Subclass: Draconic Sorcery"),
        "Your innate magic comes from the gift of a dragon. Perhaps an ancient dragon facing death bequeathed some of its magical power to you or your ancestor. You might have absorbed magic from a site infused with dragons' power. Or perhaps you handled a treasure taken from a dragon's hoard that was steeped in draconic power. Or you might have a dragon for an ancestor.",
    ),
    (
        (
            "Sorcerer",
            "Sorcerer Subclass: Draconic Sorcery",
            "Level 3: Draconic Resilience",
        ),
        "#### Level 3: Draconic Resilience",
    ),
    (
        (
            "Sorcerer",
            "Sorcerer Subclass: Draconic Sorcery",
            "Level 3: Draconic Resilience",
        ),
        "The magic in your body manifests physical traits of your draconic gift. Your Hit Point maximum increases by 3, and it increases by 1 whenever you gain another Sorcerer level.",
    ),
    (
        (
            "Sorcerer",
            "Sorcerer Subclass: Draconic Sorcery",
            "Level 3: Draconic Resilience",
        ),
        "Parts of you are also covered by dragon-like scales. While you aren't wearing armor, your base Armor Class equals 10 plus your Dexterity and Charisma modifiers.",
    ),
    (
        ("Sorcerer", "Sorcerer Subclass: Draconic Sorcery", "Level 3: Draconic Spells"),
        "#### Level 3: Draconic Spells",
    ),
    (
        ("Sorcerer", "Sorcerer Subclass: Draconic Sorcery", "Level 3: Draconic Spells"),
        "When you reach a Sorcerer level specified in the Draconic Spells table, you thereafter always have the listed spells prepared.",
    ),
    (
        ("Sorcerer", "Sorcerer Subclass: Draconic Sorcery", "Level 3: Draconic Spells"),
        "**Draconic Spells**\n\n<table>\n  <thead>\n    <tr>\n      <th>Sorcerer Level</th>\n      <th>Spells</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>3</td>\n      <td>Alter Self, Chromatic Orb, Command, Dragon's Breath</td>\n    </tr>\n    <tr>\n      <td>5</td>\n      <td>Fear, Fly</td>\n    </tr>\n    <tr>\n      <td>7</td>\n      <td>Arcane Eye, Charm Monster</td>\n    </tr>\n    <tr>\n      <td>9</td>\n      <td>Legend Lore, Summon Dragon</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Sorcerer",
            "Sorcerer Subclass: Draconic Sorcery",
            "Level 6: Elemental Affinity",
        ),
        "#### Level 6: Elemental Affinity",
    ),
    (
        (
            "Sorcerer",
            "Sorcerer Subclass: Draconic Sorcery",
            "Level 6: Elemental Affinity",
        ),
        "Your draconic magic has an affinity with a damage type associated with dragons. Choose one of those types: Acid, Cold, Fire, Lightning, or Poison.",
    ),
    (
        (
            "Sorcerer",
            "Sorcerer Subclass: Draconic Sorcery",
            "Level 6: Elemental Affinity",
        ),
        "You have Resistance to that damage type, and when you cast a spell that deals damage of that type, you can add your Charisma modifier to one damage roll of that spell.",
    ),
    (
        ("Sorcerer", "Sorcerer Subclass: Draconic Sorcery", "Level 14: Dragon Wings"),
        "#### Level 14: Dragon Wings",
    ),
    (
        ("Sorcerer", "Sorcerer Subclass: Draconic Sorcery", "Level 14: Dragon Wings"),
        "As a Bonus Action, you can cause draconic wings to appear on your back. The wings last for 1 hour or until you dismiss them (no action required). For the duration, you have a Fly Speed of 60 feet.",
    ),
    (
        ("Sorcerer", "Sorcerer Subclass: Draconic Sorcery", "Level 14: Dragon Wings"),
        "Once you use this feature, you can't use it again until you finish a Long Rest unless you spend 3 Sorcery Points (no action required) to restore your use of it.",
    ),
    (
        (
            "Sorcerer",
            "Sorcerer Subclass: Draconic Sorcery",
            "Level 18: Dragon Companion",
        ),
        "#### Level 18: Dragon Companion",
    ),
    (
        (
            "Sorcerer",
            "Sorcerer Subclass: Draconic Sorcery",
            "Level 18: Dragon Companion",
        ),
        "You can cast _Summon Dragon_ without a Material component. You can also cast it once without a spell slot, and you regain the ability to cast it in this way when you finish a Long Rest.",
    ),
    (
        (
            "Sorcerer",
            "Sorcerer Subclass: Draconic Sorcery",
            "Level 18: Dragon Companion",
        ),
        "Whenever you start casting the spell, you can modify it so that it doesn't require Concentration. If you do so, the spell's duration becomes 1 minute for that casting.",
    ),
    (("Warlock",), "## Warlock"),
    (
        ("Warlock",),
        "**Core Warlock Traits**\n\n<table>\n  <tbody>\n    <tr>\n      <td>Primary Ability</td>\n      <td>Charisma</td>\n    </tr>\n    <tr>\n      <td>Hit Point Die</td>\n      <td>D8 per Warlock level</td>\n    </tr>\n    <tr>\n      <td>Saving Throw Proficiencies</td>\n      <td>Wisdom and Charisma</td>\n    </tr>\n    <tr>\n      <td>Skill Proficiencies</td>\n      <td>Choose 2: Arcana, Deception, History, Intimidation, Investigation, Nature, or Religion</td>\n    </tr>\n    <tr>\n      <td>Weapon Proficiencies</td>\n      <td>Simple weapons</td>\n    </tr>\n    <tr>\n      <td>Armor Training</td>\n      <td>Light armor</td>\n    </tr>\n    <tr>\n      <td>Starting Equipment</td>\n      <td>Choose A or B: (A) Leather Armor, Sickle, 2 Daggers, Arcane Focus (orb), Book (occult lore), Scholar's Pack, and 15 GP; or (B) 100 GP</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (("Warlock", "Becoming a Warlock …"), "### Becoming a Warlock …"),
    (
        ("Warlock", "Becoming a Warlock …", "As a Level 1 Character"),
        "#### As a Level 1 Character",
    ),
    (
        ("Warlock", "Becoming a Warlock …", "As a Level 1 Character"),
        "- Gain all the traits in the Core Warlock Traits table.\n- Gain the Warlock's level 1 features, which are listed in the Warlock Features table.",
    ),
    (
        ("Warlock", "Becoming a Warlock …", "As a Multiclass Character"),
        "#### As a Multiclass Character",
    ),
    (
        ("Warlock", "Becoming a Warlock …", "As a Multiclass Character"),
        '- Gain the following traits from the Core Warlock Traits table: Hit Point Die and training with Light armor.\n- Gain the Warlock\'s level 1 features, which are listed in the Warlock Features table. See the multiclassing rules in "Character Creation" to determine your available spell slots.',
    ),
    (("Warlock", "Warlock Class Features"), "### Warlock Class Features"),
    (
        ("Warlock", "Warlock Class Features"),
        "As a Warlock, you gain the following class features when you reach the specified Warlock levels. These features are listed in the Warlock Features table.",
    ),
    (
        ("Warlock", "Warlock Class Features"),
        "**Warlock Features**\n\n<table>\n  <thead>\n    <tr>\n      <th>Level</th>\n      <th>Proficiency Bonus</th>\n      <th>Class Features</th>\n      <th>Eldritch Invocations</th>\n      <th>Cantrips</th>\n      <th>Prepared Spells</th>\n      <th>Spell Slots</th>\n      <th>Slot Level</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>1</td>\n      <td>+2</td>\n      <td>Eldritch Invocations, Pact Magic</td>\n      <td>1</td>\n      <td>2</td>\n      <td>2</td>\n      <td>1</td>\n      <td>1</td>\n    </tr>\n    <tr>\n      <td>2</td>\n      <td>+2</td>\n      <td>Magical Cunning</td>\n      <td>3</td>\n      <td>2</td>\n      <td>3</td>\n      <td>2</td>\n      <td>1</td>\n    </tr>\n    <tr>\n      <td>3</td>\n      <td>+2</td>\n      <td>Warlock Subclass</td>\n      <td>3</td>\n      <td>2</td>\n      <td>4</td>\n      <td>2</td>\n      <td>2</td>\n    </tr>\n    <tr>\n      <td>4</td>\n      <td>+2</td>\n      <td>Ability Score Improvement</td>\n      <td>3</td>\n      <td>3</td>\n      <td>5</td>\n      <td>2</td>\n      <td>2</td>\n    </tr>\n    <tr>\n      <td>5</td>\n      <td>+3</td>\n      <td>—</td>\n      <td>5</td>\n      <td>3</td>\n      <td>6</td>\n      <td>2</td>\n      <td>3</td>\n    </tr>\n    <tr>\n      <td>6</td>\n      <td>+3</td>\n      <td>Subclass feature</td>\n      <td>5</td>\n      <td>3</td>\n      <td>7</td>\n      <td>2</td>\n      <td>3</td>\n    </tr>\n    <tr>\n      <td>7</td>\n      <td>+3</td>\n      <td>—</td>\n      <td>6</td>\n      <td>3</td>\n      <td>8</td>\n      <td>2</td>\n      <td>4</td>\n    </tr>\n    <tr>\n      <td>8</td>\n      <td>+3</td>\n      <td>Ability Score Improvement</td>\n      <td>6</td>\n      <td>3</td>\n      <td>9</td>\n      <td>2</td>\n      <td>4</td>\n    </tr>\n    <tr>\n      <td>9</td>\n      <td>+4</td>\n      <td>Contact Patron</td>\n      <td>7</td>\n      <td>3</td>\n      <td>10</td>\n      <td>2</td>\n      <td>5</td>\n    </tr>\n    <tr>\n      <td>10</td>\n      <td>+4</td>\n      <td>Subclass feature</td>\n      <td>7</td>\n      <td>4</td>\n      <td>10</td>\n      <td>2</td>\n      <td>5</td>\n    </tr>\n    <tr>\n      <td>11</td>\n      <td>+4</td>\n      <td>Mystic Arcanum (level 6 spell)</td>\n      <td>7</td>\n      <td>4</td>\n      <td>11</td>\n      <td>3</td>\n      <td>5</td>\n    </tr>\n    <tr>\n      <td>12</td>\n      <td>+4</td>\n      <td>Ability Score Improvement</td>\n      <td>8</td>\n      <td>4</td>\n      <td>11</td>\n      <td>3</td>\n      <td>5</td>\n    </tr>\n    <tr>\n      <td>13</td>\n      <td>+5</td>\n      <td>Mystic Arcanum (level 7 spell)</td>\n      <td>8</td>\n      <td>4</td>\n      <td>12</td>\n      <td>3</td>\n      <td>5</td>\n    </tr>\n    <tr>\n      <td>14</td>\n      <td>+5</td>\n      <td>Subclass feature</td>\n      <td>8</td>\n      <td>4</td>\n      <td>12</td>\n      <td>3</td>\n      <td>5</td>\n    </tr>\n    <tr>\n      <td>15</td>\n      <td>+5</td>\n      <td>Mystic Arcanum (level 8 spell)</td>\n      <td>9</td>\n      <td>4</td>\n      <td>13</td>\n      <td>3</td>\n      <td>5</td>\n    </tr>\n    <tr>\n      <td>16</td>\n      <td>+5</td>\n      <td>Ability Score Improvement</td>\n      <td>9</td>\n      <td>4</td>\n      <td>13</td>\n      <td>3</td>\n      <td>5</td>\n    </tr>\n    <tr>\n      <td>17</td>\n      <td>+6</td>\n      <td>Mystic Arcanum (level 9 spell)</td>\n      <td>9</td>\n      <td>4</td>\n      <td>14</td>\n      <td>4</td>\n      <td>5</td>\n    </tr>\n    <tr>\n      <td>18</td>\n      <td>+6</td>\n      <td>—</td>\n      <td>10</td>\n      <td>4</td>\n      <td>14</td>\n      <td>4</td>\n      <td>5</td>\n    </tr>\n    <tr>\n      <td>19</td>\n      <td>+6</td>\n      <td>Epic Boon</td>\n      <td>10</td>\n      <td>4</td>\n      <td>15</td>\n      <td>4</td>\n      <td>5</td>\n    </tr>\n    <tr>\n      <td>20</td>\n      <td>+6</td>\n      <td>Eldritch Master</td>\n      <td>10</td>\n      <td>4</td>\n      <td>15</td>\n      <td>4</td>\n      <td>5</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        ("Warlock", "Warlock Class Features", "Level 1: Eldritch Invocations"),
        "#### Level 1: Eldritch Invocations",
    ),
    (
        ("Warlock", "Warlock Class Features", "Level 1: Eldritch Invocations"),
        'You have unearthed Eldritch Invocations, pieces of forbidden knowledge that imbue you with an abiding magical ability or other lessons. You gain one invocation of your choice, such as Pact of the Tome. Invocations are described in the "Eldritch Invocation Options" section later in this class\'s description.',
    ),
    (
        ("Warlock", "Warlock Class Features", "Level 1: Eldritch Invocations"),
        "_Prerequisites._ If an invocation has a prerequisite, you must meet it to learn that invocation. For example, if an invocation requires you to be a level 5+ Warlock, you can select the invocation once you reach Warlock level 5.",
    ),
    (
        ("Warlock", "Warlock Class Features", "Level 1: Eldritch Invocations"),
        "_Replacing and Gaining Invocations._ Whenever you gain a Warlock level, you can replace one of your invocations with another one for which you qualify. You can't replace an invocation if it's a prerequisite for another invocation that you have.",
    ),
    (
        ("Warlock", "Warlock Class Features", "Level 1: Eldritch Invocations"),
        "When you gain certain Warlock levels, you gain more invocations of your choice, as shown in the Invocations column of the Warlock Features table.",
    ),
    (
        ("Warlock", "Warlock Class Features", "Level 1: Eldritch Invocations"),
        "You can't pick the same invocation more than once unless its description says otherwise.",
    ),
    (
        ("Warlock", "Warlock Class Features", "Level 1: Pact Magic"),
        "#### Level 1: Pact Magic",
    ),
    (
        ("Warlock", "Warlock Class Features", "Level 1: Pact Magic"),
        'Through occult ceremony, you have formed a pact with a mysterious entity to gain magical powers. The entity is a voice in the shadows—its identity unclear—but its boon to you is concrete: the ability to cast spells. See "Spells" for the rules on spellcasting. The information below details how you use those rules with Warlock spells, which appear in the Warlock spell list later in the class\'s description.',
    ),
    (
        ("Warlock", "Warlock Class Features", "Level 1: Pact Magic"),
        "_Cantrips._ You know two Warlock cantrips of your choice. _Eldritch Blast_ and _Prestidigitation_ are recommended. Whenever you gain a Warlock level, you can replace one of your cantrips from this feature with another Warlock cantrip of your choice.",
    ),
    (
        ("Warlock", "Warlock Class Features", "Level 1: Pact Magic"),
        "When you reach Warlock levels 4 and 10, you learn another Warlock cantrip of your choice, as shown in the Cantrips column of the Warlock Features table.",
    ),
    (
        ("Warlock", "Warlock Class Features", "Level 1: Pact Magic"),
        "_Spell Slots._ The Warlock Features table shows how many spell slots you have to cast your Warlock spells of levels 1–5. The table also shows the level of those slots, all of which are the same level. You regain all expended Pact Magic spell slots when you finish a Short or Long Rest.",
    ),
    (
        ("Warlock", "Warlock Class Features", "Level 1: Pact Magic"),
        "For example, when you're a level 5 Warlock, you have two level 3 spell slots. To cast the level 1 spell _Charm Person_, you must spend one of those slots, and you cast it as a level 3 spell.",
    ),
    (
        ("Warlock", "Warlock Class Features", "Level 1: Pact Magic"),
        "_Prepared Spells of Level 1+._ You prepare the list of level 1+ spells that are available for you to cast with this feature. To start, choose two level 1 Warlock spells. _Charm Person_ and _Hex_ are recommended.",
    ),
    (
        ("Warlock", "Warlock Class Features", "Level 1: Pact Magic"),
        "The number of spells on your list increases as you gain Warlock levels, as shown in the Prepared Spells column of the Warlock Features table. Whenever that number increases, choose additional Warlock spells until the number of spells on your list matches the number in the table. The chosen spells must be of a level no higher than what's shown in the table's Slot Level column for your level. When you reach level 6, for example, you learn a new Warlock spell, which can be of levels 1–3.",
    ),
    (
        ("Warlock", "Warlock Class Features", "Level 1: Pact Magic"),
        "If another Warlock feature gives you spells that you always have prepared, those spells don't count against the number of spells you can prepare with this feature, but those spells otherwise count as Warlock spells for you.",
    ),
    (
        ("Warlock", "Warlock Class Features", "Level 1: Pact Magic"),
        "_Changing Your Prepared Spells._ Whenever you gain a Warlock level, you can replace one spell on your list with another Warlock spell of an eligible level.",
    ),
    (
        ("Warlock", "Warlock Class Features", "Level 1: Pact Magic"),
        "_Spellcasting Ability._ Charisma is the spellcasting ability for your Warlock spells.",
    ),
    (
        ("Warlock", "Warlock Class Features", "Level 1: Pact Magic"),
        "_Spellcasting Focus._ You can use an Arcane Focus as a Spellcasting Focus for your Warlock spells.",
    ),
    (
        ("Warlock", "Warlock Class Features", "Level 2: Magical Cunning"),
        "#### Level 2: Magical Cunning",
    ),
    (
        ("Warlock", "Warlock Class Features", "Level 2: Magical Cunning"),
        "You can perform an esoteric rite for 1 minute. At the end of it, you regain expended Pact Magic spell slots but no more than a number equal to half your maximum (round up). Once you use this feature, you can't do so again until you finish a Long Rest.",
    ),
    (
        ("Warlock", "Warlock Class Features", "Level 3: Warlock Subclass"),
        "#### Level 3: Warlock Subclass",
    ),
    (
        ("Warlock", "Warlock Class Features", "Level 3: Warlock Subclass"),
        "You gain a Warlock subclass of your choice. The Fiend Patron subclass is detailed after this class's description. A subclass is a specialization that grants you features at certain Warlock levels. For the rest of your career, you gain each of your subclass's features that are of your Warlock level or lower.",
    ),
    (
        ("Warlock", "Warlock Class Features", "Level 4: Ability Score Improvement"),
        "#### Level 4: Ability Score Improvement",
    ),
    (
        ("Warlock", "Warlock Class Features", "Level 4: Ability Score Improvement"),
        'You gain the Ability Score Improvement feat (see "Feats") or another feat of your choice for which you qualify. You gain this feature again at Warlock levels 8, 12, and 16.',
    ),
    (
        ("Warlock", "Warlock Class Features", "Level 9: Contact Patron"),
        "#### Level 9: Contact Patron",
    ),
    (
        ("Warlock", "Warlock Class Features", "Level 9: Contact Patron"),
        "In the past, you usually contacted your patron through intermediaries. Now you can communicate directly; you always have the _Contact Other Plane_ spell prepared. With this feature, you can cast the spell without expending a spell slot to contact your patron, and you automatically succeed on the spell's saving throw.",
    ),
    (
        ("Warlock", "Warlock Class Features", "Level 9: Contact Patron"),
        "Once you cast the spell with this feature, you can't do so in this way again until you finish a Long Rest.",
    ),
    (
        ("Warlock", "Warlock Class Features", "Level 11: Mystic Arcanum"),
        "#### Level 11: Mystic Arcanum",
    ),
    (
        ("Warlock", "Warlock Class Features", "Level 11: Mystic Arcanum"),
        "Your patron grants you a magical secret called an arcanum. Choose one level 6 Warlock spell as this arcanum.",
    ),
    (
        ("Warlock", "Warlock Class Features", "Level 11: Mystic Arcanum"),
        "You can cast your arcanum spell once without expending a spell slot, and you must finish a Long Rest before you can cast it in this way again.",
    ),
    (
        ("Warlock", "Warlock Class Features", "Level 11: Mystic Arcanum"),
        "As shown in the Warlock Features table, you gain another Warlock spell of your choice that can be cast in this way when you reach Warlock levels 13 (level 7 spell), 15 (level 8 spell), and 17 (level 9 spell). You regain all uses of your Mystic Arcanum when you finish a Long Rest.",
    ),
    (
        ("Warlock", "Warlock Class Features", "Level 11: Mystic Arcanum"),
        "Whenever you gain a Warlock level, you can replace one of your arcanum spells with another Warlock spell of the same level.",
    ),
    (
        ("Warlock", "Warlock Class Features", "Level 19: Epic Boon"),
        "#### Level 19: Epic Boon",
    ),
    (
        ("Warlock", "Warlock Class Features", "Level 19: Epic Boon"),
        'You gain an Epic Boon feat (see "Feats") or another feat of your choice for which you qualify. Boon of Fate is recommended.',
    ),
    (
        ("Warlock", "Warlock Class Features", "Level 20: Eldritch Master"),
        "#### Level 20: Eldritch Master",
    ),
    (
        ("Warlock", "Warlock Class Features", "Level 20: Eldritch Master"),
        "When you use your Magical Cunning feature, you regain all your expended Pact Magic spell slots.",
    ),
    (("Warlock", "Eldritch Invocation Options"), "### Eldritch Invocation Options"),
    (
        ("Warlock", "Eldritch Invocation Options"),
        "Eldritch Invocation options appear in alphabetical order.",
    ),
    (
        ("Warlock", "Eldritch Invocation Options", "Agonizing Blast"),
        "#### Agonizing Blast",
    ),
    (
        ("Warlock", "Eldritch Invocation Options", "Agonizing Blast"),
        "_Prerequisite: Level 2+ Warlock, a Warlock Cantrip That Deals Damage_",
    ),
    (
        ("Warlock", "Eldritch Invocation Options", "Agonizing Blast"),
        "Choose one of your known Warlock cantrips that deals damage. You can add your Charisma modifier to that spell's damage rolls.",
    ),
    (
        ("Warlock", "Eldritch Invocation Options", "Agonizing Blast"),
        "_Repeatable._ You can gain this invocation more than once. Each time you do so, choose a different eligible cantrip.",
    ),
    (
        ("Warlock", "Eldritch Invocation Options", "Armor of Shadows"),
        "#### Armor of Shadows",
    ),
    (
        ("Warlock", "Eldritch Invocation Options", "Armor of Shadows"),
        "You can cast _Mage Armor_ on yourself without expending a spell slot.",
    ),
    (
        ("Warlock", "Eldritch Invocation Options", "Ascendant Step"),
        "#### Ascendant Step",
    ),
    (
        ("Warlock", "Eldritch Invocation Options", "Ascendant Step"),
        "_Prerequisite: Level 5+ Warlock_",
    ),
    (
        ("Warlock", "Eldritch Invocation Options", "Ascendant Step"),
        "You can cast _Levitate_ on yourself without expending a spell slot.",
    ),
    (("Warlock", "Eldritch Invocation Options", "Devil's Sight"), "#### Devil's Sight"),
    (
        ("Warlock", "Eldritch Invocation Options", "Devil's Sight"),
        "_Prerequisite: Level 2+ Warlock_",
    ),
    (
        ("Warlock", "Eldritch Invocation Options", "Devil's Sight"),
        "You can see normally in Dim Light and Darkness—both magical and nonmagical—within 120 feet of yourself.",
    ),
    (
        ("Warlock", "Eldritch Invocation Options", "Devouring Blade"),
        "#### Devouring Blade",
    ),
    (
        ("Warlock", "Eldritch Invocation Options", "Devouring Blade"),
        "_Prerequisite: Level 12+ Warlock, Thirsting Blade Invocation_",
    ),
    (
        ("Warlock", "Eldritch Invocation Options", "Devouring Blade"),
        "The Extra Attack of your Thirsting Blade invocation confers two extra attacks rather than one.",
    ),
    (("Warlock", "Eldritch Invocation Options", "Eldritch Mind"), "#### Eldritch Mind"),
    (
        ("Warlock", "Eldritch Invocation Options", "Eldritch Mind"),
        "You have Advantage on Constitution saving throws that you make to maintain Concentration.",
    ),
    (
        ("Warlock", "Eldritch Invocation Options", "Eldritch Smite"),
        "#### Eldritch Smite",
    ),
    (
        ("Warlock", "Eldritch Invocation Options", "Eldritch Smite"),
        "_Prerequisite: Level 5+ Warlock, Pact of the Blade Invocation_",
    ),
    (
        ("Warlock", "Eldritch Invocation Options", "Eldritch Smite"),
        "Once per turn when you hit a creature with your pact weapon, you can expend a Pact Magic spell slot to deal an extra 1d8 Force damage to the target,\nplus another 1d8 per level of the spell slot, and you can give the target the Prone condition if it is Huge or smaller.",
    ),
    (
        ("Warlock", "Eldritch Invocation Options", "Eldritch Spear"),
        "#### Eldritch Spear",
    ),
    (
        ("Warlock", "Eldritch Invocation Options", "Eldritch Spear"),
        "_Prerequisite: Level 2+ Warlock, a Warlock Cantrip That Deals Damage_",
    ),
    (
        ("Warlock", "Eldritch Invocation Options", "Eldritch Spear"),
        "Choose one of your known Warlock cantrips that deals damage and has a range of 10+ feet. When you cast that spell, its range increases by a number of feet equal to 30 times your Warlock level.",
    ),
    (
        ("Warlock", "Eldritch Invocation Options", "Eldritch Spear"),
        "_Repeatable._ You can gain this invocation more than once. Each time you do so, choose a different eligible cantrip.",
    ),
    (
        ("Warlock", "Eldritch Invocation Options", "Fiendish Vigor"),
        "#### Fiendish Vigor",
    ),
    (
        ("Warlock", "Eldritch Invocation Options", "Fiendish Vigor"),
        "_Prerequisite: Level 2+ Warlock_",
    ),
    (
        ("Warlock", "Eldritch Invocation Options", "Fiendish Vigor"),
        "You can cast _False Life_ on yourself without expending a spell slot. When you cast the spell with this feature, you don't roll the die for the Temporary Hit Points; you automatically get the highest number on the die.",
    ),
    (
        ("Warlock", "Eldritch Invocation Options", "Gaze of Two Minds"),
        "#### Gaze of Two Minds",
    ),
    (
        ("Warlock", "Eldritch Invocation Options", "Gaze of Two Minds"),
        "_Prerequisite: Level 5+ Warlock_",
    ),
    (
        ("Warlock", "Eldritch Invocation Options", "Gaze of Two Minds"),
        "You can use a Bonus Action to touch a willing creature and perceive through its senses until the end of your next turn. As long as the creature is on the same plane of existence as you, you can take a Bonus Action on subsequent turns to maintain this connection, extending the duration until the end of your next turn. The connection ends if you don't maintain it in this way.",
    ),
    (
        ("Warlock", "Eldritch Invocation Options", "Gaze of Two Minds"),
        "While perceiving through the other creature's senses, you benefit from any special senses possessed by that creature, and you can cast spells as if you were in your space or the other creature's space if the two of you are within 60 feet of each other.",
    ),
    (
        ("Warlock", "Eldritch Invocation Options", "Gift of the Depths"),
        "#### Gift of the Depths",
    ),
    (
        ("Warlock", "Eldritch Invocation Options", "Gift of the Depths"),
        "_Prerequisite: Level 5+ Warlock_",
    ),
    (
        ("Warlock", "Eldritch Invocation Options", "Gift of the Depths"),
        "You can breathe underwater, and you gain a Swim Speed equal to your Speed.",
    ),
    (
        ("Warlock", "Eldritch Invocation Options", "Gift of the Depths"),
        "You can also cast _Water Breathing_ once without expending a spell slot. You regain the ability to cast it in this way again when you finish a Long Rest.",
    ),
    (
        ("Warlock", "Eldritch Invocation Options", "Gift of the Protectors"),
        "#### Gift of the Protectors",
    ),
    (
        ("Warlock", "Eldritch Invocation Options", "Gift of the Protectors"),
        "_Prerequisite: Level 9+ Warlock, Pact of the Tome Invocation_",
    ),
    (
        ("Warlock", "Eldritch Invocation Options", "Gift of the Protectors"),
        "A new page appears in your _Book of Shadows_ when you conjure it. With your permission, a creature can take an action to write its name on that page, which can contain a number of names equal to your Charisma modifier (minimum of one name).",
    ),
    (
        ("Warlock", "Eldritch Invocation Options", "Gift of the Protectors"),
        "When any creature whose name is on the page is reduced to 0 Hit Points but not killed outright, the creature magically drops to 1 Hit Point instead. Once this magic is triggered, no creature can benefit from it until you finish a Long Rest.",
    ),
    (
        ("Warlock", "Eldritch Invocation Options", "Gift of the Protectors"),
        "As a Magic action, you can erase a name on the page by touching it.",
    ),
    (
        ("Warlock", "Eldritch Invocation Options", "Investment of the Chain Master"),
        "#### Investment of the Chain Master",
    ),
    (
        ("Warlock", "Eldritch Invocation Options", "Investment of the Chain Master"),
        "_Prerequisite: Level 5+ Warlock, Pact of the Chain Invocation_",
    ),
    (
        ("Warlock", "Eldritch Invocation Options", "Investment of the Chain Master"),
        "When you cast _Find Familiar_, you infuse the summoned familiar with a measure of your eldritch power, granting the creature the following benefits.",
    ),
    (
        ("Warlock", "Eldritch Invocation Options", "Investment of the Chain Master"),
        "_Aerial or Aquatic._ The familiar gains either a Fly Speed or a Swim Speed (your choice) of 40 feet.",
    ),
    (
        ("Warlock", "Eldritch Invocation Options", "Investment of the Chain Master"),
        "_Quick Attack._ As a Bonus Action, you can command the familiar to take the Attack action.",
    ),
    (
        ("Warlock", "Eldritch Invocation Options", "Investment of the Chain Master"),
        "_Necrotic or Radiant Damage._ Whenever the familiar deals Bludgeoning, Piercing, or Slashing damage, you can make it deal Necrotic or Radiant damage instead.",
    ),
    (
        ("Warlock", "Eldritch Invocation Options", "Investment of the Chain Master"),
        "_Your Save DC._ If the familiar forces a creature to make a saving throw, it uses your spell save DC.",
    ),
    (
        ("Warlock", "Eldritch Invocation Options", "Investment of the Chain Master"),
        "_Resistance._ When the familiar takes damage, you can take a Reaction to grant it Resistance against that damage.",
    ),
    (
        ("Warlock", "Eldritch Invocation Options", "Lessons of the First Ones"),
        "#### Lessons of the First Ones",
    ),
    (
        ("Warlock", "Eldritch Invocation Options", "Lessons of the First Ones"),
        "_Prerequisite: Level 2+ Warlock_",
    ),
    (
        ("Warlock", "Eldritch Invocation Options", "Lessons of the First Ones"),
        'You have received knowledge from an elder entity of the multiverse, allowing you to gain one Origin feat of your choice (see "Feats").',
    ),
    (
        ("Warlock", "Eldritch Invocation Options", "Lessons of the First Ones"),
        "_Repeatable._ You can gain this invocation more than once. Each time you do so, choose a different Origin feat.",
    ),
    (("Warlock", "Eldritch Invocation Options", "Lifedrinker"), "#### Lifedrinker"),
    (
        ("Warlock", "Eldritch Invocation Options", "Lifedrinker"),
        "_Prerequisite: Level 9+ Warlock, Pact of the Blade Invocation_",
    ),
    (
        ("Warlock", "Eldritch Invocation Options", "Lifedrinker"),
        "Once per turn when you hit a creature with your pact weapon, you can deal an extra 1d6 Necrotic, Psychic, or Radiant damage (your choice) to the creature, and you can expend one of your Hit Point Dice to roll it and regain a number of Hit Points equal to the roll plus your Constitution modifier (minimum of 1 Hit Point).",
    ),
    (
        ("Warlock", "Eldritch Invocation Options", "Mask of Many Faces"),
        "#### Mask of Many Faces",
    ),
    (
        ("Warlock", "Eldritch Invocation Options", "Mask of Many Faces"),
        "_Prerequisite: Level 2+ Warlock_",
    ),
    (
        ("Warlock", "Eldritch Invocation Options", "Mask of Many Faces"),
        "You can cast _Disguise Self_ without expending a spell slot.",
    ),
    (
        ("Warlock", "Eldritch Invocation Options", "Master of Myriad Forms"),
        "#### Master of Myriad Forms",
    ),
    (
        ("Warlock", "Eldritch Invocation Options", "Master of Myriad Forms"),
        "_Prerequisite: Level 5+ Warlock_",
    ),
    (
        ("Warlock", "Eldritch Invocation Options", "Master of Myriad Forms"),
        "You can cast _Alter Self_ without expending a spell slot.",
    ),
    (("Warlock", "Eldritch Invocation Options", "Misty Visions"), "#### Misty Visions"),
    (
        ("Warlock", "Eldritch Invocation Options", "Misty Visions"),
        "_Prerequisite: Level 2+ Warlock_",
    ),
    (
        ("Warlock", "Eldritch Invocation Options", "Misty Visions"),
        "You can cast _Silent Image_ without expending a spell slot.",
    ),
    (
        ("Warlock", "Eldritch Invocation Options", "One with Shadows"),
        "#### One with Shadows",
    ),
    (
        ("Warlock", "Eldritch Invocation Options", "One with Shadows"),
        "_Prerequisite: Level 5+ Warlock_",
    ),
    (
        ("Warlock", "Eldritch Invocation Options", "One with Shadows"),
        "While you're in an area of Dim Light or Darkness, you can cast _Invisibility_ on yourself without expending a spell slot.",
    ),
    (
        ("Warlock", "Eldritch Invocation Options", "Otherworldly Leap"),
        "#### Otherworldly Leap",
    ),
    (
        ("Warlock", "Eldritch Invocation Options", "Otherworldly Leap"),
        "_Prerequisite: Level 2+ Warlock_",
    ),
    (
        ("Warlock", "Eldritch Invocation Options", "Otherworldly Leap"),
        "You can cast _Jump_ on yourself without expending a spell slot.",
    ),
    (
        ("Warlock", "Eldritch Invocation Options", "Pact of the Blade"),
        "#### Pact of the Blade",
    ),
    (
        ("Warlock", "Eldritch Invocation Options", "Pact of the Blade"),
        "As a Bonus Action, you can conjure a pact weapon in your hand—a Simple or Martial Melee weapon of your choice with which you bond—or create a bond with a magic weapon you touch; you can't bond with a magic weapon if someone else is attuned to it or another Warlock is bonded with it. Until the bond ends, you have proficiency with the weapon, and you can use it as a Spellcasting Focus.",
    ),
    (
        ("Warlock", "Eldritch Invocation Options", "Pact of the Blade"),
        "Whenever you attack with the bonded weapon, you can use your Charisma modifier for the attack and damage rolls instead of using Strength or Dexterity; and you can cause the weapon to deal Necrotic, Psychic, or Radiant damage or its normal damage type.",
    ),
    (
        ("Warlock", "Eldritch Invocation Options", "Pact of the Blade"),
        "Your bond with the weapon ends if you use this feature's Bonus Action again, if the weapon is more than 5 feet away from you for 1 minute or more, or if you die. A conjured weapon disappears when the bond ends.",
    ),
    (
        ("Warlock", "Eldritch Invocation Options", "Pact of the Chain"),
        "#### Pact of the Chain",
    ),
    (
        ("Warlock", "Eldritch Invocation Options", "Pact of the Chain"),
        "You learn the _Find Familiar_ spell and can cast it as a Magic action without expending a spell slot.",
    ),
    (
        ("Warlock", "Eldritch Invocation Options", "Pact of the Chain"),
        'When you cast the spell, you choose one of the normal forms for your familiar or one of the following special forms: **Imp, Pseudodragon, Quasit, Skeleton, Sphinx of Wonder, Sprite,** or **Venomous Snake** (see "Monsters" for the familiar\'s stat block).',
    ),
    (
        ("Warlock", "Eldritch Invocation Options", "Pact of the Chain"),
        "Additionally, when you take the Attack action, you can forgo one of your own attacks to allow your familiar to make one attack of its own with its Reaction.",
    ),
    (
        ("Warlock", "Eldritch Invocation Options", "Pact of the Tome"),
        "#### Pact of the Tome",
    ),
    (
        ("Warlock", "Eldritch Invocation Options", "Pact of the Tome"),
        "Stitching together strands of shadow, you conjure forth a book in your hand at the end of a Short or Long Rest. This _Book of Shadows_ (you determine its appearance) contains eldritch magic that only you can access, granting you the benefits below. The book disappears if you conjure another book with this feature or if you die.",
    ),
    (
        ("Warlock", "Eldritch Invocation Options", "Pact of the Tome"),
        "_Cantrips and Rituals._ When the book appears, choose three cantrips, and choose two level 1 spells that have the Ritual tag. The spells can be from any class's spell list, and they must be spells you don't already have prepared. While the book is on your person, you have the chosen spells prepared, and they function as Warlock spells for you.",
    ),
    (
        ("Warlock", "Eldritch Invocation Options", "Pact of the Tome"),
        "_Spellcasting Focus._ You can use the book as a Spellcasting Focus.",
    ),
    (
        ("Warlock", "Eldritch Invocation Options", "Repelling Blast"),
        "#### Repelling Blast",
    ),
    (
        ("Warlock", "Eldritch Invocation Options", "Repelling Blast"),
        "_Prerequisite: Level 2+ Warlock, a Warlock Cantrip That Deals Damage via an Attack Roll_",
    ),
    (
        ("Warlock", "Eldritch Invocation Options", "Repelling Blast"),
        "Choose one of your known Warlock cantrips that requires an attack roll. When you hit a Large or smaller creature with that cantrip, you can push the creature up to 10 feet straight away from you.",
    ),
    (
        ("Warlock", "Eldritch Invocation Options", "Repelling Blast"),
        "_Repeatable._ You can gain this invocation more than once. Each time you do so, choose a different eligible cantrip.",
    ),
    (
        ("Warlock", "Eldritch Invocation Options", "Thirsting Blade"),
        "#### Thirsting Blade",
    ),
    (
        ("Warlock", "Eldritch Invocation Options", "Thirsting Blade"),
        "_Prerequisite: Level 5+ Warlock, Pact of the Blade Invocation_",
    ),
    (
        ("Warlock", "Eldritch Invocation Options", "Thirsting Blade"),
        "You gain the Extra Attack feature for your pact weapon only. With that feature, you can attack twice with the weapon instead of once when you take the Attack action on your turn.",
    ),
    (
        ("Warlock", "Eldritch Invocation Options", "Visions of Distant Realms"),
        "#### Visions of Distant Realms",
    ),
    (
        ("Warlock", "Eldritch Invocation Options", "Visions of Distant Realms"),
        "_Prerequisite: Level 9+ Warlock_",
    ),
    (
        ("Warlock", "Eldritch Invocation Options", "Visions of Distant Realms"),
        "You can cast _Arcane Eye_ without expending a spell slot.",
    ),
    (
        ("Warlock", "Eldritch Invocation Options", "Whispers of the Grave"),
        "#### Whispers of the Grave",
    ),
    (
        ("Warlock", "Eldritch Invocation Options", "Whispers of the Grave"),
        "_Prerequisite: Level 7+ Warlock_",
    ),
    (
        ("Warlock", "Eldritch Invocation Options", "Whispers of the Grave"),
        "You can cast _Speak with Dead_ without expending a spell slot.",
    ),
    (("Warlock", "Eldritch Invocation Options", "Witch Sight"), "#### Witch Sight"),
    (
        ("Warlock", "Eldritch Invocation Options", "Witch Sight"),
        "_Prerequisite: Level 15+ Warlock_",
    ),
    (
        ("Warlock", "Eldritch Invocation Options", "Witch Sight"),
        "You have Truesight with a range of 30 feet.",
    ),
    (("Warlock", "Warlock Spell List"), "### Warlock Spell List"),
    (
        ("Warlock", "Warlock Spell List"),
        "This section presents the Warlock spell list. The spells are organized by spell level and then alphabetized, and each spell's school of magic is listed. In the Special column, _C_ means the spell requires Concentration, _R_ means it's a Ritual, and _M_ means it requires a specific Material component.",
    ),
    (
        ("Warlock", "Warlock Spell List", "Cantrips (Level 0 Warlock Spells)"),
        "#### Cantrips (Level 0 Warlock Spells)",
    ),
    (
        ("Warlock", "Warlock Spell List", "Cantrips (Level 0 Warlock Spells)"),
        "<table>\n  <thead>\n    <tr>\n      <th>Spell</th>\n      <th>School</th>\n      <th>Special</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>Chill Touch</td>\n      <td>Necromancy</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Eldritch Blast</td>\n      <td>Evocation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Mage Hand</td>\n      <td>Conjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Minor Illusion</td>\n      <td>Illusion</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Poison Spray</td>\n      <td>Necromancy</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Prestidigitation</td>\n      <td>Transmutation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>True Strike</td>\n      <td>Divination</td>\n      <td>—</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        ("Warlock", "Warlock Spell List", "Level 1 Warlock Spells"),
        "#### Level 1 Warlock Spells",
    ),
    (
        ("Warlock", "Warlock Spell List", "Level 1 Warlock Spells"),
        "<table>\n  <thead>\n    <tr>\n      <th>Spell</th>\n      <th>School</th>\n      <th>Special</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>Bane</td>\n      <td>Enchantment</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Charm Person</td>\n      <td>Enchantment</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Comprehend Languages</td>\n      <td>Divination</td>\n      <td>R</td>\n    </tr>\n    <tr>\n      <td>Detect Magic</td>\n      <td>Divination</td>\n      <td>C, R</td>\n    </tr>\n    <tr>\n      <td>Expeditious Retreat</td>\n      <td>Transmutation</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Hellish Rebuke</td>\n      <td>Evocation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Hex</td>\n      <td>Enchantment</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Hideous Laughter</td>\n      <td>Enchantment</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Illusory Script</td>\n      <td>Illusion</td>\n      <td>R, M</td>\n    </tr>\n    <tr>\n      <td>Protection from Evil and Good</td>\n      <td>Abjuration</td>\n      <td>C, M</td>\n    </tr>\n    <tr>\n      <td>Speak with Animals</td>\n      <td>Divination</td>\n      <td>R</td>\n    </tr>\n    <tr>\n      <td>Unseen Servant</td>\n      <td>Conjuration</td>\n      <td>R</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        ("Warlock", "Warlock Spell List", "Level 2 Warlock Spells"),
        "#### Level 2 Warlock Spells",
    ),
    (
        ("Warlock", "Warlock Spell List", "Level 2 Warlock Spells"),
        "<table>\n  <thead>\n    <tr>\n      <th>Spell</th>\n      <th>School</th>\n      <th>Special</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>Darkness</td>\n      <td>Evocation</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Enthrall</td>\n      <td>Enchantment</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Hold Person</td>\n      <td>Enchantment</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Invisibility</td>\n      <td>Illusion</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Mind Spike</td>\n      <td>Divination</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Mirror Image</td>\n      <td>Illusion</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Misty Step</td>\n      <td>Conjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Ray of Enfeeblement</td>\n      <td>Necromancy</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Spider Climb</td>\n      <td>Transmutation</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Suggestion</td>\n      <td>Enchantment</td>\n      <td>C</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        ("Warlock", "Warlock Spell List", "Level 3 Warlock Spells"),
        "#### Level 3 Warlock Spells",
    ),
    (
        ("Warlock", "Warlock Spell List", "Level 3 Warlock Spells"),
        "<table>\n  <thead>\n    <tr>\n      <th>Spell</th>\n      <th>School</th>\n      <th>Special</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>Counterspell</td>\n      <td>Abjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Dispel Magic</td>\n      <td>Abjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Fear</td>\n      <td>Illusion</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Fly</td>\n      <td>Transmutation</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Gaseous Form</td>\n      <td>Transmutation</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Hypnotic Pattern</td>\n      <td>Illusion</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Magic Circle</td>\n      <td>Abjuration</td>\n      <td>M</td>\n    </tr>\n    <tr>\n      <td>Major Image</td>\n      <td>Illusion</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Remove Curse</td>\n      <td>Abjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Tongues</td>\n      <td>Divination</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Vampiric Touch</td>\n      <td>Necromancy</td>\n      <td>C</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        ("Warlock", "Warlock Spell List", "Level 4 Warlock Spells"),
        "#### Level 4 Warlock Spells",
    ),
    (
        ("Warlock", "Warlock Spell List", "Level 4 Warlock Spells"),
        "<table>\n  <thead>\n    <tr>\n      <th>Spell</th>\n      <th>School</th>\n      <th>Special</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>Banishment</td>\n      <td>Abjuration</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Blight</td>\n      <td>Necromancy</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Charm Monster</td>\n      <td>Enchantment</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Dimension Door</td>\n      <td>Conjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Hallucinatory Terrain</td>\n      <td>Illusion</td>\n      <td>—</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        ("Warlock", "Warlock Spell List", "Level 5 Warlock Spells"),
        "#### Level 5 Warlock Spells",
    ),
    (
        ("Warlock", "Warlock Spell List", "Level 5 Warlock Spells"),
        "<table>\n  <thead>\n    <tr>\n      <th>Spell</th>\n      <th>School</th>\n      <th>Special</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>Contact Other Plane</td>\n      <td>Divination</td>\n      <td>R</td>\n    </tr>\n    <tr>\n      <td>Dream</td>\n      <td>Illusion</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Hold Monster</td>\n      <td>Enchantment</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Mislead</td>\n      <td>Illusion</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Planar Binding</td>\n      <td>Abjuration</td>\n      <td>M</td>\n    </tr>\n    <tr>\n      <td>Scrying</td>\n      <td>Divination</td>\n      <td>C, M</td>\n    </tr>\n    <tr>\n      <td>Teleportation Circle</td>\n      <td>Conjuration</td>\n      <td>M</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        ("Warlock", "Warlock Spell List", "Level 6 Warlock Spells"),
        "#### Level 6 Warlock Spells",
    ),
    (
        ("Warlock", "Warlock Spell List", "Level 6 Warlock Spells"),
        "<table>\n  <thead>\n    <tr>\n      <th>Spell</th>\n      <th>School</th>\n      <th>Special</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>Circle of Death</td>\n      <td>Necromancy</td>\n      <td>M</td>\n    </tr>\n    <tr>\n      <td>Create Undead</td>\n      <td>Necromancy</td>\n      <td>M</td>\n    </tr>\n    <tr>\n      <td>Eyebite</td>\n      <td>Necromancy</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>True Seeing</td>\n      <td>Divination</td>\n      <td>M</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        ("Warlock", "Warlock Spell List", "Level 7 Warlock Spells"),
        "#### Level 7 Warlock Spells",
    ),
    (
        ("Warlock", "Warlock Spell List", "Level 7 Warlock Spells"),
        "<table>\n  <thead>\n    <tr>\n      <th>Spell</th>\n      <th>School</th>\n      <th>Special</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>Etherealness</td>\n      <td>Conjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Finger of Death</td>\n      <td>Necromancy</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Forcecage</td>\n      <td>Evocation</td>\n      <td>C, M</td>\n    </tr>\n    <tr>\n      <td>Plane Shift</td>\n      <td>Conjuration</td>\n      <td>M</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        ("Warlock", "Warlock Spell List", "Level 8 Warlock Spells"),
        "#### Level 8 Warlock Spells",
    ),
    (
        ("Warlock", "Warlock Spell List", "Level 8 Warlock Spells"),
        "<table>\n  <thead>\n    <tr>\n      <th>Spell</th>\n      <th>School</th>\n      <th>Special</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>Befuddlement</td>\n      <td>Enchantment</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Demiplane</td>\n      <td>Conjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Dominate Monster</td>\n      <td>Enchantment</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Glibness</td>\n      <td>Enchantment</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Power Word Stun</td>\n      <td>Enchantment</td>\n      <td>—</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        ("Warlock", "Warlock Spell List", "Level 9 Warlock Spells"),
        "#### Level 9 Warlock Spells",
    ),
    (
        ("Warlock", "Warlock Spell List", "Level 9 Warlock Spells"),
        "<table>\n  <thead>\n    <tr>\n      <th>Spell</th>\n      <th>School</th>\n      <th>Special</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>Astral Projection</td>\n      <td>Necromancy</td>\n      <td>M</td>\n    </tr>\n    <tr>\n      <td>Foresight</td>\n      <td>Divination</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Gate</td>\n      <td>Conjuration</td>\n      <td>C, M</td>\n    </tr>\n    <tr>\n      <td>Imprisonment</td>\n      <td>Abjuration</td>\n      <td>M</td>\n    </tr>\n    <tr>\n      <td>Power Word Kill</td>\n      <td>Enchantment</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>True Polymorph</td>\n      <td>Transmutation</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Weird</td>\n      <td>Illusion</td>\n      <td>C</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        ("Warlock", "Warlock Subclass: Fiend Patron"),
        "### Warlock Subclass: Fiend Patron",
    ),
    (
        ("Warlock", "Warlock Subclass: Fiend Patron"),
        "_Make a Deal with the Lower Planes_",
    ),
    (
        ("Warlock", "Warlock Subclass: Fiend Patron"),
        "Your pact draws on the Lower Planes, the realms of perdition. You might forge a bargain with a demon lord, an archdevil, or another fiend that is especially mighty. That patron's aims are evil—the corruption or destruction of all things, ultimately including you—and your path is defined by the extent to which you strive against those aims.",
    ),
    (
        ("Warlock", "Warlock Subclass: Fiend Patron", "Level 3: Dark One's Blessing"),
        "#### Level 3: Dark One's Blessing",
    ),
    (
        ("Warlock", "Warlock Subclass: Fiend Patron", "Level 3: Dark One's Blessing"),
        "When you reduce an enemy to 0 Hit Points, you gain Temporary Hit Points equal to your Charisma modifier plus your Warlock level (minimum of 1 Temporary Hit Point). You also gain this benefit if someone else reduces an enemy within 10 feet of you to 0 Hit Points.",
    ),
    (
        ("Warlock", "Warlock Subclass: Fiend Patron", "Level 3: Fiend Spells"),
        "#### Level 3: Fiend Spells",
    ),
    (
        ("Warlock", "Warlock Subclass: Fiend Patron", "Level 3: Fiend Spells"),
        "The magic of your patron ensures you always have certain spells ready; when you reach a Warlock level specified in the Fiend Spells table, you thereafter always have the listed spells prepared.",
    ),
    (
        ("Warlock", "Warlock Subclass: Fiend Patron", "Level 3: Fiend Spells"),
        "**Fiend Spells**\n\n<table>\n  <thead>\n    <tr>\n      <th>Warlock Level</th>\n      <th>Spells</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>3</td>\n      <td>Burning Hands, Command, Scorching Ray, Suggestion</td>\n    </tr>\n    <tr>\n      <td>5</td>\n      <td>Fireball, Stinking Cloud</td>\n    </tr>\n    <tr>\n      <td>7</td>\n      <td>Fire Shield, Wall of Fire</td>\n    </tr>\n    <tr>\n      <td>9</td>\n      <td>Geas, Insect Plague</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        ("Warlock", "Warlock Subclass: Fiend Patron", "Level 6: Dark One's Own Luck"),
        "#### Level 6: Dark One's Own Luck",
    ),
    (
        ("Warlock", "Warlock Subclass: Fiend Patron", "Level 6: Dark One's Own Luck"),
        "You can call on your fiendish patron to alter fate in your favor. When you make an ability check or a saving throw, you can use this feature to add 1d10 to your roll. You can do so after seeing the roll but before any of the roll's effects occur.",
    ),
    (
        ("Warlock", "Warlock Subclass: Fiend Patron", "Level 6: Dark One's Own Luck"),
        "You can use this feature a number of times equal to your Charisma modifier (minimum of once), but you can use it no more than once per roll. You regain all expended uses when you finish a Long Rest.",
    ),
    (
        ("Warlock", "Warlock Subclass: Fiend Patron", "Level 10: Fiendish Resilience"),
        "#### Level 10: Fiendish Resilience",
    ),
    (
        ("Warlock", "Warlock Subclass: Fiend Patron", "Level 10: Fiendish Resilience"),
        "Choose one damage type, other than Force, whenever you finish a Short or Long Rest. You have Resistance to that damage type until you choose a different one with this feature.",
    ),
    (
        ("Warlock", "Warlock Subclass: Fiend Patron", "Level 14: Hurl Through Hell"),
        "#### Level 14: Hurl Through Hell",
    ),
    (
        ("Warlock", "Warlock Subclass: Fiend Patron", "Level 14: Hurl Through Hell"),
        "Once per turn when you hit a creature with an attack roll, you can try to instantly transport the target through the Lower Planes. The target must succeed on a Charisma saving throw against your spell save DC, or the target disappears and hurtles through a nightmare landscape. The target takes 8d10 Psychic damage if it isn't a Fiend, and it has the Incapacitated condition until the end of your next turn, when it returns to the space it previously occupied or the nearest unoccupied space.",
    ),
    (
        ("Warlock", "Warlock Subclass: Fiend Patron", "Level 14: Hurl Through Hell"),
        "Once you use this feature, you can't use it again until you finish a Long Rest unless you expend a Pact Magic spell slot (no action required) to restore your use of it.",
    ),
    (("Wizard",), "## Wizard"),
    (
        ("Wizard",),
        "**Core Wizard Traits**\n\n<table>\n  <tbody>\n    <tr>\n      <td>Primary Ability</td>\n      <td>Intelligence</td>\n    </tr>\n    <tr>\n      <td>Hit Point Die</td>\n      <td>D6 per Wizard level</td>\n    </tr>\n    <tr>\n      <td>Saving Throw Proficiencies</td>\n      <td>Intelligence and Wisdom</td>\n    </tr>\n    <tr>\n      <td>Skill Proficiencies</td>\n      <td>Choose 2: Arcana, History, Insight, Investigation, Medicine, Nature, or Religion</td>\n    </tr>\n    <tr>\n      <td>Weapon Proficiencies</td>\n      <td>Simple weapons</td>\n    </tr>\n    <tr>\n      <td>Armor Training</td>\n      <td>None</td>\n    </tr>\n    <tr>\n      <td>Starting Equipment</td>\n      <td>Choose A or B: (A) 2 Daggers, Arcane Focus (Quarterstaff), Robe, Spellbook, Scholar's Pack, and 5 GP; or (B) 55 GP</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (("Wizard", "Becoming a Wizard …"), "### Becoming a Wizard …"),
    (
        ("Wizard", "Becoming a Wizard …", "As a Level 1 Character"),
        "#### As a Level 1 Character",
    ),
    (
        ("Wizard", "Becoming a Wizard …", "As a Level 1 Character"),
        "• Gain all the traits in the Core Wizard Traits table.\n• Gain the Wizard's level 1 features, which are listed in the Wizard Features table.",
    ),
    (
        ("Wizard", "Becoming a Wizard …", "As a Multiclass Character"),
        "#### As a Multiclass Character",
    ),
    (
        ("Wizard", "Becoming a Wizard …", "As a Multiclass Character"),
        '• Gain the Hit Point Die from the Core Wizard Traits table.\n• Gain the Wizard\'s level 1 features, which are listed in the Wizard Features table. See the multiclassing rules in "Character Creation" to determine your available spell slots.',
    ),
    (("Wizard", "Wizard Class Features"), "### Wizard Class Features"),
    (
        ("Wizard", "Wizard Class Features"),
        "As a Wizard, you gain the following class features when you reach the specified Wizard levels. These features are listed in the Wizard Features table.",
    ),
    (
        ("Wizard", "Wizard Class Features"),
        '**Wizard Features**\n\n<table>\n  <thead>\n    <tr>\n      <th>Level</th>\n      <th>Proficiency Bonus</th>\n      <th>Class Features</th>\n      <th>Cantrips</th>\n      <th>Prepared Spells</th>\n      <th colspan="9">——Spell Slots per Spell Level——</th>\n    </tr>\n    <tr>\n      <th>\n      </th>\n      <th>\n      </th>\n      <th>\n      </th>\n      <th>\n      </th>\n      <th>\n      </th>\n      <th>1</th>\n      <th>2</th>\n      <th>3</th>\n      <th>4</th>\n      <th>5</th>\n      <th>6</th>\n      <th>7</th>\n      <th>8</th>\n      <th>9</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>1</td>\n      <td>+2</td>\n      <td>Spellcasting, Ritual Adept, Arcane Recovery</td>\n      <td>3</td>\n      <td>4</td>\n      <td>2</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>2</td>\n      <td>+2</td>\n      <td>Scholar</td>\n      <td>3</td>\n      <td>5</td>\n      <td>3</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>3</td>\n      <td>+2</td>\n      <td>Wizard Subclass</td>\n      <td>3</td>\n      <td>6</td>\n      <td>4</td>\n      <td>2</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>4</td>\n      <td>+2</td>\n      <td>Ability Score Improvement</td>\n      <td>4</td>\n      <td>7</td>\n      <td>4</td>\n      <td>3</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>5</td>\n      <td>+3</td>\n      <td>Memorize Spell</td>\n      <td>4</td>\n      <td>9</td>\n      <td>4</td>\n      <td>3</td>\n      <td>2</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>6</td>\n      <td>+3</td>\n      <td>Subclass feature</td>\n      <td>4</td>\n      <td>10</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>7</td>\n      <td>+3</td>\n      <td>—</td>\n      <td>4</td>\n      <td>11</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>1</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>8</td>\n      <td>+3</td>\n      <td>Ability Score Improvement</td>\n      <td>4</td>\n      <td>12</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>2</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>9</td>\n      <td>+4</td>\n      <td>—</td>\n      <td>4</td>\n      <td>14</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>3</td>\n      <td>1</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>10</td>\n      <td>+4</td>\n      <td>Subclass feature</td>\n      <td>5</td>\n      <td>15</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>3</td>\n      <td>2</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>11</td>\n      <td>+4</td>\n      <td>—</td>\n      <td>5</td>\n      <td>16</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>3</td>\n      <td>2</td>\n      <td>1</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>12</td>\n      <td>+4</td>\n      <td>Ability Score Improvement</td>\n      <td>5</td>\n      <td>16</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>3</td>\n      <td>2</td>\n      <td>1</td>\n      <td>—</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>13</td>\n      <td>+5</td>\n      <td>—</td>\n      <td>5</td>\n      <td>17</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>3</td>\n      <td>2</td>\n      <td>1</td>\n      <td>1</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>14</td>\n      <td>+5</td>\n      <td>Subclass feature</td>\n      <td>5</td>\n      <td>18</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>3</td>\n      <td>2</td>\n      <td>1</td>\n      <td>1</td>\n      <td>—</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>15</td>\n      <td>+5</td>\n      <td>—</td>\n      <td>5</td>\n      <td>19</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>3</td>\n      <td>2</td>\n      <td>1</td>\n      <td>1</td>\n      <td>1</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>16</td>\n      <td>+5</td>\n      <td>Ability Score Improvement</td>\n      <td>5</td>\n      <td>21</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>3</td>\n      <td>2</td>\n      <td>1</td>\n      <td>1</td>\n      <td>1</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>17</td>\n      <td>+6</td>\n      <td>—</td>\n      <td>5</td>\n      <td>22</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>3</td>\n      <td>2</td>\n      <td>1</td>\n      <td>1</td>\n      <td>1</td>\n      <td>1</td>\n    </tr>\n    <tr>\n      <td>18</td>\n      <td>+6</td>\n      <td>Spell Mastery</td>\n      <td>5</td>\n      <td>23</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>3</td>\n      <td>3</td>\n      <td>1</td>\n      <td>1</td>\n      <td>1</td>\n      <td>1</td>\n    </tr>\n    <tr>\n      <td>19</td>\n      <td>+6</td>\n      <td>Epic Boon</td>\n      <td>5</td>\n      <td>24</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>3</td>\n      <td>3</td>\n      <td>2</td>\n      <td>1</td>\n      <td>1</td>\n      <td>1</td>\n    </tr>\n    <tr>\n      <td>20</td>\n      <td>+6</td>\n      <td>Signature Spells</td>\n      <td>5</td>\n      <td>25</td>\n      <td>4</td>\n      <td>3</td>\n      <td>3</td>\n      <td>3</td>\n      <td>3</td>\n      <td>2</td>\n      <td>2</td>\n      <td>1</td>\n      <td>1</td>\n    </tr>\n  </tbody>\n</table>',
    ),
    (
        ("Wizard", "Wizard Class Features", "Level 1: Spellcasting"),
        "#### Level 1: Spellcasting",
    ),
    (
        ("Wizard", "Wizard Class Features", "Level 1: Spellcasting"),
        'As a student of arcane magic, you have learned to cast spells. See "Spells" for the rules on spellcasting. The information below details how you use those rules with Wizard spells, which appear in the Wizard spell list later in the class\'s description.',
    ),
    (
        ("Wizard", "Wizard Class Features", "Level 1: Spellcasting"),
        "_Cantrips._ You know three Wizard cantrips of your choice. _Light_, _Mage Hand_, and _Ray of Frost_ are recommended. Whenever you finish a Long Rest, you can replace one of your cantrips from this feature with another Wizard cantrip of your choice.",
    ),
    (
        ("Wizard", "Wizard Class Features", "Level 1: Spellcasting"),
        "When you reach Wizard levels 4 and 10, you learn another Wizard cantrip of your choice, as shown in the Cantrips column of the Wizard Features table.",
    ),
    (
        ("Wizard", "Wizard Class Features", "Level 1: Spellcasting"),
        "_Spellbook._ Your wizardly apprenticeship culminated in the creation of a unique book: your spellbook. It is a Tiny object that weighs 3 pounds, contains 100 pages, and can be read only by you or someone casting _Identify_. You determine the book's appearance and materials, such as a gilt-edged tome or a collection of vellum bound with twine.",
    ),
    (
        ("Wizard", "Wizard Class Features", "Level 1: Spellcasting"),
        "The book contains the level 1+ spells you know. It starts with six level 1 Wizard spells of your choice. _Detect Magic_, _Feather Fall_, _Mage Armor_, _Magic Missile_, _Sleep_, and _Thunderwave_ are recommended.",
    ),
    (
        ("Wizard", "Wizard Class Features", "Level 1: Spellcasting"),
        "Whenever you gain a Wizard level after 1, add two Wizard spells of your choice to your spellbook. Each of these spells must be of a level for which you have spell slots, as shown in the Wizard Features table. The spells are the culmination of arcane research you do regularly.",
    ),
    (
        ("Wizard", "Wizard Class Features", "Level 1: Spellcasting"),
        "_Spell Slots._ The Wizard Features table shows how many spell slots you have to cast your level 1+ spells. You regain all expended slots when you finish a Long Rest.",
    ),
    (
        ("Wizard", "Wizard Class Features", "Level 1: Spellcasting"),
        "_Prepared Spells of Level 1+._ You prepare the list of level 1+ spells that are available for you to cast with this feature. To do so, choose four spells from your spellbook. The chosen spells must be of a level for which you have spell slots.",
    ),
    (
        ("Wizard", "Wizard Class Features", "Level 1: Spellcasting"),
        "The number of spells on your list increases as you gain Wizard levels, as shown in the Prepared Spells column of the Wizard Features table. Whenever that number increases, choose additional Wizard spells until the number of spells on your list matches the number in the table. The chosen spells must be of a level for which you have spell slots. For example, if you're a level 3 Wizard, your list of prepared spells can include six spells of levels 1 and 2 in any combination, chosen from your spellbook.",
    ),
    (
        ("Wizard", "Wizard Class Features", "Level 1: Spellcasting"),
        "If another Wizard feature gives you spells that you always have prepared, those spells don't count against the number of spells you can prepare with this feature, but those spells otherwise count as Wizard spells for you.",
    ),
    (
        ("Wizard", "Wizard Class Features", "Level 1: Spellcasting"),
        "_Changing Your Prepared Spells._ Whenever you finish a Long Rest, you can change your list of prepared spells, replacing any of the spells there with spells from your spellbook.",
    ),
    (
        ("Wizard", "Wizard Class Features", "Level 1: Spellcasting"),
        "_Spellcasting Ability._ Intelligence is your spellcasting ability for your Wizard spells.",
    ),
    (
        ("Wizard", "Wizard Class Features", "Level 1: Spellcasting"),
        "_Spellcasting Focus._ You can use an Arcane Focus or your spellbook as a Spellcasting Focus for your Wizard spells.",
    ),
    (
        ("Wizard", "Wizard Class Features", "Level 1: Ritual Adept"),
        "#### Level 1: Ritual Adept",
    ),
    (
        ("Wizard", "Wizard Class Features", "Level 1: Ritual Adept"),
        "You can cast any spell as a Ritual if that spell has the Ritual tag and the spell is in your spellbook. You needn't have the spell prepared, but you must read from the book to cast a spell in this way.",
    ),
    (
        ("Wizard", "Wizard Class Features", "Level 1: Arcane Recovery"),
        "#### Level 1: Arcane Recovery",
    ),
    (
        ("Wizard", "Wizard Class Features", "Level 1: Arcane Recovery"),
        "You can regain some of your magical energy by studying your spellbook. When you finish a Short Rest, you can choose expended spell slots to recover. The spell slots can have a combined level equal to no more than half your Wizard level (round up), and none of the slots can be level 6 or higher. For example, if you're a level 4 Wizard, you can recover up to two levels' worth of spell slots, regaining either one level 2 spell slot or two level 1 spell slots.",
    ),
    (
        ("Wizard", "Wizard Class Features", "Level 1: Arcane Recovery"),
        "Once you use this feature, you can't do so again until you finish a Long Rest.",
    ),
    (("Wizard", "Wizard Class Features", "Level 2: Scholar"), "#### Level 2: Scholar"),
    (
        ("Wizard", "Wizard Class Features", "Level 2: Scholar"),
        "While studying magic, you also specialized in another field of study. Choose one of the following skills in which you have proficiency: Arcana, History, Investigation, Medicine, Nature, or Religion. You have Expertise in the chosen skill.",
    ),
    (
        ("Wizard", "Wizard Class Features", "Level 3: Wizard Subclass"),
        "#### Level 3: Wizard Subclass",
    ),
    (
        ("Wizard", "Wizard Class Features", "Level 3: Wizard Subclass"),
        "You gain a Wizard subclass of your choice. The Evoker subclass is detailed after this class's description. A subclass is a specialization that grants you features at certain Wizard levels. For the rest of your career, you gain each of your subclass's features that are of your Wizard level or lower.",
    ),
    (
        ("Wizard", "Wizard Class Features", "Level 3: Wizard Subclass"),
        "> **Expanding and Replacing a Spellbook**\n>\n> The spells you add to your spellbook as you gain levels reflect your ongoing magical research, but you might find other spells during your adventures that you can add to the book. You could discover a Wizard spell on a _Spell Scroll_, for example, and then copy it into your spellbook.\n>\n> _Copying a Spell into the Book._ When you find a level 1+ Wizard spell, you can copy it into your spellbook if it's of a level you can prepare and if you have time to copy it. For each level of the spell, the transcription takes 2 hours and costs 50 GP. Afterward you can prepare the spell like the other spells in your spellbook.\n>\n> _Copying the Book._ You can copy a spell from your spellbook into another book. This is like copying a new spell into your spellbook but faster, since you already know how to cast the spell. You need spend only 1 hour and 10 GP for each level of the copied spell.\n>\n> If you lose your spellbook, you can use the same procedure to transcribe the Wizard spells that you have prepared into a new spellbook. Filling out the remainder of the new book requires you to find new spells to do so. For this reason, many wizards keep a backup spellbook.",
    ),
    (
        ("Wizard", "Wizard Class Features", "Level 4: Ability Score Improvement"),
        "#### Level 4: Ability Score Improvement",
    ),
    (
        ("Wizard", "Wizard Class Features", "Level 4: Ability Score Improvement"),
        'You gain the Ability Score Improvement feat (see "Feats") or another feat of your choice for which you qualify. You gain this feature again at Wizard levels 8, 12, and 16.',
    ),
    (
        ("Wizard", "Wizard Class Features", "Level 5: Memorize Spell"),
        "#### Level 5: Memorize Spell",
    ),
    (
        ("Wizard", "Wizard Class Features", "Level 5: Memorize Spell"),
        "Whenever you finish a Short Rest, you can study your spellbook and replace one of the level 1+ Wizard spells you have prepared for your Spellcasting feature with another level 1+ spell from the book.",
    ),
    (
        ("Wizard", "Wizard Class Features", "Level 18: Spell Mastery"),
        "#### Level 18: Spell Mastery",
    ),
    (
        ("Wizard", "Wizard Class Features", "Level 18: Spell Mastery"),
        "You have achieved such mastery over certain spells that you can cast them at will. Choose a level 1 and a level 2 spell in your spellbook that have a casting time of an action. You always have those spells prepared, and you can cast them at their lowest level without expending a spell slot. To cast either spell at a higher level, you must expend a spell slot.",
    ),
    (
        ("Wizard", "Wizard Class Features", "Level 18: Spell Mastery"),
        "Whenever you finish a Long Rest, you can study your spellbook and replace one of those spells with an eligible spell of the same level from the book.",
    ),
    (
        ("Wizard", "Wizard Class Features", "Level 19: Epic Boon"),
        "#### Level 19: Epic Boon",
    ),
    (
        ("Wizard", "Wizard Class Features", "Level 19: Epic Boon"),
        'You gain an Epic Boon feat (see "Feats") or another feat of your choice for which you qualify. Boon of Spell Recall is recommended.',
    ),
    (
        ("Wizard", "Wizard Class Features", "Level 20: Signature Spells"),
        "#### Level 20: Signature Spells",
    ),
    (
        ("Wizard", "Wizard Class Features", "Level 20: Signature Spells"),
        "Choose two level 3 spells in your spellbook as your signature spells. You always have these spells prepared, and you can cast each of them once at level 3 without expending a spell slot. When you do so, you can't cast them in this way again until you finish a Short or Long Rest. To cast either spell at a higher level, you must expend a spell slot.",
    ),
    (("Wizard", "Wizard Spell List"), "### Wizard Spell List"),
    (
        ("Wizard", "Wizard Spell List"),
        "This section presents the Wizard spell list. The spells are organized by spell level and then alphabetized, and each spell's school of magic is listed. In the Special column, C means the spell requires Concentration, R means it's a Ritual, and M means it requires a specific Material component.",
    ),
    (
        ("Wizard", "Wizard Spell List", "Cantrips (Level 0 Wizard Spells)"),
        "#### Cantrips (Level 0 Wizard Spells)",
    ),
    (
        ("Wizard", "Wizard Spell List", "Cantrips (Level 0 Wizard Spells)"),
        "<table>\n  <thead>\n    <tr>\n      <th>Spell</th>\n      <th>School</th>\n      <th>Special</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>Acid Splash</td>\n      <td>Evocation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Chill Touch</td>\n      <td>Necromancy</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Dancing Lights</td>\n      <td>Illusion</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Elementalism</td>\n      <td>Transmutation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Fire Bolt</td>\n      <td>Evocation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Light</td>\n      <td>Evocation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Mage Hand</td>\n      <td>Conjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Mending</td>\n      <td>Transmutation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Message</td>\n      <td>Transmutation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Minor Illusion</td>\n      <td>Illusion</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Poison Spray</td>\n      <td>Necromancy</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Prestidigitation</td>\n      <td>Transmutation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Ray of Frost</td>\n      <td>Evocation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Shocking Grasp</td>\n      <td>Evocation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>True Strike</td>\n      <td>Divination</td>\n      <td>—</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        ("Wizard", "Wizard Spell List", "Level 1 Wizard Spells"),
        "#### Level 1 Wizard Spells",
    ),
    (
        ("Wizard", "Wizard Spell List", "Level 1 Wizard Spells"),
        "<table>\n  <thead>\n    <tr>\n      <th>Spell</th>\n      <th>School</th>\n      <th>Special</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>Alarm</td>\n      <td>Abjuration</td>\n      <td>R</td>\n    </tr>\n    <tr>\n      <td>Burning Hands</td>\n      <td>Evocation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Charm Person</td>\n      <td>Enchantment</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Chromatic Orb</td>\n      <td>Evocation</td>\n      <td>M</td>\n    </tr>\n    <tr>\n      <td>Color Spray</td>\n      <td>Illusion</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Comprehend Languages</td>\n      <td>Divination</td>\n      <td>R</td>\n    </tr>\n    <tr>\n      <td>Detect Magic</td>\n      <td>Divination</td>\n      <td>C, R</td>\n    </tr>\n    <tr>\n      <td>Disguise Self</td>\n      <td>Illusion</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Expeditious Retreat</td>\n      <td>Transmutation</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>False Life</td>\n      <td>Necromancy</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Feather Fall</td>\n      <td>Transmutation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Find Familiar</td>\n      <td>Conjuration</td>\n      <td>R, M</td>\n    </tr>\n    <tr>\n      <td>Floating Disk</td>\n      <td>Conjuration</td>\n      <td>R</td>\n    </tr>\n    <tr>\n      <td>Fog Cloud</td>\n      <td>Conjuration</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Grease</td>\n      <td>Conjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Hideous Laughter</td>\n      <td>Enchantment</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Ice Knife</td>\n      <td>Conjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Identify</td>\n      <td>Divination</td>\n      <td>R, M</td>\n    </tr>\n    <tr>\n      <td>Illusory Script</td>\n      <td>Illusion</td>\n      <td>R, M</td>\n    </tr>\n    <tr>\n      <td>Jump</td>\n      <td>Transmutation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Longstrider</td>\n      <td>Transmutation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Mage Armor</td>\n      <td>Abjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Magic Missile</td>\n      <td>Evocation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Protection from Evil and Good</td>\n      <td>Abjuration</td>\n      <td>C, M</td>\n    </tr>\n    <tr>\n      <td>Ray of Sickness</td>\n      <td>Necromancy</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Shield</td>\n      <td>Abjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Silent Image</td>\n      <td>Illusion</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Sleep</td>\n      <td>Enchantment</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Thunderwave</td>\n      <td>Evocation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Unseen Servant</td>\n      <td>Conjuration</td>\n      <td>R</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        ("Wizard", "Wizard Spell List", "Level 2 Wizard Spells"),
        "#### Level 2 Wizard Spells",
    ),
    (
        ("Wizard", "Wizard Spell List", "Level 2 Wizard Spells"),
        "<table>\n  <thead>\n    <tr>\n      <th>Spell</th>\n      <th>School</th>\n      <th>Special</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>Acid Arrow</td>\n      <td>Evocation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Alter Self</td>\n      <td>Transmutation</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Arcane Lock</td>\n      <td>Abjuration</td>\n      <td>M</td>\n    </tr>\n    <tr>\n      <td>Arcanist's Magic Aura</td>\n      <td>Illusion</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Augury</td>\n      <td>Divination</td>\n      <td>R, M</td>\n    </tr>\n    <tr>\n      <td>Blindness/Deafness</td>\n      <td>Transmutation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Blur</td>\n      <td>Illusion</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Continual Flame</td>\n      <td>Evocation</td>\n      <td>M</td>\n    </tr>\n    <tr>\n      <td>Darkness</td>\n      <td>Evocation</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Darkvision</td>\n      <td>Transmutation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Detect Thoughts</td>\n      <td>Divination</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Dragon's Breath</td>\n      <td>Transmutation</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Enhance Ability</td>\n      <td>Transmutation</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Enlarge/Reduce</td>\n      <td>Transmutation</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Flaming Sphere</td>\n      <td>Conjuration</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Gentle Repose</td>\n      <td>Necromancy</td>\n      <td>R, M</td>\n    </tr>\n    <tr>\n      <td>Gust of Wind</td>\n      <td>Evocation</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Hold Person</td>\n      <td>Enchantment</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Invisibility</td>\n      <td>Illusion</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Knock</td>\n      <td>Transmutation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Levitate</td>\n      <td>Transmutation</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Locate Object</td>\n      <td>Divination</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Magic Mouth</td>\n      <td>Illusion</td>\n      <td>R, M</td>\n    </tr>\n    <tr>\n      <td>Magic Weapon</td>\n      <td>Transmutation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Mind Spike</td>\n      <td>Divination</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Mirror Image</td>\n      <td>Illusion</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Misty Step</td>\n      <td>Conjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Phantasmal Force</td>\n      <td>Illusion</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Ray of Enfeeblement</td>\n      <td>Necromancy</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Rope Trick</td>\n      <td>Transmutation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Scorching Ray</td>\n      <td>Evocation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>See Invisibility</td>\n      <td>Divination</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Shatter</td>\n      <td>Evocation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Spider Climb</td>\n      <td>Transmutation</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Suggestion</td>\n      <td>Enchantment</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Web</td>\n      <td>Conjuration</td>\n      <td>C</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        ("Wizard", "Wizard Spell List", "Level 3 Wizard Spells"),
        "#### Level 3 Wizard Spells",
    ),
    (
        ("Wizard", "Wizard Spell List", "Level 3 Wizard Spells"),
        "<table>\n  <thead>\n    <tr>\n      <th>Spell</th>\n      <th>School</th>\n      <th>Special</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>Animate Dead</td>\n      <td>Necromancy</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Bestow Curse</td>\n      <td>Necromancy</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Blink</td>\n      <td>Transmutation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Clairvoyance</td>\n      <td>Divination</td>\n      <td>C, M</td>\n    </tr>\n    <tr>\n      <td>Counterspell</td>\n      <td>Abjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Dispel Magic</td>\n      <td>Abjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Fear</td>\n      <td>Illusion</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Fireball</td>\n      <td>Evocation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Fly</td>\n      <td>Transmutation</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Gaseous Form</td>\n      <td>Transmutation</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Glyph of Warding</td>\n      <td>Abjuration</td>\n      <td>M</td>\n    </tr>\n    <tr>\n      <td>Haste</td>\n      <td>Transmutation</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Hypnotic Pattern</td>\n      <td>Illusion</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Lightning Bolt</td>\n      <td>Evocation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Magic Circle</td>\n      <td>Abjuration</td>\n      <td>M</td>\n    </tr>\n    <tr>\n      <td>Major Image</td>\n      <td>Illusion</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Nondetection</td>\n      <td>Abjuration</td>\n      <td>M</td>\n    </tr>\n    <tr>\n      <td>Phantom Steed</td>\n      <td>Illusion</td>\n      <td>R</td>\n    </tr>\n    <tr>\n      <td>Protection from Energy</td>\n      <td>Abjuration</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Remove Curse</td>\n      <td>Abjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Sending</td>\n      <td>Divination</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Sleet Storm</td>\n      <td>Conjuration</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Slow</td>\n      <td>Transmutation</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Speak with Dead</td>\n      <td>Necromancy</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Stinking Cloud</td>\n      <td>Conjuration</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Tiny Hut</td>\n      <td>Evocation</td>\n      <td>R</td>\n    </tr>\n    <tr>\n      <td>Tongues</td>\n      <td>Divination</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Vampiric Touch</td>\n      <td>Necromancy</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Water Breathing</td>\n      <td>Transmutation</td>\n      <td>R</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        ("Wizard", "Wizard Spell List", "Level 4 Wizard Spells"),
        "#### Level 4 Wizard Spells",
    ),
    (
        ("Wizard", "Wizard Spell List", "Level 4 Wizard Spells"),
        "<table>\n  <thead>\n    <tr>\n      <th>Spell</th>\n      <th>School</th>\n      <th>Special</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>Arcane Eye</td>\n      <td>Divination</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Banishment</td>\n      <td>Abjuration</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Black Tentacles</td>\n      <td>Conjuration</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Blight</td>\n      <td>Necromancy</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Charm Monster</td>\n      <td>Enchantment</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Confusion</td>\n      <td>Enchantment</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Conjure Minor Elementals</td>\n      <td>Conjuration</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Control Water</td>\n      <td>Transmutation</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Dimension Door</td>\n      <td>Conjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Divination</td>\n      <td>Divination</td>\n      <td>R, M</td>\n    </tr>\n    <tr>\n      <td>Fabricate</td>\n      <td>Transmutation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Faithful Hound</td>\n      <td>Conjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Fire Shield</td>\n      <td>Evocation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Greater Invisibility</td>\n      <td>Illusion</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Hallucinatory Terrain</td>\n      <td>Illusion</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Ice Storm</td>\n      <td>Evocation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Locate Creature</td>\n      <td>Divination</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Phantasmal Killer</td>\n      <td>Illusion</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Polymorph</td>\n      <td>Transmutation</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Private Sanctum</td>\n      <td>Abjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Resilient Sphere</td>\n      <td>Abjuration</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Secret Chest</td>\n      <td>Conjuration</td>\n      <td>M</td>\n    </tr>\n    <tr>\n      <td>Stone Shape</td>\n      <td>Transmutation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Stoneskin</td>\n      <td>Transmutation</td>\n      <td>C, M</td>\n    </tr>\n    <tr>\n      <td>Vitriolic Sphere</td>\n      <td>Evocation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Wall of Fire</td>\n      <td>Evocation</td>\n      <td>C</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        ("Wizard", "Wizard Spell List", "Level 5 Wizard Spells"),
        "#### Level 5 Wizard Spells",
    ),
    (
        ("Wizard", "Wizard Spell List", "Level 5 Wizard Spells"),
        "<table>\n  <thead>\n    <tr>\n      <th>Spell</th>\n      <th>School</th>\n      <th>Special</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>Animate Objects</td>\n      <td>Transmutation</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Arcane Hand</td>\n      <td>Evocation</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Cloudkill</td>\n      <td>Conjuration</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Cone of Cold</td>\n      <td>Evocation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Conjure Elemental</td>\n      <td>Conjuration</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Contact Other Plane</td>\n      <td>Divination</td>\n      <td>R</td>\n    </tr>\n    <tr>\n      <td>Creation</td>\n      <td>Illusion</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Dominate Person</td>\n      <td>Enchantment</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Dream</td>\n      <td>Illusion</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Geas</td>\n      <td>Enchantment</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Hold Monster</td>\n      <td>Enchantment</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Legend Lore</td>\n      <td>Divination</td>\n      <td>M</td>\n    </tr>\n    <tr>\n      <td>Mislead</td>\n      <td>Illusion</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Modify Memory</td>\n      <td>Enchantment</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Passwall</td>\n      <td>Transmutation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Planar Binding</td>\n      <td>Abjuration</td>\n      <td>M</td>\n    </tr>\n    <tr>\n      <td>Scrying</td>\n      <td>Divination</td>\n      <td>C, M</td>\n    </tr>\n    <tr>\n      <td>Seeming</td>\n      <td>Illusion</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Summon Dragon</td>\n      <td>Conjuration</td>\n      <td>C, M</td>\n    </tr>\n    <tr>\n      <td>Telekinesis</td>\n      <td>Transmutation</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Telepathic Bond</td>\n      <td>Divination</td>\n      <td>R</td>\n    </tr>\n    <tr>\n      <td>Teleportation Circle</td>\n      <td>Conjuration</td>\n      <td>M</td>\n    </tr>\n    <tr>\n      <td>Wall of Force</td>\n      <td>Evocation</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Wall of Stone</td>\n      <td>Evocation</td>\n      <td>C</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        ("Wizard", "Wizard Spell List", "Level 6 Wizard Spells"),
        "#### Level 6 Wizard Spells",
    ),
    (
        ("Wizard", "Wizard Spell List", "Level 6 Wizard Spells"),
        "<table>\n  <thead>\n    <tr>\n      <th>Spell</th>\n      <th>School</th>\n      <th>Special</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>Chain Lightning</td>\n      <td>Evocation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Circle of Death</td>\n      <td>Necromancy</td>\n      <td>M</td>\n    </tr>\n    <tr>\n      <td>Contingency</td>\n      <td>Abjuration</td>\n      <td>M</td>\n    </tr>\n    <tr>\n      <td>Create Undead</td>\n      <td>Necromancy</td>\n      <td>M</td>\n    </tr>\n    <tr>\n      <td>Disintegrate</td>\n      <td>Transmutation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Eyebite</td>\n      <td>Necromancy</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Flesh to Stone</td>\n      <td>Transmutation</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Freezing Sphere</td>\n      <td>Evocation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Globe of Invulnerability</td>\n      <td>Abjuration</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Guards and Wards</td>\n      <td>Abjuration</td>\n      <td>M</td>\n    </tr>\n    <tr>\n      <td>Instant Summons</td>\n      <td>Conjuration</td>\n      <td>R, M</td>\n    </tr>\n    <tr>\n      <td>Irresistible Dance</td>\n      <td>Enchantment</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Magic Jar</td>\n      <td>Necromancy</td>\n      <td>M</td>\n    </tr>\n    <tr>\n      <td>Mass Suggestion</td>\n      <td>Enchantment</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Move Earth</td>\n      <td>Transmutation</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Programmed Illusion</td>\n      <td>Illusion</td>\n      <td>M</td>\n    </tr>\n    <tr>\n      <td>Sunbeam</td>\n      <td>Evocation</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>True Seeing</td>\n      <td>Divination</td>\n      <td>M</td>\n    </tr>\n    <tr>\n      <td>Wall of Ice</td>\n      <td>Evocation</td>\n      <td>C</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        ("Wizard", "Wizard Spell List", "Level 7 Wizard Spells"),
        "#### Level 7 Wizard Spells",
    ),
    (
        ("Wizard", "Wizard Spell List", "Level 7 Wizard Spells"),
        "<table>\n  <thead>\n    <tr>\n      <th>Spell</th>\n      <th>School</th>\n      <th>Special</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>Arcane Sword</td>\n      <td>Evocation</td>\n      <td>C, M</td>\n    </tr>\n    <tr>\n      <td>Delayed Blast Fireball</td>\n      <td>Evocation</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Etherealness</td>\n      <td>Conjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Finger of Death</td>\n      <td>Necromancy</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Forcecage</td>\n      <td>Evocation</td>\n      <td>C, M</td>\n    </tr>\n    <tr>\n      <td>Magnificent Mansion</td>\n      <td>Conjuration</td>\n      <td>M</td>\n    </tr>\n    <tr>\n      <td>Mirage Arcane</td>\n      <td>Illusion</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Plane Shift</td>\n      <td>Conjuration</td>\n      <td>M</td>\n    </tr>\n    <tr>\n      <td>Prismatic Spray</td>\n      <td>Evocation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Project Image</td>\n      <td>Illusion</td>\n      <td>C, M</td>\n    </tr>\n    <tr>\n      <td>Reverse Gravity</td>\n      <td>Transmutation</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Sequester</td>\n      <td>Transmutation</td>\n      <td>M</td>\n    </tr>\n    <tr>\n      <td>Simulacrum</td>\n      <td>Illusion</td>\n      <td>M</td>\n    </tr>\n    <tr>\n      <td>Symbol</td>\n      <td>Abjuration</td>\n      <td>M</td>\n    </tr>\n    <tr>\n      <td>Teleport</td>\n      <td>Conjuration</td>\n      <td>—</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        ("Wizard", "Wizard Spell List", "Level 8 Wizard Spells"),
        "#### Level 8 Wizard Spells",
    ),
    (
        ("Wizard", "Wizard Spell List", "Level 8 Wizard Spells"),
        "<table>\n  <thead>\n    <tr>\n      <th>Spell</th>\n      <th>School</th>\n      <th>Special</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>Antimagic Field</td>\n      <td>Abjuration</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Antipathy/Sympathy</td>\n      <td>Enchantment</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Befuddlement</td>\n      <td>Enchantment</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Clone</td>\n      <td>Necromancy</td>\n      <td>M</td>\n    </tr>\n    <tr>\n      <td>Control Weather</td>\n      <td>Transmutation</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Demiplane</td>\n      <td>Conjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Dominate Monster</td>\n      <td>Enchantment</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Incendiary Cloud</td>\n      <td>Conjuration</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Maze</td>\n      <td>Conjuration</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Mind Blank</td>\n      <td>Abjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Power Word Stun</td>\n      <td>Enchantment</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Sunburst</td>\n      <td>Evocation</td>\n      <td>—</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        ("Wizard", "Wizard Spell List", "Level 9 Wizard Spells"),
        "#### Level 9 Wizard Spells",
    ),
    (
        ("Wizard", "Wizard Spell List", "Level 9 Wizard Spells"),
        "<table>\n  <thead>\n    <tr>\n      <th>Spell</th>\n      <th>School</th>\n      <th>Special</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>Astral Projection</td>\n      <td>Necromancy</td>\n      <td>M</td>\n    </tr>\n    <tr>\n      <td>Foresight</td>\n      <td>Divination</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Gate</td>\n      <td>Conjuration</td>\n      <td>C, M</td>\n    </tr>\n    <tr>\n      <td>Imprisonment</td>\n      <td>Abjuration</td>\n      <td>M</td>\n    </tr>\n    <tr>\n      <td>Meteor Swarm</td>\n      <td>Evocation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Power Word Kill</td>\n      <td>Enchantment</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Prismatic Wall</td>\n      <td>Abjuration</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>Shapechange</td>\n      <td>Transmutation</td>\n      <td>C, M</td>\n    </tr>\n    <tr>\n      <td>Time Stop</td>\n      <td>Transmutation</td>\n      <td>—</td>\n    </tr>\n    <tr>\n      <td>True Polymorph</td>\n      <td>Transmutation</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Weird</td>\n      <td>Illusion</td>\n      <td>C</td>\n    </tr>\n    <tr>\n      <td>Wish</td>\n      <td>Conjuration</td>\n      <td>—</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (("Wizard", "Wizard Subclass: Evoker"), "### Wizard Subclass: Evoker"),
    (("Wizard", "Wizard Subclass: Evoker"), "_Create Explosive Elemental Effects_"),
    (
        ("Wizard", "Wizard Subclass: Evoker"),
        "Your studies focus on magic that creates powerful elemental effects such as bitter cold, searing flame, rolling thunder, crackling lightning, and burning acid. Some Evokers find employment in military forces, serving as artillery to blast armies from afar. Others use their power to protect others, while some seek their own gain.",
    ),
    (
        ("Wizard", "Wizard Subclass: Evoker", "Level 3: Evocation Savant"),
        "#### Level 3: Evocation Savant",
    ),
    (
        ("Wizard", "Wizard Subclass: Evoker", "Level 3: Evocation Savant"),
        "Choose two Wizard spells from the Evocation school, each of which must be no higher than level 2, and add them to your spellbook for free.",
    ),
    (
        ("Wizard", "Wizard Subclass: Evoker", "Level 3: Evocation Savant"),
        "In addition, whenever you gain access to a new level of spell slots in this class, you can add one Wizard spell from the Evocation school to your spellbook for free. The chosen spell must be of a level for which you have spell slots.",
    ),
    (
        ("Wizard", "Wizard Subclass: Evoker", "Level 3: Potent Cantrip"),
        "#### Level 3: Potent Cantrip",
    ),
    (
        ("Wizard", "Wizard Subclass: Evoker", "Level 3: Potent Cantrip"),
        "Your damaging cantrips affect even creatures that avoid the brunt of the effect. When you cast a cantrip at a creature and you miss with the attack roll or the target succeeds on a saving throw against the cantrip, the target takes half the cantrip's damage (if any) but suffers no additional effect from the cantrip.",
    ),
    (
        ("Wizard", "Wizard Subclass: Evoker", "Level 6: Sculpt Spells"),
        "#### Level 6: Sculpt Spells",
    ),
    (
        ("Wizard", "Wizard Subclass: Evoker", "Level 6: Sculpt Spells"),
        "You can create pockets of relative safety within the effects of your evocations. When you cast an Evocation spell that affects other creatures that you can see, you can choose a number of them equal to 1 plus the spell's level. The chosen creatures automatically succeed on their saving throws against the spell, and they take no damage if they would normally take half damage on a successful save.",
    ),
    (
        ("Wizard", "Wizard Subclass: Evoker", "Level 10: Empowered Evocation"),
        "#### Level 10: Empowered Evocation",
    ),
    (
        ("Wizard", "Wizard Subclass: Evoker", "Level 10: Empowered Evocation"),
        "Whenever you cast a Wizard spell from the Evocation school, you can add your Intelligence modifier to one damage roll of that spell.",
    ),
    (
        ("Wizard", "Wizard Subclass: Evoker", "Level 14: Overchannel"),
        "#### Level 14: Overchannel",
    ),
    (
        ("Wizard", "Wizard Subclass: Evoker", "Level 14: Overchannel"),
        "You can increase the power of your spells. When you cast a Wizard spell with a spell slot of levels 1–5 that deals damage, you can deal maximum damage with that spell on the turn you cast it.",
    ),
    (
        ("Wizard", "Wizard Subclass: Evoker", "Level 14: Overchannel"),
        "The first time you do so, you suffer no adverse effect. If you use this feature again before you finish a Long Rest, you take 2d12 Necrotic damage for each level of the spell slot immediately after you cast it. This damage ignores Resistance and Immunity.",
    ),
    (
        ("Wizard", "Wizard Subclass: Evoker", "Level 14: Overchannel"),
        "Each time you use this feature again before finishing a Long Rest, the Necrotic damage per spell level increases by 1d12.",
    ),
)
