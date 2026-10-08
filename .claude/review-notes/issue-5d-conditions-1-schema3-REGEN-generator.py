"""REGENERATION — conditions-1 against `5d-representation-schema-3`, from merged main.

Run against exact `origin/main` at `0ce2e53f147710c0b620bbb418622fb89e5cbd13`,
the merge of PR #157, which is the first commit where schema 3 is merged
authority rather than branch work.

Lineage, disclosed rather than implied. This is a copy of
`issue-5d-conditions-1-schema2-REGEN-generator.py` — itself a disclosed copy of
the original `issue-5d-batch-conditions-1-schema2-generator.py` — amended for
schema 3. The schema-3 amendments to the authored inputs are:

  1. `MovementCostFact` gained a required `payer`, so Grappled's surcharge
     states `COUNTERPART` and Prone's stand-up cost states `SUBJECT`. Prone also
     states `RoundingRule.DOWN`, which schema 2 could not record.
  2. `SizeComparison` gained `measured`/`reference`, so the two size tests in
     Grappled's exception name their operands instead of leaving them to a
     positional convention that does not exist.
  3. *"The grappler can drag or carry you when it moves"* becomes a
     `MovementTransportFact`. Under schema 2 it had no family and was recorded
     as SUPPORTING_AUTHORITY producing no typed fact; it is now SUBSTANTIVE.
  4. *"unless you are Tiny or two or more sizes smaller than it"* becomes a
     `FactQualifier` addressing the surcharge alone, with its own
     `FACT_QUALIFIER` provenance. Under schema 2 the only available scope was
     the whole component, which would have made the transport permission
     vanish for a Tiny subject — a rule the source does not state.

Nothing else in the authored inputs is amended. Every number in the envelope is
computed from the live objects; the canaries are compared programmatically and
are deliberately still the **pre-schema-3** values, so drift is the measurement
rather than a failure — see `canary_drift`, where each drifting line carries a
stated cause and any drift without one is a stop condition.

The output filenames carry a `schema3-REGEN` infix so the retained schema-1,
schema-2, and non-authoritative schema-3 smoke artifacts all stay intact; the
smoke proposal in particular is needed to answer "did the exact regeneration
reproduce it".

DISPOSABLE REVIEW MATERIAL. Emits a `MechanicalProposal` payload and a scratch
SQLite persistence proof only. Never writes to `oracles/`, never calls
`accept_proposal`, never publishes or activates anything.
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
}
for _bad in SUPERSEDED:
    assert ident != _bad, f"regenerated identity collides with refused {_bad}"

#: Deliberately NOT in SUPERSEDED. `2f42f2bb…` was run from an unmerged branch
#: head and was labelled non-authoritative for that reason alone — never
#: because its content was doubted. The exact regeneration from merged
#: `0ce2e53` derives the same identity, which *confirms* it rather than
#: replacing it, and is checked below rather than asserted either way here.
SMOKE_IDENTITY = "2f42f2bb82bcb4ed6ac489b47f774495d2ec5d985871a0d5b69f659fc83fb24b"

# "Cannot be accidentally selected" is a property of the repository, not a
# promise: nothing is accepted, so nothing can be picked up as authority.
_ORACLES = REPO / "src/afterworlds/ingestion/mechanical/oracles"
ORACLE_DIR_CONTENTS = sorted(x.name for x in _ORACLES.iterdir())
assert ORACLE_DIR_CONTENTS == ["README.md"], ORACLE_DIR_CONTENTS


# ---------------------------------------------------------------------------
# Did the exact regeneration reproduce the non-authoritative smoke?
# ---------------------------------------------------------------------------
#
# Answered by hashing both payloads rather than by asserting either outcome.
# The proposal payload is a pure function of (binding, policy declaration,
# schema declaration, proposed spans, proposed representation), so equality is
# provable and difference is attributable.

_SMOKE_PATH = Path(
    r"C:\Users\raven\AppData\Local\Temp\claude"
    r"\D--AI-Claude-afterworlds\ab7d9737-8024-43ad-9d26-75f0f4afe63e"
    r"\scratchpad\issue-5d-conditions-1-schema3-SMOKE-PROPOSAL.json"
)
SMOKE_COMPARISON: dict[str, object] = {
    "smoke_identity": SMOKE_IDENTITY,
    "regenerated_identity": ident,
    "identities_equal": ident == SMOKE_IDENTITY,
    "smoke_payload_available": _SMOKE_PATH.is_file(),
}
if _SMOKE_PATH.is_file():
    _smoke = json.loads(_SMOKE_PATH.read_text(encoding="utf-8"))
    SMOKE_COMPARISON["payloads_equal"] = _smoke == payload
    SMOKE_COMPARISON["smoke_payload_hash"] = hash_obj(_smoke)
    SMOKE_COMPARISON["regenerated_payload_hash"] = hash_obj(payload)
    SMOKE_COMPARISON["hashes_equal"] = hash_obj(_smoke) == hash_obj(payload)
    if _smoke != payload:
        # Attribute every difference rather than calling drift benign.
        _diffs: list[dict[str, object]] = []

        def _walk(a: object, b: object, path: str) -> None:
            if type(a) is not type(b):
                _diffs.append({"path": path, "kind": "type", "smoke": str(type(a)), "regen": str(type(b))})
                return
            if isinstance(a, dict):
                for k in sorted(set(a) | set(b)):
                    if k not in a:
                        _diffs.append({"path": f"{path}.{k}", "kind": "added", "regen": b[k]})
                    elif k not in b:
                        _diffs.append({"path": f"{path}.{k}", "kind": "removed", "smoke": a[k]})
                    else:
                        _walk(a[k], b[k], f"{path}.{k}")
            elif isinstance(a, list):
                if len(a) != len(b):
                    _diffs.append({"path": path, "kind": "length", "smoke": len(a), "regen": len(b)})
                for i, (x, y) in enumerate(zip(a, b)):
                    _walk(x, y, f"{path}[{i}]")
            elif a != b:
                _diffs.append({"path": path, "kind": "value", "smoke": a, "regen": b})

        _walk(_smoke, payload, "$")
        SMOKE_COMPARISON["difference_count"] = len(_diffs)
        SMOKE_COMPARISON["differences"] = _diffs[:200]
        SMOKE_COMPARISON["differences_truncated"] = len(_diffs) > 200
    else:
        assert ident == SMOKE_IDENTITY, (ident, SMOKE_IDENTITY)
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
OUT = Path(__file__).parent  # .claude/review-notes; untracked, never committed
PROPOSAL_PATH = OUT / "issue-5d-conditions-1-schema3-REGEN-PROPOSAL.json"
AUDIT_PATH = OUT / "issue-5d-conditions-1-schema3-REGEN-audit.json"
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
    # The non-authoritative schema-3 smoke, kept intact because the exact
    # regeneration is compared against it below.
    "issue-5d-conditions-1-schema3-SMOKE-PROPOSAL.json",
    "issue-5d-conditions-1-schema3-SMOKE-audit.json",
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
print("conditions-1 against 5d-representation-schema-3 (merged main 0ce2e53)")
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
    "substantive_spans": (
        '"The grappler can drag or carry you when it moves" had no fact family '
        "under schema 2 and was recorded as supporting authority; schema 3 "
        "carries it as a MovementTransportFact, so it becomes substantive"
    ),
    "supporting_authority_spans": (
        "the same span, leaving the supporting set — the mirror of the "
        "substantive increase, and the two must move by the same amount"
    ),
    "typed_facts": (
        "the transport fact schema 2 could not represent at all"
    ),
}

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

#: The two dispositions must move together and in opposite directions, or a
#: span changed disposition for some reason other than the transport family.
_sub = next(d for d in drift if d["measure"] == "substantive_spans")
_sup = next(d for d in drift if d["measure"] == "supporting_authority_spans")
DISPOSITION_SHIFT = {
    "substantive_delta": _sub["derived"] - _sub["expected_pre_schema_3"],
    "supporting_delta": _sup["derived"] - _sup["expected_pre_schema_3"],
    "conserved": (
        (_sub["derived"] - _sub["expected_pre_schema_3"])
        == -(_sup["derived"] - _sup["expected_pre_schema_3"])
    ),
}

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
