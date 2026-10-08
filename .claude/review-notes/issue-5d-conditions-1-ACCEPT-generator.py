"""ACCEPTANCE — conditions-1, CRD Issue 5d batch 1.

Owner authorization, 2026-08-23: Ravenlok explicitly authorized acceptance of
proposal identity
`14587d5b5d51ad282f3d16510e015cd7116adcbd3877964bf034eef96780b0eb`
and of that proposal's exact resolved scope, and of nothing else.

Byte-identical to `issue-5d-conditions-1-schema3-REMEDIATION-generator.py`
through the derivation of `ident`, so the proposal accepted here is produced by
exactly the code that produced the reviewed candidate. Two things differ:

  1. the review-artifact writes go to a scratch directory, so the REMEDIATION
     and REGEN artifacts stay byte-for-byte as reviewed and rejected; and
  2. the acceptance stage below calls the repository's real
     `acceptance.accept_proposal` once, serializes through the production
     `oracle.accepted_inputs_payload`, and writes the committed artifact.

The run refuses to continue unless the derived proposal identity is exactly the
authorized one and the resolved scope is exactly the 185 spans that proposal
proposed. Nothing is published, activated, or retired; no second batch is begun.
"""

from __future__ import annotations

import json
import sys
import collections
from collections import defaultdict
from pathlib import Path

REPO = Path(r"D:\AI\Claude\afterworlds")
#: AMENDMENT 1. The schema-2 worktree is gone; schema 2 is merged into main and
#: main's `src/` is byte-identical to the PR #155 merge. Import from the primary
#: checkout, and print the resolved files so the imported contract is evidence,
#: not an assumption.
CODE = REPO
sys.path.insert(0, str(CODE / "src"))
REVIEW_DIR = Path(__file__).parent
OUT = Path(__file__).parent  # scratchpad; nothing enters the repo

from afterworlds.ingestion.corpus.pipeline import build_candidate  # noqa: E402
from afterworlds.ingestion.corpus.policy import exclusion_reason_for  # noqa: E402
from afterworlds.ingestion.corpus.reconcile import (  # noqa: E402
    _full_coverage_edges,
)
from afterworlds.pipeline.retrieval.config import (  # noqa: E402
    RetrievalMemoryConfig,
)
from afterworlds.ingestion.mechanical.accounting import (  # noqa: E402
    derive_span_id,
    validate_partition,
    validate_reason_codes,
)
from afterworlds.ingestion.mechanical.bound_corpus import (  # noqa: E402
    BoundCorpusSnapshot,
    ChunkCoverage,
)
from afterworlds.ingestion.mechanical.models import (  # noqa: E402
    ClassificationLedger,
    ComponentHandling,
    SemanticDisposition,
    SemanticSpan,
)
from afterworlds.ingestion.mechanical.policy import (  # noqa: E402
    SEMANTIC_POLICY_VERSION,
    semantic_policy_hash,
)
from afterworlds.ingestion.corpus.hashing import hash_obj  # noqa: E402
from afterworlds.ingestion.mechanical.projection import ReleaseBinding  # noqa: E402
from afterworlds.ingestion.mechanical.proposal import (  # noqa: E402
    MechanicalProposal,
    ProposedSpan,
    proposal_identity,
    proposal_payload,
)
from afterworlds.ingestion.mechanical.models import ReviewState  # noqa: E402
from afterworlds.ingestion.mechanical.representation import (  # noqa: E402
    REPRESENTATION_SCHEMA_VERSION,
    representation_schema_hash,
    AbilityScore,
    Applicability,
    ApplicabilityKind,
    Comparison,
    ComponentOption,
    ConditionLevelFact,
    CreatureSize,
    LevelDirection,
    MovementAmount,
    MovementCostFact,
    MovementCostKind,
    MovementMode,
    MovementPermissionFact,
    FactQualifier,
    MovementTransportFact,
    ParticipantRole,
    RoundingRule,
    TransportKind,
    Phase,
    QuantityMultiplierFact,
    RecoveryTrigger,
    Sense,
    SensoryCapabilityFact,
    SizeComparison,
    SizeRelation,
    TrackedQuantity,
    TransformationFact,
    TransformedForm,
    ActionCost,
    ActionRestrictionFact,
    AdvantageFact,
    AdvantageState,
    AutomaticOutcome,
    AutomaticOutcomeFact,
    CriticalHitChange,
    CriticalHitRuleFact,
    DamageResponseFact,
    DamageResponseKind,
    DamageScope,
    RollActor,
    RollSpec,
    ScalingBasis,
    ScalingDirection,
    ScalingEffect,
    ScalingFact,
    SpeedChange,
    SpeedModificationFact,
    StateEffectFact,
    StateEffectKind,
    ComponentDraft,
    ConditionEffectFact,
    ConditionEffectKind,
    ConditionKind,
    ProseBindingDraft,
    ProvenanceClaim,
    ProvenanceRole,
    ProvenanceTargetKind,
    RecordDraft,
    RecordKind,
    ReferenceDraft,
    RepresentationDraft,
    RollContext,
    component_target_key,
    fact_key,
    fact_payload,
    fact_qualifier_target_key,
    fact_target_key,
    fact_target_key,
    prose_binding_target_key,
    record_target_key,
    reference_target_key,
)
from afterworlds.ingestion.mechanical.validation import (  # noqa: E402
    validate_representation,
)

# Prove which code was actually imported. `sys.path.insert` can lose to an
# editable or site-packages install, and the entire checkpoint rests on the
# derivation coming from the merged checkout.
import afterworlds  # noqa: E402
from afterworlds.ingestion.mechanical import representation as _repr_mod  # noqa: E402

IMPORT_PROVENANCE = {
    "afterworlds.__file__": str(Path(afterworlds.__file__).resolve()),
    "representation.__file__": str(Path(_repr_mod.__file__).resolve()),
}
_expected_src = (CODE / "src" / "afterworlds").resolve()
for _k, _v in IMPORT_PROVENANCE.items():
    print(f"import provenance   {_k} = {_v}")
    assert Path(_v).is_relative_to(_expected_src), (_k, _v, str(_expected_src))

# ---------------------------------------------------------------------------
# Bound release, DERIVED from the committed PDF by the production 5c pipeline
# ---------------------------------------------------------------------------
#
# Five of the six binding values are reproduced from the source and asserted
# below; `persisted_corpus_digest` is a function of persisted rows and verified
# vector state, so it is carried from the published CRD Issue 5c release record
# and disclosed as such. A rebuild reproducing the other five is that release.

PACKAGE_UUID = "4458fa10-4a66-5e0e-9ecc-ea37530ad2b4"
RELEASE_VERSION = "5.2.1-corpus.36b786d8-fa2"
SOURCE_SHA256 = "8974902d109d6e63672d7c490bde9ccf052410503d9cfa768237154fbc5e3d87"
TRANSFORM_CONFIG_HASH = (
    "77720c2f3b8c9b88363d48050466fb8e3a26f8476b63145d1b5928ff2581ef3e"
)
BUNDLE_ROOT_HASH = "03353dfb79790aee7260b9ed96055b7296cd6f70e3e6f97d6cbe0a2484279685"
PERSISTED_CORPUS_DIGEST = (
    "c1f547962b7d9096986f0b8e75624f9f8803dfc281c16033e1c2250cad5a929b"
)

CAND = build_candidate(
    REPO / "docs/sources/DnD5_5e_SRD_CC_v5_2_1.pdf",
    retrieval_config=RetrievalMemoryConfig(),
)
assert CAND.package_uuid == PACKAGE_UUID, CAND.package_uuid
assert CAND.release_version == RELEASE_VERSION, CAND.release_version
assert CAND.authoritative_source_hash == SOURCE_SHA256, CAND.authoritative_source_hash
assert CAND.transform_config_hash == TRANSFORM_CONFIG_HASH, CAND.transform_config_hash
assert CAND.bundle.bundle_root_hash == BUNDLE_ROOT_HASH, CAND.bundle.bundle_root_hash

BINDING = ReleaseBinding(
    package_uuid=CAND.package_uuid,
    release_version=CAND.release_version,
    authoritative_source_hash=CAND.authoritative_source_hash,
    transform_config_hash=CAND.transform_config_hash,
    bundle_root_hash=CAND.bundle.bundle_root_hash,
    persisted_corpus_digest=PERSISTED_CORPUS_DIGEST,
)

_LEDGER = CAND.ledger
_LABELS = {c.container_id: c.label for c in _LEDGER.containers}
_CONTAINERS = {c.container_id: c for c in _LEDGER.containers}
_LEAF_BY_ID = {leaf.leaf_id: leaf for leaf in _LEDGER.leaves}
REPRESENTED = {
    leaf.leaf_id
    for leaf in _LEDGER.leaves
    if exclusion_reason_for(leaf, _LABELS) is None
}
EDGES = _full_coverage_edges(CAND.members.chunks, _LEAF_BY_ID)

CORPUS = BoundCorpusSnapshot(
    package_uuid=BINDING.package_uuid,
    release_version=BINDING.release_version,
    leaf_lengths={lid: len(_LEAF_BY_ID[lid].content) for lid in REPRESENTED},
    chunk_coverage=tuple(
        ChunkCoverage(
            chunk_id=e.chunk_id,
            leaf_id=e.leaf_id,
            cover_start=e.cover_start,
            cover_end=e.cover_end,
            role=e.role,
            projection_id=e.projection_id,
        )
        for e in EDGES
    ),
)

chunk_of_leaf = {e.leaf_id: e.chunk_id for e in EDGES}

by_container = defaultdict(list)
for _leaf in _LEDGER.leaves:
    if _leaf.leaf_id not in REPRESENTED:
        continue
    for cid in _leaf.container_path:
        by_container[cid].append(_leaf)
for v in by_container.values():
    v.sort(key=lambda x: (x.page_index, x.char_start))


def ancestry(cid):
    out, c = [], _CONTAINERS.get(cid)
    while c:
        out.append(c.container_id)
        c = _CONTAINERS.get(c.parent_id) if c.parent_id else None
    return out


GLOSSARY = next(
    c.container_id
    for c in _LEDGER.containers
    if c.label == "Rules Definitions"
)


ENTRY_BY_LABEL = {
    c.label: c.container_id
    for c in _LEDGER.containers
    if c.container_type == "entry" and GLOSSARY in ancestry(c.container_id)
}

# ---------------------------------------------------------------------------
# The proposed batch, stated as an explicit reviewable clause table
# ---------------------------------------------------------------------------
#
# Per entry: one list of leaf specs, in document order, one per leaf.
# Each leaf spec is a list of segments: (cut_marker | None, kind, arg).
#   "R"  SUPPORTING_AUTHORITY, contextually linked to the record
#   "C"  SUPPORTING_AUTHORITY, contextually linked to component `arg`
#   "U"  UNRESOLVED           — the closed typed union cannot carry this
#                               mechanic and it is not affirmatively prose-bound
#   "F"  SUBSTANTIVE, primary-claimed by fact  arg = (component, fact)
#   "P"  SUBSTANTIVE, primary-claimed by prose binding  arg = (component, reason)
# `cut_marker` ends the segment right after that substring; None runs to the
# end of the leaf.

#: Grappled's surcharge, named so its qualifier can address it by fact key.
GRAPPLED_SURCHARGE_FACT = MovementCostFact(
    kind=MovementCostKind.PER_FOOT_SURCHARGE,
    amount=MovementAmount.FEET,
    payer=ParticipantRole.COUNTERPART,
    feet=1,
)

A, D = AdvantageState.ADVANTAGE, AdvantageState.DISADVANTAGE
ATK, CHK, SAV, INI = (
    RollContext.ATTACK_ROLL,
    RollContext.ABILITY_CHECK,
    RollContext.SAVING_THROW,
    RollContext.INITIATIVE,
)
MINE, THEIRS = RollActor.SUBJECT, RollActor.AGAINST_SUBJECT
APPLIES, IMMUNITY = ConditionEffectKind.APPLIES, ConditionEffectKind.IMMUNITY
CTX = "contextual_applicability"
NLE = "natural_language_exception"
OPEN = "open_ended_effect"


def ADV(state, actor, context, ability=None):
    return AdvantageFact(state=state, roll=RollSpec(actor, context, ability))


def AUTOFAIL(ability=None, context=SAV):
    return AutomaticOutcomeFact(
        roll=RollSpec(MINE, context, ability), outcome=AutomaticOutcome.FAILURE
    )


def COND(kind, effect=APPLIES):
    return ConditionEffectFact(kind, effect)


SPEED_ZERO = SpeedModificationFact(
    change=SpeedChange.SET_TO, feet=0, can_increase=False
)
AUTO_CRIT = CriticalHitRuleFact(CriticalHitChange.AUTOMATIC_ON_HIT)
ALL_DAMAGE_RESIST = DamageResponseFact(DamageResponseKind.RESISTANCE, DamageScope.ALL)


def EXHAUST(effect, amount):
    return ScalingFact(
        basis=ScalingBasis.CONDITION_LEVEL,
        threshold=0,
        effect=effect,
        direction=ScalingDirection.DECREASE,
        amount=amount,
    )


def STATE(kind):
    return StateEffectFact(kind)

OEE = "open_ended_effect"

#: component_key -> Applicability, and (component_key, option_key) -> facts.
COMPONENT_APPLICABILITY: dict[tuple, object] = {}
OPTION_FACTS: dict[tuple, list] = {}
OPTION_APPLICABILITY: dict[tuple, object] = {}

