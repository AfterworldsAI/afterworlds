# ruff: noqa: E501  -- clause literals are verbatim source text, kept whole to be greppable
"""Author the fresh **actions-pilot** proposal: the twelve actions + Unarmed Strike.

REVIEW MATERIAL for CRD Issue 5d (#137) over the qualified 5c release
``9717e288-c099-5217-b2d2-f89aeabd7b73`` / ``5.2.1-corpus.883aabdf-462``. It
emits an *unaccepted* ``5d-proposal-2`` artifact. It accepts nothing, publishes
nothing, writes nothing under ``oracles/``, and imports no earlier batch's
content, identity or authority (the quarantined ``actions-1`` batches included).

Scope: the twelve ``[Action]`` glossary entries and ``Unarmed Strike`` -- 13
peer entries under *Rules Glossary > Rules Definitions*, 49 represented leaves,
one ``ENTRY`` review unit each. *Playing the Game*'s Actions, D20 Tests and
Combat sections, the ``Action`` glossary entry, and every other glossary entry
these cite are outside it; their pointers stay explicit unknown targets.

This file is literal review data only. The assembly is the committed shared
:mod:`afterworlds.ingestion.mechanical.authoring`, which the conditions pilot
also runs on. ``CLAUSES`` is the source review; ``COMPONENTS`` is the
representation proposed for it; expected rules come from ``CLAUSES`` alone.

Authoring conventions (as the conditions pilot, plus):

* A table is one clause with its caption, written as its rows by
  :func:`html_table`; the leaf must still match it verbatim.
* An option set is used only where every arm has typed facts. A choice with an
  arm the closed vocabulary cannot state stays governing prose; its chooser is
  kept in that prose rather than implied by a partial option set.
* Terms carried by closed code-owned vocabulary (Opportunity Attacks, Heavily
  Obscured, Cover, Reaction, Concentration and Speed inside facts) are bound by
  that type, not by a reference. The source's own *See also* pointers, the
  conditions and attitudes it names, and in-batch pointers are references.

Run: ``python issue-5d-actions-pilot-generator.py <published afterworlds.db>``
"""

from __future__ import annotations

import sys
from pathlib import Path

from sqlalchemy.orm import Session

from afterworlds.ingestion.mechanical.authoring import (
    Built,
    EntryBatch,
    EntryComponent,
    build_entry_batch,
    emit,
    html_table,
    unknown_target_findings,
)
from afterworlds.ingestion.mechanical.authoring import batch_findings as batch_findings
from afterworlds.ingestion.mechanical.authoring import render as render
from afterworlds.ingestion.mechanical.bound_corpus import published_release_binding
from afterworlds.ingestion.mechanical.representation import (
    AbilityCheckFact,
    AbilityScore,
    ActionAllowanceFact,
    ActionCost,
    ActivationCostEligibilityFact,
    AdvantageFact,
    AdvantageState,
    AllowanceScope,
    Applicability,
    ApplicabilityKind,
    AttackRelativeTiming,
    AutomaticOutcome,
    BenefitUseLimit,
    CastingTimeThreshold,
    Comparison,
    ComponentHandling,
    ComponentOption,
    ConditionEffectFact,
    ConditionEffectKind,
    ConditionKind,
    CoverDegree,
    DcKind,
    EffectDurationFact,
    EffectTerminationFact,
    EligibilitySubject,
    EquipmentChange,
    EquipmentChangeFact,
    ExpendableResource,
    GrantedActivity,
    InterleavePoint,
    MovementAllowanceBasis,
    MovementAllowanceFact,
    MovementInterleaveFact,
    ObscurementState,
    ReactionProvocationFact,
    RecordKind,
    RecurrenceBoundary,
    RecurringActionRequirementFact,
    ResolutionTiming,
    ResourceExpenditureFact,
    RetryRestrictionFact,
    RollActor,
    RollContext,
    RollSpec,
    Skill,
    StateEffectKind,
    SustainedState,
    SustainedStateRequirementFact,
    TimeUnit,
    TrackedQuantity,
    TriggeredReaction,
    TriggeredResolutionFact,
)
from afterworlds.ingestion.mechanical.schema_lift import (
    SCHEMA_15_HASH,
    SCHEMA_15_VERSION,
)

ORIGIN = "issue-5d-actions-pilot-generator.py"
PROPOSAL_FILE = "issue-5d-actions-pilot-PROPOSAL.json"
PARENT = ("Rules Glossary", "Rules Definitions")

