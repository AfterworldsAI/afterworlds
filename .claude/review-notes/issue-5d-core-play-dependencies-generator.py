# ruff: noqa: E501
"""Author the **core-play-dependencies** proposal: eleven Rules Glossary entries.

REVIEW MATERIAL for CRD Issue 5d (#137) over the qualified 5c release
``9717e288-c099-5217-b2d2-f89aeabd7b73`` / ``5.2.1-corpus.883aabdf-462``. It
emits an *unaccepted* ``5d-proposal-2`` artifact. It accepts nothing, publishes
nothing, writes nothing under ``oracles/``, records no reference resolution,
and imports no earlier batch's content, identity or authority: every leaf is
read afresh from the release.

Scope, 52 leaves, one ``ENTRY`` review unit per record. These are the eleven
named targets the accepted core play cites and no accepted record defines:

* *Attack Roll* (2 leaves), cited by ``glossary.armor_class``;
* *Stat Block* (21), cited by ``glossary.challenge_rating``, every subsection
  from *Size* to *Damage Notation* (the *Areas of Knowledge* table printed
  beside it belongs to *Study*);
* *Carrying Capacity* (4), cited by ``play.exploration`` / ``carrying_objects``;
* *Blindsight* (2), *Darkvision* (2), *Tremorsense* (3) and *Truesight* (7),
  cited by ``play.exploration`` / ``special_senses``;
* *Burning* (2), *Dehydration* (3), *Malnutrition* (4) and *Suffocation* (2),
  printed as ``<name> [Hazard]`` and cited by ``play.exploration`` / ``hazards``.

No accepted reference with an empty target points into these entries, so no
reference resolution is drafted, and the recorded attack-roll resolution
(``play.combat`` / ``attack_structure`` -> ``play.d20_tests``) is untouched.

This file is literal review data only; the assembly is the committed shared
:mod:`afterworlds.ingestion.mechanical.authoring`. ``CLAUSES`` is the source
review; ``COMPONENTS`` is the representation proposed for it; expected rules
come from ``CLAUSES`` alone.

Authoring conventions (as the nine accepted batches, plus one):

* A typed fact is used only where it is true under the conditions the typed
  surface states. A condition the closed vocabulary cannot state stays in the
  same component's governing prose, beside the fact it conditions, and a lead
  that conditions a list is governing prose of the component holding the list:
  Truesight's *"within that range"* governs all five benefits, so the lead and
  the five are one component.
* A cadence is the component's ``recurs`` -- Burning at the start of each of
  the subject's turns, Suffocation at the end of each, Dehydration and both
  Malnutrition accruals at the end of each day -- never an unrepeated fact.
* One source statement, one typed copy. Attack Roll restates
  ``play.d20_tests`` and stays prose.
* Examples and *See also* pointers are supporting spans of the component they
  illustrate or of the record.
* References: every explicit pointer and each accepted glossary term a rule
  depends on. A pointer to a named glossary entry resolves to that entry's key
  whether or not it is accepted yet; one with no record yet reports an unknown
  target. A pointer to a part ("Playing the Game", "Monsters") is a reference
  in that part's scope with no target, reported unresolved. Terms only
  mentioned (Total Cover, Darkness, Dim Light, Ethereal Plane, "this
  glossary", Darkvision in *Senses*) stay unreferenced.

Run: ``python issue-5d-core-play-dependencies-generator.py <published afterworlds.db>``
"""

from __future__ import annotations

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
    ActionCost,
    ActionEconomyFact,
    Applicability,
    ApplicabilityKind,
    AutomaticOutcome,
    ConditionEffectFact,
    ConditionEffectKind,
    ConditionKind,
    ConditionLevelFact,
    ConditionRemovalRestrictionFact,
    ConsumptionBand,
    CreatureSize,
    DamageFact,
    DamageType,
    DcKind,
    DerivedQuantityFact,
    DiceExpression,
    DieSize,
    EffectTerminationFact,
    LevelDirection,
    MeasureUnit,
    Rational,
    RecordKind,
    Recurrence,
    RecurrenceBoundary,
    RequiredQuantity,
    RollActor,
    RollContext,
    SizeKeyedQuantityFact,
    SizeQuantity,
    TimePeriod,
    TimeUnit,
)
from afterworlds.ingestion.mechanical.schema_lift import (
    SCHEMA_15_HASH,
    SCHEMA_15_VERSION,
)

ORIGIN = "issue-5d-core-play-dependencies-generator.py"
PROPOSAL_FILE = "issue-5d-core-play-dependencies-PROPOSAL.json"
PARENT = ("Rules Glossary", "Rules Definitions")
PLAY = "srd-5.2.1/playing-the-game"
#: The *Monsters* part, formed from the release's own part name under the
#: ``<release-family>/<section-slug>`` convention ``PLAY`` uses.
MONSTERS = "srd-5.2.1/monsters"
#: The target of a printed pointer whose destination has no record yet. It is
#: reported as ``unresolved reference`` until a reviewed resolution names one;
#: naming a key here would guess at a record nobody has authored.
UNRESOLVED_TARGET = ""