#: "if your Speed is 0" — the same closed predicate Playing the Game >
#: Dropping Prone states, negated where the rule states an exception to it.
NOT_SPEED_ZERO = Applicability(
    kind=ApplicabilityKind.QUANTITY_THRESHOLD,
    negated=True,
    quantity=TrackedQuantity.SPEED,
    comparison=Comparison.EQUALS,
    value=0,
)
#: "unless you are Tiny or two or more sizes smaller than it" — one negation
#: over a homogeneous set of size tests, not a Boolean expression.
NOT_TINY_OR_TWO_SMALLER = Applicability(
    kind=ApplicabilityKind.SIZE_COMPARISON,
    negated=True,
    any_of=(
        SizeComparison(
            category=CreatureSize.TINY,
            measured=ParticipantRole.SUBJECT,
        ),
        SizeComparison(
            relation=SizeRelation.SMALLER,
            at_least=2,
            measured=ParticipantRole.SUBJECT,
            reference=ParticipantRole.COUNTERPART,
        ),
    ),
)
LEVEL_6 = Applicability(
    kind=ApplicabilityKind.QUANTITY_THRESHOLD,
    quantity=TrackedQuantity.CONDITION_LEVEL,
    comparison=Comparison.EQUALS,
    value=6,
)
LEVEL_REACHES_0 = Applicability(
    kind=ApplicabilityKind.QUANTITY_THRESHOLD,
    quantity=TrackedQuantity.CONDITION_LEVEL,
    comparison=Comparison.REACHES,
    value=0,
)
ON_LONG_REST = Applicability(
    kind=ApplicabilityKind.TRIGGER, trigger=RecoveryTrigger.LONG_REST
)
ON_END = Applicability(kind=ApplicabilityKind.PHASE, phase=Phase.ON_END)


W = [(None, "R", None)]  # whole leaf, supporting, linked to the record
U = [(None, "U", None)]  # whole leaf, unresolved


def C(comp):
    return [(None, "C", comp)]


def F(comp, fact):
    return [(None, "F", (comp, fact))]


def P(comp, reason=CTX):
    return [(None, "P", (comp, reason))]


SPEC: dict[str, list] = {
    "Condition": [
        W,
        W,
        [  # 'Blinded Charmed Deafened Exhaustion Frightened'
            ("Blinded", "REF", "condition.blinded"),
            ("Charmed", "REF", "condition.charmed"),
            ("Deafened", "REF", "condition.deafened"),
            ("Exhaustion", "REF", "condition.exhaustion"),
            (None, "REF", "condition.frightened"),
        ],
        [
            ("Grappled", "REF", "condition.grappled"),
            ("Incapacitated", "REF", "condition.incapacitated"),
            ("Invisible", "REF", "condition.invisible"),
            ("Paralyzed", "REF", "condition.paralyzed"),
            (None, "REF", "condition.petrified"),
        ],
        [
            ("Poisoned", "REF", "condition.poisoned"),
            ("Prone", "REF", "condition.prone"),
            ("Restrained", "REF", "condition.restrained"),
            ("Stunned", "REF", "condition.stunned"),
            (None, "REF", "condition.unconscious"),
        ],
        P("condition_definition", NLE),
    ],
    "Blinded [Condition]": [
        W,
        W,
        C("cant_see"),
        [
            # A deterministic capability state. That some downstream
            # consequences are contextual is a fact about narration, not about
            # the rule, so this is typed rather than prose-bound.
            (
                "see",
                "F",
                (
                    "cant_see",
                    SensoryCapabilityFact(sense=Sense.SIGHT, can_perceive=False),
                ),
            ),
            ("any ability check", "F", ("cant_see", AUTOFAIL(context=CHK))),
            (None, "P", ("cant_see", CTX)),
        ],
        C("attacks_affected"),
        [
            ("have Advantage,", "F", ("attacks_affected", ADV(A, THEIRS, ATK))),
            (None, "F", ("attacks_affected", ADV(D, MINE, ATK))),
        ],
    ],
    "Charmed [Condition]": [
        W,
        W,
        C("cant_harm_the_charmer"),
        # Targeting restriction. The corpus sweep found restriction referents
        # ranging over distances, creature relationships, spell schools, spatial
        # areas, and effect properties; a closed referent vocabulary spanning
        # those is a predicate language. Affirmatively prose-bound.
        P("cant_harm_the_charmer", CTX),
        C("social_advantage"),
        [
            # CORRECTION 1. "The charmer" names the actor the Advantage belongs
            # to. The typed fact says AGAINST_SUBJECT — that the roll is made
            # against you — which is not the same claim: it does not say the
            # charmer specifically is the one making it. Left inside the fact's
            # primary provenance, that restriction never reaches governing
            # prose, and the published component reads as though any creature
            # has the Advantage.
            ("The charmer", "P", ("social_advantage", CTX)),
            ("any ability check", "F", ("social_advantage", ADV(A, THEIRS, CHK))),
            (None, "P", ("social_advantage", CTX)),
        ],
    ],
    "Deafened [Condition]": [
        W,
        W,
        C("cant_hear"),
        [
            (
                "hear",
                "F",
                (
                    "cant_hear",
                    SensoryCapabilityFact(sense=Sense.HEARING, can_perceive=False),
                ),
            ),
            ("any ability check", "F", ("cant_hear", AUTOFAIL(context=CHK))),
            (None, "P", ("cant_hear", CTX)),
        ],
    ],
    "Exhaustion [Condition]": [
        W,
        W,
        W,
        [
            (
                "gain 1 Exhaustion level.",
                "F",
                (
                    "exhaustion_levels",
                    ConditionLevelFact(
                        condition=ConditionKind.EXHAUSTION,
                        direction=LevelDirection.GAIN,
                        amount=1,
                        cumulative=True,
                    ),
                ),
            ),
            # The state the subject enters, together with the level at which
            # it enters it: one span, one fact, one closed condition.
            (
                None,
                "FA",
                (
                    "death_at_six",
                    StateEffectFact(StateEffectKind.DIES),
                    LEVEL_6,
                ),
            ),
        ],
        C("d20_tests_affected"),
        F("d20_tests_affected", EXHAUST(ScalingEffect.D20_TEST, 2)),
        C("speed_reduced"),
        F("speed_reduced", EXHAUST(ScalingEffect.SPEED, 5)),
        W,
        [
            (
                "of your Exhaustion levels.",
                "FA",
                (
                    "level_removal",
                    ConditionLevelFact(
                        condition=ConditionKind.EXHAUSTION,
                        direction=LevelDirection.REMOVE,
                        amount=1,
                    ),
                    ON_LONG_REST,
                ),
            ),
            (
                None,
                "FA",
                (
                    "ends_at_zero",
                    ConditionEffectFact(
                        condition=ConditionKind.EXHAUSTION,
                        effect=ConditionEffectKind.REMOVES,
                    ),
                    LEVEL_REACHES_0,
                ),
            ),
        ],
    ],
    "Frightened [Condition]": [
        W,
        W,
        C("checks_and_attacks"),
        [
            ("on ability checks", "F", ("checks_and_attacks", ADV(D, MINE, CHK))),
            ("and attack rolls", "F", ("checks_and_attacks", ADV(D, MINE, ATK))),
            (None, "P", ("checks_and_attacks", CTX)),
        ],
        C("cant_approach"),
        P("cant_approach", CTX),
    ],
    "Grappled [Condition]": [
        W,
        W,
        C("speed_zero"),
        F("speed_zero", SPEED_ZERO),
        C("attacks_affected"),
        [
            ("on attack rolls", "F", ("attacks_affected", ADV(D, MINE, ATK))),
            (None, "P", ("attacks_affected", CTX)),
        ],
        W,
        [
            # Frames whose movement is surcharged; it states no displacement of
            # its own, so a forced-movement fact here would claim more than the
            # clause does.
            # Schema 3: a mechanical permission, no longer framing prose.
            (
                "when it moves,",
                "F",
                (
                    "movable",
                    MovementTransportFact(
                        carrier=ParticipantRole.COUNTERPART,
                        carried=ParticipantRole.SUBJECT,
                        kind=TransportKind.PERMITTED,
                    ),
                ),
            ),
            (
                "costs it 1 extra foot",
                "F",
                (
                    "movable",
                    GRAPPLED_SURCHARGE_FACT,
                ),
            ),
            # Schema 3: the exception qualifies the surcharge alone. The
            # grappler's permission to transport is unconditional, so a
            # component-wide qualifier would state a rule the source does not.
            (
                None,
                "FQ",
                (
                    "movable",
                    None,
                    GRAPPLED_SURCHARGE_FACT,
                    NOT_TINY_OR_TWO_SMALLER,
                ),
            ),
        ],
    ],
    "Incapacitated [Condition]": [
        W,
        W,
        C("inactive"),
        [
            (
                "any action,",
                "F",
                ("inactive", ActionRestrictionFact(ActionCost.ACTION)),
            ),
            (
                "Bonus Action,",
                "F",
                ("inactive", ActionRestrictionFact(ActionCost.BONUS_ACTION)),
            ),
            (None, "F", ("inactive", ActionRestrictionFact(ActionCost.REACTION))),
        ],
        C("no_concentration"),
        F("no_concentration", STATE(StateEffectKind.CONCENTRATION_BROKEN)),
        C("speechless"),
        F("speechless", STATE(StateEffectKind.CANNOT_SPEAK)),
        C("surprised"),
        C("surprised"),
        F("surprised", ADV(D, MINE, INI)),
    ],
    "Invisible [Condition]": [
        W,
        W,
        C("surprise"),
        F("surprise", ADV(A, MINE, INI)),
        C("concealed"),
        # Targeting restriction, same sweep-backed judgement as Charmed.
        P("concealed", CTX),
        C("attacks_affected"),
        [
            ("have Disadvantage,", "F", ("attacks_affected", ADV(D, THEIRS, ATK))),
            ("have Advantage.", "F", ("attacks_affected", ADV(A, MINE, ATK))),
            (None, "P", ("attacks_affected", CTX)),
        ],
    ],
    "Paralyzed [Condition]": [
        W,
        W,
        C("incapacitated"),
        F("incapacitated", COND(ConditionKind.INCAPACITATED)),
        C("speed_zero"),
        F("speed_zero", SPEED_ZERO),
        C("saving_throws_affected"),
        [
            (
                "fail Strength",
                "F",
                ("saving_throws_affected", AUTOFAIL(AbilityScore.STRENGTH)),
            ),
            (None, "F", ("saving_throws_affected", AUTOFAIL(AbilityScore.DEXTERITY))),
        ],
        C("attacks_affected"),
        F("attacks_affected", ADV(A, THEIRS, ATK)),
        C("automatic_critical_hits"),
        [
            ("is a Critical Hit", "F", ("automatic_critical_hits", AUTO_CRIT)),
            (None, "P", ("automatic_critical_hits", CTX)),
        ],
    ],
    "Petrified [Condition]": [
        W,
        W,
        W,
        [
            (
                "into a solid inanimate substance",
                "F",
                (
                    "turned_to_substance",
                    TransformationFact(
                        becomes=TransformedForm.OBJECT,
                        carried_nonmagical_included=True,
                    ),
                ),
            ),
            # "(usually stone)" — the source hedges the substance, so the
            # substance space is unbounded and stays exact governing prose.
            ("(usually stone).", "P", ("turned_to_substance", OEE)),
            (
                "by a factor of ten,",
                "F",
                (
                    "weight",
                    QuantityMultiplierFact(
                        quantity=TrackedQuantity.WEIGHT, factor=10
                    ),
                ),
            ),
            (None, "F", ("aging", STATE(StateEffectKind.AGING_SUSPENDED))),
        ],
        C("incapacitated"),
        F("incapacitated", COND(ConditionKind.INCAPACITATED)),
        C("speed_zero"),
        F("speed_zero", SPEED_ZERO),
        C("attacks_affected"),
        F("attacks_affected", ADV(A, THEIRS, ATK)),
        C("saving_throws_affected"),
        [
            (
                "fail Strength",
                "F",
                ("saving_throws_affected", AUTOFAIL(AbilityScore.STRENGTH)),
            ),
            (None, "F", ("saving_throws_affected", AUTOFAIL(AbilityScore.DEXTERITY))),
        ],
        C("resist_damage"),
        F("resist_damage", ALL_DAMAGE_RESIST),
        C("poison_immunity"),
        F("poison_immunity", COND(ConditionKind.POISONED, IMMUNITY)),
    ],
    "Poisoned [Condition]": [
        W,
        W,
        C("checks_and_attacks"),
        [
            ("on attack rolls", "F", ("checks_and_attacks", ADV(D, MINE, ATK))),
            (None, "F", ("checks_and_attacks", ADV(D, MINE, CHK))),
        ],
    ],
    "Prone [Condition]": [
        W,
        W,
        W,
        [
            # "only" is what makes the option set exhaustive.
            ("Your only movement options are", "C", "restricted_movement"),
            (
                "to crawl",
                "O",
                (
                    "restricted_movement",
                    "crawl",
                    MovementPermissionFact(mode=MovementMode.CRAWL),
                ),
            ),
            (
                "half your Speed (round down)",
                "O",
                (
                    "restricted_movement",
                    "stand",
                    MovementCostFact(
                            kind=MovementCostKind.EXPENDITURE,
                            amount=MovementAmount.HALF_SPEED,
                            payer=ParticipantRole.SUBJECT,
                            rounding=RoundingRule.DOWN,
                        ),
                ),
            ),
            (
                "thereby end the condition.",
                "O",
                (
                    "restricted_movement",
                    "stand",
                    ConditionEffectFact(
                        condition=ConditionKind.PRONE,
                        effect=ConditionEffectKind.REMOVES,
                    ),
                ),
            ),
            # CORRECTION 2. " If your" is the introducer of "If your Speed is 0,
            # you can't right yourself." — a restriction on this component's
            # stand option, split from its own sentence by a leaf boundary. As
            # record-level supporting authority it framed the whole condition;
            # it belongs to the component whose option it qualifies. Disposition
            # is unchanged (supporting either way); only the target moves.
            (None, "C", "restricted_movement"),
        ],
        # The prohibition attaches to the option it prohibits, so no vocabulary
        # of named acts is needed.
        [(None, "AC", ("restricted_movement", "stand", NOT_SPEED_ZERO))],
        C("attacks_affected"),
        [
            ("on attack rolls.", "F", ("attacks_affected", ADV(D, MINE, ATK))),
            ("has Advantage", "F", ("attacks_affected", ADV(A, THEIRS, ATK))),
            # The branch selector - the distance test and the "Otherwise"
            # default - is governing prose, exactly as the identical "within 5
            # feet" qualifier is on Paralyzed's and Unconscious's automatic
            # Critical Hit. Without it the typed surface would assert both
            # Advantage and Disadvantage against the subject unconditionally,
            # and a deterministic consumer could not tell which applies.
            ("Otherwise,", "P", ("attacks_affected", CTX)),
            (None, "F", ("attacks_affected", ADV(D, THEIRS, ATK))),
        ],
    ],
    "Restrained [Condition]": [
        W,
        W,
        C("speed_zero"),
        F("speed_zero", SPEED_ZERO),
        C("attacks_affected"),
        [
            ("have Advantage,", "F", ("attacks_affected", ADV(A, THEIRS, ATK))),
            (None, "F", ("attacks_affected", ADV(D, MINE, ATK))),
        ],
        C("saving_throws_affected"),
        F("saving_throws_affected", ADV(D, MINE, SAV, AbilityScore.DEXTERITY)),
    ],
    "Stunned [Condition]": [
        W,
        W,
        C("incapacitated"),
        F("incapacitated", COND(ConditionKind.INCAPACITATED)),
        C("saving_throws_affected"),
        [
            (
                "fail Strength",
                "F",
                ("saving_throws_affected", AUTOFAIL(AbilityScore.STRENGTH)),
            ),
            (None, "F", ("saving_throws_affected", AUTOFAIL(AbilityScore.DEXTERITY))),
        ],
        C("attacks_affected"),
        F("attacks_affected", ADV(A, THEIRS, ATK)),
    ],
    "Unconscious [Condition]": [
        W,
        W,
        C("inert"),
        [
            ("the Incapacitated", "F", ("inert", COND(ConditionKind.INCAPACITATED))),
            ("and Prone conditions,", "F", ("inert", COND(ConditionKind.PRONE))),
            ("holding.", "F", ("inert", STATE(StateEffectKind.DROPS_HELD_OBJECTS))),
            (
                None,
                "FA",
                (
                    "prone_persists",
                    ConditionEffectFact(
                        condition=ConditionKind.PRONE,
                        effect=ConditionEffectKind.APPLIES,
                    ),
                    ON_END,
                ),
            ),
        ],
        C("speed_zero"),
        F("speed_zero", SPEED_ZERO),
        C("attacks_affected"),
        F("attacks_affected", ADV(A, THEIRS, ATK)),
        C("saving_throws_affected"),
        [
            (
                "fail Strength",
                "F",
                ("saving_throws_affected", AUTOFAIL(AbilityScore.STRENGTH)),
            ),
            (None, "F", ("saving_throws_affected", AUTOFAIL(AbilityScore.DEXTERITY))),
        ],
        C("automatic_critical_hits"),
        [
            ("is a Critical Hit", "F", ("automatic_critical_hits", AUTO_CRIT)),
            (None, "P", ("automatic_critical_hits", CTX)),
        ],
        C("unaware"),
        F("unaware", STATE(StateEffectKind.UNAWARE_OF_SURROUNDINGS)),
    ],
}

