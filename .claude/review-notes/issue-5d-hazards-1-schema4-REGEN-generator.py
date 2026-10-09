"""Machine proposal generator - CRD Issue 5d batch `hazards-1`, representation schema 4.

DISPOSABLE REVIEW MATERIAL. Emits a `MechanicalProposal` payload and an audit
trail only. Never writes to `oracles/`, never calls `accept_proposal`, never
touches the database, never publishes or activates anything.

Regeneration, not an edit. The schema-1 and schema-3 hazards artifacts are
retained byte-for-byte as the record of what was previously concluded; their
span cuts, classifications, components, facts, counts and identity are NOT
authoritative here. What IS carried across is the boundary (the source's own
`[Hazard]` entry class plus its umbrella `Hazard` glossary rule), the derivation
method, the release assertions, and the refusal guards. The boundary is
re-derived from the bound 5c release and asserted, not asserted from memory.

THE EMISSION RULE, unchanged in wording and re-applied against a wider schema:

    Emit a typed fact only when the fact's own claim is true as stated and its
    scope is not narrowed or multiplied by a predicate the schema cannot carry.
    Refuse when an unrepresentable qualifier would make the fact apply where the
    source does not, or apply once where the source repeats it.

Under schema 3 that rule refused six facts, because the narrowing predicates -
a consumption threshold, a roll outcome, a damage outcome, a cadence, a cause
scope - had no structures. Schema 4 supplies all of them, so the same rule now
admits them. No fact is emitted here that schema 3 could have carried.

TWO DISCLOSED REPRESENTATION LIMITS. Neither is an unresolved span and neither
is an Owner Decision; both are stated so a semantic reviewer can rule on them.
See the header of the audit file, which carries the same two entries.

  D-1 (corpus-general, the one worth ruling on). `AbilityCheckFact` carries no
      roll-context axis, so Malnutrition's *"must succeed on a DC 10
      Constitution saving throw"* and a hypothetical DC 10 Constitution *check*
      produce byte-identical typed authority. The family's docstring has
      declared its scope as "a check or save with a typed DC source" since
      schema 1 (83abb91, #137), through two accepted reviews, and schema 4's
      only context rule - `_check_alternatives`' refusal of a non-check
      alternative - governs the alternatives set and never runs on an empty
      tuple. Emitting the fact is therefore using the family exactly as
      declared. What a consumer cannot recover from the typed surface is which
      of the three D20 Tests is called for. Candidate shape for a later
      schema: a `RollContext` axis on the family. Prevalence: every DC-bearing
      saving throw in the corpus.

  D-2 (settled, recorded for completeness). `Applicability(ELAPSED_DURATION,
      value=5, unit=DAY)` carries Malnutrition's *"A creature that eats nothing
      for 5 days"* - the clause the enum member's own docstring cites as its
      evidence. "eats nothing" rides the owning record and component rather
      than the applicability. The alternative considered and rejected was a
      component `applies_when` plus a `FactQualifier` composing conjunctively:
      that has no accepted precedent, and `FactQualifier` declares its purpose
      as one fact's condition *where it differs from its siblings'*, which is
      not this case. Using two scopes as a conjunction operator would be the
      predicate language `Applicability` is built to refuse.

TWO COMPOSITION READINGS, stated rather than left to a reader (Falling):

  C-1 `ScalingFact.threshold` under `DISTANCE_FALLEN` is the **per-unit
      interval** - 1d6 per 10 feet - which is how the closure manifest declared
      the enum member. Under `HIGHER_LEVEL_SPELL_SLOT` the same field is the
      level above which the increase begins. The two readings agree at this
      record's granularity, but they are not the same reading.
  C-2 `DamageFact(1d6, maximum_dice=20)` and `ScalingFact(dice_amount=1d6)` are
      one composition, not a base plus an increment: the damage *is* the
      scaling. The die is stated once by the sentence and the two families
      state different halves of it - the amount and type, and the basis and
      interval it repeats over. They carry different fact keys, so
      `_validate_duplicated_fact_authority` does not see them; the intended
      reading is recorded here instead of relied on.
"""

from __future__ import annotations

import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(r"D:\AI\Claude\afterworlds")
sys.path.insert(0, str(REPO / "src"))
OUT = Path(__file__).parent

# --- Retained-evidence guard ------------------------------------------------
# The schema-1 and schema-3 artifacts are the record of superseded conclusions
# and of the discovery this run derives from. Refuse to run at all if this file
# would overwrite one of them, and assert after the run that none of them moved.
RETAINED = (
    "issue-5d-batch-hazards-1-PROPOSAL.json",
    "issue-5d-batch-hazards-1-audit.json",
    "issue-5d-batch-hazards-1-generator.py",
    "issue-5d-hazards-1-schema3-REGEN-PROPOSAL.json",
    "issue-5d-hazards-1-schema3-REGEN-audit.json",
    "issue-5d-hazards-1-schema3-REGEN-generator.py",
    "issue-5d-hazards-1-obligation-LEDGER.md",
    "issue-5d-hazards-1-sibling-AUDIT.md",
    "issue-5d-hazards-1-schema-closure-CHECKPOINT.md",
)
WRITES = {
    "issue-5d-hazards-1-schema4-REGEN-PROPOSAL.json",
    "issue-5d-hazards-1-schema4-REGEN-audit.json",
}
assert not (WRITES & set(RETAINED)), "would overwrite retained evidence"
_RETAINED_BEFORE = {
    n: hashlib.md5((OUT / n).read_bytes()).hexdigest()
    for n in RETAINED
    if (OUT / n).exists()
}

from afterworlds.ingestion.corpus.pipeline import build_candidate  # noqa: E402
from afterworlds.ingestion.corpus.policy import exclusion_reason_for  # noqa: E402
from afterworlds.ingestion.corpus.reconcile import _full_coverage_edges  # noqa: E402
from afterworlds.ingestion.mechanical.acceptance import (  # noqa: E402
    _merge_representation,
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
    ReviewState,
    SemanticDisposition,
    SemanticSpan,
)
from afterworlds.ingestion.mechanical.oracle import (  # noqa: E402
    _representation,
    load_accepted_inputs,
)
from afterworlds.ingestion.mechanical.policy import (  # noqa: E402
    SEMANTIC_POLICY_VERSION,
    semantic_policy_hash,
)
from afterworlds.ingestion.mechanical.projection import (  # noqa: E402
    ReleaseBinding,
    representation_payload,
)
from afterworlds.ingestion.mechanical.proposal import (  # noqa: E402
    MechanicalProposal,
    ProposedSpan,
    proposal_identity,
    proposal_payload,
)
from afterworlds.ingestion.mechanical.representation import (  # noqa: E402
    RECORD_OWNED_REFERENCE,
    REPRESENTATION_SCHEMA_VERSION,
    AbilityCheckFact,
    AbilityScore,
    ActionCost,
    ActionEconomyFact,
    Applicability,
    ApplicabilityKind,
    AutomaticOutcome,
    Comparison,
    ComponentDraft,
    ConditionEffectFact,
    ConditionEffectKind,
    ConditionKind,
    ConditionLevelFact,
    ConditionRemovalRestrictionFact,
    CreatureSize,
    DamageFact,
    DamageModDirection,
    DamageModificationFact,
    DamageOutcome,
    DamageType,
    DerivedQuantityFact,
    DiceExpression,
    DieSize,
    EffectTerminationFact,
    FactQualifier,
    LevelDirection,
    MeasureUnit,
    ProseBindingDraft,
    ProvenanceClaim,
    ProvenanceRole,
    ProvenanceTargetKind,
    Rational,
    RecordDraft,
    RecordKind,
    Recurrence,
    RecurrenceBoundary,
    ReferenceDraft,
    RepresentationDraft,
    RequiredQuantity,
    RollActor,
    RollContext,
    RollSpec,
    ScalingBasis,
    ScalingDirection,
    ScalingEffect,
    ScalingFact,
    SizeKeyedQuantityFact,
    SizeQuantity,
    Skill,
    TimePeriod,
    TimeUnit,
    DcKind,
    fact_key,
    fact_qualifier_target_key,
    fact_target_key,
    held_structure_violations,
    prose_binding_target_key,
    reference_target_key,
    representation_draft_violations,
    representation_schema_hash,
)
from afterworlds.ingestion.mechanical.schema_lift import (  # noqa: E402
    lift_for,
    schema_binding_violations,
    verify_lift,
)
from afterworlds.ingestion.mechanical.validation import (  # noqa: E402
    validate_representation,
)
from afterworlds.pipeline.retrieval.config import RetrievalMemoryConfig  # noqa: E402

SCHEMA = (REPRESENTATION_SCHEMA_VERSION, representation_schema_hash())
assert SCHEMA[0] == "5d-representation-schema-4", SCHEMA

# ---------------------------------------------------------------------------
# Bound release - derived from the committed PDF, asserted against production
# ---------------------------------------------------------------------------

