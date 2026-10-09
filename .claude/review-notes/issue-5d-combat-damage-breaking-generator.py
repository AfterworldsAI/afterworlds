# ruff: noqa: E501  -- clause literals are verbatim source text, kept whole to be greppable
"""Author the **combat-damage-breaking** proposal: three whole sections, two entries.

REVIEW MATERIAL for CRD Issue 5d (#137) over the qualified 5c release
``9717e288-c099-5217-b2d2-f89aeabd7b73`` / ``5.2.1-corpus.883aabdf-462``. It
emits an *unaccepted* ``5d-proposal-2`` artifact. It accepts nothing, publishes
nothing, writes nothing under ``oracles/``, and imports no earlier batch's
content, identity or authority: every leaf is read afresh from the release.

Scope, 168 leaves, one review unit per record:

* *Playing the Game > Combat* (90 leaves), ``play.combat``, ``SECTION``;
* *Playing the Game > Damage and Healing* (64), ``play.damage_and_healing``,
  ``SECTION``;
* *Playing the Game > Exploration > Interacting with Objects > Breaking
  Objects* (3), ``play.exploration.breaking_objects``, ``SECTION``. The release
  places the *Marching Order* sidebar in this container by page layout; its
  travel rule is authored whole as the record's ``marching_order`` component,
  never discarded as off-topic;
* *Rules Glossary > Breaking Objects* (9) and *Damage Threshold* (2), the
  latter because Breaking Objects points at it and its rule is what an object's
  threshold means, ``ENTRY`` each.

These close the three targets the accepted batches cite: ``play.combat``,
``play.damage_and_healing`` and ``glossary.breaking_objects``.

This file is literal review data only; the assembly is the committed shared
:mod:`afterworlds.ingestion.mechanical.authoring`. ``CLAUSES`` is the source
review; ``COMPONENTS`` is the representation proposed for it; expected rules
come from ``CLAUSES`` alone.

Authoring conventions (as the six accepted batches), plus one for sections:

* A typed fact is used only where it is true under the conditions the typed
  surface states. A condition the closed vocabulary cannot state stays in the
  same component's governing prose, beside the fact it conditions.
* One source statement, one typed copy. **Restatements of accepted typed
  rules are prose.** The sections reprint rules an accepted glossary record
  already types (Surprise, Difficult Terrain, Resistance, Vulnerability,
  Immunity, ...). Each reprinting is its own exact governing prose, typed
  nothing, and references the accepted record, so the two sites never hold two
  typed copies of one rule. No mechanism shares one component's provenance
  across batches, so the reprinting cannot instead claim the accepted fact.
* Examples, list leads and chapter pointers are supporting spans of the
  component they illustrate. Pointers into this batch's own section ("see the
  next section", "Stabilizing a Character" below) name no reference.
* References: every explicit pointer ("(see "Rules Glossary")", *See also*,
  ``"Actions" earlier in "Playing the Game"``) and each accepted glossary term a
  rule depends on. A pointer to a part with no record yet ("Equipment",
  "Spells", the attack roll's "Playing the Game") is a reference in that part's
  scope with no target, reported unresolved until a real destination exists. Unaccepted glossary terms that are only mentioned (Bloodied,
  Critical Hit, Stable, Death Saving Throw, Teleport, Cover, Bonus Action,
  Reaction) stay unreferenced, as the accepted batches leave terms no accepted
  record defines.

Run: ``python issue-5d-combat-damage-breaking-generator.py <published afterworlds.db>``
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
    AbilityCheckFact,
    AbilityScore,
    AdvantageFact,
    AdvantageState,
    Applicability,
    ApplicabilityKind,
    AutomaticOutcome,
    AutomaticOutcomeFact,
    BenefitOriginSide,
    ConditionEffectFact,
    ConditionEffectKind,
    ConditionKind,
    CoverageThreshold,
    CoverBenefitOriginFact,
    CoverDefense,
    CoverDefensiveBonusFact,
    CoverDegree,
    CoverDegreeCombination,
    CoverDegreeSelection,
    CoverDegreeSelectionFact,
    CoveredInteraction,
    CoverOfferor,
    CoverProvisionFact,
    CoverTargetingProhibitionFact,
    DamageModDirection,
    DamageModificationFact,
    DamageResponseFact,
    DamageResponseKind,
    DamageType,
    DcKind,
    MovementAmount,
    MovementCostFact,
    MovementCostKind,
    ParticipantRole,
    Rational,
    RecordKind,
    RollActor,
    RollContext,
    RollSpec,
    RoundingRule,
    Skill,
    TargetingProhibition,
)
from afterworlds.ingestion.mechanical.schema_lift import (
    SCHEMA_15_HASH,
    SCHEMA_15_VERSION,
)

ORIGIN = "issue-5d-combat-damage-breaking-generator.py"
PROPOSAL_FILE = "issue-5d-combat-damage-breaking-PROPOSAL.json"
PARENT = ("Rules Glossary", "Rules Definitions")
PLAY = "srd-5.2.1/playing-the-game"
#: The parts the damage-dice pointer names, formed from the release's own part
#: names under the ``<release-family>/<section-slug>`` convention ``PLAY`` uses.
EQUIPMENT = "srd-5.2.1/equipment"
SPELLS = "srd-5.2.1/spells"
#: The target of a printed pointer whose destination has no record yet. It is
#: reported as ``unresolved reference`` until a reviewed resolution names one;
#: naming a key here would guess at a record nobody has authored.
UNRESOLVED_TARGET = ""

#: (record slug, printed container label, record kind), in printed order.
ENTRIES: tuple[tuple[str, str, RecordKind], ...] = (
    ("exploration_breaking_objects", "Breaking Objects", RecordKind.GENERAL_RULE),
    ("combat", "Combat", RecordKind.GENERAL_RULE),
    ("damage_and_healing", "Damage and Healing", RecordKind.GENERAL_RULE),
    ("breaking_objects", "Breaking Objects", RecordKind.GLOSSARY_RULE),
    ("damage_threshold", "Damage Threshold", RecordKind.GLOSSARY_RULE),
)

#: The three *Playing the Game* sections. ``play.combat`` and
#: ``play.damage_and_healing`` are the keys the accepted batches already cite.
#: The Exploration subsection has no citing key; it is named by its full path
#: so it cannot collide with a future ``play.exploration``.
PLACEMENTS: dict[str, Placement] = {
    "exploration_breaking_objects": Placement(
        "play.exploration.breaking_objects",
        (
            "Playing the Game",
            "Exploration",
            "Interacting with Objects",
            "Breaking Objects",
        ),
        "#### Breaking Objects",
    ),
    "combat": Placement("play.combat", ("Playing the Game", "Combat"), "## Combat"),
    "damage_and_healing": Placement(
        "play.damage_and_healing",
        ("Playing the Game", "Damage and Healing"),
        "## Damage and Healing",
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
CREATURE_SIZE_TABLE = html_table(
    "Creature Size and Space",
    ("Size", "Space (Feet)", "Space (Squares)"),
    [
        ("Tiny", "2½ by 2½ feet", "4 per square"),
        ("Small", "5 by 5 feet", "1 square"),
        ("Medium", "5 by 5 feet", "1 square"),
        ("Large", "10 by 10 feet", "4 squares (2 by 2)"),
        ("Huge", "15 by 15 feet", "9 squares (3 by 3)"),
        ("Gargantuan", "20 by 20 feet", "16 squares (4 by 4)"),
    ],
)
COVER_TABLE = html_table(
    "Cover",
    ("Degree", "Benefit to Target", "Offered By …"),
    [
        (
            "Half",
            "+2 bonus to AC and Dexterity saving throws",
            "Another creature or an object that covers at least half of the target",
        ),
        (
            "Three-Quarters",
            "+5 bonus to AC and Dexterity saving throws",
            "An object that covers at least three-quarters of the target",
        ),
        (
            "Total",
            "Can't be targeted directly",
            "An object that covers the whole target",
        ),
    ],
)
OBJECT_HIT_POINTS_TABLE = html_table(
    "Object Hit Points",
    ("Size", "Fragile", "Resilient"),
    [
        ("Tiny (bottle, lock)", "2 (1d4)", "5 (2d4)"),
        ("Small (chest, lute)", "3 (1d6)", "10 (3d6)"),
        ("Medium (barrel, chandelier)", "4 (1d8)", "18 (4d8)"),
        ("Large (cart, dining table)", "5 (1d10)", "27 (5d10)"),
    ],
)
#: Written out rather than through ``html_table``: its last row prints one
#: ``colspan`` cell, which the row helper does not render.
OBJECT_ARMOR_CLASS_TABLE = (
    "**Object Armor Class**\n\n<table>\n  <thead>\n    <tr>\n      <th>AC</th>\n"
    "      <th>Substance</th>\n      <th>AC</th>\n      <th>Substance</th>\n"
    "    </tr>\n  </thead>\n  <tbody>\n"
    "    <tr>\n      <td>11</td>\n      <td>Cloth, paper, rope</td>\n"
    "      <td>19</td>\n      <td>Iron, steel</td>\n    </tr>\n"
    "    <tr>\n      <td>13</td>\n      <td>Crystal, glass, ice</td>\n"
    "      <td>21</td>\n      <td>Mithral</td>\n    </tr>\n"
    "    <tr>\n      <td>15</td>\n      <td>Wood</td>\n"
    "      <td>23</td>\n      <td>Adamantine</td>\n    </tr>\n"
    '    <tr>\n      <td>17</td>\n      <td>Stone</td>\n      <td colspan="2"></td>\n'
    "    </tr>\n  </tbody>\n</table>"
)

# ---------------------------------------------------------------------------
# Source review: what each printed clause must be read as
# ---------------------------------------------------------------------------

ATTACK = RollSpec(RollActor.SUBJECT, RollContext.ATTACK_ROLL)

#: (entry, component key, expected fact families + ``None`` for governing
#: prose, clause texts). Every rule-stating sentence of the batch is named here.
CLAUSES: tuple[tuple[str, str, tuple[str | None, ...], tuple[str, ...]], ...] = (
    # == Exploration > Interacting with Objects > Breaking Objects (p12) =====
    (
        "exploration_breaking_objects",
        "fragile_objects",
        (PROSE,),
        (
            "As an action, you can automatically break or otherwise destroy a fragile, nonmagical object, such as a glass container or a piece of paper.",
        ),
    ),
    # The Marching Order sidebar: a travel rule the release places here.
    (
        "exploration_breaking_objects",
        "marching_order",
        (PROSE,),
        (
            "The adventurers should establish a marching order while they travel, whether indoors or outdoors.",
            "A marching order makes it easier to determine which characters are affected by traps, which ones can spot hidden enemies, and which ones are the closest to those enemies if a fight breaks out.",
            "You can change your marching order outside combat and record the order any way you like:",
        ),
    ),
    # == Combat (p13-16) =====================================================
    # -- The Order of Combat --------------------------------------------------
    (
        "combat",
        "rounds_and_turns",
        (PROSE,),
        (
            "The game organizes combat into a cycle of rounds and turns. A round represents about 6 seconds in the game world.",
            "During a round, each participant in a battle takes a turn. The order of turns is determined at the beginning of combat when everyone rolls Initiative. Once everyone has taken a turn, the fight continues to the next round if neither side is defeated.",
        ),
    ),
    (
        "combat",
        "step_by_step",
        (PROSE,),
        (
            "**1: Establish Positions.** The Game Master determines where all the characters and monsters are located. Given the adventurers' marching order or their stated positions in the room or other location, the GM figures out where the adversaries are—how far away and in what direction.",
            "**2: Roll Initiative.** Everyone involved in the combat encounter rolls Initiative, determining the order of combatants' turns.",
            "**3: Take Turns.** Each participant in the battle takes a turn in Initiative order. When everyone involved in the combat has had a turn, the round ends. Repeat this step until the fighting stops.",
        ),
    ),
    (
        "combat",
        "initiative_roll",
        (PROSE,),
        (
            "Initiative determines the order of turns during combat. When combat starts, every participant rolls Initiative; they make a Dexterity check that determines their place in the Initiative order. The GM rolls for monsters. For a group of identical creatures, the GM makes a single roll, so each member of the group has the same Initiative.",
        ),
    ),
    (
        "combat",
        "surprise",
        (PROSE,),
        (
            "**Surprise.** If a combatant is surprised by combat starting, that combatant has Disadvantage on their Initiative roll.",
        ),
    ),
    (
        "combat",
        "initiative_order",
        (PROSE,),
        (
            "**Initiative Order.** A combatant's check total is called their Initiative count, or Initiative for short. The GM ranks the combatants, from highest to lowest Initiative. This is the order in which they act during each round. The Initiative order remains the same from round to round.",
        ),
    ),
    (
        "combat",
        "ties",
        (PROSE,),
        (
            "**Ties.** If a tie occurs, the GM decides the order among tied monsters, and the players decide the order among tied characters. The GM decides the order if the tie is between a monster and a player character.",
        ),
    ),
    (
        "combat",
        "move_and_action",
        (PROSE,),
        (
            "On your turn, you can move a distance up to your Speed and take one action. You decide whether to move first or take your action first.",
        ),
    ),
    (
        "combat",
        "communicating",
        (PROSE,),
        (
            "**Communicating.** You can communicate however you are able—through brief utterances and gestures—as you take your turn. Doing so uses neither your action nor your move.",
            "Extended communication, such as a detailed explanation of something or an attempt to persuade a foe, requires an action. The Influence action is the main way you try to influence a monster.",
        ),
    ),
    (
        "combat",
        "interacting",
        (PROSE,),
        (
            "**Interacting with Things.** You can interact with one object or feature of the environment for free, during either your move or action.",
            "If you want to interact with a second object, you need to take the Utilize action. Some magic items and other special objects always require an action to use, as stated in their descriptions.",
            "The GM might require you to use an action for any of these activities when it needs special care or when it presents an unusual obstacle.",
        ),
    ),
    (
        "combat",
        "grid",
        (PROSE,),
        (
            "If you play using a square grid and miniatures or other tokens, follow these rules.",
            "_Squares._ Each square represents 5 feet.",
            "_Speed._ Rather than moving foot by foot, move square by square on the grid, using your Speed in 5-foot segments. You can translate your Speed into squares by dividing it by 5.",
            "_Entering a Square._ To enter a square, you must have enough movement left to pay for entering. It costs 1 square of movement to enter an unoccupied square that's adjacent to your space (orthogonally or diagonally adjacent). A square of Difficult Terrain costs 2 squares to enter. Other effects might make a square cost even more.",
            "_Corners._ Diagonal movement can't cross the corner of a wall, a large tree, or another terrain feature that fills its space.",
            "_Ranges._ To determine the range on a grid between two things—whether creatures or objects—count squares from a square adjacent to one of them and stop counting in the space of the other one. Count by the shortest route.",
        ),
    ),
    (
        "combat",
        "doing_nothing",
        (PROSE,),
        (
            "_Doing Nothing on Your Turn._ You can forgo moving, taking an action, or doing anything at all on your turn. If you can't decide what to do, consider taking the defensive Dodge action or the Ready action to delay acting.",
        ),
    ),
    (
        "combat",
        "ending_combat",
        (PROSE,),
        (
            "Combat ends when one side or the other is defeated, which can mean the creatures are killed or knocked out or have surrendered or fled. Combat can also end when both sides agree to end it.",
        ),
    ),
    # -- Movement and Position ------------------------------------------------
    (
        "combat",
        "movement",
        (PROSE,),
        (
            "On your turn, you can move a distance equal to your Speed or less. Or you can decide not to move.",
            "However you're moving with your Speed, you deduct the distance of each part of your move from it until it is used up or until you are done moving, whichever comes first.",
        ),
    ),
    (
        "combat",
        "movement_modes",
        (PROSE,),
        (
            'Your movement can include climbing, crawling, jumping, and swimming (each explained in "Rules Glossary"). These different modes of movement can be combined with your regular movement, or they can constitute your entire move.',
        ),
    ),
    (
        "combat",
        "difficult_terrain",
        (PROSE,),
        (
            "Every foot of movement in Difficult Terrain costs 1 extra foot, even if multiple things in a space count as Difficult Terrain.",
        ),
    ),
    (
        "combat",
        "breaking_up_move",
        (PROSE,),
        (
            "You can break up your move, using some of its movement before and after any action, Bonus Action, or Reaction you take on the same turn.",
        ),
    ),
    (
        "combat",
        "dropping_prone",
        (PROSE,),
        (
            'On your turn, you can give yourself the Prone condition (see "Rules Glossary") without using an action or any of your Speed, but you can\'t do so if your Speed is 0.',
        ),
    ),
    (
        "combat",
        "creature_size",
        (PROSE,),
        (
            "A creature belongs to a size category, which determines the width of the square space the creature occupies on a map, as shown on the Creature Size and Space table. That table lists the sizes from smallest (Tiny) to largest (Gargantuan). A creature's space is the area that it effectively controls in combat and the area it needs to fight effectively.",
            CREATURE_SIZE_TABLE,
        ),
    ),
    (
        "combat",
        "moving_around",
        (PROSE,),
        (
            'During your move, you can pass through the space of an ally, a creature that has the Incapacitated condition (see "Rules Glossary"), a Tiny creature, or a creature that is two sizes larger or smaller than you.',
            "Another creature's space is Difficult Terrain for you unless that creature is Tiny or your ally.",
            "You can't willingly end a move in a space occupied by another creature.",
        ),
    ),
    (
        "combat",
        "ending_in_occupied_space",
        ("condition_effect", PROSE),
        (
            'If you somehow end a turn in a space with another creature, you have the Prone condition (see "Rules Glossary") unless you are Tiny or are of a larger size than the other creature.',
        ),
    ),
    # -- Making an Attack -----------------------------------------------------
    (
        "combat",
        "attack_structure",
        (PROSE,),
        (
            "When you take the Attack action, you make an attack. Some other actions, Bonus Actions, and Reactions also let you make an attack. Whether you strike with a Melee weapon, fire a Ranged weapon, or make an attack roll as part of a spell, an attack has the following structure:",
            "**1: Choose a Target.** Pick a target within your attack's range: a creature, an object, or a location.",
            "**2: Determine Modifiers.** The GM determines whether the target has Cover (see the next section) and whether you have Advantage or Disadvantage against the target. In addition, spells, special abilities, and other effects can apply penalties or bonuses to your attack roll.",
            '**3: Resolve the Attack.** Make the attack roll, as detailed earlier in "Playing the Game." On a hit, you roll damage unless the particular attack has rules that specify otherwise. Some attacks cause special effects in addition to or instead of damage.',
        ),
    ),
    (
        "combat",
        "unseen_target",
        ("advantage", PROSE),
        (
            "When you make an attack roll against a target you can't see, you have Disadvantage on the roll. This is true whether you're guessing the target's location or targeting a creature you can hear but not see. If the target isn't in the location you targeted, you miss.",
        ),
    ),
    (
        "combat",
        "unseen_attacker",
        ("advantage", PROSE),
        (
            "When a creature can't see you, you have Advantage on attack rolls against it.",
        ),
    ),
    (
        "combat",
        "hidden_attacker",
        (PROSE,),
        (
            "If you are hidden when you make an attack roll, you give away your location when the attack hits or misses.",
        ),
    ),
    # -- Cover ----------------------------------------------------------------
    (
        "combat",
        "cover_degrees",
        (
            "cover_defensive_bonus",
            "cover_targeting_prohibition",
            "cover_provision",
        ),
        (COVER_TABLE,),
    ),
    (
        "combat",
        "cover_origin",
        ("cover_benefit_origin",),
        (
            "A target can benefit from cover only when an attack or other effect originates on the opposite side of the cover.",
        ),
    ),
    (
        "combat",
        "cover_selection",
        ("cover_degree_selection",),
        (
            "If a target is behind multiple sources of cover, only the most protective degree of cover applies; the degrees aren't added together.",
        ),
    ),
    # -- Ranged and Melee Attacks ---------------------------------------------
    (
        "combat",
        "range",
        (PROSE,),
        (
            "You can make ranged attacks only against targets within a specified range. If a ranged attack, such as one made with a spell, has a single range, you can't attack a target beyond this range.",
            "Some ranged attacks, such as those made with a Longbow, have two ranges. The smaller number is the normal range, and the larger number is the long range.",
        ),
    ),
    (
        "combat",
        "long_range",
        ("advantage", PROSE),
        (
            "Your attack roll has Disadvantage when your target is beyond normal range, and you can't attack a target beyond long range.",
        ),
    ),
    (
        "combat",
        "close_combat",
        ("advantage", PROSE),
        (
            'When you make a ranged attack roll with a weapon, a spell, or some other means, you have Disadvantage on the roll if you are within 5 feet of an enemy who can see you and doesn\'t have the Incapacitated condition (see "Rules Glossary").',
        ),
    ),
    (
        "combat",
        "melee",
        (PROSE,),
        (
            "A melee attack allows you to attack a target within your reach. A melee attack typically uses a handheld weapon or an Unarmed Strike. Many monsters make melee attacks with claws, teeth, or other body parts. A few spells also involve melee attacks.",
        ),
    ),
    (
        "combat",
        "reach",
        (PROSE,),
        (
            "A creature has a 5-foot reach and can thus attack targets within 5 feet when making a melee attack. Certain creatures have melee attacks with a reach greater than 5 feet, as noted in their descriptions.",
        ),
    ),
    (
        "combat",
        "opportunity_attacks",
        (PROSE,),
        (
            "If you move heedlessly past your foes, you put yourself in danger by provoking an Opportunity Attack.",
            "_Avoiding Opportunity Attacks._ You can avoid provoking an Opportunity Attack by taking the Disengage action. You also don't provoke an Opportunity Attack when you Teleport or when you are moved without using your movement, action, Bonus Action, or Reaction.",
            "_Making an Opportunity Attack._ You can make an Opportunity Attack when a creature that you can see leaves your reach. To make the attack, take a Reaction to make one melee attack with a weapon or an Unarmed Strike against that creature. The attack occurs right before it leaves your reach.",
        ),
    ),
    # -- Mounted Combat -------------------------------------------------------
    (
        "combat",
        "mount_eligibility",
        (PROSE,),
        (
            "A willing creature that is at least one size larger than a rider and that has an appropriate anatomy can serve as a mount, using the following rules.",
        ),
    ),
    (
        "combat",
        "mounting",
        ("movement_cost", PROSE),
        (
            "During your move, you can mount a creature that is within 5 feet of you or dismount. Doing so costs an amount of movement equal to half your Speed (round down).",
        ),
    ),
    (
        "combat",
        "controlling_mount",
        (PROSE,),
        (
            "You can control a mount only if it has been trained to accept a rider. Domesticated horses, mules, and similar creatures have such training.",
            "The Initiative of a controlled mount changes to match yours when you mount it. It moves on your turn as you direct it, and it has only three action options during that turn: Dash, Disengage, and Dodge. A controlled mount can move and act even on the turn that you mount it.",
            "In contrast, an independent mount—one that lets you ride but ignores your control—retains its place in the Initiative order and moves and acts as it likes.",
        ),
    ),
    (
        "combat",
        "falling_off",
        ("ability_check", "condition_effect", PROSE),
        (
            'If an effect is about to move your mount against its will while you\'re on it, you must succeed on a DC 10 Dexterity saving throw or fall off, landing with the Prone condition (see "Rules Glossary") in an unoccupied space within 5 feet of the mount.',
            "While mounted, you must make the same save if you're knocked Prone or the mount is.",
        ),
    ),
    # -- Underwater Combat ----------------------------------------------------
    (
        "combat",
        "underwater_melee",
        ("advantage", PROSE),
        (
            "When making a melee attack roll with a weapon underwater, a creature that lacks a Swim Speed has Disadvantage on the attack roll unless the weapon deals Piercing damage.",
        ),
    ),
    (
        "combat",
        "underwater_ranged",
        ("automatic_outcome", "advantage", PROSE),
        (
            "A ranged attack roll with a weapon underwater automatically misses a target beyond the weapon's normal range, and the attack roll has Disadvantage against a target within normal range.",
        ),
    ),
    (
        "combat",
        "underwater_fire",
        ("damage_response", PROSE),
        (
            'Anything underwater has Resistance to Fire damage (explained in "Damage and Healing").',
        ),
    ),
    # == Damage and Healing (p16-18) =========================================
    (
        "damage_and_healing",
        "hit_points",
        (PROSE,),
        (
            "Hit Points represent durability and the will to live. Creatures with more Hit Points are more difficult to kill. Your Hit Point maximum is the number of Hit Points you have when uninjured. Your current Hit Points can be any number from that maximum down to 0, which is the lowest Hit Points can go.",
            "Whenever you take damage, subtract it from your Hit Points. Hit Point loss has no effect on your capabilities until you reach 0 Hit Points.",
        ),
    ),
    (
        "damage_and_healing",
        "bloodied",
        (PROSE,),
        (
            "If you have half your Hit Points or fewer, you're Bloodied, which has no game effect on its own but which might trigger other game effects.",
        ),
    ),
    (
        "damage_and_healing",
        "resting",
        (PROSE,),
        (
            "Any creature can take hour-long Short Rests in the midst of a day and an 8-hour Long Rest to end it. Regaining Hit Points is one of the main benefits of a rest.",
        ),
    ),
    (
        "damage_and_healing",
        "damage_rolls",
        (PROSE,),
        (
            "Each weapon, spell, and damaging monster ability specifies the damage it deals. You roll the damage dice, add any modifiers, and deal the damage to your target. If there's a penalty to the damage, it's possible to deal 0 damage but not negative damage.",
            "When attacking with a weapon, you add your ability modifier—the same modifier used for the attack roll—to the damage roll. A spell tells you which dice to roll for damage and whether to add any modifiers. Unless a rule says otherwise, you don't add your ability modifier to a fixed damage amount that doesn't use a roll, such as the damage of a Blowgun.",
        ),
    ),
    (
        "damage_and_healing",
        "critical_hits",
        (PROSE,),
        (
            "When you score a Critical Hit, you deal extra damage. Roll the attack's damage dice twice, add them together, and add any relevant modifiers as normal.",
            "If the attack involves other damage dice, such as from the Rogue's Sneak Attack feature, you also roll those dice twice.",
        ),
    ),
    (
        "damage_and_healing",
        "multiple_targets",
        (PROSE,),
        (
            "When you create a damaging effect that forces two or more targets to make saving throws against it at the same time, roll the damage once for all the targets.",
        ),
    ),
    (
        "damage_and_healing",
        "half_damage",
        ("damage_modification", PROSE),
        (
            "Many saving throw effects deal half damage (round down) to a target when the target succeeds on the saving throw. The halved damage is equal to half the damage that would be dealt on a failed save.",
        ),
    ),
    (
        "damage_and_healing",
        "damage_types",
        (PROSE,),
        (
            'Each instance of damage has a type, like Fire or Slashing. Damage types are listed in "Rules\nGlossary" and have no rules of their own, but other rules, such as Resistance, rely on damage types.',
        ),
    ),
    (
        "damage_and_healing",
        "resistance_and_vulnerability",
        (PROSE,),
        (
            "Some creatures and objects have Resistance or Vulnerability to certain damage types. If you have Resistance to a damage type, damage of that type is halved against you (round down). If you have Vulnerability to a damage type, damage of that type is doubled against you.",
        ),
    ),
    (
        "damage_and_healing",
        "no_stacking",
        (PROSE,),
        (
            "Multiple instances of Resistance or Vulnerability that affect the same damage type count as only one instance.",
        ),
    ),
    (
        "damage_and_healing",
        "order_of_application",
        (PROSE,),
        (
            "Modifiers to damage are applied in the following order: adjustments such as bonuses, penalties, or multipliers are applied first; Resistance is applied second; and Vulnerability is applied third.",
        ),
    ),
    (
        "damage_and_healing",
        "immunity",
        (PROSE,),
        (
            "Some creatures and objects have Immunity to certain damage types and conditions. Immunity to a damage type means you don't take damage of that type, and Immunity to a condition means you aren't affected by it.",
        ),
    ),
    (
        "damage_and_healing",
        "healing_sources",
        (PROSE,),
        (
            'Hit Points can be restored by magic, such as the _Cure Wounds_ spell or a _Potion of Healing_, or by a Short or Long Rest (see "Rules Glossary").',
        ),
    ),
    (
        "damage_and_healing",
        "knocking_out",
        ("condition_effect", "ability_check", PROSE),
        (
            "When you would reduce a creature to 0 Hit Points with a melee attack, you can instead reduce the creature to 1 Hit Point and give it the Unconscious condition. It then starts a Short Rest, at the end of which that condition ends on it. The condition ends early if the creature regains any Hit Points or if someone takes an action to administer first aid to it, making a successful DC 10 Wisdom (Medicine) check.",
        ),
    ),
    (
        "damage_and_healing",
        "receiving_healing",
        (PROSE,),
        (
            "When you receive healing, add the restored Hit Points to your current Hit Points. Your Hit Points can't exceed your Hit Point maximum, so any Hit Points regained in excess of the maximum are lost.",
        ),
    ),
    (
        "damage_and_healing",
        "monster_death",
        (PROSE,),
        (
            "_Monster Death._ A monster dies the instant it drops to 0 Hit Points, although a Game Master can ignore this rule for an individual monster and treat it like a character.",
        ),
    ),
    (
        "damage_and_healing",
        "hit_point_maximum_of_0",
        (PROSE,),
        (
            "_Hit Point Maximum of 0._ A creature dies if its Hit Point maximum reaches 0. Certain effects drain life energy, reducing a creature's Hit Point maximum.",
        ),
    ),
    (
        "damage_and_healing",
        "massive_damage",
        (PROSE,),
        (
            "_Massive Damage._ When damage reduces a character to 0 Hit Points and damage remains, the character dies if the remainder equals or exceeds their Hit Point maximum.",
        ),
    ),
    (
        "damage_and_healing",
        "character_demise",
        (PROSE,),
        (
            "If your character dies, others might find a magical way to revive your character, such as with the _Raise Dead_ spell. Or talk with the GM about making a new character to join the group.",
        ),
    ),
    (
        "damage_and_healing",
        "falling_unconscious",
        ("condition_effect", PROSE),
        (
            'If you reach 0 Hit Points and don\'t die instantly, you have the Unconscious condition (see "Rules Glossary") until you regain any Hit Points, and you now face making Death Saving Throws (see below).',
        ),
    ),
    (
        "damage_and_healing",
        "death_saving_throws",
        (PROSE,),
        (
            "Whenever you start your turn with 0 Hit Points, you must make a Death Saving Throw to determine whether you creep closer to death or hang on to life. Unlike other saving throws, this one isn't tied to an ability score.",
            '_Three Successes/Failures._ Roll 1d20. If the roll is 10 or higher, you succeed. Otherwise, you fail. A success or failure has no effect by itself. On your third success, you become Stable (see "Stabilizing a Character" below). On your third failure, you die.',
            "The successes and failures don't need to be consecutive; keep track of both until you collect three of a kind. The number of both is reset to zero when you regain any Hit Points or become Stable.",
            "**Rolling a 1 or 20.** When you roll a 1 on the d20 for a Death Saving Throw, you suffer two failures. If you roll a 20 on the d20, you regain 1 Hit Point.",
        ),
    ),
    (
        "damage_and_healing",
        "damage_at_0_hit_points",
        (PROSE,),
        (
            "**Damage at 0 Hit Points.** If you take any damage while you have 0 Hit Points, you suffer a Death Saving Throw failure. If the damage is from a Critical Hit, you suffer two failures instead. If the damage equals or exceeds your Hit Point maximum, you die.",
        ),
    ),
    (
        "damage_and_healing",
        "stabilizing",
        ("ability_check", PROSE),
        (
            "You can take the Help action to try to stabilize a creature with 0 Hit Points, which requires a successful DC 10 Wisdom (Medicine) check.",
        ),
    ),
    (
        "damage_and_healing",
        "stable",
        (PROSE,),
        (
            "A Stable creature doesn't make Death Saving Throws even though it has 0 Hit Points, but it still has the Unconscious condition. If the creature takes damage, it stops being Stable and starts making Death Saving Throws again. A Stable creature that isn't healed regains 1 Hit Point after 1d4 hours.",
        ),
    ),
    (
        "damage_and_healing",
        "temporary_hit_points",
        (PROSE,),
        (
            "Some spells and other effects confer Temporary Hit Points, which are a buffer against losing actual Hit Points, as explained below.",
        ),
    ),
    (
        "damage_and_healing",
        "lost_first",
        (PROSE,),
        (
            "If you have Temporary Hit Points and take damage, those points are lost first, and any leftover damage carries over to your Hit Points.",
        ),
    ),
    (
        "damage_and_healing",
        "duration",
        (PROSE,),
        (
            'Temporary Hit Points last until they\'re depleted or you finish a Long Rest (see "Rules Glossary").',
        ),
    ),
    (
        "damage_and_healing",
        "no_stacking_temporary",
        (PROSE,),
        (
            "Temporary Hit Points can't be added together. If you have Temporary Hit Points and receive more of them, you decide whether to keep the ones you have or to gain the new ones.",
        ),
    ),
    (
        "damage_and_healing",
        "not_hit_points_or_healing",
        (PROSE,),
        (
            "Temporary Hit Points can't be added to your Hit Points, healing can't restore them, and receiving Temporary Hit Points doesn't count as healing. Because Temporary Hit Points aren't Hit Points, a creature can be at full Hit Points and receive Temporary Hit Points.",
            "If you have 0 Hit Points, receiving Temporary Hit Points doesn't restore you to consciousness. Only true healing can save you.",
        ),
    ),
    # == Rules Glossary: Breaking Objects (p177) =============================
    (
        "breaking_objects",
        "harming_objects",
        (PROSE,),
        (
            "Objects can be harmed by attacks and by some spells, using the rules below. If an object is exceedingly fragile, the GM may allow a creature to break it automatically with the Attack or Utilize action.",
        ),
    ),
    (
        "breaking_objects",
        "object_armor_class",
        (PROSE,),
        (
            "_Armor Class._ The Object Armor Class table suggests ACs for various substances.",
            OBJECT_ARMOR_CLASS_TABLE,
        ),
    ),
    (
        "breaking_objects",
        "destroyed_at_0",
        (PROSE,),
        ("_Hit Points._ An object is destroyed when it has 0 Hit Points.",),
    ),
    (
        "breaking_objects",
        "object_hit_points",
        (PROSE,),
        (
            "The Object Hit Points table suggests Hit Points for fragile and resilient objects that are Large or smaller.",
            OBJECT_HIT_POINTS_TABLE,
        ),
    ),
    (
        "breaking_objects",
        "huge_and_gargantuan",
        (PROSE,),
        (
            "To track Hit Points for a Huge or Gargantuan object, divide it into Large or smaller sections, and track each section's Hit Points separately. The GM determines whether destroying part of an object causes the whole thing to collapse.",
        ),
    ),
    (
        "breaking_objects",
        "object_immunities",
        ("damage_response", PROSE),
        (
            "_Damage Types and Objects._ Objects have Immunity to Poison and Psychic damage.",
        ),
    ),
    (
        "breaking_objects",
        "damage_type_effectiveness",
        (PROSE,),
        (
            "The GM might decide that some damage types are more or less effective against an object.",
            "Paper or cloth objects might have Vulnerability to Fire damage.",
        ),
    ),
    (
        "breaking_objects",
        "object_damage_threshold",
        (PROSE,),
        (
            "_Damage Threshold._ Big objects, such as castle walls, often have extra resilience represented by a damage threshold.",
        ),
    ),
    (
        "breaking_objects",
        "no_ability_scores",
        ("automatic_outcome", PROSE),
        (
            "_No Ability Scores._ An object lacks ability scores unless a rule assigns scores to the object. Without ability scores, an object can't make ability checks, and it fails all saving throws.",
        ),
    ),
    # == Rules Glossary: Damage Threshold (p180) =============================
    (
        "damage_threshold",
        "threshold",
        (PROSE,),
        (
            "A creature or an object that has a damage threshold has Immunity to all damage unless it takes an amount of damage from a single attack or effect equal to or greater than its damage threshold, in which case it takes that entire instance of damage. Any damage that fails to meet or exceed the damage threshold is superficial and doesn't reduce Hit Points.",
        ),
    ),
)

#: (entry, leaf prefix): whole leaves that introduce the rules after them and
#: state none of their own.
FRAMING: tuple[tuple[str, str], ...] = (
    ("combat", "Adventurers encounter many dangerous monsters"),
    ("combat", "When you make a ranged attack, you fire a bow"),
    ("combat", "A fight underwater follows these rules."),
    ("damage_and_healing", "Injury and death are frequent threats"),
    ("damage_and_healing", "Damage dealt via saving throws uses these rules."),
    ("damage_and_healing", "When a creature drops to 0 Hit Points, it either dies"),
    ("damage_and_healing", "Here are the main ways a creature can die instantly."),
)

SUBSECTION_HEADING = "subsection heading: names a subsection and states no rule"

#: (entry, exact leaf contents, reason): whole leaves that only name a
#: subsection. Only headings are excluded; a rule printed off its record's
#: topic is still authored (see ``marching_order``).
EXCLUDED: tuple[tuple[str, tuple[str, ...], str], ...] = (
    (
        "combat",
        (
            "### The Order of Combat",
            "#### Combat Step by Step",
            "#### Initiative",
            "#### Your Turn",
            "#### Ending Combat",
            "### Movement and Position",
            "#### Difficult Terrain",
            "#### Breaking Up Your Move",
            "#### Dropping Prone",
            "#### Creature Size",
            "#### Moving around Other Creatures",
            "### Making an Attack",
            "### Cover",
            "### Ranged Attacks",
            "#### Range",
            "#### Ranged Attacks in Close Combat",
            "### Melee Attacks",
            "#### Reach",
            "#### Opportunity Attacks",
            "### Mounted Combat",
            "#### Mounting and Dismounting",
            "#### Controlling a Mount",
            "#### Falling Off",
            "### Underwater Combat",
            "#### Impeded Weapons",
            "#### Fire Resistance",
        ),
        SUBSECTION_HEADING,
    ),
    (
        "damage_and_healing",
        (
            "### Hit Points",
            "### Damage Rolls",
            "### Critical Hits",
            "### Saving Throws and Damage",
            "#### Damage against Multiple Targets",
            "#### Half Damage",
            "### Damage Types",
            "### Resistance and Vulnerability",
            "#### No Stacking",
            "#### Order of Application",
            "### Immunity",
            "### Healing",
            "### Dropping to 0 Hit Points",
            "#### Instant Death",
            "#### Character Demise",
            "#### Falling Unconscious",
            "#### Death Saving Throws",
            "#### Stabilizing a Character",
            "### Temporary Hit Points",
            "#### Lose Temporary Hit Points First",
            "#### Duration",
            "#### They Don't Stack",
            "#### They're Not Hit Points or Healing",
        ),
        SUBSECTION_HEADING,
    ),
)

# ---------------------------------------------------------------------------
# Representation proposed for the clauses above
# ---------------------------------------------------------------------------

C = EntryComponent


def on(outcome: AutomaticOutcome) -> Applicability:
    return Applicability(kind=ApplicabilityKind.ROLL_OUTCOME, outcome=outcome)


def dc10(
    ability: AbilityScore, context: RollContext, skill: Skill | None = None
) -> AbilityCheckFact:
    return AbilityCheckFact(
        ability, DcKind.FIXED, context=context, dc_value=10, skill=skill
    )


def disadvantage() -> AdvantageFact:
    return AdvantageFact(AdvantageState.DISADVANTAGE, ATTACK)


PRONE = ConditionEffectFact(ConditionKind.PRONE, ConditionEffectKind.APPLIES)
UNCONSCIOUS = ConditionEffectFact(
    ConditionKind.UNCONSCIOUS, ConditionEffectKind.APPLIES
)
HALF_DAMAGE = DamageModificationFact(
    DamageModDirection.REDUCE, Rational(1, 2), rounding=RoundingRule.DOWN
)
MEDICINE_DC10 = dc10(AbilityScore.WISDOM, RollContext.ABILITY_CHECK, Skill.MEDICINE)

#: The two out-of-glossary destinations this batch defines.
PLAY_COMBAT = (PLAY, "play.combat")
PLAY_DAMAGE_AND_HEALING = (PLAY, "play.damage_and_healing")

COMPONENTS: tuple[EntryComponent, ...] = (
    # == Exploration > Breaking Objects =====================================
    # Which objects are "fragile" is judged against the fiction.
    C("exploration_breaking_objects", "fragile_objects", P, CTX),
    # How the party orders itself for travel has no typed family. The sidebar
    # prints no pointer, so it names no reference.
    C("exploration_breaking_objects", "marching_order", P, NO_USE),
    # == Combat =============================================================
    # The round/turn cycle and its roughly 6 seconds have no typed family.
    C(
        "combat",
        "rounds_and_turns",
        P,
        NO_USE,
        refs=(("Initiative", "initiative"),),
    ),
    # The GM places everyone from the fiction; steps 2 and 3 restate the
    # Initiative rules below.
    C("combat", "step_by_step", P, GM),
    # A Dexterity check with no DC: AbilityCheckFact types a DC source and there
    # is none. Restates and extends the accepted Initiative definition.
    C(
        "combat",
        "initiative_roll",
        P,
        NO_USE,
        refs=(("Initiative", "initiative"),),
    ),
    # Restates the accepted glossary Surprise, which types this Disadvantage.
    C("combat", "surprise", P, CTX, refs=(("Surprise", "surprise"),)),
    C("combat", "initiative_order", P, NO_USE),
    C("combat", "ties", P, GM),
    C("combat", "move_and_action", P, NO_USE, refs=(("Speed", "speed"),)),
    C(
        "combat",
        "communicating",
        P,
        CTX,
        refs=(("Influence", "influence"),),
    ),
    C("combat", "interacting", P, GM, refs=(("Utilize", "utilize"),)),
    # The grid is optional ("If you play using a square grid"); its squares,
    # costs and counting rules are one prose unit under that condition.
    C(
        "combat",
        "grid",
        P,
        CTX,
        refs=(("Speed", "speed"), ("Difficult Terrain", "difficult_terrain")),
    ),
    C(
        "combat",
        "doing_nothing",
        P,
        NO_USE,
        refs=(("Dodge", "dodge"), ("Ready", "ready")),
    ),
    C("combat", "ending_combat", P, CTX),
    C("combat", "movement", P, NO_USE, refs=(("Speed", "speed"),)),
    C(
        "combat",
        "movement_modes",
        P,
        NO_USE,
        refs=(
            ("climbing", "climbing"),
            ("crawling", "crawling"),
            ("jumping", "jumping"),
            ("swimming", "swimming"),
        ),
    ),
    # Restates the accepted Difficult Terrain surcharge, which is typed there.
    C(
        "combat",
        "difficult_terrain",
        P,
        NO_USE,
        refs=(("Difficult Terrain", "difficult_terrain"),),
    ),
    C("combat", "breaking_up_move", P, NO_USE),
    C("combat", "dropping_prone", P, NO_USE, refs=(("Prone", "prone"),)),
    # SizeKeyedQuantityFact keys a required quantity over a time period; a
    # space is neither, so the table is exact prose.
    C("combat", "creature_size", P, NO_USE),
    C(
        "combat",
        "moving_around",
        P,
        NO_USE,
        refs=(
            ("Incapacitated", "incapacitated"),
            ("Difficult Terrain", "difficult_terrain"),
        ),
    ),
    # Prone is typed; the trigger and the size exception stay its prose.
    C(
        "combat",
        "ending_in_occupied_space",
        M,
        NO_USE,
        facts=(PRONE,),
        refs=(("Prone", "prone"),),
    ),
    C(
        "combat",
        "attack_structure",
        P,
        GM,
        refs=(
            ("Attack", "attack"),
            ("Playing the Game", (PLAY, UNRESOLVED_TARGET)),
        ),
    ),
    # Disadvantage on your own attack roll is typed; "a target you can't see"
    # has no applicability kind and stays beside it, as does the miss.
    C("combat", "unseen_target", M, CTX, facts=(disadvantage(),)),
    C(
        "combat",
        "unseen_attacker",
        M,
        CTX,
        facts=(AdvantageFact(AdvantageState.ADVANTAGE, ATTACK),),
    ),
    C("combat", "hidden_attacker", P, CTX),
    # Cover. These families were designed from exactly this table: a bonus per
    # degree, Total's prohibition, and one provision per row.
    C(
        "combat",
        "cover_degrees",
        S,
        None,
        facts=(
            CoverDefensiveBonusFact(
                CoverDegree.HALF, 2, CoverDefense.ARMOR_CLASS, AbilityScore.DEXTERITY
            ),
            CoverDefensiveBonusFact(
                CoverDegree.THREE_QUARTERS,
                5,
                CoverDefense.ARMOR_CLASS,
                AbilityScore.DEXTERITY,
            ),
            CoverTargetingProhibitionFact(
                CoverDegree.TOTAL, TargetingProhibition.DIRECT_TARGETING
            ),
            CoverProvisionFact(
                CoverDegree.HALF,
                CoverOfferor.ANOTHER_CREATURE_OR_AN_OBJECT,
                CoverageThreshold.AT_LEAST_HALF,
            ),
            CoverProvisionFact(
                CoverDegree.THREE_QUARTERS,
                CoverOfferor.AN_OBJECT,
                CoverageThreshold.AT_LEAST_THREE_QUARTERS,
            ),
            CoverProvisionFact(
                CoverDegree.TOTAL,
                CoverOfferor.AN_OBJECT,
                CoverageThreshold.WHOLE_TARGET,
            ),
        ),
    ),
    C(
        "combat",
        "cover_origin",
        S,
        None,
        facts=(
            CoverBenefitOriginFact(
                CoveredInteraction.AN_ATTACK_OR_OTHER_EFFECT,
                BenefitOriginSide.OPPOSITE_SIDE_OF_THE_COVER,
            ),
        ),
    ),
    C(
        "combat",
        "cover_selection",
        S,
        None,
        facts=(
            CoverDegreeSelectionFact(
                CoverDegreeSelection.MOST_PROTECTIVE,
                CoverDegreeCombination.NOT_ADDED_TOGETHER,
            ),
        ),
    ),
    C("combat", "range", P, NO_USE),
    # "beyond normal range" has no applicability kind; the prohibition beyond
    # long range is not an automatic roll outcome (no roll is made).
    C("combat", "long_range", M, NO_USE, facts=(disadvantage(),)),
    C(
        "combat",
        "close_combat",
        M,
        CTX,
        facts=(disadvantage(),),
        refs=(("Incapacitated", "incapacitated"),),
    ),
    C(
        "combat",
        "melee",
        P,
        NO_USE,
        refs=(("Unarmed Strike", "unarmed_strike"),),
    ),
    # Restates the accepted Reach default.
    C("combat", "reach", P, NO_USE, refs=(("reach", "reach"),)),
    # Restates and details the accepted Opportunity Attacks entry.
    C(
        "combat",
        "opportunity_attacks",
        P,
        NO_USE,
        refs=(
            ("Opportunity Attack", "opportunity_attacks"),
            ("Disengage", "disengage"),
            ("Unarmed Strike", "unarmed_strike"),
        ),
    ),
    # "appropriate anatomy" is judged against the fiction.
    C("combat", "mount_eligibility", P, CTX),
    # MovementCostFact names this wording as its HALF_SPEED precedent.
    C(
        "combat",
        "mounting",
        M,
        NO_USE,
        facts=(
            MovementCostFact(
                MovementCostKind.EXPENDITURE,
                MovementAmount.HALF_SPEED,
                payer=ParticipantRole.SUBJECT,
                rounding=RoundingRule.DOWN,
            ),
        ),
    ),
    C(
        "combat",
        "controlling_mount",
        P,
        CTX,
        refs=(
            ("Initiative", "initiative"),
            ("Dash", "dash"),
            ("Disengage", "disengage"),
            ("Dodge", "dodge"),
        ),
    ),
    # The save and the Prone landing on its failure are typed, as the accepted
    # Long Jump landing; the triggers and the landing space stay prose.
    C(
        "combat",
        "falling_off",
        M,
        CTX,
        facts=(dc10(AbilityScore.DEXTERITY, RollContext.SAVING_THROW), PRONE),
        qualifiers=((PRONE, on(AutomaticOutcome.FAILURE)),),
        refs=(("Prone", "prone"),),
    ),
    C(
        "combat",
        "underwater_melee",
        M,
        CTX,
        facts=(disadvantage(),),
        refs=(("Swim Speed", "swim_speed"),),
    ),
    # Two outcomes under two range conditions, both kept in the prose.
    C(
        "combat",
        "underwater_ranged",
        M,
        CTX,
        facts=(
            AutomaticOutcomeFact(ATTACK, AutomaticOutcome.FAILURE),
            disadvantage(),
        ),
    ),
    C(
        "combat",
        "underwater_fire",
        M,
        CTX,
        facts=(
            DamageResponseFact(
                DamageResponseKind.RESISTANCE, damage_type=DamageType.FIRE
            ),
        ),
        refs=(
            ("Resistance", "resistance"),
            ("Damage and Healing", PLAY_DAMAGE_AND_HEALING),
        ),
    ),
    # == Damage and Healing ==================================================
    # Restates the accepted Hit Points bounds and loss; no tracked quantity.
    C(
        "damage_and_healing",
        "hit_points",
        P,
        NO_USE,
        refs=(("Hit Points", "hit_points"),),
    ),
    C("damage_and_healing", "bloodied", P, NO_USE),
    C(
        "damage_and_healing",
        "resting",
        P,
        NO_USE,
        refs=(("Short Rest", "short_rest"), ("Long Rest", "long_rest")),
    ),
    C("damage_and_healing", "damage_rolls", P, NO_USE),
    # CriticalHitRuleFact states when a roll is a Critical Hit, not what one
    # deals; doubling dice has no family.
    C("damage_and_healing", "critical_hits", P, NO_USE),
    C("damage_and_healing", "multiple_targets", P, NO_USE),
    # The halving and its rounding are typed. The successful save it follows
    # stays prose: a roll-outcome qualifier needs a roll fact in scope, and the
    # save belongs to each effect; "Many saving throw effects" leaves which.
    C("damage_and_healing", "half_damage", M, CTX, facts=(HALF_DAMAGE,)),
    C(
        "damage_and_healing",
        "damage_types",
        P,
        NO_USE,
        refs=(("Damage types", "damage_types"), ("Resistance", "resistance")),
    ),
    # Restates the accepted Resistance and Vulnerability, which type these.
    C(
        "damage_and_healing",
        "resistance_and_vulnerability",
        P,
        NO_USE,
        refs=(("Resistance", "resistance"), ("Vulnerability", "vulnerability")),
    ),
    C("damage_and_healing", "no_stacking", P, NO_USE),
    C("damage_and_healing", "order_of_application", P, NO_USE),
    C(
        "damage_and_healing",
        "immunity",
        P,
        NO_USE,
        refs=(("Immunity", "immunity"),),
    ),
    C(
        "damage_and_healing",
        "healing_sources",
        P,
        CTX,
        refs=(("Short", "short_rest"), ("Long Rest", "long_rest")),
    ),
    # Unconscious and the first-aid check are typed; the melee trigger, the
    # 1 Hit Point and the Short Rest ending stay prose.
    C(
        "damage_and_healing",
        "knocking_out",
        M,
        NO_USE,
        facts=(UNCONSCIOUS, MEDICINE_DC10),
        refs=(("Unconscious", "unconscious"),),
    ),
    C("damage_and_healing", "receiving_healing", P, NO_USE),
    C("damage_and_healing", "monster_death", P, GM),
    C("damage_and_healing", "hit_point_maximum_of_0", P, NO_USE),
    C("damage_and_healing", "massive_damage", P, NO_USE),
    C("damage_and_healing", "character_demise", P, GM),
    C(
        "damage_and_healing",
        "falling_unconscious",
        M,
        NO_USE,
        facts=(UNCONSCIOUS,),
        refs=(("Unconscious", "unconscious"),),
    ),
    # A d20 with no ability, success on 10+ and three-of-a-kind tracking: no
    # family states a save that is not an ability's save.
    C("damage_and_healing", "death_saving_throws", P, NO_USE),
    C("damage_and_healing", "damage_at_0_hit_points", P, NO_USE),
    C(
        "damage_and_healing",
        "stabilizing",
        M,
        NO_USE,
        facts=(MEDICINE_DC10,),
        refs=(("Help", "help"),),
    ),
    C(
        "damage_and_healing",
        "stable",
        P,
        NO_USE,
        refs=(("Unconscious", "unconscious"),),
    ),
    C(
        "damage_and_healing",
        "temporary_hit_points",
        P,
        CTX,
        refs=(("Temporary Hit Points", "temporary_hit_points"),),
    ),
    C("damage_and_healing", "lost_first", P, NO_USE),
    C(
        "damage_and_healing",
        "duration",
        P,
        NO_USE,
        refs=(("Long Rest", "long_rest"),),
    ),
    C("damage_and_healing", "no_stacking_temporary", P, NO_USE),
    C("damage_and_healing", "not_hit_points_or_healing", P, NO_USE),
    # == Rules Glossary: Breaking Objects ===================================
    C(
        "breaking_objects",
        "harming_objects",
        P,
        GM,
        refs=(("Attack", "attack"), ("Utilize", "utilize")),
    ),
    # Both tables "suggest": the GM chooses, so neither is typed authority.
    C("breaking_objects", "object_armor_class", P, GM),
    C(
        "breaking_objects",
        "destroyed_at_0",
        P,
        NO_USE,
        refs=(("Hit Points", "hit_points"),),
    ),
    C("breaking_objects", "object_hit_points", P, GM),
    C("breaking_objects", "huge_and_gargantuan", P, GM),
    # Both immunities are typed; "Objects" as the subject stays the prose.
    C(
        "breaking_objects",
        "object_immunities",
        M,
        NO_USE,
        facts=(
            DamageResponseFact(
                DamageResponseKind.IMMUNITY, damage_type=DamageType.POISON
            ),
            DamageResponseFact(
                DamageResponseKind.IMMUNITY, damage_type=DamageType.PSYCHIC
            ),
        ),
        refs=(("Immunity", "immunity"),),
    ),
    C(
        "breaking_objects",
        "damage_type_effectiveness",
        P,
        GM,
        refs=(("Vulnerability", "vulnerability"),),
    ),
    C("breaking_objects", "object_damage_threshold", P, CTX),
    # Automatic failure of every saving throw is typed; "unless a rule assigns
    # scores" and the no-checks rule stay prose.
    C(
        "breaking_objects",
        "no_ability_scores",
        M,
        NO_USE,
        facts=(
            AutomaticOutcomeFact(
                RollSpec(RollActor.SUBJECT, RollContext.SAVING_THROW),
                AutomaticOutcome.FAILURE,
            ),
        ),
    ),
    # == Rules Glossary: Damage Threshold ===================================
    # No family states a threshold below which damage is nullified.
    C(
        "damage_threshold",
        "threshold",
        P,
        NO_USE,
        refs=(("Immunity", "immunity"), ("Hit Points", "hit_points")),
    ),
)

ACTIONS_POINTER = 'The main actions you can take are listed in "Actions" earlier in "Playing the Game."'
SPEED_POINTER = 'See "Rules Glossary" for more about Speed as well as about special speeds, such as a Climb Speed, Fly Speed, or Swim Speed.'
RESTS_POINTER = '"Rules Glossary" provides the rules for Short and Long Rests.'
DEAD_POINTER = '"Rules Glossary" has more information on being dead.'
BREAKING_POINTER = 'If you try to damage something more resilient, the GM might use the rules on breaking objects in "Rules Glossary."'
DICE_POINTER = (
    'See "Equipment" for weapons\' damage dice and "Spells" for spells\' damage dice.'
)
THRESHOLD_SEE_ALSO = '_See also_ "Damage Threshold."'

#: Supporting spans: (entry, text, component supported or ``None`` for the
#: record). Examples illustrate; leads, sidebar titles and chapter pointers
#: identify or scope.
SUPPORTING: tuple[tuple[str, str, str | None], ...] = (
    ("exploration_breaking_objects", BREAKING_POINTER, None),
    ("exploration_breaking_objects", "**Marching Order**", "marching_order"),
    (
        "exploration_breaking_objects",
        "write it down, for example, or arrange miniatures to show it.",
        "marching_order",
    ),
    # -- Combat ---------------------------------------------------------------
    (
        "combat",
        "A typical combat encounter is a clash between two sides: a flurry of weapon swings, feints, parries, footwork, and spellcasting.",
        "rounds_and_turns",
    ),
    ("combat", "Combat unfolds in these steps:", "step_by_step"),
    (
        "combat",
        "For example, if an ambusher starts combat while hidden from a foe who is unaware that combat is starting, that foe is surprised.",
        "surprise",
    ),
    ("combat", ACTIONS_POINTER, None),
    (
        "combat",
        "A character's features and a monster's stat block also provide action options.",
        "move_and_action",
    ),
    (
        "combat",
        '"Movement and Position" later in "Playing the Game" gives the rules for movement.',
        "move_and_action",
    ),
    (
        "combat",
        "For example, you could open a door during your move as you stride toward a foe.",
        "interacting",
    ),
    (
        "combat",
        "For instance, the GM might require you to take the Utilize action to open a stuck door or turn a crank to lower a drawbridge.",
        "interacting",
    ),
    ("combat", "**Playing on a Grid**", "grid"),
    ("combat", "For example, a Speed of 30 feet translates into 6 squares.", "grid"),
    (
        "combat",
        "If you use a grid often, consider writing your Speed in squares on your character sheet.",
        "grid",
    ),
    (
        "combat",
        "A character's Speed is determined during character creation. A monster's Speed is noted in the monster's stat block.",
        "movement",
    ),
    ("combat", SPEED_POINTER, None),
    (
        "combat",
        "Combatants are often slowed down by Difficult Terrain. Low furniture, rubble, undergrowth, steep stairs, snow, and shallow bogs are examples of Difficult Terrain.",
        "difficult_terrain",
    ),
    (
        "combat",
        "For example, if you have a Speed of 30 feet, you could go 10 feet, take an action, and then go 20 feet.",
        "breaking_up_move",
    ),
    (
        "combat",
        "A character's size is determined by species, and a monster's size is specified in the monster's stat block.",
        "creature_size",
    ),
    ("combat", "**Unseen Attackers and Targets**", "unseen_target"),
    (
        "combat",
        "Walls, trees, creatures, and other obstacles can provide cover, making a target more difficult to harm. As detailed in the Cover table, there are three degrees of cover, each of which gives a different benefit to a target.",
        "cover_degrees",
    ),
    (
        "combat",
        "For example, if a target is behind a creature that gives Half Cover and a tree trunk that gives Three-Quarters Cover, the target has Three-Quarters Cover.",
        "cover_selection",
    ),
    (
        "combat",
        "Aiming a ranged attack is more difficult when a foe is next to you.",
        "close_combat",
    ),
    (
        "combat",
        "Combatants watch for enemies to drop their guard.",
        "opportunity_attacks",
    ),
    (
        "combat",
        "For example, you don't provoke an Opportunity Attack if an explosion hurls you out of a foe's reach or if you fall past an enemy.",
        "opportunity_attacks",
    ),
    (
        "combat",
        "For example, if your Speed is 30 feet, you spend 15 feet of movement to mount a horse.",
        "mounting",
    ),
    # -- Damage and Healing ---------------------------------------------------
    ("damage_and_healing", "**RESTING**", "resting"),
    (
        "damage_and_healing",
        "Adventurers can't spend every hour adventuring. They need rest.",
        "resting",
    ),
    ("damage_and_healing", RESTS_POINTER, None),
    ("damage_and_healing", DICE_POINTER, "damage_rolls"),
    (
        "damage_and_healing",
        "For example, if you score a Critical Hit with a Dagger, roll 2d4 for the damage rather than 1d4, and add your relevant ability modifier.",
        "critical_hits",
    ),
    (
        "damage_and_healing",
        "For example, when a wizard casts _Fireball_, the spell's damage is rolled once for all creatures caught in the blast.",
        "multiple_targets",
    ),
    (
        "damage_and_healing",
        "For example, if you have Resistance to Cold damage, such damage is halved against you, and if you have Vulnerability to Fire damage, such damage is doubled against you.",
        "resistance_and_vulnerability",
    ),
    (
        "damage_and_healing",
        "For example, if you have Resistance to Necrotic damage as well as Resistance to all damage, Necrotic damage is reduced by half against you.",
        "no_stacking",
    ),
    (
        "damage_and_healing",
        "For example, a creature has Resistance to all damage and Vulnerability to Fire damage, and it's within a magical aura that reduces all damage by 5. If it takes 28 Fire damage, the damage is first reduced by 5 (to 23), then halved for the creature's Resistance (and rounded down to 11), then doubled for its Vulnerability (to 22).",
        "order_of_application",
    ),
    ("damage_and_healing", "**Knocking Out a Creature**", "knocking_out"),
    (
        "damage_and_healing",
        "For example, if you receive 8 Hit Points of healing and have 14 Hit Points and a Hit Point maximum of 20, you regain 6 Hit Points, not 8.",
        "receiving_healing",
    ),
    (
        "damage_and_healing",
        "For example, if your character has a Hit Point maximum of 12, currently has 6 Hit Points, and takes 18 damage, the character drops to 0 Hit Points, but 12 damage remains. The character then dies, since 12 equals their Hit Point maximum.",
        "massive_damage",
    ),
    ("damage_and_healing", DEAD_POINTER, None),
    ("damage_and_healing", "You're in the hands of fate now.", "death_saving_throws"),
    (
        "damage_and_healing",
        "For example, if you have 5 Temporary Hit Points and take 7 damage, you lose those points and then lose 2 Hit Points.",
        "lost_first",
    ),
    (
        "damage_and_healing",
        "For example, if a spell grants you 12 Temporary Hit Points when you already have 10, you can have 12 or 10, not 22.",
        "no_stacking_temporary",
    ),
    # -- Rules Glossary -------------------------------------------------------
    (
        "breaking_objects",
        "For example, Bludgeoning damage works well for smashing things but not for cutting.",
        "damage_type_effectiveness",
    ),
    ("breaking_objects", THRESHOLD_SEE_ALSO, None),
    (
        "damage_threshold",
        "For example, if an object has a damage threshold of 10, the object takes no damage if 9 damage is dealt to it, since that damage fails to exceed the threshold. If the same object is dealt 11 damage, it takes all of that damage.",
        "threshold",
    ),
)

#: Record-owned references: (entry, printed text, target, texts of the spans the
#: pointer is read from).
RECORD_REFERENCES: tuple[RecordReference, ...] = (
    (
        "exploration_breaking_objects",
        "breaking objects",
        "breaking_objects",
        (BREAKING_POINTER,),
    ),
    ("combat", "Actions", (PLAY, "play.actions"), (ACTIONS_POINTER,)),
    ("combat", "Speed", "speed", (SPEED_POINTER,)),
    ("combat", "Climb Speed", "climb_speed", (SPEED_POINTER,)),
    ("combat", "Fly Speed", "fly_speed", (SPEED_POINTER,)),
    ("combat", "Swim Speed", "swim_speed", (SPEED_POINTER,)),
    ("damage_and_healing", "Short", "short_rest", (RESTS_POINTER,)),
    ("damage_and_healing", "Long Rests", "long_rest", (RESTS_POINTER,)),
    ("damage_and_healing", "dead", "dead", (DEAD_POINTER,)),
    (
        "damage_and_healing",
        "Equipment",
        (EQUIPMENT, UNRESOLVED_TARGET),
        (DICE_POINTER,),
    ),
    ("damage_and_healing", "Spells", (SPELLS, UNRESOLVED_TARGET), (DICE_POINTER,)),
    ("breaking_objects", "Damage Threshold", "damage_threshold", (THRESHOLD_SEE_ALSO,)),
)

#: Targets outside this batch that no accepted record defines. Each citation is
#: an expected unresolved-reference finding, repeats included.
OUTSTANDING_TARGETS: tuple[Target, ...] = (
    (PLAY, "play.actions"),
    "damage_types",
    "dead",
    "long_rest",
    "short_rest",
)
#: Targets outside this batch that the accepted inputs define.
ACCEPTED_CONTEXT_TARGETS: tuple[Target, ...] = (
    "attack",
    "climb_speed",
    "climbing",
    "crawling",
    "dash",
    "difficult_terrain",
    "disengage",
    "dodge",
    "fly_speed",
    "help",
    "hit_points",
    "immunity",
    "incapacitated",
    "influence",
    "initiative",
    "jumping",
    "opportunity_attacks",
    "prone",
    "reach",
    "ready",
    "resistance",
    "speed",
    "surprise",
    "swim_speed",
    "swimming",
    "temporary_hit_points",
    "unarmed_strike",
    "unconscious",
    "utilize",
    "vulnerability",
)


def batch() -> EntryBatch:
    """The tables above, read at call time so tests can mutate them."""
    return EntryBatch(
        origin=ORIGIN,
        schema=(SCHEMA_15_VERSION, SCHEMA_15_HASH),
        proposal_origin=f"{ORIGIN} (CRD Issue 5d combat, damage and breaking objects batch; unaccepted)",
        unit_prefix="combat-damage-breaking",
        parent=PARENT,
        entries=ENTRIES,
        expected_leaves=168,
        clauses=CLAUSES,
        framing=FRAMING,
        components=COMPONENTS,
        supporting=SUPPORTING,
        record_references=RECORD_REFERENCES,
        placements=PLACEMENTS,
        excluded=EXCLUDED,
    )


def build(session: Session) -> Built:
    """Derive the combat-damage-breaking proposal from the release *session* published."""
    return build_entry_batch(session, batch(), published_release_binding(session))


#: Printed pointers whose destination has no record yet, as (scope, text). Each
#: stays unresolved, alone and composed, until a reviewed resolution names it.
UNRESOLVED: tuple[tuple[str, str], ...] = (
    (PLAY, "Playing the Game"),
    (EQUIPMENT, "Equipment"),
    (SPELLS, "Spells"),
)


def expected_representation_findings() -> list[str]:
    """Every out-of-batch target: the accepted ones stay unknown to the batch alone."""
    return sorted(
        [
            *unknown_target_findings(
                RECORD_REFERENCES,
                COMPONENTS,
                (*OUTSTANDING_TARGETS, *ACCEPTED_CONTEXT_TARGETS),
            ),
            *(f"reference {s}:{t!r}: unresolved reference" for s, t in UNRESOLVED),
        ]
    )


def main(db: str) -> int:
    out = Path(__file__).resolve().parent / PROPOSAL_FILE
    return emit(db, build, out, expected_representation_findings())


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