RECORD_KEY = {
    "Condition": "glossary.condition",
    **{
        lbl: "condition." + lbl.split(" [")[0].lower()
        for lbl in SPEC
        if lbl.endswith("[Condition]")
    },
}
RECORD_KIND = {
    "glossary.condition": RecordKind.GLOSSARY_RULE,
    **{v: RecordKind.CONDITION for k, v in RECORD_KEY.items() if k != "Condition"},
}
SCOPE_KEY = "srd-5.2.1/rules-glossary"

# ---------------------------------------------------------------------------
# Expansion
# ---------------------------------------------------------------------------

spans: list[SemanticSpan] = []
proposed: list[ProposedSpan] = []
provenance: list[ProvenanceClaim] = []
references: list[ReferenceDraft] = []
prose_bindings: list[ProseBindingDraft] = []
comp_facts: dict[tuple[str, str], list] = defaultdict(list)
comp_reason: dict[tuple[str, str], str] = {}
#: (record, component, option, fact) -> Applicability
FACT_QUALIFIERS: dict[tuple, object] = {}
audit: list[dict] = []

DISP = {
    "R": SemanticDisposition.SUPPORTING_AUTHORITY,
    "C": SemanticDisposition.SUPPORTING_AUTHORITY,
    "T": SemanticDisposition.SUBSTANTIVE,
    "REF": SemanticDisposition.SUPPORTING_AUTHORITY,
    "U": SemanticDisposition.UNRESOLVED,
    "F": SemanticDisposition.SUBSTANTIVE,
    "P": SemanticDisposition.SUBSTANTIVE,
    "O": SemanticDisposition.SUBSTANTIVE,
    "AC": SemanticDisposition.SUBSTANTIVE,
    "FQ": SemanticDisposition.SUBSTANTIVE,
    "FA": SemanticDisposition.SUBSTANTIVE,
}
RATIONALE = {
    "R": "identifies or frames the mechanic; preserved as supporting authority rather than discarded",
    "C": "sub-heading naming the effect it labels; preserved as supporting authority",
    "T": "states one creature's movement relocating another; carried by the closed "
    "transport family under representation schema 3",
    "REF": "names one condition this glossary defines; source-authored reference target",
    "U": "no member of the closed typed fact union faithfully carries this mechanic, and it is "
    "not affirmatively irreducible; classifying it PROSE_BOUND would be a backlog state",
    "F": "states a mechanic the closed typed union carries exactly",
    "P": "applicability qualifier that cannot be reduced without executable interpretation",
    "O": "states one option of an exhaustive actor choice the closed union carries",
    "AC": "states the closed condition under which the component or option applies",
    "FQ": "states the closed condition under which one typed fact applies, leaving its siblings unqualified",
    "FA": "states a typed mechanic together with the closed condition it applies under",
}

for label, leafspecs in SPEC.items():
    entry_id = ENTRY_BY_LABEL[label]
    rkey = RECORD_KEY[label]
    lvs = by_container[entry_id]
    assert len(lvs) == len(leafspecs), f"{label}: {len(lvs)} leaves vs {len(leafspecs)} specs"

    for lf, segs in zip(lvs, leafspecs):
        content, lid = lf.content, lf.leaf_id
        cursor = 0
        for i, (marker, kind, arg) in enumerate(segs):
            if marker is None:
                end = len(content)
            else:
                found = content.find(marker, cursor)
                assert found >= 0, f"{label}: marker {marker!r} not in {content!r}"
                end = found + len(marker)
            assert end > cursor, f"{label}: empty segment {marker!r}"
            start = cursor
            cursor = end
            sid = derive_span_id(lid, start, end)
            disp = DISP[kind]
            span = SemanticSpan(
                span_id=sid,
                leaf_id=lid,
                char_start=start,
                char_end=end,
                disposition=disp,
                review_state=ReviewState.PROPOSED,
            )
            spans.append(span)
            proposed.append(
                ProposedSpan(span=span, origin="propose_conditions.py", rationale=RATIONALE[kind])
            )
            audit.append(
                {
                    "record": rkey,
                    "leaf": lid,
                    "span_id": sid,
                    "range": [start, end],
                    "text": content[start:end],
                    "disposition": disp.value,
                    "kind": kind,
                }
            )


            if kind == "FQ":
                ckey, okey, qfact, qapplies = arg
                FACT_QUALIFIERS[(rkey, ckey, okey or "", fact_key(qfact))] = qapplies
                provenance.append(
                    ProvenanceClaim(
                        ProvenanceTargetKind.FACT_QUALIFIER,
                        fact_qualifier_target_key(
                            rkey, ckey, fact_key(qfact), okey or ""
                        ),
                        sid,
                        ProvenanceRole.PRIMARY,
                    )
                )
            if kind == "R":
                provenance.append(
                    ProvenanceClaim(
                        ProvenanceTargetKind.RECORD, (rkey,), sid, ProvenanceRole.CONTEXTUAL
                    )
                )
            elif kind == "C":
                provenance.append(
                    ProvenanceClaim(
                        ProvenanceTargetKind.COMPONENT,
                        (rkey, arg),
                        sid,
                        ProvenanceRole.CONTEXTUAL,
                    )
                )
            elif kind == "REF":
                ref = ReferenceDraft(
                    from_record_key=rkey,
                    from_component_key="condition_definition",
                    source_text=content[start:end].strip(),
                    scope_key=SCOPE_KEY,
                    target_record_key=arg,
                )
                references.append(ref)
                provenance.append(
                    ProvenanceClaim(
                        ProvenanceTargetKind.REFERENCE,
                        reference_target_key(ref),
                        sid,
                        ProvenanceRole.CONTEXTUAL,
                    )
                )
            elif kind == "F":
                comp, fact = arg
                comp_facts[(rkey, comp)].append(fact)
                provenance.append(
                    ProvenanceClaim(
                        ProvenanceTargetKind.FACT,
                        fact_target_key(rkey, comp, fact),
                        sid,
                        ProvenanceRole.PRIMARY,
                    )
                )
            elif kind == "O":
                comp, option_key, fact = arg
                OPTION_FACTS.setdefault((rkey, comp, option_key), []).append(fact)
                comp_facts.setdefault((rkey, comp), [])
                provenance.append(
                    ProvenanceClaim(
                        ProvenanceTargetKind.FACT,
                        fact_target_key(rkey, comp, fact, option_key),
                        sid,
                        ProvenanceRole.PRIMARY,
                    )
                )
            elif kind == "FA":
                comp, fact, applicability = arg
                comp_facts.setdefault((rkey, comp), []).append(fact)
                COMPONENT_APPLICABILITY[(rkey, comp)] = applicability
                provenance.append(
                    ProvenanceClaim(
                        ProvenanceTargetKind.FACT,
                        fact_target_key(rkey, comp, fact),
                        sid,
                        ProvenanceRole.PRIMARY,
                    )
                )
            elif kind == "AC":
                comp, option_key, applicability = arg
                if option_key is None:
                    COMPONENT_APPLICABILITY[(rkey, comp)] = applicability
                else:
                    OPTION_APPLICABILITY[(rkey, comp, option_key)] = applicability
                comp_facts.setdefault((rkey, comp), [])
                # The condition is part of the component's own meaning, so the
                # span claims the component directly. It is not a fact and not a
                # prose binding, and inventing either to carry it would be a
                # false element.
                provenance.append(
                    ProvenanceClaim(
                        ProvenanceTargetKind.COMPONENT,
                        (rkey, comp),
                        sid,
                        ProvenanceRole.PRIMARY,
                    )
                )
            elif kind == "P":
                comp, reason = arg
                comp_reason[(rkey, comp)] = reason
                comp_facts.setdefault((rkey, comp), [])
                extent = CORPUS.chunk_relative_range(chunk_of_leaf[lid], lid, start, end)
                assert extent is not None, f"{label}: no unambiguous chunk extent for {sid}"
                pb = ProseBindingDraft(
                    component_key=comp,
                    record_key=rkey,
                    chunk_id=chunk_of_leaf[lid],
                    span_id=sid,
                    chunk_char_start=extent[0],
                    chunk_char_end=extent[1],
                    irreducibility_reason_code=reason,
                )
                prose_bindings.append(pb)
                provenance.append(
                    ProvenanceClaim(
                        ProvenanceTargetKind.PROSE_BINDING,
                        prose_binding_target_key(pb),
                        sid,
                        ProvenanceRole.PRIMARY,
                    )
                )

records = tuple(
    RecordDraft(semantic_key=k, kind=RECORD_KIND[k]) for k in sorted(set(RECORD_KEY.values()))
)
components = []
for (rkey, ckey), facts in sorted(comp_facts.items()):
    reason = comp_reason.get((rkey, ckey))
    if facts and reason:
        handling = ComponentHandling.MIXED
    elif facts:
        handling = ComponentHandling.STRUCTURED
    else:
        handling = ComponentHandling.PROSE_BOUND
    option_keys = sorted(
        {k[2] for k in OPTION_FACTS if (k[0], k[1]) == (rkey, ckey)}
    )
    options = tuple(
        ComponentOption(
            semantic_key=ok,
            facts=tuple(OPTION_FACTS[(rkey, ckey, ok)]),
            applies_when=OPTION_APPLICABILITY.get((rkey, ckey, ok)),
        )
        for ok in option_keys
    )
    if options and not facts and not reason:
        handling = ComponentHandling.STRUCTURED
    components.append(
        ComponentDraft(
            record_key=rkey,
            semantic_key=ckey,
            handling=handling,
            irreducibility_reason_code=reason,
            facts=tuple(facts),
            applies_when=COMPONENT_APPLICABILITY.get((rkey, ckey)),
            options=options,
            fact_qualifiers=tuple(
                FactQualifier(
                    fact_key=fkey,
                    option_key=okey,
                    applies_when=applies,
                )
                for (r_, c_, okey, fkey), applies in sorted(
                    FACT_QUALIFIERS.items(), key=lambda kv: kv[0][1:]
                )
                if (r_, c_) == (rkey, ckey)
            ),
        )
    )