#: (record slug, printed container label, record kind). Printed order.
ENTRIES: tuple[tuple[str, str, RecordKind], ...] = (
    ("attack", "Attack [Action]", RecordKind.GLOSSARY_RULE),
    ("dash", "Dash [Action]", RecordKind.GLOSSARY_RULE),
    ("disengage", "Disengage [Action]", RecordKind.GLOSSARY_RULE),
    ("dodge", "Dodge [Action]", RecordKind.GLOSSARY_RULE),
    ("help", "Help [Action]", RecordKind.GLOSSARY_RULE),
    ("hide", "Hide [Action]", RecordKind.GLOSSARY_RULE),
    ("influence", "Influence [Action]", RecordKind.GLOSSARY_RULE),
    ("magic", "Magic [Action]", RecordKind.GLOSSARY_RULE),
    ("ready", "Ready [Action]", RecordKind.GLOSSARY_RULE),
    ("search", "Search [Action]", RecordKind.GLOSSARY_RULE),
    ("study", "Study [Action]", RecordKind.GLOSSARY_RULE),
    ("unarmed_strike", "Unarmed Strike", RecordKind.GLOSSARY_RULE),
    ("utilize", "Utilize [Action]", RecordKind.GLOSSARY_RULE),
)

# ---------------------------------------------------------------------------
# Reason codes and handling
# ---------------------------------------------------------------------------
CTX = "contextual_applicability"
SUBJ = "subjective_judgment"
OPEN = "open_ended_effect"
GM = "gamemaster_latitude"
FICTION = "fiction_dependent_consequence"
NO_USE = "no_identified_structured_use"
S, M, P = (
    ComponentHandling.STRUCTURED,
    ComponentHandling.MIXED,
    ComponentHandling.PROSE_BOUND,
)
PROSE = None


def until_your_next_turn() -> EffectDurationFact:
    return EffectDurationFact(RecurrenceBoundary.START_OF_TURN, RollActor.SUBJECT)


def rest_of_your_turn() -> EffectDurationFact:
    return EffectDurationFact(RecurrenceBoundary.END_OF_TURN, RollActor.SUBJECT)


def when_concentration_breaks() -> Applicability:
    return Applicability(
        kind=ApplicabilityKind.EFFECT_STATE,
        effect_state=StateEffectKind.CONCENTRATION_BROKEN,
    )


def on(outcome: AutomaticOutcome) -> Applicability:
    return Applicability(kind=ApplicabilityKind.ROLL_OUTCOME, outcome=outcome)


def cover(degree: CoverDegree) -> Applicability:
    return Applicability(kind=ApplicabilityKind.COVER, cover=degree)


# ---------------------------------------------------------------------------
# Source review: what each printed clause must be read as
# ---------------------------------------------------------------------------

DASH_SPECIAL = "If you have a special speed, such as a Fly Speed or Swim Speed, you can use that speed instead of your Speed when you take this action."
DASH_CHOICE = "You choose which speed to use each time you take it."

HELP_INTRO = "When you take the Help action, you do one of the following."
HELP_CHECK = (
    "_Assist an Ability Check._ Choose one of your skill or tool proficiencies and one ally who is near\nenough for you to assist verbally or physically when they make an ability check.",
    "That ally has Advantage on the next ability check they make with the chosen skill or tool.",
    "This benefit expires if the ally doesn't use it before the start of your next turn.",
)
HELP_ATTACK = "_Assist an Attack Roll._ You momentarily distract an enemy within 5 feet of you, giving Advantage to the next attack roll by one of your allies against that enemy. This benefit expires at the start of your next turn."

