# ruff: noqa: E501
"""The SRD 5.2.1 *Animals* part as the release prints it -- CRD Issue 5d.

Every leaf of the part below its ``# Animals`` heading, in printed order
(pp. 344-364), as (full container label path, exact leaf text). Each text was
qualified against the official PDF (``docs/sources/DnD5_5e_SRD_CC_v5_2_1.pdf``)
before it was written here: prose word for word, every table row cell for
cell, every stat block's ability table by its MOD and SAVE columns, and the
part's printed order in the PDF's column stream (see the animals review
packet). The part heading is left with the other part headings. The generator
names its spans from these texts; a text the release prints differently fails
to locate, loudly.
"""

from __future__ import annotations

LEAVES: tuple[tuple[tuple[str, ...], str], ...] = (
    (
        (
            "Animals",
            "Allosaurus",
        ),
        "## Allosaurus",
    ),
    (
        (
            "Animals",
            "Allosaurus",
        ),
        "_Large Beast (Dinosaur), Unaligned_",
    ),
    (
        (
            "Animals",
            "Allosaurus",
        ),
        "**AC** 13 **Initiative** +1 (11) <br>\n**HP** 51 (6d10 + 18) <br>\n**Speed** 60 ft. <br>",
    ),
    (
        (
            "Animals",
            "Allosaurus",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>19</td>\n      <td>+4</td>\n      <td>+4</td>\n      <td><strong>DEX</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CON</strong></td>\n      <td>17</td>\n      <td>+3</td>\n      <td>+3</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>2</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>WIS</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CHA</strong></td>\n      <td>5</td>\n      <td>−3</td>\n      <td>−3</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Allosaurus",
        ),
        "**Skills** Perception +5<br>\n**Senses** Passive Perception 15<br>\n**Languages** None<br>\n**CR** 2 (XP 450; PB +2)",
    ),
    (
        (
            "Animals",
            "Allosaurus",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Allosaurus",
            "Actions",
        ),
        "**_Bite._** _Melee Attack Roll:_ +6, reach 5 ft. _Hit:_ 15 (2d10 + 4) Piercing damage.",
    ),
    (
        (
            "Animals",
            "Allosaurus",
            "Actions",
        ),
        "**_Claws._** _Melee Attack Roll:_ +6, reach 5 ft. _Hit:_ 8 (1d8 + 4) Slashing damage. If the target is a Large or smaller creature and the allosaurus moved 30+ feet straight toward it immediately before the hit, the target has the Prone condition, and the allosaurus can make one Bite attack against it.",
    ),
    (
        (
            "Animals",
            "Ankylosaurus",
        ),
        "## Ankylosaurus",
    ),
    (
        (
            "Animals",
            "Ankylosaurus",
        ),
        "_Huge Beast (Dinosaur), Unaligned_",
    ),
    (
        (
            "Animals",
            "Ankylosaurus",
        ),
        "**AC** 15 **Initiative** +0 (10) <br>\n**HP** 68 (8d12 + 16) <br>\n**Speed** 30 ft. <br>",
    ),
    (
        (
            "Animals",
            "Ankylosaurus",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>19</td>\n      <td>+4</td>\n      <td>+6</td>\n      <td><strong>DEX</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CON</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>2</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>WIS</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CHA</strong></td>\n      <td>5</td>\n      <td>−3</td>\n      <td>−3</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Ankylosaurus",
        ),
        "**Senses** Passive Perception 11<br>\n**Languages** None<br>\n**CR** 3 (XP 700; PB +2)",
    ),
    (
        (
            "Animals",
            "Ankylosaurus",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Ankylosaurus",
            "Actions",
        ),
        "**_Multiattack._** The ankylosaurus makes two Tail attacks.",
    ),
    (
        (
            "Animals",
            "Ankylosaurus",
            "Actions",
        ),
        "**_Tail._** _Melee Attack Roll:_ +6, reach 10 ft. _Hit:_ 9 (1d10 + 4) Bludgeoning damage. If the target is a Huge or smaller creature, it has the Prone condition.",
    ),
    (
        (
            "Animals",
            "Ape",
        ),
        "## Ape",
    ),
    (
        (
            "Animals",
            "Ape",
        ),
        "_Medium Beast, Unaligned_",
    ),
    (
        (
            "Animals",
            "Ape",
        ),
        "**AC** 12 **Initiative** +2 (12) <br>\n**HP** 19 (3d8 + 6) <br>\n**Speed** 30 ft., Climb 30 ft. <br>",
    ),
    (
        (
            "Animals",
            "Ape",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>DEX</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CON</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>6</td>\n      <td>−2</td>\n      <td>−2</td>\n      <td><strong>WIS</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CHA</strong></td>\n      <td>7</td>\n      <td>−2</td>\n      <td>−2</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Ape",
        ),
        "**Skills** Athletics +5, Perception +3<br>\n**Senses** Passive Perception 13<br>\n**Languages** None<br>\n**CR** 1/2 (XP 100; PB +2)",
    ),
    (
        (
            "Animals",
            "Ape",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Ape",
            "Actions",
        ),
        "**_Multiattack._** The ape makes two Fist attacks.",
    ),
    (
        (
            "Animals",
            "Ape",
            "Actions",
        ),
        "**_Fist._** _Melee Attack Roll:_ +5, reach 5 ft. _Hit:_ 5 (1d4 + 3) Bludgeoning damage.",
    ),
    (
        (
            "Animals",
            "Ape",
            "Actions",
        ),
        "**_Rock (Recharge 6)._** _Ranged Attack Roll:_ +5, range 25/50 ft. _Hit:_ 10 (2d6 + 3) Bludgeoning damage.",
    ),
    (
        (
            "Animals",
            "Archelon",
        ),
        "## Archelon",
    ),
    (
        (
            "Animals",
            "Archelon",
        ),
        "_Huge Beast (Dinosaur), Unaligned_",
    ),
    (
        (
            "Animals",
            "Archelon",
        ),
        "**AC** 17 **Initiative** +3 (13) <br>\n**HP** 90 (12d12 + 12) <br>\n**Speed** 20 ft., Swim 80 ft. <br>",
    ),
    (
        (
            "Animals",
            "Archelon",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+4</td>\n      <td><strong>DEX</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>CON</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>4</td>\n      <td>−3</td>\n      <td>−3</td>\n      <td><strong>WIS</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CHA</strong></td>\n      <td>6</td>\n      <td>−2</td>\n      <td>−2</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Archelon",
        ),
        "**Skills** Stealth +5<br>\n**Senses** Passive Perception 12<br>\n**Languages** None<br>\n**CR** 4 (XP 1,100; PB +2)",
    ),
    (
        (
            "Animals",
            "Archelon",
            "Traits",
        ),
        "### Traits",
    ),
    (
        (
            "Animals",
            "Archelon",
            "Traits",
        ),
        "**_Amphibious._** The archelon can breathe air and water.",
    ),
    (
        (
            "Animals",
            "Archelon",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Archelon",
            "Actions",
        ),
        "**_Multiattack._** The archelon makes two Bite attacks.",
    ),
    (
        (
            "Animals",
            "Archelon",
            "Actions",
        ),
        "**_Bite._** _Melee Attack Roll:_ +6, reach 5 ft. _Hit:_ 14 (3d6 + 4) Piercing damage.",
    ),
    (
        (
            "Animals",
            "Baboon",
        ),
        "## Baboon",
    ),
    (
        (
            "Animals",
            "Baboon",
        ),
        "_Small Beast, Unaligned_",
    ),
    (
        (
            "Animals",
            "Baboon",
        ),
        "**AC** 12 **Initiative** +2 (12) <br>\n**HP** 3 (1d6) <br>\n**Speed** 30 ft., Climb 30 ft. <br>",
    ),
    (
        (
            "Animals",
            "Baboon",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>8</td>\n      <td>−1</td>\n      <td>−1</td>\n      <td><strong>DEX</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CON</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>4</td>\n      <td>−3</td>\n      <td>−3</td>\n      <td><strong>WIS</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CHA</strong></td>\n      <td>6</td>\n      <td>−2</td>\n      <td>−2</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Baboon",
        ),
        "**Senses** Passive Perception 11<br>\n**Languages** None<br>\n**CR** 0 (XP 10; PB +2)",
    ),
    (
        (
            "Animals",
            "Baboon",
            "Traits",
        ),
        "### Traits",
    ),
    (
        (
            "Animals",
            "Baboon",
            "Traits",
        ),
        "**_Pack Tactics._** The baboon has Advantage on an attack roll against a creature if at least one of the baboon's allies is within 5 feet of the creature and the ally doesn't have the Incapacitated condition.",
    ),
    (
        (
            "Animals",
            "Baboon",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Baboon",
            "Actions",
        ),
        "**_Bite._** _Melee Attack Roll:_ +1, reach 5 ft. _Hit:_ 1 (1d4 − 1) Piercing damage.",
    ),
    (
        (
            "Animals",
            "Badger",
        ),
        "## Badger",
    ),
    (
        (
            "Animals",
            "Badger",
        ),
        "_Tiny Beast, Unaligned_",
    ),
    (
        (
            "Animals",
            "Badger",
        ),
        "**AC** 11 **Initiative** +0 (10) <br>\n**HP** 5 (1d4 + 3) <br>\n**Speed** 20 ft., Burrow 5 ft. <br>",
    ),
    (
        (
            "Animals",
            "Badger",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>DEX</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CON</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>2</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>WIS</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CHA</strong></td>\n      <td>5</td>\n      <td>−3</td>\n      <td>−3</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Badger",
        ),
        "**Skills** Perception +3<br>\n**Resistances** Poison<br>\n**Senses** Darkvision 30 ft.; Passive Perception 13<br>\n**Languages** None<br>\n**CR** 0 (XP 10; PB +2)",
    ),
    (
        (
            "Animals",
            "Badger",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Badger",
            "Actions",
        ),
        "**_Bite._** _Melee Attack Roll:_ +2, reach 5 ft. _Hit:_ 1 Piercing damage.",
    ),
    (
        (
            "Animals",
            "Bat",
        ),
        "## Bat",
    ),
    (
        (
            "Animals",
            "Bat",
        ),
        "_Tiny Beast, Unaligned_",
    ),
    (
        (
            "Animals",
            "Bat",
        ),
        "**AC** 12 **Initiative** +2 (12) <br>\n**HP** 1 (1d4 − 1) <br>\n**Speed** 5 ft., Fly 30 ft. <br>",
    ),
    (
        (
            "Animals",
            "Bat",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>2</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>DEX</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CON</strong></td>\n      <td>8</td>\n      <td>−1</td>\n      <td>−1</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>2</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>WIS</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CHA</strong></td>\n      <td>4</td>\n      <td>−3</td>\n      <td>−3</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Bat",
        ),
        "**Senses** Blindsight 60 ft.; Passive Perception 11<br>\n**Languages** None<br>\n**CR** 0 (XP 10; PB +2)",
    ),
    (
        (
            "Animals",
            "Bat",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Bat",
            "Actions",
        ),
        "**_Bite._** _Melee Attack Roll:_ +4, reach 5 ft. _Hit:_ 1 Piercing damage.",
    ),
    (
        (
            "Animals",
            "Black Bear",
        ),
        "## Black Bear",
    ),
    (
        (
            "Animals",
            "Black Bear",
        ),
        "_Medium Beast, Unaligned_",
    ),
    (
        (
            "Animals",
            "Black Bear",
        ),
        "**AC** 11 **Initiative** +1 (11) <br>\n**HP** 19 (3d8 + 6) <br>\n**Speed** 30 ft., Climb 30 ft., Swim 30 ft. <br>",
    ),
    (
        (
            "Animals",
            "Black Bear",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>DEX</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CON</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>2</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>WIS</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CHA</strong></td>\n      <td>7</td>\n      <td>−2</td>\n      <td>−2</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Black Bear",
        ),
        "**Skills** Perception +5<br>\n**Senses** Darkvision 60 ft.; Passive Perception 15<br>\n**Languages** None<br>\n**CR** 1/2 (XP 100; PB +2)",
    ),
    (
        (
            "Animals",
            "Black Bear",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Black Bear",
            "Actions",
        ),
        "**_Multiattack._** The bear makes two Rend attacks.",
    ),
    (
        (
            "Animals",
            "Black Bear",
            "Actions",
        ),
        "**_Rend._** _Melee Attack Roll:_ +4, reach 5 ft. _Hit:_ 5 (1d6 + 2) Slashing damage.",
    ),
    (
        (
            "Animals",
            "Blood Hawk",
        ),
        "## Blood Hawk",
    ),
    (
        (
            "Animals",
            "Blood Hawk",
        ),
        "_Small Beast, Unaligned_",
    ),
    (
        (
            "Animals",
            "Blood Hawk",
        ),
        "**AC** 12 **Initiative** +2 (12) <br>\n**HP** 7 (2d6) <br>\n**Speed** 10 ft., Fly 60 ft. <br>",
    ),
    (
        (
            "Animals",
            "Blood Hawk",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>6</td>\n      <td>−2</td>\n      <td>−2</td>\n      <td><strong>DEX</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CON</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>3</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>WIS</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CHA</strong></td>\n      <td>5</td>\n      <td>−3</td>\n      <td>−3</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Blood Hawk",
        ),
        "**Skills** Perception +6<br>\n**Senses** Passive Perception 16<br>\n**Languages** None<br>\n**CR** 1/8 (XP 25; PB +2)",
    ),
    (
        (
            "Animals",
            "Blood Hawk",
            "Traits",
        ),
        "### Traits",
    ),
    (
        (
            "Animals",
            "Blood Hawk",
            "Traits",
        ),
        "**_Pack Tactics._** The hawk has Advantage on an attack roll against a creature if at least one of the hawk's allies is within 5 feet of the creature and the ally doesn't have the Incapacitated condition.",
    ),
    (
        (
            "Animals",
            "Blood Hawk",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Blood Hawk",
            "Actions",
        ),
        "**_Beak._** _Melee Attack Roll:_ +4, reach 5 ft. _Hit:_ 4 (1d4 + 2) Piercing damage, or 6 (1d8 + 2) Piercing damage if the target is Bloodied.",
    ),
    (
        (
            "Animals",
            "Boar",
        ),
        "## Boar",
    ),
    (
        (
            "Animals",
            "Boar",
        ),
        "_Medium Beast, Unaligned_",
    ),
    (
        (
            "Animals",
            "Boar",
        ),
        "**AC** 11 **Initiative** +0 (10) <br>\n**HP** 13 (2d8 + 4) <br>\n**Speed** 40 ft. <br>",
    ),
    (
        (
            "Animals",
            "Boar",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>DEX</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CON</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>2</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>WIS</strong></td>\n      <td>9</td>\n      <td>−1</td>\n      <td>−1</td>\n      <td><strong>CHA</strong></td>\n      <td>5</td>\n      <td>−3</td>\n      <td>−3</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Boar",
        ),
        "**Senses** Passive Perception 9<br>\n**Languages** None<br>\n**CR** 1/4 (XP 50; PB +2)",
    ),
    (
        (
            "Animals",
            "Boar",
            "Traits",
        ),
        "### Traits",
    ),
    (
        (
            "Animals",
            "Boar",
            "Traits",
        ),
        "**_Bloodied Fury._** While Bloodied, the boar has Advantage on attack rolls.",
    ),
    (
        (
            "Animals",
            "Boar",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Boar",
            "Actions",
        ),
        "**_Gore._** _Melee Attack Roll:_ +3, reach 5 ft. _Hit:_ 4 (1d6 + 1) Piercing damage. If the target is a Medium or smaller creature and the boar moved 20+ feet straight toward it immediately before the hit, the target takes an extra 3 (1d6) Piercing damage and has the Prone condition.",
    ),
    (
        (
            "Animals",
            "Brown Bear",
        ),
        "## Brown Bear",
    ),
    (
        (
            "Animals",
            "Brown Bear",
        ),
        "_Large Beast, Unaligned_",
    ),
    (
        (
            "Animals",
            "Brown Bear",
        ),
        "**AC** 11 **Initiative** +1 (11) <br>\n**HP** 22 (3d10 + 6) <br>\n**Speed** 40 ft., Climb 30 ft. <br>",
    ),
    (
        (
            "Animals",
            "Brown Bear",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>17</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>DEX</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CON</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>2</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>WIS</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CHA</strong></td>\n      <td>7</td>\n      <td>−2</td>\n      <td>−2</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Brown Bear",
        ),
        "**Skills** Perception +3<br>\n**Senses** Darkvision 60 ft.; Passive Perception 13<br>\n**Languages** None<br>\n**CR** 1 (XP 200; PB +2)",
    ),
    (
        (
            "Animals",
            "Brown Bear",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Brown Bear",
            "Actions",
        ),
        "**_Multiattack._** The bear makes one Bite attack and one Claw attack.",
    ),
    (
        (
            "Animals",
            "Brown Bear",
            "Actions",
        ),
        "**_Bite._** _Melee Attack Roll:_ +5, reach 5 ft. _Hit:_ 7 (1d8 + 3) Piercing damage.",
    ),
    (
        (
            "Animals",
            "Brown Bear",
            "Actions",
        ),
        "**_Claw._** _Melee Attack Roll:_ +5, reach 5 ft. _Hit:_ 5 (1d4 + 3) Slashing damage. If the target is a Large or smaller creature, it has the Prone condition.",
    ),
    (
        (
            "Animals",
            "Camel",
        ),
        "## Camel",
    ),
    (
        (
            "Animals",
            "Camel",
        ),
        "_Large Beast, Unaligned_",
    ),
    (
        (
            "Animals",
            "Camel",
        ),
        "**AC** 10 **Initiative** −1 (9) <br>\n**HP** 17 (2d10 + 6) <br>\n**Speed** 50 ft. <br>",
    ),
    (
        (
            "Animals",
            "Camel",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>DEX</strong></td>\n      <td>8</td>\n      <td>−1</td>\n      <td>−1</td>\n      <td><strong>CON</strong></td>\n      <td>17</td>\n      <td>+3</td>\n      <td>+5</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>2</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>WIS</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CHA</strong></td>\n      <td>5</td>\n      <td>−3</td>\n      <td>−3</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Camel",
        ),
        "**Senses** Darkvision 60 ft.; Passive Perception 10<br>\n**Languages** None<br>\n**CR** 1/8 (XP 25; PB +2)",
    ),
    (
        (
            "Animals",
            "Camel",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Camel",
            "Actions",
        ),
        "**_Bite._** _Melee Attack Roll:_ +4, reach 5 ft. _Hit:_ 4 (1d4 + 2) Bludgeoning damage.",
    ),
    (
        (
            "Animals",
            "Cat",
        ),
        "## Cat",
    ),
    (
        (
            "Animals",
            "Cat",
        ),
        "_Tiny Beast, Unaligned_",
    ),
    (
        (
            "Animals",
            "Cat",
        ),
        "**AC** 12 **Initiative** +2 (12) <br>\n**HP** 2 (1d4) <br>\n**Speed** 40 ft., Climb 40 ft. <br>",
    ),
    (
        (
            "Animals",
            "Cat",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>3</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>DEX</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+4</td>\n      <td><strong>CON</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>3</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>WIS</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CHA</strong></td>\n      <td>7</td>\n      <td>−2</td>\n      <td>−2</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Cat",
        ),
        "**Skills** Perception +3, Stealth +4<br>\n**Senses** Darkvision 60 ft.; Passive Perception 13<br>\n**Languages** None<br>\n**CR** 0 (XP 10; PB +2)",
    ),
    (
        (
            "Animals",
            "Cat",
            "Traits",
        ),
        "### Traits",
    ),
    (
        (
            "Animals",
            "Cat",
            "Traits",
        ),
        "**_Jumper._** The cat's jump distance is determined using its Dexterity rather than its Strength.",
    ),
    (
        (
            "Animals",
            "Cat",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Cat",
            "Actions",
        ),
        "**_Scratch._** _Melee Attack Roll:_ +4, reach 5 ft. _Hit:_ 1 Slashing damage.",
    ),
    (
        (
            "Animals",
            "Constrictor Snake",
        ),
        "## Constrictor Snake",
    ),
    (
        (
            "Animals",
            "Constrictor Snake",
        ),
        "_Large Beast, Unaligned_",
    ),
    (
        (
            "Animals",
            "Constrictor Snake",
        ),
        "**AC** 13 **Initiative** +2 (12) <br>\n**HP** 13 (2d10 + 2) <br>\n**Speed** 30 ft., Swim 30 ft. <br>",
    ),
    (
        (
            "Animals",
            "Constrictor Snake",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>DEX</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CON</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>1</td>\n      <td>−5</td>\n      <td>−5</td>\n      <td><strong>WIS</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CHA</strong></td>\n      <td>3</td>\n      <td>−4</td>\n      <td>−4</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Constrictor Snake",
        ),
        "**Skills** Perception +2, Stealth +4<br>\n**Senses** Blindsight 10 ft.; Passive Perception 12<br>\n**Languages** None<br>\n**CR** 1/4 (XP 50; PB +2)",
    ),
    (
        (
            "Animals",
            "Constrictor Snake",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Constrictor Snake",
            "Actions",
        ),
        "**_Bite._** _Melee Attack Roll:_ +4, reach 5 ft. _Hit:_ 6 (1d8 + 2) Piercing damage.",
    ),
    (
        (
            "Animals",
            "Constrictor Snake",
            "Actions",
        ),
        "**_Constrict._** _Strength Saving Throw:_ DC 12, one Medium or smaller creature the snake can see within 5 feet. _Failure:_ 7 (3d4) Bludgeoning damage, and the target has the Grappled condition (escape DC 12).",
    ),
    (
        (
            "Animals",
            "Crab",
        ),
        "## Crab",
    ),
    (
        (
            "Animals",
            "Crab",
        ),
        "_Tiny Beast, Unaligned_",
    ),
    (
        (
            "Animals",
            "Crab",
        ),
        "**AC** 11 **Initiative** +0 (10) <br>\n**HP** 3 (1d4 + 1) <br>\n**Speed** 20 ft., Swim 20 ft. <br>",
    ),
    (
        (
            "Animals",
            "Crab",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>6</td>\n      <td>−2</td>\n      <td>−2</td>\n      <td><strong>DEX</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CON</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>1</td>\n      <td>−5</td>\n      <td>−5</td>\n      <td><strong>WIS</strong></td>\n      <td>8</td>\n      <td>−1</td>\n      <td>−1</td>\n      <td><strong>CHA</strong></td>\n      <td>2</td>\n      <td>−4</td>\n      <td>−4</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Crab",
        ),
        "**Skills** Stealth +2<br>\n**Senses** Blindsight 30 ft.; Passive Perception 9<br>\n**Languages** None<br>\n**CR** 0 (XP 10; PB +2)",
    ),
    (
        (
            "Animals",
            "Crab",
            "Traits",
        ),
        "### Traits",
    ),
    (
        (
            "Animals",
            "Crab",
            "Traits",
        ),
        "**_Amphibious._** The crab can breathe air and water.",
    ),
    (
        (
            "Animals",
            "Crab",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Crab",
            "Actions",
        ),
        "**_Claw._** _Melee Attack Roll:_ +2, reach 5 ft. _Hit:_ 1 Bludgeoning damage.",
    ),
    (
        (
            "Animals",
            "Crocodile",
        ),
        "## Crocodile",
    ),
    (
        (
            "Animals",
            "Crocodile",
        ),
        "_Large Beast, Unaligned_",
    ),
    (
        (
            "Animals",
            "Crocodile",
        ),
        "**AC** 12 **Initiative** +0 (10) <br>\n**HP** 13 (2d10 + 2) <br>\n**Speed** 20 ft., Swim 30 ft. <br>",
    ),
    (
        (
            "Animals",
            "Crocodile",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>DEX</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CON</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+3</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>2</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>WIS</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CHA</strong></td>\n      <td>5</td>\n      <td>−3</td>\n      <td>−3</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Crocodile",
        ),
        "**Skills** Stealth +2<br>\n**Senses** Passive Perception 10<br>\n**Languages** None<br>\n**CR** 1/2 (XP 100; PB +2)",
    ),
    (
        (
            "Animals",
            "Crocodile",
            "Traits",
        ),
        "### Traits",
    ),
    (
        (
            "Animals",
            "Crocodile",
            "Traits",
        ),
        "**_Hold Breath._** The crocodile can hold its breath for 1 hour.",
    ),
    (
        (
            "Animals",
            "Crocodile",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Crocodile",
            "Actions",
        ),
        "**_Bite._** _Melee Attack Roll:_ +4, reach 5 ft. _Hit:_ 6 (1d8 + 2) Piercing damage. If the target is a Medium or smaller creature, it has the Grappled condition (escape DC 12). While Grappled, the target has the Restrained condition.",
    ),
    (
        (
            "Animals",
            "Deer",
        ),
        "## Deer",
    ),
    (
        (
            "Animals",
            "Deer",
        ),
        "_Medium Beast, Unaligned_",
    ),
    (
        (
            "Animals",
            "Deer",
        ),
        "**AC** 13 **Initiative** +3 (13) <br>\n**HP** 4 (1d8) <br>\n**Speed** 50 ft. <br>",
    ),
    (
        (
            "Animals",
            "Deer",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>DEX</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>CON</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>2</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>WIS</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CHA</strong></td>\n      <td>5</td>\n      <td>−3</td>\n      <td>−3</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Deer",
        ),
        "**Skills** Perception +4<br>\n**Senses** Darkvision 60 ft.; Passive Perception 14<br>\n**Languages** None<br>\n**CR** 0 (XP 10; PB +2)",
    ),
    (
        (
            "Animals",
            "Deer",
            "Traits",
        ),
        "### Traits",
    ),
    (
        (
            "Animals",
            "Deer",
            "Traits",
        ),
        "**_Agile._** The deer doesn't provoke an Opportunity Attack when it moves out of an enemy's reach.",
    ),
    (
        (
            "Animals",
            "Deer",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Deer",
            "Actions",
        ),
        "**_Ram._** _Melee Attack Roll:_ +2, reach 5 ft. _Hit:_ 2 (1d4) Bludgeoning damage.",
    ),
    (
        (
            "Animals",
            "Dire Wolf",
        ),
        "## Dire Wolf",
    ),
    (
        (
            "Animals",
            "Dire Wolf",
        ),
        "_Large Beast, Unaligned_",
    ),
    (
        (
            "Animals",
            "Dire Wolf",
        ),
        "**AC** 14 **Initiative** +2 (12) <br>\n**HP** 22 (3d10 + 6) <br>\n**Speed** 50 ft. <br>",
    ),
    (
        (
            "Animals",
            "Dire Wolf",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>17</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>DEX</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CON</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>3</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>WIS</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CHA</strong></td>\n      <td>7</td>\n      <td>−2</td>\n      <td>−2</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Dire Wolf",
        ),
        "**Skills** Perception +5, Stealth +4<br>\n**Senses** Darkvision 60 ft.; Passive Perception 15<br>\n**Languages** None<br>\n**CR** 1 (XP 200; PB +2)",
    ),
    (
        (
            "Animals",
            "Dire Wolf",
            "Traits",
        ),
        "### Traits",
    ),
    (
        (
            "Animals",
            "Dire Wolf",
            "Traits",
        ),
        "**_Pack Tactics._** The wolf has Advantage on an attack roll against a creature if at least one of the wolf's allies is within 5 feet of the creature and the ally doesn't have the Incapacitated condition.",
    ),
    (
        (
            "Animals",
            "Dire Wolf",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Dire Wolf",
            "Actions",
        ),
        "**_Bite._** _Melee Attack Roll:_ +5, reach 5 ft. _Hit:_ 8 (1d10 + 3) Piercing damage. If the target is a Large or smaller creature, it has the Prone condition.",
    ),
    (
        (
            "Animals",
            "Draft Horse",
        ),
        "## Draft Horse",
    ),
    (
        (
            "Animals",
            "Draft Horse",
        ),
        "_Large Beast, Unaligned_",
    ),
    (
        (
            "Animals",
            "Draft Horse",
        ),
        "**AC** 10 **Initiative** +0 (10) <br>\n**HP** 15 (2d10 + 4) <br>\n**Speed** 40 ft. <br>",
    ),
    (
        (
            "Animals",
            "Draft Horse",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+4</td>\n      <td><strong>DEX</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CON</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>2</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>WIS</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CHA</strong></td>\n      <td>7</td>\n      <td>−2</td>\n      <td>−2</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Draft Horse",
        ),
        "**Senses** Passive Perception 10<br>\n**Languages** None<br>\n**CR** 1/4 (XP 50; PB +2)",
    ),
    (
        (
            "Animals",
            "Draft Horse",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Draft Horse",
            "Actions",
        ),
        "**_Hooves._** _Melee Attack Roll:_ +6, reach 5 ft. _Hit:_ 6 (1d4 + 4) Bludgeoning damage.",
    ),
    (
        (
            "Animals",
            "Eagle",
        ),
        "## Eagle",
    ),
    (
        (
            "Animals",
            "Eagle",
        ),
        "_Small Beast, Unaligned_",
    ),
    (
        (
            "Animals",
            "Eagle",
        ),
        "**AC** 12 **Initiative** +2 (12) <br>\n**HP** 4 (1d6 + 1) <br>\n**Speed** 10 ft., Fly 60 ft. <br>",
    ),
    (
        (
            "Animals",
            "Eagle",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>6</td>\n      <td>−2</td>\n      <td>−2</td>\n      <td><strong>DEX</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CON</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>2</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>WIS</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CHA</strong></td>\n      <td>7</td>\n      <td>−2</td>\n      <td>−2</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Eagle",
        ),
        "**Skills** Perception +6<br>\n**Senses** Passive Perception 16<br>\n**Languages** None<br>\n**CR** 0 (XP 10; PB +2)",
    ),
    (
        (
            "Animals",
            "Eagle",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Eagle",
            "Actions",
        ),
        "**_Talons._** _Melee Attack Roll:_ +4, reach 5 feet. _Hit:_ 4 (1d4 + 2) Slashing damage.",
    ),
    (
        (
            "Animals",
            "Elephant",
        ),
        "## Elephant",
    ),
    (
        (
            "Animals",
            "Elephant",
        ),
        "_Huge Beast, Unaligned_",
    ),
    (
        (
            "Animals",
            "Elephant",
        ),
        "**AC** 12 **Initiative** −1 (9) <br>\n**HP** 76 (8d12 + 24) <br>\n**Speed** 40 ft. <br>",
    ),
    (
        (
            "Animals",
            "Elephant",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>22</td>\n      <td>+6</td>\n      <td>+6</td>\n      <td><strong>DEX</strong></td>\n      <td>9</td>\n      <td>−1</td>\n      <td>−1</td>\n      <td><strong>CON</strong></td>\n      <td>17</td>\n      <td>+3</td>\n      <td>+3</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>3</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>WIS</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CHA</strong></td>\n      <td>6</td>\n      <td>−2</td>\n      <td>−2</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Elephant",
        ),
        "**Senses** Passive Perception 10<br>\n**Languages** None<br>\n**CR** 4 (XP 1,100; PB +2)",
    ),
    (
        (
            "Animals",
            "Elephant",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Elephant",
            "Actions",
        ),
        "**_Multiattack._** The elephant makes two Gore attacks.",
    ),
    (
        (
            "Animals",
            "Elephant",
            "Actions",
        ),
        "**_Gore._** _Melee Attack Roll:_ +8, reach 5 ft. _Hit:_ 15 (2d8 + 6) Piercing damage. If the target is a Huge or smaller creature and the elephant moved 20+ feet straight toward it immediately before the hit, the target has the Prone condition.",
    ),
    (
        (
            "Animals",
            "Elephant",
            "Bonus Actions",
        ),
        "### Bonus Actions",
    ),
    (
        (
            "Animals",
            "Elephant",
            "Bonus Actions",
        ),
        "**_Trample._** _Dexterity Saving Throw:_ DC 16, one creature within 5 feet that has the Prone condition. _Failure:_ 17 (2d10 + 6) Bludgeoning damage. _Success:_ Half damage.",
    ),
    (
        (
            "Animals",
            "Elk",
        ),
        "## Elk",
    ),
    (
        (
            "Animals",
            "Elk",
        ),
        "_Large Beast, Unaligned_",
    ),
    (
        (
            "Animals",
            "Elk",
        ),
        "**AC** 10 **Initiative** +0 (10) <br>\n**HP** 11 (2d10) <br>\n**Speed** 50 ft. <br>",
    ),
    (
        (
            "Animals",
            "Elk",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>DEX</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CON</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>2</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>WIS</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CHA</strong></td>\n      <td>6</td>\n      <td>−2</td>\n      <td>−2</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Elk",
        ),
        "**Skills** Perception +2<br>\n**Senses** Darkvision 60 ft.; Passive Perception 12<br>\n**Languages** None<br>\n**CR** 1/4 (XP 50; PB +2)",
    ),
    (
        (
            "Animals",
            "Elk",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Elk",
            "Actions",
        ),
        "**_Ram._** _Melee Attack Roll:_ +5, reach 5 ft. _Hit:_ 6 (1d6 + 3) Bludgeoning damage. If the target is a Large or smaller creature and the elk moved 20+ feet straight toward it immediately before the hit, the target takes an extra 3 (1d6) Bludgeoning damage and has the Prone condition.",
    ),
    (
        (
            "Animals",
            "Flying Snake",
        ),
        "## Flying Snake",
    ),
    (
        (
            "Animals",
            "Flying Snake",
        ),
        "_Tiny Monstrosity, Unaligned_",
    ),
    (
        (
            "Animals",
            "Flying Snake",
        ),
        "**AC** 14 **Initiative** +2 (12) <br>\n**HP** 5 (2d4) <br>\n**Speed** 30 ft., Fly 60 ft., Swim 30 ft. <br>",
    ),
    (
        (
            "Animals",
            "Flying Snake",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>4</td>\n      <td>−3</td>\n      <td>−3</td>\n      <td><strong>DEX</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CON</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>2</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>WIS</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CHA</strong></td>\n      <td>5</td>\n      <td>−3</td>\n      <td>−3</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Flying Snake",
        ),
        "**Senses** Blindsight 10 ft.; Passive Perception 11<br>\n**Languages** None<br>\n**CR** 1/8 (XP 25; PB +2)",
    ),
    (
        (
            "Animals",
            "Flying Snake",
            "Traits",
        ),
        "### Traits",
    ),
    (
        (
            "Animals",
            "Flying Snake",
            "Traits",
        ),
        "**_Flyby._** The snake doesn't provoke an Opportunity Attack when it flies out of an enemy's reach.",
    ),
    (
        (
            "Animals",
            "Flying Snake",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Flying Snake",
            "Actions",
        ),
        "**_Bite._** _Melee Attack Roll:_ +4, reach 5 ft. _Hit:_ 1 Piercing damage plus 5 (2d4) Poison damage.",
    ),
    (
        (
            "Animals",
            "Frog",
        ),
        "## Frog",
    ),
    (
        (
            "Animals",
            "Frog",
        ),
        "_Tiny Beast, Unaligned_",
    ),
    (
        (
            "Animals",
            "Frog",
        ),
        "**AC** 11 **Initiative** +1 (11) <br>\n**HP** 1 (1d4 − 1) <br>\n**Speed** 20 ft., Swim 20 ft. <br>",
    ),
    (
        (
            "Animals",
            "Frog",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>1</td>\n      <td>−5</td>\n      <td>−5</td>\n      <td><strong>DEX</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CON</strong></td>\n      <td>8</td>\n      <td>−1</td>\n      <td>−1</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>1</td>\n      <td>−5</td>\n      <td>−5</td>\n      <td><strong>WIS</strong></td>\n      <td>8</td>\n      <td>−1</td>\n      <td>−1</td>\n      <td><strong>CHA</strong></td>\n      <td>3</td>\n      <td>−4</td>\n      <td>−4</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Frog",
        ),
        "**Skills** Perception +1, Stealth +3<br>\n**Senses** Darkvision 30 ft.; Passive Perception 11<br>\n**Languages** None<br>\n**CR** 0 (XP 10; PB +2)",
    ),
    (
        (
            "Animals",
            "Frog",
            "Traits",
        ),
        "### Traits",
    ),
    (
        (
            "Animals",
            "Frog",
            "Traits",
        ),
        "**_Amphibious._** The frog can breathe air and water.",
    ),
    (
        (
            "Animals",
            "Frog",
            "Traits",
        ),
        "**_Standing Leap._** The frog's Long Jump is up to 10 feet and its High Jump is up to 5 feet with or without a running start.",
    ),
    (
        (
            "Animals",
            "Frog",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Frog",
            "Actions",
        ),
        "**_Bite._** _Melee Attack Roll:_ +3, reach 5 ft. _Hit:_ 1 Piercing damage.",
    ),
    (
        (
            "Animals",
            "Giant Ape",
        ),
        "## Giant Ape",
    ),
    (
        (
            "Animals",
            "Giant Ape",
        ),
        "_Huge Beast, Unaligned_",
    ),
    (
        (
            "Animals",
            "Giant Ape",
        ),
        "**AC** 12 **Initiative** +5 (15) <br>\n**HP** 168 (16d12 + 64) <br>\n**Speed** 40 ft., Climb 40 ft. <br>",
    ),
    (
        (
            "Animals",
            "Giant Ape",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>23</td>\n      <td>+6</td>\n      <td>+6</td>\n      <td><strong>DEX</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CON</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+4</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>5</td>\n      <td>−3</td>\n      <td>−3</td>\n      <td><strong>WIS</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CHA</strong></td>\n      <td>7</td>\n      <td>−2</td>\n      <td>−2</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Giant Ape",
        ),
        "**Skills** Athletics +9, Perception +4, Survival +4<br>\n**Senses** Passive Perception 14<br>\n**Languages** None<br>\n**CR** 7 (XP 2,900; PB +3)",
    ),
    (
        (
            "Animals",
            "Giant Ape",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Giant Ape",
            "Actions",
        ),
        "**_Multiattack._** The ape makes two Fist attacks.",
    ),
    (
        (
            "Animals",
            "Giant Ape",
            "Actions",
        ),
        "**_Fist._** _Melee Attack Roll:_ +9, reach 10 ft. _Hit:_ 22 (3d10 + 6) Bludgeoning damage.",
    ),
    (
        (
            "Animals",
            "Giant Ape",
            "Actions",
        ),
        "**_Boulder Toss (Recharge 6)._** The ape hurls a boulder at a point it can see within 90 feet. _Dexterity Saving Throw:_ DC 17, each creature in a 5-foot-radius Sphere centered on that point. _Failure:_ 24 (7d6) Bludgeoning damage. If the target is a Large or smaller creature, it has the Prone condition. _Success:_ Half damage only.",
    ),
    (
        (
            "Animals",
            "Giant Ape",
            "Bonus Actions",
        ),
        "### Bonus Actions",
    ),
    (
        (
            "Animals",
            "Giant Ape",
            "Bonus Actions",
        ),
        "**_Leap._** The ape jumps up to 30 feet by spending 10 feet of movement.",
    ),
    (
        (
            "Animals",
            "Giant Badger",
        ),
        "## Giant Badger",
    ),
    (
        (
            "Animals",
            "Giant Badger",
        ),
        "_Medium Beast, Unaligned_",
    ),
    (
        (
            "Animals",
            "Giant Badger",
        ),
        "**AC** 13 **Initiative** +0 (10) <br>\n**HP** 15 (2d8 + 6) <br>\n**Speed** 30 ft., Burrow 10 ft. <br>",
    ),
    (
        (
            "Animals",
            "Giant Badger",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>DEX</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CON</strong></td>\n      <td>17</td>\n      <td>+3</td>\n      <td>+3</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>2</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>WIS</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CHA</strong></td>\n      <td>5</td>\n      <td>−3</td>\n      <td>−3</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Giant Badger",
        ),
        "**Skills** Perception +3<br>\n**Resistances** Poison<br>\n**Senses** Darkvision 60 ft.; Passive Perception 13<br>\n**Languages** None<br>\n**CR** 1/4 (XP 50; PB +2)",
    ),
    (
        (
            "Animals",
            "Giant Badger",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Giant Badger",
            "Actions",
        ),
        "**_Bite._** _Melee Attack Roll:_ +3, reach 5 ft. _Hit:_ 6 (2d4 + 1) Piercing damage.",
    ),
    (
        (
            "Animals",
            "Giant Bat",
        ),
        "## Giant Bat",
    ),
    (
        (
            "Animals",
            "Giant Bat",
        ),
        "_Large Beast, Unaligned_",
    ),
    (
        (
            "Animals",
            "Giant Bat",
        ),
        "**AC** 13 **Initiative** +3 (13) <br>\n**HP** 22 (4d10) <br>\n**Speed** 10 ft., Fly 60 ft. <br>",
    ),
    (
        (
            "Animals",
            "Giant Bat",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>DEX</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>CON</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>2</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>WIS</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CHA</strong></td>\n      <td>6</td>\n      <td>−2</td>\n      <td>−2</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Giant Bat",
        ),
        "**Senses** Blindsight 120 ft.; Passive Perception 11<br>\n**Languages** None<br>\n**CR** 1/4 (XP 50; PB +2)",
    ),
    (
        (
            "Animals",
            "Giant Bat",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Giant Bat",
            "Actions",
        ),
        "**_Bite._** _Melee Attack Roll:_ +5, reach 5 ft. _Hit:_ 6 (1d6 + 3) Piercing damage.",
    ),
    (
        (
            "Animals",
            "Giant Boar",
        ),
        "## Giant Boar",
    ),
    (
        (
            "Animals",
            "Giant Boar",
        ),
        "_Large Beast, Unaligned_",
    ),
    (
        (
            "Animals",
            "Giant Boar",
        ),
        "**AC** 13 **Initiative** +0 (10) <br>\n**HP** 42 (5d10 + 15) <br>\n**Speed** 40 ft. <br>",
    ),
    (
        (
            "Animals",
            "Giant Boar",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>17</td>\n      <td>+3</td>\n      <td>+5</td>\n      <td><strong>DEX</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CON</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>2</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>WIS</strong></td>\n      <td>7</td>\n      <td>−2</td>\n      <td>−2</td>\n      <td><strong>CHA</strong></td>\n      <td>5</td>\n      <td>−3</td>\n      <td>−3</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Giant Boar",
        ),
        "**Senses** Passive Perception 8<br>\n**Languages** None<br>\n**CR** 2 (XP 450; PB +2)",
    ),
    (
        (
            "Animals",
            "Giant Boar",
            "Traits",
        ),
        "### Traits",
    ),
    (
        (
            "Animals",
            "Giant Boar",
            "Traits",
        ),
        "**_Bloodied Fury._** The boar has Advantage on melee attack rolls while it is Bloodied.",
    ),
    (
        (
            "Animals",
            "Giant Boar",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Giant Boar",
            "Actions",
        ),
        "**_Gore._** _Melee Attack Roll:_ +5, reach 5 ft. _Hit:_ 10 (2d6 + 3) Piercing damage. If the target is a Large or smaller creature and the boar moved 20+ feet straight toward it immediately before the hit, the target takes an extra 7 (2d6) Piercing damage and has the Prone condition.",
    ),
    (
        (
            "Animals",
            "Giant Centipede",
        ),
        "## Giant Centipede",
    ),
    (
        (
            "Animals",
            "Giant Centipede",
        ),
        "_Small Beast, Unaligned_",
    ),
    (
        (
            "Animals",
            "Giant Centipede",
        ),
        "**AC** 14 **Initiative** +2 (12) <br>\n**HP** 9 (2d6 + 2) <br>\n**Speed** 30 ft., Climb 30 ft. <br>",
    ),
    (
        (
            "Animals",
            "Giant Centipede",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>5</td>\n      <td>−3</td>\n      <td>−3</td>\n      <td><strong>DEX</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CON</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>1</td>\n      <td>−5</td>\n      <td>−5</td>\n      <td><strong>WIS</strong></td>\n      <td>7</td>\n      <td>−2</td>\n      <td>−2</td>\n      <td><strong>CHA</strong></td>\n      <td>3</td>\n      <td>−4</td>\n      <td>−4</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Giant Centipede",
        ),
        "**Senses** Blindsight 30 ft.; Passive Perception 8<br>\n**Languages** None<br>\n**CR** 1/4 (XP 50; PB +2)",
    ),
    (
        (
            "Animals",
            "Giant Centipede",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Giant Centipede",
            "Actions",
        ),
        "**_Bite._** _Melee Attack Roll:_ +4, reach 5 ft. _Hit:_ 4 (1d4 + 2) Piercing damage, and the target has the Poisoned condition until the start of the centipede's next turn.",
    ),
    (
        (
            "Animals",
            "Giant Constrictor Snake",
        ),
        "## Giant Constrictor Snake",
    ),
    (
        (
            "Animals",
            "Giant Constrictor Snake",
        ),
        "_Huge Beast, Unaligned_",
    ),
    (
        (
            "Animals",
            "Giant Constrictor Snake",
        ),
        "**AC** 12 **Initiative** +2 (12) <br>\n**HP** 60 (8d12 + 8) <br>\n**Speed** 30 ft., Swim 30 ft. <br>",
    ),
    (
        (
            "Animals",
            "Giant Constrictor Snake",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>19</td>\n      <td>+4</td>\n      <td>+4</td>\n      <td><strong>DEX</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CON</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>1</td>\n      <td>−5</td>\n      <td>−5</td>\n      <td><strong>WIS</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CHA</strong></td>\n      <td>3</td>\n      <td>−4</td>\n      <td>−4</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Giant Constrictor Snake",
        ),
        "**Skills** Perception +2<br>\n**Senses** Blindsight 10 ft.; Passive Perception 12<br>\n**Languages** None<br>\n**CR** 2 (XP 450; PB +2)",
    ),
    (
        (
            "Animals",
            "Giant Constrictor Snake",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Giant Constrictor Snake",
            "Actions",
        ),
        "**_Multiattack._** The snake makes one Bite attack and uses Constrict.",
    ),
    (
        (
            "Animals",
            "Giant Constrictor Snake",
            "Actions",
        ),
        "**_Bite._** _Melee Attack Roll:_ +6, reach 10 ft. _Hit:_ 11 (2d6 + 4) Piercing damage.",
    ),
    (
        (
            "Animals",
            "Giant Constrictor Snake",
            "Actions",
        ),
        "**_Constrict._** _Strength Saving Throw:_ DC 14, one Large or smaller creature the snake can see within 10 feet. _Failure:_ 13 (2d8 + 4) Bludgeoning damage, and the target has the Grappled condition (escape DC 14).",
    ),
    (
        (
            "Animals",
            "Giant Crab",
        ),
        "## Giant Crab",
    ),
    (
        (
            "Animals",
            "Giant Crab",
        ),
        "_Medium Beast, Unaligned_",
    ),
    (
        (
            "Animals",
            "Giant Crab",
        ),
        "**AC** 15 **Initiative** +1 (11) <br>\n**HP** 13 (3d8) <br>\n**Speed** 30 ft., Swim 30 ft. <br>",
    ),
    (
        (
            "Animals",
            "Giant Crab",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>DEX</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CON</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>1</td>\n      <td>−5</td>\n      <td>−5</td>\n      <td><strong>WIS</strong></td>\n      <td>9</td>\n      <td>−1</td>\n      <td>−1</td>\n      <td><strong>CHA</strong></td>\n      <td>3</td>\n      <td>−4</td>\n      <td>−4</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Giant Crab",
        ),
        "**Skills** Stealth +3<br>\n**Senses** Blindsight 30 ft.; Passive Perception 9<br>\n**Languages** None<br>\n**CR** 1/8 (XP 25; PB +2)",
    ),
    (
        (
            "Animals",
            "Giant Crab",
            "Traits",
        ),
        "### Traits",
    ),
    (
        (
            "Animals",
            "Giant Crab",
            "Traits",
        ),
        "**_Amphibious._** The crab can breathe air and water.",
    ),
    (
        (
            "Animals",
            "Giant Crab",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Giant Crab",
            "Actions",
        ),
        "**_Claw._** _Melee Attack Roll:_ +3, reach 5 ft. _Hit:_ 4 (1d6 + 1) Bludgeoning damage. If the target is a Medium or smaller creature, it has the Grappled condition (escape DC 11) from one of two claws.",
    ),
    (
        (
            "Animals",
            "Giant Crocodile",
        ),
        "## Giant Crocodile",
    ),
    (
        (
            "Animals",
            "Giant Crocodile",
        ),
        "_Huge Beast, Unaligned_",
    ),
    (
        (
            "Animals",
            "Giant Crocodile",
        ),
        "**AC** 14 **Initiative** −1 (9) <br>\n**HP** 85 (9d12 + 27) <br>\n**Speed** 30 ft., Swim 50 ft. <br>",
    ),
    (
        (
            "Animals",
            "Giant Crocodile",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>21</td>\n      <td>+5</td>\n      <td>+5</td>\n      <td><strong>DEX</strong></td>\n      <td>9</td>\n      <td>−1</td>\n      <td>−1</td>\n      <td><strong>CON</strong></td>\n      <td>17</td>\n      <td>+3</td>\n      <td>+3</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>2</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>WIS</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CHA</strong></td>\n      <td>7</td>\n      <td>−2</td>\n      <td>−2</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Giant Crocodile",
        ),
        "**Skills** Stealth +5<br>\n**Senses** Passive Perception 10<br>\n**Languages** None<br>\n**CR** 5 (XP 1,800; PB +3)",
    ),
    (
        (
            "Animals",
            "Giant Crocodile",
            "Traits",
        ),
        "### Traits",
    ),
    (
        (
            "Animals",
            "Giant Crocodile",
            "Traits",
        ),
        "**_Hold Breath._** The crocodile can hold its breath for 1 hour.",
    ),
    (
        (
            "Animals",
            "Giant Crocodile",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Giant Crocodile",
            "Actions",
        ),
        "**_Multiattack._** The crocodile makes one Bite attack and one Tail attack.",
    ),
    (
        (
            "Animals",
            "Giant Crocodile",
            "Actions",
        ),
        "**_Bite._** _Melee Attack Roll:_ +8, reach 5 ft. _Hit:_ 21 (3d10 + 5) Piercing damage. If the target is a Large or smaller creature, it has the Grappled condition (escape DC 15). While Grappled, the target has the Restrained condition and can't be targeted by the crocodile's Tail.",
    ),
    (
        (
            "Animals",
            "Giant Crocodile",
            "Actions",
        ),
        "**_Tail._** _Melee Attack Roll:_ +8, reach 10 ft. _Hit:_ 18 (3d8 + 5) Bludgeoning damage. If the target is a Large or smaller creature, it has the Prone condition.",
    ),
    (
        (
            "Animals",
            "Giant Eagle",
        ),
        "## Giant Eagle",
    ),
    (
        (
            "Animals",
            "Giant Eagle",
        ),
        "_Large Celestial, Neutral Good_",
    ),
    (
        (
            "Animals",
            "Giant Eagle",
        ),
        "**AC** 13 **Initiative** +3 (13) <br>\n**HP** 26 (4d10 + 4) <br>\n**Speed** 10 ft., Fly 80 ft. <br>",
    ),
    (
        (
            "Animals",
            "Giant Eagle",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>DEX</strong></td>\n      <td>17</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>CON</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>8</td>\n      <td>−1</td>\n      <td>−1</td>\n      <td><strong>WIS</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CHA</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Giant Eagle",
        ),
        "**Skills** Perception +6<br>\n**Resistances** Necrotic, Radiant<br>\n**Senses** Passive Perception 16<br>\n**Languages** Celestial; understands Common and Primordial (Auran) but can't speak them<br>\n**CR** 1 (XP 200; PB +2)",
    ),
    (
        (
            "Animals",
            "Giant Eagle",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Giant Eagle",
            "Actions",
        ),
        "**_Multiattack._** The eagle makes two Rend attacks.",
    ),
    (
        (
            "Animals",
            "Giant Eagle",
            "Actions",
        ),
        "**_Rend._** _Melee Attack Roll:_ +5, reach 5 ft. _Hit:_ 5 (1d4 + 3) Slashing damage plus 3 (1d6) Radiant damage.",
    ),
    (
        (
            "Animals",
            "Giant Elk",
        ),
        "## Giant Elk",
    ),
    (
        (
            "Animals",
            "Giant Elk",
        ),
        "_Huge Celestial, Neutral Good_",
    ),
    (
        (
            "Animals",
            "Giant Elk",
        ),
        "**AC** 14 **Initiative** +6 (16) <br>\n**HP** 42 (5d12 + 10) <br>\n**Speed** 60 ft. <br>",
    ),
    (
        (
            "Animals",
            "Giant Elk",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>19</td>\n      <td>+4</td>\n      <td>+6</td>\n      <td><strong>DEX</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+6</td>\n      <td><strong>CON</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>7</td>\n      <td>−2</td>\n      <td>−2</td>\n      <td><strong>WIS</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CHA</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Giant Elk",
        ),
        "**Skills** Perception +4<br>\n**Resistances** Necrotic, Radiant<br>\n**Senses** Darkvision 90 ft.; Passive Perception 14<br>\n**Languages** Celestial; understands Common, Elvish, and Sylvan but can't speak them<br>\n**CR** 2 (XP 450; PB +2)",
    ),
    (
        (
            "Animals",
            "Giant Elk",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Giant Elk",
            "Actions",
        ),
        "**_Ram._** _Melee Attack Roll:_ +6, reach 10 ft. _Hit:_ 11 (2d6 + 4) Bludgeoning damage plus 5 (2d4) Radiant damage. If the target is a Huge or smaller creature and the elk moved 20+ feet straight toward it immediately before the hit, the target takes an extra 5 (2d4) Bludgeoning damage and has the Prone condition.",
    ),
    (
        (
            "Animals",
            "Giant Fire Beetle",
        ),
        "## Giant Fire Beetle",
    ),
    (
        (
            "Animals",
            "Giant Fire Beetle",
        ),
        "_Small Beast, Unaligned_",
    ),
    (
        (
            "Animals",
            "Giant Fire Beetle",
        ),
        "**AC** 13 **Initiative** +0 (10) <br>\n**HP** 4 (1d6 + 1) <br>\n**Speed** 30 ft., Climb 30 ft. <br>",
    ),
    (
        (
            "Animals",
            "Giant Fire Beetle",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>8</td>\n      <td>−1</td>\n      <td>−1</td>\n      <td><strong>DEX</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CON</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>1</td>\n      <td>−5</td>\n      <td>−5</td>\n      <td><strong>WIS</strong></td>\n      <td>7</td>\n      <td>−2</td>\n      <td>−2</td>\n      <td><strong>CHA</strong></td>\n      <td>3</td>\n      <td>−4</td>\n      <td>−4</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Giant Fire Beetle",
        ),
        "**Resistances** Fire<br>\n**Senses** Blindsight 30 ft.; Passive Perception 8<br>\n**Languages** None<br>\n**CR** 0 (XP 10; PB +2)",
    ),
    (
        (
            "Animals",
            "Giant Fire Beetle",
            "Traits",
        ),
        "### Traits",
    ),
    (
        (
            "Animals",
            "Giant Fire Beetle",
            "Traits",
        ),
        "**_Illumination._** The beetle sheds Bright Light in a 10-foot radius and Dim Light for an additional 10 feet.",
    ),
    (
        (
            "Animals",
            "Giant Fire Beetle",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Giant Fire Beetle",
            "Actions",
        ),
        "**_Bite._** _Melee Attack Roll:_ +1, reach 5 ft. _Hit:_ 1 Fire damage.",
    ),
    (
        (
            "Animals",
            "Giant Frog",
        ),
        "## Giant Frog",
    ),
    (
        (
            "Animals",
            "Giant Frog",
        ),
        "_Medium Beast, Unaligned_",
    ),
    (
        (
            "Animals",
            "Giant Frog",
        ),
        "**AC** 11 **Initiative** +1 (11) <br>\n**HP** 18 (4d8) <br>\n**Speed** 30 ft., Swim 30 ft. <br>",
    ),
    (
        (
            "Animals",
            "Giant Frog",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>DEX</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CON</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>2</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>WIS</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CHA</strong></td>\n      <td>3</td>\n      <td>−4</td>\n      <td>−4</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Giant Frog",
        ),
        "**Skills** Perception +2, Stealth +4<br>\n**Senses** Darkvision 30 ft.; Passive Perception 12<br>\n**Languages** None<br>\n**CR** 1/4 (XP 50; PB +2)",
    ),
    (
        (
            "Animals",
            "Giant Frog",
            "Traits",
        ),
        "### Traits",
    ),
    (
        (
            "Animals",
            "Giant Frog",
            "Traits",
        ),
        "**_Amphibious._** The frog can breathe air and water.",
    ),
    (
        (
            "Animals",
            "Giant Frog",
            "Traits",
        ),
        "**_Standing Leap._** The frog's Long Jump is up to 20 feet and its High Jump is up to 10 feet with or without a running start.",
    ),
    (
        (
            "Animals",
            "Giant Frog",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Giant Frog",
            "Actions",
        ),
        "**_Bite._** _Melee Attack Roll:_ +3, reach 5 ft. _Hit:_ 5 (1d6 + 2) Piercing damage. If the target is a Medium or smaller creature, it has the Grappled condition (escape DC 11).",
    ),
    (
        (
            "Animals",
            "Giant Frog",
            "Actions",
        ),
        "**_Swallow._** The frog swallows a Small or smaller target it is grappling. While swallowed, the target isn't Grappled but has the Blinded and Restrained conditions, and it has Total Cover against attacks and other effects outside the frog. While swallowing the target, the frog can't use Bite, and if the frog dies, the swallowed target is no longer Restrained and can escape from the corpse using 5 feet of movement, exiting with the Prone condition. <br>\n&emsp;At the end of the frog's next turn, the swallowed target takes 5 (2d4) Acid damage. If that damage doesn't kill it, the frog disgorges it, causing it to exit Prone.",
    ),
    (
        (
            "Animals",
            "Giant Goat",
        ),
        "## Giant Goat",
    ),
    (
        (
            "Animals",
            "Giant Goat",
        ),
        "_Large Beast, Unaligned_",
    ),
    (
        (
            "Animals",
            "Giant Goat",
        ),
        "**AC** 11 **Initiative** +1 (11) <br>\n**HP** 19 (3d10 + 3) <br>\n**Speed** 40 ft., Climb 30 ft. <br>",
    ),
    (
        (
            "Animals",
            "Giant Goat",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>17</td>\n      <td>+3</td>\n      <td>+5</td>\n      <td><strong>DEX</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CON</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>3</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>WIS</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CHA</strong></td>\n      <td>6</td>\n      <td>−2</td>\n      <td>−2</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Giant Goat",
        ),
        "**Skills** Perception +3<br>\n**Senses** Darkvision 60 ft.; Passive Perception 13<br>\n**Languages** None<br>\n**CR** 1/2 (XP 100; PB +2)",
    ),
    (
        (
            "Animals",
            "Giant Goat",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Giant Goat",
            "Actions",
        ),
        "**_Ram._** _Melee Attack Roll:_ +5, reach 5 ft. _Hit:_ 6 (1d6 + 3) Bludgeoning damage. If the target is a Large or smaller creature and the goat moved 20+ feet straight toward it immediately before the hit, the target takes an extra 5 (2d4) Bludgeoning damage and has the Prone condition.",
    ),
    (
        (
            "Animals",
            "Giant Hyena",
        ),
        "## Giant Hyena",
    ),
    (
        (
            "Animals",
            "Giant Hyena",
        ),
        "_Large Beast, Unaligned_",
    ),
    (
        (
            "Animals",
            "Giant Hyena",
        ),
        "**AC** 12 **Initiative** +2 (12) <br>\n**HP** 45 (6d10 + 12) <br>\n**Speed** 50 ft. <br>",
    ),
    (
        (
            "Animals",
            "Giant Hyena",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>DEX</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CON</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>2</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>WIS</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CHA</strong></td>\n      <td>7</td>\n      <td>−2</td>\n      <td>−2</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Giant Hyena",
        ),
        "**Skills** Perception +3<br>\n**Senses** Darkvision 60 ft.; Passive Perception 13<br>\n**Languages** None<br>\n**CR** 1 (XP 200; PB +2)",
    ),
    (
        (
            "Animals",
            "Giant Hyena",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Giant Hyena",
            "Actions",
        ),
        "**_Bite._** _Melee Attack Roll:_ +5, reach 5 ft. _Hit:_ 10 (2d6 + 3) Piercing damage.",
    ),
    (
        (
            "Animals",
            "Giant Hyena",
            "Bonus Actions",
        ),
        "### Bonus Actions",
    ),
    (
        (
            "Animals",
            "Giant Hyena",
            "Bonus Actions",
        ),
        "**_Rampage (1/Day)._** Immediately after dealing damage to a creature that was already Bloodied, the hyena can move up to half its Speed, and it makes one Bite attack.",
    ),
    (
        (
            "Animals",
            "Giant Lizard",
        ),
        "## Giant Lizard",
    ),
    (
        (
            "Animals",
            "Giant Lizard",
        ),
        "_Large Beast, Unaligned_",
    ),
    (
        (
            "Animals",
            "Giant Lizard",
        ),
        "**AC** 12 **Initiative** +1 (11) <br>\n**HP** 19 (3d10 + 3) <br>\n**Speed** 40 ft., Climb 40 ft. <br>",
    ),
    (
        (
            "Animals",
            "Giant Lizard",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>DEX</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+3</td>\n      <td><strong>CON</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>2</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>WIS</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CHA</strong></td>\n      <td>5</td>\n      <td>−3</td>\n      <td>−3</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Giant Lizard",
        ),
        "**Senses** Darkvision 60 ft.; Passive Perception 10<br>\n**Languages** None<br>\n**CR** 1/4 (XP 50; PB +2)",
    ),
    (
        (
            "Animals",
            "Giant Lizard",
            "Traits",
        ),
        "### Traits",
    ),
    (
        (
            "Animals",
            "Giant Lizard",
            "Traits",
        ),
        "**_Spider Climb._** The lizard can climb difficult surfaces, including along ceilings, without needing to make an ability check.",
    ),
    (
        (
            "Animals",
            "Giant Lizard",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Giant Lizard",
            "Actions",
        ),
        "**_Bite._** _Melee Attack Roll:_ +4, reach 5 ft. _Hit:_ 6 (1d8 + 2) Piercing damage.",
    ),
    (
        (
            "Animals",
            "Giant Octopus",
        ),
        "## Giant Octopus",
    ),
    (
        (
            "Animals",
            "Giant Octopus",
        ),
        "_Large Beast, Unaligned_",
    ),
    (
        (
            "Animals",
            "Giant Octopus",
        ),
        "**AC** 11 **Initiative** +1 (11) <br>\n**HP** 45 (7d10 + 7) <br>\n**Speed** 10 ft., Swim 60 ft. <br>",
    ),
    (
        (
            "Animals",
            "Giant Octopus",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>17</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>DEX</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CON</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>5</td>\n      <td>−3</td>\n      <td>−3</td>\n      <td><strong>WIS</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CHA</strong></td>\n      <td>4</td>\n      <td>−3</td>\n      <td>−3</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Giant Octopus",
        ),
        "**Skills** Perception +4, Stealth +5<br>\n**Senses** Darkvision 60 ft.; Passive Perception 14<br>\n**Languages** None<br>\n**CR** 1 (XP 200; PB +2)",
    ),
    (
        (
            "Animals",
            "Giant Octopus",
            "Traits",
        ),
        "### Traits",
    ),
    (
        (
            "Animals",
            "Giant Octopus",
            "Traits",
        ),
        "**_Water Breathing._** The octopus can breathe only underwater. It can hold its breath for 1 hour outside water.",
    ),
    (
        (
            "Animals",
            "Giant Octopus",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Giant Octopus",
            "Actions",
        ),
        "**_Tentacles._** _Melee Attack Roll:_ +5, reach 10 ft. _Hit:_ 10 (2d6 + 3) Bludgeoning damage. If the target is a Medium or smaller creature, it has the Grappled condition (escape DC 13) from all eight tentacles. While Grappled, the target has the Restrained condition.",
    ),
    (
        (
            "Animals",
            "Giant Octopus",
            "Reactions",
        ),
        "### Reactions",
    ),
    (
        (
            "Animals",
            "Giant Octopus",
            "Reactions",
        ),
        "**_Ink Cloud (1/Day)._** _Trigger:_ The octopus takes damage while underwater. _Response:_ The octopus releases ink that fills a 10-foot Cube centered on itself, and the octopus moves up to its Swim Speed. The Cube is Heavily Obscured for 1 minute or until a strong current or similar effect disperses the ink.",
    ),
    (
        (
            "Animals",
            "Giant Owl",
        ),
        "## Giant Owl",
    ),
    (
        (
            "Animals",
            "Giant Owl",
        ),
        "_Large Celestial, Neutral_",
    ),
    (
        (
            "Animals",
            "Giant Owl",
        ),
        "**AC** 12 **Initiative** +2 (12) <br>\n**HP** 19 (3d10 + 3) <br>\n**Speed** 5 ft., Fly 60 ft. <br>",
    ),
    (
        (
            "Animals",
            "Giant Owl",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>DEX</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CON</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>WIS</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+4</td>\n      <td><strong>CHA</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Giant Owl",
        ),
        "**Skills** Perception +6, Stealth +6<br>\n**Resistances** Necrotic, Radiant<br>\n**Senses** Darkvision 120 ft.; Passive Perception 16<br>\n**Languages** Celestial; understands Common, Elvish, and Sylvan but can't speak them<br>\n**CR** 1/4 (XP 50; PB +2)",
    ),
    (
        (
            "Animals",
            "Giant Owl",
            "Traits",
        ),
        "### Traits",
    ),
    (
        (
            "Animals",
            "Giant Owl",
            "Traits",
        ),
        "**_Flyby._** The owl doesn't provoke an Opportunity Attack when it flies out of an enemy's reach.",
    ),
    (
        (
            "Animals",
            "Giant Owl",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Giant Owl",
            "Actions",
        ),
        "**_Talons._** _Melee Attack Roll:_ +4, reach 5 ft. _Hit:_ 7 (1d10 + 2) Slashing damage.",
    ),
    (
        (
            "Animals",
            "Giant Owl",
            "Actions",
        ),
        "**_Spellcasting._** The owl casts one of the following spells, requiring no spell components and using Wisdom as the spellcasting ability: <br>\n&emsp;**At Will:** _Detect Evil and Good_, _Detect Magic_ <br>\n&emsp;**1/Day:** _Clairvoyance_",
    ),
    (
        (
            "Animals",
            "Giant Rat",
        ),
        "## Giant Rat",
    ),
    (
        (
            "Animals",
            "Giant Rat",
        ),
        "_Small Beast, Unaligned_",
    ),
    (
        (
            "Animals",
            "Giant Rat",
        ),
        "**AC** 13 **Initiative** +3 (13) <br>\n**HP** 7 (2d6) <br>\n**Speed** 30 ft., Climb 30 ft. <br>",
    ),
    (
        (
            "Animals",
            "Giant Rat",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>7</td>\n      <td>−2</td>\n      <td>−2</td>\n      <td><strong>DEX</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+5</td>\n      <td><strong>CON</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>2</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>WIS</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CHA</strong></td>\n      <td>4</td>\n      <td>−3</td>\n      <td>−3</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Giant Rat",
        ),
        "**Skills** Perception +2<br>\n**Senses** Darkvision 60 ft.; Passive Perception 12<br>\n**Languages** None<br>\n**CR** 1/8 (XP 25; PB +2)",
    ),
    (
        (
            "Animals",
            "Giant Rat",
            "Traits",
        ),
        "### Traits",
    ),
    (
        (
            "Animals",
            "Giant Rat",
            "Traits",
        ),
        "**_Pack Tactics._** The rat has Advantage on an attack roll against a creature if at least one of the rat's allies is within 5 feet of the creature and the ally doesn't have the Incapacitated condition.",
    ),
    (
        (
            "Animals",
            "Giant Rat",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Giant Rat",
            "Actions",
        ),
        "**_Bite._** _Melee Attack Roll:_ +5, reach 5 feet. _Hit:_ 5 (1d4 + 3) Piercing damage.",
    ),
    (
        (
            "Animals",
            "Giant Scorpion",
        ),
        "## Giant Scorpion",
    ),
    (
        (
            "Animals",
            "Giant Scorpion",
        ),
        "_Large Beast, Unaligned_",
    ),
    (
        (
            "Animals",
            "Giant Scorpion",
        ),
        "**AC** 15 **Initiative** +1 (11) <br>\n**HP** 52 (7d10 + 14) <br>\n**Speed** 40 ft. <br>",
    ),
    (
        (
            "Animals",
            "Giant Scorpion",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>DEX</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CON</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>1</td>\n      <td>−5</td>\n      <td>−5</td>\n      <td><strong>WIS</strong></td>\n      <td>9</td>\n      <td>−1</td>\n      <td>−1</td>\n      <td><strong>CHA</strong></td>\n      <td>3</td>\n      <td>−4</td>\n      <td>−4</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Giant Scorpion",
        ),
        "**Senses** Blindsight 60 ft.; Passive Perception 9<br>\n**Languages** None<br>\n**CR** 3 (XP 700; PB +2)",
    ),
    (
        (
            "Animals",
            "Giant Scorpion",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Giant Scorpion",
            "Actions",
        ),
        "**_Multiattack._** The scorpion makes two Claw attacks and one Sting attack.",
    ),
    (
        (
            "Animals",
            "Giant Scorpion",
            "Actions",
        ),
        "**_Claw._** _Melee Attack Roll:_ +5, reach 5 ft. _Hit:_ 6 (1d6 + 3) Bludgeoning damage. If the target is a Large or smaller creature, it has the Grappled condition (escape DC 13) from one of two claws.",
    ),
    (
        (
            "Animals",
            "Giant Scorpion",
            "Actions",
        ),
        "**_Sting._** _Melee Attack Roll:_ +5, reach 5 ft. _Hit:_ 7 (1d8 + 3) Piercing damage plus 11 (2d10) Poison damage.",
    ),
    (
        (
            "Animals",
            "Giant Seahorse",
        ),
        "## Giant Seahorse",
    ),
    (
        (
            "Animals",
            "Giant Seahorse",
        ),
        "_Large Beast, Unaligned_",
    ),
    (
        (
            "Animals",
            "Giant Seahorse",
        ),
        "**AC** 14 **Initiative** +1 (11) <br>\n**HP** 16 (3d10) <br>\n**Speed** 5 ft., Swim 40 ft. <br>",
    ),
    (
        (
            "Animals",
            "Giant Seahorse",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>DEX</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CON</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>2</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>WIS</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CHA</strong></td>\n      <td>5</td>\n      <td>−3</td>\n      <td>−3</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Giant Seahorse",
        ),
        "**Senses** Passive Perception 11<br>\n**Languages** None<br>\n**CR** 1/2 (XP 100; PB +2)",
    ),
    (
        (
            "Animals",
            "Giant Seahorse",
            "Traits",
        ),
        "### Traits",
    ),
    (
        (
            "Animals",
            "Giant Seahorse",
            "Traits",
        ),
        "**_Water Breathing._** The seahorse can breathe only underwater.",
    ),
    (
        (
            "Animals",
            "Giant Seahorse",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Giant Seahorse",
            "Actions",
        ),
        "**_Ram._** _Melee Attack Roll:_ +4, reach 5 ft. _Hit:_ 9 (2d6 + 2) Bludgeoning damage, or 11 (2d8 + 2) Bludgeoning damage if the seahorse moved 20+ feet straight toward the target immediately before the hit.",
    ),
    (
        (
            "Animals",
            "Giant Seahorse",
            "Bonus Actions",
        ),
        "### Bonus Actions",
    ),
    (
        (
            "Animals",
            "Giant Seahorse",
            "Bonus Actions",
        ),
        "**_Bubble Dash._** While underwater, the seahorse moves up to half its Swim Speed without provoking Opportunity Attacks.",
    ),
    (
        (
            "Animals",
            "Giant Shark",
        ),
        "## Giant Shark",
    ),
    (
        (
            "Animals",
            "Giant Shark",
        ),
        "_Huge Beast, Unaligned_",
    ),
    (
        (
            "Animals",
            "Giant Shark",
        ),
        "**AC** 13 **Initiative** +3 (13) <br>\n**HP** 92 (8d12 + 40) <br>\n**Speed** 5 ft., Swim 60 ft. <br>",
    ),
    (
        (
            "Animals",
            "Giant Shark",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>23</td>\n      <td>+6</td>\n      <td>+6</td>\n      <td><strong>DEX</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CON</strong></td>\n      <td>21</td>\n      <td>+5</td>\n      <td>+5</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>1</td>\n      <td>−5</td>\n      <td>−5</td>\n      <td><strong>WIS</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CHA</strong></td>\n      <td>5</td>\n      <td>−3</td>\n      <td>−3</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Giant Shark",
        ),
        "**Skills** Perception +3<br>\n**Senses** Blindsight 60 ft.; Passive Perception 13<br>\n**Languages** None<br>\n**CR** 5 (XP 1,800; PB +3)",
    ),
    (
        (
            "Animals",
            "Giant Shark",
            "Traits",
        ),
        "### Traits",
    ),
    (
        (
            "Animals",
            "Giant Shark",
            "Traits",
        ),
        "**_Water Breathing._** The shark can breathe only underwater.",
    ),
    (
        (
            "Animals",
            "Giant Shark",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Giant Shark",
            "Actions",
        ),
        "**_Multiattack._** The shark makes two Bite attacks.",
    ),
    (
        (
            "Animals",
            "Giant Shark",
            "Actions",
        ),
        "**_Bite._** _Melee Attack Roll:_ +9 (with Advantage if the target doesn't have all its Hit Points), reach 5 ft. _Hit:_ 22 (3d10 + 6) Piercing damage.",
    ),
    (
        (
            "Animals",
            "Giant Spider",
        ),
        "## Giant Spider",
    ),
    (
        (
            "Animals",
            "Giant Spider",
        ),
        "_Large Beast, Unaligned_",
    ),
    (
        (
            "Animals",
            "Giant Spider",
        ),
        "**AC** 14 **Initiative** +3 (13) <br>\n**HP** 26 (4d10 + 4) <br>\n**Speed** 30 ft., Climb 30 ft. <br>",
    ),
    (
        (
            "Animals",
            "Giant Spider",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>DEX</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>CON</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>2</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>WIS</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CHA</strong></td>\n      <td>4</td>\n      <td>−3</td>\n      <td>−3</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Giant Spider",
        ),
        "**Skills** Perception +4, Stealth +7<br>\n**Senses** Darkvision 60 ft.; Passive Perception 14<br>\n**Languages** None<br>\n**CR** 1 (XP 200; PB +2)",
    ),
    (
        (
            "Animals",
            "Giant Spider",
            "Traits",
        ),
        "### Traits",
    ),
    (
        (
            "Animals",
            "Giant Spider",
            "Traits",
        ),
        "**_Spider Climb._** The spider can climb difficult surfaces, including along ceilings, without needing to make an ability check.",
    ),
    (
        (
            "Animals",
            "Giant Spider",
            "Traits",
        ),
        "**_Web Walker._** The spider ignores movement restrictions caused by webs, and it knows the location of any other creature in contact with the same web.",
    ),
    (
        (
            "Animals",
            "Giant Spider",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Giant Spider",
            "Actions",
        ),
        "**_Bite._** _Melee Attack Roll:_ +5, reach 5 ft. _Hit:_ 7 (1d8 + 3) Piercing damage plus 7 (2d6) Poison damage.",
    ),
    (
        (
            "Animals",
            "Giant Spider",
            "Actions",
        ),
        "**_Web (Recharge 5–6)._** _Dexterity Saving Throw:_ DC 13, one creature the spider can see within 60 feet. _Failure:_ The target has the Restrained condition until the web is destroyed (AC 10; HP 5; Vulnerability to Fire damage; Immunity to Poison and Psychic damage).",
    ),
    (
        (
            "Animals",
            "Giant Toad",
        ),
        "## Giant Toad",
    ),
    (
        (
            "Animals",
            "Giant Toad",
        ),
        "_Large Beast, Unaligned_",
    ),
    (
        (
            "Animals",
            "Giant Toad",
        ),
        "**AC** 11 **Initiative** +1 (11) <br>\n**HP** 39 (6d10 + 6) <br>\n**Speed** 30 ft., Swim 30 ft. <br>",
    ),
    (
        (
            "Animals",
            "Giant Toad",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>DEX</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CON</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>2</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>WIS</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CHA</strong></td>\n      <td>3</td>\n      <td>−4</td>\n      <td>−4</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Giant Toad",
        ),
        "**Senses** Darkvision 60 ft.; Passive Perception 10<br>\n**Languages** None<br>\n**CR** 1 (XP 200; PB +2)",
    ),
    (
        (
            "Animals",
            "Giant Toad",
            "Traits",
        ),
        "### Traits",
    ),
    (
        (
            "Animals",
            "Giant Toad",
            "Traits",
        ),
        "**_Amphibious._** The toad can breathe air and water.",
    ),
    (
        (
            "Animals",
            "Giant Toad",
            "Traits",
        ),
        "**_Standing Leap._** The toad's Long Jump is up to 20 feet and its High Jump is up to 10 feet with or without a running start.",
    ),
    (
        (
            "Animals",
            "Giant Toad",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Giant Toad",
            "Actions",
        ),
        "**_Bite._** _Melee Attack Roll:_ +4, reach 5 ft. _Hit:_ 5 (1d6 + 2) Piercing damage plus 5 (2d4) Poison damage. If the target is a Medium or smaller creature, it has the Grappled condition (escape DC 12).",
    ),
    (
        (
            "Animals",
            "Giant Toad",
            "Actions",
        ),
        "**_Swallow._** The toad swallows a Medium or smaller target it is grappling. While swallowed, the target isn't Grappled but has the Blinded and Restrained conditions, and it has Total Cover against attacks and other effects outside the toad. In addition, the target takes 10 (3d6) Acid damage at the end of each of the toad's turns. The <br>\n&emsp;toad can have only one target swallowed at a time, and it can't use Bite while it has a swallowed target. If the toad dies, a swallowed creature is no longer Restrained and can escape from the corpse using 5 feet of movement, exiting with the Prone condition.",
    ),
    (
        (
            "Animals",
            "Giant Venomous Snake",
        ),
        "## Giant Venomous Snake",
    ),
    (
        (
            "Animals",
            "Giant Venomous Snake",
        ),
        "_Medium Beast, Unaligned_",
    ),
    (
        (
            "Animals",
            "Giant Venomous Snake",
        ),
        "**AC** 14 **Initiative** +4 (14) <br>\n**HP** 11 (2d8 + 2) <br>\n**Speed** 40 ft., Swim 40 ft. <br>",
    ),
    (
        (
            "Animals",
            "Giant Venomous Snake",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>DEX</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+4</td>\n      <td><strong>CON</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>2</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>WIS</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CHA</strong></td>\n      <td>3</td>\n      <td>−4</td>\n      <td>−4</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Giant Venomous Snake",
        ),
        "**Skills** Perception +2<br>\n**Senses** Blindsight 10 ft.; Passive Perception 12<br>\n**Languages** None<br>\n**CR** 1/4 (XP 50; PB +2)",
    ),
    (
        (
            "Animals",
            "Giant Venomous Snake",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Giant Venomous Snake",
            "Actions",
        ),
        "**_Bite._** _Melee Attack Roll:_ +6, reach 10 ft. _Hit:_ 6 (1d4 + 4) Piercing damage plus 4 (1d8) Poison damage.",
    ),
    (
        (
            "Animals",
            "Giant Vulture",
        ),
        "## Giant Vulture",
    ),
    (
        (
            "Animals",
            "Giant Vulture",
        ),
        "_Large Monstrosity, Neutral Evil_",
    ),
    (
        (
            "Animals",
            "Giant Vulture",
        ),
        "**AC** 10 **Initiative** +0 (10) <br>\n**HP** 25 (3d10 + 9) <br>\n**Speed** 10 ft., Fly 60 ft. <br>",
    ),
    (
        (
            "Animals",
            "Giant Vulture",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>DEX</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CON</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>6</td>\n      <td>−2</td>\n      <td>−2</td>\n      <td><strong>WIS</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CHA</strong></td>\n      <td>7</td>\n      <td>−2</td>\n      <td>−2</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Giant Vulture",
        ),
        "**Skills** Perception +3<br>\n**Resistances** Necrotic<br>\n**Senses** Darkvision 60 ft.; Passive Perception 13<br>\n**Languages** Understands Common but can't speak<br>\n**CR** 1 (XP 200; PB +2)",
    ),
    (
        (
            "Animals",
            "Giant Vulture",
            "Traits",
        ),
        "### Traits",
    ),
    (
        (
            "Animals",
            "Giant Vulture",
            "Traits",
        ),
        "**_Pack Tactics._** The vulture has Advantage on an attack roll against a creature if at least one of the vulture's allies is within 5 feet of the creature and the ally doesn't have the Incapacitated condition.",
    ),
    (
        (
            "Animals",
            "Giant Vulture",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Giant Vulture",
            "Actions",
        ),
        "**_Gouge._** _Melee Attack Roll:_ +4, reach 5 ft. _Hit:_ 9 (2d6 + 2) Piercing damage, and the target has the Poisoned condition until the end of its next turn.",
    ),
    (
        (
            "Animals",
            "Giant Wasp",
        ),
        "## Giant Wasp",
    ),
    (
        (
            "Animals",
            "Giant Wasp",
        ),
        "_Medium Beast, Unaligned_",
    ),
    (
        (
            "Animals",
            "Giant Wasp",
        ),
        "**AC** 13 **Initiative** +2 (12) <br>\n**HP** 22 (5d8) <br>\n**Speed** 10 ft., Fly 50 ft. <br>",
    ),
    (
        (
            "Animals",
            "Giant Wasp",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>DEX</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CON</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>1</td>\n      <td>−5</td>\n      <td>−5</td>\n      <td><strong>WIS</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CHA</strong></td>\n      <td>3</td>\n      <td>−4</td>\n      <td>−4</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Giant Wasp",
        ),
        "**Senses** Passive Perception 10<br>\n**Languages** None<br>\n**CR** 1/2 (XP 100; PB +2)",
    ),
    (
        (
            "Animals",
            "Giant Wasp",
            "Traits",
        ),
        "### Traits",
    ),
    (
        (
            "Animals",
            "Giant Wasp",
            "Traits",
        ),
        "**_Flyby._** The wasp doesn't provoke an Opportunity Attack when it flies out of an enemy's reach.",
    ),
    (
        (
            "Animals",
            "Giant Wasp",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Giant Wasp",
            "Actions",
        ),
        "**_Sting._** _Melee Attack Roll:_ +4, reach 5 ft. _Hit:_ 5 (1d6 + 2) Piercing damage plus 5 (2d4) Poison damage.",
    ),
    (
        (
            "Animals",
            "Giant Weasel",
        ),
        "## Giant Weasel",
    ),
    (
        (
            "Animals",
            "Giant Weasel",
        ),
        "_Medium Beast, Unaligned_",
    ),
    (
        (
            "Animals",
            "Giant Weasel",
        ),
        "**AC** 13 **Initiative** +3 (13) <br>\n**HP** 9 (2d8) <br>\n**Speed** 40 ft., Climb 30 ft. <br>",
    ),
    (
        (
            "Animals",
            "Giant Weasel",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>DEX</strong></td>\n      <td>17</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>CON</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>4</td>\n      <td>−3</td>\n      <td>−3</td>\n      <td><strong>WIS</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CHA</strong></td>\n      <td>5</td>\n      <td>−3</td>\n      <td>−3</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Giant Weasel",
        ),
        "**Skills** Acrobatics +5, Perception +3, Stealth +5<br>\n**Senses** Darkvision 60 ft.; Passive Perception 13<br>\n**Languages** None<br>\n**CR** 1/8 (XP 25; PB +2)",
    ),
    (
        (
            "Animals",
            "Giant Weasel",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Giant Weasel",
            "Actions",
        ),
        "**_Bite._** _Melee Attack Roll:_ +5, reach 5 ft. _Hit:_ 5 (1d4 + 3) Piercing damage.",
    ),
    (
        (
            "Animals",
            "Giant Wolf Spider",
        ),
        "## Giant Wolf Spider",
    ),
    (
        (
            "Animals",
            "Giant Wolf Spider",
        ),
        "_Medium Beast, Unaligned_",
    ),
    (
        (
            "Animals",
            "Giant Wolf Spider",
        ),
        "**AC** 13 **Initiative** +3 (13) <br>\n**HP** 11 (2d8 + 2) <br>\n**Speed** 40 ft., Climb 40 ft. <br>",
    ),
    (
        (
            "Animals",
            "Giant Wolf Spider",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>DEX</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>CON</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>3</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>WIS</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CHA</strong></td>\n      <td>4</td>\n      <td>−3</td>\n      <td>−3</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Giant Wolf Spider",
        ),
        "**Skills** Perception +3, Stealth +7<br>\n**Senses** Blindsight 10 ft., Darkvision 60 ft.; Passive Perception 13<br>\n**Languages** None<br>\n**CR** 1/4 (XP 50; PB +2)",
    ),
    (
        (
            "Animals",
            "Giant Wolf Spider",
            "Traits",
        ),
        "### Traits",
    ),
    (
        (
            "Animals",
            "Giant Wolf Spider",
            "Traits",
        ),
        "**_Spider Climb._** The spider can climb difficult surfaces, including along ceilings, without needing to make an ability check.",
    ),
    (
        (
            "Animals",
            "Giant Wolf Spider",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Giant Wolf Spider",
            "Actions",
        ),
        "**_Bite._** _Melee Attack Roll:_ +5, reach 5 ft. _Hit:_ 5 (1d4 + 3) Piercing damage plus 5 (2d4) Poison damage.",
    ),
    (
        (
            "Animals",
            "Goat",
        ),
        "## Goat",
    ),
    (
        (
            "Animals",
            "Goat",
        ),
        "_Medium Beast, Unaligned_",
    ),
    (
        (
            "Animals",
            "Goat",
        ),
        "**AC** 10 **Initiative** +0 (10) <br>\n**HP** 4 (1d8) <br>\n**Speed** 40 ft., Climb 30 ft. <br>",
    ),
    (
        (
            "Animals",
            "Goat",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+2</td>\n      <td><strong>DEX</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CON</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>2</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>WIS</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CHA</strong></td>\n      <td>5</td>\n      <td>−3</td>\n      <td>−3</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Goat",
        ),
        "**Skills** Perception +2<br>\n**Senses** Darkvision 60 ft.; Passive Perception 12<br>\n**Languages** None<br>\n**CR** 0 (XP 10; PB +2)",
    ),
    (
        (
            "Animals",
            "Goat",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Goat",
            "Actions",
        ),
        "**_Ram._** _Melee Attack Roll:_ +2, reach 5 ft. _Hit:_ 1 Bludgeoning damage, or 2 (1d4) Bludgeoning damage if the goat moved 20+ feet straight toward the target immediately before the hit.",
    ),
    (
        (
            "Animals",
            "Hawk",
        ),
        "## Hawk",
    ),
    (
        (
            "Animals",
            "Hawk",
        ),
        "_Tiny Beast, Unaligned_",
    ),
    (
        (
            "Animals",
            "Hawk",
        ),
        "**AC** 13 **Initiative** +3 (13) <br>\n**HP** 1 (1d4 − 1) <br>\n**Speed** 10 ft., Fly 60 ft. <br>",
    ),
    (
        (
            "Animals",
            "Hawk",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>5</td>\n      <td>−3</td>\n      <td>−3</td>\n      <td><strong>DEX</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>CON</strong></td>\n      <td>8</td>\n      <td>−1</td>\n      <td>−1</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>2</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>WIS</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CHA</strong></td>\n      <td>6</td>\n      <td>−2</td>\n      <td>−2</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Hawk",
        ),
        "**Skills** Perception +6<br>\n**Senses** Passive Perception 16<br>\n**Languages** None<br>\n**CR** 0 (XP 10; PB +2)",
    ),
    (
        (
            "Animals",
            "Hawk",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Hawk",
            "Actions",
        ),
        "**_Talons._** _Melee Attack Roll:_ +5, reach 5 ft. _Hit:_ 1 Slashing damage.",
    ),
    (
        (
            "Animals",
            "Hippopotamus",
        ),
        "## Hippopotamus",
    ),
    (
        (
            "Animals",
            "Hippopotamus",
        ),
        "_Large Beast, Unaligned_",
    ),
    (
        (
            "Animals",
            "Hippopotamus",
        ),
        "**AC** 14 **Initiative** −2 (8) <br>\n**HP** 82 (11d10 + 22) <br>\n**Speed** 30 ft., Swim 30 ft. <br>",
    ),
    (
        (
            "Animals",
            "Hippopotamus",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>21</td>\n      <td>+5</td>\n      <td>+7</td>\n      <td><strong>DEX</strong></td>\n      <td>7</td>\n      <td>−2</td>\n      <td>−2</td>\n      <td><strong>CON</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>2</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>WIS</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CHA</strong></td>\n      <td>4</td>\n      <td>−3</td>\n      <td>−3</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Hippopotamus",
        ),
        "**Skills** Perception +3<br>\n**Senses** Passive Perception 13<br>\n**Languages** None<br>\n**CR** 4 (XP 1,100; PB +2)",
    ),
    (
        (
            "Animals",
            "Hippopotamus",
            "Traits",
        ),
        "### Traits",
    ),
    (
        (
            "Animals",
            "Hippopotamus",
            "Traits",
        ),
        "**_Hold Breath._** The hippopotamus can hold its breath for 10 minutes.",
    ),
    (
        (
            "Animals",
            "Hippopotamus",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Hippopotamus",
            "Actions",
        ),
        "**_Multiattack._** The hippopotamus makes two Bite attacks.",
    ),
    (
        (
            "Animals",
            "Hippopotamus",
            "Actions",
        ),
        "**_Bite._** _Melee Attack Roll:_ +7, reach 5 ft. _Hit:_ 16 (2d10 + 5) Piercing damage.",
    ),
    (
        (
            "Animals",
            "Hunter Shark",
        ),
        "## Hunter Shark",
    ),
    (
        (
            "Animals",
            "Hunter Shark",
        ),
        "_Large Beast, Unaligned_",
    ),
    (
        (
            "Animals",
            "Hunter Shark",
        ),
        "**AC** 12 **Initiative** +2 (12) <br>\n**HP** 45 (6d10 + 12) <br>\n**Speed** 5 ft., Swim 40 ft. <br>",
    ),
    (
        (
            "Animals",
            "Hunter Shark",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+4</td>\n      <td><strong>DEX</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CON</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>1</td>\n      <td>−5</td>\n      <td>−5</td>\n      <td><strong>WIS</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CHA</strong></td>\n      <td>4</td>\n      <td>−3</td>\n      <td>−3</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Hunter Shark",
        ),
        "**Skills** Perception +2<br>\n**Senses** Blindsight 60 ft.; Passive Perception 12<br>\n**Languages** None<br>\n**CR** 2 (XP 450; PB +2)",
    ),
    (
        (
            "Animals",
            "Hunter Shark",
            "Traits",
        ),
        "### Traits",
    ),
    (
        (
            "Animals",
            "Hunter Shark",
            "Traits",
        ),
        "**_Water Breathing._** The shark can breathe only underwater.",
    ),
    (
        (
            "Animals",
            "Hunter Shark",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Hunter Shark",
            "Actions",
        ),
        "**_Bite._** _Melee Attack Roll:_ +6 (with Advantage if the target doesn't have all its Hit Points), reach 5 ft. _Hit:_ 14 (3d6 + 4) Piercing damage.",
    ),
    (
        (
            "Animals",
            "Hyena",
        ),
        "## Hyena",
    ),
    (
        (
            "Animals",
            "Hyena",
        ),
        "_Medium Beast, Unaligned_",
    ),
    (
        (
            "Animals",
            "Hyena",
        ),
        "**AC** 11 **Initiative** +1 (11) <br>\n**HP** 5 (1d8 + 1) <br>\n**Speed** 50 ft. <br>",
    ),
    (
        (
            "Animals",
            "Hyena",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>DEX</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CON</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>2</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>WIS</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CHA</strong></td>\n      <td>5</td>\n      <td>−3</td>\n      <td>−3</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Hyena",
        ),
        "**Skills** Perception +3<br>\n**Senses** Darkvision 60 ft.; Passive Perception 13<br>\n**Languages** None<br>\n**CR** 0 (XP 10; PB +2)",
    ),
    (
        (
            "Animals",
            "Hyena",
            "Traits",
        ),
        "### Traits",
    ),
    (
        (
            "Animals",
            "Hyena",
            "Traits",
        ),
        "**_Pack Tactics._** The hyena has Advantage on an attack roll against a creature if at least one of the hyena's allies is within 5 feet of the creature and the ally doesn't have the Incapacitated condition.",
    ),
    (
        (
            "Animals",
            "Hyena",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Hyena",
            "Actions",
        ),
        "**_Bite._** _Melee Attack Roll:_ +2, reach 5 ft. _Hit:_ 3 (1d6) Piercing damage.",
    ),
    (
        (
            "Animals",
            "Jackal",
        ),
        "## Jackal",
    ),
    (
        (
            "Animals",
            "Jackal",
        ),
        "_Small Beast, Unaligned_",
    ),
    (
        (
            "Animals",
            "Jackal",
        ),
        "**AC** 12 **Initiative** +2 (12) <br>\n**HP** 3 (1d6) <br>\n**Speed** 40 ft. <br>",
    ),
    (
        (
            "Animals",
            "Jackal",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>8</td>\n      <td>−1</td>\n      <td>−1</td>\n      <td><strong>DEX</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CON</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>3</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>WIS</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CHA</strong></td>\n      <td>6</td>\n      <td>−2</td>\n      <td>−2</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Jackal",
        ),
        "**Skills** Perception +5, Stealth +4<br>\n**Senses** Darkvision 90 ft.; Passive Perception 15<br>\n**Languages** None<br>\n**CR** 0 (XP 10; PB +2)",
    ),
    (
        (
            "Animals",
            "Jackal",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Jackal",
            "Actions",
        ),
        "**_Bite._** _Melee Attack Roll:_ +1, reach 5 ft. _Hit:_ 1 (1d4 − 1) Piercing damage.",
    ),
    (
        (
            "Animals",
            "Killer Whale",
        ),
        "## Killer Whale",
    ),
    (
        (
            "Animals",
            "Killer Whale",
        ),
        "_Huge Beast, Unaligned_",
    ),
    (
        (
            "Animals",
            "Killer Whale",
        ),
        "**AC** 12 **Initiative** +2 (12) <br>\n**HP** 90 (12d12 + 12) <br>\n**Speed** 5 ft., Swim 60 ft. <br>",
    ),
    (
        (
            "Animals",
            "Killer Whale",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>19</td>\n      <td>+4</td>\n      <td>+4</td>\n      <td><strong>DEX</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CON</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>3</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>WIS</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CHA</strong></td>\n      <td>7</td>\n      <td>−2</td>\n      <td>−2</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Killer Whale",
        ),
        "**Skills** Perception +3, Stealth +4<br>\n**Senses** Blindsight 120 ft.; Passive Perception 13<br>\n**Languages** None<br>\n**CR** 3 (XP 700; PB +2)",
    ),
    (
        (
            "Animals",
            "Killer Whale",
            "Traits",
        ),
        "### Traits",
    ),
    (
        (
            "Animals",
            "Killer Whale",
            "Traits",
        ),
        "**_Hold Breath._** The whale can hold its breath for 30 minutes.",
    ),
    (
        (
            "Animals",
            "Killer Whale",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Killer Whale",
            "Actions",
        ),
        "**_Bite._** _Melee Attack Roll:_ +6, reach 5 ft. _Hit:_ 21 (5d6 + 4) Piercing damage.",
    ),
    (
        (
            "Animals",
            "Lion",
        ),
        "## Lion",
    ),
    (
        (
            "Animals",
            "Lion",
        ),
        "_Large Beast, Unaligned_",
    ),
    (
        (
            "Animals",
            "Lion",
        ),
        "**AC** 12 **Initiative** +2 (12) <br>\n**HP** 22 (4d10) <br>\n**Speed** 50 ft. <br>",
    ),
    (
        (
            "Animals",
            "Lion",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>17</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>DEX</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CON</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>3</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>WIS</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CHA</strong></td>\n      <td>8</td>\n      <td>−1</td>\n      <td>−1</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Lion",
        ),
        "**Skills** Perception +3, Stealth +4<br>\n**Senses** Darkvision 60 ft.; Passive Perception 13<br>\n**Languages** None<br>\n**CR** 1 (XP 200; PB +2)",
    ),
    (
        (
            "Animals",
            "Lion",
            "Traits",
        ),
        "### Traits",
    ),
    (
        (
            "Animals",
            "Lion",
            "Traits",
        ),
        "**_Pack Tactics._** The lion has Advantage on an attack roll against a creature if at least one of the lion's allies is within 5 feet of the creature and the ally doesn't have the Incapacitated condition.",
    ),
    (
        (
            "Animals",
            "Lion",
            "Traits",
        ),
        "**_Running Leap._** With a 10-foot running start, the lion can Long Jump up to 25 feet.",
    ),
    (
        (
            "Animals",
            "Lion",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Lion",
            "Actions",
        ),
        "**_Multiattack._** The lion makes two Rend attacks. It can replace one attack with a use of Roar.",
    ),
    (
        (
            "Animals",
            "Lion",
            "Actions",
        ),
        "**_Rend._** _Melee Attack Roll:_ +5, reach 5 ft. _Hit:_ 7 (1d8 + 3) Slashing damage.",
    ),
    (
        (
            "Animals",
            "Lion",
            "Actions",
        ),
        "**_Roar._** _Wisdom Saving Throw:_ DC 11, one creature within 15 feet. _Failure:_ The target has the Frightened condition until the start of the lion's next turn.",
    ),
    (
        (
            "Animals",
            "Lizard",
        ),
        "## Lizard",
    ),
    (
        (
            "Animals",
            "Lizard",
        ),
        "_Tiny Beast, Unaligned_",
    ),
    (
        (
            "Animals",
            "Lizard",
        ),
        "**AC** 10 **Initiative** +0 (10) <br>\n**HP** 2 (1d4) <br>\n**Speed** 20 ft., Climb 20 ft. <br>",
    ),
    (
        (
            "Animals",
            "Lizard",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>2</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>DEX</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CON</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>1</td>\n      <td>−5</td>\n      <td>−5</td>\n      <td><strong>WIS</strong></td>\n      <td>8</td>\n      <td>−1</td>\n      <td>−1</td>\n      <td><strong>CHA</strong></td>\n      <td>3</td>\n      <td>−4</td>\n      <td>−4</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Lizard",
        ),
        "**Senses** Darkvision 30 ft.; Passive Perception 9<br>\n**Languages** None<br>\n**CR** 0 (XP 10; PB +2)",
    ),
    (
        (
            "Animals",
            "Lizard",
            "Traits",
        ),
        "### Traits",
    ),
    (
        (
            "Animals",
            "Lizard",
            "Traits",
        ),
        "**_Spider Climb._** The lizard can climb difficult surfaces, including along ceilings, without needing to make an ability check.",
    ),
    (
        (
            "Animals",
            "Lizard",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Lizard",
            "Actions",
        ),
        "**_Bite._** _Melee Attack Roll:_ +2, reach 5 ft. _Hit:_ 1 Piercing damage.",
    ),
    (
        (
            "Animals",
            "Mammoth",
        ),
        "## Mammoth",
    ),
    (
        (
            "Animals",
            "Mammoth",
        ),
        "_Huge Beast, Unaligned_",
    ),
    (
        (
            "Animals",
            "Mammoth",
        ),
        "**AC** 13 **Initiative** +2 (12) <br>\n**HP** 126 (11d12 + 55) <br>\n**Speed** 50 ft. <br>",
    ),
    (
        (
            "Animals",
            "Mammoth",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>24</td>\n      <td>+7</td>\n      <td>+10</td>\n      <td><strong>DEX</strong></td>\n      <td>9</td>\n      <td>−1</td>\n      <td>−1</td>\n      <td><strong>CON</strong></td>\n      <td>21</td>\n      <td>+5</td>\n      <td>+8</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>3</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>WIS</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CHA</strong></td>\n      <td>6</td>\n      <td>−2</td>\n      <td>−2</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Mammoth",
        ),
        "**Senses** Passive Perception 10<br>\n**Languages** None<br>\n**CR** 6 (XP 2,300; PB +3)",
    ),
    (
        (
            "Animals",
            "Mammoth",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Mammoth",
            "Actions",
        ),
        "**_Multiattack._** The mammoth makes two Gore attacks.",
    ),
    (
        (
            "Animals",
            "Mammoth",
            "Actions",
        ),
        "**_Gore._** _Melee Attack Roll:_ +10, reach 10 ft. _Hit:_ 18 (2d10 + 7) Piercing damage. If the target is a Huge or smaller creature and the mammoth moved 20+ feet straight toward it immediately before the hit, the target has the Prone condition.",
    ),
    (
        (
            "Animals",
            "Mammoth",
            "Bonus Actions",
        ),
        "### Bonus Actions",
    ),
    (
        (
            "Animals",
            "Mammoth",
            "Bonus Actions",
        ),
        "**_Trample._** _Dexterity Saving Throw:_ DC 18, one creature within 5 feet that has the Prone condition. _Failure:_ 29 (4d10 + 7) Bludgeoning damage. _Success:_ Half damage.",
    ),
    (
        (
            "Animals",
            "Mastiff",
        ),
        "## Mastiff",
    ),
    (
        (
            "Animals",
            "Mastiff",
        ),
        "_Medium Beast, Unaligned_",
    ),
    (
        (
            "Animals",
            "Mastiff",
        ),
        "**AC** 12 **Initiative** +2 (12) <br>\n**HP** 5 (1d8 + 1) <br>\n**Speed** 40 ft. <br>",
    ),
    (
        (
            "Animals",
            "Mastiff",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>DEX</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CON</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>3</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>WIS</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+3</td>\n      <td><strong>CHA</strong></td>\n      <td>7</td>\n      <td>−2</td>\n      <td>−2</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Mastiff",
        ),
        "**Skills** Perception +5<br>\n**Senses** Darkvision 60 ft.; Passive Perception 15<br>\n**Languages** None<br>\n**CR** 1/8 (XP 25; PB +2)",
    ),
    (
        (
            "Animals",
            "Mastiff",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Mastiff",
            "Actions",
        ),
        "**_Bite._** _Melee Attack Roll:_ +3, reach 5 ft. _Hit:_ 4 (1d6 + 1) Piercing damage. If the target is a Medium or smaller creature, it has the Prone condition.",
    ),
    (
        (
            "Animals",
            "Mule",
        ),
        "## Mule",
    ),
    (
        (
            "Animals",
            "Mule",
        ),
        "_Medium Beast, Unaligned_",
    ),
    (
        (
            "Animals",
            "Mule",
        ),
        "**AC** 10 **Initiative** +0 (10) <br>\n**HP** 11 (2d8 + 2) <br>\n**Speed** 40 ft. <br>",
    ),
    (
        (
            "Animals",
            "Mule",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+4</td>\n      <td><strong>DEX</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CON</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>2</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>WIS</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CHA</strong></td>\n      <td>5</td>\n      <td>−3</td>\n      <td>−3</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Mule",
        ),
        "**Senses** Passive Perception 10<br>\n**Languages** None<br>\n**CR** 1/8 (XP 25; PB +2)",
    ),
    (
        (
            "Animals",
            "Mule",
            "Traits",
        ),
        "### Traits",
    ),
    (
        (
            "Animals",
            "Mule",
            "Traits",
        ),
        "**_Beast of Burden._** The mule counts as one size larger for the purpose of determining its carrying capacity.",
    ),
    (
        (
            "Animals",
            "Mule",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Mule",
            "Actions",
        ),
        "**_Hooves._** _Melee Attack Roll:_ +4, reach 5 ft. _Hit:_ 4 (1d4 + 2) Bludgeoning damage.",
    ),
    (
        (
            "Animals",
            "Octopus",
        ),
        "## Octopus",
    ),
    (
        (
            "Animals",
            "Octopus",
        ),
        "_Small Beast, Unaligned_",
    ),
    (
        (
            "Animals",
            "Octopus",
        ),
        "**AC** 12 **Initiative** +2 (12) <br>\n**HP** 3 (1d6) <br>\n**Speed** 5 ft., Swim 30 ft. <br>",
    ),
    (
        (
            "Animals",
            "Octopus",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>4</td>\n      <td>-3</td>\n      <td>-3</td>\n      <td><strong>DEX</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CON</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>3</td>\n      <td>-4</td>\n      <td>-4</td>\n      <td><strong>WIS</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CHA</strong></td>\n      <td>4</td>\n      <td>-3</td>\n      <td>-3</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Octopus",
        ),
        "**Skills** Perception +2, Stealth +6<br>\n**Senses** Darkvision 30 ft.; Passive Perception 12<br>\n**Languages** None<br>\n**CR** 0 (XP 10; PB +2)",
    ),
    (
        (
            "Animals",
            "Octopus",
            "Traits",
        ),
        "### Traits",
    ),
    (
        (
            "Animals",
            "Octopus",
            "Traits",
        ),
        "**_Compression._** The octopus can move through a space as narrow as 1 inch without expending extra movement to do so.",
    ),
    (
        (
            "Animals",
            "Octopus",
            "Traits",
        ),
        "**_Water Breathing._** The octopus can breathe only underwater.",
    ),
    (
        (
            "Animals",
            "Octopus",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Octopus",
            "Actions",
        ),
        "**_Tentacles._** _Melee Attack Roll:_ +4, reach 5 ft. _Hit:_ 1 Bludgeoning damage.",
    ),
    (
        (
            "Animals",
            "Octopus",
            "Reactions",
        ),
        "### Reactions",
    ),
    (
        (
            "Animals",
            "Octopus",
            "Reactions",
        ),
        "**_Ink Cloud (1/Day)._** _Trigger:_ A creature ends its turn within 5 feet of the octopus while underwater. _Response:_ The octopus releases ink that fills a 5-foot Cube centered on itself, and the octopus moves up to its Swim Speed. The Cube is Heavily Obscured for 1 minute or until a strong current or similar effect disperses the ink.",
    ),
    (
        (
            "Animals",
            "Owl",
        ),
        "## Owl",
    ),
    (
        (
            "Animals",
            "Owl",
        ),
        "_Tiny Beast, Unaligned_",
    ),
    (
        (
            "Animals",
            "Owl",
        ),
        "**AC** 11 **Initiative** +1 (11) <br>\n**HP** 1 (1d4 − 1) <br>\n**Speed** 5 ft., Fly 60 ft. <br>",
    ),
    (
        (
            "Animals",
            "Owl",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>3</td>\n      <td>-4</td>\n      <td>-4</td>\n      <td><strong>DEX</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CON</strong></td>\n      <td>8</td>\n      <td>-1</td>\n      <td>-1</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>2</td>\n      <td>-4</td>\n      <td>-4</td>\n      <td><strong>WIS</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CHA</strong></td>\n      <td>7</td>\n      <td>-2</td>\n      <td>-2</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Owl",
        ),
        "**Skills** Perception +5, Stealth +5<br>\n**Senses** Darkvision 120 ft.; Passive Perception 15<br>\n**Languages** None<br>\n**CR** 0 (XP 10; PB +2)",
    ),
    (
        (
            "Animals",
            "Owl",
            "Traits",
        ),
        "### Traits",
    ),
    (
        (
            "Animals",
            "Owl",
            "Traits",
        ),
        "**_Flyby._** The owl doesn't provoke an Opportunity Attack when it flies out of an enemy's reach.",
    ),
    (
        (
            "Animals",
            "Owl",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Owl",
            "Actions",
        ),
        "**_Talons._** _Melee Attack Roll:_ +3, reach 5 ft. _Hit:_ 1 Slashing damage.",
    ),
    (
        (
            "Animals",
            "Panther",
        ),
        "## Panther",
    ),
    (
        (
            "Animals",
            "Panther",
        ),
        "_Medium Beast, Unaligned_",
    ),
    (
        (
            "Animals",
            "Panther",
        ),
        "**AC** 13 **Initiative** +3 (13) <br>\n**HP** 13 (3d8) <br>\n**Speed** 50 ft., Climb 40 ft. <br>",
    ),
    (
        (
            "Animals",
            "Panther",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>DEX</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>CON</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>3</td>\n      <td>-4</td>\n      <td>-4</td>\n      <td><strong>WIS</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CHA</strong></td>\n      <td>7</td>\n      <td>-2</td>\n      <td>-2</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Panther",
        ),
        "**Skills** Perception +4, Stealth +7<br>\n**Senses** Darkvision 60 ft.; Passive Perception 14<br>\n**Languages** None<br>\n**CR** 1/4 (XP 50; PB +2)",
    ),
    (
        (
            "Animals",
            "Panther",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Panther",
            "Actions",
        ),
        "**_Rend._** _Melee Attack Roll:_ +5, reach 5 ft. _Hit:_ 6 (1d6 + 3) Slashing damage.",
    ),
    (
        (
            "Animals",
            "Panther",
            "Bonus Actions",
        ),
        "### Bonus Actions",
    ),
    (
        (
            "Animals",
            "Panther",
            "Bonus Actions",
        ),
        "**_Nimble Escape._** The panther takes the Disengage or Hide action.",
    ),
    (
        (
            "Animals",
            "Piranha",
        ),
        "## Piranha",
    ),
    (
        (
            "Animals",
            "Piranha",
        ),
        "_Tiny Beast, Unaligned_",
    ),
    (
        (
            "Animals",
            "Piranha",
        ),
        "**AC** 13 **Initiative** +3 (13) <br>\n**HP** 1 (1d4 − 1) <br>\n**Speed** 5 ft., Swim 40 ft. <br>",
    ),
    (
        (
            "Animals",
            "Piranha",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>2</td>\n      <td>-4</td>\n      <td>-4</td>\n      <td><strong>DEX</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>CON</strong></td>\n      <td>9</td>\n      <td>-1</td>\n      <td>-1</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>1</td>\n      <td>-5</td>\n      <td>-5</td>\n      <td><strong>WIS</strong></td>\n      <td>7</td>\n      <td>-2</td>\n      <td>-2</td>\n      <td><strong>CHA</strong></td>\n      <td>2</td>\n      <td>-4</td>\n      <td>-4</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Piranha",
        ),
        "**Senses** Darkvision 60 ft.; Passive Perception 8<br>\n**Languages** None<br>\n**CR** 0 (XP 10; PB +2)",
    ),
    (
        (
            "Animals",
            "Piranha",
            "Traits",
        ),
        "### Traits",
    ),
    (
        (
            "Animals",
            "Piranha",
            "Traits",
        ),
        "**_Water Breathing._** The piranha can breathe only underwater.",
    ),
    (
        (
            "Animals",
            "Piranha",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Piranha",
            "Actions",
        ),
        "**_Bite._** _Melee Attack Roll:_ +5 (with Advantage if the target doesn't have all its Hit Points), reach 5 ft. _Hit:_ 1 Piercing damage.",
    ),
    (
        (
            "Animals",
            "Plesiosaurus",
        ),
        "## Plesiosaurus",
    ),
    (
        (
            "Animals",
            "Plesiosaurus",
        ),
        "_Large Beast (Dinosaur), Unaligned_",
    ),
    (
        (
            "Animals",
            "Plesiosaurus",
        ),
        "**AC** 13 **Initiative** +2 (12) <br>\n**HP** 68 (8d10 + 24) <br>\n**Speed** 20 ft., Swim 40 ft. <br>",
    ),
    (
        (
            "Animals",
            "Plesiosaurus",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+4</td>\n      <td><strong>DEX</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CON</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>2</td>\n      <td>-4</td>\n      <td>-4</td>\n      <td><strong>WIS</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CHA</strong></td>\n      <td>5</td>\n      <td>-3</td>\n      <td>-3</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Plesiosaurus",
        ),
        "**Skills** Perception +3, Stealth +4<br>\n**Senses** Passive Perception 13<br>\n**Languages** None<br>\n**CR** 2 (XP 450; PB +2)",
    ),
    (
        (
            "Animals",
            "Plesiosaurus",
            "Traits",
        ),
        "### Traits",
    ),
    (
        (
            "Animals",
            "Plesiosaurus",
            "Traits",
        ),
        "**_Hold Breath._** The plesiosaurus can hold its breath for 1 hour.",
    ),
    (
        (
            "Animals",
            "Plesiosaurus",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Plesiosaurus",
            "Actions",
        ),
        "**_Bite._** _Melee Attack Roll:_ +6, reach 10 ft. _Hit:_ 11 (2d6 + 4) Piercing damage.",
    ),
    (
        (
            "Animals",
            "Polar Bear",
        ),
        "## Polar Bear",
    ),
    (
        (
            "Animals",
            "Polar Bear",
        ),
        "_Large Beast, Unaligned_",
    ),
    (
        (
            "Animals",
            "Polar Bear",
        ),
        "**AC** 12 **Initiative** +2 (12) <br>\n**HP** 42 (5d10 + 15) <br>\n**Speed** 40 ft., Swim 40 ft. <br>",
    ),
    (
        (
            "Animals",
            "Polar Bear",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>20</td>\n      <td>+5</td>\n      <td>+5</td>\n      <td><strong>DEX</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CON</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>2</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>WIS</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CHA</strong></td>\n      <td>7</td>\n      <td>−2</td>\n      <td>−2</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Polar Bear",
        ),
        "**Skills** Perception +5, Stealth +4<br>\n**Resistances** Cold<br>\n**Senses** Darkvision 60 ft.; Passive Perception 15<br>\n**Languages** None<br>\n**CR** 2 (XP 450; PB +2)",
    ),
    (
        (
            "Animals",
            "Polar Bear",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Polar Bear",
            "Actions",
        ),
        "**_Multiattack._** The bear makes two Rend attacks.",
    ),
    (
        (
            "Animals",
            "Polar Bear",
            "Actions",
        ),
        "**_Rend._** _Melee Attack Roll:_ +7, reach 5 ft. _Hit:_ 9 (1d8 + 5) Slashing damage.",
    ),
    (
        (
            "Animals",
            "Pony",
        ),
        "## Pony",
    ),
    (
        (
            "Animals",
            "Pony",
        ),
        "_Medium Beast, Unaligned_",
    ),
    (
        (
            "Animals",
            "Pony",
        ),
        "**AC** 10 **Initiative** +0 (10) <br>\n**HP** 11 (2d8 + 2) <br>\n**Speed** 40 ft. <br>",
    ),
    (
        (
            "Animals",
            "Pony",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+4</td>\n      <td><strong>DEX</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CON</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>2</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>WIS</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CHA</strong></td>\n      <td>7</td>\n      <td>−2</td>\n      <td>−2</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Pony",
        ),
        "**Senses** Passive Perception 10<br>\n**Languages** None<br>\n**CR** 1/8 (XP 25; PB +2)",
    ),
    (
        (
            "Animals",
            "Pony",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Pony",
            "Actions",
        ),
        "**_Hooves._** _Melee Attack Roll:_ +4, reach 5 ft. _Hit:_ 4 (1d4 + 2) Bludgeoning damage.",
    ),
    (
        (
            "Animals",
            "Pteranodon",
        ),
        "## Pteranodon",
    ),
    (
        (
            "Animals",
            "Pteranodon",
        ),
        "_Medium Beast (Dinosaur), Unaligned_",
    ),
    (
        (
            "Animals",
            "Pteranodon",
        ),
        "**AC** 13 **Initiative** +2 (12) <br>\n**HP** 13 (3d8) <br>\n**Speed** 10 ft., Fly 60 ft. <br>",
    ),
    (
        (
            "Animals",
            "Pteranodon",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>DEX</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CON</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>2</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>WIS</strong></td>\n      <td>9</td>\n      <td>−1</td>\n      <td>−1</td>\n      <td><strong>CHA</strong></td>\n      <td>5</td>\n      <td>−3</td>\n      <td>−3</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Pteranodon",
        ),
        "**Skills** Perception +1<br>\n**Senses** Passive Perception 11<br>\n**Languages** None<br>\n**CR** 1/4 (XP 50; PB +2)",
    ),
    (
        (
            "Animals",
            "Pteranodon",
            "Traits",
        ),
        "### Traits",
    ),
    (
        (
            "Animals",
            "Pteranodon",
            "Traits",
        ),
        "**_Flyby._** The pteranodon doesn't provoke an Opportunity Attack when it flies out of an enemy's reach.",
    ),
    (
        (
            "Animals",
            "Pteranodon",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Pteranodon",
            "Actions",
        ),
        "**_Bite._** _Melee Attack Roll:_ +4, reach 5 ft. _Hit:_ 6 (1d8 + 2) Piercing damage.",
    ),
    (
        (
            "Animals",
            "Rat",
        ),
        "## Rat",
    ),
    (
        (
            "Animals",
            "Rat",
        ),
        "_Tiny Beast, Unaligned_",
    ),
    (
        (
            "Animals",
            "Rat",
        ),
        "**AC** 10 **Initiative** +0 (10) <br>\n**HP** 1 (1d4 − 1) <br>\n**Speed** 20 ft., Climb 20 ft. <br>",
    ),
    (
        (
            "Animals",
            "Rat",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>2</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>DEX</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CON</strong></td>\n      <td>9</td>\n      <td>−1</td>\n      <td>−1</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>2</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>WIS</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CHA</strong></td>\n      <td>4</td>\n      <td>−3</td>\n      <td>−3</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Rat",
        ),
        "**Skills** Perception +2<br>\n**Senses** Darkvision 30 ft.; Passive Perception 12<br>\n**Languages** None<br>\n**CR** 0 (XP 10; PB +2)",
    ),
    (
        (
            "Animals",
            "Rat",
            "Traits",
        ),
        "### Traits",
    ),
    (
        (
            "Animals",
            "Rat",
            "Traits",
        ),
        "**_Agile._** The rat doesn't provoke an Opportunity Attack when it moves out of an enemy's reach.",
    ),
    (
        (
            "Animals",
            "Rat",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Rat",
            "Actions",
        ),
        "**_Bite._** _Melee Attack Roll:_ +2, reach 5 ft. _Hit:_ 1 Piercing damage.",
    ),
    (
        (
            "Animals",
            "Raven",
        ),
        "## Raven",
    ),
    (
        (
            "Animals",
            "Raven",
        ),
        "_Tiny Beast, Unaligned_",
    ),
    (
        (
            "Animals",
            "Raven",
        ),
        "**AC** 12 **Initiative** +2 (12) <br>\n**HP** 2 (1d4) <br>\n**Speed** 10 ft., Fly 50 ft. <br>",
    ),
    (
        (
            "Animals",
            "Raven",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>2</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>DEX</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CON</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>5</td>\n      <td>−3</td>\n      <td>−3</td>\n      <td><strong>WIS</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CHA</strong></td>\n      <td>6</td>\n      <td>−2</td>\n      <td>−2</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Raven",
        ),
        "**Skills** Perception +3<br>\n**Senses** Passive Perception 13<br>\n**Languages** None<br>\n**CR** 0 (XP 10; PB +2)",
    ),
    (
        (
            "Animals",
            "Raven",
            "Traits",
        ),
        "### Traits",
    ),
    (
        (
            "Animals",
            "Raven",
            "Traits",
        ),
        "**_Mimicry._** The raven can mimic simple sounds it has heard, such as a whisper or chitter. A hearer can discern the sounds are imitations with a successful DC 10 Wisdom (Insight) check.",
    ),
    (
        (
            "Animals",
            "Raven",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Raven",
            "Actions",
        ),
        "**_Beak._** _Melee Attack Roll:_ +4, reach 5 ft. _Hit:_ 1 Piercing damage.",
    ),
    (
        (
            "Animals",
            "Reef Shark",
        ),
        "## Reef Shark",
    ),
    (
        (
            "Animals",
            "Reef Shark",
        ),
        "_Medium Beast, Unaligned_",
    ),
    (
        (
            "Animals",
            "Reef Shark",
        ),
        "**AC** 12 **Initiative** +2 (12) <br>\n**HP** 22 (4d8 + 4) <br>\n**Speed** 5 ft., Swim 30 ft. <br>",
    ),
    (
        (
            "Animals",
            "Reef Shark",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>DEX</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CON</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>1</td>\n      <td>−5</td>\n      <td>−5</td>\n      <td><strong>WIS</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CHA</strong></td>\n      <td>4</td>\n      <td>−3</td>\n      <td>−3</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Reef Shark",
        ),
        "**Skills** Perception +2<br>\n**Senses** Blindsight 30 ft.; Passive Perception 12<br>\n**Languages** None<br>\n**CR** 1/2 (XP 100; PB +2)",
    ),
    (
        (
            "Animals",
            "Reef Shark",
            "Traits",
        ),
        "### Traits",
    ),
    (
        (
            "Animals",
            "Reef Shark",
            "Traits",
        ),
        "**_Pack Tactics._** The shark has Advantage on an attack roll against a creature if at least one of the shark's allies is within 5 feet of the creature and the ally doesn't have the Incapacitated condition.",
    ),
    (
        (
            "Animals",
            "Reef Shark",
            "Traits",
        ),
        "**_Water Breathing._** The shark can breathe only underwater.",
    ),
    (
        (
            "Animals",
            "Reef Shark",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Reef Shark",
            "Actions",
        ),
        "**_Bite._** _Melee Attack Roll:_ +4, reach 5 ft. _Hit:_ 7 (2d4 + 2) Piercing damage.",
    ),
    (
        (
            "Animals",
            "Rhinoceros",
        ),
        "## Rhinoceros",
    ),
    (
        (
            "Animals",
            "Rhinoceros",
        ),
        "_Large Beast, Unaligned_",
    ),
    (
        (
            "Animals",
            "Rhinoceros",
        ),
        "**AC** 13 **Initiative** −1 (9) <br>\n**HP** 45 (6d10 + 12) <br>\n**Speed** 40 ft. <br>",
    ),
    (
        (
            "Animals",
            "Rhinoceros",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>21</td>\n      <td>+5</td>\n      <td>+5</td>\n      <td><strong>DEX</strong></td>\n      <td>8</td>\n      <td>−1</td>\n      <td>−1</td>\n      <td><strong>CON</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>2</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>WIS</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CHA</strong></td>\n      <td>6</td>\n      <td>−2</td>\n      <td>−2</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Rhinoceros",
        ),
        "**Senses** Passive Perception 11<br>\n**Languages** None<br>\n**CR** 2 (XP 450; PB +2)",
    ),
    (
        (
            "Animals",
            "Rhinoceros",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Rhinoceros",
            "Actions",
        ),
        "**_Gore._** _Melee Attack Roll:_ +7, reach 5 ft. _Hit:_ 14 (2d8 + 5) Piercing damage. If target is a Large or smaller creature and the rhinoceros moved 20+ feet straight toward it immediately before the hit, the target takes an extra 9 (2d8) Piercing damage and has the Prone condition.",
    ),
    (
        (
            "Animals",
            "Riding Horse",
        ),
        "## Riding Horse",
    ),
    (
        (
            "Animals",
            "Riding Horse",
        ),
        "_Large Beast, Unaligned_",
    ),
    (
        (
            "Animals",
            "Riding Horse",
        ),
        "**AC** 11 **Initiative** +1 (11) <br>\n**HP** 13 (2d10 + 2) <br>\n**Speed** 60 ft. <br>",
    ),
    (
        (
            "Animals",
            "Riding Horse",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>DEX</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CON</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>2</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>WIS</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CHA</strong></td>\n      <td>7</td>\n      <td>−2</td>\n      <td>−2</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Riding Horse",
        ),
        "**Senses** Passive Perception 10<br>\n**Languages** None<br>\n**CR** 1/4 (XP 50; PB +2)",
    ),
    (
        (
            "Animals",
            "Riding Horse",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Riding Horse",
            "Actions",
        ),
        "**_Hooves._** _Melee Attack Roll:_ +5, reach 5 ft. _Hit:_ 7 (1d8 + 3) Bludgeoning damage.",
    ),
    (
        (
            "Animals",
            "Saber-Toothed Tiger",
        ),
        "## Saber-Toothed Tiger",
    ),
    (
        (
            "Animals",
            "Saber-Toothed Tiger",
        ),
        "_Large Beast, Unaligned_",
    ),
    (
        (
            "Animals",
            "Saber-Toothed Tiger",
        ),
        "**AC** 13 **Initiative** +3 (13) <br>\n**HP** 52 (7d10 + 14) <br>\n**Speed** 40 ft. <br>",
    ),
    (
        (
            "Animals",
            "Saber-Toothed Tiger",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+6</td>\n      <td><strong>DEX</strong></td>\n      <td>17</td>\n      <td>+3</td>\n      <td>+5</td>\n      <td><strong>CON</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>3</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>WIS</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CHA</strong></td>\n      <td>8</td>\n      <td>−1</td>\n      <td>−1</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Saber-Toothed Tiger",
        ),
        "**Skills** Perception +5, Stealth +7<br>\n**Senses** Darkvision 60 ft.; Passive Perception 15<br>\n**Languages** None<br>\n**CR** 2 (XP 450; PB +2)",
    ),
    (
        (
            "Animals",
            "Saber-Toothed Tiger",
            "Traits",
        ),
        "### Traits",
    ),
    (
        (
            "Animals",
            "Saber-Toothed Tiger",
            "Traits",
        ),
        "**_Running Leap._** With a 10-foot running start, the tiger can Long Jump up to 25 feet.",
    ),
    (
        (
            "Animals",
            "Saber-Toothed Tiger",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Saber-Toothed Tiger",
            "Actions",
        ),
        "**_Multiattack._** The tiger makes two Rend attacks.",
    ),
    (
        (
            "Animals",
            "Saber-Toothed Tiger",
            "Actions",
        ),
        "**_Rend._** _Melee Attack Roll:_ +6, reach 5 ft. _Hit:_ 11 (2d6 + 4) Slashing damage.",
    ),
    (
        (
            "Animals",
            "Saber-Toothed Tiger",
            "Bonus Actions",
        ),
        "### Bonus Actions",
    ),
    (
        (
            "Animals",
            "Saber-Toothed Tiger",
            "Bonus Actions",
        ),
        "**_Nimble Escape._** The tiger takes the Disengage or Hide action.",
    ),
    (
        (
            "Animals",
            "Scorpion",
        ),
        "## Scorpion",
    ),
    (
        (
            "Animals",
            "Scorpion",
        ),
        "_Tiny Beast, Unaligned_",
    ),
    (
        (
            "Animals",
            "Scorpion",
        ),
        "**AC** 11 **Initiative** +0 (10) <br>\n**HP** 1 (1d4 − 1) <br>\n**Speed** 10 ft. <br>",
    ),
    (
        (
            "Animals",
            "Scorpion",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>2</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>DEX</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CON</strong></td>\n      <td>8</td>\n      <td>−1</td>\n      <td>−1</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>1</td>\n      <td>−5</td>\n      <td>−5</td>\n      <td><strong>WIS</strong></td>\n      <td>8</td>\n      <td>−1</td>\n      <td>−1</td>\n      <td><strong>CHA</strong></td>\n      <td>2</td>\n      <td>−4</td>\n      <td>−4</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Scorpion",
        ),
        "**Senses** Blindsight 10 ft.; Passive Perception 9<br>\n**Languages** None<br>\n**CR** 0 (XP 10; PB +2)",
    ),
    (
        (
            "Animals",
            "Scorpion",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Scorpion",
            "Actions",
        ),
        "**_Sting._** _Melee Attack Roll:_ +2, reach 5 ft. _Hit:_ 1 Piercing damage plus 3 (1d6) Poison damage.",
    ),
    (
        (
            "Animals",
            "Seahorse",
        ),
        "## Seahorse",
    ),
    (
        (
            "Animals",
            "Seahorse",
        ),
        "_Tiny Beast, Unaligned_",
    ),
    (
        (
            "Animals",
            "Seahorse",
        ),
        "**AC** 12 **Initiative** +1 (11) <br>\n**HP** 1 (1d4 − 1) <br>\n**Speed** 5 ft., Swim 20 ft. <br>",
    ),
    (
        (
            "Animals",
            "Seahorse",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>1</td>\n      <td>−5</td>\n      <td>−5</td>\n      <td><strong>DEX</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CON</strong></td>\n      <td>8</td>\n      <td>−1</td>\n      <td>−1</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>1</td>\n      <td>−5</td>\n      <td>−5</td>\n      <td><strong>WIS</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CHA</strong></td>\n      <td>2</td>\n      <td>−4</td>\n      <td>−4</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Seahorse",
        ),
        "**Skills** Perception +2, Stealth +5<br>\n**Senses** Passive Perception 12<br>\n**Languages** None<br>\n**CR** 0 (XP 0; PB +2)",
    ),
    (
        (
            "Animals",
            "Seahorse",
            "Traits",
        ),
        "### Traits",
    ),
    (
        (
            "Animals",
            "Seahorse",
            "Traits",
        ),
        "**_Water Breathing._** The seahorse can breathe only underwater.",
    ),
    (
        (
            "Animals",
            "Seahorse",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Seahorse",
            "Actions",
        ),
        "**_Bubble Dash._** While underwater, the seahorse moves up to its Swim Speed without provoking Opportunity Attacks.",
    ),
    (
        (
            "Animals",
            "Spider",
        ),
        "## Spider",
    ),
    (
        (
            "Animals",
            "Spider",
        ),
        "_Tiny Beast, Unaligned_",
    ),
    (
        (
            "Animals",
            "Spider",
        ),
        "**AC** 12 **Initiative** +2 (12) <br>\n**HP** 1 (1d4 − 1) <br>\n**Speed** 20 ft., Climb 20 ft. <br>",
    ),
    (
        (
            "Animals",
            "Spider",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>2</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>DEX</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CON</strong></td>\n      <td>8</td>\n      <td>−1</td>\n      <td>−1</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>1</td>\n      <td>−5</td>\n      <td>−5</td>\n      <td><strong>WIS</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CHA</strong></td>\n      <td>2</td>\n      <td>−4</td>\n      <td>−4</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Spider",
        ),
        "**Skills** Stealth +4<br>\n**Senses** Darkvision 30 ft.; Passive Perception 10<br>\n**Languages** None<br>\n**CR** 0 (XP 10; PB +2)",
    ),
    (
        (
            "Animals",
            "Spider",
            "Traits",
        ),
        "### Traits",
    ),
    (
        (
            "Animals",
            "Spider",
            "Traits",
        ),
        "**_Spider Climb._** The spider can climb difficult surfaces, including along ceilings, without needing to make an ability check.",
    ),
    (
        (
            "Animals",
            "Spider",
            "Traits",
        ),
        "**_Web Walker._** The spider ignores movement restrictions caused by webs, and the spider knows the location of any other creature in contact with the same web.",
    ),
    (
        (
            "Animals",
            "Spider",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Spider",
            "Actions",
        ),
        "**_Bite._** _Melee Attack Roll:_ +4, reach 5 ft. _Hit:_ 1 Piercing damage plus 2 (1d4) Poison damage.",
    ),
    (
        (
            "Animals",
            "Swarm of Bats",
        ),
        "## Swarm of Bats",
    ),
    (
        (
            "Animals",
            "Swarm of Bats",
        ),
        "_Large Swarm of Tiny Beasts, Unaligned_",
    ),
    (
        (
            "Animals",
            "Swarm of Bats",
        ),
        "**AC** 12 **Initiative** +2 (12) <br>\n**HP** 11 (2d10) <br>\n**Speed** 5 ft., Fly 30 ft. <br>",
    ),
    (
        (
            "Animals",
            "Swarm of Bats",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>5</td>\n      <td>−3</td>\n      <td>−3</td>\n      <td><strong>DEX</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CON</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>2</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>WIS</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CHA</strong></td>\n      <td>4</td>\n      <td>−3</td>\n      <td>−3</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Swarm of Bats",
        ),
        "**Resistances** Bludgeoning, Piercing, Slashing<br>\n**Immunities** Charmed, Frightened, Grappled, Paralyzed, Petrified, Prone, Restrained, Stunned<br>\n**Senses** Blindsight 60 ft.; Passive Perception 11<br>\n**Languages** None<br>\n**CR** 1/4 (XP 50; PB +2)",
    ),
    (
        (
            "Animals",
            "Swarm of Bats",
            "Traits",
        ),
        "### Traits",
    ),
    (
        (
            "Animals",
            "Swarm of Bats",
            "Traits",
        ),
        "**_Swarm._** The swarm can occupy another creature's space and vice versa, and the swarm can move through any opening large enough for a Tiny bat. The swarm can't regain Hit Points or gain Temporary Hit Points.",
    ),
    (
        (
            "Animals",
            "Swarm of Bats",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Swarm of Bats",
            "Actions",
        ),
        "**_Bites._** _Melee Attack Roll:_ +4, reach 5 ft. _Hit:_ 5 (2d4) Piercing damage, or 2 (1d4) Piercing damage if the swarm is Bloodied.",
    ),
    (
        (
            "Animals",
            "Swarm of Insects",
        ),
        "## Swarm of Insects",
    ),
    (
        (
            "Animals",
            "Swarm of Insects",
        ),
        "_Medium Swarm of Tiny Beasts, Unaligned_",
    ),
    (
        (
            "Animals",
            "Swarm of Insects",
        ),
        "**AC** 11 **Initiative** +1 (11) <br>\n**HP** 19 (3d8 + 6) <br>\n**Speed** 20 ft., Climb or Fly 20 ft. (GM's choice) <br>",
    ),
    (
        (
            "Animals",
            "Swarm of Insects",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>3</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>DEX</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CON</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>1</td>\n      <td>−5</td>\n      <td>−5</td>\n      <td><strong>WIS</strong></td>\n      <td>7</td>\n      <td>−2</td>\n      <td>−2</td>\n      <td><strong>CHA</strong></td>\n      <td>1</td>\n      <td>−5</td>\n      <td>−5</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Swarm of Insects",
        ),
        "**Resistances** Bludgeoning, Piercing, Slashing<br>\n**Immunities** Charmed, Frightened, Grappled, Paralyzed, Petrified, Prone, Restrained, Stunned<br>\n**Senses** Blindsight 30 ft.; Passive Perception 8<br>\n**Languages** None<br>\n**CR** 1/2 (XP 100; PB +2)",
    ),
    (
        (
            "Animals",
            "Swarm of Insects",
            "Traits",
        ),
        "### Traits",
    ),
    (
        (
            "Animals",
            "Swarm of Insects",
            "Traits",
        ),
        "**_Spider Climb._** If the swarm has a Climb Speed, the swarm can climb difficult surfaces, including along ceilings, without needing to make an ability check.",
    ),
    (
        (
            "Animals",
            "Swarm of Insects",
            "Traits",
        ),
        "**_Swarm._** The swarm can occupy another creature's space and vice versa, and the swarm can move through any opening large enough for a Tiny insect. The swarm can't regain Hit Points or gain Temporary Hit Points.",
    ),
    (
        (
            "Animals",
            "Swarm of Insects",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Swarm of Insects",
            "Actions",
        ),
        "**_Bites._** _Melee Attack Roll:_ +3, reach 5 ft. _Hit:_ 6 (2d4 + 1) Poison damage, or 3 (1d4 + 1) Poison damage if the swarm is Bloodied.",
    ),
    (
        (
            "Animals",
            "Swarm of Piranhas",
        ),
        "## Swarm of Piranhas",
    ),
    (
        (
            "Animals",
            "Swarm of Piranhas",
        ),
        "_Medium Swarm of Tiny Beasts, Unaligned_",
    ),
    (
        (
            "Animals",
            "Swarm of Piranhas",
        ),
        "**AC** 13 **Initiative** +3 (13) <br>\n**HP** 28 (8d8 − 8) <br>\n**Speed** 5 ft., Swim 40 ft. <br>",
    ),
    (
        (
            "Animals",
            "Swarm of Piranhas",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>DEX</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>CON</strong></td>\n      <td>9</td>\n      <td>−1</td>\n      <td>−1</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>1</td>\n      <td>−5</td>\n      <td>−5</td>\n      <td><strong>WIS</strong></td>\n      <td>7</td>\n      <td>−2</td>\n      <td>−2</td>\n      <td><strong>CHA</strong></td>\n      <td>2</td>\n      <td>−4</td>\n      <td>−4</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Swarm of Piranhas",
        ),
        "**Resistances** Bludgeoning, Piercing, Slashing<br>\n**Immunities** Charmed, Frightened, Grappled, Paralyzed, Petrified, Prone, Restrained, Stunned<br>\n**Senses** Darkvision 60 ft.; Passive Perception 8<br>\n**Languages** None<br>\n**CR** 1 (XP 200; PB +2)",
    ),
    (
        (
            "Animals",
            "Swarm of Piranhas",
            "Traits",
        ),
        "### Traits",
    ),
    (
        (
            "Animals",
            "Swarm of Piranhas",
            "Traits",
        ),
        "**_Swarm._** The swarm can occupy another creature's space and vice versa, and the swarm can move through any opening large enough for a Tiny piranha. The swarm can't regain Hit Points or gain Temporary Hit Points.",
    ),
    (
        (
            "Animals",
            "Swarm of Piranhas",
            "Traits",
        ),
        "**_Water Breathing._** The swarm can breathe only underwater.",
    ),
    (
        (
            "Animals",
            "Swarm of Piranhas",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Swarm of Piranhas",
            "Actions",
        ),
        "**_Bites._** _Melee Attack Roll:_ +5 (with Advantage if the target doesn't have all its Hit Points), reach 5 ft. _Hit:_ 8 (2d4 + 3) Piercing damage, or 5 (1d4 + 3) Piercing damage if the swarm is Bloodied.",
    ),
    (
        (
            "Animals",
            "Swarm of Rats",
        ),
        "## Swarm of Rats",
    ),
    (
        (
            "Animals",
            "Swarm of Rats",
        ),
        "_Medium Swarm of Tiny Beasts, Unaligned_",
    ),
    (
        (
            "Animals",
            "Swarm of Rats",
        ),
        "**AC** 10 **Initiative** +0 (10) <br>\n**HP** 14 (4d8 − 4) <br>\n**Speed** 30 ft., Climb 30 ft. <br>",
    ),
    (
        (
            "Animals",
            "Swarm of Rats",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>9</td>\n      <td>−1</td>\n      <td>−1</td>\n      <td><strong>DEX</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+2</td>\n      <td><strong>CON</strong></td>\n      <td>9</td>\n      <td>−1</td>\n      <td>−1</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>2</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>WIS</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CHA</strong></td>\n      <td>3</td>\n      <td>−4</td>\n      <td>−4</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Swarm of Rats",
        ),
        "**Resistances** Bludgeoning, Piercing, Slashing<br>\n**Immunities** Charmed, Frightened, Grappled, Paralyzed, Petrified, Prone, Restrained, Stunned<br>\n**Senses** Darkvision 30 ft.; Passive Perception 10<br>\n**Languages** None<br>\n**CR** 1/4 (XP 50; PB +2)",
    ),
    (
        (
            "Animals",
            "Swarm of Rats",
            "Traits",
        ),
        "### Traits",
    ),
    (
        (
            "Animals",
            "Swarm of Rats",
            "Traits",
        ),
        "**_Swarm._** The swarm can occupy another creature's space and vice versa, and the swarm can move through any opening large enough for a Tiny rat. The swarm can't regain Hit Points or gain Temporary Hit Points.",
    ),
    (
        (
            "Animals",
            "Swarm of Rats",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Swarm of Rats",
            "Actions",
        ),
        "**_Bites._** _Melee Attack Roll:_ +2, reach 5 ft. _Hit:_ 5 (2d4) Piercing damage, or 2 (1d4) Piercing damage if the swarm is Bloodied.",
    ),
    (
        (
            "Animals",
            "Swarm of Ravens",
        ),
        "## Swarm of Ravens",
    ),
    (
        (
            "Animals",
            "Swarm of Ravens",
        ),
        "_Medium Swarm of Tiny Beasts, Unaligned_",
    ),
    (
        (
            "Animals",
            "Swarm of Ravens",
        ),
        "**AC** 12 **Initiative** +2 (12) <br>\n**HP** 11 (2d8 + 2) <br>\n**Speed** 10 ft., Fly 50 ft. <br>",
    ),
    (
        (
            "Animals",
            "Swarm of Ravens",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>6</td>\n      <td>−2</td>\n      <td>−2</td>\n      <td><strong>DEX</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CON</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>5</td>\n      <td>−3</td>\n      <td>−3</td>\n      <td><strong>WIS</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CHA</strong></td>\n      <td>6</td>\n      <td>−2</td>\n      <td>−2</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Swarm of Ravens",
        ),
        "**Skills** Perception +5<br>\n**Resistances** Bludgeoning, Piercing, Slashing<br>\n**Immunities** Charmed, Frightened, Grappled, Paralyzed, Petrified, Prone, Restrained, Stunned<br>\n**Senses** Passive Perception 15<br>\n**Languages** None<br>\n**CR** 1/4 (XP 50; PB +2)",
    ),
    (
        (
            "Animals",
            "Swarm of Ravens",
            "Traits",
        ),
        "### Traits",
    ),
    (
        (
            "Animals",
            "Swarm of Ravens",
            "Traits",
        ),
        "**_Swarm._** The swarm can occupy another creature's space and vice versa, and the swarm can move through any opening large enough for a Tiny raven. The swarm can't regain Hit Points or gain Temporary Hit Points.",
    ),
    (
        (
            "Animals",
            "Swarm of Ravens",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Swarm of Ravens",
            "Actions",
        ),
        "**_Beaks._** _Melee Attack Roll:_ +4, reach 5 ft. _Hit:_ 5 (1d6 + 2) Piercing damage, or 2 (1d4) Piercing damage if the swarm is Bloodied.",
    ),
    (
        (
            "Animals",
            "Swarm of Ravens",
            "Actions",
        ),
        "**_Cacophony (Recharge 6)._** _Wisdom Saving Throw:_ DC 10, one creature in the swarm's space. _Failure:_ The target has the Deafened condition until the start of the swarm's next turn. While Deafened, the target also has Disadvantage on ability checks and attack rolls.",
    ),
    (
        (
            "Animals",
            "Swarm of Venomous Snakes",
        ),
        "## Swarm of Venomous Snakes",
    ),
    (
        (
            "Animals",
            "Swarm of Venomous Snakes",
        ),
        "_Medium Swarm of Tiny Beasts, Unaligned_",
    ),
    (
        (
            "Animals",
            "Swarm of Venomous Snakes",
        ),
        "**AC** 14 **Initiative** +4 (14) <br>\n**HP** 36 (8d8) <br>\n**Speed** 30 ft., Swim 30 ft. <br>",
    ),
    (
        (
            "Animals",
            "Swarm of Venomous Snakes",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>8</td>\n      <td>−1</td>\n      <td>−1</td>\n      <td><strong>DEX</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+4</td>\n      <td><strong>CON</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>1</td>\n      <td>−5</td>\n      <td>−5</td>\n      <td><strong>WIS</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CHA</strong></td>\n      <td>3</td>\n      <td>−4</td>\n      <td>−4</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Swarm of Venomous Snakes",
        ),
        "**Resistances** Bludgeoning, Piercing, Slashing<br>\n**Immunities** Charmed, Frightened, Grappled, Paralyzed, Petrified, Prone, Restrained, Stunned<br>\n**Senses** Blindsight 10 ft.; Passive Perception 10<br>\n**Languages** None<br>\n**CR** 2 (XP 450; PB +2)",
    ),
    (
        (
            "Animals",
            "Swarm of Venomous Snakes",
            "Traits",
        ),
        "### Traits",
    ),
    (
        (
            "Animals",
            "Swarm of Venomous Snakes",
            "Traits",
        ),
        "**_Swarm._** The swarm can occupy another creature's space and vice versa, and the swarm can move through any opening large enough for a Tiny snake. The swarm can't regain Hit Points or gain Temporary Hit Points.",
    ),
    (
        (
            "Animals",
            "Swarm of Venomous Snakes",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Swarm of Venomous Snakes",
            "Actions",
        ),
        "**_Bites._** _Melee Attack Roll:_ +6, reach 5 ft. _Hit:_ 8 (1d8 + 4) Piercing damage—or 6 (1d4 + 4) Piercing damage if the swarm is Bloodied—plus 10 (3d6) Poison damage.",
    ),
    (
        (
            "Animals",
            "Tiger",
        ),
        "## Tiger",
    ),
    (
        (
            "Animals",
            "Tiger",
        ),
        "_Large Beast, Unaligned_",
    ),
    (
        (
            "Animals",
            "Tiger",
        ),
        "**AC** 13 **Initiative** +3 (13) <br>\n**HP** 30 (4d10 + 8) <br>\n**Speed** 40 ft. <br>",
    ),
    (
        (
            "Animals",
            "Tiger",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>17</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>DEX</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>CON</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>3</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>WIS</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CHA</strong></td>\n      <td>8</td>\n      <td>−1</td>\n      <td>−1</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Tiger",
        ),
        "**Skills** Perception +3, Stealth +7<br>\n**Senses** Darkvision 60 ft.; Passive Perception 13<br>\n**Languages** None<br>\n**CR** 1 (XP 200; PB +2)",
    ),
    (
        (
            "Animals",
            "Tiger",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Tiger",
            "Actions",
        ),
        "**_Rend._** _Melee Attack Roll:_ +5, reach 5 ft. _Hit:_ 10 (2d6 + 3) Slashing damage. If the target is a Large or smaller creature, it has the Prone condition.",
    ),
    (
        (
            "Animals",
            "Tiger",
            "Bonus Actions",
        ),
        "### Bonus Actions",
    ),
    (
        (
            "Animals",
            "Tiger",
            "Bonus Actions",
        ),
        "**_Nimble Escape._** The tiger takes the Disengage or Hide action.",
    ),
    (
        (
            "Animals",
            "Triceratops",
        ),
        "## Triceratops",
    ),
    (
        (
            "Animals",
            "Triceratops",
        ),
        "_Huge Beast (Dinosaur), Unaligned_",
    ),
    (
        (
            "Animals",
            "Triceratops",
        ),
        "**AC** 14 **Initiative** −1 (9) <br>\n**HP** 114 (12d12 + 36) <br>\n**Speed** 50 ft. <br>",
    ),
    (
        (
            "Animals",
            "Triceratops",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>22</td>\n      <td>+6</td>\n      <td>+6</td>\n      <td><strong>DEX</strong></td>\n      <td>9</td>\n      <td>−1</td>\n      <td>−1</td>\n      <td><strong>CON</strong></td>\n      <td>17</td>\n      <td>+3</td>\n      <td>+3</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>2</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>WIS</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CHA</strong></td>\n      <td>5</td>\n      <td>−3</td>\n      <td>−3</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Triceratops",
        ),
        "**Senses** Passive Perception 10<br>\n**Languages** None<br>\n**CR** 5 (XP 1,800; PB +3)",
    ),
    (
        (
            "Animals",
            "Triceratops",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Triceratops",
            "Actions",
        ),
        "**_Multiattack._** The triceratops makes two Gore attacks.",
    ),
    (
        (
            "Animals",
            "Triceratops",
            "Actions",
        ),
        "**_Gore._** _Melee Attack Roll:_ +9, reach 5 ft. _Hit:_ 19 (2d12 + 6) Piercing damage. If the target is Huge or smaller and the triceratops moved 20+ feet straight toward it immediately before the hit, the target takes an extra 9 (2d8) Piercing damage and has the Prone condition.",
    ),
    (
        (
            "Animals",
            "Tyrannosaurus Rex",
        ),
        "## Tyrannosaurus Rex",
    ),
    (
        (
            "Animals",
            "Tyrannosaurus Rex",
        ),
        "_Huge Beast (Dinosaur), Unaligned_",
    ),
    (
        (
            "Animals",
            "Tyrannosaurus Rex",
        ),
        "**AC** 13 **Initiative** +3 (13) <br>\n**HP** 136 (13d12 + 52) <br>\n**Speed** 50 ft. <br>",
    ),
    (
        (
            "Animals",
            "Tyrannosaurus Rex",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>25</td>\n      <td>+7</td>\n      <td>+10</td>\n      <td><strong>DEX</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CON</strong></td>\n      <td>19</td>\n      <td>+4</td>\n      <td>+4</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>2</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>WIS</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+4</td>\n      <td><strong>CHA</strong></td>\n      <td>9</td>\n      <td>−1</td>\n      <td>−1</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Tyrannosaurus Rex",
        ),
        "**Skills** Perception +4<br>\n**Senses** Passive Perception 14<br>\n**Languages** None<br>\n**CR** 8 (XP 3,900; PB +3)",
    ),
    (
        (
            "Animals",
            "Tyrannosaurus Rex",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Tyrannosaurus Rex",
            "Actions",
        ),
        "**_Multiattack._** The tyrannosaurus makes one Bite attack and one Tail attack.",
    ),
    (
        (
            "Animals",
            "Tyrannosaurus Rex",
            "Actions",
        ),
        "**_Bite._** _Melee Attack Roll:_ +10, reach 10 ft. _Hit:_ 33 (4d12 + 7) Piercing damage. If the target is a Large or smaller creature, it has the Grappled condition (escape DC 17). While Grappled, the target has the Restrained condition and can't be targeted by the tyrannosaurus's Tail.",
    ),
    (
        (
            "Animals",
            "Tyrannosaurus Rex",
            "Actions",
        ),
        "**_Tail._** _Melee Attack Roll:_ +10, reach 15 ft. _Hit:_ 25 (4d8 + 7) Bludgeoning damage. If the target is a Huge or smaller creature, it has the Prone condition.",
    ),
    (
        (
            "Animals",
            "Venomous Snake",
        ),
        "## Venomous Snake",
    ),
    (
        (
            "Animals",
            "Venomous Snake",
        ),
        "_Tiny Beast, Unaligned_",
    ),
    (
        (
            "Animals",
            "Venomous Snake",
        ),
        "**AC** 12 **Initiative** +2 (12) <br>\n**HP** 5 (2d4) <br>\n**Speed** 30 ft., Swim 30 ft. <br>",
    ),
    (
        (
            "Animals",
            "Venomous Snake",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>2</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>DEX</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CON</strong></td>\n      <td>11</td>\n      <td>+0</td>\n      <td>+0</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>1</td>\n      <td>−5</td>\n      <td>−5</td>\n      <td><strong>WIS</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CHA</strong></td>\n      <td>3</td>\n      <td>−4</td>\n      <td>−4</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Venomous Snake",
        ),
        "**Senses** Blindsight 10 ft.; Passive Perception 10<br>\n**Languages** None<br>\n**CR** 1/8 (XP 25; PB +2)",
    ),
    (
        (
            "Animals",
            "Venomous Snake",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Venomous Snake",
            "Actions",
        ),
        "**_Bite._** _Melee Attack Roll:_ +4, reach 5 ft. _Hit:_ 4 (1d4 + 2) Piercing damage plus 3 (1d6) Poison damage.",
    ),
    (
        (
            "Animals",
            "Vulture",
        ),
        "## Vulture",
    ),
    (
        (
            "Animals",
            "Vulture",
        ),
        "_Medium Beast, Unaligned_",
    ),
    (
        (
            "Animals",
            "Vulture",
        ),
        "**AC** 10 **Initiative** +0 (10) <br>\n**HP** 5 (1d8 + 1) <br>\n**Speed** 10 ft., Fly 50 ft. <br>",
    ),
    (
        (
            "Animals",
            "Vulture",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>7</td>\n      <td>−2</td>\n      <td>−2</td>\n      <td><strong>DEX</strong></td>\n      <td>10</td>\n      <td>+0</td>\n      <td>+0</td>\n      <td><strong>CON</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>2</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>WIS</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CHA</strong></td>\n      <td>4</td>\n      <td>−3</td>\n      <td>−3</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Vulture",
        ),
        "**Skills** Perception +3<br>\n**Senses** Passive Perception 13<br>\n**Languages** None<br>\n**CR** 0 (XP 10; PB +2)",
    ),
    (
        (
            "Animals",
            "Vulture",
            "Traits",
        ),
        "### Traits",
    ),
    (
        (
            "Animals",
            "Vulture",
            "Traits",
        ),
        "**_Pack Tactics._** The vulture has Advantage on an attack roll against a creature if at least one of the vulture's allies is within 5 feet of the creature and the ally doesn't have the Incapacitated condition.",
    ),
    (
        (
            "Animals",
            "Vulture",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Vulture",
            "Actions",
        ),
        "**_Beak._** _Melee Attack Roll:_ +2, reach 5 ft. _Hit:_ 2 (1d4) Piercing damage.",
    ),
    (
        (
            "Animals",
            "Warhorse",
        ),
        "## Warhorse",
    ),
    (
        (
            "Animals",
            "Warhorse",
        ),
        "_Large Beast, Unaligned_",
    ),
    (
        (
            "Animals",
            "Warhorse",
        ),
        "**AC** 11 **Initiative** +1 (11) <br>\n**HP** 19 (3d10 + 3) <br>\n**Speed** 60 ft. <br>",
    ),
    (
        (
            "Animals",
            "Warhorse",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>18</td>\n      <td>+4</td>\n      <td>+4</td>\n      <td><strong>DEX</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CON</strong></td>\n      <td>13</td>\n      <td>+1</td>\n      <td>+1</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>2</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>WIS</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+3</td>\n      <td><strong>CHA</strong></td>\n      <td>7</td>\n      <td>−2</td>\n      <td>−2</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Warhorse",
        ),
        "**Senses** Passive Perception 11<br>\n**Languages** None<br>\n**CR** 1/2 (XP 100; PB +2)",
    ),
    (
        (
            "Animals",
            "Warhorse",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Warhorse",
            "Actions",
        ),
        "**_Hooves._** _Melee Attack Roll:_ +6, reach 5 ft. _Hit:_ 9 (2d4 + 4) Bludgeoning damage. If the target is a Large or smaller creature and the horse moved 20+ feet straight toward it immediately before the hit, the target takes an extra 5 (2d4) Bludgeoning damage and has the Prone condition.",
    ),
    (
        (
            "Animals",
            "Weasel",
        ),
        "## Weasel",
    ),
    (
        (
            "Animals",
            "Weasel",
        ),
        "_Tiny Beast, Unaligned_",
    ),
    (
        (
            "Animals",
            "Weasel",
        ),
        "**AC** 13 **Initiative** +3 (13) <br>\n**HP** 1 (1d4 − 1) <br>\n**Speed** 30 ft., Climb 30 ft. <br>",
    ),
    (
        (
            "Animals",
            "Weasel",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>3</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>DEX</strong></td>\n      <td>16</td>\n      <td>+3</td>\n      <td>+3</td>\n      <td><strong>CON</strong></td>\n      <td>8</td>\n      <td>−1</td>\n      <td>−1</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>2</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>WIS</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CHA</strong></td>\n      <td>3</td>\n      <td>−4</td>\n      <td>−4</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Weasel",
        ),
        "**Skills** Acrobatics +5, Perception +3, Stealth +5<br>\n**Senses** Darkvision 60 ft.; Passive Perception 13<br>\n**Languages** None<br>\n**CR** 0 (XP 10; PB +2)",
    ),
    (
        (
            "Animals",
            "Weasel",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Weasel",
            "Actions",
        ),
        "**_Bite._** _Melee Attack Roll:_ +5, reach 5 ft. _Hit:_ 1 Piercing damage.",
    ),
    (
        (
            "Animals",
            "Wolf",
        ),
        "## Wolf",
    ),
    (
        (
            "Animals",
            "Wolf",
        ),
        "_Medium Beast, Unaligned_",
    ),
    (
        (
            "Animals",
            "Wolf",
        ),
        "**AC** 12 **Initiative** +2 (12) <br>\n**HP** 11 (2d8 + 2) <br>\n**Speed** 40 ft. <br>",
    ),
    (
        (
            "Animals",
            "Wolf",
        ),
        "<table>\n  <thead>\n    <tr>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n      <th></th>\n      <th></th>\n      <th>MOD</th>\n      <th>SAVE</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td><strong>STR</strong></td>\n      <td>14</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>DEX</strong></td>\n      <td>15</td>\n      <td>+2</td>\n      <td>+2</td>\n      <td><strong>CON</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n    </tr>\n    <tr>\n      <td><strong>INT</strong></td>\n      <td>3</td>\n      <td>−4</td>\n      <td>−4</td>\n      <td><strong>WIS</strong></td>\n      <td>12</td>\n      <td>+1</td>\n      <td>+1</td>\n      <td><strong>CHA</strong></td>\n      <td>6</td>\n      <td>−2</td>\n      <td>−2</td>\n    </tr>\n  </tbody>\n</table>",
    ),
    (
        (
            "Animals",
            "Wolf",
        ),
        "**Skills** Perception +5, Stealth +4<br>\n**Senses** Darkvision 60 ft.; Passive Perception 15<br>\n**Languages** None<br>\n**CR** 1/4 (XP 50; PB +2)",
    ),
    (
        (
            "Animals",
            "Wolf",
            "Traits",
        ),
        "### Traits",
    ),
    (
        (
            "Animals",
            "Wolf",
            "Traits",
        ),
        "**_Pack Tactics._** The wolf has Advantage on attack rolls against a creature if at least one of the wolf's allies is within 5 feet of the creature and the ally doesn't have the Incapacitated condition.",
    ),
    (
        (
            "Animals",
            "Wolf",
            "Actions",
        ),
        "### Actions",
    ),
    (
        (
            "Animals",
            "Wolf",
            "Actions",
        ),
        "**_Bite._** _Melee Attack Roll:_ +4, reach 5 ft. _Hit:_ 5 (1d6 + 2) Piercing damage. If the target is a Medium or smaller creature, it has the Prone condition.",
    ),
)