#: (record slug, printed container label, record kind), in printed order. The
#: hazards print as ``<name> [Hazard]``; the label is the container's own.
ENTRIES: tuple[tuple[str, str, RecordKind], ...] = (
    ("attack_roll", "Attack Roll", RecordKind.GLOSSARY_RULE),
    ("blindsight", "Blindsight", RecordKind.GLOSSARY_RULE),
    ("burning", "Burning [Hazard]", RecordKind.GLOSSARY_RULE),
    ("carrying_capacity", "Carrying Capacity", RecordKind.GLOSSARY_RULE),
    ("darkvision", "Darkvision", RecordKind.GLOSSARY_RULE),
    ("dehydration", "Dehydration [Hazard]", RecordKind.GLOSSARY_RULE),
    ("malnutrition", "Malnutrition [Hazard]", RecordKind.GLOSSARY_RULE),
    ("stat_block", "Stat Block", RecordKind.GLOSSARY_RULE),
    ("suffocation", "Suffocation [Hazard]", RecordKind.GLOSSARY_RULE),
    ("tremorsense", "Tremorsense", RecordKind.GLOSSARY_RULE),
    ("truesight", "Truesight", RecordKind.GLOSSARY_RULE),
)

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
#: Every cell prints U+00D7 MULTIPLICATION SIGN, not the letter x.
CARRYING_CAPACITY_TABLE = html_table(
    "Carrying Capacity",
    ("Creature Size", "Carry", "Drag/Lift/Push"),
    [
        ("Tiny", "Str. × 7.5 lb.", "Str. × 15 lb."),
        ("Small/Medium", "Str. × 15 lb.", "Str. × 30 lb."),
        ("Large", "Str. × 30 lb.", "Str. × 60 lb."),
        ("Huge", "Str. × 60 lb.", "Str. × 120 lb."),
        ("Gargantuan", "Str. × 120 lb.", "Str. × 240 lb."),
    ],
)
WATER_TABLE = html_table(
    "Water Needs per Day",
    ("Size", "Water", "Size", "Water"),
    [
        ("Tiny", "1/4 gallon", "Large", "4 gallons"),
        ("Small", "1 gallon", "Huge", "16 gallons"),
        ("Medium", "1 gallon", "Gargantuan", "64 gallons"),
    ],
)
FOOD_TABLE = html_table(
    "Food Needs per Day",
    ("Size", "Food", "Size", "Food"),
    [
        ("Tiny", "1/4 pound", "Large", "4 pounds"),
        ("Small", "1 pound", "Huge", "16 pounds"),
        ("Medium", "1 pound", "Gargantuan", "64 pounds"),
    ],
)

# ---------------------------------------------------------------------------
# Source review: what each printed clause must be read as
# ---------------------------------------------------------------------------

TRUESIGHT_LEAD = "If you have Truesight, your vision is enhanced within a specified range. Within that range, your vision pierces through the following:"
TRUESIGHT_BENEFITS = (
    "**Darkness.** You can see in normal and magical Darkness.",
    "**Invisibility.** You see creatures and objects that have the Invisible condition.",
    "**Visual Illusions.** Visual illusions appear transparent to you, and you automatically succeed on saving throws against them.",
    "**Transformations.** You discern the true form of any creature or object you see that has been transformed by magic.",
    "**Ethereal Plane.** You see into the Ethereal Plane.",
)
BURN_DAMAGE_CLAUSE = "A burning creature or object takes 1d4 Fire damage at the start of each of its turns."
SUFFOCATION_ACCRUAL_CLAUSE = "When a creature runs out of breath or is choking, it gains 1 Exhaustion level at the end of each of its turns."
SUFFOCATION_RECOVERY_CLAUSE = "When a creature can breathe again, it removes all levels of Exhaustion it gained from suffocating."

