"""REGENERATION — conditions-1 against `5d-representation-schema-2`, from merged main.

Byte-identical copy of `issue-5d-batch-conditions-1-schema2-generator.py` except
for three disclosed amendments, made because that artifact's environment
assumption went stale when the schema-2 branch merged:

  1. `CODE` pointed at the now-removed worktree `D:\\AI\\Claude\\aw-5d-schema2`.
     Schema 2 merged as PR #155; `git diff --stat 97f924c 7395c52 -- src/` is
     empty, so main's `src/` is byte-identical to the merge the original ran
     against. `CODE = REPO` therefore reuses the same contract, and the run
     prints the resolved module files to prove which code was imported.
  2. Output filenames carry a `REGEN` infix so the retained schema-2 proposal
     and audit are preserved intact.
  3. The audit is emitted as a full envelope (binding, schema identity,
     proposal identity, derived counts, validation findings, canary drift)
     around the original per-span rows, which are retained unchanged.

No semantic content is amended. Every number in the envelope is computed from
the live objects; the canaries are compared programmatically, never hand-copied.

DISPOSABLE REVIEW MATERIAL. Emits a `MechanicalProposal` payload only. Never
writes to `oracles/`, never calls `accept_proposal`, never touches the database.
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(r"D:\AI\Claude\afterworlds")
#: AMENDMENT 1. The schema-2 worktree is gone; schema 2 is merged into main and
#: main's `src/` is byte-identical to the PR #155 merge. Import from the primary
#: checkout, and print the resolved files so the imported contract is evidence,
#: not an assumption.
CODE = REPO
sys.path.insert(0, str(CODE / "src"))
OUT = Path(__file__).parent

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
        SizeComparison(category=CreatureSize.TINY),
        SizeComparison(relation=SizeRelation.SMALLER, at_least=2),
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
            ("when it moves,", "C", "movable"),
            (
                "costs it 1 extra foot",
                "F",
                (
                    "movable",
                    MovementCostFact(
                        kind=MovementCostKind.PER_FOOT_SURCHARGE,
                        amount=MovementAmount.FEET,
                        feet=1,
                    ),
                ),
            ),
            # One negation over a homogeneous set of size tests.
            (None, "AC", ("movable", None, NOT_TINY_OR_TWO_SMALLER)),
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
            (None, "R", None),
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
audit: list[dict] = []

DISP = {
    "R": SemanticDisposition.SUPPORTING_AUTHORITY,
    "C": SemanticDisposition.SUPPORTING_AUTHORITY,
    "REF": SemanticDisposition.SUPPORTING_AUTHORITY,
    "U": SemanticDisposition.UNRESOLVED,
    "F": SemanticDisposition.SUBSTANTIVE,
    "P": SemanticDisposition.SUBSTANTIVE,
    "O": SemanticDisposition.SUBSTANTIVE,
    "AC": SemanticDisposition.SUBSTANTIVE,
    "FA": SemanticDisposition.SUBSTANTIVE,
}
RATIONALE = {
    "R": "identifies or frames the mechanic; preserved as supporting authority rather than discarded",
    "C": "sub-heading naming the effect it labels; preserved as supporting authority",
    "REF": "names one condition this glossary defines; source-authored reference target",
    "U": "no member of the closed typed fact union faithfully carries this mechanic, and it is "
    "not affirmatively irreducible; classifying it PROSE_BOUND would be a backlog state",
    "F": "states a mechanic the closed typed union carries exactly",
    "P": "applicability qualifier that cannot be reduced without executable interpretation",
    "O": "states one option of an exhaustive actor choice the closed union carries",
    "AC": "states the closed condition under which the component or option applies",
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

# AMENDMENT 2. New filenames; the retained schema-2 proposal/audit are untouched.
PROPOSAL_PATH = OUT / "issue-5d-conditions-1-schema2-REGEN-PROPOSAL.json"
AUDIT_PATH = OUT / "issue-5d-conditions-1-schema2-REGEN-audit.json"
#: The constraint is "never overwrite the retained review evidence", not "never
#: re-run this checkpoint". Assert the retained filenames are not write targets.
_RETAINED = {
    "issue-5d-batch-conditions-1-schema2-PROPOSAL.json",
    "issue-5d-batch-conditions-1-schema2-audit.json",
    "issue-5d-batch-conditions-1-schema2-generator.py",
    "issue-5d-batch-conditions-1-PROPOSAL.json",
    "issue-5d-batch-conditions-1-audit.json",
    "issue-5d-batch-conditions-1-generator.py",
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
print("conditions-1 against 5d-representation-schema-2")
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
    drift.append(
        {
            "measure": _key,
            "expected": _expected,
            "derived": _actual,
            "match": _actual == _expected,
            **({"note": _note} if _note else {}),
        }
    )

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
        "reuse_justification": (
            "Copy of issue-5d-batch-conditions-1-schema2-generator.py with the "
            "stale worktree import path repointed at merged main. "
            "`git diff --stat 97f924c 7395c52 -- src/` is empty, so main's src/ "
            "is byte-identical to the PR #155 schema-2 merge."
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
        "NO REGENERATION DRIFT"
        if all(d["match"] for d in drift)
        else "DRIFT — see canary_drift"
    ),
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
    print(
        f"  {'OK ' if d['match'] else 'DRIFT'}  {d['measure']:<34} "
        f"expected={d['expected']}  derived={d['derived']}"
    )
print()
print(f"typed facts (component-only)        : {FACTS_COMPONENT_ONLY}")
print(f"typed facts (including option facts): {FACTS_INCLUDING_OPTIONS}")
print(f"missing human acceptance records    : {len(_missing_records)}")
print()
print(AUDIT["canary_drift_summary"])
print(f"proposal -> {PROPOSAL_PATH}")
print(f"audit    -> {AUDIT_PATH}")