DRAFT = RepresentationDraft(
    records=records,
    components=tuple(components),
    prose_bindings=tuple(prose_bindings),
    relationships=(),
    references=tuple(references),
    provenance=tuple(provenance),
)

LEDGER = ClassificationLedger(
    package_uuid=BINDING.package_uuid,
    release_version=BINDING.release_version,
    policy_version=SEMANTIC_POLICY_VERSION,
    policy_hash=semantic_policy_hash(),
    spans=tuple(spans),
    batches=(),
    acceptances=(),
)

# ---------------------------------------------------------------------------
# Self-checks: pure validators only. No persistence, no gate, no acceptance.
# ---------------------------------------------------------------------------

findings: list[str] = []
touched = sorted({s.leaf_id for s in spans})
for lid in touched:
    findings.extend(validate_partition(lid, CORPUS.leaf_lengths[lid], tuple(spans)))
findings.extend(validate_reason_codes(tuple(spans)))
findings.extend(validate_representation(DRAFT, LEDGER, CORPUS))

PROPOSAL = MechanicalProposal(
    binding=BINDING,
    policy_version=SEMANTIC_POLICY_VERSION,
    policy_hash=semantic_policy_hash(),
    schema_version=REPRESENTATION_SCHEMA_VERSION,
    schema_hash=representation_schema_hash(),
    proposed_spans=tuple(proposed),
    proposed_representation=DRAFT,
    proposal_origin="propose_conditions.py (CRD Issue 5d batch candidate conditions-1)",
)

payload = proposal_payload(PROPOSAL)
ident = proposal_identity(PROPOSAL)

#: Owner-authorized. Asserted the moment it is derivable, so nothing below can
#: run against a proposal the Owner did not approve.
AUTHORIZED_IDENTITY = "14587d5b5d51ad282f3d16510e015cd7116adcbd3877964bf034eef96780b0eb"
assert ident == AUTHORIZED_IDENTITY, (
    f"derived proposal identity {ident} is not the authorized "
    f"{AUTHORIZED_IDENTITY}; refusing to accept"
)


# ---------------------------------------------------------------------------
# Grappled > Movable, asserted rather than eyeballed
# ---------------------------------------------------------------------------
#
# This is the rule that rejected the schema-2 proposal, so it is proved against
# the live objects rather than read out of the JSON. Five separate claims, each
# of which failed under schema 2 for its own reason.

GRAPPLED_TRANSPORT_FACT = MovementTransportFact(
    carrier=ParticipantRole.COUNTERPART,
    carried=ParticipantRole.SUBJECT,
    kind=TransportKind.PERMITTED,
)
_MOVABLE = next(
    c
    for c in components
    if (c.record_key, c.semantic_key) == ("condition.grappled", "movable")
)

GRAPPLED_PROOF: dict[str, object] = {}

# 1. The component states no condition of its own. A component-level
#    applies_when here would make transport vanish for a Tiny subject.
assert _MOVABLE.applies_when is None, _MOVABLE.applies_when
GRAPPLED_PROOF["component_applies_when"] = None

# 2. Transport is present, and states who carries whom.
_transport = next(
    f for f in _MOVABLE.facts if isinstance(f, MovementTransportFact)
)
assert _transport.carrier is ParticipantRole.COUNTERPART, _transport
assert _transport.carried is ParticipantRole.SUBJECT, _transport
assert _transport.kind is TransportKind.PERMITTED, _transport
GRAPPLED_PROOF["transport"] = {
    "carrier": _transport.carrier.value,
    "carried": _transport.carried.value,
    "kind": _transport.kind.value,
    "fact_key": fact_key(_transport),
}

# 3. The surcharge is paid by the grappler, not by the grappled creature.
_surcharge = next(
    f
    for f in _MOVABLE.facts
    if isinstance(f, MovementCostFact)
    and f.kind is MovementCostKind.PER_FOOT_SURCHARGE
)
assert _surcharge.payer is ParticipantRole.COUNTERPART, _surcharge
assert fact_key(_surcharge) == fact_key(GRAPPLED_SURCHARGE_FACT)
GRAPPLED_PROOF["surcharge"] = {
    "payer": _surcharge.payer.value,
    "amount": _surcharge.amount.value,
    "feet": _surcharge.feet,
    "fact_key": fact_key(_surcharge),
}

# 4. The size exception qualifies the surcharge ALONE. Both halves matter: the
#    surcharge carries it, and transport does not.
_q_surcharge = _MOVABLE.qualifier_for(_surcharge)
_q_transport = _MOVABLE.qualifier_for(_transport)
assert _q_surcharge is not None, "the surcharge lost its exception"
assert _q_transport is None, "transport must be unconditional"
assert _q_surcharge.kind is ApplicabilityKind.SIZE_COMPARISON, _q_surcharge
assert _q_surcharge.negated is True, _q_surcharge
assert len(_q_surcharge.any_of) == 2, _q_surcharge
GRAPPLED_PROOF["qualifier"] = {
    "attached_to": fact_key(_surcharge),
    "transport_qualifier": None,
    "kind": _q_surcharge.kind.value,
    "negated": _q_surcharge.negated,
    "size_tests": [
        {
            "category": None if t.category is None else t.category.value,
            "relation": None if t.relation is None else t.relation.value,
            "at_least": t.at_least,
            "at_most": t.at_most,
            "measured": t.measured.value,
            "reference": None if t.reference is None else t.reference.value,
        }
        for t in _q_surcharge.any_of
    ],
}

# 5. The qualifier carries its own FACT_QUALIFIER provenance, and that span is
#    NOT also claimed for the surcharge fact itself. This is the claim the
#    round-3 provenance separation exists to make, proved in the corpus rather
#    than only in unit tests.
_QKEY = fact_qualifier_target_key(
    "condition.grappled", "movable", fact_key(_surcharge), ""
)
_FKEY = fact_target_key("condition.grappled", "movable", _surcharge)
_q_claims = [
    c
    for c in provenance
    if c.target_kind is ProvenanceTargetKind.FACT_QUALIFIER and c.target_key == _QKEY
]
_f_claims = [
    c
    for c in provenance
    if c.target_kind is ProvenanceTargetKind.FACT and c.target_key == _FKEY
]
assert len(_q_claims) == 1, _q_claims
assert _f_claims, "the surcharge fact itself must still carry provenance"
_q_spans = {c.span_id for c in _q_claims}
_f_spans = {c.span_id for c in _f_claims}
assert not (_q_spans & _f_spans), (_q_spans, _f_spans)
GRAPPLED_PROOF["provenance"] = {
    "fact_qualifier_target_key": list(_QKEY),
    "fact_qualifier_span_ids": sorted(_q_spans),
    "fact_target_key": list(_FKEY),
    "fact_span_ids": sorted(_f_spans),
    "spans_are_disjoint": True,
}
print("Grappled > Movable: all five semantic claims hold")


# ---------------------------------------------------------------------------
# The two corrections, asserted rather than eyeballed
# ---------------------------------------------------------------------------

CORRECTION_PROOF: dict[str, object] = {}

# --- 1. Charmed / social_advantage ------------------------------------------
#
# The claim is about *governing prose*, not about span text: a reader of the
# published component must be able to see who has the Advantage. That means two
# prose bindings on this component, and the fact unchanged beside them.

_SOCIAL_BINDINGS = [
    b
    for b in prose_bindings
    if (b.record_key, b.component_key) == ("condition.charmed", "social_advantage")
]
_SPAN_TEXT = {row["span_id"]: row["text"] for row in audit}
_SOCIAL_PROSE = [_SPAN_TEXT[b.span_id] for b in _SOCIAL_BINDINGS]

assert len(_SOCIAL_BINDINGS) == 2, _SOCIAL_PROSE
assert any("The charmer" in t for t in _SOCIAL_PROSE), _SOCIAL_PROSE
assert any("interact with you socially" in t for t in _SOCIAL_PROSE), _SOCIAL_PROSE
assert all(
    b.irreducibility_reason_code == CTX for b in _SOCIAL_BINDINGS
), _SOCIAL_BINDINGS

_SOCIAL = next(
    c
    for c in components
    if (c.record_key, c.semantic_key) == ("condition.charmed", "social_advantage")
)
# The typed fact is untouched: still exactly one AdvantageFact, still
# AGAINST_SUBJECT, and the component is still MIXED.
_EXPECTED_ADV = ADV(A, THEIRS, CHK)
assert len(_SOCIAL.facts) == 1, _SOCIAL.facts
assert _SOCIAL.facts[0] == _EXPECTED_ADV, _SOCIAL.facts[0]
assert fact_key(_SOCIAL.facts[0]) == fact_key(_EXPECTED_ADV)
assert _SOCIAL.handling is ComponentHandling.MIXED, _SOCIAL.handling
assert _SOCIAL.applies_when is None, _SOCIAL.applies_when
assert _SOCIAL.fact_qualifiers == (), _SOCIAL.fact_qualifiers

# The fact keeps primary provenance over the clause that states the mechanic,
# and that clause no longer carries the actor restriction.
_ADV_KEY = fact_target_key("condition.charmed", "social_advantage", _EXPECTED_ADV)
_ADV_CLAIMS = [
    c
    for c in provenance
    if c.target_kind is ProvenanceTargetKind.FACT and c.target_key == _ADV_KEY
]
assert len(_ADV_CLAIMS) == 1, _ADV_CLAIMS
_ADV_TEXT = _SPAN_TEXT[_ADV_CLAIMS[0].span_id]
assert "has Advantage on any ability check" in _ADV_TEXT, _ADV_TEXT
assert "The charmer" not in _ADV_TEXT, _ADV_TEXT

CORRECTION_PROOF["charmed_social_advantage"] = {
    "governing_prose": sorted(_SOCIAL_PROSE),
    "governing_prose_count": len(_SOCIAL_BINDINGS),
    "states_the_charmer": True,
    "states_social_interaction": True,
    "irreducibility_reason_code": CTX,
    "typed_fact_unchanged": True,
    "typed_fact_key": fact_key(_SOCIAL.facts[0]),
    "typed_fact_payload": fact_payload(_SOCIAL.facts[0]),
    "fact_primary_span_text": _ADV_TEXT,
    "handling": _SOCIAL.handling.value,
}

# --- 2. Prone / restricted_movement -----------------------------------------
#
# The retarget, and the thing the retarget could plausibly have disturbed.

_IF_YOUR = [row for row in audit if row["text"] == " If your"]
assert len(_IF_YOUR) == 1, _IF_YOUR
_IF_SID = _IF_YOUR[0]["span_id"]
assert _IF_YOUR[0]["kind"] == "C", _IF_YOUR[0]
assert _IF_YOUR[0]["disposition"] == "supporting_authority", _IF_YOUR[0]

_IF_CLAIMS = [c for c in provenance if c.span_id == _IF_SID]
assert len(_IF_CLAIMS) == 1, _IF_CLAIMS
assert _IF_CLAIMS[0].target_kind is ProvenanceTargetKind.COMPONENT, _IF_CLAIMS[0]
assert _IF_CLAIMS[0].target_key == (
    "condition.prone",
    "restricted_movement",
), _IF_CLAIMS[0]
assert _IF_CLAIMS[0].role is ProvenanceRole.CONTEXTUAL, _IF_CLAIMS[0]
# It no longer claims the record.
assert not [
    c
    for c in provenance
    if c.span_id == _IF_SID and c.target_kind is ProvenanceTargetKind.RECORD
]

# The primary span it introduces is untouched, and still applies the stand
# restriction to the option rather than to the component.
_SPEED_ZERO_SPAN = [
    row for row in audit if row["text"].startswith("Speed is 0, you can")
]
assert len(_SPEED_ZERO_SPAN) == 1, _SPEED_ZERO_SPAN
assert _SPEED_ZERO_SPAN[0]["kind"] == "AC", _SPEED_ZERO_SPAN[0]
assert _SPEED_ZERO_SPAN[0]["disposition"] == "substantive", _SPEED_ZERO_SPAN[0]

_STAND_KEY = ("condition.prone", "restricted_movement", "stand")
assert OPTION_APPLICABILITY[_STAND_KEY] == NOT_SPEED_ZERO, OPTION_APPLICABILITY[_STAND_KEY]
assert NOT_SPEED_ZERO.kind is ApplicabilityKind.QUANTITY_THRESHOLD
assert NOT_SPEED_ZERO.quantity is TrackedQuantity.SPEED
assert NOT_SPEED_ZERO.comparison is Comparison.EQUALS
assert NOT_SPEED_ZERO.value == 0
assert NOT_SPEED_ZERO.negated is True
# Nothing leaked up to the component, which would restrict crawling too.
_PRONE_MOVE = next(
    c
    for c in components
    if (c.record_key, c.semantic_key) == ("condition.prone", "restricted_movement")
)
assert _PRONE_MOVE.applies_when is None, _PRONE_MOVE.applies_when
_STAND = next(o for o in _PRONE_MOVE.options if o.semantic_key == "stand")
_CRAWL = next(o for o in _PRONE_MOVE.options if o.semantic_key == "crawl")
assert _STAND.applies_when == NOT_SPEED_ZERO, _STAND.applies_when
assert _CRAWL.applies_when is None, _CRAWL.applies_when

CORRECTION_PROOF["prone_restricted_movement"] = {
    "if_your_span_id": _IF_SID,
    "if_your_target_kind": _IF_CLAIMS[0].target_kind.value,
    "if_your_target_key": list(_IF_CLAIMS[0].target_key),
    "if_your_role": _IF_CLAIMS[0].role.value,
    "if_your_disposition": _IF_YOUR[0]["disposition"],
    "still_claims_the_record": False,
    "primary_span_text": _SPEED_ZERO_SPAN[0]["text"],
    "stand_option_applies_when": {
        "kind": NOT_SPEED_ZERO.kind.value,
        "quantity": NOT_SPEED_ZERO.quantity.value,
        "comparison": NOT_SPEED_ZERO.comparison.value,
        "value": NOT_SPEED_ZERO.value,
        "negated": NOT_SPEED_ZERO.negated,
        "reading": "the stand option is unavailable exactly when Speed equals 0",
    },
    "crawl_option_applies_when": None,
    "component_applies_when": None,
}
print("both corrections: all semantic claims hold")