#: (entry, component key, expected fact families + ``None`` for governing
#: prose, clause texts). Every rule-stating sentence of the batch is named here.
CLAUSES: tuple[tuple[str, str, tuple[str | None, ...], tuple[str, ...]], ...] = (
    # == Attack Roll (p177) ===================================================
    (
        "attack_roll",
        "attack_roll",
        (PROSE,),
        (
            "An attack roll is a D20 Test that represents making an attack with a weapon, an Unarmed Strike, or a spell.",
        ),
    ),
    # == Blindsight (p177) ====================================================
    # "Within that range" and "in that range" govern both perceptions.
    (
        "blindsight",
        "blindsight",
        (PROSE,),
        (
            "If you have Blindsight, you can see within a specific range without relying on physical sight. Within that range, you can see anything that isn't behind Total Cover even if you have the Blinded condition or are in Darkness. Moreover, in that range, you can see something that has the Invisible condition.",
        ),
    ),
    # == Burning [Hazard] (p178) ==============================================
    ("burning", "burning_damage", ("damage",), (BURN_DAMAGE_CLAUSE,)),
    (
        "burning",
        "self_extinguish",
        ("action_economy", "condition_effect", "effect_termination", PROSE),
        (
            "As an action, you can extinguish fire on yourself by giving yourself the Prone condition and rolling on the ground.",
        ),
    ),
    (
        "burning",
        "ambient_extinguish",
        ("effect_termination", PROSE),
        ("The fire also goes out if it is doused, submerged, or suffocated.",),
    ),
    # == Carrying Capacity (p178) =============================================
    (
        "carrying_capacity",
        "carrying_capacity",
        (PROSE,),
        (
            "Your size and Strength score determine the maximum weight in pounds that you can carry, as shown in the Carrying Capacity table. The table also shows the maximum weight you can drag, lift, or push.",
            CARRYING_CAPACITY_TABLE,
        ),
    ),
    (
        "carrying_capacity",
        "dragging_lifting_pushing",
        (PROSE,),
        (
            "While dragging, lifting, or pushing weight in excess of the maximum weight you can carry, your Speed can be no more than 5 feet.",
        ),
    ),
    # == Darkvision (p180) ====================================================
    (
        "darkvision",
        "darkvision",
        (PROSE,),
        (
            "If you have Darkvision, you can see in Dim Light within a specified range as if it were Bright Light and in Darkness within that range as if it were Dim Light. You discern colors in that Darkness only as shades of gray.",
        ),
    ),
    # == Dehydration [Hazard] (p181) ==========================================
    (
        "dehydration",
        "water_requirement",
        ("size_keyed_quantity",),
        (
            "A creature requires an amount of water per day based on its size, as shown in the Water Needs per Day table.",
            WATER_TABLE,
        ),
    ),
    (
        "dehydration",
        "dehydration_exhaustion",
        ("condition_level",),
        (
            "A creature that drinks less than half the required water for a day gains 1 Exhaustion level at the day's end.",
        ),
    ),
    (
        "dehydration",
        "dehydration_recovery",
        ("condition_removal_restriction",),
        (
            "Exhaustion caused by dehydration can't be removed until the creature drinks the full amount of water required for a day.",
        ),
    ),
    # == Malnutrition [Hazard] (p185) =========================================
    (
        "malnutrition",
        "food_requirement",
        ("size_keyed_quantity",),
        (
            "A creature needs an amount of food per day based on its size, as shown in the Food Needs per Day table.",
            FOOD_TABLE,
        ),
    ),
    (
        "malnutrition",
        "starvation_save",
        ("ability_check", "condition_level"),
        (
            "A creature that eats but consumes less than half the required food for a day must succeed on a DC 10 Constitution saving throw or gain 1 Exhaustion level at the day's end.",
        ),
    ),
    (
        "malnutrition",
        "starvation_automatic",
        ("condition_level",),
        (
            "A creature that eats nothing for 5 days automatically gains 1 Exhaustion level at the end of the fifth day as well as an additional level at the end of each subsequent day without food.",
        ),
    ),
    (
        "malnutrition",
        "malnutrition_recovery",
        ("condition_removal_restriction",),
        (
            "Exhaustion caused by malnutrition can't be removed until the creature eats the full amount of food required for a day.",
        ),
    ),
    # == Stat Block (pp188-189) ===============================================
    (
        "stat_block",
        "stat_block",
        (PROSE,),
        (
            "A stat block contains the game statistics of a monster. Each stat block includes the following information presented after the monster's name.",
        ),
    ),
    (
        "stat_block",
        "size",
        (PROSE,),
        ("_Size._ A monster is Tiny, Small, Medium, Large, Huge, or Gargantuan.",),
    ),
    (
        "stat_block",
        "creature_type",
        (PROSE,),
        (
            "_Creature Type._ This entry notes the family of beings a monster belongs to, along with any descriptive tags.",
        ),
    ),
    (
        "stat_block",
        "alignment",
        (PROSE,),
        (
            "_Alignment._ An alignment is suggested for the monster, with the GM determining its actual alignment.",
        ),
    ),
    (
        "stat_block",
        "ac_initiative_hp",
        (PROSE,),
        (
            "_AC, Initiative, and HP._ These entries give the monster's Armor Class, Initiative, and Hit Points, which are detailed in \"Playing the Game.\" In parentheses after the Hit Points, the monster's Hit Point Dice are provided, along with the contribution of its Constitution, if any, to its Hit Points. Following the Initiative modifier is an Initiative score. Some creatures that are created by magic lack Hit Dice and Initiative information.",
        ),
    ),
    (
        "stat_block",
        "speed",
        (PROSE,),
        (
            "_Speed._ Here the monster's Speed is provided, along with any special speeds.",
        ),
    ),
    (
        "stat_block",
        "ability_scores",
        (PROSE,),
        (
            '_Ability Scores._ A table provides the monster\'s ability scores, modifiers, and saving throw modifiers, all of which are detailed in "Playing the Game."',
        ),
    ),
    (
        "stat_block",
        "skills",
        (PROSE,),
        ("_Skills._ This entry lists the monster's skill proficiencies, if any.",),
    ),
    (
        "stat_block",
        "resistances_and_vulnerabilities",
        (PROSE,),
        (
            "_Resistances and Vulnerabilities._ These entries list the monster's Resistances and Vulnerabilities, if any.",
        ),
    ),
    (
        "stat_block",
        "immunities",
        (PROSE,),
        (
            "_Immunities._ This section lists the monster's damage and condition Immunities, if any.",
        ),
    ),
    (
        "stat_block",
        "gear",
        (PROSE,),
        (
            "_Gear._ If the monster has any equipment that can be given away or retrieved, it's listed in this entry.",
        ),
    ),
    (
        "stat_block",
        "senses",
        (PROSE,),
        (
            "_Senses._ This entry lists the monster's special senses, such as Darkvision, and its Passive Perception.",
        ),
    ),
    # *Languages* and *CR* share one leaf; each is its own clause.
    (
        "stat_block",
        "languages",
        (PROSE,),
        ("_Languages._ This entry lists any languages the monster knows.",),
    ),
    (
        "stat_block",
        "challenge_rating",
        (PROSE,),
        (
            '_CR._ Challenge Rating summarizes the threat a monster poses and is detailed in "Monsters." The Experience Points characters receive for defeating a monster and its Proficiency Bonus follow. Some creatures that are created by magic have no CR.',
        ),
    ),
    (
        "stat_block",
        "traits",
        (PROSE,),
        (
            "_Traits._ The monster's traits, if any, are features that are active at all times or in certain situations.",
        ),
    ),
    (
        "stat_block",
        "actions",
        (PROSE,),
        (
            "_Actions._ The monster can take these actions in addition to those detailed in this glossary.",
        ),
    ),
    (
        "stat_block",
        "bonus_actions",
        (PROSE,),
        (
            "_Bonus Actions._ If the monster has Bonus Action options, they are listed in this section.",
        ),
    ),
    (
        "stat_block",
        "reactions",
        (PROSE,),
        (
            "_Reactions._ If the monster can take special Reactions, those are listed in this section.",
        ),
    ),
    (
        "stat_block",
        "attack_notation",
        (PROSE,),
        (
            "_Attack Notation._ The entry for a monster's attack starts by identifying whether the attack is a melee or a ranged attack and then provides the attack roll's bonus, its reach or range, and what happens on a hit. An attack is against one target unless its entry says otherwise.",
        ),
    ),
    (
        "stat_block",
        "saving_throw_effect_notation",
        (PROSE,),
        (
            "_Saving Throw Effect Notation._ If an effect forces a saving throw, the effect's entry starts by identifying the kind of saving throw required and then provides the save's DC, a description of which creatures must make the save, and what happens on a failed or a successful save.",
        ),
    ),
    (
        "stat_block",
        "damage_notation",
        (PROSE,),
        (
            "_Damage Notation._ A stat block usually provides both a static number and a die expression for each instance of damage.",
            "The GM determines whether you use the static number or the die expression in parentheses; you don't use both.",
        ),
    ),
    # == Suffocation [Hazard] (p189) ==========================================
    (
        "suffocation",
        "breath_duration",
        ("derived_quantity",),
        (
            "A creature can hold its breath for a number of minutes equal to 1 plus its Constitution modifier (minimum of 30 seconds) before suffocation begins.",
        ),
    ),
    (
        "suffocation",
        "suffocation_accrual",
        ("condition_level", PROSE),
        (SUFFOCATION_ACCRUAL_CLAUSE,),
    ),
    (
        "suffocation",
        "suffocation_recovery",
        ("condition_level", PROSE),
        (SUFFOCATION_RECOVERY_CLAUSE,),
    ),
    # == Tremorsense (p190) ===================================================
    # The second paragraph limits what the first grants: one component.
    (
        "tremorsense",
        "tremorsense",
        (PROSE,),
        (
            "A creature with Tremorsense can pinpoint the location of creatures and moving objects within a specific range, provided that the creature with Tremorsense and anything it is detecting are both in contact with the same surface (such as the ground, a wall, or a ceiling) or the same liquid.",
            "Tremorsense can't detect creatures or objects in the air, and it doesn't count as a form of sight.",
        ),
    ),
    # == Truesight (p190) =====================================================
    # The range lead governs every benefit, so the six are one component.
    (
        "truesight",
        "truesight",
        (PROSE,),
        (TRUESIGHT_LEAD, *TRUESIGHT_BENEFITS),
    ),
)