INFLUENCE_HESITANT = (
    "_Hesitant._ If you urge the monster to do something that it is hesitant to do, you must make an ability check, which is affected by the monster's attitude: Indifferent, Friendly, or Hostile, each of which is defined in this glossary.",
    "The GM chooses the check, which has a default DC equal to 15 or the monster's Intelligence score, whichever is higher.",
    "On a successful check, the monster does as urged.",
    "On a failed check, you must wait 24 hours (or a duration set by the GM) before urging it in the same way again.",
)
INFLUENCE_TABLE = html_table(
    "Influence Checks",
    ("Ability Check", "Interaction"),
    [
        ("Charisma (Deception)", "Deceiving a monster that understands you"),
        ("Charisma (Intimidation)", "Intimidating a monster"),
        ("Charisma (Performance)", "Amusing a monster"),
        ("Charisma (Persuasion)", "Persuading a monster that understands you"),
        ("Wisdom (Animal Handling)", "Gently coaxing a Beast or Monstrosity"),
    ],
)
SEARCH_TABLE = html_table(
    "Search",
    ("Skill", "Thing to Detect"),
    [
        ("Insight", "Creature's state of mind"),
        ("Medicine", "Creature's ailment or cause of death"),
        ("Perception", "Concealed creature or object"),
        ("Survival", "Tracks or food"),
    ],
)
STUDY_TABLE = html_table(
    "Areas of Knowledge",
    ("Skill", "Areas"),
    [
        (
            "Arcana",
            "Spells, magic items, eldritch symbols, magical traditions, planes of existence, and certain creatures (Aberrations, Constructs, Elementals, Fey, and Monstrosities)",
        ),
        (
            "History",
            "Historic events and people, ancient civilizations, wars, and certain creatures (Giants and Humanoids)",
        ),
        ("Investigation", "Traps, ciphers, riddles, and gadgetry"),
        (
            "Nature",
            "Terrain, flora, weather, and certain creatures (Beasts, Dragons, Oozes, and Plants)",
        ),
        (
            "Religion",
            "Deities, religious hierarchies and rites, holy symbols, cults, and certain creatures (Celestials, Fiends, and Undead)",
        ),
    ],
)

