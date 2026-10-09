# ruff: noqa: E501  -- clause literals are verbatim source text, kept whole to be greppable
"""Author the fresh **conditions-pilot** proposal: Rules Glossary > Conditions.

REVIEW MATERIAL for CRD Issue 5d (#137) over the qualified 5c release
``9717e288-c099-5217-b2d2-f89aeabd7b73`` / ``5.2.1-corpus.883aabdf-462``. It
emits an *unaccepted* ``5d-proposal-2`` artifact. It accepts nothing, publishes
nothing, writes nothing under ``oracles/``, and imports no earlier batch's
content, identity or authority.

Scope: the fifteen ``[Condition]`` glossary entries plus ``Condition`` (the
index) and ``Grappling`` -- 17 peer entries under *Rules Glossary > Rules
Definitions*, 87 represented leaves, one ``ENTRY`` review unit each.

Everything below is literal review data plus committed shared tooling
(``published_release_binding``, ``load_bound_corpus``, ``leaves_under``,
``unique_chunk_range``, ``seed_proposal``, ``locate_span``,
``validate_partition``, ``review_unit_violations``, ``validate_representation``,
``proposal_payload``). No schema, validator or acceptance machinery is added
here. The clause-to-draft assembly that first lived in this file is now the
shared :mod:`afterworlds.ingestion.mechanical.authoring`; the committed
proposal bytes are unchanged by that move.

The source review is held apart from the representation: ``CLAUSES`` says what
each printed clause must be read as, ``FRAMING`` and the entry headings name
every leaf that states no rule, and ``COMPONENTS`` is the representation
proposed for them. Expected rules are built from ``CLAUSES`` alone, so a
component dropped from ``COMPONENTS`` leaves its clause's expectation standing
for ``review_unit_violations`` to report.

Authoring conventions (engineering proposals, stated once so a reviewer can
check them rather than infer them):

* A clause is located by its exact text inside its own entry's leaves and must
  occur exactly once there; offsets are never written down.
* One PRIMARY owner per substantive span: the prose binding where the
  component retains governing prose, else the component itself. Facts,
  qualifiers and references claim CONTEXTUAL provenance to the same spans.
* ``STRUCTURED`` only where the typed facts say everything the clause says.
  Where a typed fact is true but its circumstance has no closed vocabulary
  (line of sight, "requires sight", "within 5 feet", "other than the
  grappler"), the component is ``MIXED`` and the prose governs, with
  ``contextual_applicability``. Petrified's "(usually stone)" is the one
  ``fiction_dependent_consequence``: what the subject becomes is hedged prose.
* References are stated for condition-to-condition dependencies and for the
  source's own *See also* pointers. Glossary terms whose meaning is carried by
  closed code-owned vocabulary (Long Rest trigger, Concentration, D20 Test,
  Initiative, Speed, Critical Hit, Resistance/Immunity) are bound by that type,
  not by a reference; see the review packet.

Run: ``python issue-5d-conditions-pilot-generator.py <published afterworlds.db>``
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
    unknown_target_findings,
)
from afterworlds.ingestion.mechanical.authoring import batch_findings as batch_findings
from afterworlds.ingestion.mechanical.authoring import render as render
from afterworlds.ingestion.mechanical.bound_corpus import (
    published_release_binding,
)
from afterworlds.ingestion.mechanical.representation import (
    AbilityScore,
    ActionCost,
    ActionRestrictionFact,
    AdvantageFact,
    AdvantageState,
    Applicability,
    ApplicabilityKind,
    AutomaticOutcome,
    AutomaticOutcomeFact,
    Comparison,
    ComponentHandling,
    ComponentOption,
    ConditionEffectFact,
    ConditionEffectKind,
    ConditionKind,
    ConditionLevelFact,
    CreatureSize,
    CriticalHitChange,
    CriticalHitRuleFact,
    DamageResponseFact,
    DamageResponseKind,
    DamageScope,
    LevelDirection,
    MovementAmount,
    MovementCostFact,
    MovementCostKind,
    MovementMode,
    MovementPermissionFact,
    MovementTransportFact,
    ParticipantRole,
    Phase,
    QuantityMultiplierFact,
    RecordKind,
    RecoveryTrigger,
    RollActor,
    RollContext,
    RollSpec,
    RoundingRule,
    ScalingBasis,
    ScalingDirection,
    ScalingEffect,
    ScalingFact,
    Sense,
    SensoryCapabilityFact,
    SizeComparison,
    SizeRelation,
    SpeedChange,
    SpeedModificationFact,
    StateEffectFact,
    StateEffectKind,
    TrackedQuantity,
    TransformationFact,
    TransformedForm,
    TransportKind,
)
from afterworlds.ingestion.mechanical.schema_lift import (
    SCHEMA_15_HASH,
    SCHEMA_15_VERSION,
)

ORIGIN = "issue-5d-conditions-pilot-generator.py"
PROPOSAL_FILE = "issue-5d-conditions-pilot-PROPOSAL.json"
PARENT = ("Rules Glossary", "Rules Definitions")

#: (record slug, printed container label, record kind). Printed order.
ENTRIES: tuple[tuple[str, str, RecordKind], ...] = (
    ("blinded", "Blinded [Condition]", RecordKind.CONDITION),
    ("charmed", "Charmed [Condition]", RecordKind.CONDITION),
    ("condition", "Condition", RecordKind.GLOSSARY_RULE),
    ("deafened", "Deafened [Condition]", RecordKind.CONDITION),
    ("exhaustion", "Exhaustion [Condition]", RecordKind.CONDITION),
    ("frightened", "Frightened [Condition]", RecordKind.CONDITION),
    ("grappled", "Grappled [Condition]", RecordKind.CONDITION),
    ("grappling", "Grappling", RecordKind.GLOSSARY_RULE),
    ("incapacitated", "Incapacitated [Condition]", RecordKind.CONDITION),
    ("invisible", "Invisible [Condition]", RecordKind.CONDITION),
    ("paralyzed", "Paralyzed [Condition]", RecordKind.CONDITION),
    ("petrified", "Petrified [Condition]", RecordKind.CONDITION),
    ("poisoned", "Poisoned [Condition]", RecordKind.CONDITION),
    ("prone", "Prone [Condition]", RecordKind.CONDITION),
    ("restrained", "Restrained [Condition]", RecordKind.CONDITION),
    ("stunned", "Stunned [Condition]", RecordKind.CONDITION),
    ("unconscious", "Unconscious [Condition]", RecordKind.CONDITION),
)
CONDITION_NAMES = tuple(
    label.removesuffix(" [Condition]")
    for _, label, kind in ENTRIES
    if kind is RecordKind.CONDITION
)
assert len(CONDITION_NAMES) == 15, CONDITION_NAMES


# ---------------------------------------------------------------------------
# Reason codes
# ---------------------------------------------------------------------------
CTX = "contextual_applicability"
NO_USE = "no_identified_structured_use"
FICTION = "fiction_dependent_consequence"
S, M, P = (
    ComponentHandling.STRUCTURED,
    ComponentHandling.MIXED,
    ComponentHandling.PROSE_BOUND,
)

# ---------------------------------------------------------------------------
# Recurring typed facts (existing vocabulary only)
# ---------------------------------------------------------------------------


def roll(actor: RollActor, ctx: RollContext, ability: AbilityScore | None = None):  # type: ignore[no-untyped-def]
    return RollSpec(actor=actor, context=ctx, ability=ability)


def adv(state: AdvantageState, actor: RollActor, ctx: RollContext, ability=None):  # type: ignore[no-untyped-def]
    return AdvantageFact(state=state, roll=roll(actor, ctx, ability))


ADV, DIS = AdvantageState.ADVANTAGE, AdvantageState.DISADVANTAGE
YOU, AGAINST = RollActor.SUBJECT, RollActor.AGAINST_SUBJECT
ATTACK, CHECK, SAVE, INIT = (
    RollContext.ATTACK_ROLL,
    RollContext.ABILITY_CHECK,
    RollContext.SAVING_THROW,
    RollContext.INITIATIVE,
)
SPEED_0 = SpeedModificationFact(change=SpeedChange.SET_TO, feet=0, can_increase=False)
ATTACKED_WITH_ADVANTAGE = adv(ADV, AGAINST, ATTACK)
FAIL_STR_DEX_SAVES = tuple(
    AutomaticOutcomeFact(roll=roll(YOU, SAVE, a), outcome=AutomaticOutcome.FAILURE)
    for a in (AbilityScore.STRENGTH, AbilityScore.DEXTERITY)
)
FAIL_CHECK = AutomaticOutcomeFact(
    roll=roll(YOU, CHECK), outcome=AutomaticOutcome.FAILURE
)
AUTO_CRIT = CriticalHitRuleFact(change=CriticalHitChange.AUTOMATIC_ON_HIT)


def applies(c: ConditionKind) -> ConditionEffectFact:
    return ConditionEffectFact(condition=c, effect=ConditionEffectKind.APPLIES)


def level_is(comparison: Comparison, value: int) -> Applicability:
    return Applicability(
        kind=ApplicabilityKind.QUANTITY_THRESHOLD,
        quantity=TrackedQuantity.CONDITION_LEVEL,
        comparison=comparison,
        value=value,
    )


EXH_GAIN = ConditionLevelFact(
    condition=ConditionKind.EXHAUSTION,
    direction=LevelDirection.GAIN,
    amount=1,
    cumulative=True,
)
EXH_DIES = StateEffectFact(effect=StateEffectKind.DIES)
EXH_REMOVE_ONE = ConditionLevelFact(
    condition=ConditionKind.EXHAUSTION, direction=LevelDirection.REMOVE, amount=1
)
EXH_ENDS = ConditionEffectFact(
    condition=ConditionKind.EXHAUSTION, effect=ConditionEffectKind.REMOVES
)
DRAG_SURCHARGE = MovementCostFact(
    kind=MovementCostKind.PER_FOOT_SURCHARGE,
    amount=MovementAmount.FEET,
    payer=ParticipantRole.COUNTERPART,
    feet=1,
)
#: FactQualifier's own docstring names this exception as its forced instance:
#: it limits the surcharge only, never the transport permission.
UNLESS_TINY_OR_TWO_SMALLER = Applicability(
    kind=ApplicabilityKind.SIZE_COMPARISON,
    negated=True,
    any_of=(
        SizeComparison(measured=ParticipantRole.SUBJECT, category=CreatureSize.TINY),
        SizeComparison(
            measured=ParticipantRole.SUBJECT,
            relation=SizeRelation.SMALLER,
            at_least=2,
            reference=ParticipantRole.COUNTERPART,
        ),
    ),
)

# ---------------------------------------------------------------------------
# Source review: every clause of the seventeen entries, what it must be read as
# ---------------------------------------------------------------------------
#: Marks a clause whose governing prose must stay bound (MIXED / PROSE_BOUND).
PROSE = None

SPEED_0_TEXT = "_Speed 0._ Your Speed is 0 and can't increase."
ATTACKED_WITH_ADVANTAGE_TEXT = (
    "_Attacks Affected._ Attack rolls against you have Advantage."
)
FAIL_STR_DEX_TEXT = "_Saving Throws Affected._ You automatically fail Strength and Dexterity saving throws."
INCAPACITATED_TEXT = "_Incapacitated._ You have the Incapacitated condition."
AUTO_CRIT_TEXT = "_Automatic Critical Hits._ Any attack roll that hits you is a Critical Hit if the attacker is within 5 feet of you."

#: (entry, component key, expected fact families + PROSE, clause texts).
#: Written from the printed entry, not from ``COMPONENTS``: each row becomes an
#: ``ExpectedRule`` whether or not a component satisfies it, so a clause the
#: representation drops is a review-unit finding, never a silent omission.
CLAUSES: tuple[tuple[str, str, tuple[str | None, ...], tuple[str, ...]], ...] = (
    (
        "blinded",
        "cant_see",
        ("automatic_outcome", "sensory_capability", PROSE),
        (
            "_Can't See._ You can't see and automatically fail any ability check that requires sight.",
        ),
    ),
    (
        "blinded",
        "attacks_affected",
        ("advantage",),
        (
            "_Attacks Affected._ Attack rolls against you have Advantage, and your attack rolls have Disadvantage.",
        ),
    ),
    (
        "charmed",
        "cant_harm_the_charmer",
        (PROSE,),
        (
            "_Can't Harm the Charmer._ You can't attack the charmer or target the charmer with damaging abilities or magical effects.",
        ),
    ),
    (
        "charmed",
        "social_advantage",
        (PROSE,),
        (
            "_Social Advantage._ The charmer has Advantage on any ability check to interact with you socially.",
        ),
    ),
    (
        "condition",
        "definition",
        (PROSE,),
        (
            "A condition is a temporary game state.",
            "The definition of a condition says how it affects its recipient, and various rules define how to end a condition.",
        ),
    ),
    (
        "condition",
        "non_stacking",
        (PROSE,),
        (
            "A condition doesn't stack with itself; a recipient either has a condition or doesn't.",
            "The Exhaustion condition is an exception to that rule.",
        ),
    ),
    (
        "deafened",
        "cant_hear",
        ("automatic_outcome", "sensory_capability", PROSE),
        (
            "_Can't Hear._ You can't hear and automatically fail any ability check that requires hearing.",
        ),
    ),
    (
        "exhaustion",
        "exhaustion_levels",
        ("condition_level", "state_effect"),
        (
            "_Exhaustion Levels._ This condition is cumulative. Each time you receive it, you gain 1 Exhaustion level. You die if your Exhaustion level is 6.",
        ),
    ),
    (
        "exhaustion",
        "d20_tests_affected",
        ("scaling",),
        (
            "_D20 Tests Affected._ When you make a D20 Test, the roll is reduced by 2 times your Exhaustion level.",
        ),
    ),
    (
        "exhaustion",
        "speed_reduced",
        ("scaling",),
        (
            "_Speed Reduced._ Your Speed is reduced by a number of feet equal to 5 times your Exhaustion level.",
        ),
    ),
    (
        "exhaustion",
        "removing_exhaustion_levels",
        ("condition_effect", "condition_level"),
        (
            "_Removing Exhaustion Levels._ Finishing a Long Rest removes 1 of your Exhaustion levels. When your Exhaustion level reaches 0, the condition ends.",
        ),
    ),
    (
        "frightened",
        "ability_checks_and_attacks_affected",
        ("advantage", PROSE),
        (
            "_Ability Checks and Attacks Affected._ You have Disadvantage on ability checks and attack rolls while the source of fear is within line of sight.",
        ),
    ),
    (
        "frightened",
        "cant_approach",
        (PROSE,),
        ("_Can't Approach._ You can't willingly move closer to the source of fear.",),
    ),
    ("grappled", "speed_0", ("speed_modification",), (SPEED_0_TEXT,)),
    (
        "grappled",
        "attacks_affected",
        ("advantage", PROSE),
        (
            "_Attacks Affected._ You have Disadvantage on attack rolls against any target other than the grappler.",
        ),
    ),
    (
        "grappled",
        "movable",
        ("movement_cost", "movement_transport"),
        (
            "_Movable._ The grappler can drag or carry you when it moves, but every foot of movement costs it 1 extra foot unless you are Tiny or two or more sizes smaller than it.",
        ),
    ),
    (
        "grappling",
        "grapple_basis",
        (PROSE,),
        (
            "A creature can grapple another creature.",
            "Characters typically grapple by using an Unarmed Strike.",
        ),
    ),
    (
        "grappling",
        "grappled_condition",
        ("condition_effect",),
        (
            "_Grappled Condition._ Successfully grappling a creature gives it the Grappled condition.",
        ),
    ),
    (
        "grappling",
        "one_grapple_per_hand",
        (PROSE,),
        (
            "_One Grapple per Hand._ A creature must have a hand free to grapple another creature. Some stat blocks and game effects allow a creature to grapple using a tentacle, a maw, or another body part. Whatever part a grappler uses, it can grapple only one creature at a time with that part, and the grappler can't use that part to target another creature unless it ends the grapple.",
        ),
    ),
    (
        "grappling",
        "ending_a_grapple",
        (PROSE,),
        (
            "_Ending a Grapple._ A Grappled creature can use its action to make a Strength (Athletics) or Dexterity (Acrobatics) check against the grapple's escape DC, ending the condition on itself on a success. The condition also ends if the grappler has the Incapacitated condition or if the distance between the Grappled target and the grappler exceeds the grapple's range. In addition, the grappler can release the target at any time (no action required).",
        ),
    ),
    (
        "incapacitated",
        "inactive",
        ("action_restriction",),
        ("_Inactive._ You can't take any action, Bonus Action, or Reaction.",),
    ),
    (
        "incapacitated",
        "no_concentration",
        ("state_effect",),
        ("_No Concentration._ Your Concentration is broken.",),
    ),
    (
        "incapacitated",
        "speechless",
        ("state_effect",),
        ("_Speechless._ You can't speak.",),
    ),
    (
        "incapacitated",
        "surprised",
        ("advantage",),
        (
            "_Surprised._ If you're Incapacitated when you roll Initiative, you have Disadvantage on the roll.",
        ),
    ),
    (
        "invisible",
        "surprise",
        ("advantage",),
        (
            "_Surprise._ If you're Invisible when you roll Initiative, you have Advantage on the roll.",
        ),
    ),
    (
        "invisible",
        "concealed",
        (PROSE,),
        (
            "_Concealed._ You aren't affected by any effect that requires its target to be seen unless the effect's creator can somehow see you. Any equipment you are wearing or carrying is also concealed.",
        ),
    ),
    (
        "invisible",
        "attacks_affected",
        ("advantage", PROSE),
        (
            "_Attacks Affected._ Attack rolls against you have Disadvantage, and your attack rolls have Advantage.",
            "If a creature can somehow see you, you don't gain this benefit against that creature.",
        ),
    ),
    ("paralyzed", "incapacitated", ("condition_effect",), (INCAPACITATED_TEXT,)),
    ("paralyzed", "speed_0", ("speed_modification",), (SPEED_0_TEXT,)),
    (
        "paralyzed",
        "saving_throws_affected",
        ("automatic_outcome",),
        (FAIL_STR_DEX_TEXT,),
    ),
    ("paralyzed", "attacks_affected", ("advantage",), (ATTACKED_WITH_ADVANTAGE_TEXT,)),
    (
        "paralyzed",
        "automatic_critical_hits",
        ("critical_hit_rule", PROSE),
        (AUTO_CRIT_TEXT,),
    ),
    (
        "petrified",
        "turned_to_inanimate_substance",
        ("quantity_multiplier", "state_effect", "transformation", PROSE),
        (
            "_Turned to Inanimate Substance._ You are transformed, along with any nonmagical objects you are wearing and carrying, into a solid inanimate substance (usually stone). Your weight increases by a factor of ten, and you cease aging.",
        ),
    ),
    ("petrified", "incapacitated", ("condition_effect",), (INCAPACITATED_TEXT,)),
    ("petrified", "speed_0", ("speed_modification",), (SPEED_0_TEXT,)),
    ("petrified", "attacks_affected", ("advantage",), (ATTACKED_WITH_ADVANTAGE_TEXT,)),
    (
        "petrified",
        "saving_throws_affected",
        ("automatic_outcome",),
        (FAIL_STR_DEX_TEXT,),
    ),
    (
        "petrified",
        "resist_damage",
        ("damage_response",),
        ("_Resist Damage._ You have Resistance to all damage.",),
    ),
    (
        "petrified",
        "poison_immunity",
        ("condition_effect",),
        ("_Poison Immunity._ You have Immunity to the Poisoned condition.",),
    ),
    (
        "poisoned",
        "ability_checks_and_attacks_affected",
        ("advantage",),
        (
            "_Ability Checks and Attacks Affected._ You have Disadvantage on attack rolls and ability checks.",
        ),
    ),
    (
        "prone",
        "restricted_movement",
        ("condition_effect", "movement_cost", "movement_permission"),
        (
            "_Restricted Movement._ Your only movement options are to crawl or to spend an amount of movement equal to half your Speed (round down) to right yourself and thereby end the condition. If your Speed is 0, you can't right yourself.",
        ),
    ),
    (
        "prone",
        "own_attacks_affected",
        ("advantage",),
        ("_Attacks Affected._ You have Disadvantage on attack rolls.",),
    ),
    (
        "prone",
        "attacks_against_affected",
        (PROSE,),
        (
            "An attack roll against you has Advantage if the attacker is within 5 feet of you. Otherwise, that attack roll has Disadvantage.",
        ),
    ),
    ("restrained", "speed_0", ("speed_modification",), (SPEED_0_TEXT,)),
    (
        "restrained",
        "attacks_affected",
        ("advantage",),
        (
            "_Attacks Affected._ Attack rolls against you have Advantage, and your attack rolls have Disadvantage.",
        ),
    ),
    (
        "restrained",
        "saving_throws_affected",
        ("advantage",),
        (
            "_Saving Throws Affected._ You have Disadvantage on Dexterity saving throws.",
        ),
    ),
    ("stunned", "incapacitated", ("condition_effect",), (INCAPACITATED_TEXT,)),
    ("stunned", "saving_throws_affected", ("automatic_outcome",), (FAIL_STR_DEX_TEXT,)),
    ("stunned", "attacks_affected", ("advantage",), (ATTACKED_WITH_ADVANTAGE_TEXT,)),
    (
        "unconscious",
        "inert",
        ("condition_effect", "state_effect"),
        (
            "_Inert._ You have the Incapacitated and Prone conditions, and you drop whatever you're holding.",
        ),
    ),
    (
        "unconscious",
        "remains_prone",
        ("condition_effect",),
        ("When this condition ends, you remain Prone.",),
    ),
    ("unconscious", "speed_0", ("speed_modification",), (SPEED_0_TEXT,)),
    (
        "unconscious",
        "attacks_affected",
        ("advantage",),
        (ATTACKED_WITH_ADVANTAGE_TEXT,),
    ),
    (
        "unconscious",
        "saving_throws_affected",
        ("automatic_outcome",),
        (FAIL_STR_DEX_TEXT,),
    ),
    (
        "unconscious",
        "automatic_critical_hits",
        ("critical_hit_rule", PROSE),
        (AUTO_CRIT_TEXT,),
    ),
    (
        "unconscious",
        "unaware",
        ("state_effect",),
        ("_Unaware._ You're unaware of your surroundings.",),
    ),
)

#: Framing leaves: (entry, whole-leaf text prefix). Each is the entry's
#: SupportingGroup -- it restates the entry name or enumerates the index -- and
#: must match exactly one leaf of its entry. Nothing is inferred as framing.
FRAMING: tuple[tuple[str, str], ...] = (
    (
        "blinded",
        "While you have the Blinded condition, you experience the following effects.",
    ),
    (
        "charmed",
        "While you have the Charmed condition, you experience the following effects.",
    ),
    (
        "deafened",
        "While you have the Deafened condition, you experience the following effect.",
    ),
    (
        "exhaustion",
        "While you have the Exhaustion condition, you experience the following effects.",
    ),
    (
        "frightened",
        "While you have the Frightened condition, you experience the following effects.",
    ),
    (
        "grappled",
        "While you have the Grappled condition, you experience the following effects.",
    ),
    (
        "incapacitated",
        "While you have the Incapacitated condition, you experience the following effects.",
    ),
    (
        "invisible",
        "While you have the Invisible condition, you experience the following effects.",
    ),
    (
        "paralyzed",
        "While you have the Paralyzed condition, you experience the following effects.",
    ),
    (
        "petrified",
        "While you have the Petrified condition, you experience the following effects.",
    ),
    (
        "poisoned",
        "While you have the Poisoned condition, you experience the following effect.",
    ),
    (
        "prone",
        "While you have the Prone condition, you experience the following effects.",
    ),
    (
        "restrained",
        "While you have the Restrained condition, you experience the following effects.",
    ),
    (
        "stunned",
        "While you have the Stunned condition, you experience the following effects.",
    ),
    (
        "unconscious",
        "While you have the Unconscious condition, you experience the following effects.",
    ),
    ("condition", "<table>"),
)

# ---------------------------------------------------------------------------
# Components: (entry, key, handling, reason, facts, qualifiers,
# options, applies_when, component references (text, target slug))
# ---------------------------------------------------------------------------


C = EntryComponent


def speed_0(entry: str) -> C:
    return C(
        entry,
        "speed_0",
        S,
        None,
        (SPEED_0,),
    )


def attacked_with_advantage(entry: str) -> C:
    return C(
        entry,
        "attacks_affected",
        S,
        None,
        (ATTACKED_WITH_ADVANTAGE,),
    )


def fail_str_dex(entry: str) -> C:
    return C(
        entry,
        "saving_throws_affected",
        S,
        None,
        FAIL_STR_DEX_SAVES,
    )


def has_incapacitated(entry: str) -> C:
    return C(
        entry,
        "incapacitated",
        S,
        None,
        (applies(ConditionKind.INCAPACITATED),),
        refs=(("Incapacitated", "incapacitated"),),
    )


def auto_crit(entry: str) -> C:
    return C(
        entry,
        "automatic_critical_hits",
        M,
        CTX,
        (AUTO_CRIT,),
    )


COMPONENTS: tuple[C, ...] = (
    # Blinded -- the check failure is limited to checks that require sight.
    C(
        "blinded",
        "cant_see",
        M,
        CTX,
        (SensoryCapabilityFact(sense=Sense.SIGHT, can_perceive=False), FAIL_CHECK),
    ),
    C(
        "blinded",
        "attacks_affected",
        S,
        None,
        (ATTACKED_WITH_ADVANTAGE, adv(DIS, YOU, ATTACK)),
    ),
    # Charmed -- both clauses depend on who the charmer is and on judgement of
    # "damaging" and "interact socially"; no fact would be true unqualified.
    C(
        "charmed",
        "cant_harm_the_charmer",
        P,
        CTX,
    ),
    C(
        "charmed",
        "social_advantage",
        P,
        CTX,
    ),
    # Condition (index)
    C(
        "condition",
        "definition",
        P,
        NO_USE,
    ),
    C(
        "condition",
        "non_stacking",
        P,
        NO_USE,
        refs=(("Exhaustion", "exhaustion"),),
    ),
    # Deafened
    C(
        "deafened",
        "cant_hear",
        M,
        CTX,
        (SensoryCapabilityFact(sense=Sense.HEARING, can_perceive=False), FAIL_CHECK),
    ),
    # Exhaustion -- cumulative levels, formulas, death at 6. No effects table.
    C(
        "exhaustion",
        "exhaustion_levels",
        S,
        None,
        (EXH_GAIN, EXH_DIES),
        qualifiers=((EXH_DIES, level_is(Comparison.EQUALS, 6)),),
    ),
    C(
        "exhaustion",
        "d20_tests_affected",
        S,
        None,
        (
            ScalingFact(
                basis=ScalingBasis.CONDITION_LEVEL,
                threshold=0,
                effect=ScalingEffect.D20_TEST,
                direction=ScalingDirection.DECREASE,
                amount=2,
            ),
        ),
    ),
    C(
        "exhaustion",
        "speed_reduced",
        S,
        None,
        (
            ScalingFact(
                basis=ScalingBasis.CONDITION_LEVEL,
                threshold=0,
                effect=ScalingEffect.SPEED,
                direction=ScalingDirection.DECREASE,
                amount=5,
            ),
        ),
    ),
    C(
        "exhaustion",
        "removing_exhaustion_levels",
        S,
        None,
        (EXH_REMOVE_ONE, EXH_ENDS),
        qualifiers=(
            (
                EXH_REMOVE_ONE,
                Applicability(
                    kind=ApplicabilityKind.TRIGGER, trigger=RecoveryTrigger.LONG_REST
                ),
            ),
            (EXH_ENDS, level_is(Comparison.REACHES, 0)),
        ),
    ),
    # Frightened -- the Disadvantage holds only while the source of fear is in
    # line of sight; cannot-approach is a distinct clause.
    C(
        "frightened",
        "ability_checks_and_attacks_affected",
        M,
        CTX,
        (adv(DIS, YOU, CHECK), adv(DIS, YOU, ATTACK)),
    ),
    C(
        "frightened",
        "cant_approach",
        P,
        CTX,
    ),
    # Grappled
    speed_0("grappled"),
    C(
        "grappled",
        "attacks_affected",
        M,
        CTX,
        (adv(DIS, YOU, ATTACK),),
    ),
    C(
        "grappled",
        "movable",
        S,
        None,
        (
            MovementTransportFact(
                carrier=ParticipantRole.COUNTERPART,
                carried=ParticipantRole.SUBJECT,
                kind=TransportKind.PERMITTED,
            ),
            DRAG_SURCHARGE,
        ),
        qualifiers=((DRAG_SURCHARGE, UNLESS_TINY_OR_TWO_SMALLER),),
    ),
    # Grappling
    C(
        "grappling",
        "grapple_basis",
        P,
        NO_USE,
    ),
    C(
        "grappling",
        "grappled_condition",
        S,
        None,
        (applies(ConditionKind.GRAPPLED),),
    ),
    C(
        "grappling",
        "one_grapple_per_hand",
        P,
        CTX,
    ),
    C(
        "grappling",
        "ending_a_grapple",
        P,
        CTX,
        refs=(("Incapacitated", "incapacitated"),),
    ),
    # Incapacitated
    C(
        "incapacitated",
        "inactive",
        S,
        None,
        tuple(
            ActionRestrictionFact(cost=c)
            for c in (ActionCost.ACTION, ActionCost.BONUS_ACTION, ActionCost.REACTION)
        ),
    ),
    C(
        "incapacitated",
        "no_concentration",
        S,
        None,
        (StateEffectFact(effect=StateEffectKind.CONCENTRATION_BROKEN),),
    ),
    C(
        "incapacitated",
        "speechless",
        S,
        None,
        (StateEffectFact(effect=StateEffectKind.CANNOT_SPEAK),),
    ),
    C(
        "incapacitated",
        "surprised",
        S,
        None,
        (adv(DIS, YOU, INIT),),
    ),
    # Invisible -- the seen-target exception and the per-observer exception
    # are both circumstances code cannot evaluate.
    C(
        "invisible",
        "surprise",
        S,
        None,
        (adv(ADV, YOU, INIT),),
    ),
    C(
        "invisible",
        "concealed",
        P,
        CTX,
    ),
    C(
        "invisible",
        "attacks_affected",
        M,
        CTX,
        (adv(DIS, AGAINST, ATTACK), adv(ADV, YOU, ATTACK)),
    ),
    # Paralyzed
    has_incapacitated("paralyzed"),
    speed_0("paralyzed"),
    fail_str_dex("paralyzed"),
    attacked_with_advantage("paralyzed"),
    auto_crit("paralyzed"),
    # Petrified -- nonmagical carried objects, x10 weight, aging ceased,
    # Resistance to all damage, Immunity to the Poisoned *condition*. What the
    # subject becomes -- "a solid inanimate substance (usually stone)" -- is
    # hedged by the source, so TransformationFact leaves it to governing prose.
    C(
        "petrified",
        "turned_to_inanimate_substance",
        M,
        FICTION,
        (
            TransformationFact(
                becomes=TransformedForm.OBJECT, carried_nonmagical_included=True
            ),
            QuantityMultiplierFact(quantity=TrackedQuantity.WEIGHT, factor=10),
            StateEffectFact(effect=StateEffectKind.AGING_SUSPENDED),
        ),
    ),
    has_incapacitated("petrified"),
    speed_0("petrified"),
    attacked_with_advantage("petrified"),
    fail_str_dex("petrified"),
    C(
        "petrified",
        "resist_damage",
        S,
        None,
        (
            DamageResponseFact(
                response=DamageResponseKind.RESISTANCE, scope=DamageScope.ALL
            ),
        ),
    ),
    C(
        "petrified",
        "poison_immunity",
        S,
        None,
        (
            ConditionEffectFact(
                condition=ConditionKind.POISONED, effect=ConditionEffectKind.IMMUNITY
            ),
        ),
        refs=(("Poisoned", "poisoned"),),
    ),
    # Poisoned
    C(
        "poisoned",
        "ability_checks_and_attacks_affected",
        S,
        None,
        (adv(DIS, YOU, ATTACK), adv(DIS, YOU, CHECK)),
    ),
    # Prone -- the only-movement-options clause is the ComponentDraft
    # docstring's own instance of an exhaustive actor choice.
    C(
        "prone",
        "restricted_movement",
        S,
        None,
        options=(
            ComponentOption(
                semantic_key="crawl",
                facts=(MovementPermissionFact(mode=MovementMode.CRAWL),),
            ),
            ComponentOption(
                semantic_key="right_yourself",
                facts=(
                    MovementCostFact(
                        kind=MovementCostKind.EXPENDITURE,
                        amount=MovementAmount.HALF_SPEED,
                        payer=ParticipantRole.SUBJECT,
                        rounding=RoundingRule.DOWN,
                    ),
                    ConditionEffectFact(
                        condition=ConditionKind.PRONE,
                        effect=ConditionEffectKind.REMOVES,
                    ),
                ),
                applies_when=Applicability(
                    kind=ApplicabilityKind.QUANTITY_THRESHOLD,
                    negated=True,
                    quantity=TrackedQuantity.SPEED,
                    comparison=Comparison.EQUALS,
                    value=0,
                ),
            ),
        ),
    ),
    C(
        "prone",
        "own_attacks_affected",
        S,
        None,
        (adv(DIS, YOU, ATTACK),),
    ),
    C(
        "prone",
        "attacks_against_affected",
        P,
        CTX,
    ),
    # Restrained -- Disadvantage on Dexterity saves, not automatic failure.
    speed_0("restrained"),
    C(
        "restrained",
        "attacks_affected",
        S,
        None,
        (ATTACKED_WITH_ADVANTAGE, adv(DIS, YOU, ATTACK)),
    ),
    C(
        "restrained",
        "saving_throws_affected",
        S,
        None,
        (adv(DIS, YOU, SAVE, AbilityScore.DEXTERITY),),
    ),
    # Stunned
    has_incapacitated("stunned"),
    fail_str_dex("stunned"),
    attacked_with_advantage("stunned"),
    # Unconscious -- a peer entry; Prone applies while active and remains on end.
    C(
        "unconscious",
        "inert",
        S,
        None,
        (
            applies(ConditionKind.INCAPACITATED),
            applies(ConditionKind.PRONE),
            StateEffectFact(effect=StateEffectKind.DROPS_HELD_OBJECTS),
        ),
        refs=(("Incapacitated", "incapacitated"), ("Prone", "prone")),
    ),
    C(
        "unconscious",
        "remains_prone",
        S,
        None,
        (applies(ConditionKind.PRONE),),
        applies_when=Applicability(kind=ApplicabilityKind.PHASE, phase=Phase.ON_END),
        refs=(("Prone", "prone"),),
    ),
    speed_0("unconscious"),
    attacked_with_advantage("unconscious"),
    fail_str_dex("unconscious"),
    auto_crit("unconscious"),
    C(
        "unconscious",
        "unaware",
        S,
        None,
        (StateEffectFact(effect=StateEffectKind.UNAWARE_OF_SURROUNDINGS),),
    ),
)

#: Supporting authority: (entry, text, what it contextualizes). A component key,
#: or ``None`` where the span is linked by the entry's record-owned references.
SUPPORTING: tuple[tuple[str, str, str | None], ...] = (
    ("condition", "This glossary defines these conditions:", None),
    *(("condition", name, None) for name in CONDITION_NAMES),
    (
        "grappling",
        "Many monsters have special attacks that allow them to quickly grapple prey.",
        "grapple_basis",
    ),
    (
        "grappling",
        "However a grapple is initiated, it follows these rules.",
        "grapple_basis",
    ),
    ("grappling", '_See also_ "Unarmed Strike" and "Grappled."', None),
)

#: Record-owned references: (entry, printed text, target slug, clause texts
#: whose span the pointer is read from). ``unarmed_strike`` is outside this
#: pilot and stays an honest outstanding target.
RECORD_REFERENCES: tuple[tuple[str, str, str, tuple[str, ...]], ...] = (
    *(
        (
            "condition",
            name,
            name.lower(),
            (name, "This glossary defines these conditions:"),
        )
        for name in CONDITION_NAMES
    ),
    (
        "grappling",
        "Unarmed Strike",
        "unarmed_strike",
        (
            "Characters typically grapple by using an Unarmed Strike.",
            '_See also_ "Unarmed Strike" and "Grappled."',
        ),
    ),
    (
        "grappling",
        "Grappled",
        "grappled",
        (
            '_See also_ "Unarmed Strike" and "Grappled."',
            "_Grappled Condition._ Successfully grappling a creature gives it the Grappled condition.",
        ),
    ),
)

#: Target slugs this pilot does not declare, so each stays an ``unknown target
#: record`` finding and the gate stays fail-closed until its batch exists.
OUTSTANDING_TARGETS = ("unarmed_strike",)

# ---------------------------------------------------------------------------
# Build: the shared entry-batch assembly over the tables above
# ---------------------------------------------------------------------------


def batch() -> EntryBatch:
    """The tables above, read at call time so tests can mutate them."""
    return EntryBatch(
        origin=ORIGIN,
        schema=(SCHEMA_15_VERSION, SCHEMA_15_HASH),
        proposal_origin=f"{ORIGIN} (CRD Issue 5d fresh conditions pilot; unaccepted)",
        unit_prefix="conditions-pilot",
        parent=PARENT,
        entries=ENTRIES,
        expected_leaves=87,
        clauses=CLAUSES,
        framing=FRAMING,
        components=COMPONENTS,
        supporting=SUPPORTING,
        record_references=RECORD_REFERENCES,
        # A table cell's name also occurs in running prose; anchor it on its cell.
        cell_anchors=CONDITION_NAMES,
    )


def build(session: Session) -> Built:
    """Derive the pilot proposal from the release *session* published."""
    return build_entry_batch(session, batch(), published_release_binding(session))


def expected_representation_findings() -> list[str]:
    """Exactly the outstanding out-of-scope targets, and nothing else."""
    return unknown_target_findings(RECORD_REFERENCES, COMPONENTS, OUTSTANDING_TARGETS)


def main(db: str) -> int:
    out = Path(__file__).resolve().parent / PROPOSAL_FILE
    return emit(db, build, out, expected_representation_findings())


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