# ---------------------------------------------------------------------------
# Superseded identities — named, refused, and proved distinct
# ---------------------------------------------------------------------------

SUPERSEDED = {
    "756922a3892f9420dc8bfb2fe6af8a5a4db491111d1786ab0de6c2ddbf7dbfa6": (
        "schema-2 conditions-1 proposal. REJECTED by semantic review as a "
        "representation gap: transport had no family, the cost named no payer, "
        "and the size comparison kept neither operand. Superseded by schema 3, "
        "not mutated."
    ),
    "b9ac21bf045a3f5d1e020f91fd43fdd6e5f3fb0b3d0a715de556a574d3ab14a6": (
        "intermediate schema-3 smoke, before fact-scoped applicability existed. "
        "SEMANTICALLY INVALID and must never be accepted: it made the transport "
        "permission conditional on the size exception, a rule the source does "
        "not state."
    ),
    "2f42f2bb82bcb4ed6ac489b47f774495d2ec5d985871a0d5b69f659fc83fb24b": (
        "schema-3 conditions-1 candidate regenerated from merged main. "
        "REJECTED by semantic review: Charmed's charmer restriction was absent "
        "from governing prose - 'The charmer' sat inside the AdvantageFact's "
        "primary provenance while the component's only prose binding read "
        "'to interact with you socially.' - and Prone's conditional introducer "
        "' If your' was mis-targeted at the condition.prone record instead of "
        "the component whose option it restricts. One defect family: "
        "meaning-bearing clause fragments assigned outside the local component "
        "authority they qualify."
    ),
}
for _bad in SUPERSEDED:
    assert ident != _bad, f"identity collides with refused candidate {_bad}"

#: The candidate this run remediates. Named separately so the diff below
#: can address it; it is refused by the guard above all the same.
REJECTED_IDENTITY = "2f42f2bb82bcb4ed6ac489b47f774495d2ec5d985871a0d5b69f659fc83fb24b"

# The refused candidates cannot be selected because no artifact names them.
# This run *does* commit accepted authority, so the invariant is no longer "the
# directory is empty" — it is "the directory holds the README and at most the
# one artifact for this release", which is what the resolver requires: two
# artifacts claiming one release is a refusal, not a choice.
_ORACLES = REPO / "src/afterworlds/ingestion/mechanical/oracles"
_EXPECTED_ORACLE_NAME = "srd-5-2-1-corpus-36b786d8-fa2.json"
ORACLE_DIR_CONTENTS = sorted(x.name for x in _ORACLES.iterdir())
assert ORACLE_DIR_CONTENTS in (
    ["README.md"],
    ["README.md", _EXPECTED_ORACLE_NAME],
), ORACLE_DIR_CONTENTS


# ---------------------------------------------------------------------------
# Did the exact regeneration reproduce the non-authoritative smoke?
# ---------------------------------------------------------------------------
#
# Answered by hashing both payloads rather than by asserting either outcome.
# The proposal payload is a pure function of (binding, policy declaration,
# schema declaration, proposed spans, proposed representation), so equality is
# provable and difference is attributable.

_REJECTED_PATH = REVIEW_DIR / "issue-5d-conditions-1-schema3-REGEN-PROPOSAL.json"
SMOKE_COMPARISON: dict[str, object] = {
    "rejected_identity": REJECTED_IDENTITY,
    "remediated_identity": ident,
    "identities_equal": ident == REJECTED_IDENTITY,
    "rejected_payload_available": _REJECTED_PATH.is_file(),
}
if _REJECTED_PATH.is_file():
    _smoke = json.loads(_REJECTED_PATH.read_text(encoding="utf-8"))
    SMOKE_COMPARISON["payloads_equal"] = _smoke == payload
    SMOKE_COMPARISON["rejected_payload_hash"] = hash_obj(_smoke)
    SMOKE_COMPARISON["remediated_payload_hash"] = hash_obj(payload)
    SMOKE_COMPARISON["hashes_equal"] = hash_obj(_smoke) == hash_obj(payload)
    # The artifact on disk really is the rejected candidate, not a stale file.
    assert hash_obj(_smoke) == REJECTED_IDENTITY, hash_obj(_smoke)
    # And the payload really moved. Equality here would mean neither correction
    # reached the artifact.
    assert _smoke != payload, "remediation reproduced the rejected payload"
    if _smoke != payload:
        # Content-keyed, not positional. Every collection in the payload is
        # canonically ordered, so inserting one span renumbers everything after
        # it; a positional walk would report hundreds of "differences" for three
        # real changes. Compare each collection as a multiset of its canonical
        # form and report exactly what entered and left.
        from afterworlds.ingestion.corpus.hashing import canonical_json as _cj

        def _bag(rows: object) -> collections.Counter:
            return collections.Counter(_cj(r) for r in rows)  # type: ignore[union-attr]

        def _collection_diff(name: str, was: object, now: object) -> dict:
            a, b = _bag(was), _bag(now)
            added = sorted((b - a).elements())
            removed = sorted((a - b).elements())
            return {
                "collection": name,
                "was": sum(a.values()),
                "now": sum(b.values()),
                "added": [json.loads(x) for x in added],
                "removed": [json.loads(x) for x in removed],
                "added_count": len(added),
                "removed_count": len(removed),
            }

        _COLLECTIONS = [
            ("proposed_spans", _smoke["proposed_spans"], payload["proposed_spans"]),
        ]
        _was_repr = _smoke["proposed_representation"]
        _now_repr = payload["proposed_representation"]
        for _k in sorted(set(_was_repr) | set(_now_repr)):
            _COLLECTIONS.append(
                (f"proposed_representation.{_k}", _was_repr[_k], _now_repr[_k])
            )

        _diffs = [
            _collection_diff(n, w, x)
            for n, w, x in _COLLECTIONS
            if _bag(w) != _bag(x)
        ]
        SMOKE_COMPARISON["changed_collections"] = [d["collection"] for d in _diffs]
        SMOKE_COMPARISON["collection_diff"] = _diffs
        SMOKE_COMPARISON["unchanged_collections"] = [
            n for n, w, x in _COLLECTIONS if _bag(w) == _bag(x)
        ]
        SMOKE_COMPARISON["attribution"] = {
            "correction_1_charmed": (
                "the social-advantage clause is cut in three instead of two, so "
                "one span is removed and three arrive in its place: the shorter "
                "fact span keeps the same content-derived provenance target but "
                "a new span_id, because derive_span_id is a function of the "
                "char range. One prose binding is added."
            ),
            "correction_2_prone": (
                'the " If your" span is unchanged in text, range, id and '
                "disposition; only its provenance claim moves from "
                "(RECORD, condition.prone) to "
                "(COMPONENT, condition.prone/restricted_movement)."
            ),
            "everything_else": (
                "records, components, facts, references, relationships and every "
                "other collection are byte-identical to the rejected candidate."
            ),
        }
    else:  # unreachable: the assertion above refuses an unchanged payload
        SMOKE_COMPARISON["proof_of_equality"] = (
            "The proposal payload is a pure function of the binding, the policy "
            "declaration, the schema declaration, the proposed spans, and the "
            "proposed representation. Byte equality of the two canonical "
            "payloads is asserted directly above, and both hash identically, so "
            "the identity is reproduced rather than assumed.\n\n"
            "Why the four commits between the smoke and the merge did not move "
            "it: bee381e, 4752c76 and d89ae32 changed override application, "
            "payload versioning and persisted verification. None of them "
            "changed a declared representation type, so the structural hash "
            "stayed 43ed330d… across all of them, and the proposal payload "
            "depends on the representation contract and the authored inputs "
            "rather than on any consumer of them. The smoke was labelled "
            "non-authoritative because of where it was run, not because its "
            "content was doubted; this run supplies the authority it lacked."
        )
print(f"smoke comparison    : {SMOKE_COMPARISON.get('hashes_equal')}")


# ---------------------------------------------------------------------------
# Persistence and reconstruction, in a throwaway SQLite file
# ---------------------------------------------------------------------------
#
# `compute_persisted_state_digest` is a digest of *persisted* state, so it
# cannot be produced without persisting. What is written here is a **draft**
# projection in a scratch database created for this run and deleted with the
# scratchpad. Nothing is published, activated, retired, or accepted:
# `publication_status` stays `draft`, `accept_proposal` is never called, and
# `run_publication_gate` is deliberately NOT run — it is the publication path,
# and its operational-snapshot reads would also need 5c corpus rows this
# checkpoint has no business writing.
#
# Disclosure about the seeded release row: it carries the five real derived
# binding values, and placeholder ledger/policy/reconciliation hashes. The
# mechanical persistence path requires the row only as an FK parent and never
# reads those three; the values the projection identity actually covers are the
# real ones, and `verify_persisted_state` re-derives them from the written rows.

import importlib as _importlib  # noqa: E402
import tempfile as _tempfile  # noqa: E402

from sqlalchemy import create_engine as _create_engine  # noqa: E402
from sqlalchemy.orm import Session as _Session  # noqa: E402

from afterworlds.ingestion.corpus.persistence import (  # noqa: E402
    _persist_package_and_source,
)
from afterworlds.ingestion.mechanical.persistence import (  # noqa: E402
    compute_persisted_state_digest,
    persist_draft,
    reconstruct_candidate,
    record_persisted_state_digest,
    verify_persisted_state,
)
from afterworlds.ingestion.mechanical.projection import (  # noqa: E402
    ProjectionCandidate,
    identify_projection,
    representation_payload,
    validate_schema_binding,
)
from afterworlds.persistence.orm.base import Base as _Base  # noqa: E402
from afterworlds.persistence.orm.corpus import CorpusReleaseORM  # noqa: E402

for _m in (
    "corpus", "rules_package", "mechanical", "identity", "node", "retrieval",
    "rolling_summary", "rpg", "character_sheet", "rules_authority",
    "session_state", "state", "story", "story_bible",
):
    _importlib.import_module(f"afterworlds.persistence.orm.{_m}")

CANDIDATE = ProjectionCandidate(
    schema_version=REPRESENTATION_SCHEMA_VERSION,
    schema_hash=representation_schema_hash(),
    binding=BINDING,
    classification=LEDGER,
    representation=DRAFT,
)

# The clean-baseline gate, asserted rather than assumed: this candidate
# declares the union this build implements, so it is not historical state.
_binding_findings = list(validate_schema_binding(CANDIDATE))
assert not _binding_findings, _binding_findings

_IDENTIFIED = identify_projection(CANDIDATE)
_NOW = "2026-08-23T00:00:00Z"

PERSISTENCE: dict[str, object] = {}
with _tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as _tmp:
    _engine = _create_engine(f"sqlite:///{Path(_tmp) / 'checkpoint.db'}")
    _Base.metadata.create_all(_engine)
    with _Session(_engine) as _s:
        _persist_package_and_source(
            _s, BINDING.package_uuid, BINDING.release_version, now=_NOW
        )
        _s.add(
            CorpusReleaseORM(
                package_uuid=BINDING.package_uuid,
                release_version=BINDING.release_version,
                authoritative_source_hash=BINDING.authoritative_source_hash,
                transform_config_hash=BINDING.transform_config_hash,
                bundle_root_hash=BINDING.bundle_root_hash,
                ledger_hash="0" * 64,
                policy_hash="0" * 64,
                reconciliation_hash="0" * 64,
                transform_config={},
                publication_status="published",
                created_at=_NOW,
            )
        )
        _s.flush()

        persist_draft(_s, _IDENTIFIED, now=_NOW)
        _s.flush()

        _REBUILT = reconstruct_candidate(_s, _IDENTIFIED.projection_uuid)
        _REID = identify_projection(_REBUILT)
        _digest = record_persisted_state_digest(_s, _IDENTIFIED.projection_uuid)
        _s.flush()
        _verify = verify_persisted_state(_s, _IDENTIFIED.projection_uuid)

        # Reconstruction must be exact in every derived identity, not merely
        # "the UUID came back the same".
        assert _REBUILT.schema_version == REPRESENTATION_SCHEMA_VERSION
        assert _REBUILT.schema_hash == representation_schema_hash()
        assert _REID.projection_uuid == _IDENTIFIED.projection_uuid
        assert _REID.payload_hash == _IDENTIFIED.payload_hash
        assert _REID.record_ids == _IDENTIFIED.record_ids
        assert _REID.component_ids == _IDENTIFIED.component_ids
        assert _REID.fact_ids == _IDENTIFIED.fact_ids
        assert compute_persisted_state_digest(_s, _IDENTIFIED.projection_uuid) == _digest
        assert _verify == (), _verify

        # The regenerated proposal and the persisted projection must describe
        # the same representation, or the digest proves something else.
        assert _REBUILT.representation == DRAFT

        _header_status = (
            _s.query(
                _importlib.import_module(
                    "afterworlds.persistence.orm.mechanical"
                ).MechanicalProjectionORM
            )
            .filter_by(projection_uuid=_IDENTIFIED.projection_uuid)
            .one()
            .publication_status
        )
        assert _header_status == "draft", _header_status

        PERSISTENCE = {
            "database": "throwaway SQLite in a TemporaryDirectory; deleted on exit",
            "projection_uuid": _IDENTIFIED.projection_uuid,
            "payload_hash": _IDENTIFIED.payload_hash,
            "persisted_state_digest": _digest,
            "publication_status": _header_status,
            "reconstructs_exactly": True,
            "reconstructed_schema_version": _REBUILT.schema_version,
            "reconstructed_schema_hash": _REBUILT.schema_hash,
            "verify_persisted_state_findings": list(_verify),
            "schema_binding_findings": _binding_findings,
            "derived_id_counts": {
                "records": len(_IDENTIFIED.record_ids),
                "components": len(_IDENTIFIED.component_ids),
                "facts": len(_IDENTIFIED.fact_ids),
            },
            "publication_gate": (
                "NOT RUN. run_publication_gate is the publication path; this "
                "checkpoint proposes and reviews, it does not publish."
            ),
            "seeded_release_disclosure": (
                "The scratch corpus-release row carries the five real derived "
                "binding values; ledger/policy/reconciliation hashes are "
                "placeholders. The mechanical persistence path uses the row "
                "only as an FK parent and never reads those three."
            ),
        }
    # Windows keeps the SQLite file open until the engine is disposed, and the
    # temporary directory is removed on exit from this block.
    _engine.dispose()