#: (entry, component key, expected fact families + ``None`` for governing
#: prose, clause texts). Every non-heading leaf of the batch is named here.
CLAUSES: tuple[tuple[str, str, tuple[str | None, ...], tuple[str, ...]], ...] = (
    # -- Attack (p177) ------------------------------------------------------
    (
        "attack",
        "attack_roll",
        ("action_allowance", PROSE),
        (
            "When you take the Attack action, you can make one attack roll with a weapon or an Unarmed Strike.",
        ),
    ),
    (
        "attack",
        "equip_or_unequip",
        ("action_allowance", "equipment_change"),
        (
            "_Equipping and Unequipping Weapons._ You can either equip or unequip one weapon when you make an attack as part of this action.",
            "You do so either before or after the attack.",
        ),
    ),
    (
        "attack",
        "equipping_scope",
        (PROSE,),
        (
            "If you equip a weapon before an attack, you don't need to use it for that attack.",
            "Equipping a weapon includes drawing it from a sheath or picking it up.",
            "Unequipping a weapon includes sheathing, stowing, or dropping it.",
        ),
    ),
    (
        "attack",
        "moving_between_attacks",
        ("movement_interleave", PROSE),
        (
            "_Moving between Attacks._ If you move on your turn and have a feature, such as Extra Attack, that gives you more than one attack as part of the Attack action, you can use some or all of that movement to move between those attacks.",
        ),
    ),
    # -- Dash (p180) --------------------------------------------------------
    (
        "dash",
        "extra_movement",
        ("movement_allowance", "effect_duration"),
        (
            "When you take the Dash action, you gain extra movement for the current turn.",
            "The increase equals your Speed after applying any modifiers.",
        ),
    ),
    (
        "dash",
        "special_speed",
        ("movement_allowance", PROSE),
        (DASH_SPECIAL, DASH_CHOICE),
    ),
    # -- Disengage (p181) ---------------------------------------------------
    (
        "disengage",
        "no_opportunity_attacks",
        ("reaction_provocation", "effect_duration"),
        (
            "If you take the Disengage action, your movement doesn't provoke Opportunity Attacks for the rest of the current turn.",
        ),
    ),
    # -- Dodge (p181) -------------------------------------------------------
    (
        "dodge",
        "dodge_benefits",
        ("advantage", "effect_duration", PROSE),
        (
            "If you take the Dodge action, you gain the following benefits: until the start of your next turn, any attack roll made against you has Disadvantage if you can see the attacker, and you make Dexterity saving throws with Advantage.",
        ),
    ),
    (
        "dodge",
        "benefits_lost",
        ("effect_termination",),
        (
            "You lose these benefits if you have the Incapacitated condition or if your Speed is 0.",
        ),
    ),
    # -- Help (pp182-183) ---------------------------------------------------
    (
        "help",
        "assistance",
        ("advantage", "effect_duration", PROSE),
        (HELP_INTRO, *HELP_CHECK, HELP_ATTACK),
    ),
    (
        "help",
        "gm_final_say",
        (PROSE,),
        ("The GM has final say on whether your assistance is possible.",),
    ),
    # -- Hide (p183) --------------------------------------------------------
    (
        "hide",
        "hide_check",
        ("ability_check", PROSE),
        (
            "With the Hide action, you try to hide yourself.",
            "To do so, you must succeed on a DC 15 Dexterity (Stealth) check while you're Heavily Obscured or behind Three-Quarters Cover or Total Cover, and you must be out of any enemy's line of sight;",
        ),
    ),
    (
        "hide",
        "discern_sight",
        (PROSE,),
        ("if you can see a creature, you can discern whether it can see you.",),
    ),
    (
        "hide",
        "hidden",
        ("condition_effect", "ability_check", PROSE),
        (
            "On a successful check, you have the Invisible condition while hidden.",
            "Make note of your check's total, which is the DC for a creature to find you with a Wisdom (Perception) check.",
        ),
    ),
    (
        "hide",
        "stop_hiding",
        ("effect_termination", PROSE),
        (
            "You stop being hidden immediately after any of the following occurs: you make a sound louder than a whisper, an enemy finds you, you make an attack roll, or you cast a spell with a Verbal component.",
        ),
    ),
    # -- Influence (p184) ---------------------------------------------------
    (
        "influence",
        "urging",
        (PROSE,),
        (
            "With the Influence action, you urge a monster to do something.",
            "Describe or roleplay how you're communicating with the monster.",
            "Are you trying to deceive, intimidate, amuse, or gently persuade?",
            "The GM then determines whether the monster feels willing, unwilling, or hesitant due to your interaction; this determination establishes whether an ability check is necessary, as explained below.",
        ),
    ),
    (
        "influence",
        "willing",
        (PROSE,),
        (
            "_Willing._ If your urging aligns with the monster's desires, no ability check is necessary; the monster fulfills your request in a way it prefers.",
        ),
    ),
    (
        "influence",
        "unwilling",
        (PROSE,),
        (
            "_Unwilling._ If your urging is repugnant to the monster or counter to its alignment, no ability check is necessary; it doesn't comply.",
        ),
    ),
    (
        "influence",
        "hesitant_check",
        ("ability_check", "retry_restriction", PROSE),
        INFLUENCE_HESITANT,
    ),
    (
        "influence",
        "influence_checks",
        (PROSE,),
        (
            "The Influence Checks table suggests which ability check to make based on how you're interacting with the monster.",
            INFLUENCE_TABLE,
        ),
    ),
    # -- Magic (p185) -------------------------------------------------------
    (
        "magic",
        "magic_action",
        ("activation_cost_eligibility", PROSE),
        (
            "When you take the Magic action, you cast a spell that has a casting time of an action or use a feature or magic item that requires a Magic action to be activated.",
        ),
    ),
    (
        "magic",
        "long_casting",
        (
            "recurring_action_requirement",
            "sustained_state_requirement",
            "effect_termination",
            "resource_expenditure",
            PROSE,
        ),
        (
            "If you cast a spell that has a casting time of 1 minute or longer, you must take the Magic action on each turn of that casting, and you must maintain Concentration while you do so.",
            "If your Concentration is broken, the spell fails, but you don't expend a spell slot.",
        ),
    ),
    # -- Ready (pp186-187) --------------------------------------------------
    (
        "ready",
        "readied_reaction",
        ("action_allowance", "effect_duration", PROSE),
        (
            "You take the Ready action to wait for a particular circumstance before you act.",
            "To do so, you take this action on your turn, which lets you act by taking a Reaction before the start of your next turn.",
        ),
    ),
    (
        "ready",
        "trigger_and_response",
        (PROSE,),
        (
            "First, you decide what perceivable circumstance will trigger your Reaction.",
            "Then, you choose the action you will take in response to that trigger, or you choose to move up to your Speed in response to it.",
        ),
    ),
    (
        "ready",
        "trigger_resolution",
        ("triggered_resolution",),
        (
            "When the trigger occurs, you can either take your Reaction right after the trigger finishes or ignore the trigger.",
        ),
    ),
    (
        "ready",
        "readied_spell",
        (
            "resource_expenditure",
            "activation_cost_eligibility",
            "sustained_state_requirement",
            "effect_duration",
            PROSE,
        ),
        (
            "When you Ready a spell, you cast it as normal (expending any resources used to cast it) but hold its energy, which you release with your Reaction when the trigger occurs.",
            "To be readied, a spell must have a casting time of an action, and holding on to the spell's magic requires Concentration, which you can maintain up to the start of your next turn.",
        ),
    ),
    (
        "ready",
        "readied_spell_dissipates",
        ("effect_termination",),
        (
            "If your Concentration is broken, the spell dissipates without taking effect.",
        ),
    ),
    # -- Search (p187) ------------------------------------------------------
    (
        "search",
        "search_check",
        (PROSE,),
        (
            "When you take the Search action, you make a Wisdom check to discern something that isn't obvious.",
        ),
    ),
    (
        "search",
        "search_skills",
        (PROSE,),
        (
            "The Search table suggests which skills are applicable when you take this action, depending on what you're trying to detect.",
            SEARCH_TABLE,
        ),
    ),
    # -- Study (p189) -------------------------------------------------------
    (
        "study",
        "study_check",
        (PROSE,),
        (
            "When you take the Study action, you make an Intelligence check to study your memory, a book, a clue, or another source of knowledge and call to mind an important piece of information about it.",
        ),
    ),
    (
        "study",
        "study_skills",
        (PROSE,),
        (
            "The Areas of Knowledge table suggests which skills are applicable to various areas of knowledge.",
            STUDY_TABLE,
        ),
    ),
    # -- Unarmed Strike (p190) ----------------------------------------------
    (
        "unarmed_strike",
        "definition",
        (PROSE,),
        (
            "Instead of using a weapon to make a melee attack, you can use a punch, kick, headbutt, or similar forceful blow.",
            "In game terms, this is an Unarmed Strike—a melee attack that involves you using your body to damage, grapple, or shove a target within 5 feet of you.",
        ),
    ),
    (
        "unarmed_strike",
        "effect_choice",
        (PROSE,),
        (
            "Whenever you use your Unarmed Strike, choose one of the following options for its effect.",
        ),
    ),
    (
        "unarmed_strike",
        "damage_option",
        (PROSE,),
        (
            "_Damage._ You make an attack roll against the target.",
            "Your bonus to the roll equals your Strength modifier plus your Proficiency Bonus.",
            "On a hit, the target takes Bludgeoning damage equal to 1 plus your Strength modifier.",
        ),
    ),
    (
        "unarmed_strike",
        "grapple_option",
        ("condition_effect", PROSE),
        (
            "_Grapple._ The target must succeed on a Strength or Dexterity saving throw (it chooses which), or it has the Grappled condition.",
            "The DC for the saving throw and any escape attempts equals 8 plus your Strength modifier and Proficiency Bonus.",
            "This grapple is possible only if the target is no more than one size larger than you and if you have a hand free to grab it.",
        ),
    ),
    (
        "unarmed_strike",
        "shove_option",
        (PROSE,),
        (
            "_Shove._ The target must succeed on a Strength or Dexterity saving throw (it chooses which), or you either push it 5 feet away or cause it to have the Prone condition.",
            "The DC for the saving throw equals 8 plus your Strength modifier and Proficiency Bonus.",
            "This shove is possible only if the target is no more than one size larger than you.",
        ),
    ),
    # -- Utilize (p191) -----------------------------------------------------
    (
        "utilize",
        "object_interaction",
        (PROSE,),
        (
            "You normally interact with an object while doing something else, such as when you draw a sword as part of the Attack action.",
        ),
    ),
    (
        "utilize",
        "utilize_action",
        ("activation_cost_eligibility",),
        (
            "When an object requires an action for its use, you take the Utilize action.",
        ),
    ),
)