#: No entry prints a whole leaf that only frames the rules after it: Stat
#: Block's lead states what a stat block is, and Truesight's states the range.
FRAMING: tuple[tuple[str, str], ...] = ()

# ---------------------------------------------------------------------------
# Representation proposed for the clauses above
# ---------------------------------------------------------------------------

C = EntryComponent

#: The accepted *Playing the Game* destinations this batch cites.
PLAY_ACTIONS = (PLAY, "play.actions")
PLAY_D20_TESTS = (PLAY, "play.d20_tests")
PLAY_EXPLORATION = (PLAY, "play.exploration")
PLAY_PROFICIENCY = (PLAY, "play.proficiency")
PLAY_UNRESOLVED = (PLAY, UNRESOLVED_TARGET)
MONSTERS_UNRESOLVED = (MONSTERS, UNRESOLVED_TARGET)

EXHAUSTION_REF: tuple[tuple[str, Target], ...] = (("Exhaustion", "exhaustion"),)

HALF, WHOLE, ZERO = Rational(1, 2), Rational(1, 1), Rational(0, 1)


def band(
    quantity: RequiredQuantity,
    *,
    lower: Rational | None = None,
    lower_inclusive: bool = False,
    upper: Rational | None = None,
    upper_inclusive: bool = False,
    sustained_at_least: int | None = None,
    sustained_unit: TimeUnit | None = None,
) -> Applicability:
    """Consumption over one day, as a share of the printed daily requirement."""
    return Applicability(
        kind=ApplicabilityKind.CONSUMPTION_THRESHOLD,
        band=ConsumptionBand(
            quantity=quantity,
            period=TimePeriod.DAY,
            lower=lower,
            lower_inclusive=lower_inclusive,
            upper=upper,
            upper_inclusive=upper_inclusive,
            sustained_at_least=sustained_at_least,
            sustained_unit=sustained_unit,
        ),
    )


