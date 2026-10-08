# ruff: noqa: E501  -- clause literals are verbatim source text, kept whole to be greppable
"""Author the fresh **movement-closure** proposal: 5 complete glossary entries.

REVIEW MATERIAL for CRD Issue 5d (#137) over the qualified 5c release
``9717e288-c099-5217-b2d2-f89aeabd7b73`` / ``5.2.1-corpus.883aabdf-462``. It
emits an *unaccepted* ``5d-proposal-2`` artifact. It accepts nothing, publishes
nothing, writes nothing under ``oracles/``, and imports no earlier batch's
content, identity or authority (the quarantined ``hazards-1`` batch included:
Falling is read afresh from the release and the PDF).

Scope: Difficult Terrain, Falling [Hazard], High Jump, Hover and Long Jump --
five peer entries under *Rules Glossary > Rules Definitions*, 16 leaves (five of
them headings), one ``ENTRY`` review unit each. They are the four glossary
targets the accepted 44-entry composition leaves unresolved, plus Hover, which
Flying's "if you can hover" depends on. *Playing the Game* ("Combat") stays out
of scope and unresolved; nothing here points at it or at any new target.

This file is literal review data only; the assembly is the committed shared
:mod:`afterworlds.ingestion.mechanical.authoring`. ``CLAUSES`` is the source
review; ``COMPONENTS`` is the representation proposed for it; expected rules
come from ``CLAUSES`` alone.

Authoring conventions (as the accepted batches):

* A typed fact is used only where it is true under the conditions the typed
  surface states. A condition the closed vocabulary cannot state stays in the
  same component's governing prose, beside the fact it conditions.
* One source statement, one typed copy.
* Terms carried by closed code-owned vocabulary (Reaction, Bludgeoning,
  Strength/Dexterity and their skills) are bound by that type, not by a
  reference. *See also* pointers, named conditions and in-batch glossary terms
  a rule depends on are references. Generic nouns the accepted batches leave
  unreferenced stay so here: "ally" (Help), "Tiny" (Grappled), "stat blocks"
  (Grappling).

Run: ``python issue-5d-movement-closure-generator.py <published afterworlds.db>``
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
    AutomaticOutcome,
    ComponentHandling,
    ConditionEffectFact,
    ConditionEffectKind,
    ConditionKind,
    DamageFact,
    DamageInterval,
    DamageModDirection,
    DamageModificationFact,
    DamageOutcome,
    DamageType,
    DcKind,
    DiceExpression,
    DieSize,
    DistanceUnit,
    MovementAmount,
    MovementCostFact,
    MovementCostKind,
    ParticipantRole,
    Rational,
    RecordKind,
    RollActor,
    RollContext,
    RollSpec,
    ScalingBasis,
    Skill,
)
from afterworlds.ingestion.mechanical.schema_lift import (
    SCHEMA_15_HASH,
    SCHEMA_15_VERSION,
)

ORIGIN = "issue-5d-movement-closure-generator.py"
PROPOSAL_FILE = "issue-5d-movement-closure-PROPOSAL.json"
PARENT = ("Rules Glossary", "Rules Definitions")

#: (record slug, printed container label, record kind), in printed order.
ENTRIES: tuple[tuple[str, str, RecordKind], ...] = (
    ("difficult_terrain", "Difficult Terrain", RecordKind.GLOSSARY_RULE),
    ("falling", "Falling [Hazard]", RecordKind.GLOSSARY_RULE),
    ("high_jump", "High Jump", RecordKind.GLOSSARY_RULE),
    ("hover", "Hover", RecordKind.GLOSSARY_RULE),
    ("long_jump", "Long Jump", RecordKind.GLOSSARY_RULE),
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


def check(
    ability: AbilityScore, skill: Skill, dc: int, *alternatives: RollSpec
) -> AbilityCheckFact:
    return AbilityCheckFact(
        ability,
        DcKind.FIXED,
        context=RollContext.ABILITY_CHECK,
        dc_value=dc,
        skill=skill,
        alternatives=alternatives,
    )


def roll(ability: AbilityScore, skill: Skill) -> RollSpec:
    return RollSpec(RollActor.SUBJECT, RollContext.ABILITY_CHECK, ability, skill)


def on(outcome: AutomaticOutcome) -> Applicability:
    return Applicability(kind=ApplicabilityKind.ROLL_OUTCOME, outcome=outcome)


def prone() -> ConditionEffectFact:
    return ConditionEffectFact(ConditionKind.PRONE, ConditionEffectKind.APPLIES)


# ---------------------------------------------------------------------------
# Source review: what each printed clause must be read as
# ---------------------------------------------------------------------------

#: The lead states the open-ended rule ("or something similar"), so it is
#: governing, not a supporting list lead; each item keeps its printed bullet.
DIFFICULT_SPACES = (
    "A space is Difficult Terrain if the space contains any of the following or something similar:",
    "- A creature that isn't Tiny or your ally",
    "- Furniture that is sized for creatures of your size or larger",
    "- Heavy snow, ice, rubble, or undergrowth",
    "- Liquid that's between shin- and waist-deep",
    "- A narrow opening sized for a creature one size smaller than you",
    "- A slope of 20 degrees or more",
)

#: (entry, component key, expected fact families + ``None`` for governing
#: prose, clause texts). Every rule-stating sentence of the batch is named here.
CLAUSES: tuple[tuple[str, str, tuple[str | None, ...], tuple[str, ...]], ...] = (
    # -- Difficult Terrain (p181) -------------------------------------------
    (
        "difficult_terrain",
        "extra_cost",
        ("movement_cost", PROSE),
        (
            "If a space is Difficult Terrain, every foot of movement in that space costs 1 extra foot.",
            "Difficult Terrain isn't cumulative; either a space is Difficult Terrain or it isn't.",
        ),
    ),
    ("difficult_terrain", "difficult_spaces", (PROSE,), DIFFICULT_SPACES),
    # -- Falling [Hazard] (p182) --------------------------------------------
    (
        "falling",
        "fall_damage",
        ("damage", PROSE),
        (
            "A creature that falls takes 1d6 Bludgeoning damage at the end of the fall for every 10 feet it fell, to a maximum of 20d6.",
        ),
    ),
    (
        "falling",
        "prone_on_landing",
        ("condition_effect", PROSE),
        (
            "When the creature lands, it has the Prone condition unless it avoids taking any damage from the fall.",
        ),
    ),
    (
        "falling",
        "falling_into_liquid",
        ("action_economy", "ability_check", "damage_modification", PROSE),
        (
            "A creature that falls into water or another liquid can use its Reaction to make a DC 15 Strength (Athletics) or Dexterity (Acrobatics) check to hit the surface head or feet first.",
            "On a successful check, any damage resulting from the fall is halved.",
        ),
    ),
    # -- High Jump (p183) ---------------------------------------------------
    (
        "high_jump",
        "jump_height",
        (PROSE,),
        (
            "When you make a High Jump, you leap into the air a number of feet equal to 3 plus your Strength modifier (minimum of 0 feet) if you move at least 10 feet on foot immediately before the jump.",
            "When you make a standing High Jump, you can jump only half that distance.",
            "Either way, each foot of the jump costs a foot of movement.",
        ),
    ),
    (
        "high_jump",
        "reach",
        (PROSE,),
        (
            "You can extend your arms half your height above yourself during the jump.",
            "Thus, you can reach a distance equal to the height of the jump plus 1½ times your height.",
        ),
    ),
    # -- Hover (p183) -------------------------------------------------------
    (
        "hover",
        "hovering",
        (PROSE,),
        (
            "Some creatures can hover, as noted in their stat blocks, and some spells and other effects grant the ability to hover.",
            "Hovering while flying prevents you from falling in certain circumstances.",
        ),
    ),
    # -- Long Jump (pp184-185) ----------------------------------------------
    (
        "long_jump",
        "jump_distance",
        (PROSE,),
        (
            # The line break is the release's own: the pinned Markdown wraps here.
            "When you make a Long Jump, you leap horizontally a number of feet up to your Strength score if you\nmove at least 10 feet immediately before the jump.",
            "When you make a standing Long Jump, you can leap only half that distance.",
            "Either way, each foot you jump costs a foot of movement.",
        ),
    ),
    (
        "long_jump",
        "difficult_landing",
        ("ability_check", "condition_effect", PROSE),
        (
            "If you land in Difficult Terrain, you must succeed on a DC 10 Dexterity (Acrobatics) check or have the Prone condition.",
        ),
    ),
    (
        "long_jump",
        "low_obstacle",
        ("ability_check", PROSE),
        (
            "This Long Jump rule assumes that the height of the jump doesn't matter, such as a jump across a stream or chasm.",
            "At your GM's option, you must succeed on a DC 10 Strength (Athletics) check to clear a low obstacle (no taller than a quarter of the jump's distance), such as a hedge or low wall.",
            "Otherwise, you hit the obstacle.",
        ),
    ),
)

#: No whole-leaf framing: every non-heading leaf of these entries states a rule.
FRAMING: tuple[tuple[str, str], ...] = ()

# ---------------------------------------------------------------------------
# Representation proposed for the clauses above
# ---------------------------------------------------------------------------

C = EntryComponent

FALL_HALVED = DamageModificationFact(DamageModDirection.REDUCE, Rational(1, 2))
LANDING_PRONE = prone()

COMPONENTS: tuple[EntryComponent, ...] = (
    # Difficult Terrain. The noncumulative rule limits this same surcharge, so
    # it is the surcharge's own prose (NO_USE, as the accepted Climbing,
    # Crawling and Swimming surcharges); which spaces qualify is the sibling.
    C(
        "difficult_terrain",
        "extra_cost",
        M,
        NO_USE,
        facts=(
            MovementCostFact(
                MovementCostKind.PER_FOOT_SURCHARGE,
                MovementAmount.FEET,
                payer=ParticipantRole.SUBJECT,
                feet=1,
            ),
        ),
    ),
    # The list is open-ended ("or something similar") and judged against the
    # fiction; its lead and every item are one prose unit.
    C("difficult_terrain", "difficult_spaces", P, CTX),
    # Falling. The per-interval amount and its ceiling are the damage family's
    # own fields; the end-of-fall timing has no carrier and stays its prose.
    C(
        "falling",
        "fall_damage",
        M,
        NO_USE,
        facts=(
            DamageFact(
                DamageType.BLUDGEONING,
                dice=DiceExpression(1, DieSize.D6),
                maximum_dice=20,
                per=DamageInterval(ScalingBasis.DISTANCE_FALLEN, 10, DistanceUnit.FOOT),
            ),
        ),
    ),
    # "unless it avoids taking any damage from the fall" governs the Prone
    # consequence as the component's own applicability; the landing moment and
    # "from the fall" stay its prose.
    C(
        "falling",
        "prone_on_landing",
        M,
        NO_USE,
        facts=(LANDING_PRONE,),
        applies_when=Applicability(
            kind=ApplicabilityKind.DAMAGE_OUTCOME,
            damage_outcome=DamageOutcome.ANY_DAMAGE,
        ),
        refs=(("Prone", "prone"),),
    ),
    # The trigger (falling into a liquid) is fiction; the Reaction, the one DC
    # with its closed pair of checks, and the halving on success are typed, and
    # the halving answers to that one check.
    C(
        "falling",
        "falling_into_liquid",
        M,
        CTX,
        facts=(
            ActionEconomyFact(ActionCost.REACTION),
            check(
                AbilityScore.STRENGTH,
                Skill.ATHLETICS,
                15,
                # The closed choice, in the type's canonical (payload) order.
                roll(AbilityScore.DEXTERITY, Skill.ACROBATICS),
                roll(AbilityScore.STRENGTH, Skill.ATHLETICS),
            ),
            FALL_HALVED,
        ),
        qualifiers=((FALL_HALVED, on(AutomaticOutcome.SUCCESS)),),
    ),
    # Jumps. The distance formulas (3 + Strength modifier, minimum 0; up to the
    # Strength score), the running prerequisite, the standing halving and the
    # one-for-one cost have no faithful family: DerivedQuantityFact derives a
    # time, and MovementCostFact states a surcharge or a lump expenditure, not
    # an ordinary per-foot spend. Each is one prose unit with its conditions.
    C("high_jump", "jump_height", P, NO_USE),
    C("high_jump", "reach", P, NO_USE),
    C("hover", "hovering", P, CTX),
    C("long_jump", "jump_distance", P, NO_USE),
    # Landing in Difficult Terrain is fiction and stays prose; the check and
    # the Prone consequence of failing it are typed, the consequence qualified
    # by the check's failure.
    C(
        "long_jump",
        "difficult_landing",
        M,
        CTX,
        facts=(check(AbilityScore.DEXTERITY, Skill.ACROBATICS, 10), LANDING_PRONE),
        qualifiers=((LANDING_PRONE, on(AutomaticOutcome.FAILURE)),),
        refs=(("Difficult Terrain", "difficult_terrain"), ("Prone", "prone")),
    ),
    # The height assumption scopes the GM's option; "hit the obstacle" is a
    # fiction consequence with no carrier. Both stay beside the typed check.
    C(
        "long_jump",
        "low_obstacle",
        M,
        GM,
        facts=(check(AbilityScore.STRENGTH, Skill.ATHLETICS, 10),),
    ),
)

#: Supporting spans: (entry, text, component supported or ``None`` for the
#: record). Examples illustrate; *See also* pointers identify another entry.
SUPPORTING: tuple[tuple[str, str, str | None], ...] = (
    (
        "difficult_terrain",
        "For example, moving 5 feet through Difficult Terrain costs 10 feet of movement.",
        "extra_cost",
    ),
    ("hover", '_See also_ "Flying."', None),
)

#: Record-owned references: (entry, printed text, target, texts of the spans the
#: pointer is read from).
RECORD_REFERENCES: tuple[RecordReference, ...] = (
    ("hover", "Flying", "flying", ('_See also_ "Flying."',)),
)

#: Targets outside this batch that no accepted record defines: none. The batch
#: adds no new dependency; Playing the Game ("Combat") is not cited here.
OUTSTANDING_TARGETS: tuple[Target, ...] = ()
#: Targets outside this batch that the accepted 44-entry inputs define. The
#: proposal alone reports them; composed with them they resolve.
ACCEPTED_CONTEXT_TARGETS = ("flying", "prone")


def batch() -> EntryBatch:
    """The tables above, read at call time so tests can mutate them."""
    return EntryBatch(
        origin=ORIGIN,
        schema=(SCHEMA_15_VERSION, SCHEMA_15_HASH),
        proposal_origin=f"{ORIGIN} (CRD Issue 5d fresh movement-closure batch; unaccepted)",
        unit_prefix="movement-closure",
        parent=PARENT,
        entries=ENTRIES,
        expected_leaves=16,
        clauses=CLAUSES,
        framing=FRAMING,
        components=COMPONENTS,
        supporting=SUPPORTING,
        record_references=RECORD_REFERENCES,
    )


def build(session: Session) -> Built:
    """Derive the movement-closure proposal from the release *session* published."""
    return build_entry_batch(session, batch(), published_release_binding(session))


def expected_representation_findings() -> list[str]:
    """Exactly the out-of-batch targets the accepted inputs define."""
    return unknown_target_findings(
        RECORD_REFERENCES, COMPONENTS, (*OUTSTANDING_TARGETS, *ACCEPTED_CONTEXT_TARGETS)
    )


def main(db: str) -> int:
    out = Path(__file__).resolve().parent / PROPOSAL_FILE
    return emit(db, build, out, expected_representation_findings())


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