#: No whole-leaf framing: every non-heading leaf of these entries states a rule.
FRAMING: tuple[tuple[str, str], ...] = ()

# ---------------------------------------------------------------------------
# Representation proposed for the clauses above
# ---------------------------------------------------------------------------

C = EntryComponent


def equip_option(
    key: str, change: EquipmentChange, timing: AttackRelativeTiming
) -> ComponentOption:
    return ComponentOption(
        semantic_key=key,
        facts=(
            ActionAllowanceFact(
                1, AllowanceScope.ATTACK, activity=GrantedActivity.EQUIPMENT_CHANGE
            ),
            EquipmentChangeFact(change, timing),
        ),
    )


def assist(context: RollContext) -> tuple[AdvantageFact, EffectDurationFact]:
    return (
        AdvantageFact(
            AdvantageState.ADVANTAGE,
            RollSpec(RollActor.ALLY, context),
            use_limit=BenefitUseLimit.NEXT_QUALIFYING_ROLL,
        ),
        until_your_next_turn(),
    )


INFLUENCE_CHECK = AbilityCheckFact(
    None,
    DcKind.HIGHER_OF_FIXED_OR_TARGET_ABILITY_SCORE,
    context=RollContext.ABILITY_CHECK,
    dc_value=15,
    dc_ability=AbilityScore.INTELLIGENCE,
)
INFLUENCE_RETRY = RetryRestrictionFact(24, TimeUnit.HOUR, gamemaster_may_set_other=True)
LONG_CASTING_FAILS = EffectTerminationFact()
LONG_CASTING_SLOT_KEPT = ResourceExpenditureFact(
    ExpendableResource.SPELL_SLOT, expended=False
)