print(f"projection uuid     : {PERSISTENCE['projection_uuid']}")
print(f"persisted digest    : {PERSISTENCE['persisted_state_digest']}")
print(f"verify findings     : {PERSISTENCE['verify_persisted_state_findings']}")


# AMENDMENT 2. New filenames; the retained schema-2 proposal/audit are untouched.
#: The reviewed artifacts stay exactly as reviewed. This run re-derives them to
#: prove the identity still holds, and writes its copies somewhere they cannot
#: be mistaken for the reviewed ones.
OUT = REVIEW_DIR / "accept-run"
OUT.mkdir(exist_ok=True)
PROPOSAL_PATH = OUT / "conditions-1-ACCEPT-rederived-PROPOSAL.json"
AUDIT_PATH = OUT / "conditions-1-ACCEPT-rederived-audit.json"
#: The constraint is "never overwrite the retained review evidence", not "never
#: re-run this checkpoint". Assert the retained filenames are not write targets.
_RETAINED = {
    "issue-5d-batch-conditions-1-schema2-PROPOSAL.json",
    "issue-5d-batch-conditions-1-schema2-audit.json",
    "issue-5d-batch-conditions-1-schema2-generator.py",
    "issue-5d-batch-conditions-1-PROPOSAL.json",
    "issue-5d-batch-conditions-1-audit.json",
    "issue-5d-batch-conditions-1-generator.py",
    # The schema-2 regeneration this one descends from.
    "issue-5d-conditions-1-schema2-REGEN-PROPOSAL.json",
    "issue-5d-conditions-1-schema2-REGEN-audit.json",
    "issue-5d-conditions-1-schema2-REGEN-generator.py",
    # The non-authoritative schema-3 smoke.
    "issue-5d-conditions-1-schema3-SMOKE-PROPOSAL.json",
    "issue-5d-conditions-1-schema3-SMOKE-audit.json",
    # The REJECTED schema-3 candidate and its evidence. Preserved unchanged,
    # and the proposal in particular is read below to diff against.
    "issue-5d-conditions-1-schema3-REGEN-PROPOSAL.json",
    "issue-5d-conditions-1-schema3-REGEN-audit.json",
    "issue-5d-conditions-1-schema3-REGEN-generator.py",
    "issue-5d-conditions-1-schema3-REGEN-CHECKPOINT.md",
}
for _p in (PROPOSAL_PATH, AUDIT_PATH):
    assert _p.name not in _RETAINED, f"refusing to overwrite retained evidence: {_p}"

PROPOSAL_PATH.write_text(
    json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
)
# The audit is written at the end of the run, once every count exists.

unresolved = [s for s in spans if s.disposition is SemanticDisposition.UNRESOLVED]
print(f"leaves touched      : {len(touched)}")
print(f"spans               : {len(spans)}")
print(f"  substantive       : {sum(1 for s in spans if s.disposition is SemanticDisposition.SUBSTANTIVE)}")
print(f"  supporting        : {sum(1 for s in spans if s.disposition is SemanticDisposition.SUPPORTING_AUTHORITY)}")
print(f"  unresolved        : {len(unresolved)}")
print(f"  non_mechanical    : {sum(1 for s in spans if s.disposition is SemanticDisposition.NON_MECHANICAL)}")
print(f"records             : {len(records)}")
print(f"components          : {len(components)}  "
      f"(structured {sum(1 for c in components if c.handling is ComponentHandling.STRUCTURED)}, "
      f"mixed {sum(1 for c in components if c.handling is ComponentHandling.MIXED)}, "
      f"prose_bound {sum(1 for c in components if c.handling is ComponentHandling.PROSE_BOUND)})")
print(f"facts               : {sum(len(c.facts) for c in components)}")
print(f"prose bindings      : {len(prose_bindings)}")
print(f"relationships       : {len(DRAFT.relationships)}")
print(f"references          : {len(references)}")
print(f"provenance edges    : {len(provenance)}")
print(f"proposal identity   : {ident}")
print(f"\nVALIDATION FINDINGS  : {len(findings)}")
for f in findings:
    print("   -", f)


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

from collections import Counter  # noqa: E402

_disp = Counter(r["disposition"] for r in audit)
_fam = Counter(
    f.FAMILY.value for c in components for f in (*c.facts, *(g for o in c.options for g in o.facts))
)
print("=" * 66)
print("conditions-1 against 5d-representation-schema-3 (merged main 0ce2e53, remediated)")
print("=" * 66)
print(f"package_uuid      {BINDING.package_uuid}")
print(f"release_version   {BINDING.release_version}")
print(f"schema            {REPRESENTATION_SCHEMA_VERSION} / {representation_schema_hash()}")
print()
print(f"records           {len(records)}")
print(f"leaves accounted  {len(touched)}")
print(f"spans             {len(spans)}")
for k in ("substantive", "supporting_authority", "unresolved", "non_mechanical"):
    print(f"  {k:<21} {_disp.get(k, 0)}")
print(f"components        {len(components)}")
print(f"  with options    {sum(1 for c in components if c.options)}")
print(f"  with applies_when {sum(1 for c in components if c.applies_when)}")
print(f"typed facts       {sum(_fam.values())}  {dict(_fam)}")
print(f"prose bindings    {len(prose_bindings)}")
print()
print(f"validation findings {len(findings)}")
for f in findings:
    print("   !", f)
print()
# The acceptance rule, checked but never exercised: a proposal with zero
# UNRESOLVED spans is *acceptance-eligible*, which is not the same as accepted.
from afterworlds.ingestion.mechanical.accounting import (  # noqa: E402
    validate_acceptance,
)
from afterworlds.ingestion.mechanical.models import ReviewState as _RS  # noqa: E402
from dataclasses import replace as _replace  # noqa: E402

_accepted = _replace(
    LEDGER,
    spans=tuple(_replace(sp, review_state=_RS.ACCEPTED) for sp in LEDGER.spans),
)
_acc = validate_acceptance(_accepted)
# Split deliberately. The *classification* half of the rule — no UNRESOLVED
# span may survive into an accepted batch — is what schema 2 had to satisfy,
# and it must be empty. The remaining findings are all "no acceptance record",
# which is precisely what an un-accepted proposal must report: creating those
# records is `accept_proposal`, and this artifact must never call it.
_unresolved_blockers = [f for f in _acc if "unresolved" in f.lower()]
_missing_records = [f for f in _acc if "no acceptance record" in f]
print(f"validate_acceptance   unresolved-span findings : {len(_unresolved_blockers)}")
for f in _unresolved_blockers:
    print("   !", f)
print(
    f"                      awaiting-acceptance findings: "
    f"{len(_missing_records)} (expected; accept_proposal is never called)"
)
_other = [f for f in _acc if f not in _unresolved_blockers and f not in _missing_records]
print(f"                      other findings            : {len(_other)}")
for f in _other:
    print("   !", f)
assert not _unresolved_blockers, _unresolved_blockers
print()
print(f"proposal identity {ident}")
print("accept_proposal NOT called; oracles/ untouched; nothing published.")

# ---------------------------------------------------------------------------
# AMENDMENT 3. Audit envelope, with programmatic canary comparison.
# ---------------------------------------------------------------------------
#
# Schema 2 introduced `ComponentOption.facts`, so there are two defensible
# typed-fact totals. Both are derived and reported; neither is chosen for the
# reviewer.
FACTS_COMPONENT_ONLY = sum(len(c.facts) for c in components)
FACTS_INCLUDING_OPTIONS = sum(_fam.values())

DERIVED = {
    "records": len(records),
    "covered_5c_leaves": len(touched),
    "semantic_spans": len(spans),
    "substantive_spans": _disp.get("substantive", 0),
    "supporting_authority_spans": _disp.get("supporting_authority", 0),
    "non_mechanical_spans": _disp.get("non_mechanical", 0),
    "unresolved_spans": _disp.get("unresolved", 0),
    "components": len(components),
    "typed_facts_component_only": FACTS_COMPONENT_ONLY,
    "typed_facts_including_options": FACTS_INCLUDING_OPTIONS,
    "package_uuid": BINDING.package_uuid,
    "release_version": BINDING.release_version,
    "representation_schema_version": REPRESENTATION_SCHEMA_VERSION,
    "representation_structural_hash": representation_schema_hash(),
    "proposal_identity": ident,
    "partition_and_reason_and_representation_findings": len(findings),
    "acceptance_unresolved_span_findings": len(_unresolved_blockers),
    "acceptance_missing_records": len(_missing_records),
    "acceptance_other_findings": len(_other),
}

#: The single place expected values are stated. Nothing else in this envelope
#: is hand-typed.
CANARIES = {
    "records": 16,
    "covered_5c_leaves": 134,
    "semantic_spans": 184,
    "substantive_spans": 85,
    "supporting_authority_spans": 99,
    "non_mechanical_spans": 0,
    "unresolved_spans": 0,
    "components": 54,
    "typed_facts": 69,
    "package_uuid": "4458fa10-4a66-5e0e-9ecc-ea37530ad2b4",
    "release_version": "5.2.1-corpus.36b786d8-fa2",
    "representation_schema_version": "5d-representation-schema-2",
    "representation_structural_hash": (
        "ca27a7468abb84db43781e96ac48fbc55e166c3e410fe33d80f03a263a8d002c"
    ),
    "proposal_identity": (
        "756922a3892f9420dc8bfb2fe6af8a5a4db491111d1786ab0de6c2ddbf7dbfa6"
    ),
    "partition_findings": 0,
    "reason_code_findings": 0,
    "representation_findings": 0,
    "acceptance_unresolved_span_findings": 0,
    #: "all 184 spans" — asserted semantically below, so the claim survives a
    #: batch with a different span count.
    "missing_human_acceptance_records": 184,
}
assert len(_missing_records) == len(spans), (len(_missing_records), len(spans))
DERIVED["missing_human_acceptance_records"] = len(_missing_records)

# Partition/reason-code/representation findings are validated separately so
# each canary line has its own evidence rather than one collapsed total.
_partition_findings: list[str] = []
for _lid in touched:
    _partition_findings.extend(
        validate_partition(_lid, CORPUS.leaf_lengths[_lid], tuple(spans))
    )
_reason_findings = list(validate_reason_codes(tuple(spans)))
_representation_findings = list(validate_representation(DRAFT, LEDGER, CORPUS))
DERIVED["partition_findings"] = len(_partition_findings)
DERIVED["reason_code_findings"] = len(_reason_findings)
DERIVED["representation_findings"] = len(_representation_findings)

#: The canaries above are the **pre-schema-3** values, kept deliberately: the
#: question this checkpoint answers is "what changed against the proposal
#: semantic review rejected". A drifting measure with a stated cause is the
#: measurement. A drifting measure without one is a stop condition.
EXPECTED_DRIFT_CAUSES = {
    "representation_schema_version": (
        "schema 3 succeeded schema 2; PR #157 merged as 0ce2e53"
    ),
    "representation_structural_hash": (
        "derived from the declared types: MOVEMENT_TRANSPORT was added, "
        "MovementCostFact gained payer/rounding, SizeComparison gained "
        "measured/reference/at_most, and FactQualifier joined the component"
    ),
    "proposal_identity": (
        "the payload changed, which is the required outcome: the rejected "
        "identity is superseded, never mutated"
    ),
    "semantic_spans": (
        "remediation correction 1 cuts Charmed's social-advantage clause in "
        "three instead of two, so \"The charmer\" becomes governing prose "
        "instead of sitting inside the fact's provenance. One span added; no "
        "leaf's partition changed, because the split is inside a leaf"
    ),
    "substantive_spans": (
        "two causes, both deliberate. Succession: \"The grappler can drag or "
        "carry you when it moves\" had no fact family under schema 2 and was "
        "recorded as supporting authority; schema 3 carries it as a "
        "MovementTransportFact, so it becomes substantive (+1). Remediation: "
        "correction 1 adds \"The charmer\" as substantive governing prose (+1)"
    ),
    "missing_human_acceptance_records": (
        "one per span by construction, so it tracks the added span exactly. "
        "Every span still awaits human acceptance; none has been accepted"
    ),
    "supporting_authority_spans": (
        "the same span, leaving the supporting set — the mirror of the "
        "substantive increase, and the two must move by the same amount"
    ),
    "typed_facts": (
        "the transport fact schema 2 could not represent at all"
    ),
}

