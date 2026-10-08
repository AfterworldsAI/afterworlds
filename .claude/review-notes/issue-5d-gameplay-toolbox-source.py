# ruff: noqa: E501
"""The SRD 5.2.1 *Gameplay Toolbox* part as the release prints it -- CRD Issue 5d.

Every leaf of the part below its ``# Gameplay Toolbox`` heading, in printed
order (pp. 192-203), as (container label path below *Gameplay Toolbox*, exact
leaf text). Each text was qualified against the official PDF
(``docs/sources/DnD5_5e_SRD_CC_v5_2_1.pdf``) before it was written here: prose
word for word, every table row cell for cell (see the gameplay toolbox review
packet). The part heading itself is left with the other part headings. The
generator names its spans from these texts; a text the release prints
differently fails to locate, loudly.
"""

from __future__ import annotations

LEAVES: tuple[tuple[tuple[str, ...], str], ...] = (
    (("Travel Pace",), "## Travel Pace"),
    (
        ("Travel Pace",),
        "A group of characters can travel overland at a Normal, Fast, or Slow pace, as described in \"Playing the Game.\" During any journey stage, the predominant terrain determines the characters' maximum travel pace, as shown in the Maximum Pace column of the Travel Terrain table. Certain factors can affect a group's travel pace.",
    ),
    (("Travel Pace", "Good Roads"), "### Good Roads"),
    (
        ("Travel Pace", "Good Roads"),
        "The presence of a good road increases the group's maximum pace by one step (from Slow to Normal or from Normal to Fast).",
    ),
    (("Travel Pace", "Slower Travelers"), "### Slower Travelers"),
    (
        ("Travel Pace", "Slower Travelers"),
        "The group must move at a Slow pace if any group member's Speed is reduced to half or less of normal.",
    ),
    (("Travel Pace", "Extended Travel"), "### Extended Travel"),
    (
        ("Travel Pace", "Extended Travel"),
        "Characters can push themselves to travel for more than 8 hours per day, at the risk of tiring. At the end of each additional hour of travel beyond 8 hours, each character must succeed on a Constitution saving throw or gain 1 Exhaustion level. The DC is 10 plus 1 for each hour past 8 hours.",
    ),
    (("Travel Pace", "Special Movement"), "### Special Movement"),
    (
        ("Travel Pace", "Special Movement"),
        "If a party can travel at a high Speed for an extended time, as with a spell such as _Wind Walk_ or a magic item such as a _Carpet of Flying_, translate the party's Speed into travel rates using these rules:",
    ),
    (
        ("Travel Pace", "Special Movement"),
        "**Miles per hour** = Speed ÷ 10\n**Miles per day** (Normal pace) = Miles per hour × number of hours traveled (typically 8)\n**Fast pace** = Miles per day × 1⅓ (round down)\n**Slow pace** = Miles per day × 2/3 (round down)",
    ),
    (
        ("Travel Pace", "Special Movement"),
        "If the characters are flying or their special movement allows them to ignore Difficult Terrain, they can move at a Fast pace regardless of the terrain.",
    ),
    (("Travel Pace", "Vehicles"), "### Vehicles"),
    (
        ("Travel Pace", "Vehicles"),
        "Characters traveling in a vehicle use the vehicle's speed in miles per hour (as shown in \"Equipment\") to determine their rate of travel, and they don't choose a travel pace.",
    ),
    (
        ("Travel Pace", "Vehicles"),
        '**Travel Terrain**\n\n<table>\n  <thead>\n    <tr>\n      <th>Terrain</th>\n      <th>Maximum Pace</th>\n      <th>Encounter Distance</th>\n      <th>Foraging DC</th>\n      <th>Navigation DC</th>\n      <th>Search DC</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>Arctic</td>\n      <td>Fast*</td>\n      <td>6d6 × 10 feet</td>\n      <td>20</td>\n      <td>10</td>\n      <td>10</td>\n    </tr>\n    <tr>\n      <td>Coastal</td>\n      <td>Normal</td>\n      <td>2d10 × 10 feet</td>\n      <td>10</td>\n      <td>5</td>\n      <td>15</td>\n    </tr>\n    <tr>\n      <td>Desert</td>\n      <td>Normal</td>\n      <td>6d6 × 10 feet</td>\n      <td>20</td>\n      <td>10</td>\n      <td>10</td>\n    </tr>\n    <tr>\n      <td>Forest</td>\n      <td>Normal</td>\n      <td>2d8 × 10 feet</td>\n      <td>10</td>\n      <td>15</td>\n      <td>15</td>\n    </tr>\n    <tr>\n      <td>Grassland</td>\n      <td>Fast</td>\n      <td>6d6 × 10 feet</td>\n      <td>15</td>\n      <td>5</td>\n      <td>15</td>\n    </tr>\n    <tr>\n      <td>Hill</td>\n      <td>Normal</td>\n      <td>2d10 × 10 feet</td>\n      <td>15</td>\n      <td>10</td>\n      <td>15</td>\n    </tr>\n    <tr>\n      <td>Mountain</td>\n      <td>Slow</td>\n      <td>4d10 × 10 feet</td>\n      <td>20</td>\n      <td>15</td>\n      <td>20</td>\n    </tr>\n    <tr>\n      <td>Swamp</td>\n      <td>Slow</td>\n      <td>2d8 × 10 feet</td>\n      <td>10</td>\n      <td>15</td>\n      <td>20</td>\n    </tr>\n    <tr>\n      <td>Underdark</td>\n      <td>Normal</td>\n      <td>2d6 × 10 feet</td>\n      <td>20</td>\n      <td>10</td>\n      <td>20</td>\n    </tr>\n    <tr>\n      <td>Urban</td>\n      <td>Normal</td>\n      <td>2d6 × 10 feet</td>\n      <td>20</td>\n      <td>15</td>\n      <td>15</td>\n    </tr>\n    <tr>\n      <td>Waterborne</td>\n      <td>Special†</td>\n      <td>6d6 × 10 feet</td>\n      <td>15</td>\n      <td>10</td>\n      <td>15</td>\n    </tr>\n  </tbody>\n</table>\n\n\\*Appropriate equipment (such as skis) is necessary to keep up a Fast pace in Arctic terrain.\n†Characters\' rate of travel while waterborne depends on the vehicle carrying them; see "Vehicles."',
    ),
    (("Creating a Background",), "## Creating a Background"),
    (
        ("Creating a Background",),
        "A character's background represents what the character did prior to becoming an adventurer. Creating a unique background or customizing an existing one can reflect the particular theme of your campaign or elements of your world. You can also create a background to help a player craft the story they have in mind for their character.",
    ),
    (
        ("Creating a Background",),
        "This section describes, step by step, how you can create backgrounds tailored for your world and the heroes in it.",
    ),
    (("Creating a Background", "1: Choose Abilities"), "### 1: Choose Abilities"),
    (
        ("Creating a Background", "1: Choose Abilities"),
        "Choose three abilities that seem appropriate for the background:",
    ),
    (
        ("Creating a Background", "1: Choose Abilities"),
        "**Strength or Dexterity.** These abilities are ideal for a background involving physical exertion.\n**Constitution.** This ability is ideal for a background that involves endurance or long hours of activity.\n**Intelligence or Wisdom.** One or both abilities are ideal for a background that focuses on cerebral or spiritual matters.\n**Charisma.** This ability is ideal for a background that involves performance or social interaction.",
    ),
    (("Creating a Background", "2: Choose a Feat"), "### 2: Choose a Feat"),
    (
        ("Creating a Background", "2: Choose a Feat"),
        'Choose one feat from the Origin category. See "Origin Feats" for examples of Origin feats.',
    ),
    (
        ("Creating a Background", "3: Choose Skill Proficiencies"),
        "### 3: Choose Skill Proficiencies",
    ),
    (
        ("Creating a Background", "3: Choose Skill Proficiencies"),
        "Choose two skills appropriate for the background. There needn't be a relationship between the skill proficiencies a background grants and the ability scores it increases.",
    ),
    (
        ("Creating a Background", "4: Choose a Tool Proficiency"),
        "### 4: Choose a Tool Proficiency",
    ),
    (
        ("Creating a Background", "4: Choose a Tool Proficiency"),
        "Choose one tool used in the practice of the background or often associated with it.",
    ),
    (("Creating a Background", "5: Choose Equipment"), "### 5: Choose Equipment"),
    (
        ("Creating a Background", "5: Choose Equipment"),
        "Assemble a package of equipment worth 50 GP (including unspent gold). Don't include Martial weapons or armor, as characters get them from their class choices.",
    ),
    (("Curses and Magical Contagions",), "## Curses and Magical Contagions"),
    (
        ("Curses and Magical Contagions",),
        "A curse is a magical burden that lasts for a specified time or until it is ended by some means. A magical contagion is an adverse effect of magical origin that is contagious by definition.",
    ),
    (
        ("Curses and Magical Contagions",),
        "The following sections discuss curses and magical contagions in detail.",
    ),
    (("Curses and Magical Contagions", "Curses"), "### Curses"),
    (
        ("Curses and Magical Contagions", "Curses"),
        "A curse typically takes one of the forms detailed below.",
    ),
    (("Curses and Magical Contagions", "Curses", "Bestow Curse"), "#### Bestow Curse"),
    (
        ("Curses and Magical Contagions", "Curses", "Bestow Curse"),
        "The simplest curses are created by the _Bestow Curse_ spell. The effects of such curses are limited and can be ended by the _Remove Curse_ spell.",
    ),
    (
        ("Curses and Magical Contagions", "Curses", "Bestow Curse"),
        "_Bestow Curse_ provides useful benchmarks for gauging the potency of other curses. A curse that lasts for 1 minute equates to a level 3 spell, while one that lasts until dispelled equates to a level 9 spell.",
    ),
    (
        ("Curses and Magical Contagions", "Curses", "Cursed Creatures"),
        "#### Cursed Creatures",
    ),
    (
        ("Curses and Magical Contagions", "Curses", "Cursed Creatures"),
        "Some monsters are associated with curses, whether as part of their origins or due to their ability to spread curses—werewolves being a prime example.",
    ),
    (
        ("Curses and Magical Contagions", "Curses", "Cursed Creatures"),
        "You decide how a spell like _Remove Curse_ affects a creature with accursed origins. For example, you might decide that a mummy was created through a curse and it can be destroyed permanently only by casting _Remove Curse_ on its corpse.",
    ),
    (
        ("Curses and Magical Contagions", "Curses", "Cursed Magic Items"),
        "#### Cursed Magic Items",
    ),
    (
        ("Curses and Magical Contagions", "Curses", "Cursed Magic Items"),
        'Cursed magic items are created deliberately or originate as the result of supernatural events. Such items are detailed in "Magic Items."',
    ),
    (
        ("Curses and Magical Contagions", "Curses", "Narrative Curses"),
        "#### Narrative Curses",
    ),
    (
        ("Curses and Magical Contagions", "Curses", "Narrative Curses"),
        "A curse might manifest during an adventure when a creature's violation of a taboo warrants supernatural punishment, such as breaking a vow, defiling a tomb, or murdering an innocent. Such a curse can have any effects you design, or it might be a customized version of another type of curse discussed in this section.",
    ),
    (
        ("Curses and Magical Contagions", "Curses", "Narrative Curses"),
        "A creature affected by such a curse should know why they're being punished and be able to learn how to end their curse, likely by symbolically righting the wrong they committed. How a spell like _Remove Curse_ affects a curse that's part of your adventure is up to you—the spell might merely suppress the effects of the curse for a time. Regardless, narrative curses should feel like rare, potent magic rooted in the lore of your campaign.",
    ),
    (
        ("Curses and Magical Contagions", "Curses", "Environmental Curses"),
        "#### Environmental Curses",
    ),
    (
        ("Curses and Magical Contagions", "Curses", "Environmental Curses"),
        "Some locations are so suffused with evil that anyone who lingers there is burdened with a curse. Demonic Possession is one example of an environmental curse.",
    ),
    (
        ("Curses and Magical Contagions", "Curses", "Environmental Curses"),
        "_Demonic Possession._ Demonic Possession arises from the chaos and evil of the Abyss and commonly besets creatures that interact with demonic objects or linger in desecrated locations, where demonic spirits await victims.",
    ),
    (
        ("Curses and Magical Contagions", "Curses", "Environmental Curses"),
        "A creature that becomes the target of Demonic Possession must succeed on a DC 15 Charisma saving throw or be possessed by a bodiless demonic entity. Whenever the possessed creature rolls a 1 on a D20 Test, the demonic entity takes control of the creature and determines the creature's behavior thereafter. At the end of each of the possessed creature's later turns, the creature makes a DC 15 Charisma saving throw, regaining control of itself on a success.",
    ),
    (
        ("Curses and Magical Contagions", "Curses", "Environmental Curses"),
        "After finishing a Long Rest, a creature with Demonic Possession makes a DC 15 Charisma saving throw. On a successful save, the effect ends on the creature. A _Dispel Evil and Good_ spell or any magic that removes a curse also ends the effect on it.",
    ),
    (("Curses and Magical Contagions", "Magical Contagions"), "### Magical Contagions"),
    (
        ("Curses and Magical Contagions", "Magical Contagions"),
        "Alchemists, potion brewers, and areas of wild magic are credited with creating the first magical contagions. An outbreak of such a contagion can form the basis of an adventure as characters search for a cure and try to stop the contagion's spread.",
    ),
    (
        (
            "Curses and Magical Contagions",
            "Magical Contagions",
            "Rest and Recuperation",
        ),
        "#### Rest and Recuperation",
    ),
    (
        (
            "Curses and Magical Contagions",
            "Magical Contagions",
            "Rest and Recuperation",
        ),
        "If a creature infected with a magical contagion spends 3 days recuperating—engaging in no activities that would interrupt a Long Rest—the creature makes a DC 15 Constitution saving throw at the end of the recuperation period. On a successful save, the creature has Advantage on saving throws to fight off the magical contagion for the next 24 hours.",
    ),
    (
        ("Curses and Magical Contagions", "Magical Contagions", "Example Contagions"),
        "#### Example Contagions",
    ),
    (
        ("Curses and Magical Contagions", "Magical Contagions", "Example Contagions"),
        "The following examples show how magical contagions can work. Feel free to alter the saving throw DCs, effects, and other characteristics of these contagions to suit your campaign.",
    ),
    (
        ("Curses and Magical Contagions", "Magical Contagions", "Cackle Fever"),
        "#### Cackle Fever",
    ),
    (
        ("Curses and Magical Contagions", "Magical Contagions", "Cackle Fever"),
        "_Magical Contagion_",
    ),
    (
        ("Curses and Magical Contagions", "Magical Contagions", "Cackle Fever"),
        "Cheaply made potions and elixirs are sometimes tainted by Cackle Fever, which affects Humanoids only (gnomes are strangely immune). A creature suffers the following effects 1d4 days after infection:",
    ),
    (
        ("Curses and Magical Contagions", "Magical Contagions", "Cackle Fever"),
        "**Fever.** The creature gains 1 Exhaustion level, which lasts until the contagion ends on the creature.",
    ),
    (
        ("Curses and Magical Contagions", "Magical Contagions", "Cackle Fever"),
        "**Uncontrollable Laughter.** While the creature has the Exhaustion condition, the creature makes a DC 13 Constitution saving throw each time it takes damage other than Psychic damage. On a failed save, the creature takes 5 (1d10) Psychic damage and has the Incapacitated condition as it laughs uncontrollably. At the end of each of its turns, the creature repeats the save, ending the effect on itself on a success. After 1 minute, it succeeds automatically.",
    ),
    (
        ("Curses and Magical Contagions", "Magical Contagions", "Cackle Fever"),
        "_Fighting the Contagion._ At the end of each Long Rest, an infected creature makes a DC 13 Constitution saving throw. After the creature succeeds on three of these saves, the contagion ends on it, and the creature is immune to Cackle Fever for 1 year.",
    ),
    (
        ("Curses and Magical Contagions", "Magical Contagions", "Cackle Fever"),
        "_Spreading the Contagion._ Any Humanoid (other than a gnome) that starts its turn within a 10-foot Emanation originating from a creature infected with Cackle Fever must succeed on a DC 10 Constitution saving throw or also become infected with the contagion. On a successful save, the Humanoid can't catch the contagion from that particular infected creature for the next 24 hours.",
    ),
    (
        ("Curses and Magical Contagions", "Magical Contagions", "Sewer Plague"),
        "#### Sewer Plague",
    ),
    (
        ("Curses and Magical Contagions", "Magical Contagions", "Sewer Plague"),
        "_Magical Contagion_",
    ),
    (
        ("Curses and Magical Contagions", "Magical Contagions", "Sewer Plague"),
        "Fouled potions and alchemical waste can give rise to Sewer Plague, which incubates in sewers and refuse heaps and is sometimes transmitted by creatures that dwell in such areas, including otyughs and rats. Any Humanoid that is wounded by a creature that carries the contagion or that comes into contact with contaminated filth or offal must succeed on a DC 11 Constitution saving throw or become infected with Sewer Plague. A creature suffers the following effects 1d4 days after infection:",
    ),
    (
        ("Curses and Magical Contagions", "Magical Contagions", "Sewer Plague"),
        "**Fatigue.** The creature gains 1 Exhaustion level.",
    ),
    (
        ("Curses and Magical Contagions", "Magical Contagions", "Sewer Plague"),
        "**Weakness.** While the creature has any Exhaustion levels, it regains only half the normal number of Hit Points from spending Hit Point Dice.",
    ),
    (
        ("Curses and Magical Contagions", "Magical Contagions", "Sewer Plague"),
        "**Restlessness.** While the creature has any Exhaustion levels, finishing a Long Rest neither restores lost Hit Points nor reduces the creature's Exhaustion level.",
    ),
    (
        ("Curses and Magical Contagions", "Magical Contagions", "Sewer Plague"),
        "_Fighting the Contagion._ Daily at dawn, an infected creature makes a DC 11 Constitution saving throw. On a failed save, the creature gains 1 Exhaustion level as its fatigue worsens. On a successful save, the creature's Exhaustion level decreases by 1. If the creature's Exhaustion level is reduced to 0, the contagion ends on the creature.",
    ),
    (
        ("Curses and Magical Contagions", "Magical Contagions", "Sight Rot"),
        "#### Sight Rot",
    ),
    (
        ("Curses and Magical Contagions", "Magical Contagions", "Sight Rot"),
        "_Magical Contagion_",
    ),
    (
        ("Curses and Magical Contagions", "Magical Contagions", "Sight Rot"),
        "Any Beast or Humanoid that drinks water tainted by Sight Rot must succeed on a DC 15 Constitution saving throw or have the Blinded condition until the contagion ends.",
    ),
    (
        ("Curses and Magical Contagions", "Magical Contagions", "Sight Rot"),
        "_Fighting the Contagion._ Magic such as a _Heal_ or _Lesser Restoration_ spell ends the contagion immediately. A character who is proficient with an Herbalism Kit can use it to create one dose of nonmagical ointment, which takes 1 hour. When applied to the eyes of a creature suffering from Sight Rot, the ointment suppresses the contagion on that creature for 24 hours. If the contagion is suppressed in this way for a total of 72 hours (requiring three doses and applications of the ointment), the contagion ends on the creature.",
    ),
    (
        ("Curses and Magical Contagions", "Magical Contagions", "Sight Rot"),
        "_Spreading the Contagion._ Any Humanoid that makes skin contact with a creature infected with Sight Rot must succeed on a DC 15 Constitution saving throw or also become infected with the contagion. On a successful save, the Humanoid can't catch the contagion from that particular infected creature for the next 24 hours.",
    ),
    (("Environmental Effects",), "## Environmental Effects"),
    (("Environmental Effects", "Deep Water"), "### Deep Water"),
    (
        ("Environmental Effects", "Deep Water"),
        "Swimming through deep water (more than 100 feet deep) presents additional challenges because of the water's pressure and cold temperature. After each hour of swimming in deep water, a creature that lacks a Swim Speed must succeed on a DC 10 Constitution saving throw or gain 1 Exhaustion level.",
    ),
    (("Environmental Effects", "Extreme Cold"), "### Extreme Cold"),
    (
        ("Environmental Effects", "Extreme Cold"),
        "When the temperature is 0 degrees Fahrenheit or lower, a creature exposed to the extreme cold must succeed on a DC 10 Constitution saving throw at the end of each hour or gain 1 Exhaustion level. Creatures that have Resistance or Immunity to Cold damage automatically succeed on the save.",
    ),
    (("Environmental Effects", "Extreme Heat"), "### Extreme Heat"),
    (
        ("Environmental Effects", "Extreme Heat"),
        "When the temperature is 100 degrees Fahrenheit or higher, a creature exposed to the extreme heat and without access to drinkable water must succeed on a Constitution saving throw at the end of each hour or gain 1 Exhaustion level. The DC is 5 for the first hour and increases by 1 for each additional hour. Creatures wearing Medium or Heavy armor have Disadvantage on the save. Creatures that have Resistance or Immunity to Fire damage automatically succeed on the save.",
    ),
    (("Environmental Effects", "Frigid Water"), "### Frigid Water"),
    (
        ("Environmental Effects", "Frigid Water"),
        "A creature can be immersed in frigid water for a number of minutes equal to its Constitution score before suffering any ill effects. Each additional minute spent in frigid water requires the creature to succeed on a DC 10 Constitution saving throw or gain 1 Exhaustion level. Creatures with Resistance or Immunity to Cold damage automatically succeed on the save, as do creatures that are naturally adapted to living in ice-cold water.",
    ),
    (("Environmental Effects", "Heavy Precipitation"), "### Heavy Precipitation"),
    (
        ("Environmental Effects", "Heavy Precipitation"),
        "Everything within an area of heavy rain or heavy snowfall is Lightly Obscured, and creatures in the area have Disadvantage on all Wisdom (Perception) checks. Heavy rain also extinguishes open flames.",
    ),
    (("Environmental Effects", "High Altitude"), "### High Altitude"),
    (
        ("Environmental Effects", "High Altitude"),
        'Traveling at altitudes of 10,000 feet or higher above sea level is taxing for most creatures because of the reduced amount of oxygen in the air. Each hour such a creature spends traveling at high altitude counts as 2 hours for the purpose of determining how long that creature can travel (see "Travel Pace").',
    ),
    (
        ("Environmental Effects", "High Altitude"),
        "Creatures can become acclimated to a high altitude by spending 30 days or more at this elevation. Creatures can't become acclimated to elevations above 20,000 feet unless they are native to such environments.",
    ),
    (("Environmental Effects", "Slippery Ice"), "### Slippery Ice"),
    (
        ("Environmental Effects", "Slippery Ice"),
        "Slippery ice is Difficult Terrain. A creature that moves onto slippery ice for the first time on a turn or starts its turn there must succeed on a DC 10 Dexterity saving throw or have the Prone condition.",
    ),
    (("Environmental Effects", "Strong Wind"), "### Strong Wind"),
    (
        ("Environmental Effects", "Strong Wind"),
        "Strong wind imposes Disadvantage on ranged attack rolls with weapons. It also extinguishes open flames and disperses fog. A flying creature in a strong wind must land at the end of its turn or fall.",
    ),
    (
        ("Environmental Effects", "Strong Wind"),
        "A strong wind in a desert can create a sandstorm that imposes Disadvantage on Wisdom (Perception) checks.",
    ),
    (("Environmental Effects", "Thin Ice"), "### Thin Ice"),
    (
        ("Environmental Effects", "Thin Ice"),
        'Thin ice has a weight tolerance of 3d10 × 10 pounds per 10-foot-square area. Whenever the total weight on an area of thin ice exceeds its tolerance, the ice in that area breaks. All creatures on broken ice fall through. Below the ice is frigid water (see "Frigid Water" above).',
    ),
    (("Fear and Mental Stress",), "## Fear and Mental Stress"),
    (
        ("Fear and Mental Stress",),
        "Due to the nature of their vocation, adventurers tend to be less susceptible to fear and mental stress than common folk. Whereas a farmer might flee in terror from a bear or an apparition, adventurers are made of sterner stuff. That said, certain creatures and game effects can terrify or fray the mind of even the most stalwart adventurer.",
    ),
    (
        ("Fear and Mental Stress",),
        "If you plan to use any of these rules, discuss them with your players at the start of the campaign.",
    ),
    (("Fear and Mental Stress", "Fear Effects"), "### Fear Effects"),
    (
        ("Fear and Mental Stress", "Fear Effects"),
        "Whenever the characters encounter something that is supernaturally frightful, use the Frightened condition as the baseline effect. Fear effects typically require a Wisdom saving throw, with a save DC based on how terrifying the situation is. The Sample Fear DCs table provides some examples.",
    ),
    (
        ("Fear and Mental Stress", "Fear Effects"),
        "**Sample Fear DCs**\n\n<table>\n  <thead>\n    <tr>\n      <th>Example</th>\n      <th>Save DC</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>When the characters open a sarcophagus, a harmless yet terrifying apparition appears.</td>\n      <td>10</td>\n    </tr>\n    <tr>\n      <td>A character triggers a magical trap that creates an illusory manifestation of that character's worst fears, visible only to that character.</td>\n      <td>15</td>\n    </tr>\n    <tr>\n      <td>A portal to the Abyss opens, revealing a nightmarish realm of torment and slaughter.</td>\n      <td>20</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        ("Fear and Mental Stress", "Fear Effects"),
        "Typically, a Frightened creature repeats the saving throw at the end of each of its turns, ending the effect on itself on a success.",
    ),
    (
        ("Fear and Mental Stress", "Fear Effects"),
        "At your discretion, a Frightened creature might be subject to other effects as long as the Frightened condition lasts. Consider these examples:",
    ),
    (
        ("Fear and Mental Stress", "Fear Effects"),
        "- The Frightened creature must take the Dash action on each of its turns and uses its movement to get farther away from the source of its fear.\n- Attack rolls against the Frightened creature have Advantage.\n- The Frightened creature can do only one of the following on each of its turns: move, take an action, or take a Bonus Action.",
    ),
    (("Fear and Mental Stress", "Mental Stress Effects"), "### Mental Stress Effects"),
    (
        ("Fear and Mental Stress", "Mental Stress Effects"),
        "When a character is subjected to an effect that causes intense mental stress, Psychic damage is the best way to emulate that effect.",
    ),
    (
        ("Fear and Mental Stress", "Mental Stress Effects"),
        "The Sample Mental Stress Effects table provides a few examples of such effects, with suggested saving throw DCs and damage. Mental stress can usually be resisted with a successful Wisdom save, but sometimes an Intelligence or Charisma save is more appropriate. On a successful save, a character might take half as much damage instead of no damage, at your discretion.",
    ),
    (
        ("Fear and Mental Stress", "Mental Stress Effects"),
        "**Sample Mental Stress Effects**\n\n<table>\n  <thead>\n    <tr>\n      <th>Example</th>\n      <th>Save DC</th>\n      <th>Psychic Damage</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>A character ingests a hallucinogenic substance that distorts the character's perception of reality.</td>\n      <td>10</td>\n      <td>1d6</td>\n    </tr>\n    <tr>\n      <td>A character touches a fiendish idol that tears at the character's mind, threatening to shatter it.</td>\n      <td>15</td>\n      <td>3d6</td>\n    </tr>\n    <tr>\n      <td>A magical trap flings a character into the Far Realm until the end of that character's next turn.</td>\n      <td>20</td>\n      <td>9d6</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        ("Fear and Mental Stress", "Mental Stress Effects", "Prolonged Effects"),
        "#### Prolonged Effects",
    ),
    (
        ("Fear and Mental Stress", "Mental Stress Effects", "Prolonged Effects"),
        "Exposure to mental stress can cause prolonged effects. Consider the following possibilities.",
    ),
    (
        ("Fear and Mental Stress", "Mental Stress Effects", "Prolonged Effects"),
        "_Short-Term Effects._ The character has the Frightened, Incapacitated, or Stunned condition for 1d10 minutes. This condition might be accompanied by alarming behavior or hallucinations. These effects can be suppressed with the _Calm Emotions_ spell or removed by the _Lesser Restoration_ spell.",
    ),
    (
        ("Fear and Mental Stress", "Mental Stress Effects", "Prolonged Effects"),
        "_Long-Term Effects._ The character has Disadvantage on some or all ability checks for 1d10 × 10 hours, stemming from an unwillingness or inability to exert a particular set of abilities. The character might feel enervated and unable to exert much Strength, for example, or become so suspicious of others that Charisma checks are more difficult. These effects can be suppressed with the _Calm Emotions_ spell or removed by the _Lesser Restoration_ spell.",
    ),
    (
        ("Fear and Mental Stress", "Mental Stress Effects", "Prolonged Effects"),
        "_Indefinite Effects._ An indefinite effect is a long-term effect (see above) that lasts until removed by a _Greater Restoration_ spell. It can be suppressed by a _Calm Emotions_ spell.",
    ),
    (("Poison",), "## Poison"),
    (
        ("Poison",),
        "Given their insidious and deadly nature, poisons are a favorite tool among assassins and evil creatures.",
    ),
    (("Poison",), "Poisons come in the following four types:"),
    (
        ("Poison",),
        "**Contact.** Contact poison can be smeared on an object and remains potent until it is touched or washed off. A creature that touches contact poison with exposed skin suffers its effects.",
    ),
    (
        ("Poison",),
        "**Ingested.** A creature must swallow an entire dose of ingested poison to suffer its effects. The dose can be delivered in food or a liquid. You may decide that a partial dose has a reduced effect, such as allowing Advantage on the saving throw or dealing only half as much damage on a failed save.",
    ),
    (
        ("Poison",),
        "**Inhaled.** Poisonous powders and gases take effect when inhaled. Blowing the powder or releasing the gas subjects creatures in a 5-foot Cube to its effect. The resulting cloud dissipates immediately afterward. Holding one's breath is ineffective against inhaled poisons, as they affect nasal membranes, tear ducts, and other parts of the body.",
    ),
    (
        ("Poison",),
        "**Injury.** Injury poison can be applied as a Bonus Action to a weapon, a piece of ammunition, or similar object. The poison remains potent until delivered through a wound or washed off. A creature that takes Piercing or Slashing damage from an object coated with the poison is exposed to its effects.",
    ),
    (("Poison", "Purchasing Poison"), "### Purchasing Poison"),
    (
        ("Poison", "Purchasing Poison"),
        "In some settings, laws prohibit the possession and use of poison, but an illicit dealer or unscrupulous apothecary might keep a hidden stash. Characters with criminal contacts might be able to acquire poison easily. Other characters might have to make extensive inquiries and pay bribes before they acquire the poison they seek.",
    ),
    (("Poison", "Harvesting Poison"), "### Harvesting Poison"),
    (
        ("Poison", "Harvesting Poison"),
        "A character can attempt to harvest poison from a venomous creature that is dead or has the Incapacitated condition. The effort takes 1d6 minutes, after which the character makes a DC 20 Intelligence (Nature) check using a Poisoner's Kit. On a successful check, the character harvests enough poison for a single dose, and no additional poison can be harvested from that creature. On a failed check, the character is unable to extract any poison. If the character fails the check by 5 or more, the character is subjected to the creature's poison.",
    ),
    (("Poison", "Sample Poisons"), "### Sample Poisons"),
    (
        ("Poison", "Sample Poisons"),
        "Example poisons are detailed here in alphabetical order. Each poison's description includes the suggested price for a single dose of the poison, its type (contact, ingested, inhaled, or injury), and a description of the poison's debilitating effects.",
    ),
    (
        ("Poison", "Sample Poisons", "Assassin's Blood (150 GP)"),
        "#### Assassin's Blood (150 GP)",
    ),
    (("Poison", "Sample Poisons", "Assassin's Blood (150 GP)"), "_Ingested Poison_"),
    (
        ("Poison", "Sample Poisons", "Assassin's Blood (150 GP)"),
        "A creature subjected to Assassin's Blood makes a DC 10 Constitution saving throw. On a failed save, the creature takes 6 (1d12) Poison damage and has the Poisoned condition for 24 hours. On a successful save, the creature takes half as much damage only.",
    ),
    (
        ("Poison", "Sample Poisons", "Burnt Othur Fumes (500 GP)"),
        "#### Burnt Othur Fumes (500 GP)",
    ),
    (("Poison", "Sample Poisons", "Burnt Othur Fumes (500 GP)"), "_Inhaled Poison_"),
    (
        ("Poison", "Sample Poisons", "Burnt Othur Fumes (500 GP)"),
        "A creature subjected to Burnt Othur Fumes must succeed on a DC 13 Constitution saving throw or take 10 (3d6) Poison damage, and it must repeat the save at the start of each of its turns. On each successive failed save, the creature takes 3 (1d6) Poison damage. After three successful saves, the poison ends.",
    ),
    (
        ("Poison", "Sample Poisons", "Crawler Mucus (200 GP)"),
        "#### Crawler Mucus (200 GP)",
    ),
    (("Poison", "Sample Poisons", "Crawler Mucus (200 GP)"), "_Contact Poison_"),
    (
        ("Poison", "Sample Poisons", "Crawler Mucus (200 GP)"),
        "A creature subjected to Crawler Mucus must succeed on a DC 13 Constitution saving throw or have the Poisoned condition for 1 minute. The creature also has the Paralyzed condition while Poisoned in this way. The creature repeats the save at the end of each of its turns, ending the effect on itself on a success.",
    ),
    (
        ("Poison", "Sample Poisons", "Essence of Ether (300 GP)"),
        "#### Essence of Ether (300 GP)",
    ),
    (("Poison", "Sample Poisons", "Essence of Ether (300 GP)"), "_Inhaled Poison_"),
    (
        ("Poison", "Sample Poisons", "Essence of Ether (300 GP)"),
        "A creature subjected to Essence of Ether must succeed on a DC 15 Constitution saving throw or have the Poisoned condition for 8 hours. The creature also has the Unconscious condition while Poisoned in this way. The creature wakes up if it takes damage or if another creature takes an action to shake it awake.",
    ),
    (("Poison", "Sample Poisons", "Malice (250 GP)"), "#### Malice (250 GP)"),
    (("Poison", "Sample Poisons", "Malice (250 GP)"), "_Inhaled Poison_"),
    (
        ("Poison", "Sample Poisons", "Malice (250 GP)"),
        "A creature subjected to Malice must succeed on a DC 15 Constitution saving throw or have the Poisoned condition for 1 hour. The creature also has the Blinded condition while Poisoned in this way.",
    ),
    (
        ("Poison", "Sample Poisons", "Midnight Tears (1,500 GP)"),
        "#### Midnight Tears (1,500 GP)",
    ),
    (("Poison", "Sample Poisons", "Midnight Tears (1,500 GP)"), "_Ingested Poison_"),
    (
        ("Poison", "Sample Poisons", "Midnight Tears (1,500 GP)"),
        "A creature that ingests Midnight Tears suffers no effect until the stroke of midnight. Any effect that\nends the Poisoned condition neutralizes this poison. If the poison hasn't been neutralized before midnight, the creature makes a DC 17 Constitution saving throw, taking 31 (9d6) Poison damage on a failed save or half as much damage on a successful one.",
    ),
    (
        ("Poison", "Sample Poisons", "Oil of Taggit (400 GP)"),
        "#### Oil of Taggit (400 GP)",
    ),
    (("Poison", "Sample Poisons", "Oil of Taggit (400 GP)"), "_Contact Poison_"),
    (
        ("Poison", "Sample Poisons", "Oil of Taggit (400 GP)"),
        "A creature subjected to Oil of Taggit must succeed on a DC 13 Constitution saving throw or have the Poisoned condition for 24 hours. The creature also has the Unconscious condition while Poisoned in this way. It wakes up if it takes damage.",
    ),
    (
        ("Poison", "Sample Poisons", "Pale Tincture (250 GP)"),
        "#### Pale Tincture (250 GP)",
    ),
    (("Poison", "Sample Poisons", "Pale Tincture (250 GP)"), "_Ingested Poison_"),
    (
        ("Poison", "Sample Poisons", "Pale Tincture (250 GP)"),
        "A creature subjected to Pale Tincture must succeed on a DC 16 Constitution saving throw or take 3 (1d6) Poison damage and have the Poisoned condition. The Poisoned creature repeats the save every 24 hours, taking 3 (1d6) Poison damage on a failed save. The damage the poison deals can't be healed by any means while the creature remains Poisoned. After seven successful saves against the poison, the creature is no longer Poisoned.",
    ),
    (
        ("Poison", "Sample Poisons", "Purple Worm Poison (2,000 GP)"),
        "#### Purple Worm Poison (2,000 GP)",
    ),
    (("Poison", "Sample Poisons", "Purple Worm Poison (2,000 GP)"), "_Injury Poison_"),
    (
        ("Poison", "Sample Poisons", "Purple Worm Poison (2,000 GP)"),
        "A creature subjected to Purple Worm Poison makes a DC 21 Constitution saving throw, taking 35 (10d6) Poison damage on a failed save or half as much damage on a successful one.",
    ),
    (
        ("Poison", "Sample Poisons", "Serpent Venom (200 GP)"),
        "#### Serpent Venom (200 GP)",
    ),
    (("Poison", "Sample Poisons", "Serpent Venom (200 GP)"), "_Injury Poison_"),
    (
        ("Poison", "Sample Poisons", "Serpent Venom (200 GP)"),
        "A creature subjected to Serpent Venom must succeed on a DC 11 Constitution saving throw, taking 10 (3d6) Poison damage on a failed save or half as much damage on a successful one.",
    ),
    (
        ("Poison", "Sample Poisons", "Spider's Sting (200 GP)"),
        "#### Spider's Sting (200 GP)",
    ),
    (("Poison", "Sample Poisons", "Spider's Sting (200 GP)"), "_Injury Poison_"),
    (
        ("Poison", "Sample Poisons", "Spider's Sting (200 GP)"),
        "A creature subjected to Spider's Sting must succeed on a DC 13 Constitution saving throw or have the Poisoned condition for 1 hour. If the creature fails the save by 5 or more, the creature also has the Unconscious condition while Poisoned in this way. The creature wakes up if it takes damage or if another creature takes an action to shake it awake.",
    ),
    (("Poison", "Sample Poisons", "Torpor (600 GP)"), "#### Torpor (600 GP)"),
    (("Poison", "Sample Poisons", "Torpor (600 GP)"), "_Ingested Poison_"),
    (
        ("Poison", "Sample Poisons", "Torpor (600 GP)"),
        "A creature subjected to Torpor poison must succeed on a DC 15 Constitution saving throw or have the Poisoned condition for 4d6 hours. The creature's Speed is halved while the creature is Poisoned in this way.",
    ),
    (("Poison", "Sample Poisons", "Truth Serum (150 GP)"), "#### Truth Serum (150 GP)"),
    (("Poison", "Sample Poisons", "Truth Serum (150 GP)"), "_Ingested Poison_"),
    (
        ("Poison", "Sample Poisons", "Truth Serum (150 GP)"),
        "A creature subjected to Truth Serum must succeed on a DC 11 Constitution saving throw or have the Poisoned condition for 1 hour. The Poisoned creature can't knowingly communicate a lie.",
    ),
    (
        ("Poison", "Sample Poisons", "Wyvern Poison (1,200 GP)"),
        "#### Wyvern Poison (1,200 GP)",
    ),
    (("Poison", "Sample Poisons", "Wyvern Poison (1,200 GP)"), "_Injury Poison_"),
    (
        ("Poison", "Sample Poisons", "Wyvern Poison (1,200 GP)"),
        "A creature subjected to Wyvern Poison makes a DC 14 Constitution saving throw, taking 24 (7d6) Poison damage on a failed save or half as much damage on a successful one.",
    ),
    (("Traps",), "## Traps"),
    (
        ("Traps",),
        "Traps should be used sparingly, lest they lose their charm. A hidden pit can be a fun surprise, but too many traps in an adventure can lead players to become overly cautious, which slows down the game.",
    ),
    (
        ("Traps",),
        "The best traps are fleeting distractions that skilled characters can overcome in a short amount of time or deadly puzzles that require quick thinking and teamwork to overcome. Traps that are undetectable and inescapable are rarely fun.",
    ),
    (("Traps", "Parts of a Trap"), "### Parts of a Trap"),
    (
        ("Traps", "Parts of a Trap"),
        "The description of a trap includes the following parts after the trap's name:",
    ),
    (
        ("Traps", "Parts of a Trap"),
        "**Severity and Levels.** A trap is designated as a nuisance or as deadly for characters of certain levels. A nuisance trap is unlikely to seriously harm characters of the indicated levels, whereas a deadly trap can grievously damage characters of the indicated levels.",
    ),
    (
        ("Traps", "Parts of a Trap"),
        "**Trigger.** Traps are often set to go off when a creature enters an area or touches an object. Examples of triggers include stepping on a pressure plate, crossing a trip wire, turning a doorknob, or using the wrong key in a lock.",
    ),
    (
        ("Traps", "Parts of a Trap"),
        "**Duration.** Some traps have durations expressed in rounds, minutes, or hours. Others specify that their effects last until the trap is destroyed or dispelled. If a trap's duration is instantaneous, its effect is resolved instantly. If a trap resets after activating, that fact is noted in this entry. A trap is otherwise inert after activation.",
    ),
    (
        ("Traps", "Parts of a Trap"),
        "Use caution when introducing a trap to characters of a level lower than the trap's level range. A trap that is a nuisance at one level range could be deadly to characters of a lower level range.",
    ),
    (("Traps", "Example Traps"), "### Example Traps"),
    (("Traps", "Example Traps"), "Traps are presented in alphabetical order."),
    (("Traps", "Example Traps", "Collapsing Roof"), "#### Collapsing Roof"),
    (("Traps", "Example Traps", "Collapsing Roof"), "_Deadly Trap (Levels 1–4)_"),
    (
        ("Traps", "Example Traps", "Collapsing Roof"),
        "**Trigger:** A creature crosses a trip wire\n**Duration:** Instantaneous",
    ),
    (
        ("Traps", "Example Traps", "Collapsing Roof"),
        "This trap uses a trip wire to collapse an unstable section of ceiling. The trip wire is 3 inches off the ground and stretches between two weak supports that topple when the trip wire is pulled.",
    ),
    (
        ("Traps", "Example Traps", "Collapsing Roof"),
        "The first creature that crosses the trip wire causes the supports to topple and the unstable section of ceiling to collapse. Each creature beneath the unstable section of ceiling must succeed on a DC 13 Dexterity saving throw, taking 11 (2d10) Bludgeoning damage on a failed save or half as much damage on a successful one. Rubble from the collapse turns the trapped area into Difficult Terrain.",
    ),
    (
        ("Traps", "Example Traps", "Collapsing Roof"),
        "_Detect and Disarm._ As a Search action, a creature can examine the trapped area and make a DC 11 Wisdom (Perception) check, detecting the trip wire and the unstable section of ceiling on a successful check. Once detected, the trip wire can be easily cut or avoided (no ability check required).",
    ),
    (
        ("Traps", "Example Traps", "Collapsing Roof"),
        "_At Higher Levels._ You can scale the trap for higher levels by increasing the damage and the save DC, as shown in the following table.",
    ),
    (
        ("Traps", "Example Traps", "Collapsing Roof"),
        "<table>\n  <thead>\n    <tr>\n      <th>Levels</th>\n      <th>Bludgeoning Damage</th>\n      <th>Save DC</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>5–10</td>\n      <td>22 (4d10)</td>\n      <td>15</td>\n    </tr>\n    <tr>\n      <td>11–16</td>\n      <td>55 (10d10)</td>\n      <td>17</td>\n    </tr>\n    <tr>\n      <td>17–20</td>\n      <td>99 (18d10)</td>\n      <td>19</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (("Traps", "Example Traps", "Falling Net"), "#### Falling Net"),
    (("Traps", "Example Traps", "Falling Net"), "_Nuisance Trap (Levels 1–4)_"),
    (
        ("Traps", "Example Traps", "Falling Net"),
        "**Trigger:** A creature crosses a trip wire\n**Duration:** Instantaneous",
    ),
    (
        ("Traps", "Example Traps", "Falling Net"),
        "A falling net trap uses a trip wire to release a weighted, 10-foot-square Net suspended from the ceiling. The trip wire is 3 inches off the ground and stretches between two columns or trees.",
    ),
    (
        ("Traps", "Example Traps", "Falling Net"),
        "The first creature that crosses the trip wire causes the Net to fall on it. The target must succeed on a DC 10 Dexterity saving throw or have the Restrained condition until it escapes. The target succeeds automatically if it's Huge or larger. A creature can take an action to make a DC 10 Strength (Athletics) check, freeing itself or another creature within its reach from the Net on a successful check.",
    ),
    (
        ("Traps", "Example Traps", "Falling Net"),
        "_Detect and Disarm._ As a Search action, a creature can examine the trapped area and make a DC 11 Wisdom (Perception) check, detecting the trip wire and the suspended Net on a successful check. Once detected, the trip wire can be easily cut or avoided (no ability check required).",
    ),
    (
        ("Traps", "Example Traps", "Falling Net"),
        '_Destroy the Net._ Reducing the Net to 0 Hit Points frees any creature trapped in it (see "Adventuring Gear" for the Net\'s statistics).',
    ),
    (
        ("Traps", "Example Traps", "Falling Net"),
        "_Set the Trap._ A creature that has Thieves' Tools and all the trap's components (including a Net) can try to set a falling net trap, doing so with a successful DC 13 Dexterity (Sleight of Hand) check. Each attempt to set this trap takes 10 minutes.",
    ),
    (
        ("Traps", "Example Traps", "Falling Net"),
        "_At Higher Levels._ You can scale the trap for higher levels by increasing the weight of the Net, which increases the save DC and the DC of the Strength (Athletics) check as follows: DC 12 at levels 5–10, DC 14 at levels 11–16, or DC 16 at levels 17–20.",
    ),
    (("Traps", "Example Traps", "Fire-Casting Statue"), "#### Fire-Casting Statue"),
    (("Traps", "Example Traps", "Fire-Casting Statue"), "_Deadly Trap (Levels 1–4)_"),
    (
        ("Traps", "Example Traps", "Fire-Casting Statue"),
        "**Trigger:** A creature moves onto a pressure plate\n**Duration:** Instantaneous, and the trap resets at the start of the next turn",
    ),
    (
        ("Traps", "Example Traps", "Fire-Casting Statue"),
        "When a creature moves onto this trap's pressure plate for the first time on a turn or starts its turn there, a nearby statue exhales a 15-foot Cone of magical flame. The statue can look like anything, such as a dragon or a wizard. Each creature in the Cone must succeed on a DC 15 Dexterity saving throw, taking 11 (2d10) Fire damage on a failed save or half as much damage on a successful one.",
    ),
    (
        ("Traps", "Example Traps", "Fire-Casting Statue"),
        '_Detect and Disarm._ A _Detect Magic_ spell reveals an aura of Evocation magic around the statue. As a Search action, a creature within 5 feet of the statue can examine it and make a DC 10 Wisdom (Perception) check, detecting a tiny glyph on the statue on a successful check. Once the glyph is found, a character can take a Study action to examine it and make a DC 15 Intelligence (Arcana) check, ascertaining that the glyph means "fire" on a successful check. As an action, a character can use a sharp tool to deface the glyph, which disarms the trap.',
    ),
    (
        ("Traps", "Example Traps", "Fire-Casting Statue"),
        "As a Search action, a creature can examine the section of floor that forms the pressure plate and make a DC 15 Wisdom (Perception) check, detecting the pressure plate on a successful check. Wedging an Iron Spike or similar object under the pressure plate prevents the trap from triggering.",
    ),
    (
        ("Traps", "Example Traps", "Fire-Casting Statue"),
        "_At Higher Levels._ You can scale the trap for higher levels by increasing the damage and the area of effect, as shown in the following table.",
    ),
    (
        ("Traps", "Example Traps", "Fire-Casting Statue"),
        "<table>\n  <thead>\n    <tr>\n      <th>Levels</th>\n      <th>Fire Damage</th>\n      <th>Area of Effect</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>5–10</td>\n      <td>22 (4d10)</td>\n      <td>30-foot Cone</td>\n    </tr>\n    <tr>\n      <td>11–16</td>\n      <td>55 (10d10)</td>\n      <td>60-foot Cone</td>\n    </tr>\n    <tr>\n      <td>17–20</td>\n      <td>99 (18d10)</td>\n      <td>120-foot Cone</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (("Traps", "Example Traps", "Hidden Pit"), "#### Hidden Pit"),
    (("Traps", "Example Traps", "Hidden Pit"), "_Nuisance Trap (Levels 1–4)_"),
    (
        ("Traps", "Example Traps", "Hidden Pit"),
        "**Trigger:** A creature moves onto the pit's lid\n**Duration:** Instantaneous",
    ),
    (
        ("Traps", "Example Traps", "Hidden Pit"),
        "This 10-foot-deep pit has a hinged lid constructed from material identical to the surrounding floor. When a creature moves onto the lid, it swings open like a trapdoor, causing the creature to fall into the pit. The lid remains open thereafter.",
    ),
    (
        ("Traps", "Example Traps", "Hidden Pit"),
        "A creature that falls into the pit takes 3 (1d6) Bludgeoning damage from the fall.",
    ),
    (
        ("Traps", "Example Traps", "Hidden Pit"),
        "_Detect and Disarm._ As a Study action, a creature can examine the section of floor that forms the pit's lid and make a DC 15 Intelligence (Investigation) check, detecting the pit on a successful check. Once the pit is detected, an Iron Spike or a similar object can be wedged between the pit's lid and the surrounding floor to prevent the lid from opening, thereby making it safe to cross. The cover can also be held shut using _Arcane Lock_ or similar magic.",
    ),
    (
        ("Traps", "Example Traps", "Hidden Pit"),
        "_Escape._ A creature needs a Climb Speed, climbing gear, or magic such as _Spider Climb_ to scale the pit's smooth walls. You can make the pit easier to escape by adding cracks in the walls big enough to serve as handholds and footholds.",
    ),
    (
        ("Traps", "Example Traps", "Hidden Pit"),
        "_At Higher Levels._ You can scale the trap for higher levels by increasing the pit's depth and damage, as shown in the following table.",
    ),
    (
        ("Traps", "Example Traps", "Hidden Pit"),
        "<table>\n  <thead>\n    <tr>\n      <th>Levels</th>\n      <th>Pit Depth</th>\n      <th>Bludgeoning Damage</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>5–10</td>\n      <td>30 feet</td>\n      <td>10 (3d6)</td>\n    </tr>\n    <tr>\n      <td>11–16</td>\n      <td>60 feet</td>\n      <td>21 (6d6)</td>\n    </tr>\n    <tr>\n      <td>17–20</td>\n      <td>120 feet</td>\n      <td>42 (12d6)</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (("Traps", "Example Traps", "Poisoned Darts"), "#### Poisoned Darts"),
    (("Traps", "Example Traps", "Poisoned Darts"), "_Deadly Trap (Levels 1–4)_"),
    (
        ("Traps", "Example Traps", "Poisoned Darts"),
        "**Trigger:** A creature moves onto a pressure plate\n**Duration:** Instantaneous, and the trap resets at the start of the next turn if it has activated fewer than three times",
    ),
    (
        ("Traps", "Example Traps", "Poisoned Darts"),
        "When a creature moves onto this trap's pressure plate for the first time on a turn, poisoned darts shoot from tubes embedded in the surrounding walls. The holes that house these tubes are obscured by dust and cobwebs or skillfully hidden amid bas-reliefs, murals, or frescoes.",
    ),
    (
        ("Traps", "Example Traps", "Poisoned Darts"),
        "Each creature in the darts' path must succeed on a DC 13 Dexterity saving throw or be struck by 1d3 darts, taking 3 (1d6) Poison damage per dart.",
    ),
    (
        ("Traps", "Example Traps", "Poisoned Darts"),
        "_Detect and Disarm._ As a Search action, a creature can examine the walls and make a DC 15 Wisdom (Perception) check, detecting the holes on a successful check. Plugging all the holes with wax, cloth, or detritus prevents the darts from firing.",
    ),
    (
        ("Traps", "Example Traps", "Poisoned Darts"),
        "As a Search action, a creature can examine the section of floor that forms the pressure plate and make a DC 15 Wisdom (Perception) check, detecting the pressure plate on a successful check. Wedging an Iron Spike or a similar object under the pressure plate prevents the trap from triggering.",
    ),
    (
        ("Traps", "Example Traps", "Poisoned Darts"),
        "_At Higher Levels._ You can scale the trap for higher levels by increasing each dart's Poison damage as follows: 7 (2d6) at levels 5–10, 14 (4d6) at levels 11–16, or 24 (7d6) at levels 17–20.",
    ),
    (("Traps", "Example Traps", "Poisoned Needle"), "#### Poisoned Needle"),
    (("Traps", "Example Traps", "Poisoned Needle"), "_Nuisance Trap (Levels 1–4)_"),
    (
        ("Traps", "Example Traps", "Poisoned Needle"),
        "**Trigger:** A creature opens the trap's lock improperly or fails to disarm the trap\n**Duration:** Instantaneous",
    ),
    (
        ("Traps", "Example Traps", "Poisoned Needle"),
        "A poisoned needle is hidden in a lock. When a creature opens the lock with any object other than the proper key, the needle springs out and stabs the creature. The creature makes a DC 11 Constitution saving throw. On a failed save, the creature takes 5 (1d10) Poison damage and has the Poisoned\ncondition for 1 hour. On a successful save, the creature takes half as much damage only.",
    ),
    (
        ("Traps", "Example Traps", "Poisoned Needle"),
        "_Avoid._ The trap doesn't trigger if the lock is opened using a _Knock_ spell or similar magic.",
    ),
    (
        ("Traps", "Example Traps", "Poisoned Needle"),
        "_Detect and Disarm._ As a Search action, a creature can examine the trapped lock and make a DC 15 Wisdom (Perception) check, detecting the needle on a successful check. Once the trap is detected, a character can take an action to try to disarm the trap, doing so with a successful DC 15 Dexterity (Sleight of Hand) check. On a failed check, the creature triggers the trap.",
    ),
    (
        ("Traps", "Example Traps", "Poisoned Needle"),
        "_At Higher Levels._ You can scale the trap for higher levels by increasing the damage and the save DC, as shown in the following table.",
    ),
    (
        ("Traps", "Example Traps", "Poisoned Needle"),
        "<table>\n  <thead>\n    <tr>\n      <th>Levels</th>\n      <th>Poison Damage</th>\n      <th>Save DC</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>5–10</td>\n      <td>11 (2d10)</td>\n      <td>13</td>\n    </tr>\n    <tr>\n      <td>11–16</td>\n      <td>22 (4d10)</td>\n      <td>15</td>\n    </tr>\n    <tr>\n      <td>17–20</td>\n      <td>55 (10d10)</td>\n      <td>17</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (("Traps", "Example Traps", "Rolling Stone"), "#### Rolling Stone"),
    (
        ("Traps", "Example Traps", "Rolling Stone"),
        "_Deadly Trap (Levels 11–16) or Nuisance Trap (Levels 17–20)_",
    ),
    (
        ("Traps", "Example Traps", "Rolling Stone"),
        "**Trigger:** A creature moves onto a pressure plate\n**Duration:** Until the stone stops rolling",
    ),
    (
        ("Traps", "Example Traps", "Rolling Stone"),
        "When a creature moves onto a hidden pressure plate, a 5-foot-radius orb of solid stone is released from a secret compartment and begins to roll. The stone and all creatures nearby roll Initiative; the stone gets a +8 bonus on its Initiative roll.",
    ),
    (
        ("Traps", "Example Traps", "Rolling Stone"),
        "On its turn, the stone moves 60 feet in one direction, changing course if redirected by an obstacle. The stone can move through creatures' spaces, and creatures can move through the stone's space, treating it as Difficult Terrain. Whenever the stone enters a creature's space for the first time on a turn or a creature enters the stone's space while the stone is rolling, that creature must succeed on a DC 15 Dexterity saving throw or take 55 (10d10) Bludgeoning damage and have the Prone condition.",
    ),
    (
        ("Traps", "Example Traps", "Rolling Stone"),
        "The stone stops when it hits a wall or similar barrier. It can't go around corners, but creative dungeon builders incorporate curving turns into nearby passages that allow the stone to keep moving.",
    ),
    (
        ("Traps", "Example Traps", "Rolling Stone"),
        "_Detect and Disarm._ As a Study action, a creature can examine the section of floor that forms the pressure plate and make a DC 15 Intelligence (Investigation) check, deducing the pressure plate's function on a successful check. Wedging an Iron Spike or a similar object under the pressure plate prevents the trap from triggering.",
    ),
    (
        ("Traps", "Example Traps", "Rolling Stone"),
        "_Destroy the Stone._ The stone is a Large object that has AC 17, HP 100, a Damage Threshold of 10, and Immunity to Poison and Psychic damage.",
    ),
    (
        ("Traps", "Example Traps", "Rolling Stone"),
        "_Slow the Stone._ As an action, a creature can try to slow down the stone with a DC 20 Strength (Athletics) check. If the check is successful, the distance the stone moves on its turn is reduced by 15 feet. If that distance drops to 0, it stops moving and is no longer a threat.",
    ),
    (("Traps", "Example Traps", "Spiked Pit"), "#### Spiked Pit"),
    (("Traps", "Example Traps", "Spiked Pit"), "_Deadly Trap (Levels 1–4)_"),
    (
        ("Traps", "Example Traps", "Spiked Pit"),
        "**Trigger:** A creature moves onto the pit's lid\n**Duration:** Instantaneous",
    ),
    (
        ("Traps", "Example Traps", "Spiked Pit"),
        "A 10-foot-deep pit has a hinged lid constructed from material identical to the surrounding floor. When a creature moves onto the lid, it swings open like a trapdoor, causing the creature to fall into the pit, which has sharpened wooden or metal spikes at the bottom. The lid remains open thereafter.",
    ),
    (
        ("Traps", "Example Traps", "Spiked Pit"),
        "A creature that falls into the pit lands at the bottom and takes 3 (1d6) Bludgeoning damage from the fall plus 9 (2d8) Piercing damage from the spikes.",
    ),
    (
        ("Traps", "Example Traps", "Spiked Pit"),
        "_Detect and Disarm._ As a Study action, a creature can examine the section of floor that forms the pit's lid and make a DC 15 Intelligence (Investigation) check, detecting the pit on a successful check. Once the hidden pit is detected, an Iron Spike or a similar object can be wedged between the pit's lid and the surrounding floor to prevent the lid from opening, thereby making it safe to cross. The cover can also be held shut using an _Arcane Lock_ spell or similar magic.",
    ),
    (
        ("Traps", "Example Traps", "Spiked Pit"),
        "_Escape._ A creature needs a Climb Speed, climbing gear, or magic such as a _Spider Climb_ spell to scale the pit's smooth walls. You can make the pit easier to escape by adding cracks in the walls big enough to serve as handholds and footholds.",
    ),
    (
        ("Traps", "Example Traps", "Spiked Pit"),
        "_At Higher Levels._ You can scale the trap for higher levels by increasing the pit's depth and damage, as shown in the following table.",
    ),
    (
        ("Traps", "Example Traps", "Spiked Pit"),
        "<table>\n  <thead>\n    <tr>\n      <th>Levels</th>\n      <th>Pit Depth</th>\n      <th>Damage</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>5–10</td>\n      <td>30 feet</td>\n      <td>10 (3d6) Bludgeoning plus 13 (3d8) Piercing</td>\n    </tr>\n    <tr>\n      <td>11–16</td>\n      <td>60 feet</td>\n      <td>21 (6d6) Bludgeoning plus 36 (8d8) Piercing</td>\n    </tr>\n    <tr>\n      <td>17–20</td>\n      <td>120 feet</td>\n      <td>42 (12d6) Bludgeoning plus 57 (13d8) Piercing</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (("Combat Encounters",), "## Combat Encounters"),
    (
        ("Combat Encounters",),
        "The following features can make a combat encounter more interesting or challenging:",
    ),
    (
        ("Combat Encounters",),
        "**Changes in Elevation.** Terrain features that provide a change of elevation (such as stacks of empty crates, ledges, and balconies) reward clever positioning and encourage characters to jump, climb, fly, or teleport.",
    ),
    (
        ("Combat Encounters",),
        "**Defensive Positions.** Enemies in hard-to-reach locations or defensive positions force characters who normally attack at range to move around.",
    ),
    (
        ("Combat Encounters",),
        "**Mixed Monster Groups.** When different types of monsters work together, they can combine their abilities—just like characters with different classes and origins. A diverse force is more powerful.",
    ),
    (
        ("Combat Encounters",),
        "**Reasons to Move.** Use features that encourage characters and their enemies to move around, such as chandeliers, kegs of gunpowder or oil, and rolling stone traps.",
    ),
    (
        ("Combat Encounters", "Combat Encounter Difficulty"),
        "### Combat Encounter Difficulty",
    ),
    (
        ("Combat Encounters", "Combat Encounter Difficulty"),
        "Use the following guidelines to create a combat encounter of a desired level of difficulty.",
    ),
    (
        (
            "Combat Encounters",
            "Combat Encounter Difficulty",
            "Step 1: Choose a Difficulty",
        ),
        "#### Step 1: Choose a Difficulty",
    ),
    (
        (
            "Combat Encounters",
            "Combat Encounter Difficulty",
            "Step 1: Choose a Difficulty",
        ),
        "Three categories describe the range of encounter difficulty:",
    ),
    (
        (
            "Combat Encounters",
            "Combat Encounter Difficulty",
            "Step 1: Choose a Difficulty",
        ),
        "**Low Difficulty.** An encounter of low difficulty is likely to have one or two scary moments for the players, but their characters should emerge victorious with no casualties. One or more of them might need to use healing resources, however. As a rough guideline, a single monster generally presents a low-difficulty challenge for a party of four characters whose level equals the monster's Challenge Rating.",
    ),
    (
        (
            "Combat Encounters",
            "Combat Encounter Difficulty",
            "Step 1: Choose a Difficulty",
        ),
        "**Moderate Difficulty.** Absent healing and other resources, an encounter of moderate difficulty could go badly for the adventurers. Weaker characters might get taken out of the fight, and there's a slim chance that one or more characters might die.",
    ),
    (
        (
            "Combat Encounters",
            "Combat Encounter Difficulty",
            "Step 1: Choose a Difficulty",
        ),
        "**High Difficulty.** A high-difficulty encounter could be lethal for one or more characters. To survive it, the characters will need smart tactics, quick thinking, and maybe even a little luck.",
    ),
    (
        (
            "Combat Encounters",
            "Combat Encounter Difficulty",
            "Step 2: Determine Your XP Budget",
        ),
        "#### Step 2: Determine Your XP Budget",
    ),
    (
        (
            "Combat Encounters",
            "Combat Encounter Difficulty",
            "Step 2: Determine Your XP Budget",
        ),
        "Using the XP Budget per Character table, cross-reference the party's level with the desired encounter difficulty. Multiply the number in the table by the number of characters in the party to get your XP budget for the encounter.",
    ),
    (
        (
            "Combat Encounters",
            "Combat Encounter Difficulty",
            "Step 2: Determine Your XP Budget",
        ),
        "**XP Budget per Character**\n\n<table>\n  <thead>\n    <tr>\n      <th>Party's Level</th>\n      <th>Encounter Difficulty Low</th>\n      <th>Encounter Difficulty Moderate</th>\n      <th>Encounter Difficulty High</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>1</td>\n      <td>50</td>\n      <td>75</td>\n      <td>100</td>\n    </tr>\n    <tr>\n      <td>2</td>\n      <td>100</td>\n      <td>150</td>\n      <td>200</td>\n    </tr>\n    <tr>\n      <td>3</td>\n      <td>150</td>\n      <td>225</td>\n      <td>400</td>\n    </tr>\n    <tr>\n      <td>4</td>\n      <td>250</td>\n      <td>375</td>\n      <td>500</td>\n    </tr>\n    <tr>\n      <td>5</td>\n      <td>500</td>\n      <td>750</td>\n      <td>1,100</td>\n    </tr>\n    <tr>\n      <td>6</td>\n      <td>600</td>\n      <td>1,000</td>\n      <td>1,400</td>\n    </tr>\n    <tr>\n      <td>7</td>\n      <td>750</td>\n      <td>1,300</td>\n      <td>1,700</td>\n    </tr>\n    <tr>\n      <td>8</td>\n      <td>1,000</td>\n      <td>1,700</td>\n      <td>2,100</td>\n    </tr>\n    <tr>\n      <td>9</td>\n      <td>1,300</td>\n      <td>2,000</td>\n      <td>2,600</td>\n    </tr>\n    <tr>\n      <td>10</td>\n      <td>1,600</td>\n      <td>2,300</td>\n      <td>3,100</td>\n    </tr>\n    <tr>\n      <td>11</td>\n      <td>1,900</td>\n      <td>2,900</td>\n      <td>4,100</td>\n    </tr>\n    <tr>\n      <td>12</td>\n      <td>2,200</td>\n      <td>3,700</td>\n      <td>4,700</td>\n    </tr>\n    <tr>\n      <td>13</td>\n      <td>2,600</td>\n      <td>4,200</td>\n      <td>5,400</td>\n    </tr>\n    <tr>\n      <td>14</td>\n      <td>2,900</td>\n      <td>4,900</td>\n      <td>6,200</td>\n    </tr>\n    <tr>\n      <td>15</td>\n      <td>3,300</td>\n      <td>5,400</td>\n      <td>7,800</td>\n    </tr>\n    <tr>\n      <td>16</td>\n      <td>3,800</td>\n      <td>6,100</td>\n      <td>9,800</td>\n    </tr>\n    <tr>\n      <td>17</td>\n      <td>4,500</td>\n      <td>7,200</td>\n      <td>11,700</td>\n    </tr>\n    <tr>\n      <td>18</td>\n      <td>5,000</td>\n      <td>8,700</td>\n      <td>14,200</td>\n    </tr>\n    <tr>\n      <td>19</td>\n      <td>5,500</td>\n      <td>10,700</td>\n      <td>17,200</td>\n    </tr>\n    <tr>\n      <td>20</td>\n      <td>6,400</td>\n      <td>13,200</td>\n      <td>22,000</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        ("Combat Encounters", "Step 3: Spend Your Budget"),
        "### Step 3: Spend Your Budget",
    ),
    (
        ("Combat Encounters", "Step 3: Spend Your Budget"),
        "Every creature has an XP value in its stat block. When you add a creature to your combat encounter, deduct its XP from your XP budget to determine how many XP you have left to spend. Spend as much of your XP budget as you can without going over. It's OK if you have a few unspent XP left over. Examples are given below:",
    ),
    (
        ("Combat Encounters", "Step 3: Spend Your Budget"),
        "**Example 1.** A low-difficulty encounter for four level 1 characters has an XP budget of 50 × 4, for a total of 200 XP. With that, you could build any of the following encounters:",
    ),
    (
        ("Combat Encounters", "Step 3: Spend Your Budget"),
        "- **1 Bugbear Warrior** (200 XP)\n- **2 Giant Wasps** (100 XP each), for 200 XP total\n- **6 Giant Rats** (25 XP each), for 150 XP total",
    ),
    (
        ("Combat Encounters", "Step 3: Spend Your Budget"),
        "**Example 2.** A moderate-difficulty encounter for five level 3 characters has an XP budget of 225 × 5, for a total of 1,125 XP. With that, you could build either of these encounters:",
    ),
    (
        ("Combat Encounters", "Step 3: Spend Your Budget"),
        "- **2 Druids** (450 XP each) and **9 Stirges** (25 XP each), for 1,125 XP total\n- **1 Wight** (700 XP), **1 Warhorse Skeleton** (100 XP), and **6 Skeletons** (50 XP each), for 1,100 XP total\n  **Example 3.** A high-difficulty encounter for six level 15 characters has an XP budget of 7,800 × 6, for a total of 46,800 XP. With that, you could build this encounter:",
    ),
    (
        ("Combat Encounters", "Step 3: Spend Your Budget"),
        "• **2 Adult Red Dragons** (18,000 XP each) and **2 Fire Giants** (5,000 XP each), for 46,000 XP total",
    ),
    (("Troubleshooting",), "## Troubleshooting"),
    (
        ("Troubleshooting",),
        "When creating and running combat encounters, keep the following in mind.",
    ),
    (("Troubleshooting", "Many Creatures"), "### Many Creatures"),
    (
        ("Troubleshooting", "Many Creatures"),
        "The more creatures in an encounter, the higher the risk that a lucky streak on their part could deal more damage to the characters than you expect. If your encounter includes more than two creatures per character, include fragile creatures that can be defeated quickly. This guideline is especially important for characters of level 1 or 2.",
    ),
    (("Troubleshooting", "Adjustments"), "### Adjustments"),
    (
        ("Troubleshooting", "Adjustments"),
        "A player's absence might warrant removing creatures from an encounter to keep it at the intended difficulty. Also, die rolls and other factors can result in an encounter being easier or harder than intended. You can adjust an encounter on the fly, such as by having creatures flee (making the encounter easier) or adding reinforcements (making the encounter harder).",
    ),
    (("Troubleshooting", "CR 0 Creatures"), "### CR 0 Creatures"),
    (
        ("Troubleshooting", "CR 0 Creatures"),
        "Creatures that have a CR of 0, particularly ones that are worth 0 XP, should be used sparingly. If you want to include many CR 0 critters in an encounter, use swarms instead.",
    ),
    (("Troubleshooting", "Number of Stat Blocks"), "### Number of Stat Blocks"),
    (
        ("Troubleshooting", "Number of Stat Blocks"),
        "The best combat encounters often pair one kind of creature with another, such as fire giants paired with hell hounds. Be mindful of the number of stat blocks you need to run the encounter. Referencing more than two or three stat blocks for a single encounter can be daunting, particularly if the creatures are complex.",
    ),
    (("Troubleshooting", "Powerful Creatures"), "### Powerful Creatures"),
    (
        ("Troubleshooting", "Powerful Creatures"),
        "If your combat encounter includes a creature whose CR is higher than the party's level, be aware that such a creature might deal enough damage with a single action to take out one or more characters. For example, an **Ogre** (CR 2) can kill a level 1 Wizard with a single blow.",
    ),
    (("Troubleshooting", "Unusual Features"), "### Unusual Features"),
    (
        ("Troubleshooting", "Unusual Features"),
        "If a monster has a feature that lower-level characters can't easily overcome, consider not adding that monster to an encounter for characters whose level is lower than the monster's Challenge Rating.",
    ),
)