COMPONENTS: tuple[EntryComponent, ...] = (
    # Attack
    C(
        "attack",
        "attack_roll",
        M,
        CTX,
        facts=(
            ActionAllowanceFact(
                1, AllowanceScope.OWNING_EFFECT, activity=GrantedActivity.ATTACK_ROLL
            ),
        ),
        refs=(("Unarmed Strike", "unarmed_strike"),),
    ),
    C(
        "attack",
        "equip_or_unequip",
        S,
        None,
        options=(
            equip_option(
                "equip_before", EquipmentChange.EQUIP, AttackRelativeTiming.BEFORE
            ),
            equip_option(
                "equip_after", EquipmentChange.EQUIP, AttackRelativeTiming.AFTER
            ),
            equip_option(
                "unequip_before", EquipmentChange.UNEQUIP, AttackRelativeTiming.BEFORE
            ),
            equip_option(
                "unequip_after", EquipmentChange.UNEQUIP, AttackRelativeTiming.AFTER
            ),
        ),
    ),
    C("attack", "equipping_scope", P, NO_USE),
    C(
        "attack",
        "moving_between_attacks",
        M,
        CTX,
        facts=(MovementInterleaveFact(InterleavePoint.REPEATED_ATTACKS),),
    ),
    # Dash
    C(
        "dash",
        "extra_movement",
        S,
        None,
        facts=(
            MovementAllowanceFact(MovementAllowanceBasis.OWN_SPEED),
            rest_of_your_turn(),
        ),
    ),
    C(
        "dash",
        "special_speed",
        M,
        CTX,
        options=(
            ComponentOption(
                "own_speed", (MovementAllowanceFact(MovementAllowanceBasis.OWN_SPEED),)
            ),
            ComponentOption(
                "own_special_speed",
                (MovementAllowanceFact(MovementAllowanceBasis.OWN_SPECIAL_SPEED),),
            ),
        ),
    ),
    # Disengage
    C(
        "disengage",
        "no_opportunity_attacks",
        S,
        None,
        facts=(
            ReactionProvocationFact(
                TriggeredReaction.OPPORTUNITY_ATTACK, provokes=False
            ),
            rest_of_your_turn(),
        ),
    ),
    # Dodge
    C(
        "dodge",
        "dodge_benefits",
        M,
        CTX,
        facts=(
            AdvantageFact(
                AdvantageState.DISADVANTAGE,
                RollSpec(RollActor.AGAINST_SUBJECT, RollContext.ATTACK_ROLL),
            ),
            AdvantageFact(
                AdvantageState.ADVANTAGE,
                RollSpec(
                    RollActor.SUBJECT, RollContext.SAVING_THROW, AbilityScore.DEXTERITY
                ),
            ),
            until_your_next_turn(),
        ),
    ),
    C(
        "dodge",
        "benefits_lost",
        S,
        None,
        facts=(EffectTerminationFact(),),
        applies_when=Applicability(
            kind=ApplicabilityKind.ANY_OF,
            any_of_terms=(
                Applicability(
                    kind=ApplicabilityKind.QUANTITY_THRESHOLD,
                    quantity=TrackedQuantity.SPEED,
                    comparison=Comparison.EQUALS,
                    value=0,
                ),
                Applicability(
                    kind=ApplicabilityKind.CONDITION_STATE,
                    condition=ConditionKind.INCAPACITATED,
                ),
            ),
        ),
        refs=(("Incapacitated", "incapacitated"),),
    ),
    # Help
    C(
        "help",
        "assistance",
        M,
        CTX,
        options=(
            ComponentOption("assist_ability_check", assist(RollContext.ABILITY_CHECK)),
            ComponentOption("assist_attack_roll", assist(RollContext.ATTACK_ROLL)),
        ),
        option_sources=(
            ("assist_ability_check", (HELP_INTRO, *HELP_CHECK)),
            ("assist_attack_roll", (HELP_INTRO, HELP_ATTACK)),
        ),
    ),
    C("help", "gm_final_say", P, GM),
    # Hide
    C(
        "hide",
        "hide_check",
        M,
        CTX,
        facts=(
            AbilityCheckFact(
                AbilityScore.DEXTERITY,
                DcKind.FIXED,
                context=RollContext.ABILITY_CHECK,
                dc_value=15,
                skill=Skill.STEALTH,
            ),
        ),
        applies_when=Applicability(
            kind=ApplicabilityKind.ANY_OF,
            any_of_terms=(  # canonical order, not printed order
                cover(CoverDegree.THREE_QUARTERS),
                cover(CoverDegree.TOTAL),
                Applicability(
                    kind=ApplicabilityKind.OBSCUREMENT,
                    obscurement=ObscurementState.HEAVILY_OBSCURED,
                ),
            ),
        ),
    ),
    C("hide", "discern_sight", P, NO_USE),
    C(
        "hide",
        "hidden",
        M,
        CTX,
        facts=(
            ConditionEffectFact(ConditionKind.INVISIBLE, ConditionEffectKind.APPLIES),
            AbilityCheckFact(
                AbilityScore.WISDOM,
                DcKind.RECORDED_CHECK_TOTAL,
                context=RollContext.ABILITY_CHECK,
                against_subject=True,
                skill=Skill.PERCEPTION,
            ),
        ),
        applies_when=on(AutomaticOutcome.SUCCESS),
        refs=(("Invisible", "invisible"),),
    ),
    C("hide", "stop_hiding", M, CTX, facts=(EffectTerminationFact(),)),
    # Influence
    C("influence", "urging", P, GM),
    C("influence", "willing", P, FICTION),
    C("influence", "unwilling", P, SUBJ),
    C(
        "influence",
        "hesitant_check",
        M,
        GM,
        facts=(INFLUENCE_CHECK, INFLUENCE_RETRY),
        qualifiers=((INFLUENCE_RETRY, on(AutomaticOutcome.FAILURE)),),
        refs=(
            ("Indifferent", "indifferent"),
            ("Friendly", "friendly"),
            ("Hostile", "hostile"),
        ),
    ),
    C("influence", "influence_checks", P, GM),
    # Magic
    C(
        "magic",
        "magic_action",
        M,
        CTX,
        facts=(
            ActivationCostEligibilityFact(EligibilitySubject.SPELL, ActionCost.ACTION),
        ),
    ),
    # One component for the whole paragraph: the no-slot consequence holds only
    # for a casting of 1 minute or longer, and the prose names the Magic action
    # that ActionCost.ACTION alone does not.
    C(
        "magic",
        "long_casting",
        M,
        CTX,
        facts=(
            RecurringActionRequirementFact(ActionCost.ACTION, TimeUnit.TURN),
            SustainedStateRequirementFact(SustainedState.CONCENTRATION),
            LONG_CASTING_FAILS,
            LONG_CASTING_SLOT_KEPT,
        ),
        qualifiers=(
            (LONG_CASTING_FAILS, when_concentration_breaks()),
            (LONG_CASTING_SLOT_KEPT, when_concentration_breaks()),
        ),
        applies_when=Applicability(
            kind=ApplicabilityKind.SPELL_CASTING_TIME,
            casting_time=CastingTimeThreshold(1, TimeUnit.MINUTE),
        ),
    ),
    # Ready
    C(
        "ready",
        "readied_reaction",
        M,
        CTX,
        facts=(
            ActionAllowanceFact(
                1, AllowanceScope.OWNING_EFFECT, cost=ActionCost.REACTION
            ),
            until_your_next_turn(),
        ),
    ),
    C("ready", "trigger_and_response", P, CTX),
    C(
        "ready",
        "trigger_resolution",
        S,
        None,
        facts=(
            TriggeredResolutionFact(
                ResolutionTiming.IMMEDIATELY_AFTER_TRIGGER, optional=True
            ),
        ),
    ),
    C(
        "ready",
        "readied_spell",
        M,
        CTX,
        facts=(
            ResourceExpenditureFact(
                ExpendableResource.CASTING_RESOURCES, expended=True
            ),
            ActivationCostEligibilityFact(EligibilitySubject.SPELL, ActionCost.ACTION),
            SustainedStateRequirementFact(SustainedState.CONCENTRATION),
            until_your_next_turn(),
        ),
    ),
    C(
        "ready",
        "readied_spell_dissipates",
        S,
        None,
        facts=(EffectTerminationFact(),),
        applies_when=when_concentration_breaks(),
    ),
    # Search
    C("search", "search_check", P, SUBJ),
    C("search", "search_skills", P, CTX),
    # Study
    C("study", "study_check", P, OPEN),
    C("study", "study_skills", P, CTX),
    # Unarmed Strike
    C("unarmed_strike", "definition", P, NO_USE),
    C("unarmed_strike", "effect_choice", P, NO_USE),
    C("unarmed_strike", "damage_option", P, NO_USE),
    C(
        "unarmed_strike",
        "grapple_option",
        M,
        NO_USE,
        facts=(
            ConditionEffectFact(ConditionKind.GRAPPLED, ConditionEffectKind.APPLIES),
        ),
        refs=(("Grappled", "grappled"),),
    ),
    C("unarmed_strike", "shove_option", P, NO_USE, refs=(("Prone", "prone"),)),
    # Utilize
    C(
        "utilize",
        "object_interaction",
        P,
        NO_USE,
        refs=(("Attack action", "attack"),),
    ),
    C(
        "utilize",
        "utilize_action",
        S,
        None,
        facts=(
            ActivationCostEligibilityFact(EligibilitySubject.OBJECT, ActionCost.ACTION),
        ),
    ),
)