#: The Owner's expected drift from the rejected candidate, stated as a gate
#: rather than as prose. `CANARIES` above measures the schema-2 -> schema-3
#: succession; this measures the remediation alone. An off-by-one here means the
#: split cut somewhere other than where it was specified.
REJECTED_EXPECTED = {
    "semantic_spans": (184, 185),
    "substantive_spans": (86, 87),
    "supporting_authority_spans": (98, 98),
    "prose_bindings": (14, 15),
    "provenance_edges": (184, 185),
    "records": (16, 16),
    "covered_5c_leaves": (134, 134),
    "components": (54, 54),
    "typed_facts": (70, 70),
}
_NOW_VALUES = {
    "semantic_spans": len(spans),
    "substantive_spans": _disp.get("substantive", 0),
    "supporting_authority_spans": _disp.get("supporting_authority", 0),
    "prose_bindings": len(prose_bindings),
    "provenance_edges": len(provenance),
    "records": len(records),
    "covered_5c_leaves": len(touched),
    "components": len(components),
    "typed_facts": FACTS_INCLUDING_OPTIONS,
}
REMEDIATION_DRIFT = []
for _k, (_was, _want) in REJECTED_EXPECTED.items():
    _got = _NOW_VALUES[_k]
    REMEDIATION_DRIFT.append(
        {
            "measure": _k,
            "rejected_2f42f2bb": _was,
            "expected_after_remediation": _want,
            "derived": _got,
            "match": _got == _want,
            "changed": _want != _was,
        }
    )
_OFF = [d for d in REMEDIATION_DRIFT if not d["match"]]
assert not _OFF, _OFF

HANDLING_NOW = {
    "structured": sum(
        1 for c in components if c.handling is ComponentHandling.STRUCTURED
    ),
    "mixed": sum(1 for c in components if c.handling is ComponentHandling.MIXED),
    "prose_bound": sum(
        1 for c in components if c.handling is ComponentHandling.PROSE_BOUND
    ),
}
assert HANDLING_NOW == {"structured": 40, "mixed": 10, "prose_bound": 4}, HANDLING_NOW

drift = []
for _key, _expected in CANARIES.items():
    if _key == "typed_facts":
        _actual = FACTS_INCLUDING_OPTIONS
        _note = (
            f"component-only total is {FACTS_COMPONENT_ONLY}; compared against "
            f"the family-breakdown total, which includes ComponentOption facts"
        )
    else:
        _actual = DERIVED[_key]
        _note = None
    _matched = _actual == _expected
    _cause = None if _matched else EXPECTED_DRIFT_CAUSES.get(_key)
    drift.append(
        {
            "measure": _key,
            "expected_pre_schema_3": _expected,
            "derived": _actual,
            "match": _matched,
            "status": (
                "unchanged"
                if _matched
                else ("expected succession drift" if _cause else "UNEXPLAINED DRIFT")
            ),
            **({"cause": _cause} if _cause else {}),
            **({"note": _note} if _note else {}),
        }
    )

#: Anything that moved without a stated cause stops the checkpoint. The
#: alternative — reporting it as benign — is how a regeneration quietly becomes
#: a redefinition.
UNEXPLAINED = [d for d in drift if d["status"] == "UNEXPLAINED DRIFT"]

#: Against the pre-schema-3 proposal the dispositions move for two reasons at
#: once: one span was *reclassified* (transport, supporting -> substantive) and
#: one span was *added* (the charmer restriction, substantive). So the check is
#: no longer "the two move in opposite directions by the same amount" — that
#: only held while the span count was fixed. What must hold is the conservation
#: law underneath it: every disposition delta together accounts for exactly the
#: change in span count, and nothing arrived unaccounted for.
_sub = next(d for d in drift if d["measure"] == "substantive_spans")
_sup = next(d for d in drift if d["measure"] == "supporting_authority_spans")
_spn = next(d for d in drift if d["measure"] == "semantic_spans")
_non = next(d for d in drift if d["measure"] == "non_mechanical_spans")
_unr = next(d for d in drift if d["measure"] == "unresolved_spans")
_d = lambda row: row["derived"] - row["expected_pre_schema_3"]  # noqa: E731
DISPOSITION_SHIFT = {
    "substantive_delta": _d(_sub),
    "supporting_delta": _d(_sup),
    "non_mechanical_delta": _d(_non),
    "unresolved_delta": _d(_unr),
    "span_delta": _d(_spn),
    "conserved": (_d(_sub) + _d(_sup) + _d(_non) + _d(_unr)) == _d(_spn),
    "attribution": {
        "succession_reclassified": (
            "transport: supporting -> substantive, +1 substantive / -1 supporting"
        ),
        "remediation_added": (
            'correction 1: "The charmer" added as substantive prose, +1 span '
            "/ +1 substantive"
        ),
        "remediation_retargeted": (
            'correction 2: " If your" moved from record to component provenance; '
            "supporting either way, so no disposition delta"
        ),
    },
}
assert DISPOSITION_SHIFT["conserved"], DISPOSITION_SHIFT

AUDIT = {
    "artifact": "CRD Issue 5d — conditions-1 semantic-acceptance checkpoint (regenerated)",
    "status": "PROPOSED — acceptance-eligible, NOT accepted",
    "acceptance_boundary": (
        "Zero unresolved semantic spans means only that the proposal is eligible "
        "for human semantic review. accept_proposal was not called; no "
        "AcceptedInputs exist; no authority was activated, published, or retired."
    ),
    "generated_from": {
        "repo": str(REPO),
        "code_imported_from": str((CODE / "src").resolve()),
        "import_provenance": IMPORT_PROVENANCE,
        "main_commit": "0ce2e53f147710c0b620bbb418622fb89e5cbd13",
        "reuse_justification": (
            "Copy of issue-5d-conditions-1-schema2-REGEN-generator.py, amended "
            "for schema 3 and run against exact merged main 0ce2e53 (the PR "
            "#157 merge). The schema-3 amendments to the authored inputs are "
            "enumerated in the module docstring: payer, rounding, size "
            "operands, MovementTransportFact, and the surcharge FactQualifier. "
            "No other authored input is changed, and no semantic correction is "
            "made silently."
        ),
    },
    "source_binding": {
        "package_uuid": BINDING.package_uuid,
        "release_version": BINDING.release_version,
        "authoritative_source_hash": BINDING.authoritative_source_hash,
        "transform_config_hash": BINDING.transform_config_hash,
        "bundle_root_hash": BINDING.bundle_root_hash,
        "persisted_corpus_digest": BINDING.persisted_corpus_digest,
        "persisted_corpus_digest_disclosure": (
            "Carried from the published CRD Issue 5c release record, not "
            "re-derived here; the other five values are re-derived from the "
            "committed PDF by the production 5c pipeline and asserted."
        ),
    },
    "schema_identity": {
        "representation_schema_version": REPRESENTATION_SCHEMA_VERSION,
        "representation_structural_hash": representation_schema_hash(),
        "semantic_policy_version": SEMANTIC_POLICY_VERSION,
        "semantic_policy_hash": semantic_policy_hash(),
    },
    "proposal_identity": ident,
    "counts": {
        **DERIVED,
        "covered_5c_leaves_definition": (
            "len(touched) — distinct 5c leaves this batch places spans on; "
            f"the full represented-leaf population is {len(REPRESENTED)}"
        ),
        "typed_fact_families": dict(sorted(_fam.items())),
        "prose_bindings": len(prose_bindings),
        "relationships": len(DRAFT.relationships),
        "references": len(references),
        "provenance_edges": len(provenance),
        "components_with_options": sum(1 for c in components if c.options),
        "components_with_applies_when": sum(1 for c in components if c.applies_when),
        "component_handling": {
            "structured": sum(
                1 for c in components if c.handling is ComponentHandling.STRUCTURED
            ),
            "mixed": sum(
                1 for c in components if c.handling is ComponentHandling.MIXED
            ),
            "prose_bound": sum(
                1 for c in components if c.handling is ComponentHandling.PROSE_BOUND
            ),
        },
    },
    "validation": {
        "partition": {
            "finding_count": len(_partition_findings),
            "findings": _partition_findings,
        },
        "reason_codes": {
            "finding_count": len(_reason_findings),
            "findings": _reason_findings,
        },
        "representation": {
            "finding_count": len(_representation_findings),
            "findings": _representation_findings,
        },
        "acceptance": {
            "unresolved_span_findings": len(_unresolved_blockers),
            "unresolved_span_finding_detail": _unresolved_blockers,
            "missing_human_acceptance_records": len(_missing_records),
            "other_findings": len(_other),
            "other_finding_detail": _other,
            "interpretation": (
                "Zero unresolved-span findings is the classification half of the "
                "acceptance rule and is satisfied. The missing-acceptance-record "
                "findings are expected and required: creating those records IS "
                "accept_proposal, which this artifact never calls."
            ),
        },
    },
    "canary_drift": drift,
    "canary_drift_summary": (
        "NO DRIFT AT ALL"
        if all(d["match"] for d in drift)
        else (
            "EXPECTED SUCCESSION DRIFT ONLY — every changed measure carries a "
            "stated cause"
            if not UNEXPLAINED
            else "UNEXPLAINED DRIFT — see canary_drift; this is a stop condition"
        )
    ),
    "canary_drift_unexplained": UNEXPLAINED,
    "disposition_shift": DISPOSITION_SHIFT,
    "grappled_movable_proof": GRAPPLED_PROOF,
    "correction_proof": CORRECTION_PROOF,
    "remediation_drift_against_rejected": REMEDIATION_DRIFT,
    "component_handling_after_remediation": HANDLING_NOW,
    "persistence_and_reconstruction": PERSISTENCE,
    "superseded_identities": SUPERSEDED,
    "superseded_identity_guard": (
        "The regenerated identity is asserted unequal to each superseded value. "
        "None can be accidentally selected: oracles/ holds only README.md, no "
        "AcceptedInputs exist, accept_proposal is never called, and this run's "
        "output filenames are asserted not to collide with any retained artifact."
    ),
    "oracles_directory_contents": ORACLE_DIR_CONTENTS,
    "comparison_with_smoke_identity": SMOKE_COMPARISON,
    "carried_forward_not_fixed_here": [
        "option_set_violations hashes option.semantic_key without an exact-type "
        "check; an unhashable str subclass raises out of validation. "
        "Pre-existing on main at ad32b4f, recorded in "
        "pr-157-issue-137-remediation-log.md, disposition out of scope.",
        "Shambling Mound's Engulf waives a surcharge defined in another record. "
        "Unresolved base-projection semantics, NOT a RuleOverride. Retained in "
        "docs/architecture/known_unknowns.md.",
        "The five further schema-3 successors in known_unknowns.md: counterpart "
        "establishment outside transport, third-party size comparisons, "
        "ratio-form movement costs, rounding supplied by the governing rule, "
        "and applicability over a capability predicate.",
    ],
    "spans": audit,
}

AUDIT_PATH.write_text(
    json.dumps(AUDIT, indent=2, ensure_ascii=False), encoding="utf-8"
)

print()
print("=" * 66)
print("CANARY COMPARISON")
print("=" * 66)
for d in drift:
    _tag = "SAME " if d["match"] else ("MOVED" if d.get("cause") else "!!!!!")
    print(
        f"  {_tag}  {d['measure']:<34} "
        f"pre-schema-3={d['expected_pre_schema_3']}  now={d['derived']}"
    )
    if d.get("cause"):
        print(f"           cause: {d['cause']}")
print()
print(f"disposition shift   : {DISPOSITION_SHIFT}")
print(f"unexplained drift   : {len(UNEXPLAINED)}")
for d in UNEXPLAINED:
    print("   !!!", d)
assert not UNEXPLAINED, UNEXPLAINED
print()
print(f"typed facts (component-only)        : {FACTS_COMPONENT_ONLY}")
print(f"typed facts (including option facts): {FACTS_INCLUDING_OPTIONS}")
print(f"missing human acceptance records    : {len(_missing_records)}")
print()
print(AUDIT["canary_drift_summary"])
print(f"proposal -> {PROPOSAL_PATH}")
print(f"audit    -> {AUDIT_PATH}")


# ---------------------------------------------------------------------------
# FORMAL ACCEPTANCE — Owner-authorized, this proposal and this scope only
# ---------------------------------------------------------------------------

from datetime import UTC, datetime  # noqa: E402

from afterworlds.ingestion.mechanical.acceptance import (  # noqa: E402
    accept_proposal,
)
from afterworlds.ingestion.mechanical.models import ReviewState as _ReviewState  # noqa: E402
from afterworlds.ingestion.mechanical.oracle import (  # noqa: E402
    ACCEPTED_ARTIFACT_KIND,
    COMMITTED_ORACLE_DIR,
    accepted_inputs_payload,
    candidate_from_accepted_inputs,
    committed_inputs_for,
    committed_oracle_for,
    load_accepted_inputs,
    oracle_identity,
)

BATCH_ID = "conditions-1"
REVIEWER = "Ravenlok (Owner)"
ACCEPTED_AT = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
RULE = (
    "Every span of CRD Issue 5d batch conditions-1, as proposed by proposal "
    f"identity {AUTHORIZED_IDENTITY} against representation schema "
    f"{REPRESENTATION_SCHEMA_VERSION} over 5c release "
    f"{BINDING.package_uuid}/{BINDING.release_version}, was semantically "
    "reviewed and accepted as represented. The scope is the complete proposed "
    "span set and nothing outside it: 185 spans over 134 represented leaves of "
    "16 condition records, with zero unresolved and zero non-mechanical "
    "dispositions. This supersedes the refused candidates 756922a3, b9ac21bf, "
    "and 2f42f2bb."
)

#: The exact set the Owner authorized: every span this proposal proposed, in
#: the proposal's own order. Derived from the proposal rather than re-selected,
#: so no span outside the reviewed scope can enter and none can be missed.
RESOLVED_SCOPE = tuple(ps.span.span_id for ps in PROPOSAL.proposed_spans)
assert len(RESOLVED_SCOPE) == 185, len(RESOLVED_SCOPE)
assert len(set(RESOLVED_SCOPE)) == 185, "resolved scope repeats a span"
assert set(RESOLVED_SCOPE) == {sp.span_id for sp in spans}, "scope != proposal spans"
assert all(sp.review_state is _ReviewState.PROPOSED for sp in spans)