PACKAGE_UUID = "4458fa10-4a66-5e0e-9ecc-ea37530ad2b4"
RELEASE_VERSION = "5.2.1-corpus.36b786d8-fa2"
SOURCE_SHA256 = "8974902d109d6e63672d7c490bde9ccf052410503d9cfa768237154fbc5e3d87"  # pragma: allowlist secret
TRANSFORM_CONFIG_HASH = "77720c2f3b8c9b88363d48050466fb8e3a26f8476b63145d1b5928ff2581ef3e"  # pragma: allowlist secret
BUNDLE_ROOT_HASH = "03353dfb79790aee7260b9ed96055b7296cd6f70e3e6f97d6cbe0a2484279685"  # pragma: allowlist secret

#: The only binding value NOT independently derivable here: a function of the
#: persisted `rp_sources` rows and verified Chroma state, so reproducing it
#: requires an actual publish, which this generator must not do. Taken from the
#: published CRD Issue 5c release record. The five values above ARE derived
#: from the committed PDF and asserted below.
PERSISTED_CORPUS_DIGEST = "c1f547962b7d9096986f0b8e75624f9f8803dfc281c16033e1c2250cad5a929b"  # pragma: allowlist secret

CAND = build_candidate(
    REPO / "docs/sources/DnD5_5e_SRD_CC_v5_2_1.pdf",
    retrieval_config=RetrievalMemoryConfig(),
)
assert CAND.package_uuid == PACKAGE_UUID, CAND.package_uuid
assert CAND.release_version == RELEASE_VERSION, CAND.release_version
assert CAND.authoritative_source_hash == SOURCE_SHA256, CAND.authoritative_source_hash
assert CAND.transform_config_hash == TRANSFORM_CONFIG_HASH, CAND.transform_config_hash
assert CAND.bundle.bundle_root_hash == BUNDLE_ROOT_HASH, CAND.bundle.bundle_root_hash

LEDGER_OBJ = CAND.ledger
LABELS = {c.container_id: c.label for c in LEDGER_OBJ.containers}
CONTAINERS = {c.container_id: c for c in LEDGER_OBJ.containers}
LEAF_BY_ID = {leaf.leaf_id: leaf for leaf in LEDGER_OBJ.leaves}
REPRESENTED = {
    leaf.leaf_id
    for leaf in LEDGER_OBJ.leaves
    if exclusion_reason_for(leaf, LABELS) is None
}
EDGES = _full_coverage_edges(CAND.members.chunks, LEAF_BY_ID)