#: "drinks less than half": one-sided; drinking nothing is inside it.
DEHYDRATION_BAND = band(RequiredQuantity.WATER, upper=HALF)
#: "eats **but** consumes less than half": the "but" is the exclusive lower 0,
#: which keeps the save apart from the zero-food rule below.
STARVATION_PARTIAL_BAND = band(RequiredQuantity.FOOD, lower=ZERO, upper=HALF)
#: "eats nothing for 5 days": zero food, sustained at least five days. With the
#: daily cadence, the component repeats only while no food is eaten.
STARVATION_ZERO_BAND = band(
    RequiredQuantity.FOOD,
    lower=ZERO,
    lower_inclusive=True,
    upper=ZERO,
    upper_inclusive=True,
    sustained_at_least=5,
    sustained_unit=TimeUnit.DAY,
)
#: "the full amount ... required for a day": 1 inclusive, unbounded above.
WATER_FULL_BAND = band(RequiredQuantity.WATER, lower=WHOLE, lower_inclusive=True)
FOOD_FULL_BAND = band(RequiredQuantity.FOOD, lower=WHOLE, lower_inclusive=True)

START_OF_OWN_TURN = Recurrence(RecurrenceBoundary.START_OF_TURN, RollActor.SUBJECT)
END_OF_OWN_TURN = Recurrence(RecurrenceBoundary.END_OF_TURN, RollActor.SUBJECT)
END_OF_DAY = Recurrence(RecurrenceBoundary.END_OF_DAY)

GAIN_1 = ConditionLevelFact(ConditionKind.EXHAUSTION, LevelDirection.GAIN, amount=1)
TERMINATION = EffectTerminationFact()


def needs(quantity: RequiredQuantity, unit: MeasureUnit) -> SizeKeyedQuantityFact:
    """The Water/Food Needs per Day table: 1/4, 1, 1, 4, 16, 64 by size."""
    amounts = (Rational(1, 4), WHOLE, WHOLE, Rational(4, 1), Rational(16, 1))
    return SizeKeyedQuantityFact(
        quantity=quantity,
        period=TimePeriod.DAY,
        values=tuple(
            SizeQuantity(size, amount, unit)
            for size, amount in zip(
                CreatureSize, (*amounts, Rational(64, 1)), strict=True
            )
        ),
    )


#: "must succeed on a DC 10 Constitution saving throw": a save, no skill.
CON_SAVE = AbilityCheckFact(
    ability=AbilityScore.CONSTITUTION,
    dc_kind=DcKind.FIXED,
    context=RollContext.SAVING_THROW,
    dc_value=10,
)
FAILED = Applicability(
    kind=ApplicabilityKind.ROLL_OUTCOME, outcome=AutomaticOutcome.FAILURE
)