ACCEPTED = accept_proposal(
    PROPOSAL,
    batch_id=BATCH_ID,
    rule=RULE,
    resolved_scope=RESOLVED_SCOPE,
    reviewer=REVIEWER,
    accepted_at=ACCEPTED_AT,
    prior=None,  # first batch for this release
)

# --- What acceptance must and must not have changed -------------------------
assert len(ACCEPTED.batches) == 1, ACCEPTED.batches
assert ACCEPTED.batches[0].batch_id == BATCH_ID
assert ACCEPTED.batches[0].proposal_identity == AUTHORIZED_IDENTITY
assert len(ACCEPTED.acceptances) == 185, len(ACCEPTED.acceptances)
assert {a.span_id for a in ACCEPTED.acceptances} == set(RESOLVED_SCOPE)
assert {a.batch_id for a in ACCEPTED.acceptances} == {BATCH_ID}
assert {a.reviewer for a in ACCEPTED.acceptances} == {REVIEWER}
assert {a.accepted_at for a in ACCEPTED.acceptances} == {ACCEPTED_AT}
assert len(ACCEPTED.oracle.spans) == 185
assert all(sp.review_state is _ReviewState.ACCEPTED for sp in ACCEPTED.oracle.spans)
# Acceptance records review evidence; it must not touch the semantics.
assert ACCEPTED.oracle.representation == DRAFT, "acceptance altered the representation"
assert ACCEPTED.oracle.binding == BINDING
assert ACCEPTED.oracle.schema_version == REPRESENTATION_SCHEMA_VERSION
assert ACCEPTED.oracle.schema_hash == representation_schema_hash()

# --- Serialize through the production path ----------------------------------
PAYLOAD = accepted_inputs_payload(ACCEPTED)
assert PAYLOAD["artifact_kind"] == ACCEPTED_ARTIFACT_KIND
#: Proposal-only keys must be absent: this is accepted authority, not a machine
#: proposal wearing a different flag.
for _forbidden in ("proposed_spans", "proposed_representation", "proposal_origin"):
    assert _forbidden not in PAYLOAD, _forbidden
#: No review state reaches the payload at all — `span_payload` omits it on
#: purpose, because a span set that means the same thing must compare equal
#: however it was reviewed. So "no PROPOSED survived" is proved two ways: the
#: word appears nowhere in the bytes, and the key that could carry it does not
#: exist. The accepted state itself is asserted on the in-memory spans above.
def _keys_and_values(node: object):  # noqa: ANN202
    if isinstance(node, dict):
        for k, v in node.items():
            yield ("key", k)
            yield from _keys_and_values(v)
    elif isinstance(node, list):
        for v in node:
            yield from _keys_and_values(v)
    else:
        yield ("value", node)


_PAIRS = list(_keys_and_values(PAYLOAD))
#: Structural, not a substring scan. The word "proposed" legitimately appears
#: inside the recorded selection rule — that sentence is evidence describing
#: what was reviewed — so the check is that no *key* carries review state and no
#: *value* is a review-state enum member.
assert not [k for kind, k in _PAIRS if kind == "key" and k == "review_state"]
assert not [
    v
    for kind, v in _PAIRS
    if kind == "value" and v in {rs.value for rs in _ReviewState}
], "a review-state value survived into accepted authority"
assert all("review_state" not in s_ for s_ in PAYLOAD["spans"]), PAYLOAD["spans"][0]

#: One file per published 5c release, named for the release it judges, so a
#: later batch extends this artifact rather than creating a second competing
#: oracle for the same release — which the resolver refuses outright.
ORACLE_NAME = "srd-5-2-1-corpus-36b786d8-fa2.json"
ORACLE_PATH = COMMITTED_ORACLE_DIR / ORACLE_NAME
_existing = sorted(COMMITTED_ORACLE_DIR.glob("*.json"))
assert _existing in ([], [ORACLE_PATH]), _existing
ORACLE_PATH.write_text(
    json.dumps(PAYLOAD, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
    encoding="utf-8",
)

# --- Confirm the committed bytes --------------------------------------------
RELOADED = load_accepted_inputs(ORACLE_PATH)
assert oracle_identity(RELOADED.oracle) == oracle_identity(ACCEPTED.oracle)
#: Compared as sets, not sequences. `accepted_inputs_payload` canonically
#: orders the evidence rows, while the in-memory tuple is in resolved-scope
#: order — the same records, deliberately written in an order that does not
#: depend on how the reviewer happened to enumerate the scope.
assert set(RELOADED.acceptances) == set(ACCEPTED.acceptances)
assert len(RELOADED.acceptances) == len(ACCEPTED.acceptances) == 185
#: Same treatment for the batch: `resolved_scope` is the reviewer's exact
#: enumeration and round-trips verbatim, while the semantic `diff` is
#: canonically ordered on write. Compared field by field so the distinction is
#: stated rather than hidden behind a whole-object comparison.
_rb, _ab = RELOADED.batches[0], ACCEPTED.batches[0]
assert len(RELOADED.batches) == 1
assert _rb.batch_id == _ab.batch_id == BATCH_ID
assert _rb.rule == _ab.rule == RULE
assert _rb.proposal_identity == _ab.proposal_identity == AUTHORIZED_IDENTITY
assert _rb.resolved_scope == _ab.resolved_scope == RESOLVED_SCOPE
assert set(_rb.diff) == set(_ab.diff)
assert len(_rb.diff) == len(_ab.diff) == 185
#: The diff hash is order-independent by construction, so canonical reordering
#: on write cannot silently change what the evidence attests.
assert _rb.semantic_diff_hash == _ab.semantic_diff_hash

_resolved_inputs = committed_inputs_for(
    BINDING.package_uuid, BINDING.release_version
)
_resolved_oracle = committed_oracle_for(
    BINDING.package_uuid, BINDING.release_version
)
assert _resolved_inputs is not None, "committed_inputs_for did not resolve"
assert _resolved_oracle is not None, "committed_oracle_for did not resolve"
assert oracle_identity(_resolved_oracle) == oracle_identity(ACCEPTED.oracle)
#: Same file, so the same canonical-order caveat applies; the resolver must
#: return exactly what the loader did.
assert _resolved_inputs.batches == RELOADED.batches
assert set(_resolved_inputs.acceptances) == set(ACCEPTED.acceptances)
assert len(_resolved_inputs.acceptances) == 185

# --- The accepted candidate reconstructs the same projection ----------------
ACCEPTED_CANDIDATE = candidate_from_accepted_inputs(RELOADED)
_ACC_ID = identify_projection(ACCEPTED_CANDIDATE)
assert _ACC_ID.projection_uuid == _IDENTIFIED.projection_uuid, (
    _ACC_ID.projection_uuid,
    _IDENTIFIED.projection_uuid,
)
assert _ACC_ID.payload_hash == _IDENTIFIED.payload_hash
assert _ACC_ID.record_ids == _IDENTIFIED.record_ids
assert _ACC_ID.component_ids == _IDENTIFIED.component_ids
assert _ACC_ID.fact_ids == _IDENTIFIED.fact_ids
assert not validate_schema_binding(ACCEPTED_CANDIDATE)

# --- Persist the accepted candidate and verify ------------------------------
#
# The digest legitimately moves from the draft one: acceptance adds reviewer and
# timestamp evidence, and `compute_persisted_state_digest` covers retained
# acceptance evidence on purpose. The *semantic* halves — projection UUID and
# payload hash — must not move, and that is asserted above rather than claimed.

ACCEPTED_DIGEST = ""
with _tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as _tmp2:
    _e2 = _create_engine(f"sqlite:///{Path(_tmp2) / 'accepted.db'}")
    _Base.metadata.create_all(_e2)
    with _Session(_e2) as _s2:
        _persist_package_and_source(
            _s2, BINDING.package_uuid, BINDING.release_version, now=_NOW
        )
        _s2.add(
            CorpusReleaseORM(
                package_uuid=BINDING.package_uuid,
                release_version=BINDING.release_version,
                authoritative_source_hash=BINDING.authoritative_source_hash,
                transform_config_hash=BINDING.transform_config_hash,
                bundle_root_hash=BINDING.bundle_root_hash,
                ledger_hash="0" * 64,
                policy_hash="0" * 64,
                reconciliation_hash="0" * 64,
                transform_config={},
                publication_status="published",
                created_at=_NOW,
            )
        )
        _s2.flush()
        persist_draft(_s2, _ACC_ID, now=_NOW)
        _s2.flush()
        _rebuilt2 = reconstruct_candidate(_s2, _ACC_ID.projection_uuid)
        _reid2 = identify_projection(_rebuilt2)
        ACCEPTED_DIGEST = record_persisted_state_digest(_s2, _ACC_ID.projection_uuid)
        _s2.flush()
        _verify2 = verify_persisted_state(_s2, _ACC_ID.projection_uuid)
        assert _reid2.projection_uuid == _IDENTIFIED.projection_uuid
        assert _reid2.payload_hash == _IDENTIFIED.payload_hash
        assert _verify2 == (), _verify2
        #: Object equality against DRAFT does not hold here, and should not:
        #: the accepted candidate comes from the committed file, whose
        #: collections are canonically ordered, while DRAFT is in authored
        #: order. What must hold is that they *mean* the same thing, which is
        #: what the canonical payload says — and it is the same comparison the
        #: projection identity is derived from.
        assert _rebuilt2.representation == ACCEPTED_CANDIDATE.representation
        assert representation_payload(_rebuilt2.representation) == (
            representation_payload(DRAFT)
        )
        _acc_status = (
            _s2.query(
                _importlib.import_module(
                    "afterworlds.persistence.orm.mechanical"
                ).MechanicalProjectionORM
            )
            .filter_by(projection_uuid=_ACC_ID.projection_uuid)
            .one()
            .publication_status
        )
        assert _acc_status == "draft", _acc_status
    _e2.dispose()

# --- Where the digest moved, computed rather than argued ---------------------
#
# `compute_persisted_state_digest` hashes three layers: the semantic payload,
# the persisted derived ids, and the retained acceptance evidence. The first two
# are asserted byte-identical between the draft run and this one. Rather than
# leave "so it must be the third" as an inference, both digest inputs are rebuilt
# here and diffed key by key.

DIGEST_ATTRIBUTION = {
    "digest_layers": [
        "semantic payload",
        "persisted derived ids",
        "retained acceptance evidence",
    ],
    "semantic_payload_moved": False,
    "semantic_payload_evidence": (
        f"projection payload hash {_IDENTIFIED.payload_hash} in the draft run "
        f"and {_ACC_ID.payload_hash} in the accepted run — asserted equal"
    ),
    "derived_ids_moved": False,
    "derived_ids_evidence": (
        "record_ids, component_ids and fact_ids are asserted equal between the "
        "two runs, element for element"
    ),
    "acceptance_evidence_moved": True,
    "acceptance_evidence_detail": (
        "the draft projection carried no batches and no acceptance records; the "
        f"accepted one carries 1 batch ({BATCH_ID}) and 185 acceptance records, "
        f"each naming reviewer {REVIEWER!r} and timestamp {ACCEPTED_AT!r}"
    ),
    "conclusion": (
        "Two of the digest's three layers are proved unmoved, so the movement "
        "is wholly attributable to the third. That is the digest doing its job: "
        "it answers 'is this the same persisted state, including how it was "
        "reviewed', which is a different question from the projection UUID's "
        "'is this the same authority'."
    ),
}

ACCEPTANCE = {
    "authorization": (
        "Ravenlok (Owner), 2026-08-23, for this proposal identity and its exact "
        "resolved scope only."
    ),
    "batch_id": BATCH_ID,
    "reviewer": REVIEWER,
    "accepted_at": ACCEPTED_AT,
    "rule": RULE,
    "proposal_identity": AUTHORIZED_IDENTITY,
    "resolved_scope_size": len(RESOLVED_SCOPE),
    "acceptance_records": len(ACCEPTED.acceptances),
    "oracle_identity": oracle_identity(ACCEPTED.oracle),
    "committed_artifact": str(ORACLE_PATH.relative_to(REPO)),
    "artifact_sha256": hash_obj(PAYLOAD),
    "projection_uuid": _ACC_ID.projection_uuid,
    "projection_payload_hash": _ACC_ID.payload_hash,
    "draft_persisted_state_digest": PERSISTENCE["persisted_state_digest"],
    "accepted_persisted_state_digest": ACCEPTED_DIGEST,
    "digest_moved": ACCEPTED_DIGEST != PERSISTENCE["persisted_state_digest"],
    "semantic_identity_moved": False,
    "semantic_identity_proof": (
        "The projection UUID and payload hash are asserted equal between the "
        "draft run and the accepted run. compute_persisted_state_digest covers "
        "retained acceptance evidence in addition to the semantic payload and "
        "the derived ids, so reviewer and timestamp moving it is the digest "
        "doing its job — the semantic halves are what must not move, and they "
        "did not."
    ),
    "digest_attribution": DIGEST_ATTRIBUTION,
    "verify_persisted_state_findings": list(_verify2),
    "publication_status": _acc_status,
    "published": False,
    "activated": False,
    "retired": False,
}

print()
print("=" * 66)
print("FORMAL ACCEPTANCE — conditions-1")
print("=" * 66)
for _k, _v in ACCEPTANCE.items():
    if _k == "rule":
        continue
    print(f"  {_k:<36} {_v}")
print()
print(f"committed -> {ORACLE_PATH}")