BINDING = ReleaseBinding(
    package_uuid=CAND.package_uuid,
    release_version=CAND.release_version,
    authoritative_source_hash=CAND.authoritative_source_hash,
    transform_config_hash=CAND.transform_config_hash,
    bundle_root_hash=CAND.bundle.bundle_root_hash,
    persisted_corpus_digest=PERSISTED_CORPUS_DIGEST,
)
CORPUS = BoundCorpusSnapshot(
    package_uuid=CAND.package_uuid,
    release_version=CAND.release_version,
    leaf_lengths={lid: len(LEAF_BY_ID[lid].content) for lid in REPRESENTED},
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


def _ancestry(cid: str) -> list[str]:
    out, cur = [], CONTAINERS.get(cid)
    while cur:
        out.append(cur.container_id)
        cur = CONTAINERS.get(cur.parent_id) if cur.parent_id else None
    return out


RULES_DEFINITIONS = next(
    c.container_id for c in LEDGER_OBJ.containers if c.label == "Rules Definitions"
)
ENTRY_BY_LABEL = {
    c.label: c.container_id
    for c in LEDGER_OBJ.containers
    if c.container_type == "entry" and RULES_DEFINITIONS in _ancestry(c.container_id)
}

by_container: dict[str, list] = defaultdict(list)
for leaf in LEDGER_OBJ.leaves:
    if leaf.leaf_id not in REPRESENTED:
        continue
    for cid in leaf.container_path:
        by_container[cid].append(leaf)
for group in by_container.values():
    group.sort(key=lambda x: (x.page_index, x.char_start))

# --- Boundary, re-derived from the source rather than asserted --------------
# The source's own entry class. `[Hazard]`-tagged entries under Rules
# Definitions, plus the umbrella `Hazard` glossary rule whose See-also names
# exactly those five. Derived by scanning the labels, then checked against the
# five names the umbrella prints - so a hazard added or renamed upstream would
# fail here rather than silently drop out of the batch.
HAZARD_LABELS = sorted(lab for lab in ENTRY_BY_LABEL if lab.endswith(" [Hazard]"))
UMBRELLA_LEAF = by_container[ENTRY_BY_LABEL["Hazard"]][3]
NAMED = [
    n for n in ("Burning", "Dehydration", "Falling", "Malnutrition", "Suffocation")
]
assert HAZARD_LABELS == [f"{n} [Hazard]" for n in sorted(NAMED)], HAZARD_LABELS
for _n in NAMED:
    assert _n in UMBRELLA_LEAF.content, f"{_n} not named by the umbrella See-also"
assert len(HAZARD_LABELS) == 5, HAZARD_LABELS

POLICY_EXCLUDED = [
    leaf.leaf_id
    for lab in [*HAZARD_LABELS, "Hazard"]
    for leaf in by_container[ENTRY_BY_LABEL[lab]]
    if leaf.leaf_id not in REPRESENTED
]
assert not POLICY_EXCLUDED, POLICY_EXCLUDED

SCOPE_KEY = "srd-5.2.1/rules-glossary"
LSQ = "\u201c"  # left double quote
RSQ = "\u201d"  # right double quote
APOS = "\u2019"

RECORD_KEY: dict[str, str] = {"Hazard": "glossary.hazard"}
for lab in HAZARD_LABELS:
    RECORD_KEY[lab] = "hazard." + lab.split(" [")[0].lower()
RECORD_KIND = {k: RecordKind.GLOSSARY_RULE for k in RECORD_KEY.values()}

HAZ = "glossary.hazard"
BUR, DEH, FAL, MAL, SUF = (
    "hazard.burning",
    "hazard.dehydration",
    "hazard.falling",
    "hazard.malnutrition",
    "hazard.suffocation",
)

# ---------------------------------------------------------------------------
# The typed facts, declared once and referenced by the clause table below
# ---------------------------------------------------------------------------

D6 = DiceExpression(count=1, die=DieSize.D6)

#: Burning. The cadence rides `ComponentDraft.recurs`, so the bare amount is no
#: longer false: the fact states 1d4 Fire, the recurrence states that it repeats
#: at the start of each of the subject's turns.
BURN_DAMAGE = DamageFact(
    damage_type=DamageType.FIRE, dice=DiceExpression(count=1, die=DieSize.D4)
)
ACTION_COST = ActionEconomyFact(cost=ActionCost.ACTION)
REACTION_COST = ActionEconomyFact(cost=ActionCost.REACTION)
PRONE_APPLIES = ConditionEffectFact(
    condition=ConditionKind.PRONE, effect=ConditionEffectKind.APPLIES
)
#: Burning's two independent termination routes. `ConditionEffectKind.REMOVES`
#: removes a *condition* and a hazard is not one, which is why this family
#: exists. Two components hold the same fact from two *different* substantive
#: spans - two genuinely separate rules, which the sibling-duplication rule
#: leaves alone by design.
TERMINATION = EffectTerminationFact()

GAIN_1 = ConditionLevelFact(
    condition=ConditionKind.EXHAUSTION, direction=LevelDirection.GAIN, amount=1
)

WATER_REQ = SizeKeyedQuantityFact(
    quantity=RequiredQuantity.WATER,
    period=TimePeriod.DAY,
    values=(
        SizeQuantity(CreatureSize.TINY, Rational(1, 4), MeasureUnit.GALLON),
        SizeQuantity(CreatureSize.SMALL, Rational(1, 1), MeasureUnit.GALLON),
        SizeQuantity(CreatureSize.MEDIUM, Rational(1, 1), MeasureUnit.GALLON),
        SizeQuantity(CreatureSize.LARGE, Rational(4, 1), MeasureUnit.GALLON),
        SizeQuantity(CreatureSize.HUGE, Rational(16, 1), MeasureUnit.GALLON),
        SizeQuantity(CreatureSize.GARGANTUAN, Rational(64, 1), MeasureUnit.GALLON),
    ),
)
FOOD_REQ = SizeKeyedQuantityFact(
    quantity=RequiredQuantity.FOOD,
    period=TimePeriod.DAY,
    values=(
        SizeQuantity(CreatureSize.TINY, Rational(1, 4), MeasureUnit.POUND),
        SizeQuantity(CreatureSize.SMALL, Rational(1, 1), MeasureUnit.POUND),
        SizeQuantity(CreatureSize.MEDIUM, Rational(1, 1), MeasureUnit.POUND),
        SizeQuantity(CreatureSize.LARGE, Rational(4, 1), MeasureUnit.POUND),
        SizeQuantity(CreatureSize.HUGE, Rational(16, 1), MeasureUnit.POUND),
        SizeQuantity(CreatureSize.GARGANTUAN, Rational(64, 1), MeasureUnit.POUND),
    ),
)

#: "can't be removed until the creature drinks the full amount ... required for
#: a day". `cause_scoped` is required True by the family: this restricts the
#: levels *this record* caused, and never amends `condition.exhaustion`'s own
#: removal rule. A consumer composes the two at adjudication time.
WATER_REMOVAL = ConditionRemovalRestrictionFact(
    condition=ConditionKind.EXHAUSTION,
    until=Applicability(
        kind=ApplicabilityKind.CONSUMPTION_THRESHOLD,
        required_quantity=RequiredQuantity.WATER,
        comparison=Comparison.REACHES,
        fraction=Rational(1, 1),
    ),
)
FOOD_REMOVAL = ConditionRemovalRestrictionFact(
    condition=ConditionKind.EXHAUSTION,
    until=Applicability(
        kind=ApplicabilityKind.CONSUMPTION_THRESHOLD,
        required_quantity=RequiredQuantity.FOOD,
        comparison=Comparison.REACHES,
        fraction=Rational(1, 1),
    ),
)

FALL_DAMAGE = DamageFact(damage_type=DamageType.BLUDGEONING, dice=D6, maximum_dice=20)
FALL_SCALING = ScalingFact(
    basis=ScalingBasis.DISTANCE_FALLEN,
    threshold=10,
    effect=ScalingEffect.DAMAGE,
    direction=ScalingDirection.INCREASE,
    dice_amount=D6,
)
HALVING = DamageModificationFact(
    direction=DamageModDirection.REDUCE,
    factor=Rational(1, 2),
    #: R-3, explicit. Falling states a halving and nothing about rounding; the
    #: governing `Round Down` glossary entry is outside this boundary and is not
    #: imported. A fact must not claim provenance over a span this batch never
    #: accounted, so this stays unset and a consumer composes the two records.
    rounding=None,
)

_ATHLETICS = RollSpec(
    actor=RollActor.SUBJECT,
    context=RollContext.ABILITY_CHECK,
    ability=AbilityScore.STRENGTH,
    skill=Skill.ATHLETICS,
)
_ACROBATICS = RollSpec(
    actor=RollActor.SUBJECT,
    context=RollContext.ABILITY_CHECK,
    ability=AbilityScore.DEXTERITY,
    skill=Skill.ACROBATICS,
)


def _canonical_alternatives(*rolls: RollSpec) -> tuple[RollSpec, ...]:
    """The alternatives set in the canonical order the invariant requires.

    Sorted by the payload the validator itself compares, rather than authored in
    source order and hoped to agree: two authorings of one closed choice must
    produce one fact key.
    """
    from afterworlds.ingestion.corpus.hashing import canonical_bytes
    from afterworlds.ingestion.mechanical.representation import _dataclass_payload

    return tuple(sorted(rolls, key=lambda r: canonical_bytes(_dataclass_payload(r))))


SURFACE_CHECK = AbilityCheckFact(
    ability=AbilityScore.STRENGTH,
    dc_kind=DcKind.FIXED,
    dc_value=15,
    skill=Skill.ATHLETICS,
    alternatives=_canonical_alternatives(_ATHLETICS, _ACROBATICS),
)
#: See disclosed limit D-1 in the module docstring: the family carries no
#: roll-context axis, so this fact does not say the roll is a saving throw.
CON_SAVE = AbilityCheckFact(
    ability=AbilityScore.CONSTITUTION, dc_kind=DcKind.FIXED, dc_value=10
)

BREATH = DerivedQuantityFact(
    base=1,
    modifier=AbilityScore.CONSTITUTION,
    unit=TimeUnit.MINUTE,
    floor_amount=30,
    floor_unit=TimeUnit.SECOND,
)
SUFF_REMOVAL = ConditionLevelFact(
    condition=ConditionKind.EXHAUSTION,
    direction=LevelDirection.REMOVE,
    all_levels=True,
    #: "levels it gained from suffocating" - this removal reaches only the
    #: levels this record caused, never those dehydration or malnutrition did.
    cause_scoped=True,
)

# ---------------------------------------------------------------------------
# Components, declared explicitly. Facts are collected from the clause table.
# ---------------------------------------------------------------------------

CONS = ApplicabilityKind.CONSUMPTION_THRESHOLD
COMPONENTS: dict[tuple[str, str], dict] = {
    (BUR, "burning_damage"): dict(
        handling=ComponentHandling.STRUCTURED,
        recurs=Recurrence(
            boundary=RecurrenceBoundary.START_OF_TURN, whose=RollActor.SUBJECT
        ),
    ),
    (BUR, "self_extinguish"): dict(handling=ComponentHandling.STRUCTURED),
    (BUR, "ambient_extinguish"): dict(
        handling=ComponentHandling.MIXED, reason="contextual_applicability"
    ),
    (DEH, "water_requirement"): dict(handling=ComponentHandling.STRUCTURED),
    (DEH, "dehydration_exhaustion"): dict(
        handling=ComponentHandling.STRUCTURED,
        applies_when=Applicability(
            kind=CONS,
            required_quantity=RequiredQuantity.WATER,
            comparison=Comparison.LESS_THAN,
            fraction=Rational(1, 2),
        ),
        recurs=Recurrence(boundary=RecurrenceBoundary.END_OF_DAY),
    ),
    # Separate from the accrual on purpose. The accrual's consumption threshold
    # governs when a level is gained; it does not govern the removal
    # restriction, and a component `applies_when` composes conjunctively over
    # everything the component holds.
    (DEH, "dehydration_recovery"): dict(handling=ComponentHandling.STRUCTURED),
    (FAL, "fall_damage"): dict(handling=ComponentHandling.STRUCTURED),
    (FAL, "landing"): dict(
        handling=ComponentHandling.STRUCTURED,
        #: "unless it avoids taking any damage from the fall" - the source
        #: states the exception in the negative and `DamageOutcome.NO_DAMAGE`
        #: cites this exact clause, so the negation is kept rather than folded
        #: into `ANY_DAMAGE`.
        applies_when=Applicability(
            kind=ApplicabilityKind.DAMAGE_OUTCOME,
            negated=True,
            damage_outcome=DamageOutcome.NO_DAMAGE,
        ),
    ),
    (FAL, "surface_check"): dict(
        handling=ComponentHandling.MIXED, reason="contextual_applicability"
    ),
    (FAL, "fall_halving"): dict(
        handling=ComponentHandling.STRUCTURED,
        applies_when=Applicability(
            kind=ApplicabilityKind.ROLL_OUTCOME, outcome=AutomaticOutcome.SUCCESS
        ),
    ),
    (MAL, "food_requirement"): dict(handling=ComponentHandling.STRUCTURED),
    (MAL, "starvation_save"): dict(
        handling=ComponentHandling.STRUCTURED,
        applies_when=Applicability(
            kind=CONS,
            required_quantity=RequiredQuantity.FOOD,
            comparison=Comparison.LESS_THAN,
            fraction=Rational(1, 2),
        ),
        recurs=Recurrence(boundary=RecurrenceBoundary.END_OF_DAY),
        # The component's own condition governs both facts; only the level gain
        # is additionally conditioned on failing the save. That is exactly the
        # sibling differentiation `FactQualifier` is declared for.
        fact_qualifiers=(
            FactQualifier(
                fact_key=fact_key(GAIN_1),
                applies_when=Applicability(
                    kind=ApplicabilityKind.ROLL_OUTCOME,
                    outcome=AutomaticOutcome.FAILURE,
                ),
            ),
        ),
    ),
    (MAL, "starvation_automatic"): dict(
        handling=ComponentHandling.STRUCTURED,
        applies_when=Applicability(
            kind=ApplicabilityKind.ELAPSED_DURATION, value=5, unit=TimeUnit.DAY
        ),
        recurs=Recurrence(boundary=RecurrenceBoundary.END_OF_DAY),
    ),
    (MAL, "malnutrition_recovery"): dict(handling=ComponentHandling.STRUCTURED),
    (SUF, "breath_duration"): dict(handling=ComponentHandling.STRUCTURED),
    # H-16, Shape B. One MIXED component whose whole disjunctive trigger is
    # affirmative governing prose, with the consequence stated ONCE as typed
    # authority. No Boolean predicate, no wrapper fact, no duplicated sibling.
    # "runs out of breath" is typed-able given the breath duration above; "is
    # choking" is fiction the SRD never defines mechanically. Reducing `A or B`
    # to typed `A` loses B; carrying both as scopes asserts `A and B`, because
    # component, option and qualifier scopes compose conjunctively.
    (SUF, "suffocation_accrual"): dict(
        handling=ComponentHandling.MIXED,
        reason="contextual_applicability",
        recurs=Recurrence(
            boundary=RecurrenceBoundary.END_OF_TURN, whose=RollActor.SUBJECT
        ),
    ),
    (SUF, "suffocation_recovery"): dict(
        handling=ComponentHandling.MIXED, reason="contextual_applicability"
    ),
}

# ---------------------------------------------------------------------------
# The proposed batch, as an explicit reviewable clause table
# ---------------------------------------------------------------------------
#
# Segment kinds:
#   R  supporting authority, claimed CONTEXTUAL by the record
#   C  supporting authority, claimed CONTEXTUAL by a component        arg=comp
#   X  supporting authority, claimed CONTEXTUAL by a reference        arg=(text,target)
#   F  substantive, claimed PRIMARY by a typed fact                   arg=(comp,fact)
#   A  substantive, claimed PRIMARY by its owning component           arg=comp
#   Q  substantive, claimed PRIMARY by a fact qualifier               arg=(comp,fact)
#   P  substantive, claimed PRIMARY by a prose binding                arg=(comp,reason)
#
# `A` covers a component's applicability span and its recurrence span alike: a
# recurrence is a property of its component exactly as `applies_when` is, so the
# owning component is the honest PRIMARY claimant and no ProvenanceTargetKind
# for a recurrence is needed.

W = [(None, "R", None)]  # whole leaf, supporting authority, owned by the record
CTX = "contextual_applicability"

SPEC: dict[str, list] = {}

# --- Hazard (umbrella glossary rule) ---------------------------------------
# The five names are source-authored mechanical references (#137 contract 3 and
# 7, ADR-005d Decision 7). This record has no component and honestly cannot
# acquire one - "A hazard is an environmental danger." states a category, not a
# mechanic, and no member of the closed irreducibility catalog describes it.
# Schema 4's record-grain reference ownership is what resolves them without
# fabricating a component to hang them on.
SPEC["Hazard"] = [
    W,  # 'Hazard'
    W,  # 'A hazard is an environmental danger.' - states the category
    W,  # 'See also'
    [
        (f"{LSQ}Burning,{RSQ}", "X", ("Burning", BUR)),
        (f"{LSQ}Dehydration,{RSQ}", "X", ("Dehydration", DEH)),
        (f"{LSQ}Falling,{RSQ}", "X", ("Falling", FAL)),
        (f"{LSQ}Malnutrition,{RSQ}", "X", ("Malnutrition", MAL)),
        (" and", "R", None),
        (None, "X", ("Suffocation", SUF)),  # ' "Suffocation."'
    ],
]

# --- Burning ---------------------------------------------------------------
SPEC["Burning [Hazard]"] = [
    W,
    [
        ("A burning creature or object", "C", "burning_damage"),
        (" takes 1d4 Fire damage", "F", ("burning_damage", BURN_DAMAGE)),
        (" at the start of each of its turns.", "A", "burning_damage"),
        (" As an action,", "F", ("self_extinguish", ACTION_COST)),
        (" you can extinguish fire on yourself", "F", ("self_extinguish", TERMINATION)),
        (
            " by giving yourself the Prone condition",
            "F",
            ("self_extinguish", PRONE_APPLIES),
        ),
        (" and rolling on the ground.", "C", "self_extinguish"),
        (" The fire also goes out", "F", ("ambient_extinguish", TERMINATION)),
        # Affirmative, not a backlog state: the consequence is typed above, and
        # what remains is whether a fire counts as doused, submerged or
        # suffocated - fiction the projection cannot enumerate.
        (None, "P", ("ambient_extinguish", CTX)),
    ],
]

# --- Dehydration -----------------------------------------------------------
SPEC["Dehydration [Hazard]"] = [
    W,
    [
        (
            "as shown in the Water Needs per Day table.",
            "F",
            ("water_requirement", WATER_REQ),
        ),
        (
            " A creature that drinks less than half the required water for a day",
            "A",
            "dehydration_exhaustion",
        ),
        (" gains 1 Exhaustion level", "F", ("dehydration_exhaustion", GAIN_1)),
        (f" at the day{APOS}s end.", "A", "dehydration_exhaustion"),
        (
            " Exhaustion caused by dehydration",
            "F",
            ("dehydration_recovery", WATER_REMOVAL),
        ),
        # One fact, two spans, both PRIMARY: it states the cause scope and the
        # removal gate, and ADR-005d Decision 3 is exactly this many-to-many.
        (None, "F", ("dehydration_recovery", WATER_REMOVAL)),
    ],
    W,  # 'See also'
    [
        (f"{LSQ}Exhaustion.{RSQ}", "X", ("Exhaustion", "condition.exhaustion")),
        (None, "C", "water_requirement"),  # ' Water Needs per Day' - names the table
    ],
    [(None, "C", "water_requirement")],  # 'Size'  (column header)
    [(None, "C", "water_requirement")],  # 'Water' (column header)
    [(None, "F", ("water_requirement", WATER_REQ))],  # 'Tiny'
    [(None, "F", ("water_requirement", WATER_REQ))],  # '1/4 gallon'
    [(None, "F", ("water_requirement", WATER_REQ))],  # 'Small'
    [(None, "F", ("water_requirement", WATER_REQ))],  # '1 gallon'
    [(None, "F", ("water_requirement", WATER_REQ))],  # 'Medium'
    [(None, "F", ("water_requirement", WATER_REQ))],  # '1 gallon'
    [
        ("Size Water", "C", "water_requirement"),  # repeated header
        ("Large", "F", ("water_requirement", WATER_REQ)),
        (" 4 gallons", "F", ("water_requirement", WATER_REQ)),
        (" Huge", "F", ("water_requirement", WATER_REQ)),
        (" 16 gallons", "F", ("water_requirement", WATER_REQ)),
        (" Gargantuan", "F", ("water_requirement", WATER_REQ)),
        (None, "F", ("water_requirement", WATER_REQ)),  # ' 64 gallons'
    ],
]

# --- Falling ---------------------------------------------------------------
SPEC["Falling [Hazard]"] = [
    W,
    [
        ("A creature that falls", "C", "fall_damage"),
        (
            " takes 1d6 Bludgeoning damage at the end of the fall",
            "F",
            ("fall_damage", FALL_DAMAGE),
        ),
        (" for every 10 feet it fell,", "F", ("fall_damage", FALL_SCALING)),
        (" to a maximum of 20d6.", "F", ("fall_damage", FALL_DAMAGE)),
        (
            " When the creature lands, it has the Prone condition",
            "F",
            ("landing", PRONE_APPLIES),
        ),
        (" unless it avoids taking any damage from the fall.", "A", "landing"),
        # The source itself generalises to "another liquid"; whether a substance
        # qualifies is fiction the projection cannot enumerate.
        (
            " A creature that falls into water or another liquid",
            "P",
            ("surface_check", CTX),
        ),
        (" can use its Reaction", "F", ("surface_check", REACTION_COST)),
        (
            " to make a DC 15 Strength (Athletics) or Dexterity (Acrobatics) check",
            "F",
            ("surface_check", SURFACE_CHECK),
        ),
        (" to hit the surface head or feet first.", "C", "surface_check"),
        (" On a successful check,", "A", "fall_halving"),
        (None, "F", ("fall_halving", HALVING)),  # ' any damage ... is halved.'
    ],
]

# --- Malnutrition ----------------------------------------------------------
SPEC["Malnutrition [Hazard]"] = [
    W,
    [
        (
            "as shown in the Food Needs per Day table.",
            "F",
            ("food_requirement", FOOD_REQ),
        ),
        (
            " A creature that eats but consumes less than half the required food for a day",
            "A",
            "starvation_save",
        ),
        (
            " must succeed on a DC 10 Constitution saving throw",
            "F",
            ("starvation_save", CON_SAVE),
        ),
        # The failure branch, stated by the source's own "or". Split from the
        # consequence so the qualifier and the fact each claim the span that
        # states them - FACT_QUALIFIER is a provenance-required kind.
        (" or", "Q", ("starvation_save", GAIN_1)),
        (" gain 1 Exhaustion level", "F", ("starvation_save", GAIN_1)),
        (f" at the day{APOS}s end.", "A", "starvation_save"),
        (" A creature that eats nothing for 5 days", "A", "starvation_automatic"),
        (
            " automatically gains 1 Exhaustion level",
            "F",
            ("starvation_automatic", GAIN_1),
        ),
        (
            " at the end of the fifth day as well as an additional level at the end of"
            " each subsequent day without food.",
            "A",
            "starvation_automatic",
        ),
        (
            " Exhaustion caused by malnutrition",
            "F",
            ("malnutrition_recovery", FOOD_REMOVAL),
        ),
        (None, "F", ("malnutrition_recovery", FOOD_REMOVAL)),
    ],
    W,  # 'See also'
    [
        (f"{LSQ}Exhaustion.{RSQ}", "X", ("Exhaustion", "condition.exhaustion")),
        (None, "C", "food_requirement"),  # ' Food Needs per Day'
    ],
    [(None, "C", "food_requirement")],  # 'Size'
    [(None, "C", "food_requirement")],  # 'Food'
    [(None, "C", "food_requirement")],  # 'Size'
    [(None, "C", "food_requirement")],  # 'Food'
    *[
        [(None, "F", ("food_requirement", FOOD_REQ))] for _ in range(12)
    ],  # the twelve data cells
]

# --- Suffocation -----------------------------------------------------------
SPEC["Suffocation [Hazard]"] = [
    W,
    [
        ("(minimum of 30 seconds)", "F", ("breath_duration", BREATH)),
        (" before suffocation begins.", "C", "breath_duration"),
        (" or is choking,", "P", ("suffocation_accrual", CTX)),  # whole trigger
        (" it gains 1 Exhaustion level", "F", ("suffocation_accrual", GAIN_1)),
        (" at the end of each of its turns.", "A", "suffocation_accrual"),
        # Whether a creature can breathe again depends on the fiction - out of
        # the water, unchoked, air present. `RecoveryTrigger` is rest-shaped and
        # would be a false claim, so the trigger is affirmative governing prose.
        (" When a creature can breathe again,", "P", ("suffocation_recovery", CTX)),
        (None, "F", ("suffocation_recovery", SUFF_REMOVAL)),
    ],
]

# ---------------------------------------------------------------------------
# Emission
# ---------------------------------------------------------------------------

spans: list[SemanticSpan] = []
proposed: list[ProposedSpan] = []
provenance: list[ProvenanceClaim] = []
references: list[ReferenceDraft] = []
prose_bindings: list[ProseBindingDraft] = []
comp_facts: dict[tuple[str, str], list] = defaultdict(list)
audit: list[dict] = []

DISP = {
    "R": SemanticDisposition.SUPPORTING_AUTHORITY,
    "C": SemanticDisposition.SUPPORTING_AUTHORITY,
    "X": SemanticDisposition.SUPPORTING_AUTHORITY,
    "F": SemanticDisposition.SUBSTANTIVE,
    "A": SemanticDisposition.SUBSTANTIVE,
    "Q": SemanticDisposition.SUBSTANTIVE,
    "P": SemanticDisposition.SUBSTANTIVE,
}
RATIONALE = {
    "R": (
        "identifies, frames, or exemplifies the mechanic; preserved as supporting "
        "authority owned by the record rather than discarded"
    ),
    "C": (
        "names, frames, or describes what a component states; supporting authority "
        "owned by that component"
    ),
    "X": (
        "a source-authored mechanical reference, resolved at build time within a "
        "committed scope to an exact target record; supporting authority, because "
        "naming a rule is not stating one"
    ),
    "F": (
        "states a mechanic the closed typed union carries exactly, with every "
        "qualifier that narrows or multiplies it carried by a structure of this "
        "schema rather than left implicit"
    ),
    "A": (
        "states when its component applies, or how often its effect repeats; the "
        "owning component is the element that carries the claim, exactly as it "
        "carries an applicability"
    ),
    "Q": (
        "states the condition on one fact of a component that its siblings do not "
        "share; carried by that fact's own qualifier"
    ),
    "P": (
        "affirmatively irreducible under a closed reason code: the predicate "
        "ranges over fiction the projection cannot enumerate, and the mechanic it "
        "governs is stated as typed authority beside it"
    ),
}


def _add_fact(owner: tuple[str, str], fact: object) -> None:
    """Hold each distinct fact once, however many spans state it."""
    key = fact_key(fact)
    if all(fact_key(f) != key for f in comp_facts[owner]):
        comp_facts[owner].append(fact)


for label, leafspecs in SPEC.items():
    entry_id = ENTRY_BY_LABEL[label]
    rkey = RECORD_KEY[label]
    lvs = by_container[entry_id]
    assert len(lvs) == len(
        leafspecs
    ), f"{label}: {len(lvs)} leaves vs {len(leafspecs)} specs"

    for lf, segs in zip(lvs, leafspecs, strict=True):
        content, lid = lf.content, lf.leaf_id
        cursor = 0
        for marker, kind, arg in segs:
            if marker is None:
                end = len(content)
            else:
                found = content.find(marker, cursor)
                assert found >= 0, f"{label}: marker {marker!r} not in {content!r}"
                end = found + len(marker)
            assert end > cursor, f"{label}: empty segment for marker {marker!r}"
            start, cursor = cursor, end
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
                ProposedSpan(
                    span=span,
                    origin="issue-5d-hazards-1-schema4-REGEN-generator.py",
                    rationale=RATIONALE[kind],
                )
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
                    "owner": (arg[0] if isinstance(arg, tuple) else (arg or rkey)),
                }
            )

            if kind == "R":
                provenance.append(
                    ProvenanceClaim(
                        ProvenanceTargetKind.RECORD,
                        (rkey,),
                        sid,
                        ProvenanceRole.CONTEXTUAL,
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
            elif kind == "A":
                provenance.append(
                    ProvenanceClaim(
                        ProvenanceTargetKind.COMPONENT,
                        (rkey, arg),
                        sid,
                        ProvenanceRole.PRIMARY,
                    )
                )
            elif kind == "X":
                text, target = arg
                ref = ReferenceDraft(
                    from_record_key=rkey,
                    from_component_key=RECORD_OWNED_REFERENCE,
                    source_text=text,
                    scope_key=SCOPE_KEY,
                    target_record_key=target,
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
                _add_fact((rkey, comp), fact)
                provenance.append(
                    ProvenanceClaim(
                        ProvenanceTargetKind.FACT,
                        fact_target_key(rkey, comp, fact),
                        sid,
                        ProvenanceRole.PRIMARY,
                    )
                )
            elif kind == "Q":
                comp, fact = arg
                provenance.append(
                    ProvenanceClaim(
                        ProvenanceTargetKind.FACT_QUALIFIER,
                        fact_qualifier_target_key(rkey, comp, fact_key(fact), ""),
                        sid,
                        ProvenanceRole.PRIMARY,
                    )
                )
            elif kind == "P":
                comp, reason = arg
                extent = CORPUS.chunk_relative_range(
                    chunk_of_leaf[lid], lid, start, end
                )
                assert extent is not None, f"{label}: no chunk extent for {sid}"
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
    RecordDraft(semantic_key=k, kind=RECORD_KIND[k])
    for k in sorted(set(RECORD_KEY.values()))
)
components = tuple(
    ComponentDraft(
        record_key=rkey,
        semantic_key=ckey,
        handling=spec["handling"],
        irreducibility_reason_code=spec.get("reason"),
        facts=tuple(comp_facts[(rkey, ckey)]),
        applies_when=spec.get("applies_when"),
        fact_qualifiers=spec.get("fact_qualifiers", ()),
        recurs=spec.get("recurs"),
    )
    for (rkey, ckey), spec in COMPONENTS.items()
)

DRAFT = RepresentationDraft(
    records=records,
    components=components,
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

touched = sorted({s.leaf_id for s in spans})
partition: list[str] = []
for lid in touched:
    partition.extend(validate_partition(lid, CORPUS.leaf_lengths[lid], tuple(spans)))
reason_codes = validate_reason_codes(tuple(spans))
schema_binding = schema_binding_violations(DRAFT, SCHEMA)
standalone = list(validate_representation(DRAFT, LEDGER, CORPUS))

assert len(touched) == 43, f"leaves accounted: {len(touched)}"
assert len(records) == 6, f"records: {len(records)}"

# --- Merged verification, exactly the shape acceptance would validate -------
#
# `validate_representation` is only ever called on the post-merge candidate
# (`projection.build_candidate_findings`), never on a proposal's draft in
# isolation. Two of this batch's references - Dehydration's and Malnutrition's
# `"Exhaustion."` - resolve into ACCEPTED conditions-1 authority, which is
# supplied by the `prior=` merge inside `accept_proposal`. Reproducing that
# merge here (without accepting anything) is what proves those two obligations
# are cross-batch resolutions rather than residue: the standalone run reports
# them as unknown targets and the merged run reports nothing.
#
# The accepted artifact is READ ONLY. Nothing here writes it, and the lift is
# verified rather than applied - schema 4 is strictly additive, so a schema-3
# element's canonical form already is its schema-4 canonical form.
ACCEPTED_PATH = (
    REPO
    / "src/afterworlds/ingestion/mechanical/oracles"
    / "srd-5-2-1-corpus-36b786d8-fa2.json"
)
_accepted_before = hashlib.sha256(ACCEPTED_PATH.read_bytes()).hexdigest()
PRIOR = load_accepted_inputs(ACCEPTED_PATH)
LIFT = lift_for((PRIOR.oracle.schema_version, PRIOR.oracle.schema_hash), SCHEMA)
LIFT_RECORD = verify_lift(LIFT, PRIOR.oracle.representation)

MERGED = _merge_representation(PRIOR.oracle.representation, DRAFT)
MERGED_LEDGER = ClassificationLedger(
    package_uuid=BINDING.package_uuid,
    release_version=BINDING.release_version,
    policy_version=SEMANTIC_POLICY_VERSION,
    policy_hash=semantic_policy_hash(),
    spans=tuple(PRIOR.oracle.spans) + tuple(spans),
    batches=(),
    acceptances=(),
)
merged_findings = list(validate_representation(MERGED, MERGED_LEDGER, CORPUS))

# --- Disjointness from the accepted conditions-1 review scope ---------------
prior_spans = {s.span_id for s in PRIOR.oracle.spans}
prior_leaves = {s.leaf_id for s in PRIOR.oracle.spans}
prior_records = {r.semantic_key for r in PRIOR.oracle.representation.records}
prior_components = {
    (c.record_key, c.semantic_key) for c in PRIOR.oracle.representation.components
}
DISJOINT = {
    "span_overlap": sorted(prior_spans & {s.span_id for s in spans}),
    "leaf_overlap": sorted(prior_leaves & set(touched)),
    "record_overlap": sorted(prior_records & {r.semantic_key for r in records}),
    "component_overlap": sorted(
        prior_components & {(c.record_key, c.semantic_key) for c in components}
    ),
    "prior_spans_retained": len(prior_spans),
    "prior_records_retained": len(prior_records),
    "prior_elements_unchanged": all(
        getattr(MERGED, f)[: len(getattr(PRIOR.oracle.representation, f))]
        == getattr(PRIOR.oracle.representation, f)
        for f in (
            "records",
            "components",
            "prose_bindings",
            "references",
            "relationships",
            "provenance",
        )
    ),
}
assert not DISJOINT["span_overlap"], DISJOINT["span_overlap"]
assert not DISJOINT["leaf_overlap"], DISJOINT["leaf_overlap"]
assert not DISJOINT["record_overlap"], DISJOINT["record_overlap"]
assert not DISJOINT["component_overlap"], DISJOINT["component_overlap"]
assert DISJOINT["prior_elements_unchanged"], "the merge moved accepted authority"

# --- Structural validation, stated separately from the representation gate --
# The closed-shape checks `_merge_representation` runs at the acceptance seam,
# run here directly so the artifact records them as their own column rather than
# only as "the merge did not raise".
STRUCTURAL = [
    *representation_draft_violations(DRAFT),
    *held_structure_violations(DRAFT),
]

# --- Wire round-trip --------------------------------------------------------
# Serializing and hashing proves an identity; it does not prove the loader can
# rebuild what was emitted. This batch is the first to combine `applies_when`
# with `recurs` and `fact_qualifiers` on one component (`starvation_save`), the
# first to carry a recurrence on a MIXED component (`suffocation_accrual`), and
# the first to negate a schema-4 applicability kind (`landing`). A field silently
# dropped by canonicalization would make the proposal unacceptable, and the
# semantic review would be spent on an artifact that cannot be accepted.
#
# Payload-to-payload, never payload-to-object: `representation_payload` orders
# every collection, so comparing against DRAFT would fail on ordering alone.
_WIRE_OUT = representation_payload(DRAFT)
_WIRE_BACK = representation_payload(_representation(json.loads(json.dumps(_WIRE_OUT))))
WIRE_ROUND_TRIP = _WIRE_OUT == _WIRE_BACK
assert WIRE_ROUND_TRIP, "the emitted draft does not survive the wire"

# --- Schema-4 structure demonstration, derived from the emitted draft -------
# Every row is computed from what was actually built, never asserted from the
# design notes: a structure nothing exercises reports an empty site list and the
# assertion below fails.
_sites: dict[str, list[str]] = defaultdict(list)
for _c in components:
    _at = f"{_c.record_key}/{_c.semantic_key}"
    if _c.recurs is not None:
        _sites[f"recurrence ({_c.recurs.boundary.value})"].append(_at)
    if _c.applies_when is not None:
        _sites[f"applicability ({_c.applies_when.kind.value})"].append(_at)
    for _q in _c.fact_qualifiers:
        _sites[f"fact qualifier ({_q.applies_when.kind.value})"].append(_at)
    for _f in _c.facts:
        _fam = _f.FAMILY.value
        _sites[f"fact family ({_fam})"].append(_at)
        if _fam == "damage" and _f.maximum_dice is not None:
            _sites["DamageFact.maximum_dice (the 20d6 cap)"].append(_at)
        if _fam == "scaling" and _f.basis is ScalingBasis.DISTANCE_FALLEN:
            _sites["ScalingBasis.DISTANCE_FALLEN"].append(_at)
        if _fam == "ability_check" and _f.alternatives:
            _sites["AbilityCheckFact.alternatives + Skill axis"].append(_at)
        if _fam == "condition_level" and _f.cause_scoped:
            _sites["ConditionLevelFact.cause_scoped"].append(_at)
        if _fam == "condition_removal_restriction":
            _sites["ConditionRemovalRestrictionFact.cause_scoped"].append(_at)
        if _fam == "damage_modification":
            _sites[
                f"DamageModificationFact (factor {_f.factor.numerator}/"
                f"{_f.factor.denominator}, rounding={_f.rounding})"
            ].append(_at)
        if _fam == "derived_quantity" and _f.floor_amount is not None:
            _sites["DerivedQuantityFact floor"].append(_at)
for _r in references:
    if _r.from_component_key == RECORD_OWNED_REFERENCE:
        _sites["record-owned reference"].append(
            f"{_r.from_record_key} -> {_r.target_record_key}"
        )

#: The twelve structures this regeneration was asked to demonstrate, each keyed
#: to the site list above. A missing or empty entry fails the run.
DEMONSTRATED = {
    "recurrence and termination": [
        "recurrence (start_of_turn)",
        "recurrence (end_of_turn)",
        "recurrence (end_of_day)",
        "fact family (effect_termination)",
    ],
    "size-keyed requirements": ["fact family (size_keyed_quantity)"],
    "consumption thresholds": ["applicability (consumption_threshold)"],
    "cause-scoped Exhaustion and removal restrictions": [
        "ConditionLevelFact.cause_scoped",
        "ConditionRemovalRestrictionFact.cause_scoped",
        "fact family (condition_removal_restriction)",
    ],
    "distance-fallen scaling and the 20d6 cap": [
        "ScalingBasis.DISTANCE_FALLEN",
        "DamageFact.maximum_dice (the 20d6 cap)",
    ],
    "damage-outcome applicability": ["applicability (damage_outcome)"],
    "alternative Strength (Athletics) / Dexterity (Acrobatics) checks": [
        "AbilityCheckFact.alternatives + Skill axis"
    ],
    "roll-outcome and successful-check applicability": [
        "applicability (roll_outcome)",
        "fact qualifier (roll_outcome)",
    ],
    "damage halving": ["fact family (damage_modification)"],
    "elapsed-duration thresholds": ["applicability (elapsed_duration)"],
    "modifier-derived duration with a floor": [
        "fact family (derived_quantity)",
        "DerivedQuantityFact floor",
    ],
    "record-owned references": ["record-owned reference"],
}
DEMO_EVIDENCE = {
    obligation: {row: sorted(set(_sites[row])) for row in rows}
    for obligation, rows in DEMONSTRATED.items()
}
for _ob, _rows in DEMO_EVIDENCE.items():
    for _row, _at in _rows.items():
        assert _at, f"{_ob}: {_row} is exercised nowhere"

#: The 33 open obligations of the schema-3 ledger, mapped to what closes each
#: here. Stated as a table so a reviewer can reject one line at a time.
OBLIGATIONS = {
    "O-1": "glossary.hazard: 5 record-owned references to the five hazard records",
    "O-2": "burning_damage: DamageFact(FIRE, 1d4) + Recurrence(START_OF_TURN, subject)",
    "O-3": "self_extinguish: EffectTerminationFact(OWNING_EFFECT)",
    "O-4": "ambient_extinguish: EffectTerminationFact + prose binding over the trigger",
    "O-5": "water_requirement: SizeKeyedQuantityFact(WATER, DAY, 6 rows)",
    "O-6": "dehydration_exhaustion.applies_when CONSUMPTION_THRESHOLD(WATER, <, 1/2)",
    "O-7": "dehydration_exhaustion: ConditionLevelFact(EXHAUSTION, GAIN, 1)",
    "O-8": "dehydration_exhaustion.recurs Recurrence(END_OF_DAY)",
    "O-9": "dehydration_recovery: ConditionRemovalRestrictionFact.cause_scoped",
    "O-10": "dehydration_recovery.until CONSUMPTION_THRESHOLD(WATER, reaches, 1/1)",
    "O-11": "hazard.dehydration record-owned reference -> condition.exhaustion",
    "O-12": "fall_damage: ScalingFact(DISTANCE_FALLEN, threshold 10, DAMAGE, 1d6)",
    "O-13": "fall_damage: DamageFact.maximum_dice = 20",
    "O-14": "landing.applies_when DAMAGE_OUTCOME(NO_DAMAGE, negated)",
    "O-15": "surface_check: AbilityCheckFact skill=ATHLETICS + 2 alternatives",
    "O-16": "fall_halving.applies_when ROLL_OUTCOME(SUCCESS) + DamageModificationFact",
    "O-17": "food_requirement: SizeKeyedQuantityFact(FOOD, DAY, 6 rows)",
    "O-18": "starvation_save.applies_when CONSUMPTION_THRESHOLD(FOOD, <, 1/2)",
    "O-19": "starvation_save: AbilityCheckFact(CON, FIXED, 10) - see D-1",
    "O-20": "starvation_save.fact_qualifiers ROLL_OUTCOME(FAILURE) on the level gain",
    "O-21": "starvation_save.recurs Recurrence(END_OF_DAY)",
    "O-22": "starvation_automatic.applies_when ELAPSED_DURATION(5, DAY) - see D-2",
    "O-23": "starvation_automatic: ConditionLevelFact(EXHAUSTION, GAIN, 1)",
    "O-24": "starvation_automatic.recurs Recurrence(END_OF_DAY)",
    "O-25": "malnutrition_recovery: ConditionRemovalRestrictionFact.cause_scoped",
    "O-26": "malnutrition_recovery.until CONSUMPTION_THRESHOLD(FOOD, reaches, 1/1)",
    "O-27": "hazard.malnutrition record-owned reference -> condition.exhaustion",
    "O-28": "breath_duration: DerivedQuantityFact(1 + CON mod minutes, floor 30 s)",
    "O-29": "suffocation_accrual: MIXED prose binding over the whole trigger (H-16 B)",
    "O-30": "suffocation_accrual: ConditionLevelFact(EXHAUSTION, GAIN, 1), stated once",
    "O-31": "suffocation_accrual.recurs Recurrence(END_OF_TURN, subject)",
    "O-32": "suffocation_recovery: MIXED prose binding over the recovery trigger",
    "O-33": "suffocation_recovery: ConditionLevelFact(REMOVE, all_levels, cause_scoped)",
}
assert len(OBLIGATIONS) == 33, len(OBLIGATIONS)

# --- Sibling components holding an equivalent fact --------------------------
# The defect family PR #159's merge-blocking finding came from, so it is stated
# in the artifact rather than left as a code comment. Two pairs exist here and
# both are legal: `_validate_duplicated_fact_authority` requires all three of
# different components, an equivalent fact key, AND a shared substantive span.
# Neither pair shares a span - each draws its fact from a genuinely different
# rule - which is exactly the case the rule leaves alone by design.
_fact_spans: dict[tuple[str, str, str], list[str]] = defaultdict(list)
_text_of = {a["span_id"]: a["text"] for a in audit}
for _cl in provenance:
    if _cl.target_kind is not ProvenanceTargetKind.FACT:
        continue
    _rk, _ck, _fk = _cl.target_key[0], _cl.target_key[1], _cl.target_key[2]
    _fact_spans[(_rk, _fk, _ck)].append(_cl.span_id)
_by_record_fact: dict[tuple[str, str], dict[str, list[str]]] = defaultdict(dict)
for (_rk, _fk, _ck), _sids in _fact_spans.items():
    _by_record_fact[(_rk, _fk)][_ck] = sorted(_sids)
SIBLING_PAIRS = [
    {
        "record": _rk,
        "fact_key": _fk,
        "components": sorted(_holders),
        "spans_per_component": {
            _ck: [_text_of[s_] for s_ in _sids]
            for _ck, _sids in sorted(_holders.items())
        },
        "shares_a_substantive_span": bool(
            set.intersection(*(set(v) for v in _holders.values()))
        ),
        "verdict": (
            "legal: two different rules state the same mechanic, from different "
            "spans; the rule requires a SHARED substantive span and there is none"
        ),
    }
    for (_rk, _fk), _holders in sorted(_by_record_fact.items())
    if len(_holders) > 1
]
for _pair in SIBLING_PAIRS:
    assert not _pair["shares_a_substantive_span"], _pair

# --- H-16 and R-3, checked rather than asserted -----------------------------
_accrual = next(
    c
    for c in components
    if (c.record_key, c.semantic_key) == (SUF, "suffocation_accrual")
)
_suf_gains = [
    (c.semantic_key, f)
    for c in components
    if c.record_key == SUF
    for f in c.facts
    if getattr(f, "FAMILY", None) is not None
    and f.FAMILY.value == "condition_level"
    and f.direction is LevelDirection.GAIN
]
H16 = {
    "handling": _accrual.handling.value,
    "irreducibility_reason_code": _accrual.irreducibility_reason_code,
    "typed_facts": len(_accrual.facts),
    "components_in_record": sum(1 for c in components if c.record_key == SUF),
    "accrual_facts_in_record": len(_suf_gains),
    "trigger_carried_as": "one prose binding over the whole disjunction, uncut",
    "boolean_predicates_invented": 0,
    "wrapper_facts_invented": 0,
    "duplicated_sibling_authority": 0,
}
assert _accrual.handling is ComponentHandling.MIXED, H16
assert len(_accrual.facts) == 1 and len(_suf_gains) == 1, H16
assert (
    sum(
        1
        for b in prose_bindings
        if (b.record_key, b.component_key) == (SUF, "suffocation_accrual")
    )
    == 1
), "the H-16 trigger must be one binding, not two"

R3 = {
    "governing_rule": "Rules Glossary > Rules Definitions > Round Down",
    # It is a Rules Definitions entry of its own, and it is not in this batch.
    "exists_as_its_own_entry": "Round Down" in ENTRY_BY_LABEL,
    "in_this_boundary": "Round Down" in SPEC,
    "imported": any(r.target_record_key.endswith("round_down") for r in references),
    "rounding_field": HALVING.rounding,
    "disposition": (
        "left unset. This record states a halving and nothing about rounding; the "
        "Round Down entry states its own rule in its own batch, and a fact must "
        "not claim provenance over a span this batch never accounted."
    ),
}
assert HALVING.rounding is None and not R3["imported"], R3
assert not R3["in_this_boundary"] and R3["exists_as_its_own_entry"], R3

# --- Ownership integrity: who states what, checked over the emitted edges ----
_by_span = defaultdict(list)
for _cl in provenance:
    _by_span[_cl.span_id].append(_cl)
_disp = {s_.span_id: s_.disposition for s_ in spans}
_primary_kind: dict[str, int] = defaultdict(int)
for _sid, _cls in _by_span.items():
    for _cl in _cls:
        if _cl.role is ProvenanceRole.PRIMARY:
            _primary_kind[_cl.target_kind.value] += 1
OWNERSHIP = {
    "substantive_spans": sum(
        1 for d in _disp.values() if d is SemanticDisposition.SUBSTANTIVE
    ),
    "substantive_with_exactly_one_primary_claimant": sum(
        1
        for sid, d in _disp.items()
        if d is SemanticDisposition.SUBSTANTIVE
        and sum(1 for c in _by_span[sid] if c.role is ProvenanceRole.PRIMARY) == 1
    ),
    "primary_claimants_by_element_kind": dict(sorted(_primary_kind.items())),
    "supporting_spans": sum(
        1 for d in _disp.values() if d is SemanticDisposition.SUPPORTING_AUTHORITY
    ),
    "supporting_spans_carrying_a_primary_claim": sum(
        1
        for sid, d in _disp.items()
        if d is SemanticDisposition.SUPPORTING_AUTHORITY
        and any(c.role is ProvenanceRole.PRIMARY for c in _by_span[sid])
    ),
    "prose_bindings_over_supporting_text": sum(
        1
        for b in prose_bindings
        if _disp[b.span_id] is not SemanticDisposition.SUBSTANTIVE
    ),
    "spans_with_no_claim_at_all": sum(1 for sid in _disp if not _by_span[sid]),
}
assert (
    OWNERSHIP["substantive_with_exactly_one_primary_claimant"]
    == OWNERSHIP["substantive_spans"]
), OWNERSHIP
assert OWNERSHIP["supporting_spans_carrying_a_primary_claim"] == 0, OWNERSHIP
assert OWNERSHIP["prose_bindings_over_supporting_text"] == 0, OWNERSHIP
assert OWNERSHIP["spans_with_no_claim_at_all"] == 0, OWNERSHIP

PROPOSAL = MechanicalProposal(
    binding=BINDING,
    policy_version=SEMANTIC_POLICY_VERSION,
    policy_hash=semantic_policy_hash(),
    schema_version=SCHEMA[0],
    schema_hash=SCHEMA[1],
    proposed_spans=tuple(proposed),
    proposed_representation=DRAFT,
    proposal_origin=(
        "issue-5d-hazards-1-schema4-REGEN-generator.py "
        "(CRD Issue 5d batch hazards-1, representation schema 4)"
    ),
)
payload = proposal_payload(PROPOSAL)
ident = proposal_identity(PROPOSAL)

counts: dict[str, int] = defaultdict(int)
for s in spans:
    counts[s.disposition.value] += 1
per_record: dict[str, dict] = defaultdict(
    lambda: {"leaves": set(), "spans": 0, "unresolved": 0}
)
for a in audit:
    rec = per_record[a["record"]]
    rec["leaves"].add(a["leaf"])
    rec["spans"] += 1
    if a["disposition"] == "unresolved":
        rec["unresolved"] += 1

AUDIT_DOC = {
    "_": (
        "CRD Issue 5d batch hazards-1, representation schema 4. Proposal and "
        "audit only: nothing accepted, published, activated or retired."
    ),
    "proposal_identity": ident,
    "representation_schema": {"version": SCHEMA[0], "hash": SCHEMA[1]},
    "semantic_policy": {
        "version": SEMANTIC_POLICY_VERSION,
        "hash": semantic_policy_hash(),
    },
    "release_binding": {
        "package_uuid": BINDING.package_uuid,
        "release_version": BINDING.release_version,
        "authoritative_source_hash": BINDING.authoritative_source_hash,
        "transform_config_hash": BINDING.transform_config_hash,
        "bundle_root_hash": BINDING.bundle_root_hash,
        "persisted_corpus_digest": BINDING.persisted_corpus_digest,
        "derivation": (
            "five of six re-derived from the committed PDF through build_candidate "
            "and asserted at run time; persisted_corpus_digest carried from the "
            "published CRD Issue 5c release record and disclosed as such"
        ),
    },
    "boundary": {
        "records": len(records),
        "represented_leaves": len(touched),
        "policy_exclusions": len(POLICY_EXCLUDED),
        "derivation": (
            "the source's own [Hazard] entry class under Rules Definitions plus "
            "the umbrella Hazard glossary rule; the five names are re-checked "
            "against the umbrella's own See-also text"
        ),
    },
    "counts": {
        "spans": len(spans),
        "substantive": counts["substantive"],
        "supporting_authority": counts["supporting_authority"],
        "non_mechanical": counts["non_mechanical"],
        "unresolved": counts["unresolved"],
        "components": len(components),
        "components_structured": sum(
            1 for c in components if c.handling is ComponentHandling.STRUCTURED
        ),
        "components_mixed": sum(
            1 for c in components if c.handling is ComponentHandling.MIXED
        ),
        "components_prose_bound": sum(
            1 for c in components if c.handling is ComponentHandling.PROSE_BOUND
        ),
        "facts": sum(len(c.facts) for c in components),
        "prose_bindings": len(prose_bindings),
        "references": len(references),
        "relationships": 0,
        "provenance_edges": len(provenance),
    },
    "per_record": {
        r: {
            "leaves": len(d["leaves"]),
            "spans": d["spans"],
            "unresolved": d["unresolved"],
        }
        for r, d in sorted(per_record.items())
    },
    "validation": {
        "partition": partition,
        "structural": STRUCTURAL,
        "wire_round_trip": WIRE_ROUND_TRIP,
        "reason_codes": reason_codes,
        "schema_binding": schema_binding,
        "representation_standalone": standalone,
        "representation_merged_with_accepted_conditions_1": merged_findings,
        "note": (
            "validate_representation is only ever run on the post-merge candidate. "
            "The standalone column exists to show which findings are exactly the "
            "cross-batch reference resolutions the prior= merge supplies."
        ),
    },
    "disjointness_from_accepted_conditions_1": DISJOINT,
    "schema_succession": {
        "lift_id": LIFT_RECORD.lift_id,
        "from": [LIFT_RECORD.from_version, LIFT_RECORD.from_hash],
        "to": [LIFT_RECORD.to_version, LIFT_RECORD.to_hash],
        "verified_collections": list(LIFT_RECORD.verified_collections),
        "accepted_artifact_sha256_unchanged": _accepted_before
        == hashlib.sha256(ACCEPTED_PATH.read_bytes()).hexdigest(),
    },
    "disclosed_representation_limits": [
        {
            "id": "D-1",
            "status": "admissible as declared; imprecise; for semantic review",
            "where": (
                "hazard.malnutrition/starvation_save - "
                "' must succeed on a DC 10 Constitution saving throw'"
            ),
            "limit": (
                "AbilityCheckFact carries no roll-context axis, so a DC 10 "
                "Constitution saving throw and a DC 10 Constitution ability check "
                "produce byte-identical typed authority."
            ),
            "why_emitted": (
                "The family's docstring has declared its scope as 'a check or save "
                "with a typed DC source' since schema 1 (83abb91, #137), through "
                "two accepted reviews. Schema 4's only roll-context rule "
                "(_check_alternatives) governs the alternatives set and never runs "
                "on an empty tuple. Refusing the fact would contradict a standing "
                "declaration; leaving the span UNRESOLVED would manufacture "
                "residue as surely as emitting a false fact would manufacture zero."
            ),
            "candidate_shape": "a RollContext axis on AbilityCheckFact",
            "prevalence": "every DC-bearing saving throw in the corpus",
        },
        {
            "id": "D-2",
            "status": "settled; recorded for completeness",
            "where": (
                "hazard.malnutrition/starvation_automatic - "
                "' A creature that eats nothing for 5 days'"
            ),
            "limit": (
                "Applicability(ELAPSED_DURATION, 5, DAY) carries the duration; "
                "'eats nothing' rides the owning record and component rather than "
                "the applicability."
            ),
            "why_emitted": (
                "ApplicabilityKind.ELAPSED_DURATION's own docstring cites this "
                "exact clause as its evidence. The alternative - a component "
                "applies_when plus a FactQualifier composing conjunctively - has "
                "no accepted precedent and contradicts FactQualifier's declared "
                "purpose (one fact's condition where it differs from its "
                "siblings'), so it would be the predicate language Applicability "
                "is built to refuse."
            ),
        },
    ],
    "schema_4_structures_demonstrated": DEMO_EVIDENCE,
    "obligation_closure": OBLIGATIONS,
    "sibling_fact_pairs": SIBLING_PAIRS,
    "ownership_integrity": OWNERSHIP,
    "h16_shape_b": H16,
    "r3_disposition": R3,
    "composition_readings": {
        "C-1": (
            "ScalingFact.threshold under DISTANCE_FALLEN is the per-unit interval "
            "(1d6 per 10 feet), which is how the closure manifest declared the "
            "member; under HIGHER_LEVEL_SPELL_SLOT the same field is the level "
            "above which the increase begins."
        ),
        "C-2": (
            "DamageFact(1d6, maximum_dice=20) and ScalingFact(dice_amount=1d6) are "
            "one composition - the damage IS the scaling - not a base plus a "
            "separate increment. Two families state two halves of one sentence."
        ),
    },
    "spans": audit,
}

(OUT / "issue-5d-hazards-1-schema4-REGEN-PROPOSAL.json").write_text(
    json.dumps(payload, indent=1, sort_keys=True, ensure_ascii=False), encoding="utf-8"
)
(OUT / "issue-5d-hazards-1-schema4-REGEN-audit.json").write_text(
    json.dumps(AUDIT_DOC, indent=1, ensure_ascii=False), encoding="utf-8"
)

# Retained evidence and the accepted artifact must be untouched by this run.
for _n, _before in _RETAINED_BEFORE.items():
    _after = hashlib.md5((OUT / _n).read_bytes()).hexdigest()
    assert _after == _before, f"retained evidence {_n} changed"
assert (
    hashlib.sha256(ACCEPTED_PATH.read_bytes()).hexdigest() == _accepted_before
), "the committed accepted artifact changed"

# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

print(f"schema         {SCHEMA[0]} / {SCHEMA[1]}")
print(f"policy         {SEMANTIC_POLICY_VERSION} / {semantic_policy_hash()}")
print(f"identity       {ident}")
print(f"records        {len(records)}")
print(f"leaves         {len(touched)}   policy exclusions {len(POLICY_EXCLUDED)}")
print(f"spans          {len(spans)}")
for k in ("substantive", "supporting_authority", "non_mechanical", "unresolved"):
    print(f"  {k:22} {counts[k]}")
print(f"components     {len(components)}")
for c in components:
    bits = []
    if c.applies_when is not None:
        bits.append(f"applies_when={c.applies_when.kind.value}")
    if c.recurs is not None:
        bits.append(f"recurs={c.recurs.boundary.value}")
    if c.fact_qualifiers:
        bits.append(f"qualifiers={len(c.fact_qualifiers)}")
    print(
        f"  {c.record_key}/{c.semantic_key}: {c.handling.value}, "
        f"{len(c.facts)} facts, reason={c.irreducibility_reason_code}"
        + (("  " + " ".join(bits)) if bits else "")
    )
print(f"facts          {sum(len(c.facts) for c in components)}")
print(f"prose bindings {len(prose_bindings)}")
print(f"references     {len(references)}")
print(f"provenance     {len(provenance)}")
print("relationships  0")
print()
print(f"{'record':24} {'leaves':>6} {'spans':>6} {'unres':>6}")
for r in sorted(per_record):
    d = per_record[r]
    print(f"{r:24} {len(d['leaves']):6} {d['spans']:6} {d['unresolved']:6}")
print()
for name, found in (
    ("partition", partition),
    ("structural", STRUCTURAL),
    ("reason codes", reason_codes),
    ("schema binding", schema_binding),
    ("representation (standalone)", standalone),
    ("representation (merged w/ accepted conditions-1)", merged_findings),
):
    print(f"{name:50} {len(found)}")
    for f in found:
        print("   -", f)
print()
print(f"wire trip     {WIRE_ROUND_TRIP}")
print(f"sibling pairs  {len(SIBLING_PAIRS)} (all legal: no shared substantive span)")
print(f"ownership      {json.dumps(OWNERSHIP)}")
print(
    f"lift           {LIFT_RECORD.lift_id}: {len(LIFT_RECORD.verified_collections)} collections verified"
)
print(
    f"disjointness   {json.dumps({k: v for k, v in DISJOINT.items() if 'overlap' in k})}"
)