#: Supporting spans: (entry, text, component supported or ``None`` for the
#: record). Examples illustrate; *See also* pointers identify another entry.
SUPPORTING: tuple[tuple[str, str, str | None], ...] = (
    (
        "dash",
        "With a Speed of 30 feet, for example, you can move up to 60 feet on your turn if you Dash.",
        "extra_movement",
    ),
    (
        "dash",
        "If your Speed of 30 feet is reduced to 15 feet, you can move up to 30 feet this turn if you Dash.",
        "extra_movement",
    ),
    ("dash", '_See also_ "Speed."', None),
    ("magic", '_See also_ "Concentration."', None),
    (
        "ready",
        'Examples include "If the cultist steps on the\ntrapdoor, I\'ll pull the lever that opens it," and "If the zombie steps next to me, I move away."',
        "trigger_and_response",
    ),
    ("unarmed_strike", '_See also_ "Grappling."', None),
)

#: Record-owned references: (entry, printed text, target slug, texts of the
#: spans the pointer is read from).
RECORD_REFERENCES: tuple[tuple[str, str, str, tuple[str, ...]], ...] = (
    ("dash", "Speed", "speed", ('_See also_ "Speed."',)),
    ("magic", "Concentration", "concentration", ('_See also_ "Concentration."',)),
    ("unarmed_strike", "Grappling", "grappling", ('_See also_ "Grappling."',)),
)