COMPONENTS: tuple[EntryComponent, ...] = (
    # == Attack Roll ==========================================================
    # Restates ``play.d20_tests``, which types the attack roll; no second copy.
    C(
        "attack_roll",
        "attack_roll",
        P,
        NO_USE,
        refs=(("Unarmed Strike", "unarmed_strike"),),
    ),
    # == Blindsight ===========================================================
    # ``Sense`` has no Blindsight member, and SIGHT would claim the physical
    # sight the source says it does not rely on; the range and the Total Cover
    # limit stay beside what they limit.
    C(
        "blindsight",
        "blindsight",
        P,
        CTX,
        refs=(("Blinded", "blinded"), ("Invisible", "invisible")),
    ),
    # == Burning ==============================================================
    C(
        "burning",
        "burning_damage",
        S,
        None,
        facts=(DamageFact(DamageType.FIRE, DiceExpression(1, DieSize.D4)),),
        recurs=START_OF_OWN_TURN,
    ),
    # "on yourself" and "rolling on the ground" govern the three facts.
    C(
        "burning",
        "self_extinguish",
        M,
        CTX,
        facts=(
            ActionEconomyFact(ActionCost.ACTION),
            ConditionEffectFact(ConditionKind.PRONE, ConditionEffectKind.APPLIES),
            TERMINATION,
        ),
        refs=(("Prone", "prone"),),
    ),
    # Doused, submerged or suffocated is fiction no Applicability names.
    C("burning", "ambient_extinguish", M, CTX, facts=(TERMINATION,)),
    # == Carrying Capacity ====================================================
    # No family multiplies Strength by a size-keyed factor.
    C("carrying_capacity", "carrying_capacity", P, NO_USE),
    # A ceiling, not ``SpeedChange.SET_TO``: a Speed already below 5 feet stays.
    C(
        "carrying_capacity",
        "dragging_lifting_pushing",
        P,
        NO_USE,
        refs=(("Speed", "speed"),),
    ),
    # == Darkvision ===========================================================
    C("darkvision", "darkvision", P, CTX),
    # == Dehydration ==========================================================
    C(
        "dehydration",
        "water_requirement",
        S,
        None,
        facts=(needs(RequiredQuantity.WATER, MeasureUnit.GALLON),),
    ),
    C(
        "dehydration",
        "dehydration_exhaustion",
        S,
        None,
        facts=(GAIN_1,),
        applies_when=DEHYDRATION_BAND,
        recurs=END_OF_DAY,
        refs=EXHAUSTION_REF,
    ),
    # Apart from the accrual: its band gates the gain, not the restriction.
    C(
        "dehydration",
        "dehydration_recovery",
        S,
        None,
        facts=(
            ConditionRemovalRestrictionFact(ConditionKind.EXHAUSTION, WATER_FULL_BAND),
        ),
        refs=EXHAUSTION_REF,
    ),
    # == Malnutrition =========================================================
    C(
        "malnutrition",
        "food_requirement",
        S,
        None,
        facts=(needs(RequiredQuantity.FOOD, MeasureUnit.POUND),),
    ),
    # The band governs both facts; only the gain waits on the failed save.
    C(
        "malnutrition",
        "starvation_save",
        S,
        None,
        facts=(CON_SAVE, GAIN_1),
        qualifiers=((GAIN_1, FAILED),),
        applies_when=STARVATION_PARTIAL_BAND,
        recurs=END_OF_DAY,
        refs=EXHAUSTION_REF,
    ),
    C(
        "malnutrition",
        "starvation_automatic",
        S,
        None,
        facts=(GAIN_1,),
        applies_when=STARVATION_ZERO_BAND,
        recurs=END_OF_DAY,
        refs=EXHAUSTION_REF,
    ),
    C(
        "malnutrition",
        "malnutrition_recovery",
        S,
        None,
        facts=(
            ConditionRemovalRestrictionFact(ConditionKind.EXHAUSTION, FOOD_FULL_BAND),
        ),
        refs=EXHAUSTION_REF,
    ),
    # == Stat Block ===========================================================
    # A description of a printed format. No family states one, and reading a
    # monster's statistics is its creature record's work, not this entry's.
    C("stat_block", "stat_block", P, NO_USE),
    C("stat_block", "size", P, NO_USE),
    C("stat_block", "creature_type", P, NO_USE),
    C("stat_block", "alignment", P, GM),
    # "detailed in "Playing the Game."" names the part, not one record of it.
    C(
        "stat_block",
        "ac_initiative_hp",
        P,
        NO_USE,
        refs=(("Playing the Game", PLAY_UNRESOLVED),),
    ),
    C("stat_block", "speed", P, NO_USE),
    C(
        "stat_block",
        "ability_scores",
        P,
        NO_USE,
        refs=(("Playing the Game", PLAY_UNRESOLVED),),
    ),
    C("stat_block", "skills", P, NO_USE),
    C("stat_block", "resistances_and_vulnerabilities", P, NO_USE),
    C("stat_block", "immunities", P, NO_USE),
    C("stat_block", "gear", P, NO_USE),
    C("stat_block", "senses", P, NO_USE),
    C("stat_block", "languages", P, NO_USE),
    C(
        "stat_block",
        "challenge_rating",
        P,
        NO_USE,
        refs=(("Monsters", MONSTERS_UNRESOLVED),),
    ),
    C("stat_block", "traits", P, NO_USE),
    C("stat_block", "actions", P, NO_USE),
    C("stat_block", "bonus_actions", P, NO_USE),
    C("stat_block", "reactions", P, NO_USE),
    # "unless its entry says otherwise".
    C("stat_block", "attack_notation", P, CTX),
    C("stat_block", "saving_throw_effect_notation", P, NO_USE),
    # "The GM determines whether you use the static number or the die
    # expression"; which is used is the GM's, and never both.
    C("stat_block", "damage_notation", P, GM),
    # == Suffocation ==========================================================
    C(
        "suffocation",
        "breath_duration",
        S,
        None,
        facts=(
            DerivedQuantityFact(
                base=1,
                modifier=AbilityScore.CONSTITUTION,
                unit=TimeUnit.MINUTE,
                floor_amount=30,
                floor_unit=TimeUnit.SECOND,
            ),
        ),
    ),
    # "runs out of breath or is choking": a disjunction whose second arm no
    # Applicability names, so the whole trigger is governing prose.
    C(
        "suffocation",
        "suffocation_accrual",
        M,
        CTX,
        facts=(GAIN_1,),
        recurs=END_OF_OWN_TURN,
        refs=EXHAUSTION_REF,
    ),
    # Only the levels suffocation caused: ``cause_scoped``.
    C(
        "suffocation",
        "suffocation_recovery",
        M,
        CTX,
        facts=(
            ConditionLevelFact(
                ConditionKind.EXHAUSTION,
                LevelDirection.REMOVE,
                all_levels=True,
                cause_scoped=True,
            ),
        ),
        refs=EXHAUSTION_REF,
    ),
    # == Tremorsense ==========================================================
    C("tremorsense", "tremorsense", P, CTX),
    # == Truesight ============================================================
    # Every benefit, including the automatic success against visual illusions,
    # holds only within the range; no typed fact can carry that, and an
    # unqualified automatic success on saving throws would be broader than the
    # source. So the lead and the five benefits are one prose component.
    C("truesight", "truesight", P, CTX, refs=(("Invisible", "invisible"),)),
)

