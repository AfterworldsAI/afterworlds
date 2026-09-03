"""Machine proposal generator - CRD Issue 5d batch `hazards-1`, representation schema 5.

DISPOSABLE REVIEW MATERIAL. Emits a `MechanicalProposal` payload and an audit
trail only. Never writes to `oracles/`, never calls `accept_proposal`, never
touches the database, never publishes or activates anything.

FRESH SEMANTIC AUTHORING, not a restamp. The rejected schema-4 proposal
`6277ff735e0e47b3337f2c3736ca7922864b1cde9a3c286b3aee48ee461ba259` is historical
diagnostic evidence. Its payload is not imported, edited, translated, restamped,
cloned, or read as generator input: every span in all six records is cut from the
bound 5c source at run time and every claim is authored here. The audit asserts
the new identity differs from it, and compares against it only after the fact,
as a diagnostic.

THE EMISSION RULE, unchanged in wording across four schemas:

    Emit a typed fact only when the fact's own claim is true as stated and its
    scope is not narrowed or multiplied by a predicate the schema cannot carry.
    Refuse when an unrepresentable qualifier would make the fact apply where the
    source does not, or apply once where the source repeats it.

WHAT SCHEMA 5 CHANGES HERE, and why each is a correction rather than a rewrite.
Each was a *collapse*: two mechanically different source statements producing one
typed payload, or one statement producing two readings.

  1. `AbilityCheckFact.context` is required. Malnutrition's *"must succeed on a
     DC 10 Constitution saving throw"* is a SAVING_THROW; Falling's *"DC 15
     Strength (Athletics) or Dexterity (Acrobatics) check"* is an ABILITY_CHECK,
     as is every `RollSpec` in its alternatives set. Under schema 4 those two
     rolls produced byte-identical authority (disclosed there as D-1).
  2. `Applicability(CONSUMPTION_THRESHOLD)` ranges over one `ConsumptionBand`.
     The four forms this batch states are now four distinct payloads:
       * Dehydration accrual - *"drinks less than half"* - upper 1/2 exclusive,
         no lower bound;
       * Malnutrition save - *"eats **but** consumes less than half"* - lower 0
         exclusive, upper 1/2 exclusive;
       * Malnutrition automatic - *"eats nothing for 5 days"* - the point band
         0..0 inclusive, sustained at least 5 days;
       * both recovery gates - *"drinks/eats the full amount required for a
         day"* - lower 1 inclusive, no upper bound.
     Schema 4 gave the first two the same payload and spelled the third as an
     `ELAPSED_DURATION` that said only "five days have passed" (disclosed there
     as D-2).
  3. Falling's damage is one `DamageFact` carrying `per=DamageInterval(...)`.
     No `ScalingFact` is emitted anywhere in this batch. The schema-4 pair had
     two readings - 3d6 or 4d6 on a 30-foot fall - and nothing said which.
  4. The successful-check halving lives in the component that holds the check,
     qualified onto the halving fact alone. A detached `ROLL_OUTCOME` naming the
     outcome of nothing is refused by the schema; so it is not authored.
  5. The Prone-on-landing exception is qualified onto the landing fact alone, so
     `fall_damage` can hold the damage and the landing together without the
     exception gating the damage.

D-3 IS RESOLVED - Owner Decision 2026-09-02, Falling's timing. Recorded here as
closed rather than deleted, so the question and its answer both stay legible.

      *A normal fall finishes during the turn in which it begins. Resolve its
      damage and landing immediately. Only delay completion when a specific rule
      provides a falling rate or duration.*

      The SRD's general Falling rule gives no speed, no distance per round and
      no duration; where the SRD intends a slower descent it says so outright -
      Ring of Feather Falling prints 60 feet per round. So no general
      fall-duration calculation and no real-world physics apply, and *"at the
      end of the fall"* and *"When the creature lands"* describe the **immediate
      completion of the fall**, not a delayed event awaiting a timing structure.

      This changes the reading, not the representation. Both phrases stay
      SUBSTANTIVE and keep their exact source accounting: each is claimed
      PRIMARY inside the span of the fact it belongs to, recorded with exact
      range and text in the audit's `falling_timing_spans`. `fall_damage` stays
      one component holding the falling damage and the landing consequence, with
      the Prone result still dependent on whether falling damage occurred. No
      schema field, prose binding, recurrence, duration, falling-speed rule or
      physics calculation is added for an ordinary fall - the ruling is that
      none is needed, and adding one would state a delay the source does not.

D-4 IS RESOLVED - Burning's required physical performance is correctly
represented, and was never an open question. The governing review instructions
already decided all three parts of it: `self_extinguish` is one MIXED component,
*"and rolling on the ground"* is substantive governing rule text, and the
consequence is stated once. The proposal does exactly that - the Action cost,
the Prone application and the `EffectTerminationFact` are typed, the rolling
clause is bound as affirmative governing prose under `contextual_applicability`
because whether the extinguishing applies depends on an act the projection
cannot enumerate, and the consequence is not repeated inside the binding's span.
No schema change and no Owner decision is outstanding.

Z-1 IS RESOLVED - the sustained zero-consumption reading is correct as
represented. *"Eats nothing for 5 days"* is continuous zero consumption for **at
least** five days; Exhaustion is gained at the end of the fifth foodless day and
again at the end of each following foodless day; the recurrence stays
conditional on continued zero consumption; and eating any food ends that
applicability. That is exactly `starvation_automatic`: the point band 0..0
inclusive with `sustained_at_least=5 DAY` as `applies_when`, composed with
`Recurrence(END_OF_DAY)`. A component's `applies_when` says when the component
applies at all, so the daily gain repeats only while the band holds and stops
the day eating resumes - no stop condition, elapsed clock or second predicate
is needed, and none is added.

NO DISCLOSED REPRESENTATION LIMITS REMAIN for `hazards-1`, and no semantic
question is left open. The three questions this batch raised - D-3, D-4 and Z-1
- are all recorded as resolved in the audit under
`resolved_representation_questions`, and the run asserts that the disclosed-limit
list is empty.

R-3 IS SEPARATE AUTHORITY. `DamageModificationFact.rounding` stays None: Falling
states a halving and nothing about rounding, and the `Round Down` glossary entry
is its own Rules Definitions entry outside this boundary. Checked, not asserted.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

#: The repository this run reads everything from, derived from where this file
#: actually lives: `<repo>/.claude/review-notes/<this file>`. A hard-coded
#: absolute path would let a generator launched from a second checkout read the
#: source code, the SRD and the accepted authority out of the first one, which
#: would make a "clean checkout reproduces it" claim prove nothing at all. No
#: environment fallback: if the layout is not this, the run stops.
OUT = Path(__file__).resolve().parent
REPO = OUT.parents[1]
assert OUT.name == "review-notes" and OUT.parent.name == ".claude", OUT
sys.path.insert(0, str(REPO / "src"))

#: The three inputs, named once and required to exist beneath the derived root
#: before anything is imported or read.
SOURCE_PDF = REPO / "docs/sources/DnD5_5e_SRD_CC_v5_2_1.pdf"
ACCEPTED_PATH = (
    REPO
    / "src/afterworlds/ingestion/mechanical/oracles"
    / "srd-5-2-1-corpus-36b786d8-fa2.json"
)
PACKAGE_ROOT = REPO / "src/afterworlds"
for _required in (SOURCE_PDF, ACCEPTED_PATH, PACKAGE_ROOT):
    assert (
        _required.exists()
    ), f"missing beneath the derived repository root: {_required}"
for _module in (
    "ingestion/mechanical/representation.py",
    "ingestion/mechanical/schema_lift.py",
    "ingestion/mechanical/validation.py",
    "ingestion/mechanical/oracle.py",
    "ingestion/mechanical/acceptance.py",
    "ingestion/mechanical/projection.py",
    "ingestion/mechanical/policy.py",
    "ingestion/corpus/pipeline.py",
):
    assert (PACKAGE_ROOT / _module).exists(), f"missing module: {_module}"

#: The rejected schema-4 proposal. Named so the run can prove it differs, never
#: read as input.
REJECTED_IDENTITY = "6277ff735e0e47b3337f2c3736ca7922864b1cde9a3c286b3aee48ee461ba259"  # noqa: E501  # pragma: allowlist secret

#: The reviewed proposal's identity and the accepted artifact's digest, pinned
#: as literals. This run reproduces the first and must not disturb the second;
#: both are asserted rather than reported, so a change stops the run instead of
#: appearing quietly in an artifact.
EXPECTED_IDENTITY = "f7ce449174102f1cdb7087a806d1f594add384282e54fb17181c4f5168c40417"  # noqa: E501  # pragma: allowlist secret

#: The accepted artifact, identified by its **content** rather than by whatever
#: bytes a particular working copy happens to hold.
#:
#: Removing the hard-coded repository path surfaced why the distinction matters.
#: `.gitattributes` declares `* text=auto eol=lf`, so a fresh checkout writes
#: this file with LF; a working copy that predates the attribute can still hold
#: CRLF. Both are the same committed content and both load to the same authority
#: - line endings between JSON tokens are structural whitespace - but their raw
#: SHA-256 digests differ, so a raw digest is a property of a checkout, not of
#: the authority. The figure this batch reported earlier, `aa59c69d...6e8a1a`,
#: is the raw digest of a CRLF working copy and is not reproducible anywhere the
#: repository's own line-ending rule is honoured.
#:
#: Pinned here, and written into the audit, are the two identifiers that do not
#: depend on a checkout: the SHA-256 of the canonical LF content, and the Git
#: blob id of the committed file. The blob id is the stronger of the two - it is
#: what "accepted authority was not modified" actually means - and it is derived
#: from the same normalized bytes rather than read out of `.git`.
ACCEPTED_CONTENT_SHA256 = "ead1458e9b54cb33831908d6c6b0faf4c1038daa474bd3acc76599b5008d81ce"  # noqa: E501  # pragma: allowlist secret
ACCEPTED_BLOB_ID = (
    "42faeca2486117cd1ea518f8b679d036d6fcde87"  # pragma: allowlist secret
)
#: The raw digest of a CRLF working copy, recorded so the earlier reports remain
#: legible. Never asserted, and never written into an artifact.
ACCEPTED_CRLF_WORKING_COPY_SHA256 = "aa59c69ddb844ad086700e0ecb8f5f9d7ad07ce9e74a38d5f19656b4c66e8a1a"  # noqa: E501  # pragma: allowlist secret

# --- Retained-evidence guard ------------------------------------------------
# Every previous hazards artifact is the record of a superseded conclusion or of
# a rejection this run derives its brief from. Refuse to run at all if this file
# would overwrite one, and assert after the run that none of them moved. Guarded
# by existence, because a clean checkout carries only what is committed.
RETAINED = (
    "issue-5d-batch-hazards-1-PROPOSAL.json",
    "issue-5d-batch-hazards-1-audit.json",
    "issue-5d-batch-hazards-1-generator.py",
    "issue-5d-hazards-1-schema3-REGEN-PROPOSAL.json",
    "issue-5d-hazards-1-schema3-REGEN-audit.json",
    "issue-5d-hazards-1-schema3-REGEN-generator.py",
    "issue-5d-hazards-1-schema4-REGEN-PROPOSAL.json",
    "issue-5d-hazards-1-schema4-REGEN-audit.json",
    "issue-5d-hazards-1-schema4-REGEN-generator.py",
    "issue-5d-hazards-1-schema4-REGEN-CHECKPOINT.md",
    "issue-5d-hazards-1-obligation-LEDGER.md",
    "issue-5d-hazards-1-sibling-AUDIT.md",
    "issue-5d-hazards-1-schema-closure-CHECKPOINT.md",
    "issue-5d-h16-provenance-gate-FINDING.md",
)
PROPOSAL_FILE = "issue-5d-hazards-1-schema5-REGEN-PROPOSAL.json"
AUDIT_FILE = "issue-5d-hazards-1-schema5-REGEN-audit.json"
#: A set, for the overwrite guard below. Every *iteration* of it is sorted:
#: Python randomizes string hashing per process, so a dict built by walking this
#: set carries a different key order in every run, and a dict written into the
#: audit that way would make the audit non-deterministic across processes for a
#: reason that has nothing to do with the content.
WRITES = {PROPOSAL_FILE, AUDIT_FILE}
assert not (WRITES & set(RETAINED)), "would overwrite retained evidence"
_RETAINED_BEFORE = {
    n: hashlib.sha256((OUT / n).read_bytes()).hexdigest()
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
    irreducibility_reason_for,
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
    ComponentDraft,
    ConditionEffectFact,
    ConditionEffectKind,
    ConditionKind,
    ConditionLevelFact,
    ConditionRemovalRestrictionFact,
    ConsumptionBand,
    CreatureSize,
    DamageFact,
    DamageInterval,
    DamageModDirection,
    DamageModificationFact,
    DamageOutcome,
    DamageType,
    DcKind,
    DerivedQuantityFact,
    DiceExpression,
    DieSize,
    DistanceUnit,
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
    ScalingFact,
    SizeKeyedQuantityFact,
    SizeQuantity,
    Skill,
    TimePeriod,
    TimeUnit,
    component_damage_composition_violations,
    component_roll_outcome_violations,
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
    lift_path,
    schema_binding_violations,
    verify_lift_path,
)
from afterworlds.ingestion.mechanical.validation import (  # noqa: E402
    validate_representation,
)
from afterworlds.pipeline.retrieval.config import RetrievalMemoryConfig  # noqa: E402

import afterworlds  # noqa: E402  # isort: skip

#: Where the imported package actually came from. An editable install in the
#: virtualenv points at whichever checkout was installed, so `sys.path` order is
#: what makes this run read its own tree - and an assertion is what proves it.
IMPORTED_FROM = Path(afterworlds.__file__).resolve().parent
assert PACKAGE_ROOT.resolve() == IMPORTED_FROM, (IMPORTED_FROM, PACKAGE_ROOT)
INPUT_PATHS = {
    "repository_root_derived_from": "Path(__file__).resolve().parents[2]",
    "source_pdf": SOURCE_PDF.relative_to(REPO).as_posix(),
    "accepted_artifact": ACCEPTED_PATH.relative_to(REPO).as_posix(),
    "afterworlds_package": IMPORTED_FROM.relative_to(REPO).as_posix(),
    "output_directory": OUT.relative_to(REPO).as_posix(),
    "note": (
        "Recorded relative to the derived root on purpose: an absolute path "
        "would make this artifact differ between two checkouts that produced "
        "identical content. Every one of these is asserted to exist, and the "
        "imported package is asserted to be the one beneath this root."
    ),
}

SCHEMA = (REPRESENTATION_SCHEMA_VERSION, representation_schema_hash())
assert SCHEMA[0] == "5d-representation-schema-5", SCHEMA
assert SCHEMA[1] == (
    "2803840899363988cc2f67e0d9f310d9baffe394d52ca0919d11388bcd7f4c40"  # pragma: allowlist secret
), SCHEMA

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
#: published CRD Issue 5c release record. The five values above ARE derived from
#: the committed PDF and asserted below.
PERSISTED_CORPUS_DIGEST = "c1f547962b7d9096986f0b8e75624f9f8803dfc281c16033e1c2250cad5a929b"  # pragma: allowlist secret

CAND = build_candidate(SOURCE_PDF, retrieval_config=RetrievalMemoryConfig())
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
for _leaf in LEDGER_OBJ.leaves:
    if _leaf.leaf_id not in REPRESENTED:
        continue
    for _cid in _leaf.container_path:
        by_container[_cid].append(_leaf)
for _group in by_container.values():
    _group.sort(key=lambda x: (x.page_index, x.char_start))

# --- Boundary, re-derived from the source rather than asserted --------------
# The source's own entry class: `[Hazard]`-tagged entries under Rules
# Definitions, plus the umbrella `Hazard` glossary rule whose See-also names
# exactly those five. Derived by scanning the labels, then checked against the
# five names the umbrella prints, so a hazard added or renamed upstream fails
# here rather than silently dropping out of the batch.
HAZARD_LABELS = sorted(lab for lab in ENTRY_BY_LABEL if lab.endswith(" [Hazard]"))
UMBRELLA_LEAF = by_container[ENTRY_BY_LABEL["Hazard"]][3]
NAMED = ["Burning", "Dehydration", "Falling", "Malnutrition", "Suffocation"]
assert [f"{n} [Hazard]" for n in sorted(NAMED)] == HAZARD_LABELS, HAZARD_LABELS
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
HALF = Rational(1, 2)
ZERO = Rational(0, 1)
WHOLE = Rational(1, 1)


def _band(
    quantity: RequiredQuantity,
    *,
    lower: Rational | None = None,
    lower_inclusive: bool = False,
    upper: Rational | None = None,
    upper_inclusive: bool = False,
    sustained_at_least: int | None = None,
    sustained_unit: TimeUnit | None = None,
) -> ConsumptionBand:
    """One share-of-requirement band, over the printed daily requirement."""
    return ConsumptionBand(
        quantity=quantity,
        period=TimePeriod.DAY,
        lower=lower,
        lower_inclusive=lower_inclusive,
        upper=upper,
        upper_inclusive=upper_inclusive,
        sustained_at_least=sustained_at_least,
        sustained_unit=sustained_unit,
    )


#: *"drinks less than half the required water for a day"*. One-sided: the source
#: says nothing about a lower edge, and drinking nothing is inside this rule.
DEHYDRATION_BAND = _band(RequiredQuantity.WATER, upper=HALF)
#: *"eats **but** consumes less than half the required food for a day"*. The
#: "but" is the lower bound, and it is what separates this rule from the next.
STARVATION_PARTIAL_BAND = _band(RequiredQuantity.FOOD, lower=ZERO, upper=HALF)
#: *"eats nothing for 5 days"*. The point band, sustained: one state with a
#: duration, never a zero test conjoined with an unrelated elapsed clock. **At
#: least** five days, which is what *"as well as an additional level at the end
#: of each subsequent day without food"* states when composed with the daily
#: recurrence: the component applies only while the band holds, so eating again
#: makes it inapplicable.
STARVATION_ZERO_BAND = _band(
    RequiredQuantity.FOOD,
    lower=ZERO,
    lower_inclusive=True,
    upper=ZERO,
    upper_inclusive=True,
    sustained_at_least=5,
    sustained_unit=TimeUnit.DAY,
)
#: *"drinks/eats the full amount ... required for a day"*. Lower 1 inclusive,
#: unbounded above - drinking more than the requirement also lifts the gate.
WATER_FULL_BAND = _band(RequiredQuantity.WATER, lower=WHOLE, lower_inclusive=True)
FOOD_FULL_BAND = _band(RequiredQuantity.FOOD, lower=WHOLE, lower_inclusive=True)

#: Burning. The cadence rides `ComponentDraft.recurs`, so the bare amount is not
#: false: the fact states 1d4 Fire, the recurrence states that it repeats at the
#: start of each of the subject's turns.
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
#: exists. Two components hold this same fact from two *different* substantive
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

#: *"can't be removed until the creature drinks the full amount ... required for
#: a day"*. `cause_scoped` is required True by the family: this restricts the
#: levels *this record* caused, and never amends `condition.exhaustion`'s own
#: removal rule. A consumer composes the two at adjudication time.
WATER_REMOVAL = ConditionRemovalRestrictionFact(
    condition=ConditionKind.EXHAUSTION,
    until=Applicability(
        kind=ApplicabilityKind.CONSUMPTION_THRESHOLD, band=WATER_FULL_BAND
    ),
)
#: Malnutrition's own removal restriction, distinct from Dehydration's by its
#: band's quantity, and preserved as this record's own authority.
FOOD_REMOVAL = ConditionRemovalRestrictionFact(
    condition=ConditionKind.EXHAUSTION,
    until=Applicability(
        kind=ApplicabilityKind.CONSUMPTION_THRESHOLD, band=FOOD_FULL_BAND
    ),
)

#: *"1d6 Bludgeoning damage at the end of the fall for every 10 feet it fell, to
#: a maximum of 20d6"* - ONE fact with ONE reading. `dice` is the per-interval
#: amount and there is no base beside it, which is why no `ScalingFact` is
#: emitted for this batch at all.
FALL_DAMAGE = DamageFact(
    damage_type=DamageType.BLUDGEONING,
    dice=D6,
    maximum_dice=20,
    per=DamageInterval(
        basis=ScalingBasis.DISTANCE_FALLEN, amount=10, unit=DistanceUnit.FOOT
    ),
)
HALVING = DamageModificationFact(
    direction=DamageModDirection.REDUCE,
    factor=HALF,
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


#: *"a DC 15 Strength (Athletics) or Dexterity (Acrobatics) check"* - an ability
#: check, and every alternative is one too.
SURFACE_CHECK = AbilityCheckFact(
    ability=AbilityScore.STRENGTH,
    dc_kind=DcKind.FIXED,
    context=RollContext.ABILITY_CHECK,
    dc_value=15,
    skill=Skill.ATHLETICS,
    alternatives=_canonical_alternatives(_ATHLETICS, _ACROBATICS),
)
#: *"must succeed on a DC 10 Constitution saving throw"* - a save. No skill (a
#: skill qualifies an ability check; a save adds save proficiency) and no
#: alternatives (the source offers no choice of roll).
CON_SAVE = AbilityCheckFact(
    ability=AbilityScore.CONSTITUTION,
    dc_kind=DcKind.FIXED,
    context=RollContext.SAVING_THROW,
    dc_value=10,
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
    #: *"levels it gained from suffocating"* - this removal reaches only the
    #: levels this record caused, never those dehydration or malnutrition did.
    cause_scoped=True,
)

# ---------------------------------------------------------------------------
# Components, declared explicitly. Facts are collected from the clause table.
# ---------------------------------------------------------------------------

CONS = ApplicabilityKind.CONSUMPTION_THRESHOLD
CTX = "contextual_applicability"

COMPONENTS: dict[tuple[str, str], dict] = {
    (BUR, "burning_damage"): dict(
        handling=ComponentHandling.STRUCTURED,
        recurs=Recurrence(
            boundary=RecurrenceBoundary.START_OF_TURN, whose=RollActor.SUBJECT
        ),
    ),
    # One MIXED component. The Action cost, the Prone application and the fire's
    # termination are all typed; the required physical performance the source
    # states beside them - "and rolling on the ground" - is affirmative
    # governing prose. See disclosed limit D-4. The consequence appears once, in
    # the typed authority, and the prose binding's span does not restate it.
    (BUR, "self_extinguish"): dict(handling=ComponentHandling.MIXED, reason=CTX),
    (BUR, "ambient_extinguish"): dict(handling=ComponentHandling.MIXED, reason=CTX),
    (DEH, "water_requirement"): dict(handling=ComponentHandling.STRUCTURED),
    (DEH, "dehydration_exhaustion"): dict(
        handling=ComponentHandling.STRUCTURED,
        applies_when=Applicability(kind=CONS, band=DEHYDRATION_BAND),
        recurs=Recurrence(boundary=RecurrenceBoundary.END_OF_DAY),
    ),
    # Separate from the accrual on purpose. The accrual's band governs when a
    # level is gained; it does not govern the removal restriction, and a
    # component `applies_when` composes conjunctively over everything the
    # component holds.
    (DEH, "dehydration_recovery"): dict(handling=ComponentHandling.STRUCTURED),
    # Damage and landing together: they are one coherent rule about one fall.
    # The exception is scoped to the landing fact by a qualifier, so it cannot
    # gate the damage - which is what a component-wide `applies_when` would do,
    # and would make a creature that took no damage take no damage.
    (FAL, "fall_damage"): dict(
        handling=ComponentHandling.STRUCTURED,
        fact_qualifiers=(
            FactQualifier(
                fact_key=fact_key(PRONE_APPLIES),
                applies_when=Applicability(
                    kind=ApplicabilityKind.DAMAGE_OUTCOME,
                    negated=True,
                    damage_outcome=DamageOutcome.NO_DAMAGE,
                ),
            ),
        ),
    ),
    # The check and what its success does, in one component. A ROLL_OUTCOME in a
    # component that calls for no roll names the outcome of nothing; here the
    # component establishes exactly one roll, and the outcome qualifies only the
    # halving fact - not the Reaction cost, and not the check itself.
    (FAL, "surface_check"): dict(
        handling=ComponentHandling.MIXED,
        reason=CTX,
        fact_qualifiers=(
            FactQualifier(
                fact_key=fact_key(HALVING),
                applies_when=Applicability(
                    kind=ApplicabilityKind.ROLL_OUTCOME,
                    outcome=AutomaticOutcome.SUCCESS,
                ),
            ),
        ),
    ),
    (MAL, "food_requirement"): dict(handling=ComponentHandling.STRUCTURED),
    (MAL, "starvation_save"): dict(
        handling=ComponentHandling.STRUCTURED,
        applies_when=Applicability(kind=CONS, band=STARVATION_PARTIAL_BAND),
        recurs=Recurrence(boundary=RecurrenceBoundary.END_OF_DAY),
        # The component's own band governs both facts; only the level gain is
        # additionally conditioned on failing the save this same component calls
        # for. That is exactly the sibling differentiation `FactQualifier` is
        # declared for, and the save it answers to is in scope.
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
    # One zero-food-governed recurring component. The band is the state, the
    # recurrence is the cadence: the fifth day and every later day are alike
    # while no food is eaten, and resuming food makes the component inapplicable
    # rather than needing a stated stop.
    (MAL, "starvation_automatic"): dict(
        handling=ComponentHandling.STRUCTURED,
        applies_when=Applicability(kind=CONS, band=STARVATION_ZERO_BAND),
        recurs=Recurrence(boundary=RecurrenceBoundary.END_OF_DAY),
    ),
    (MAL, "malnutrition_recovery"): dict(handling=ComponentHandling.STRUCTURED),
    (SUF, "breath_duration"): dict(handling=ComponentHandling.STRUCTURED),
    # H-16, Shape B. One MIXED component whose whole disjunctive trigger is
    # affirmative governing prose, with the consequence stated ONCE as typed
    # authority and the cadence stated once at component scope. No Boolean
    # predicate, no wrapper fact, no duplicated sibling, no split trigger.
    # "runs out of breath" is typed-able given the breath duration above; "is
    # choking" is fiction the SRD never defines mechanically. Reducing `A or B`
    # to typed `A` loses B; carrying both as scopes asserts `A and B`, because
    # component, option and qualifier scopes compose conjunctively.
    (SUF, "suffocation_accrual"): dict(
        handling=ComponentHandling.MIXED,
        reason=CTX,
        recurs=Recurrence(
            boundary=RecurrenceBoundary.END_OF_TURN, whose=RollActor.SUBJECT
        ),
    ),
    (SUF, "suffocation_recovery"): dict(handling=ComponentHandling.MIXED, reason=CTX),
}

# ---------------------------------------------------------------------------
# The proposed batch, as an explicit reviewable clause table
# ---------------------------------------------------------------------------
#
# Every span in all six records is authored here, not only the ones schema 5
# changes. A segment's first element is the text the segment ENDS with; None
# means "to the end of the leaf". The cut is therefore derived from the bound
# leaf content at run time and fails loudly if the source moved.
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

SPEC: dict[str, list] = {}

# --- Hazard (umbrella glossary rule) ---------------------------------------
# The five names are source-authored mechanical references (#137 contract 3 and
# 7, ADR-005d Decision 7). This record has no component and honestly cannot
# acquire one - "A hazard is an environmental danger." states a category, not a
# mechanic, and no member of the closed irreducibility catalog describes it.
# Record-grain reference ownership is what resolves them without fabricating a
# component to hang them on.
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
        # Substantive governing prose, not supporting commentary: it states half
        # of a required performance, and nothing types it. See D-4.
        (" and rolling on the ground.", "P", ("self_extinguish", CTX)),
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
# The damage sentence is cut where the source's own clauses fall, and each cut
# is claimed by the element that states it. "at the end of the fall" and "When
# the creature lands" ride inside the PRIMARY span of the fact they belong to -
# claimed and substantive, never omitted and never demoted. Per Owner Decision
# 2026-09-02 they mark the immediate completion of a fall that finishes in the
# turn it begins, so nothing is deferred for a timing structure to carry.
SPEC["Falling [Hazard]"] = [
    W,
    [
        ("A creature that falls", "C", "fall_damage"),
        (
            " takes 1d6 Bludgeoning damage at the end of the fall",
            "F",
            ("fall_damage", FALL_DAMAGE),
        ),
        # The interval the amount is dealt per - one fact, a second span.
        (" for every 10 feet it fell,", "F", ("fall_damage", FALL_DAMAGE)),
        (" to a maximum of 20d6.", "F", ("fall_damage", FALL_DAMAGE)),
        (
            " When the creature lands, it has the Prone condition",
            "F",
            ("fall_damage", PRONE_APPLIES),
        ),
        # Scoped to the landing fact alone, by a qualifier rather than by the
        # component's applicability.
        (
            " unless it avoids taking any damage from the fall.",
            "Q",
            ("fall_damage", PRONE_APPLIES),
        ),
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
        # The outcome of the check this same component calls for, qualifying the
        # halving alone.
        (" On a successful check,", "Q", ("surface_check", HALVING)),
        (None, "F", ("surface_check", HALVING)),  # ' any damage ... is halved.'
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
        # The zero-food band, sustained for five days.
        (" A creature that eats nothing for 5 days", "A", "starvation_automatic"),
        (
            " automatically gains 1 Exhaustion level",
            "F",
            ("starvation_automatic", GAIN_1),
        ),
        # The fifth day and every subsequent day without food: one cadence at
        # component scope, governed by the same band.
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
        # The WHOLE disjunctive trigger, uncut: " When a creature runs out of
        # breath or is choking,". Its exact boundary is derived below and
        # asserted, rather than copied from the H-16 finding's recorded offsets.
        (" or is choking,", "P", ("suffocation_accrual", CTX)),
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
CLAIMANT_KIND = {
    "R": "record",
    "C": "component",
    "X": "reference",
    "F": "fact",
    "A": "component",
    "Q": "fact_qualifier",
    "P": "prose_binding",
}


def _add_fact(owner: tuple[str, str], fact: object) -> None:
    """Hold each distinct fact once, however many spans state it."""
    key = fact_key(fact)
    if all(fact_key(f) != key for f in comp_facts[owner]):
        comp_facts[owner].append(fact)


ORIGIN = "issue-5d-hazards-1-schema5-REGEN-generator.py"
leaf_content: dict[str, str] = {}

for label, leafspecs in SPEC.items():
    entry_id = ENTRY_BY_LABEL[label]
    rkey = RECORD_KEY[label]
    lvs = by_container[entry_id]
    assert len(lvs) == len(
        leafspecs
    ), f"{label}: {len(lvs)} leaves vs {len(leafspecs)} specs"

    for lf, segs in zip(lvs, leafspecs, strict=True):
        content, lid = lf.content, lf.leaf_id
        leaf_content[lid] = content
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
                ProposedSpan(span=span, origin=ORIGIN, rationale=RATIONALE[kind])
            )
            if kind in ("F", "Q"):
                claimant = f"{rkey}/{arg[0]}/{fact_key(arg[1])}"
            elif kind in ("C", "A"):
                claimant = f"{rkey}/{arg}"
            elif kind == "P":
                claimant = f"{rkey}/{arg[0]} ({arg[1]})"
            elif kind == "X":
                claimant = f"{rkey} -> {arg[1]}"
            else:
                claimant = rkey
            audit.append(
                {
                    "record": rkey,
                    "leaf": lid,
                    "span_id": sid,
                    "range": [start, end],
                    "text": content[start:end],
                    "disposition": disp.value,
                    "kind": kind,
                    "claimant_kind": CLAIMANT_KIND[kind],
                    "claimant": claimant,
                    "role": (
                        "primary"
                        if disp is SemanticDisposition.SUBSTANTIVE
                        else "contextual"
                    ),
                    "rationale": RATIONALE[kind],
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
                assert irreducibility_reason_for(reason) is not None, reason
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

# --- Source canaries: derived, then compared. A mismatch is stop-and-explain -
CANARIES = {
    "records": (len(records), 6),
    "represented_leaves": (len(touched), 43),
    "policy_exclusions": (len(POLICY_EXCLUDED), 0),
}
CANARY_MISMATCH = {k: v for k, v in CANARIES.items() if v[0] != v[1]}
assert not CANARY_MISMATCH, (
    "the bound source no longer yields the recorded boundary; stop and explain "
    f"rather than adjusting the batch: {CANARY_MISMATCH}"
)

# --- The classification partition, reconstructed rather than trusted --------
# `validate_partition` reports gaps and overlaps. This proves the stronger
# statement a reviewer actually needs: concatenating each leaf's spans in order
# reproduces the leaf byte for byte, so nothing was dropped and nothing double
# counted.
PARTITIONS: dict[str, list[dict]] = {}
for lid in touched:
    ordered = sorted((s for s in spans if s.leaf_id == lid), key=lambda s: s.char_start)
    rebuilt = "".join(leaf_content[lid][s.char_start : s.char_end] for s in ordered)
    assert rebuilt == leaf_content[lid], f"{lid}: partition does not reproduce the leaf"
    prev = 0
    for s in ordered:
        assert s.char_start == prev, f"{lid}: gap or overlap at {s.char_start}"
        prev = s.char_end
    assert prev == CORPUS.leaf_lengths[lid], f"{lid}: partition stops short"
    PARTITIONS[lid] = [
        {
            "range": [s.char_start, s.char_end],
            "text": leaf_content[lid][s.char_start : s.char_end],
            "disposition": s.disposition.value,
        }
        for s in ordered
    ]

# --- The Suffocation trigger boundary, derived then asserted ----------------
_suf_leaf = next(
    lid
    for lid in touched
    if "runs out of breath" in leaf_content[lid] and "choking" in leaf_content[lid]
)
_trigger_text = " When a creature runs out of breath or is choking,"
_trigger_start = leaf_content[_suf_leaf].find(_trigger_text)
assert _trigger_start >= 0, "the Suffocation trigger wording moved in the bound source"
_trigger_range = [_trigger_start, _trigger_start + len(_trigger_text)]
assert _trigger_range == [147, 197], (
    "the bound Suffocation leaf moved: the whole trigger is at "
    f"{_trigger_range}, not the [147,197) the H-16 finding recorded"
)
_trigger_span = derive_span_id(_suf_leaf, *_trigger_range)
H16_TRIGGER = {
    "leaf": _suf_leaf,
    "range": _trigger_range,
    "text": _trigger_text,
    "span_id": _trigger_span,
    "carried_as": "one prose binding over the whole disjunction, uncut",
    "derivation": (
        "found in the bound leaf at run time, then asserted equal to [147,197)"
    ),
}
assert any(
    b.span_id == _trigger_span
    and (b.record_key, b.component_key) == (SUF, "suffocation_accrual")
    for b in prose_bindings
), "the whole trigger is not the accrual component's prose binding"


# --- Merged verification, exactly the shape acceptance would validate -------
#
# `validate_representation` is only ever called on the post-merge candidate
# (`projection.build_candidate_findings`), never on a proposal's draft in
# isolation. Two of this batch's references - Dehydration's and Malnutrition's
# `"Exhaustion."` - resolve into ACCEPTED conditions-1 authority, which is
# supplied by the `prior=` merge inside `accept_proposal`. Reproducing that
# merge here (without accepting anything) is what proves those two obligations
# are cross-batch resolutions rather than residue.
#
# The accepted artifact is READ ONLY. Nothing here writes it, and the lift is
# verified rather than applied. Its path is resolved at the top of this file,
# beneath the derived repository root.
def _accepted_identifiers() -> tuple[str, str, str]:
    """The accepted artifact's raw, canonical, and Git identities.

    The canonical digest normalizes CRLF to LF, which is what
    ``.gitattributes`` declares this file is stored as; the blob id is Git's own
    content identity, computed from those same normalized bytes rather than
    read out of ``.git``, so this holds in an exported tree with no repository
    at all.
    """
    raw = ACCEPTED_PATH.read_bytes()
    canonical = raw.replace(b"\r\n", b"\n")
    blob = hashlib.sha1(  # noqa: S324 - Git's object id, not a security digest
        b"blob " + str(len(canonical)).encode() + b"\x00" + canonical
    ).hexdigest()
    return (
        hashlib.sha256(raw).hexdigest(),
        hashlib.sha256(canonical).hexdigest(),
        blob,
    )


_accepted_raw_before, _accepted_before, _accepted_blob_before = _accepted_identifiers()
assert _accepted_before == ACCEPTED_CONTENT_SHA256, _accepted_before
assert _accepted_blob_before == ACCEPTED_BLOB_ID, _accepted_blob_before
PRIOR = load_accepted_inputs(ACCEPTED_PATH)
STEPS = lift_path((PRIOR.oracle.schema_version, PRIOR.oracle.schema_hash), SCHEMA)
LIFT_RECORDS = verify_lift_path(STEPS, PRIOR.oracle.representation)

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

# --- The unresolved reference set, enumerated exactly -----------------------
# Standalone, this batch cites one record it does not define. The claim is set
# equality against that exact pair of citations, not "only exhaustion appears".
UNRESOLVED_EXPECTED = {
    (DEH, "condition.exhaustion"),
    (MAL, "condition.exhaustion"),
}
_cross_batch = {
    (r.from_record_key, r.target_record_key)
    for r in references
    if r.target_record_key not in {rec.semantic_key for rec in records}
}
assert _cross_batch == UNRESOLVED_EXPECTED, _cross_batch
_prior_records = {r.semantic_key for r in PRIOR.oracle.representation.records}
assert all(t in _prior_records for _, t in _cross_batch), _cross_batch
UNRESOLVED = {
    "standalone_unresolved_targets": sorted(
        f"{f} -> {t}" for f, t in sorted(_cross_batch)
    ),
    "standalone_findings": standalone,
    "resolved_beside_conditions_1": merged_findings == [],
    "target_present_in_accepted_authority": sorted(
        t for _, t in _cross_batch if t in _prior_records
    ),
    "note": (
        "Standalone findings are exactly the two cross-batch reference targets. "
        "The merged column is the shape acceptance validates and reports nothing."
    ),
}
assert UNRESOLVED["resolved_beside_conditions_1"], merged_findings

# --- Disjointness and zero movement, over all six collections ---------------
SIX = (
    "records",
    "components",
    "prose_bindings",
    "relationships",
    "references",
    "provenance",
)


def _identity(collection: str, element: object) -> object:
    if collection == "records":
        return element.semantic_key
    if collection == "components":
        return (element.record_key, element.semantic_key)
    if collection == "prose_bindings":
        return prose_binding_target_key(element)
    if collection == "references":
        return reference_target_key(element)
    if collection == "relationships":
        return (
            element.from_record_key,
            element.to_record_key,
            element.kind.value,
        )
    return (
        element.target_kind.value,
        element.target_key,
        element.span_id,
        element.role.value,
    )


OVERLAP = {}
ZERO_MOVEMENT = {}
for _coll in SIX:
    _prior = getattr(PRIOR.oracle.representation, _coll)
    _new = getattr(DRAFT, _coll)
    _merged = getattr(MERGED, _coll)
    OVERLAP[_coll] = sorted(
        str(k)
        for k in (
            {_identity(_coll, e) for e in _prior} & {_identity(_coll, e) for e in _new}
        )
    )
    # Two independent statements, at two levels, and neither implies the other.
    #
    # The object comparison is what the acceptance seam itself sees: the merge
    # keeps prior authority first, so a prior element that moved would break the
    # prefix.
    #
    # The payload comparison is what a consumer reading the serialized artifact
    # sees, and it is deliberately NOT a prefix: `representation_payload` orders
    # every collection canonically, so the prior elements interleave with the
    # new ones. What must hold is that every prior element still serializes to
    # the exact bytes it serialized to before - which is what would break if
    # schema 5 changed how an accepted element is written - and that the merged
    # collection is exactly the two inputs with nothing dropped or coalesced.
    _prior_payload = representation_payload(PRIOR.oracle.representation)[_coll]
    _new_payload = representation_payload(DRAFT)[_coll]
    _merged_payload = representation_payload(MERGED)[_coll]
    ZERO_MOVEMENT[_coll] = {
        "prior_elements": len(_prior),
        "prefix_is_byte_identical": _merged[: len(_prior)] == _prior,
        "prior_payloads_absent_from_the_merge": [
            str(x) for x in _prior_payload if x not in _merged_payload
        ],
        "payload_element_count": {
            "prior": len(_prior_payload),
            "new": len(_new_payload),
            "merged": len(_merged_payload),
            "sums": len(_merged_payload) == len(_prior_payload) + len(_new_payload),
        },
    }
    assert not OVERLAP[_coll], (_coll, OVERLAP[_coll])
    assert ZERO_MOVEMENT[_coll]["prefix_is_byte_identical"], _coll
    assert not ZERO_MOVEMENT[_coll]["prior_payloads_absent_from_the_merge"], _coll
    assert ZERO_MOVEMENT[_coll]["payload_element_count"]["sums"], _coll

prior_spans = {s.span_id for s in PRIOR.oracle.spans}
prior_leaves = {s.leaf_id for s in PRIOR.oracle.spans}
DISJOINT = {
    "span_overlap": sorted(prior_spans & {s.span_id for s in spans}),
    "leaf_overlap": sorted(prior_leaves & set(touched)),
    "collection_overlap": OVERLAP,
    "prior_spans_retained": len(prior_spans),
    "zero_movement": ZERO_MOVEMENT,
}
assert not DISJOINT["span_overlap"], DISJOINT["span_overlap"]
assert not DISJOINT["leaf_overlap"], DISJOINT["leaf_overlap"]

# --- Schema-5 legality at every authority-bearing seam ----------------------
# Each row is a seam that admits authority in production, exercised here rather
# than reasoned about. A seam that needs a database is named and excluded, not
# silently skipped.
STRUCTURAL = [
    *representation_draft_violations(DRAFT),
    *held_structure_violations(DRAFT),
]
_component_rules: list[str] = []
for _c in components:
    _tag = f"{_c.record_key}/{_c.semantic_key}"
    _component_rules.extend(
        component_damage_composition_violations(_c.facts, _c.options, _tag)
    )
    _component_rules.extend(
        component_roll_outcome_violations(
            _c.facts, _c.options, _c.applies_when, _tag, _c.fact_qualifiers
        )
    )

_WIRE_OUT = representation_payload(DRAFT)
_WIRE_BACK = representation_payload(_representation(json.loads(json.dumps(_WIRE_OUT))))
WIRE_ROUND_TRIP = _WIRE_OUT == _WIRE_BACK
assert WIRE_ROUND_TRIP, "the emitted draft does not survive the wire"

SEAMS = {
    "build-time draft shape (representation_draft_violations)": len(
        representation_draft_violations(DRAFT)
    ),
    "held authority shape (held_structure_violations)": len(
        held_structure_violations(DRAFT)
    ),
    "schema-5 component rules (damage composition + roll outcome)": len(
        _component_rules
    ),
    "declared schema binding (schema_binding_violations)": len(schema_binding),
    "representation gate, standalone (validate_representation)": len(standalone),
    "representation gate, merged with accepted conditions-1": len(merged_findings),
    "committed-loader round trip (representation_payload -> _representation)": (
        0 if WIRE_ROUND_TRIP else 1
    ),
}

#: Seams that answer by raising rather than by reporting findings. Kept out of
#: the table above on purpose: a hardcoded zero beside seven real finding counts
#: reads as an eighth result and proves nothing. Reaching this line at all is
#: what establishes each of these, because every one of them raises on failure.
SEAMS_THAT_RAISE = {
    "acceptance merge (_merge_representation)": {"raised": False},
    "succession (lift_path + verify_lift_path, 3 -> 4 -> 5)": {
        "raised": False,
        "steps": [r.lift_id for r in LIFT_RECORDS],
    },
    "proposal identity (proposal_payload + proposal_identity)": {"raised": False},
}
#: The one seam that is not expected to be silent, and why. A proposal's draft
#: is never validated in isolation in production: `accept_proposal` merges the
#: prior accepted authority in first. Standalone, this batch's two cross-batch
#: citations have no target, and that is the whole of what it reports - asserted
#: as an exact count against the enumerated pair rather than waved past.
_EXPECTED_NONZERO = "representation gate, standalone (validate_representation)"
assert SEAMS[_EXPECTED_NONZERO] == len(_cross_batch) == 2, SEAMS
assert all(v == 0 for k, v in SEAMS.items() if k != _EXPECTED_NONZERO), SEAMS
assert not _component_rules, _component_rules

# --- The three shape refusals this batch must satisfy by construction -------
SHAPE_CLAIMS = {
    "no_component_holds_both_facts_and_options": [
        f"{c.record_key}/{c.semantic_key}" for c in components if c.facts and c.options
    ],
    "no_scaling_fact_anywhere": [
        f"{c.record_key}/{c.semantic_key}"
        for c in components
        for f in (*c.facts, *(of for o in c.options for of in o.facts))
        if type(f) is ScalingFact
    ],
    "no_detached_or_ambiguous_roll_outcome": _component_rules,
    "roll_outcome_scopes": [
        {
            "component": f"{c.record_key}/{c.semantic_key}",
            "rolls_established_in_scope": sum(
                1 for f in c.facts if type(f) is AbilityCheckFact
            ),
            "qualified_fact": q.fact_key,
        }
        for c in components
        for q in c.fact_qualifiers
        if q.applies_when.kind is ApplicabilityKind.ROLL_OUTCOME
    ],
}
assert not SHAPE_CLAIMS["no_component_holds_both_facts_and_options"], SHAPE_CLAIMS
assert not SHAPE_CLAIMS["no_scaling_fact_anywhere"], SHAPE_CLAIMS
assert not SHAPE_CLAIMS["no_detached_or_ambiguous_roll_outcome"], SHAPE_CLAIMS
for _row in SHAPE_CLAIMS["roll_outcome_scopes"]:
    assert _row["rolls_established_in_scope"] == 1, _row
assert SHAPE_CLAIMS["roll_outcome_scopes"], "no roll-outcome scope was exercised"

# --- Falling's timing spans, claimed and accounted (D-3, resolved) ----------
_fall_rows = [a for a in audit if a["record"] == FAL]
FALLING_TIMING = []
for _phrase in ("at the end of the fall", "When the creature lands"):
    _row = next(a for a in _fall_rows if _phrase in a["text"])
    FALLING_TIMING.append(
        {
            "phrase": _phrase,
            "span_range": _row["range"],
            "span_text": _row["text"],
            "disposition": _row["disposition"],
            "claimant_kind": _row["claimant_kind"],
            "claimant": _row["claimant"],
            "accounted_as": (
                "claimed PRIMARY inside the span of the fact it belongs to; "
                "neither omitted nor demoted to supporting authority"
            ),
            "means": (
                "the immediate completion of the fall, not a delayed event: a "
                "normal fall finishes during the turn in which it begins, so "
                "damage and landing resolve at once"
            ),
            "structure_added": "none",
        }
    )
    assert _row["disposition"] == "substantive", _row
    assert _row["role"] == "primary", _row

# Owner Decision 2026-09-02 closed D-3 by ruling that an ordinary fall needs no
# timing structure at all. Checked rather than described: `fall_damage` holds
# the damage and the landing in one component, states no recurrence and no
# duration, binds no prose, and the Prone result is still gated on whether
# falling damage occurred.
_fall = next(
    c for c in components if (c.record_key, c.semantic_key) == (FAL, "fall_damage")
)
_prone_qualifier = next(
    (
        q.applies_when
        for q in _fall.fact_qualifiers
        if q.fact_key == fact_key(PRONE_APPLIES)
    ),
    None,
)
D3_RESOLUTION = {
    "id": "D-3",
    "status": "resolved - Owner Decision 2026-09-02",
    "where": "hazard.falling/fall_damage",
    "question_as_disclosed": (
        "'at the end of the fall' and 'When the creature lands' state when a "
        "one-shot effect occurs, and no declared element carried a moment. The "
        "open question was whether that needed a new timing structure."
    ),
    "ruling": (
        "A normal fall finishes during the turn in which it begins. Resolve its "
        "damage and landing immediately. Only delay completion when a specific "
        "rule provides a falling rate or duration."
    ),
    "grounds": (
        "The SRD's general Falling rule gives no speed, no distance per round "
        "and no duration. Where the SRD intends a slower descent it says so "
        "explicitly - Ring of Feather Falling prints 60 feet per round - so no "
        "general fall-duration calculation and no real-world physics apply."
    ),
    "what_the_phrases_mean": (
        "the immediate completion of the fall, not a delayed event requiring a "
        "new timing structure"
    ),
    "consequence_for_this_batch": (
        "None to the proposed mechanical authority: this ruling changes review "
        "documentation, not the proposal. Both phrases stay SUBSTANTIVE with "
        "their exact source accounting; fall_damage stays one component holding "
        "the falling damage and the landing consequence, with the Prone result "
        "dependent on whether falling damage occurred."
    ),
    "checked": {
        "fall_damage_holds_damage_and_landing": (
            any(type(f) is DamageFact for f in _fall.facts)
            and any(type(f) is ConditionEffectFact for f in _fall.facts)
        ),
        "components_for_the_fall": 1,
        "recurs": _fall.recurs,
        "applies_when": _fall.applies_when,
        "prose_bindings": sum(
            1
            for b in prose_bindings
            if (b.record_key, b.component_key) == (FAL, "fall_damage")
        ),
        "prone_gated_on_falling_damage": (
            _prone_qualifier is not None
            and _prone_qualifier.kind is ApplicabilityKind.DAMAGE_OUTCOME
        ),
        "structure_added_for_ordinary_falls": "none",
    },
    "evidence": FALLING_TIMING,
}
assert D3_RESOLUTION["checked"]["fall_damage_holds_damage_and_landing"], D3_RESOLUTION
assert _fall.recurs is None and _fall.applies_when is None, D3_RESOLUTION
assert D3_RESOLUTION["checked"]["prose_bindings"] == 0, D3_RESOLUTION
assert D3_RESOLUTION["checked"]["prone_gated_on_falling_damage"], D3_RESOLUTION

# --- D-4, Burning's required physical performance: resolved ----------------
# Not an open question and never was: the governing review instructions decided
# the shape, and this checks the proposal is that shape rather than asserting it.
_ext = next(
    c for c in components if (c.record_key, c.semantic_key) == (BUR, "self_extinguish")
)
_ext_bindings = [
    b
    for b in prose_bindings
    if (b.record_key, b.component_key) == (BUR, "self_extinguish")
]
_rolling_row = next(
    a
    for a in audit
    if a["record"] == BUR and a["text"] == " and rolling on the ground."
)
D4_RESOLUTION = {
    "id": "D-4",
    "status": "resolved - correctly represented",
    "where": "hazard.burning/self_extinguish",
    "question_as_disclosed": (
        "whether 'and rolling on the ground' - half of a compound required "
        "performance whose other half is typed - was honestly bound as "
        "governing prose, or needed a typed family."
    ),
    "resolution": (
        "Correctly represented, and settled by the governing review "
        "instructions rather than left open: self_extinguish is one MIXED "
        "component, 'and rolling on the ground' is substantive governing rule "
        "text, and the extinguishing consequence is stated once. No schema "
        "change and no Owner decision is outstanding."
    ),
    "checked": {
        "one_mixed_component": _ext.handling is ComponentHandling.MIXED,
        "typed_facts": sorted(type(f).__name__ for f in _ext.facts),
        "prose_bindings": len(_ext_bindings),
        "bound_span": {
            "range": _rolling_row["range"],
            "text": _rolling_row["text"],
            "disposition": _rolling_row["disposition"],
            "claimant": _rolling_row["claimant"],
        },
        "consequence_stated_once": sum(
            1 for f in _ext.facts if type(f) is EffectTerminationFact
        ),
        "consequence_restated_in_the_bound_span": (
            "extinguish" in _rolling_row["text"] or "goes out" in _rolling_row["text"]
        ),
        "reason_code": _ext.irreducibility_reason_code,
    },
}
assert D4_RESOLUTION["checked"]["one_mixed_component"], D4_RESOLUTION
assert D4_RESOLUTION["checked"]["prose_bindings"] == 1, D4_RESOLUTION
assert _ext_bindings[0].span_id == _rolling_row["span_id"], D4_RESOLUTION
assert _rolling_row["disposition"] == "substantive", D4_RESOLUTION
assert D4_RESOLUTION["checked"]["consequence_stated_once"] == 1, D4_RESOLUTION
assert not D4_RESOLUTION["checked"][
    "consequence_restated_in_the_bound_span"
], D4_RESOLUTION
assert D4_RESOLUTION["checked"]["typed_facts"] == [
    "ActionEconomyFact",
    "ConditionEffectFact",
    "EffectTerminationFact",
], D4_RESOLUTION

# --- Z-1, the sustained zero-food rule: resolved ----------------------------
_auto = next(
    c
    for c in components
    if (c.record_key, c.semantic_key) == (MAL, "starvation_automatic")
)
_auto_band = _auto.applies_when.band
Z1_RESOLUTION = {
    "id": "Z-1",
    "status": "resolved - correctly represented",
    "where": "hazard.malnutrition/starvation_automatic",
    "question_as_disclosed": (
        "whether the point band sustained for five days, composed with a daily "
        "recurrence, is a faithful reading of 'eats nothing for 5 days ... as "
        "well as an additional level at the end of each subsequent day without "
        "food'."
    ),
    "required_reading": [
        "'eats nothing for 5 days' means continuous zero consumption for at "
        "least five days",
        "Exhaustion is gained at the end of the fifth foodless day",
        "additional Exhaustion is gained at the end of each following foodless day",
        "the recurrence stays conditional on continued zero consumption",
        "eating any food ends that zero-consumption applicability",
    ],
    "resolution": (
        "Correctly represented. The band is the state and the recurrence is the "
        "cadence: a component's applies_when says when the component applies at "
        "all, so the daily gain repeats only while zero consumption holds and "
        "stops the day eating resumes. No stop condition, elapsed clock, or "
        "second predicate is needed, and none is added."
    ),
    "checked": {
        "band_is_the_zero_point": (
            _auto_band.lower == ZERO
            and _auto_band.upper == ZERO
            and _auto_band.lower_inclusive
            and _auto_band.upper_inclusive
        ),
        "sustained_at_least": _auto_band.sustained_at_least,
        "sustained_unit": _auto_band.sustained_unit.value,
        "quantity": _auto_band.quantity.value,
        "recurrence": _auto.recurs.boundary.value,
        "facts": sorted(type(f).__name__ for f in _auto.facts),
        "elapsed_duration_applicability_anywhere": len(
            _sites_elapsed := [
                f"{c.record_key}/{c.semantic_key}"
                for c in components
                if c.applies_when is not None
                and c.applies_when.kind is ApplicabilityKind.ELAPSED_DURATION
            ]
        ),
        "distinct_from_the_partial_band": (
            STARVATION_ZERO_BAND != STARVATION_PARTIAL_BAND
        ),
    },
}
assert Z1_RESOLUTION["checked"]["band_is_the_zero_point"], Z1_RESOLUTION
assert Z1_RESOLUTION["checked"]["sustained_at_least"] == 5, Z1_RESOLUTION
assert Z1_RESOLUTION["checked"]["sustained_unit"] == "day", Z1_RESOLUTION
assert Z1_RESOLUTION["checked"]["recurrence"] == "end_of_day", Z1_RESOLUTION
assert Z1_RESOLUTION["checked"]["facts"] == ["ConditionLevelFact"], Z1_RESOLUTION
assert not _sites_elapsed, _sites_elapsed
assert Z1_RESOLUTION["checked"]["distinct_from_the_partial_band"], Z1_RESOLUTION

# ---------------------------------------------------------------------------
# Obligation closure, checked against the emitted draft
# ---------------------------------------------------------------------------

_comp = {(c.record_key, c.semantic_key): c for c in components}


def _facts(rkey: str, ckey: str) -> tuple:
    return _comp[(rkey, ckey)].facts


def _has(rkey: str, ckey: str, fact: object) -> bool:
    return any(fact_key(f) == fact_key(fact) for f in _facts(rkey, ckey))


def _band_of(rkey: str, ckey: str) -> ConsumptionBand | None:
    aw = _comp[(rkey, ckey)].applies_when
    return None if aw is None else aw.band


def _recurs(rkey: str, ckey: str, boundary: RecurrenceBoundary, whose=None) -> bool:
    r = _comp[(rkey, ckey)].recurs
    return r is not None and r.boundary is boundary and r.whose is whose


def _qualifier(rkey: str, ckey: str, fact: object) -> Applicability | None:
    for q in _comp[(rkey, ckey)].fact_qualifiers:
        if q.fact_key == fact_key(fact):
            return q.applies_when
    return None


def _bound(rkey: str, ckey: str) -> int:
    return sum(
        1 for b in prose_bindings if (b.record_key, b.component_key) == (rkey, ckey)
    )


OBLIGATIONS: list[tuple[str, str, bool]] = [
    (
        "O-1",
        "glossary.hazard: five record-owned references, one per hazard record",
        sorted(
            r.target_record_key
            for r in references
            if r.from_record_key == HAZ
            and r.from_component_key == RECORD_OWNED_REFERENCE
        )
        == sorted([BUR, DEH, FAL, MAL, SUF]),
    ),
    (
        "O-2",
        "burning_damage: DamageFact(FIRE, 1d4), no interval and no ceiling",
        _has(BUR, "burning_damage", BURN_DAMAGE),
    ),
    (
        "O-3",
        "burning_damage.recurs Recurrence(START_OF_TURN, subject)",
        _recurs(
            BUR, "burning_damage", RecurrenceBoundary.START_OF_TURN, RollActor.SUBJECT
        ),
    ),
    (
        "O-4",
        "self_extinguish: ActionEconomyFact(ACTION) - the stated cost",
        _has(BUR, "self_extinguish", ACTION_COST),
    ),
    (
        "O-5",
        "self_extinguish: EffectTerminationFact - the fire goes out, stated once",
        _has(BUR, "self_extinguish", TERMINATION),
    ),
    (
        "O-6",
        "self_extinguish: ConditionEffectFact(PRONE, APPLIES)",
        _has(BUR, "self_extinguish", PRONE_APPLIES),
    ),
    (
        "O-7",
        "self_extinguish is one MIXED component with exactly one prose binding, "
        "over ' and rolling on the ground.' and nothing else (D-4)",
        _comp[(BUR, "self_extinguish")].handling is ComponentHandling.MIXED
        and _bound(BUR, "self_extinguish") == 1
        and next(
            b
            for b in prose_bindings
            if (b.record_key, b.component_key) == (BUR, "self_extinguish")
        ).span_id
        == next(
            a["span_id"]
            for a in audit
            if a["record"] == BUR and a["text"] == " and rolling on the ground."
        ),
    ),
    (
        "O-8",
        "ambient_extinguish: EffectTerminationFact + a prose binding over its trigger",
        _has(BUR, "ambient_extinguish", TERMINATION)
        and _bound(BUR, "ambient_extinguish") == 1,
    ),
    (
        "O-9",
        "water_requirement: SizeKeyedQuantityFact(WATER, DAY, six printed rows)",
        _has(DEH, "water_requirement", WATER_REQ) and len(WATER_REQ.values) == 6,
    ),
    (
        "O-10",
        "dehydration_exhaustion.applies_when band(WATER, upper 1/2 exclusive, "
        "no lower bound) - 'drinks less than half'",
        _band_of(DEH, "dehydration_exhaustion") == DEHYDRATION_BAND
        and DEHYDRATION_BAND.lower is None
        and DEHYDRATION_BAND.upper == HALF
        and not DEHYDRATION_BAND.upper_inclusive,
    ),
    (
        "O-11",
        "dehydration_exhaustion: ConditionLevelFact(EXHAUSTION, GAIN, 1)",
        _has(DEH, "dehydration_exhaustion", GAIN_1),
    ),
    (
        "O-12",
        "dehydration_exhaustion.recurs Recurrence(END_OF_DAY)",
        _recurs(DEH, "dehydration_exhaustion", RecurrenceBoundary.END_OF_DAY),
    ),
    (
        "O-13",
        "dehydration_recovery: cause-scoped removal restriction until "
        "band(WATER, lower 1 inclusive, unbounded above)",
        _has(DEH, "dehydration_recovery", WATER_REMOVAL)
        and WATER_REMOVAL.cause_scoped
        and WATER_REMOVAL.until.band == WATER_FULL_BAND,
    ),
    (
        "O-14",
        "hazard.dehydration cites condition.exhaustion, resolved beside conditions-1",
        (DEH, "condition.exhaustion") in _cross_batch,
    ),
    (
        "O-15",
        "fall_damage: one DamageFact - 1d6 Bludgeoning per 10 feet fallen, "
        "maximum_dice 20, and NO ScalingFact anywhere in the batch",
        _has(FAL, "fall_damage", FALL_DAMAGE)
        and FALL_DAMAGE.per
        == DamageInterval(
            basis=ScalingBasis.DISTANCE_FALLEN, amount=10, unit=DistanceUnit.FOOT
        )
        and FALL_DAMAGE.maximum_dice == 20
        and not SHAPE_CLAIMS["no_scaling_fact_anywhere"],
    ),
    (
        "O-16",
        "fall_damage holds the landing fact too, with the no-damage exception "
        "qualified onto that fact alone and no component-wide applicability",
        _has(FAL, "fall_damage", PRONE_APPLIES)
        and _comp[(FAL, "fall_damage")].applies_when is None
        and _qualifier(FAL, "fall_damage", PRONE_APPLIES)
        == Applicability(
            kind=ApplicabilityKind.DAMAGE_OUTCOME,
            negated=True,
            damage_outcome=DamageOutcome.NO_DAMAGE,
        ),
    ),
    (
        "O-17",
        "surface_check: ActionEconomyFact(REACTION)",
        _has(FAL, "surface_check", REACTION_COST),
    ),
    (
        "O-18",
        "surface_check: AbilityCheckFact context=ABILITY_CHECK, DC 15, "
        "Strength (Athletics) with Dexterity (Acrobatics) as a closed alternative, "
        "and every alternative RollSpec is itself an ability check",
        _has(FAL, "surface_check", SURFACE_CHECK)
        and SURFACE_CHECK.context is RollContext.ABILITY_CHECK
        and all(
            r.context is RollContext.ABILITY_CHECK for r in SURFACE_CHECK.alternatives
        )
        and len(SURFACE_CHECK.alternatives) == 2,
    ),
    (
        "O-19",
        "surface_check: MIXED, one prose binding over the water/liquid trigger",
        _comp[(FAL, "surface_check")].handling is ComponentHandling.MIXED
        and _bound(FAL, "surface_check") == 1,
    ),
    (
        "O-20",
        "surface_check: the halving lives with the check it answers to, "
        "qualified ROLL_OUTCOME(SUCCESS) onto the halving fact alone, "
        "rounding left unset (R-3 is separate authority)",
        _has(FAL, "surface_check", HALVING)
        and _qualifier(FAL, "surface_check", HALVING)
        == Applicability(
            kind=ApplicabilityKind.ROLL_OUTCOME, outcome=AutomaticOutcome.SUCCESS
        )
        and HALVING.rounding is None
        and _comp[(FAL, "surface_check")].applies_when is None,
    ),
    (
        "O-21",
        "food_requirement: SizeKeyedQuantityFact(FOOD, DAY, six printed rows)",
        _has(MAL, "food_requirement", FOOD_REQ) and len(FOOD_REQ.values) == 6,
    ),
    (
        "O-22",
        "starvation_save.applies_when band(FOOD, 0 exclusive .. 1/2 exclusive) - "
        "'eats BUT consumes less than half', distinct from the zero band",
        _band_of(MAL, "starvation_save") == STARVATION_PARTIAL_BAND
        and STARVATION_PARTIAL_BAND.lower == ZERO
        and not STARVATION_PARTIAL_BAND.lower_inclusive
        and STARVATION_PARTIAL_BAND.upper == HALF
        and not STARVATION_PARTIAL_BAND.upper_inclusive
        and STARVATION_PARTIAL_BAND != STARVATION_ZERO_BAND
        and STARVATION_PARTIAL_BAND != DEHYDRATION_BAND,
    ),
    (
        "O-23",
        "starvation_save: AbilityCheckFact(CON, FIXED 10) with "
        "context=SAVING_THROW, no skill, no alternatives",
        _has(MAL, "starvation_save", CON_SAVE)
        and CON_SAVE.context is RollContext.SAVING_THROW
        and CON_SAVE.skill is None
        and CON_SAVE.alternatives == ()
        and fact_key(CON_SAVE)
        != fact_key(
            AbilityCheckFact(
                ability=AbilityScore.CONSTITUTION,
                dc_kind=DcKind.FIXED,
                context=RollContext.ABILITY_CHECK,
                dc_value=10,
            )
        ),
    ),
    (
        "O-24",
        "starvation_save: the Exhaustion gain is qualified ROLL_OUTCOME(FAILURE) "
        "on the very save this component calls for",
        _qualifier(MAL, "starvation_save", GAIN_1)
        == Applicability(
            kind=ApplicabilityKind.ROLL_OUTCOME, outcome=AutomaticOutcome.FAILURE
        )
        and sum(
            1 for f in _facts(MAL, "starvation_save") if type(f) is AbilityCheckFact
        )
        == 1,
    ),
    (
        "O-25",
        "starvation_save.recurs Recurrence(END_OF_DAY)",
        _recurs(MAL, "starvation_save", RecurrenceBoundary.END_OF_DAY),
    ),
    (
        "O-26",
        "starvation_automatic.applies_when band(FOOD, 0..0 inclusive) sustained "
        "at least 5 days - 'eats nothing for 5 days', not an elapsed clock",
        _band_of(MAL, "starvation_automatic") == STARVATION_ZERO_BAND
        and STARVATION_ZERO_BAND.lower == ZERO
        and STARVATION_ZERO_BAND.upper == ZERO
        and STARVATION_ZERO_BAND.lower_inclusive
        and STARVATION_ZERO_BAND.upper_inclusive
        and STARVATION_ZERO_BAND.sustained_at_least == 5
        and STARVATION_ZERO_BAND.sustained_unit is TimeUnit.DAY
        and _comp[(MAL, "starvation_automatic")].applies_when.kind is CONS,
    ),
    (
        "O-27",
        "starvation_automatic: ConditionLevelFact(EXHAUSTION, GAIN, 1), one fact "
        "for the fifth day and every subsequent day without food",
        _has(MAL, "starvation_automatic", GAIN_1)
        and len(_facts(MAL, "starvation_automatic")) == 1,
    ),
    (
        "O-28",
        "starvation_automatic.recurs Recurrence(END_OF_DAY) - the cadence that, "
        "composed with the band, stops when eating resumes",
        _recurs(MAL, "starvation_automatic", RecurrenceBoundary.END_OF_DAY),
    ),
    (
        "O-29",
        "malnutrition_recovery: cause-scoped removal restriction until "
        "band(FOOD, lower 1 inclusive), preserved as this record's own rule",
        _has(MAL, "malnutrition_recovery", FOOD_REMOVAL)
        and FOOD_REMOVAL.cause_scoped
        and FOOD_REMOVAL.until.band == FOOD_FULL_BAND
        and fact_key(FOOD_REMOVAL) != fact_key(WATER_REMOVAL),
    ),
    (
        "O-30",
        "hazard.malnutrition cites condition.exhaustion, resolved beside conditions-1",
        (MAL, "condition.exhaustion") in _cross_batch,
    ),
    (
        "O-31",
        "breath_duration: DerivedQuantityFact(1 + CON modifier minutes, floor 30 s)",
        _has(SUF, "breath_duration", BREATH),
    ),
    (
        "O-32",
        "suffocation_accrual: one MIXED component, one prose binding carrying the "
        "WHOLE disjunctive trigger [147,197) uncut (H-16 Shape B)",
        _comp[(SUF, "suffocation_accrual")].handling is ComponentHandling.MIXED
        and _bound(SUF, "suffocation_accrual") == 1,
    ),
    (
        "O-33",
        "suffocation_accrual: the Exhaustion gain stated ONCE, and it is the "
        "record's only accrual fact",
        _facts(SUF, "suffocation_accrual") == (GAIN_1,)
        and sum(
            1
            for c in components
            if c.record_key == SUF
            for f in c.facts
            if type(f) is ConditionLevelFact and f.direction is LevelDirection.GAIN
        )
        == 1,
    ),
    (
        "O-34",
        "suffocation_accrual.recurs Recurrence(END_OF_TURN, subject), once at "
        "component scope",
        _recurs(
            SUF,
            "suffocation_accrual",
            RecurrenceBoundary.END_OF_TURN,
            RollActor.SUBJECT,
        ),
    ),
    (
        "O-35",
        "suffocation_recovery: MIXED, one prose binding over the recovery trigger",
        _comp[(SUF, "suffocation_recovery")].handling is ComponentHandling.MIXED
        and _bound(SUF, "suffocation_recovery") == 1,
    ),
    (
        "O-36",
        "suffocation_recovery: ConditionLevelFact(REMOVE, all levels, cause-scoped)",
        _has(SUF, "suffocation_recovery", SUFF_REMOVAL) and SUFF_REMOVAL.cause_scoped,
    ),
]
OBLIGATION_CLOSURE = {
    oid: {"claim": text, "closed": ok} for oid, text, ok in OBLIGATIONS
}
_open = [oid for oid, _t, ok in OBLIGATIONS if not ok]
assert not _open, f"open obligations: {_open}"

# --- Sibling components holding an equivalent fact --------------------------
# The defect family PR #159's merge-blocking finding came from, stated in the
# artifact rather than left as a code comment.
# `_validate_duplicated_fact_authority` requires all three of different
# components, an equivalent fact key, AND a shared substantive span.
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
_accrual = _comp[(SUF, "suffocation_accrual")]
H16 = {
    "handling": _accrual.handling.value,
    "irreducibility_reason_code": _accrual.irreducibility_reason_code,
    "typed_facts": len(_accrual.facts),
    "components_in_record": sum(1 for c in components if c.record_key == SUF),
    "trigger": H16_TRIGGER,
    "recurrence_stated_once_at_component_scope": _accrual.recurs is not None,
    "boolean_predicates_invented": 0,
    "wrapper_facts_invented": 0,
    "duplicated_sibling_authority": 0,
    "trigger_split_into_siblings": 0,
}
assert _accrual.handling is ComponentHandling.MIXED, H16
assert len(_accrual.facts) == 1, H16

R3 = {
    "governing_rule": "Rules Glossary > Rules Definitions > Round Down",
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

# ---------------------------------------------------------------------------
# Schema-5 structures demonstrated, derived from the emitted draft
# ---------------------------------------------------------------------------
_sites: dict[str, list[str]] = defaultdict(list)
for _c in components:
    _at = f"{_c.record_key}/{_c.semantic_key}"
    if _c.recurs is not None:
        _sites[f"recurrence ({_c.recurs.boundary.value})"].append(_at)
    if _c.applies_when is not None:
        _sites[f"applicability ({_c.applies_when.kind.value})"].append(_at)
        if _c.applies_when.band is not None:
            _b = _c.applies_when.band
            _sites[
                "ConsumptionBand "
                f"({_b.quantity.value}: "
                f"{'-inf' if _b.lower is None else f'{_b.lower.numerator}/{_b.lower.denominator}'}"
                f"{'<=' if _b.lower_inclusive else '<'}x"
                f"{'<=' if _b.upper_inclusive else '<'}"
                f"{'+inf' if _b.upper is None else f'{_b.upper.numerator}/{_b.upper.denominator}'}"
                + (
                    f", sustained>={_b.sustained_at_least} {_b.sustained_unit.value}"
                    if _b.sustained_at_least
                    else ""
                )
                + ")"
            ].append(_at)
    for _q in _c.fact_qualifiers:
        _sites[f"fact qualifier ({_q.applies_when.kind.value})"].append(_at)
    for _f in _c.facts:
        _fam = _f.FAMILY.value
        _sites[f"fact family ({_fam})"].append(_at)
        if _fam == "damage" and _f.maximum_dice is not None:
            _sites["DamageFact.maximum_dice (the 20d6 cap)"].append(_at)
        if _fam == "damage" and _f.per is not None:
            _sites[
                f"DamageFact.per = DamageInterval({_f.per.basis.value}, "
                f"{_f.per.amount} {_f.per.unit.value})"
            ].append(_at)
        if _fam == "ability_check":
            _sites[f"AbilityCheckFact.context ({_f.context.value})"].append(_at)
            if _f.alternatives:
                _sites["AbilityCheckFact.alternatives + Skill axis"].append(_at)
        if _fam == "condition_level" and _f.cause_scoped:
            _sites["ConditionLevelFact.cause_scoped"].append(_at)
        if _fam == "condition_removal_restriction":
            _sites["ConditionRemovalRestrictionFact.cause_scoped"].append(_at)
            if _f.until is not None and _f.until.band is not None:
                _sites["ConditionRemovalRestrictionFact.until carries a band"].append(
                    _at
                )
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

DEMONSTRATED = {
    "the roll a DC states (schema 5)": [
        "AbilityCheckFact.context (ability_check)",
        "AbilityCheckFact.context (saving_throw)",
    ],
    "consumption bands, all four stated forms (schema 5)": [
        "applicability (consumption_threshold)",
        "ConsumptionBand (water: -inf<x<1/2)",
        "ConsumptionBand (food: 0/1<x<1/2)",
        "ConsumptionBand (food: 0/1<=x<=0/1, sustained>=5 day)",
        "ConditionRemovalRestrictionFact.until carries a band",
    ],
    "one damage composition (schema 5)": [
        "DamageFact.per = DamageInterval(distance_fallen, 10 foot)",
        "DamageFact.maximum_dice (the 20d6 cap)",
    ],
    "a roll outcome answering to a roll in its own scope (schema 5)": [
        "fact qualifier (roll_outcome)",
    ],
    "recurrence and termination": [
        "recurrence (start_of_turn)",
        "recurrence (end_of_turn)",
        "recurrence (end_of_day)",
        "fact family (effect_termination)",
    ],
    "size-keyed requirements": ["fact family (size_keyed_quantity)"],
    "cause-scoped Exhaustion and removal restrictions": [
        "ConditionLevelFact.cause_scoped",
        "ConditionRemovalRestrictionFact.cause_scoped",
        "fact family (condition_removal_restriction)",
    ],
    "damage-outcome applicability, scoped to one fact": [
        "fact qualifier (damage_outcome)",
    ],
    "alternative Strength (Athletics) / Dexterity (Acrobatics) checks": [
        "AbilityCheckFact.alternatives + Skill axis"
    ],
    "damage halving": ["fact family (damage_modification)"],
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
# No ELAPSED_DURATION survives: schema 4 used it for "eats nothing for 5 days".
assert not _sites["applicability (elapsed_duration)"], "an elapsed clock came back"

# ---------------------------------------------------------------------------
# Proposal, identity, counts
# ---------------------------------------------------------------------------

PROPOSAL = MechanicalProposal(
    binding=BINDING,
    policy_version=SEMANTIC_POLICY_VERSION,
    policy_hash=semantic_policy_hash(),
    schema_version=SCHEMA[0],
    schema_hash=SCHEMA[1],
    proposed_spans=tuple(proposed),
    proposed_representation=DRAFT,
    proposal_origin=(
        f"{ORIGIN} (CRD Issue 5d batch hazards-1, representation schema 5)"
    ),
)
payload = proposal_payload(PROPOSAL)
ident = proposal_identity(PROPOSAL)
assert ident != REJECTED_IDENTITY, "the new proposal is the rejected one"
assert ident == EXPECTED_IDENTITY, (
    "the reviewed proposal was not reproduced: this run mints "
    f"{ident}, not {EXPECTED_IDENTITY}. Stop and explain rather than blessing "
    "a changed proposal."
)

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

COUNTS = {
    "records": len(records),
    "represented_leaves": len(touched),
    "policy_exclusions": len(POLICY_EXCLUDED),
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
    "distinct_fact_keys": len({fact_key(f) for c in components for f in c.facts}),
    "fact_qualifiers": sum(len(c.fact_qualifiers) for c in components),
    "prose_bindings": len(prose_bindings),
    "references": len(references),
    "relationships": 0,
    "provenance_edges": len(provenance),
}
# Every count is derived above; these are the two the emission arithmetic must
# agree with, so a silently dropped claim cannot pass as a smaller number.
assert COUNTS["spans"] == len(audit) == len(proposed), COUNTS
assert COUNTS["provenance_edges"] == len(spans), COUNTS
assert (
    COUNTS["substantive"]
    + COUNTS["supporting_authority"]
    + COUNTS["non_mechanical"]
    + COUNTS["unresolved"]
    == COUNTS["spans"]
), COUNTS

COUNT_DERIVATION = {
    "records": (
        "one per source entry in the boundary: the Hazard umbrella plus the "
        "five [Hazard] entries"
    ),
    "represented_leaves": (
        "distinct leaf ids the spans cover, all of them 5c-represented"
    ),
    "spans": (
        "one per segment of the run-time cut; the segments of each leaf "
        "reconstruct it byte for byte"
    ),
    "substantive": (
        "F + A + Q + P segments: a mechanic, a component-scope claim, a "
        "fact-scope qualifier, or affirmative governing prose"
    ),
    "supporting_authority": (
        "R + C + X segments: framing owned by the record, by a component, or "
        "by a reference"
    ),
    "components": (
        "declared in COMPONENTS and emitted with the facts the clause table "
        "assigned them"
    ),
    "facts": (
        "distinct fact keys per component; a fact stated by several spans is "
        "held once"
    ),
    "provenance_edges": (
        "exactly one claim per span, which is what the ownership check asserts"
    ),
    "movement_from_the_rejected_schema_4_artifact": (
        "A diagnostic comparison made AFTER this run, against the recorded "
        "counts of the rejected proposal - never an input to it. Spans 96 -> 96 "
        "and provenance edges 96 -> 96: the source cut is unchanged, because the "
        "corrections are about what claims each span, not where the source's "
        "clauses fall. Substantive 64 -> 65 and supporting 32 -> 31: exactly one "
        "span moved, ' and rolling on the ground.' from supporting commentary to "
        "affirmative governing prose. Prose bindings 4 -> 5 for that same span. "
        "Components 17 -> 15: `landing` merged into `fall_damage` and "
        "`fall_halving` into `surface_check`, so each rule sits with the fact it "
        "answers to. Facts 22 -> 21: the Falling `ScalingFact` is gone, replaced "
        "by `DamageFact.per` on the fact that already stated the amount - no "
        "other fact was added or dropped. Two further spans changed claimant kind "
        "from a component-scope claim to a fact-scope qualifier (A -> Q): "
        "' unless it avoids taking any damage from the fall.' and ' On a "
        "successful check,'. A reviewer should read the drop in components and "
        "facts as consolidation, not as loss."
    ),
}

AUDIT_DOC = {
    "_": (
        "CRD Issue 5d batch hazards-1, representation schema 5. Proposal and "
        "audit only: nothing accepted, published, activated or retired. Zero "
        "validator findings is necessary and explicitly insufficient - this is "
        "material for semantic review, not a recommendation to accept."
    ),
    "proposal_identity": ident,
    "rejected_predecessor": {
        "identity": REJECTED_IDENTITY,
        "schema": "5d-representation-schema-4",
        "differs": ident != REJECTED_IDENTITY,
        "use": (
            "historical diagnostic evidence only. Its payload was not imported, "
            "edited, translated, restamped, cloned, or read as generator input."
        ),
    },
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
        "canaries": {
            k: {"derived": v[0], "expected": v[1]} for k, v in CANARIES.items()
        },
        "derivation": (
            "the source's own [Hazard] entry class under Rules Definitions plus "
            "the umbrella Hazard glossary rule; the five names are re-checked "
            "against the umbrella's own See-also text"
        ),
    },
    "counts": COUNTS,
    "count_derivation": COUNT_DERIVATION,
    "per_record": {
        r: {
            "leaves": len(d["leaves"]),
            "spans": d["spans"],
            "unresolved": d["unresolved"],
        }
        for r, d in sorted(per_record.items())
    },
    "record_shapes": {
        f"{c.record_key}/{c.semantic_key}": {
            "handling": c.handling.value,
            "irreducibility_reason_code": c.irreducibility_reason_code,
            "facts": [type(f).__name__ for f in c.facts],
            "applies_when": (
                None if c.applies_when is None else c.applies_when.kind.value
            ),
            "recurs": None if c.recurs is None else c.recurs.boundary.value,
            "fact_qualifiers": [q.applies_when.kind.value for q in c.fact_qualifiers],
            "options": len(c.options),
        }
        for c in components
    },
    "validation": {
        "partition": partition,
        "structural": STRUCTURAL,
        "component_rules_schema_5": _component_rules,
        "wire_round_trip": WIRE_ROUND_TRIP,
        "reason_codes": reason_codes,
        "schema_binding": schema_binding,
        "representation_standalone": standalone,
        "representation_merged_with_accepted_conditions_1": merged_findings,
        "seams_reporting_findings": SEAMS,
        "seams_that_answer_by_raising": SEAMS_THAT_RAISE,
        "seams_not_exercised_here": [
            "persistence round trip and override application need a database; "
            "they are covered by the schema-5 test modules on main, not by this "
            "generator, which touches no database by design"
        ],
        "note": (
            "validate_representation is only ever run on the post-merge candidate. "
            "The standalone column exists to show which findings are exactly the "
            "cross-batch reference resolutions the prior= merge supplies."
        ),
    },
    "classification_partitions": PARTITIONS,
    "cross_batch_references": UNRESOLVED,
    "disjointness_from_accepted_conditions_1": DISJOINT,
    "shape_claims": SHAPE_CLAIMS,
    "schema_succession": {
        "path": [
            {
                "lift_id": r.lift_id,
                "from": [r.from_version, r.from_hash],
                "to": [r.to_version, r.to_hash],
                "verified_collections": list(r.verified_collections),
            }
            for r in LIFT_RECORDS
        ],
        "accepted_artifact_content_sha256_before": _accepted_before,
        "accepted_artifact_content_sha256_after": None,  # filled in after the write
        "accepted_artifact_blob_id": _accepted_blob_before,
        "accepted_artifact_unchanged": None,
        "accepted_artifact_identity_note": (
            "Identified by content, not by the bytes one working copy holds. "
            ".gitattributes declares 'text=auto eol=lf', so a fresh checkout "
            "writes this file with LF while a working copy predating the "
            "attribute can hold CRLF. Both are the same committed content and "
            "load to the same authority. The content digest normalizes CRLF to "
            "LF; the blob id is Git's own content identity, derived from those "
            "same normalized bytes. The raw on-disk digest is deliberately not "
            "recorded here - it would make this artifact differ between two "
            "checkouts of one commit - and is printed to stdout instead."
        ),
        "note": (
            "the committed conditions-1 artifact declares schema 3 and reaches "
            "schema 5 across two registered crossings, each proved separately"
        ),
    },
    "resolved_representation_questions": [D3_RESOLUTION, D4_RESOLUTION, Z1_RESOLUTION],
    "disclosed_representation_limits": [],
    "_superseded_disclosure_wording": [
        {
            "id": "D-4",
            "status": "resolved; retained wording from when it was disclosed",
            "where": "hazard.burning/self_extinguish",
            "limit": (
                "'and rolling on the ground' is half of a compound required "
                "performance whose other half - the Prone condition - is typed. "
                "Rolling on the ground has no typed family."
            ),
            "how_it_is_accounted": (
                "Bound as affirmative governing prose under "
                "contextual_applicability: whether the extinguishing applies "
                "depends on whether the creature performed an act the projection "
                "cannot enumerate. It is substantive, not supporting commentary. "
                "The typed consequence (EffectTerminationFact) is stated once "
                "beside it and is not restated inside the binding's span, so the "
                "consequence is not published twice."
            ),
            "reason_code_justification": (
                "Chosen against the catalog's literal wording rather than for "
                "validation: the clause conditions whether the rule takes effect, "
                "which is applicability, and its operand is unenumerable fiction. "
                "subjective_judgment would claim a judgement call the source does "
                "not ask for, and fiction_dependent_consequence would misdescribe "
                "a consequence that is typed."
            ),
        },
    ],
    "schema_5_structures_demonstrated": DEMO_EVIDENCE,
    "d3_resolution": D3_RESOLUTION,
    "d4_resolution": D4_RESOLUTION,
    "z1_resolution": Z1_RESOLUTION,
    "review_disposition": {
        "open_semantic_questions": [],
        "disclosed_representation_limits": [],
        "resolved": ["D-3", "D-4", "Z-1"],
        "statement": (
            "hazards-1 has passed semantic review. Every question this batch "
            "raised is resolved: D-3 by Owner Decision 2026-09-02, D-4 and Z-1 "
            "as correctly represented. Acceptance is a separate Owner step and "
            "is not performed here."
        ),
    },
    "repository_inputs": INPUT_PATHS,
    "obligation_closure": OBLIGATION_CLOSURE,
    "sibling_fact_pairs": SIBLING_PAIRS,
    "ownership_integrity": OWNERSHIP,
    "h16_shape_b": H16,
    "r3_disposition": R3,
    "falling_timing_spans": FALLING_TIMING,
    "spans": audit,
}

# Nothing is left open. Asserted, because "the audit says so" is exactly what
# this run exists to prove: the disclosed-limit and open-question lists are
# empty, all three questions carry a resolved status, and the two identities the
# review was conducted against are reproduced rather than restated.
_disclosed = [d["id"] for d in AUDIT_DOC["disclosed_representation_limits"]]
_resolved = [d["id"] for d in AUDIT_DOC["resolved_representation_questions"]]
assert _disclosed == [], _disclosed
assert _resolved == ["D-3", "D-4", "Z-1"], _resolved
assert AUDIT_DOC["review_disposition"]["open_semantic_questions"] == [], AUDIT_DOC[
    "review_disposition"
]
assert (
    AUDIT_DOC["review_disposition"]["disclosed_representation_limits"] == []
), AUDIT_DOC["review_disposition"]
for _res in AUDIT_DOC["resolved_representation_questions"]:
    assert _res["status"].startswith("resolved"), _res["status"]
assert AUDIT_DOC["proposal_identity"] == EXPECTED_IDENTITY, AUDIT_DOC[
    "proposal_identity"
]
assert (
    AUDIT_DOC["schema_succession"]["accepted_artifact_content_sha256_before"]
    == ACCEPTED_CONTENT_SHA256
), AUDIT_DOC["schema_succession"]
assert (
    AUDIT_DOC["schema_succession"]["accepted_artifact_blob_id"] == ACCEPTED_BLOB_ID
), AUDIT_DOC["schema_succession"]

(OUT / PROPOSAL_FILE).write_text(
    json.dumps(payload, indent=1, sort_keys=True, ensure_ascii=False), encoding="utf-8"
)

# The accepted artifact, read again after this run has written its own output,
# so the audit carries the after value rather than only the before value. It is
# re-read once more below, after the audit itself is written.
_, _accepted_after, _accepted_blob_after = _accepted_identifiers()
assert _accepted_after == _accepted_before, "the committed accepted artifact changed"
assert _accepted_blob_after == _accepted_blob_before, "the accepted blob id moved"
AUDIT_DOC["schema_succession"][
    "accepted_artifact_content_sha256_after"
] = _accepted_after
AUDIT_DOC["schema_succession"]["accepted_artifact_unchanged"] = (
    _accepted_after == _accepted_before == ACCEPTED_CONTENT_SHA256
    and _accepted_blob_after == ACCEPTED_BLOB_ID
)

(OUT / AUDIT_FILE).write_text(
    json.dumps(AUDIT_DOC, indent=1, ensure_ascii=False), encoding="utf-8"
)

# Retained evidence and the accepted artifact must be untouched by this run.
for _n, _before in _RETAINED_BEFORE.items():
    _after = hashlib.sha256((OUT / _n).read_bytes()).hexdigest()
    assert _after == _before, f"retained evidence {_n} changed"
_raw_end, _accepted_end, _blob_end = _accepted_identifiers()
assert _accepted_end == _accepted_before == ACCEPTED_CONTENT_SHA256, _accepted_end
assert _blob_end == _accepted_blob_before == ACCEPTED_BLOB_ID, _blob_end
assert _raw_end == _accepted_raw_before, "the accepted artifact's bytes changed"
assert (
    AUDIT_DOC["schema_succession"]["accepted_artifact_content_sha256_after"]
    == ACCEPTED_CONTENT_SHA256
), AUDIT_DOC["schema_succession"]
assert AUDIT_DOC["schema_succession"]["accepted_artifact_unchanged"], AUDIT_DOC[
    "schema_succession"
]

# ---------------------------------------------------------------------------
# Determinism: a clean rerun must reproduce identical bytes and identity
# ---------------------------------------------------------------------------
RERUN = os.environ.get("HAZARDS5_RERUN") == "1"
DETERMINISTIC: bool | None = None
if not RERUN:
    _before_bytes = {
        n: hashlib.sha256((OUT / n).read_bytes()).hexdigest() for n in sorted(WRITES)
    }
    _child = subprocess.run(
        [sys.executable, str(Path(__file__).resolve())],
        env={**os.environ, "HAZARDS5_RERUN": "1"},
        capture_output=True,
        text=True,
    )
    assert _child.returncode == 0, _child.stderr[-4000:]
    _after_bytes = {
        n: hashlib.sha256((OUT / n).read_bytes()).hexdigest() for n in sorted(WRITES)
    }
    DETERMINISTIC = _before_bytes == _after_bytes
    assert DETERMINISTIC, (_before_bytes, _after_bytes)
    assert ident in _child.stdout, "the rerun minted a different proposal identity"
    # Record the result inside the artifact it describes.
    AUDIT_DOC["determinism"] = {
        "reran_from_a_clean_process": True,
        "artifact_bytes_identical": True,
        "proposal_identity_identical": True,
        "sha256": _before_bytes,
    }
    (OUT / AUDIT_FILE).write_text(
        json.dumps(AUDIT_DOC, indent=1, ensure_ascii=False), encoding="utf-8"
    )

# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

# Absolute paths go to stdout, never into an artifact: a reader needs to see
# WHICH checkout this run read, and the artifact must not differ between two
# checkouts that produced identical content.
print(f"repo root      {REPO}")
print(f"imported from  {IMPORTED_FROM}")
print(f"source pdf     {SOURCE_PDF}")
print(f"accepted       {ACCEPTED_PATH}")
print(f"output dir     {OUT}")
print(f"schema         {SCHEMA[0]} / {SCHEMA[1]}")
print(f"policy         {SEMANTIC_POLICY_VERSION} / {semantic_policy_hash()}")
print(f"identity       {ident}")
print(f"rejected       {REJECTED_IDENTITY}  differs={ident != REJECTED_IDENTITY}")
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
print(f"facts          {COUNTS['facts']}")
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
    ("schema-5 component rules", _component_rules),
    ("reason codes", reason_codes),
    ("schema binding", schema_binding),
    ("representation (standalone)", standalone),
    ("representation (merged w/ accepted conditions-1)", merged_findings),
):
    print(f"{name:50} {len(found)}")
    for f in found:
        print("   -", f)
print()
print(f"wire trip      {WIRE_ROUND_TRIP}")
print(f"obligations    {len(OBLIGATIONS)} closed, 0 open")
print(f"unresolved refs {UNRESOLVED['standalone_unresolved_targets']}")
print(f"sibling pairs  {len(SIBLING_PAIRS)} (all legal: no shared substantive span)")
print(f"ownership      {json.dumps(OWNERSHIP)}")
for _rec in LIFT_RECORDS:
    print(
        f"lift           {_rec.lift_id}: "
        f"{len(_rec.verified_collections)} collections verified"
    )
print(f"accepted content sha {_accepted_before} -> {_accepted_after}")
print(f"accepted blob id     {_accepted_blob_before} -> {_accepted_blob_after}")
print(
    f"accepted raw sha     {_accepted_raw_before}"
    + (
        "  (CRLF working copy; matches the figure reported before the repository "
        "root was derived)"
        if _accepted_raw_before == ACCEPTED_CRLF_WORKING_COPY_SHA256
        else "  (equals the content digest: this checkout honours eol=lf)"
    )
)
print(
    "disjointness   "
    + json.dumps(
        {
            "span_overlap": DISJOINT["span_overlap"],
            "leaf_overlap": DISJOINT["leaf_overlap"],
            "collection_overlap": {k: len(v) for k, v in OVERLAP.items()},
        }
    )
)
print(f"h16 trigger    {H16_TRIGGER['range']} {H16_TRIGGER['text']!r}")
print(f"D-3            {D3_RESOLUTION['status']}")
print(f"D-4            {D4_RESOLUTION['status']}")
print(f"Z-1            {Z1_RESOLUTION['status']}")
print(f"disclosed      {_disclosed}   resolved {_resolved}")
_inputs_line = json.dumps({k: v for k, v in INPUT_PATHS.items() if k != "note"})
print(f"inputs         {_inputs_line}")
if DETERMINISTIC is not None:
    print(f"deterministic  {DETERMINISTIC}")