#: Targets outside this batch that no accepted record defines yet. Named, not
#: authored: each stays an explicit unknown-target finding.
OUTSTANDING_TARGETS = ("concentration", "friendly", "hostile", "indifferent", "speed")
#: Targets outside this batch that the accepted conditions pilot defines. The
#: proposal alone reports them; composed with accepted context they resolve.
ACCEPTED_CONTEXT_TARGETS = (
    "grappled",
    "grappling",
    "incapacitated",
    "invisible",
    "prone",
)


def batch() -> EntryBatch:
    """The tables above, read at call time so tests can mutate them."""
    return EntryBatch(
        origin=ORIGIN,
        schema=(SCHEMA_15_VERSION, SCHEMA_15_HASH),
        proposal_origin=f"{ORIGIN} (CRD Issue 5d fresh actions pilot; unaccepted)",
        unit_prefix="actions-pilot",
        parent=PARENT,
        entries=ENTRIES,
        expected_leaves=49,
        clauses=CLAUSES,
        framing=FRAMING,
        components=COMPONENTS,
        supporting=SUPPORTING,
        record_references=RECORD_REFERENCES,
    )


def build(session: Session) -> Built:
    """Derive the actions-pilot proposal from the release *session* published."""
    return build_entry_batch(session, batch(), published_release_binding(session))


def expected_representation_findings() -> list[str]:
    """Exactly the out-of-batch targets, accepted-context and outstanding."""
    return unknown_target_findings(
        RECORD_REFERENCES, COMPONENTS, (*OUTSTANDING_TARGETS, *ACCEPTED_CONTEXT_TARGETS)
    )


def main(db: str) -> int:
    out = Path(__file__).resolve().parent / PROPOSAL_FILE
    return emit(db, build, out, expected_representation_findings())


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