D20_TESTS_SEE_ALSO = '_See also_ "Playing the Game" ("D20 Tests").'
EXPLORATION_SEE_ALSO = '_See also_ "Playing the Game" ("Exploration").'
EXHAUSTION_SEE_ALSO = '_See also_ "Exhaustion."'
SIZE_SEE_ALSO = '_See also_ "Size."'
CREATURE_TYPE_SEE_ALSO = '_See also_ "Creature Type."'
ALIGNMENT_SEE_ALSO = '_See also_ "Alignment."'
SPEEDS_SEE_ALSO = (
    '_See also_ "Burrow Speed," "Climb Speed," "Fly Speed," and "Swim Speed."'
)
PROFICIENCY_SEE_ALSO = '_See also_ "Playing the Game" ("Proficiency").'
RESISTANCE_SEE_ALSO = '_See also_ "Resistance" and "Vulnerability."'
IMMUNITY_SEE_ALSO = '_See also_ "Immunity."'
PASSIVE_PERCEPTION_SEE_ALSO = '_See also_ "Passive Perception."'
CR_SEE_ALSO = '_See also_ "Challenge Rating" and "Experience Points."'
ACTIONS_SEE_ALSO = '_See also_ "Playing the Game" ("Actions").'
DAMAGE_NOTATION_EXAMPLE = (
    "For example, an attack might deal 4 (1d4 + 2) damage on a hit."
)

#: Supporting spans: (entry, text, component supported or ``None`` for the
#: record). Examples illustrate; *See also* pointers identify.
SUPPORTING: tuple[tuple[str, str, str | None], ...] = (
    ("attack_roll", D20_TESTS_SEE_ALSO, None),
    ("darkvision", EXPLORATION_SEE_ALSO, None),
    ("dehydration", EXHAUSTION_SEE_ALSO, None),
    ("malnutrition", EXHAUSTION_SEE_ALSO, None),
    ("stat_block", SIZE_SEE_ALSO, None),
    ("stat_block", CREATURE_TYPE_SEE_ALSO, None),
    ("stat_block", ALIGNMENT_SEE_ALSO, None),
    ("stat_block", SPEEDS_SEE_ALSO, None),
    ("stat_block", PROFICIENCY_SEE_ALSO, None),
    ("stat_block", RESISTANCE_SEE_ALSO, None),
    ("stat_block", IMMUNITY_SEE_ALSO, None),
    ("stat_block", PASSIVE_PERCEPTION_SEE_ALSO, None),
    ("stat_block", CR_SEE_ALSO, None),
    ("stat_block", ACTIONS_SEE_ALSO, None),
    ("stat_block", DAMAGE_NOTATION_EXAMPLE, "damage_notation"),
)

