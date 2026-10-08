# ruff: noqa: E501  -- clause literals are verbatim source text, kept whole to be greppable
"""Author the fresh **reference-closure** proposal: 14 complete glossary entries.

REVIEW MATERIAL for CRD Issue 5d (#137) over the qualified 5c release
``9717e288-c099-5217-b2d2-f89aeabd7b73`` / ``5.2.1-corpus.883aabdf-462``. It
emits an *unaccepted* ``5d-proposal-2`` artifact. It accepts nothing, publishes
nothing, writes nothing under ``oracles/``, and imports no earlier batch's
content, identity or authority (the quarantined ``speed-1``/``attitudes-1``
batches included).

Scope: Concentration; Friendly, Hostile and Indifferent [Attitude]; Speed; the
four special speeds; and Climbing, Crawling, Flying, Jumping and Swimming -- 14
peer entries under *Rules Glossary > Rules Definitions*, 33 represented leaves,
one ``ENTRY`` review unit each. It is the five targets the accepted Conditions +
Actions composition leaves unresolved, plus Speed's own movement entries. High
Jump, Long Jump, Falling, Difficult Terrain and *Playing the Game* are outside
it; their pointers stay explicit unknown targets. Speed's *Playing the Game*
("Combat") pointer leaves the glossary: it cites the exact section ``play.combat``
in scope ``srd-5.2.1/playing-the-game``, which no batch has authored.

This file is literal review data only; the assembly is the committed shared
:mod:`afterworlds.ingestion.mechanical.authoring`. ``CLAUSES`` is the source
review; ``COMPONENTS`` is the representation proposed for it; expected rules
come from ``CLAUSES`` alone.

Authoring conventions (as the conditions and actions pilots, plus):

* A typed fact is used only where it is true under the conditions the typed
  surface states. A condition the closed vocabulary cannot state stays in the
  same component's governing prose, beside the fact it conditions -- never in a
  sibling component.
* One source statement, one typed copy: sibling components never repeat a fact.
* Terms carried by closed code-owned vocabulary (Concentration and Speed inside
  facts) are bound by that type, not by a reference. *See also* pointers, named
  conditions, named glossary terms a rule depends on, and in-batch pointers are
  references.

Run: ``python issue-5d-reference-closure-generator.py <published afterworlds.db>``
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
    unknown_target_findings,
)
from afterworlds.ingestion.mechanical.authoring import batch_findings as batch_findings
from afterworlds.ingestion.mechanical.authoring import render as render
from afterworlds.ingestion.mechanical.bound_corpus import published_release_binding
from afterworlds.ingestion.mechanical.representation import (
    AbilityCheckFact,
    AbilityScore,
    ActionCost,
    ActionEconomyFact,
    Applicability,
    ApplicabilityKind,
    Attitude,
    ComponentHandling,
    ConditionKind,
    DcKind,
    DefaultAttitudeFact,
    DistanceUnit,
    EffectTerminationFact,
    MovementAmount,
    MovementCostFact,
    MovementCostKind,
    MovementMode,
    MovementWindow,
    ParticipantRole,
    RecordKind,
    RollContext,
    Skill,
    SpecialSpeedFact,
    SpecialSpeedListing,
    SpeedChangePropagationFact,
    SpeedDefinitionFact,
    SpeedPropagationDuration,
    SpeedPropagationMagnitude,
    SpeedPropagationScope,
    SpeedSelection,
    SpeedSelectionFact,
    SpeedSwitchAccounting,
    SpeedSwitchLimitFact,
    SpeedSwitchOutcome,
    StateEffectFact,
    StateEffectKind,
    SustainedState,
    SustainedStateRequirementFact,
)
from afterworlds.ingestion.mechanical.schema_lift import (
    SCHEMA_15_HASH,
    SCHEMA_15_VERSION,
)

ORIGIN = "issue-5d-reference-closure-generator.py"
PROPOSAL_FILE = "issue-5d-reference-closure-PROPOSAL.json"
PARENT = ("Rules Glossary", "Rules Definitions")

#: (record slug, printed container label, record kind). Printed order within
#: the batch's reading order: the five closing targets, then Speed's entries.
ENTRIES: tuple[tuple[str, str, RecordKind], ...] = (
    ("concentration", "Concentration", RecordKind.GLOSSARY_RULE),
    ("friendly", "Friendly [Attitude]", RecordKind.GLOSSARY_RULE),
    ("hostile", "Hostile [Attitude]", RecordKind.GLOSSARY_RULE),
    ("indifferent", "Indifferent [Attitude]", RecordKind.GLOSSARY_RULE),
    ("speed", "Speed", RecordKind.GLOSSARY_RULE),
    ("burrow_speed", "Burrow Speed", RecordKind.GLOSSARY_RULE),
    ("climb_speed", "Climb Speed", RecordKind.GLOSSARY_RULE),
    ("fly_speed", "Fly Speed", RecordKind.GLOSSARY_RULE),
    ("swim_speed", "Swim Speed", RecordKind.GLOSSARY_RULE),
    ("climbing", "Climbing", RecordKind.GLOSSARY_RULE),
    ("crawling", "Crawling", RecordKind.GLOSSARY_RULE),
    ("flying", "Flying", RecordKind.GLOSSARY_RULE),
    ("jumping", "Jumping", RecordKind.GLOSSARY_RULE),
    ("swimming", "Swimming", RecordKind.GLOSSARY_RULE),
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


def when_concentration_breaks() -> Applicability:
    return Applicability(
        kind=ApplicabilityKind.EFFECT_STATE,
        effect_state=StateEffectKind.CONCENTRATION_BROKEN,
    )


def extra_foot_per_foot() -> MovementCostFact:
    """*"each foot of movement costs 1 extra foot"*, charged to the mover."""
    return MovementCostFact(
        MovementCostKind.PER_FOOT_SURCHARGE,
        MovementAmount.FEET,
        payer=ParticipantRole.SUBJECT,
        feet=1,
    )


def dc15_athletics() -> AbilityCheckFact:
    return AbilityCheckFact(
        AbilityScore.STRENGTH,
        DcKind.FIXED,
        context=RollContext.ABILITY_CHECK,
        dc_value=15,
        skill=Skill.ATHLETICS,
    )


# ---------------------------------------------------------------------------
# Source review: what each printed clause must be read as
# ---------------------------------------------------------------------------

BREAK_FACTORS = "The following factors break Concentration."

#: (entry, component key, expected fact families + ``None`` for governing
#: prose, clause texts). Every rule-stating sentence of the batch is named here.
CLAUSES: tuple[tuple[str, str, tuple[str | None, ...], tuple[str, ...]], ...] = (
    # -- Concentration (p179) -----------------------------------------------
    (
        "concentration",
        "concentration_effects",
        ("sustained_state_requirement", "effect_termination", PROSE),
        (
            "Some spells and other effects require Concentration to remain active, as specified in their descriptions.",
            "If the effect's creator loses Concentration, the effect ends.",
        ),
    ),
    (
        "concentration",
        "maximum_duration",
        (PROSE,),
        (
            "If the effect has a maximum duration, the effect's description specifies how long the creator can concentrate on it: up to 1 minute, 1 hour, or some other duration.",
        ),
    ),
    (
        "concentration",
        "end_at_will",
        ("action_economy", PROSE),
        ("The creator can end Concentration at any time (no action required).",),
    ),
    (
        "concentration",
        "another_concentration_effect",
        (PROSE,),
        (
            "_Another Concentration Effect._ You lose Concentration on an effect the moment you start casting a spell that requires Concentration or activate another effect that requires Concentration.",
        ),
    ),
    (
        "concentration",
        "damage",
        (PROSE,),
        (
            "_Damage._ If you take damage, you must succeed on a Constitution saving throw to maintain Concentration.",
            "The DC equals 10 or half the damage taken (round down), whichever number is higher, up to a maximum DC of 30.",
        ),
    ),
    (
        "concentration",
        "incapacitated_or_dead",
        ("state_effect",),
        (
            "_Incapacitated or Dead._ Your Concentration ends if you have the Incapacitated condition or you die.",
        ),
    ),
    # -- Friendly [Attitude] (p182) -----------------------------------------
    (
        "friendly",
        "disposition",
        (PROSE,),
        ("A Friendly creature views you favorably.",),
    ),
    (
        "friendly",
        "influence_advantage",
        (PROSE,),
        ("You have Advantage on an ability check to influence a Friendly creature.",),
    ),
    # -- Hostile [Attitude] (p183) ------------------------------------------
    (
        "hostile",
        "disposition",
        (PROSE,),
        ("A Hostile creature views you unfavorably.",),
    ),
    (
        "hostile",
        "influence_disadvantage",
        (PROSE,),
        ("You have Disadvantage on an ability check to influence a Hostile creature.",),
    ),
    # -- Indifferent [Attitude] (p184) --------------------------------------
    (
        "indifferent",
        "disposition",
        (PROSE,),
        ("An Indifferent creature has no desire to help or hinder you.",),
    ),
    (
        "indifferent",
        "default_attitude",
        ("default_attitude",),
        ("Indifferent is the default attitude of a monster.",),
    ),
    # -- Speed (p188) -------------------------------------------------------
    (
        "speed",
        "definition",
        ("speed_definition",),
        (
            "A creature has a Speed, which is the distance in feet the creature can cover when it moves on its turn.",
        ),
    ),
    (
        "speed",
        "special_speeds",
        ("special_speed",),
        (
            "_Special Speeds._ Some creatures have special speeds, such as a Burrow Speed, Climb Speed, Fly Speed, or Swim Speed, each of which is defined in this glossary.",
        ),
    ),
    (
        "speed",
        "speed_selection",
        ("speed_selection",),
        (
            "If you have more than one speed, choose which one to use when you move; you can switch between the speeds during your move.",
        ),
    ),
    (
        "speed",
        "switching",
        ("speed_switch_limit",),
        (
            "Whenever you switch, subtract the distance already moved from the new speed.",
            "The result determines how much farther you can move.",
            "If the result is 0 or less, you can't use the new speed during the current move.",
        ),
    ),
    (
        "speed",
        "changes_propagate",
        ("speed_change_propagation",),
        (
            "_Changes to Your Speeds._ If an effect increases or decreases your Speed for a time, any special speed you have increases or decreases by an equal amount for the same duration.",
        ),
    ),
    # -- Burrow Speed (p178) ------------------------------------------------
    (
        "burrow_speed",
        "burrowing",
        (PROSE,),
        (
            "A creature that has a Burrow Speed can use that speed to move through sand, earth, mud, or ice.",
            "The creature can't burrow through solid rock unless the creature has a trait that allows it to do so.",
        ),
    ),
    # -- Climb Speed (p179) -------------------------------------------------
    (
        "climb_speed",
        "climb_speed_use",
        (PROSE,),
        (
            "A Climb Speed can be used in place of Speed to traverse a vertical surface without expending the extra movement normally associated with climbing.",
        ),
    ),
    # -- Fly Speed (p182) ---------------------------------------------------
    (
        "fly_speed",
        "fly_speed_use",
        (PROSE,),
        (
            "A Fly Speed can be used to travel through the air.",
            "While you have a Fly Speed, you can stay aloft until you land, fall, or die.",
        ),
    ),
    # -- Swim Speed (p189) --------------------------------------------------
    (
        "swim_speed",
        "swim_speed_use",
        (PROSE,),
        (
            "A Swim Speed can be used to swim without expending the extra movement normally associated with swimming.",
        ),
    ),
    # -- Climbing (p178) ----------------------------------------------------
    (
        "climbing",
        "extra_cost",
        ("movement_cost", PROSE),
        (
            "While you're climbing, each foot of movement costs 1 extra foot (2 extra feet in Difficult Terrain).",
            "You ignore this extra cost if you have a Climb Speed and use it to climb.",
        ),
    ),
    (
        "climbing",
        "difficult_climb",
        ("ability_check", PROSE),
        (
            "At the GM's option, climbing a slippery surface or one with few handholds might require a successful DC 15 Strength (Athletics) check.",
        ),
    ),
    # -- Crawling (p179) ----------------------------------------------------
    (
        "crawling",
        "extra_cost",
        ("movement_cost", PROSE),
        (
            "While you're crawling, each foot of movement costs 1 extra foot (2 extra feet in Difficult Terrain).",
        ),
    ),
    # -- Flying (p182) ------------------------------------------------------
    (
        "flying",
        "falling",
        (PROSE,),
        (
            "While flying, you fall if you have the Incapacitated or Prone condition or your Fly Speed is reduced to 0.",
            "You can stay aloft in those circumstances if you can hover.",
        ),
    ),
    # -- Jumping (p184) -----------------------------------------------------
    (
        "jumping",
        "jump_kinds",
        (PROSE,),
        (
            "When you jump, you make either a Long Jump (horizontal) or a High Jump (vertical).",
        ),
    ),
    # -- Swimming (p189) ----------------------------------------------------
    (
        "swimming",
        "extra_cost",
        ("movement_cost", PROSE),
        (
            "While you're swimming, each foot of movement costs 1 extra foot (2 extra feet in Difficult Terrain).",
            "You ignore this extra cost if you have a Swim Speed and use it to swim.",
        ),
    ),
    (
        "swimming",
        "rough_water",
        ("ability_check", PROSE),
        (
            "At the GM's option, moving any distance in rough water might require a successful DC 15 Strength (Athletics) check.",
        ),
    ),
)

#: No whole-leaf framing: every non-heading leaf of these entries states a rule.
FRAMING: tuple[tuple[str, str], ...] = ()

# ---------------------------------------------------------------------------
# Representation proposed for the clauses above
# ---------------------------------------------------------------------------

C = EntryComponent

CONCENTRATION_EFFECT_ENDS = EffectTerminationFact()

COMPONENTS: tuple[EntryComponent, ...] = (
    # Concentration. One typed copy per statement: the effect ending rides a
    # qualifier here, and only the Incapacitated/Dead factor -- the one whose
    # trigger the closed vocabulary states completely -- types the break.
    C(
        "concentration",
        "concentration_effects",
        M,
        NO_USE,
        facts=(
            SustainedStateRequirementFact(SustainedState.CONCENTRATION),
            CONCENTRATION_EFFECT_ENDS,
        ),
        qualifiers=((CONCENTRATION_EFFECT_ENDS, when_concentration_breaks()),),
    ),
    C("concentration", "maximum_duration", P, NO_USE),
    C(
        "concentration",
        "end_at_will",
        M,
        NO_USE,
        facts=(ActionEconomyFact(ActionCost.NONE),),
    ),
    # The trigger is the start of a casting or an activation; no applicability
    # states it, so the break stays wholly in this prose.
    C("concentration", "another_concentration_effect", P, NO_USE),
    # The save and its DC formula (10 or half the damage, round down, max 30)
    # are exact governing prose; no DcKind states the formula and no approved
    # operation names it as a separate Rules-Package field (see the packet).
    C("concentration", "damage", P, NO_USE),
    C(
        "concentration",
        "incapacitated_or_dead",
        S,
        None,
        facts=(StateEffectFact(StateEffectKind.CONCENTRATION_BROKEN),),
        applies_when=Applicability(
            kind=ApplicabilityKind.ANY_OF,
            any_of_terms=(
                Applicability(
                    kind=ApplicabilityKind.CONDITION_STATE,
                    condition=ConditionKind.INCAPACITATED,
                ),
                Applicability(
                    kind=ApplicabilityKind.EFFECT_STATE,
                    effect_state=StateEffectKind.DIES,
                ),
            ),
        ),
        refs=(("Incapacitated", "incapacitated"),),
    ),
    # Attitudes. The bias holds only for a check "to influence" that creature,
    # which no roll or applicability vocabulary states; an AdvantageFact would
    # read as a bias on every ability check. Prose, as the accepted Charmed
    # "Social Advantage" clause is.
    C("friendly", "disposition", P, NO_USE),
    C("friendly", "influence_advantage", P, CTX),
    C("hostile", "disposition", P, NO_USE),
    C("hostile", "influence_disadvantage", P, CTX),
    C("indifferent", "disposition", P, NO_USE),
    C(
        "indifferent",
        "default_attitude",
        S,
        None,
        facts=(DefaultAttitudeFact(Attitude.INDIFFERENT),),
    ),
    # Speed
    C(
        "speed",
        "definition",
        S,
        None,
        facts=(SpeedDefinitionFact(DistanceUnit.FOOT, MovementWindow.OWN_TURN),),
    ),
    C(
        "speed",
        "special_speeds",
        S,
        None,
        facts=tuple(
            SpecialSpeedFact(mode, SpecialSpeedListing.NAMED_IN_A_NON_EXHAUSTIVE_LIST)
            for mode in (
                MovementMode.BURROW,
                MovementMode.CLIMB,
                MovementMode.FLY,
                MovementMode.SWIM,
            )
        ),
        refs=(
            ("Burrow Speed", "burrow_speed"),
            ("Climb Speed", "climb_speed"),
            ("Fly Speed", "fly_speed"),
            ("Swim Speed", "swim_speed"),
        ),
    ),
    C(
        "speed",
        "speed_selection",
        S,
        None,
        facts=(
            SpeedSelectionFact(SpeedSelection.CHOOSE_BEFORE_MOVING),
            SpeedSelectionFact(SpeedSelection.SWITCH_DURING_MOVE),
        ),
    ),
    C(
        "speed",
        "switching",
        S,
        None,
        facts=(
            SpeedSwitchLimitFact(
                SpeedSwitchAccounting.SUBTRACT_DISTANCE_ALREADY_MOVED,
                SpeedSwitchOutcome.FORBIDS_USING_THE_NEW_SPEED,
            ),
        ),
    ),
    C(
        "speed",
        "changes_propagate",
        S,
        None,
        facts=(
            SpeedChangePropagationFact(
                SpeedPropagationScope.EVERY_SPECIAL_SPEED,
                SpeedPropagationMagnitude.EQUAL_AMOUNT,
                SpeedPropagationDuration.SAME_DURATION,
            ),
        ),
    ),
    # Special speeds: each permission is bounded by what the source prints
    # beside it (material, solid rock and a trait; a vertical surface; staying
    # aloft until landing, falling or dying), so each entry is one prose unit.
    C("burrow_speed", "burrowing", P, NO_USE),
    C("climb_speed", "climb_speed_use", P, NO_USE),
    C("fly_speed", "fly_speed_use", P, NO_USE),
    C("swim_speed", "swim_speed_use", P, NO_USE),
    # Movement entries. The surcharge and everything that changes it --
    # Difficult Terrain and using a Climb/Swim Speed -- are one component, so
    # the exceptions govern the fact they qualify.
    C(
        "climbing",
        "extra_cost",
        M,
        NO_USE,
        facts=(extra_foot_per_foot(),),
        refs=(
            ("Difficult Terrain", "difficult_terrain"),
            ("Climb Speed", "climb_speed"),
        ),
    ),
    C("climbing", "difficult_climb", M, GM, facts=(dc15_athletics(),)),
    C(
        "crawling",
        "extra_cost",
        M,
        NO_USE,
        facts=(extra_foot_per_foot(),),
        refs=(("Difficult Terrain", "difficult_terrain"),),
    ),
    C(
        "flying",
        "falling",
        P,
        NO_USE,
        refs=(
            ("Incapacitated", "incapacitated"),
            ("Prone", "prone"),
            ("Fly Speed", "fly_speed"),
        ),
    ),
    C(
        "jumping",
        "jump_kinds",
        P,
        NO_USE,
        refs=(("Long Jump", "long_jump"), ("High Jump", "high_jump")),
    ),
    C(
        "swimming",
        "extra_cost",
        M,
        NO_USE,
        facts=(extra_foot_per_foot(),),
        refs=(
            ("Difficult Terrain", "difficult_terrain"),
            ("Swim Speed", "swim_speed"),
        ),
    ),
    C("swimming", "rough_water", M, GM, facts=(dc15_athletics(),)),
)

#: Supporting spans: (entry, text, component supported or ``None`` for the
#: record). Examples illustrate; *See also* pointers identify another entry;
#: a list lead scopes the items it introduces.
SUPPORTING: tuple[tuple[str, str, str | None], ...] = (
    ("concentration", BREAK_FACTORS, "another_concentration_effect"),
    ("concentration", BREAK_FACTORS, "damage"),
    ("concentration", BREAK_FACTORS, "incapacitated_or_dead"),
    ("friendly", '_See also_ "Influence."', None),
    ("hostile", '_See also_ "Influence."', None),
    ("indifferent", '_See also_ "Influence."', None),
    (
        "speed",
        '_See also_ "Climbing," "Crawling," "Flying," "Jumping," "Swimming" and "Playing the Game" ("Combat").',
        None,
    ),
    (
        "speed",
        "For example, if you have a Speed of 30 and a Fly Speed of 40, you could fly 10 feet, walk 10 feet, and leap into the air to fly 20 feet more.",
        "switching",
    ),
    (
        "speed",
        "For example, if your Speed is reduced to 0 and you have a Climb Speed, your Climb Speed is also reduced to 0.",
        "changes_propagate",
    ),
    (
        "speed",
        "Similarly, if your Speed is halved and you have a Fly Speed, your Fly Speed is also halved.",
        "changes_propagate",
    ),
    ("burrow_speed", '_See also_ "Speed."', None),
    ("climb_speed", '_See also_ "Climbing" and "Speed."', None),
    ("fly_speed", '_See also_ "Flying" and "Speed."', None),
    ("swim_speed", '_See also_ "Swimming" and "Speed."', None),
    ("crawling", '_See also_ "Speed."', None),
    ("flying", "A variety of effects allow a creature to fly.", "falling"),
    ("flying", '_See also_ "Falling" and "Fly Speed."', None),
    ("jumping", '_See also_ "Long Jump" and "High Jump."', None),
)

SPEED_SEE_ALSO = '_See also_ "Climbing," "Crawling," "Flying," "Jumping," "Swimming" and "Playing the Game" ("Combat").'

#: The exact out-of-glossary destination of Speed's "Playing the Game"
#: ("Combat") pointer. Its printed text is the section name: the chapter is the
#: scope, and many glossary entries cite other sections of the same chapter.
PLAY_COMBAT = ("srd-5.2.1/playing-the-game", "play.combat")

#: Record-owned references: (entry, printed text, target, texts of the spans the
#: pointer is read from).
RECORD_REFERENCES: tuple[RecordReference, ...] = (
    ("friendly", "Influence", "influence", ('_See also_ "Influence."',)),
    ("hostile", "Influence", "influence", ('_See also_ "Influence."',)),
    ("indifferent", "Influence", "influence", ('_See also_ "Influence."',)),
    ("speed", "Climbing", "climbing", (SPEED_SEE_ALSO,)),
    ("speed", "Crawling", "crawling", (SPEED_SEE_ALSO,)),
    ("speed", "Flying", "flying", (SPEED_SEE_ALSO,)),
    ("speed", "Jumping", "jumping", (SPEED_SEE_ALSO,)),
    ("speed", "Swimming", "swimming", (SPEED_SEE_ALSO,)),
    ("speed", "Combat", PLAY_COMBAT, (SPEED_SEE_ALSO,)),
    ("burrow_speed", "Speed", "speed", ('_See also_ "Speed."',)),
    ("climb_speed", "Climbing", "climbing", ('_See also_ "Climbing" and "Speed."',)),
    ("climb_speed", "Speed", "speed", ('_See also_ "Climbing" and "Speed."',)),
    ("fly_speed", "Flying", "flying", ('_See also_ "Flying" and "Speed."',)),
    ("fly_speed", "Speed", "speed", ('_See also_ "Flying" and "Speed."',)),
    ("swim_speed", "Swimming", "swimming", ('_See also_ "Swimming" and "Speed."',)),
    ("swim_speed", "Speed", "speed", ('_See also_ "Swimming" and "Speed."',)),
    ("crawling", "Speed", "speed", ('_See also_ "Speed."',)),
    ("flying", "Falling", "falling", ('_See also_ "Falling" and "Fly Speed."',)),
    ("flying", "Fly Speed", "fly_speed", ('_See also_ "Falling" and "Fly Speed."',)),
    ("jumping", "Long Jump", "long_jump", ('_See also_ "Long Jump" and "High Jump."',)),
    ("jumping", "High Jump", "high_jump", ('_See also_ "Long Jump" and "High Jump."',)),
)

#: Targets outside this batch that no accepted record defines. Named, not
#: authored: each stays an explicit unknown-target finding, composed or not.
OUTSTANDING_TARGETS: tuple[Target, ...] = (
    "difficult_terrain",
    "falling",
    "high_jump",
    "long_jump",
    PLAY_COMBAT,
)
#: Targets outside this batch that the accepted Conditions + Actions inputs
#: define. The proposal alone reports them; composed with them they resolve.
ACCEPTED_CONTEXT_TARGETS = ("incapacitated", "influence", "prone")


def batch() -> EntryBatch:
    """The tables above, read at call time so tests can mutate them."""
    return EntryBatch(
        origin=ORIGIN,
        schema=(SCHEMA_15_VERSION, SCHEMA_15_HASH),
        proposal_origin=f"{ORIGIN} (CRD Issue 5d fresh reference-closure batch; unaccepted)",
        unit_prefix="reference-closure",
        parent=PARENT,
        entries=ENTRIES,
        expected_leaves=33,
        clauses=CLAUSES,
        framing=FRAMING,
        components=COMPONENTS,
        supporting=SUPPORTING,
        record_references=RECORD_REFERENCES,
    )


def build(session: Session) -> Built:
    """Derive the reference-closure proposal from the release *session* published."""
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