#: Record-owned references: (entry, printed text, target, texts of the spans the
#: pointer is read from).
RECORD_REFERENCES: tuple[RecordReference, ...] = (
    ("attack_roll", "D20 Tests", PLAY_D20_TESTS, (D20_TESTS_SEE_ALSO,)),
    ("darkvision", "Exploration", PLAY_EXPLORATION, (EXPLORATION_SEE_ALSO,)),
    ("dehydration", "Exhaustion", "exhaustion", (EXHAUSTION_SEE_ALSO,)),
    ("malnutrition", "Exhaustion", "exhaustion", (EXHAUSTION_SEE_ALSO,)),
    ("stat_block", "Size", "size", (SIZE_SEE_ALSO,)),
    ("stat_block", "Creature Type", "creature_type", (CREATURE_TYPE_SEE_ALSO,)),
    ("stat_block", "Alignment", "alignment", (ALIGNMENT_SEE_ALSO,)),
    ("stat_block", "Burrow Speed", "burrow_speed", (SPEEDS_SEE_ALSO,)),
    ("stat_block", "Climb Speed", "climb_speed", (SPEEDS_SEE_ALSO,)),
    ("stat_block", "Fly Speed", "fly_speed", (SPEEDS_SEE_ALSO,)),
    ("stat_block", "Swim Speed", "swim_speed", (SPEEDS_SEE_ALSO,)),
    ("stat_block", "Proficiency", PLAY_PROFICIENCY, (PROFICIENCY_SEE_ALSO,)),
    ("stat_block", "Resistance", "resistance", (RESISTANCE_SEE_ALSO,)),
    ("stat_block", "Vulnerability", "vulnerability", (RESISTANCE_SEE_ALSO,)),
    ("stat_block", "Immunity", "immunity", (IMMUNITY_SEE_ALSO,)),
    (
        "stat_block",
        "Passive Perception",
        "passive_perception",
        (PASSIVE_PERCEPTION_SEE_ALSO,),
    ),
    ("stat_block", "Challenge Rating", "challenge_rating", (CR_SEE_ALSO,)),
    ("stat_block", "Experience Points", "experience_points", (CR_SEE_ALSO,)),
    ("stat_block", "Actions", PLAY_ACTIONS, (ACTIONS_SEE_ALSO,)),
)

#: Named Rules Glossary entries outside this batch that no accepted record
#: defines and this batch does not author. Each citation is an expected
#: unknown-target finding, alone and composed.
NEW_TARGETS: tuple[Target, ...] = (
    "alignment",
    "creature_type",
    "experience_points",
    "passive_perception",
    "size",
)
#: Targets outside this batch that the accepted inputs define.
ACCEPTED_CONTEXT_TARGETS: tuple[Target, ...] = (
    PLAY_ACTIONS,
    PLAY_D20_TESTS,
    PLAY_EXPLORATION,
    PLAY_PROFICIENCY,
    "blinded",
    "burrow_speed",
    "challenge_rating",
    "climb_speed",
    "exhaustion",
    "fly_speed",
    "immunity",
    "invisible",
    "prone",
    "resistance",
    "speed",
    "swim_speed",
    "unarmed_strike",
    "vulnerability",
)


def batch() -> EntryBatch:
    """The tables above, read at call time so tests can mutate them."""
    return EntryBatch(
        origin=ORIGIN,
        schema=(SCHEMA_15_VERSION, SCHEMA_15_HASH),
        proposal_origin=f"{ORIGIN} (CRD Issue 5d core-play dependencies batch; unaccepted)",
        unit_prefix="core-play-dependencies",
        parent=PARENT,
        entries=ENTRIES,
        expected_leaves=52,
        clauses=CLAUSES,
        framing=FRAMING,
        components=COMPONENTS,
        supporting=SUPPORTING,
        record_references=RECORD_REFERENCES,
    )


def build(session: Session) -> Built:
    """Derive the core-play-dependencies proposal from the release *session* published."""
    return build_entry_batch(session, batch(), published_release_binding(session))


#: Printed pointers to a part with no record, as (scope, text). Each stays
#: unresolved, alone and composed, until a reviewed resolution names it.
UNRESOLVED: tuple[tuple[str, str], ...] = (
    (MONSTERS, "Monsters"),
    (PLAY, "Playing the Game"),
    (PLAY, "Playing the Game"),
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
