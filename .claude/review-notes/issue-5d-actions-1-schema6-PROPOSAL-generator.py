"""CRD Issue 5d — batch `actions-1`, representation schema 6.

Executable generator for a **fresh** actions-1 proposal and its audit. It reads
the committed SRD through the 5c pipeline, re-derives the action boundary from
the source's own entry class, cuts every represented leaf into an exact
partition, assigns each cut to the element that states it, and writes two
deterministic LF artifacts. It accepts nothing, publishes nothing, activates
nothing, retires nothing and touches no database.

What this run is, and is not
----------------------------
* It is *proposal preparation*. Zero validator findings is necessary and
  explicitly insufficient; this is material for semantic review.
* This batch is **not publishable on its own**. It cites five records that
  actions-1 does not define and that accepted authority does not yet carry, so
  the standalone *and* the merged validation both report exactly those five.
  That is asserted as set equality below, and reported as such — a partial
  batch is not relabelled as a complete one.
* The proposal is derived from the bound source. No earlier actions-1 proposal
  payload, audit row, or unit-test chunk id is read as input. The superseded
  schema-1 artifact is named only so the run can prove it differs.

Emission rule
-------------
Every represented leaf of every action entry is partitioned end to end. A
segment's first element is the text the segment **ends with**; ``None`` means
"to the end of the leaf". Cuts are therefore derived from the bound leaf
content at run time and fail loudly if the source moved. Separator runs are
absorbed as the *leading* text of the next segment, so the partition
reconstructs each leaf byte for byte.

What schema 6 makes authorable here
-----------------------------------
Actions-1 is the first batch that needs actor choices. Five of its records
state a choice rather than a conjunction — Attack's equip/unequip × before/
after, Dash's standard-or-special speed, Help's two ways to assist, Ready's
act-or-move response — and schema 6's ``ComponentOption`` is what carries them
without inventing a Boolean predicate or duplicating a sibling. Schema 6's new
applicability kinds carry the rest: ``ANY_OF`` for Dodge's two-way loss clause
and Hide's obscurement-or-cover precondition, ``CONDITION_STATE`` for
Incapacitated, ``EFFECT_STATE`` for broken Concentration, ``OBSCUREMENT`` and
``COVER`` for Hide.

Provenance shape this batch adds
--------------------------------
Hazards gave each span exactly one provenance edge. Actions-1 cannot: four
places state a rule that several elements share, and the schema admits at most
one PRIMARY per span.

* Dodge's ``until the start of your next turn`` is one duration governing two
  benefits. Duplicating the duration fact across the two benefit components
  would put an equivalent fact of two components on one substantive span, which
  ``_validate_duplicated_fact_authority`` refuses — correctly. So the duration
  is its own component, PRIMARY on that span, and the two benefit components
  take CONTEXTUAL edges on it.
* Attack's equipment change states two independent axes in two sentences —
  which change, and when — while ``EquipmentChangeFact`` carries both at once.
  The four combinations are an option set; neither sentence states any single
  combination, so each sentence is PRIMARY by the owning component and each
  option fact takes a CONTEXTUAL edge on both. Disclosed as limit L-1.
* Ready's ``which lets you act by taking a Reaction`` grounds the Reaction cost
  of both response arms; both option facts take CONTEXTUAL edges there.
* Dash's ``You choose which speed to use`` grounds the standard-speed arm.

A CONTEXTUAL edge on a substantive span is admissible by
``_ADMISSIBLE_ROLES``; what it is not allowed to be is a second PRIMARY, and
the ownership section below asserts that every substantive span has exactly
one.

Reason-code residue
-------------------
``R-help-reason``. Help's two arms are one option set — an option set cannot
span components — so the component carries one irreducibility reason. H2 and
H6 want ``contextual_applicability``; H5 ("The GM has final say on whether your
assistance is possible") would prefer ``gamemaster_latitude``. Nothing in
``ApplicabilityKind`` can scope a sibling component to one arm of a choice, and
demoting H5 to supporting authority would be false — it is substantive. So the
component carries ``contextual_applicability``, which is *true* of H5 (whether
the assistance applies depends on fiction the projection cannot enumerate) and
merely less specific than the label H5 alone would take. A coarsening, not a
falsehood; recorded rather than hidden.

Substantive judgment changes from discovery
-------------------------------------------
Recorded in ``JUDGMENT_CHANGES`` below and explained in the checkpoint. The
discovery ledger's dispositions were a first pass over the source, not a
target; historical counts are not reproduced for their own sake.
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
#: actually lives: `<repo>/.claude/review-notes/<this file>`.
OUT = Path(__file__).resolve().parent
REPO = OUT.parents[1]
assert OUT.name == "review-notes" and OUT.parent.name == ".claude", OUT
sys.path.insert(0, str(REPO / "src"))

SOURCE_PDF = REPO / "docs/sources/DnD5_5e_SRD_CC_v5_2_1.pdf"

#: **The frozen review prior.** Accepted authority as it stands for this batch's
#: review: conditions-1 and hazards-1, representation schema 5. Read only.
REVIEW_PRIOR_PATH = (
    REPO
    / "tests/ingestion/mechanical/data"
    / "accepted_prior_conditions_1_hazards_1.json"
)

#: **A mutation sentinel, never an input.** Bytes captured before generation and
#: asserted identical afterwards. Never loaded, lifted, merged, or recorded.
LIVE_ORACLE_PATH = (
    REPO
    / "src/afterworlds/ingestion/mechanical/oracles"
    / "srd-5-2-1-corpus-36b786d8-fa2.json"
)
PACKAGE_ROOT = REPO / "src/afterworlds"
for _required in (SOURCE_PDF, REVIEW_PRIOR_PATH, LIVE_ORACLE_PATH, PACKAGE_ROOT):
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

#: The superseded schema-1 actions-1 proposal. Named so this run can prove it
#: differs; never read as input, never imported, never restamped.
SUPERSEDED_IDENTITY = "ff30c25a568836b3e44b60b692a713aa8da90cca3ffc8326fbc8adc0ff541bf0"  # noqa: E501  # pragma: allowlist secret

#: The frozen review prior, identified by **content** rather than by whatever
#: bytes a working copy holds. `.gitattributes` declares `* text=auto eol=lf`,
#: so a raw digest is a property of a checkout; the canonical (CRLF -> LF)
#: SHA-256 and the Git blob id are properties of the authority.
REVIEW_PRIOR_CONTENT_SHA256 = "0925d796a058ff4e64f9a429c9ad73d3c39f1e74dff7e394bc2957c1587e73f7"  # noqa: E501  # pragma: allowlist secret
REVIEW_PRIOR_BLOB = (
    "6e65533f4a3523aba3d60cfc3c274ab22e66b59a"  # pragma: allowlist secret
)
REVIEW_PRIOR_BATCH_IDS = ["conditions-1", "hazards-1"]
REVIEW_PRIOR_SCHEMA_VERSION = "5d-representation-schema-5"

# --- Retained-evidence guard ------------------------------------------------
# Every previous actions-1 artifact records a superseded conclusion or the
# discovery this run derives its brief from. Refuse to run if this file would
# overwrite one, and assert afterwards that none of them moved.
RETAINED = (
    "issue-5d-batch-actions-1-PROPOSAL.json",
    "issue-5d-batch-actions-1-audit.json",
    "issue-5d-batch-actions-1-generator.py",
    "issue-5d-actions-1-obligation-coordinates.json",
    "issue-5d-actions-1-OBLIGATION-COORDINATES.py",
    "issue-5d-actions-1-SCHEMA-STOP-CHECKPOINT.md",
    "issue-5d-actions-1-DISCOVERY-KICKOFF.md",
    "issue-5d-actions-1-DISCOVERY-REVIEW.md",
    "issue-5d-actions-1-HYGIENE-CHECKPOINT.md",
)
PROPOSAL_FILE = "issue-5d-actions-1-schema6-PROPOSAL.json"
AUDIT_FILE = "issue-5d-actions-1-schema6-audit.json"
WRITES = {PROPOSAL_FILE, AUDIT_FILE}
assert not (WRITES & set(RETAINED)), "would overwrite retained evidence"
_RETAINED_BEFORE = {
    n: hashlib.sha256((OUT / n).read_bytes()).hexdigest()
    for n in RETAINED
    if (OUT / n).exists()
}

from afterworlds.ingestion.corpus.hashing import canonical_bytes  # noqa: E402
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
    ActionAllowanceFact,
    ActionCost,
    ActionEconomyFact,
    ActivationCostEligibilityFact,
    AdvantageFact,
    AdvantageState,
    AllowanceScope,
    Applicability,
    ApplicabilityKind,
    AttackRelativeTiming,
    AutomaticOutcome,
    BenefitUseLimit,
    ComponentDraft,
    ComponentOption,
    Comparison,
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
    FactQualifier,
    GrantedActivity,
    InterleavePoint,
    MovementAllowanceBasis,
    MovementAllowanceFact,
    MovementInterleaveFact,
    ObscurementState,
    ProseBindingDraft,
    ProvenanceClaim,
    ProvenanceRole,
    ProvenanceTargetKind,
    ReactionProvocationFact,
    RecordDraft,
    RecordKind,
    RecurrenceBoundary,
    RecurringActionRequirementFact,
    ReferenceDraft,
    RepresentationDraft,
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
    _dataclass_payload,
    component_damage_composition_violations,
    component_roll_outcome_violations,
    fact_invariant_violations,
    fact_key,
    fact_qualifier_target_key,
    fact_target_key,
    held_structure_violations,
    option_set_violations,
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

IMPORTED_FROM = Path(afterworlds.__file__).resolve().parent
assert PACKAGE_ROOT.resolve() == IMPORTED_FROM, (IMPORTED_FROM, PACKAGE_ROOT)
INPUT_PATHS = {
    "repository_root_derived_from": "Path(__file__).resolve().parents[2]",
    "source_pdf": SOURCE_PDF.relative_to(REPO).as_posix(),
    "review_prior": REVIEW_PRIOR_PATH.relative_to(REPO).as_posix(),
    "afterworlds_package": IMPORTED_FROM.relative_to(REPO).as_posix(),
    "output_directory": OUT.relative_to(REPO).as_posix(),
    "note": (
        "Recorded relative to the derived root on purpose: an absolute path "
        "would make this artifact differ between two checkouts that produced "
        "identical content. The live accepted-authority oracle is deliberately "
        "absent: it is not an input. This run reads it only as a mutation "
        "sentinel and records neither its path nor its digest, because an "
        "accumulating artifact's identity goes stale at the next acceptance."
    ),
}

SCHEMA = (REPRESENTATION_SCHEMA_VERSION, representation_schema_hash())
assert SCHEMA[0] == "5d-representation-schema-6", SCHEMA
assert SCHEMA[1] == (
    "0e4b4378bf1409ed3ffbbec61a279430689ce4a0d3b70b1b3e9d886f66ae20b7"  # pragma: allowlist secret
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
#: published CRD Issue 5c release record and disclosed as such.
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
# The source's own entry class: `[Action]`-tagged entries under Rules
# Definitions, plus the umbrella `Action` glossary rule whose own list names
# exactly those twelve. Derived by scanning the labels, then checked against the
# names the umbrella prints, so an action added or renamed upstream fails here
# rather than silently dropping out of the batch.
ACTION_LABELS = sorted(lab for lab in ENTRY_BY_LABEL if lab.endswith(" [Action]"))
NAMED = [
    "Attack",
    "Dash",
    "Disengage",
    "Dodge",
    "Help",
    "Hide",
    "Influence",
    "Magic",
    "Ready",
    "Search",
    "Study",
    "Utilize",
]
assert [f"{n} [Action]" for n in sorted(NAMED)] == ACTION_LABELS, ACTION_LABELS
assert len(ACTION_LABELS) == 12, ACTION_LABELS
#: The umbrella's own four name leaves - the list it prints under "These actions
#: are defined elsewhere in this glossary:".
UMBRELLA_NAME_TEXT = " ".join(
    leaf.content for leaf in by_container[ENTRY_BY_LABEL["Action"]][4:8]
)
for _n in NAMED:
    assert _n in UMBRELLA_NAME_TEXT, f"{_n} is not named by the umbrella's own list"

#: The two 5c policy exclusions inside this boundary: running headers/footers on
#: the Help and Ready pages. Enumerated rather than waved past, because a batch
#: that silently lost a body leaf would look the same as one that lost a header.
POLICY_EXCLUDED = sorted(
    leaf.leaf_id
    for lab in ["Action", *ACTION_LABELS]
    for cid in [ENTRY_BY_LABEL[lab]]
    for leaf in LEDGER_OBJ.leaves
    if cid in leaf.container_path and leaf.leaf_id not in REPRESENTED
)
assert len(POLICY_EXCLUDED) == 2, POLICY_EXCLUDED
assert [lid[:8] for lid in POLICY_EXCLUDED] == ["056d861c", "891e92d8"], POLICY_EXCLUDED
POLICY_EXCLUSION_DETAIL = [
    {
        "leaf": lid,
        "text": LEAF_BY_ID[lid].content,
        "printed_page": LEAF_BY_ID[lid].page_index + 1,
        "reason": exclusion_reason_for(LEAF_BY_ID[lid], LABELS).code,
    }
    for lid in POLICY_EXCLUDED
]
for _row in POLICY_EXCLUSION_DETAIL:
    assert _row["text"].startswith("System Reference Document"), _row

SCOPE_KEY = "srd-5.2.1/rules-glossary"
LSQ = "“"  # left double quote
RSQ = "”"  # right double quote
APOS = "’"

RECORD_KEY: dict[str, str] = {"Action": "glossary.action"}
for lab in ACTION_LABELS:
    RECORD_KEY[lab] = "action." + lab.split(" [")[0].lower()
RECORD_KIND = {k: RecordKind.GLOSSARY_RULE for k in RECORD_KEY.values()}

ACT = "glossary.action"
ATK = "action.attack"
DASH = "action.dash"
DISE = "action.disengage"
DODG = "action.dodge"
HELP = "action.help"
HIDE = "action.hide"
INFL = "action.influence"
MAGI = "action.magic"
REDY = "action.ready"
SRCH = "action.search"
STDY = "action.study"
UTIL = "action.utilize"

# Closed irreducibility reason codes, named once.
CTX = "contextual_applicability"
SUBJ = "subjective_judgment"
OEE = "open_ended_effect"
GML = "gamemaster_latitude"
FDC = "fiction_dependent_consequence"
for _code in (CTX, SUBJ, OEE, GML, FDC):
    assert irreducibility_reason_for(_code) is not None, _code

# ---------------------------------------------------------------------------
# The typed facts, declared once and referenced by the clause table below
# ---------------------------------------------------------------------------

K = ApplicabilityKind


def _canon(*terms: Applicability) -> tuple[Applicability, ...]:
    """ANY_OF terms in the canonical order the schema requires."""
    return tuple(sorted(terms, key=lambda a: canonical_bytes(_dataclass_payload(a))))


# --- glossary.action --------------------------------------------------------
ALLOW_1_ACTION_PER_TURN = ActionAllowanceFact(
    count=1, per=AllowanceScope.TURN, cost=ActionCost.ACTION
)

# --- action.attack ----------------------------------------------------------
ATTACK_ALLOWANCE = ActionAllowanceFact(
    count=1, per=AllowanceScope.OWNING_EFFECT, activity=GrantedActivity.ATTACK_ROLL
)
EQUIP_ALLOWANCE = ActionAllowanceFact(
    count=1, per=AllowanceScope.ATTACK, activity=GrantedActivity.EQUIPMENT_CHANGE
)
EQUIP_BEFORE = EquipmentChangeFact(EquipmentChange.EQUIP, AttackRelativeTiming.BEFORE)
EQUIP_AFTER = EquipmentChangeFact(EquipmentChange.EQUIP, AttackRelativeTiming.AFTER)
UNEQUIP_BEFORE = EquipmentChangeFact(
    EquipmentChange.UNEQUIP, AttackRelativeTiming.BEFORE
)
UNEQUIP_AFTER = EquipmentChangeFact(EquipmentChange.UNEQUIP, AttackRelativeTiming.AFTER)
#: Declared in one place so the option set and the CONTEXTUAL edges that ground
#: it cannot drift apart.
EQUIP_OPTIONS = (
    ("equip_before", EQUIP_BEFORE),
    ("equip_after", EQUIP_AFTER),
    ("unequip_before", UNEQUIP_BEFORE),
    ("unequip_after", UNEQUIP_AFTER),
)
INTERLEAVE = MovementInterleaveFact(between=InterleavePoint.REPEATED_ATTACKS)

# --- shared movement / duration / economy ----------------------------------
MOVE_OWN = MovementAllowanceFact(basis=MovementAllowanceBasis.OWN_SPEED)
MOVE_SPECIAL = MovementAllowanceFact(basis=MovementAllowanceBasis.OWN_SPECIAL_SPEED)
DUR_END_TURN = EffectDurationFact(
    until=RecurrenceBoundary.END_OF_TURN, whose=RollActor.SUBJECT
)
DUR_START_TURN = EffectDurationFact(
    until=RecurrenceBoundary.START_OF_TURN, whose=RollActor.SUBJECT
)
AE_ACTION = ActionEconomyFact(ActionCost.ACTION)
AE_REACTION = ActionEconomyFact(ActionCost.REACTION)
TERMINATION = EffectTerminationFact()
SUST_CONC = SustainedStateRequirementFact(state=SustainedState.CONCENTRATION)

# --- action.disengage -------------------------------------------------------
NO_OPPORTUNITY = ReactionProvocationFact(
    reaction=TriggeredReaction.OPPORTUNITY_ATTACK, provokes=False
)

# --- action.dodge -----------------------------------------------------------
DISADV_ATTACKS = AdvantageFact(
    state=AdvantageState.DISADVANTAGE,
    roll=RollSpec(actor=RollActor.AGAINST_SUBJECT, context=RollContext.ATTACK_ROLL),
)
ADV_DEX_SAVES = AdvantageFact(
    state=AdvantageState.ADVANTAGE,
    roll=RollSpec(
        actor=RollActor.SUBJECT,
        context=RollContext.SAVING_THROW,
        ability=AbilityScore.DEXTERITY,
    ),
)
#: "You lose these benefits if you have the Incapacitated condition or if your
#: Speed is 0." - a negated disjunction, which is exactly what schema 6's flat
#: ANY_OF carries. Negating the whole term is the honest reading: the benefits
#: apply while NEITHER holds.
DODGE_UNIMPAIRED = Applicability(
    kind=K.ANY_OF,
    negated=True,
    any_of_terms=_canon(
        Applicability(kind=K.CONDITION_STATE, condition=ConditionKind.INCAPACITATED),
        Applicability(
            kind=K.QUANTITY_THRESHOLD,
            quantity=TrackedQuantity.SPEED,
            comparison=Comparison.EQUALS,
            value=0,
        ),
    ),
)

# --- action.help ------------------------------------------------------------
ADV_ALLY_CHECK = AdvantageFact(
    state=AdvantageState.ADVANTAGE,
    roll=RollSpec(actor=RollActor.ALLY, context=RollContext.ABILITY_CHECK),
    use_limit=BenefitUseLimit.NEXT_QUALIFYING_ROLL,
)
ADV_ALLY_ATTACK = AdvantageFact(
    state=AdvantageState.ADVANTAGE,
    roll=RollSpec(actor=RollActor.ALLY, context=RollContext.ATTACK_ROLL),
    use_limit=BenefitUseLimit.NEXT_QUALIFYING_ROLL,
)

# --- action.hide ------------------------------------------------------------
STEALTH_DC15 = AbilityCheckFact(
    AbilityScore.DEXTERITY,
    DcKind.FIXED,
    15,
    skill=Skill.STEALTH,
    context=RollContext.ABILITY_CHECK,
)
INVISIBLE_APPLIES = ConditionEffectFact(
    ConditionKind.INVISIBLE, ConditionEffectKind.APPLIES
)
#: "Make note of your check's total, which is the DC for a creature to find you
#: with a Wisdom (Perception) check." Its own component, because a ROLL_OUTCOME
#: qualifier needs exactly one roll established in scope and `hide_check`
#: already establishes the Stealth check.
PERCEPTION_VS_HIDDEN = AbilityCheckFact(
    AbilityScore.WISDOM,
    DcKind.RECORDED_CHECK_TOTAL,
    against_subject=True,
    skill=Skill.PERCEPTION,
    context=RollContext.ABILITY_CHECK,
)
HIDE_CONCEALED = Applicability(
    kind=K.ANY_OF,
    any_of_terms=_canon(
        Applicability(
            kind=K.OBSCUREMENT, obscurement=ObscurementState.HEAVILY_OBSCURED
        ),
        Applicability(kind=K.COVER, cover=CoverDegree.THREE_QUARTERS),
        Applicability(kind=K.COVER, cover=CoverDegree.TOTAL),
    ),
)

# --- action.influence -------------------------------------------------------
INFLUENCE_CHECK = AbilityCheckFact(
    None,
    DcKind.HIGHER_OF_FIXED_OR_TARGET_ABILITY_SCORE,
    15,
    dc_ability=AbilityScore.INTELLIGENCE,
    context=RollContext.ABILITY_CHECK,
)
RETRY_24H = RetryRestrictionFact(
    amount=24, unit=TimeUnit.HOUR, gamemaster_may_set_other=True
)

# --- action.magic -----------------------------------------------------------
RECUR_ACTION_PER_TURN = RecurringActionRequirementFact(
    cost=ActionCost.ACTION, per=TimeUnit.TURN
)
NO_SLOT_EXPENDED = ResourceExpenditureFact(
    resource=ExpendableResource.SPELL_SLOT, expended=False
)
CONCENTRATION_BROKEN = Applicability(
    kind=K.EFFECT_STATE, effect_state=StateEffectKind.CONCENTRATION_BROKEN
)

# --- action.ready -----------------------------------------------------------
REACTION_GRANT = ActionAllowanceFact(
    count=1, per=AllowanceScope.OWNING_EFFECT, cost=ActionCost.REACTION
)
CASTING_RESOURCES_SPENT = ResourceExpenditureFact(
    resource=ExpendableResource.CASTING_RESOURCES, expended=True
)
TRIGGER_RESOLUTION = TriggeredResolutionFact(
    timing=ResolutionTiming.IMMEDIATELY_AFTER_TRIGGER, optional=True
)

# --- action.search / action.study ------------------------------------------
SEARCH_CHECK = AbilityCheckFact(
    AbilityScore.WISDOM, DcKind.GAMEMASTER_SET, context=RollContext.ABILITY_CHECK
)
STUDY_CHECK = AbilityCheckFact(
    AbilityScore.INTELLIGENCE, DcKind.GAMEMASTER_SET, context=RollContext.ABILITY_CHECK
)

# --- action.utilize ---------------------------------------------------------
OBJECT_NEEDS_ACTION = ActivationCostEligibilityFact(
    subject=EligibilitySubject.OBJECT, cost=ActionCost.ACTION
)

ROLL_SUCCESS = Applicability(kind=K.ROLL_OUTCOME, outcome=AutomaticOutcome.SUCCESS)
ROLL_FAILURE = Applicability(kind=K.ROLL_OUTCOME, outcome=AutomaticOutcome.FAILURE)

# ---------------------------------------------------------------------------
# Components. Facts are collected from the clause table; options are declared
# here by name and filled from the option-grain claims the table makes.
# ---------------------------------------------------------------------------

COMPONENTS: dict[tuple[str, str], dict] = {
    # --- glossary.action ---------------------------------------------------
    (ACT, "action_allowance"): dict(handling=ComponentHandling.STRUCTURED),
    # The choice of *which* action is unbounded: features add actions the
    # glossary never enumerates, so any typed reduction would narrow it.
    (ACT, "action_choice"): dict(handling=ComponentHandling.PROSE_BOUND, reason=OEE),
    # --- action.attack -----------------------------------------------------
    (ATK, "attack_allowance"): dict(handling=ComponentHandling.STRUCTURED),
    (ATK, "attack_equipment_allowance"): dict(handling=ComponentHandling.STRUCTURED),
    # Four options, because `EquipmentChangeFact` carries change and timing at
    # once while the source states the two axes in two separate sentences. See
    # disclosed limit L-1.
    (ATK, "attack_equipment_change"): dict(
        handling=ComponentHandling.STRUCTURED,
        options=tuple(k for k, _f in EQUIP_OPTIONS),
    ),
    (ATK, "attack_movement_interleave"): dict(
        handling=ComponentHandling.MIXED, reason=CTX
    ),
    # --- action.dash -------------------------------------------------------
    (DASH, "dash_movement"): dict(handling=ComponentHandling.STRUCTURED),
    # An actor choice, not a conjunction: "You choose which speed to use each
    # time you take it."
    (DASH, "dash_speed_choice"): dict(
        handling=ComponentHandling.STRUCTURED,
        options=("standard_speed", "special_speed"),
    ),
    # --- action.disengage --------------------------------------------------
    (DISE, "disengage_movement"): dict(handling=ComponentHandling.STRUCTURED),
    # --- action.dodge ------------------------------------------------------
    # Three components, and each boundary is forced rather than chosen.
    # `dodge_duration` stands alone because one duration governs two benefits
    # and duplicating the fact across both would put an equivalent fact of two
    # components on one substantive span. The two benefits are separate because
    # only the attack benefit carries a prose condition, and a component holds
    # exactly one irreducibility reason.
    (DODG, "dodge_attack_disadvantage"): dict(
        handling=ComponentHandling.MIXED, reason=CTX, applies_when=DODGE_UNIMPAIRED
    ),
    (DODG, "dodge_saving_throws"): dict(
        handling=ComponentHandling.STRUCTURED, applies_when=DODGE_UNIMPAIRED
    ),
    (DODG, "dodge_duration"): dict(handling=ComponentHandling.STRUCTURED),
    # --- action.help -------------------------------------------------------
    # One option set, one reason. See residue R-help-reason in the module
    # docstring: H5's `gamemaster_latitude` is coarsened to
    # `contextual_applicability`, which is true of it and less specific.
    (HELP, "help_choice"): dict(
        handling=ComponentHandling.MIXED,
        reason=CTX,
        options=("assist_ability_check", "assist_attack_roll"),
    ),
    # --- action.hide -------------------------------------------------------
    (HIDE, "hide_check"): dict(
        handling=ComponentHandling.MIXED,
        reason=CTX,
        applies_when=HIDE_CONCEALED,
        fact_qualifiers=(
            FactQualifier(
                fact_key=fact_key(INVISIBLE_APPLIES), applies_when=ROLL_SUCCESS
            ),
        ),
    ),
    (HIDE, "hide_awareness"): dict(handling=ComponentHandling.PROSE_BOUND, reason=FDC),
    (HIDE, "hide_discovery_dc"): dict(handling=ComponentHandling.STRUCTURED),
    (HIDE, "hide_end"): dict(handling=ComponentHandling.MIXED, reason=CTX),
    # --- action.influence --------------------------------------------------
    (INFL, "influence_attempt"): dict(
        handling=ComponentHandling.PROSE_BOUND, reason=OEE
    ),
    (INFL, "influence_disposition"): dict(
        handling=ComponentHandling.PROSE_BOUND, reason=GML
    ),
    (INFL, "influence_willing"): dict(
        handling=ComponentHandling.PROSE_BOUND, reason=OEE
    ),
    (INFL, "influence_unwilling"): dict(
        handling=ComponentHandling.PROSE_BOUND, reason=CTX
    ),
    (INFL, "influence_check"): dict(
        handling=ComponentHandling.MIXED,
        reason=GML,
        fact_qualifiers=(
            FactQualifier(fact_key=fact_key(RETRY_24H), applies_when=ROLL_FAILURE),
        ),
    ),
    # "the monster does as urged" - the effect space is the whole of what a
    # monster might be urged to do. Prose-bound rather than gated: a
    # ROLL_OUTCOME applicability in a component with no roll of its own would
    # name the outcome of nothing.
    (INFL, "influence_success"): dict(
        handling=ComponentHandling.PROSE_BOUND, reason=OEE
    ),
    # --- action.magic ------------------------------------------------------
    (MAGI, "magic_activation"): dict(handling=ComponentHandling.MIXED, reason=OEE),
    (MAGI, "magic_long_casting"): dict(handling=ComponentHandling.STRUCTURED),
    (MAGI, "magic_concentration_break"): dict(
        handling=ComponentHandling.STRUCTURED, applies_when=CONCENTRATION_BROKEN
    ),
    # --- action.ready ------------------------------------------------------
    (REDY, "ready_action"): dict(handling=ComponentHandling.STRUCTURED),
    (REDY, "ready_reaction_grant"): dict(handling=ComponentHandling.STRUCTURED),
    (REDY, "ready_trigger"): dict(handling=ComponentHandling.PROSE_BOUND, reason=OEE),
    # "the action you will take in response" is unbounded; "move up to your
    # Speed" is not. An option set carries both arms without narrowing the first
    # or prose-binding the second.
    (REDY, "ready_response"): dict(
        handling=ComponentHandling.MIXED,
        reason=OEE,
        options=("chosen_action", "move_up_to_speed"),
    ),
    (REDY, "ready_resolution"): dict(handling=ComponentHandling.STRUCTURED),
    (REDY, "ready_spell"): dict(handling=ComponentHandling.STRUCTURED),
    (REDY, "ready_concentration_break"): dict(
        handling=ComponentHandling.STRUCTURED, applies_when=CONCENTRATION_BROKEN
    ),
    # --- action.search -----------------------------------------------------
    (SRCH, "search_check"): dict(handling=ComponentHandling.MIXED, reason=SUBJ),
    # --- action.study ------------------------------------------------------
    # Two components because two reasons: what the check calls to mind is
    # open-ended, while which skill applies to an area of knowledge is a
    # judgement call.
    (STDY, "study_check"): dict(handling=ComponentHandling.MIXED, reason=OEE),
    (STDY, "study_areas"): dict(handling=ComponentHandling.PROSE_BOUND, reason=SUBJ),
    # --- action.utilize ----------------------------------------------------
    # Fully structured: "requires an action for its use" is exactly
    # `ActivationCostEligibilityFact`, and "you take the Utilize action" is
    # exactly `ActionEconomyFact`. Nothing here is irreducible, so nothing is
    # prose-bound.
    (UTIL, "utilize_action"): dict(handling=ComponentHandling.STRUCTURED),
}

# ---------------------------------------------------------------------------
# The proposed batch, as an explicit reviewable clause table
# ---------------------------------------------------------------------------
#
# Segment shape: (marker, kind, arg, obligation) with an optional fifth element
# `extras` — a tuple of (kind, arg) pairs that emit additional CONTEXTUAL edges
# on the same span without creating a second span or a second PRIMARY.
#
# Segment kinds (upper case: creates the span's single claim):
#   R  supporting authority, claimed CONTEXTUAL by the record
#   C  supporting authority, claimed CONTEXTUAL by a component        arg=comp
#   X  supporting authority, claimed CONTEXTUAL by a reference
#                                     arg=(text, target[, from_component])
#   F  substantive, claimed PRIMARY by a typed fact     arg=(comp, fact[, option])
#   A  substantive, claimed PRIMARY by its owning component           arg=comp
#   Q  substantive, claimed PRIMARY by a fact qualifier               arg=(comp,fact)
#   P  substantive, claimed PRIMARY by a prose binding
#                                     arg=(comp, reason[, option])
#
# Extra kinds (lower case: CONTEXTUAL only, never PRIMARY, never a new span):
#   f  a typed fact also grounded here                 arg=(comp, fact[, option])
#   c  a component also grounded here                                 arg=comp
#
# `A` covers a component's applicability span, and — new in this batch — the
# span that states one axis of an option set that no single option states on its
# own. Both are properties of the component rather than of any one fact, so the
# owning component is the honest PRIMARY claimant.

W = [(None, "R", None, None)]  # whole leaf, supporting authority, owned by the record

#: The four CONTEXTUAL edges that ground Attack's equipment cross-product, used
#: on both axis spans.
EQ_EXTRAS = tuple(
    ("f", ("attack_equipment_change", _f, _k)) for _k, _f in EQUIP_OPTIONS
)

SPEC: dict[str, list] = {}

# --- Action (umbrella glossary rule) ---------------------------------------
# The twelve names are source-authored mechanical references (#137 contract 3
# and 7, ADR-005d Decision 7). They are owned by `action_choice` rather than by
# the record: the record's own sentence is the allowance, and it is the choice
# of action that these twelve resolve.
SPEC["Action"] = [
    W,  # 'Action'
    [
        ("take one action.", "F", ("action_allowance", ALLOW_1_ACTION_PER_TURN), "A1"),
        (None, "P", ("action_choice", OEE), "A2"),
    ],
    [(None, "R", None, "A3")],  # 'See also'
    [
        (f"({LSQ}Actions{RSQ}).", "R", None, "A3"),
        (None, "C", "action_choice", "A4"),
    ],
    [
        ("Attack", "X", ("Attack", ATK, "action_choice"), "A4"),
        (" Dash", "X", ("Dash", DASH, "action_choice"), "A4"),
        (None, "X", ("Disengage", DISE, "action_choice"), "A4"),
    ],
    [
        ("Dodge", "X", ("Dodge", DODG, "action_choice"), "A4"),
        (" Help", "X", ("Help", HELP, "action_choice"), "A4"),
        (None, "X", ("Hide", HIDE, "action_choice"), "A4"),
    ],
    [
        ("Influence", "X", ("Influence", INFL, "action_choice"), "A4"),
        (" Magic", "X", ("Magic", MAGI, "action_choice"), "A4"),
        (None, "X", ("Ready", REDY, "action_choice"), "A4"),
    ],
    [
        ("Search", "X", ("Search", SRCH, "action_choice"), "A4"),
        (" Study", "X", ("Study", STDY, "action_choice"), "A4"),
        (None, "X", ("Utilize", UTIL, "action_choice"), "A4"),
    ],
]

# --- Attack ----------------------------------------------------------------
SPEC["Attack [Action]"] = [
    W,
    [
        ("one attack roll", "F", ("attack_allowance", ATTACK_ALLOWANCE), "B1"),
        # Identifies the instrument the granted attack is made with; it limits
        # and identifies rather than stating a separate mechanic, and no closed
        # reason is true of it.
        (None, "C", "attack_allowance", "B2"),
    ],
    [(None, "C", "attack_equipment_change", "B3")],
    [
        ("one weapon", "A", "attack_equipment_change", "B3", EQ_EXTRAS),
        ("this action.", "F", ("attack_equipment_allowance", EQUIP_ALLOWANCE), "B3"),
        ("after the attack.", "A", "attack_equipment_change", "B4", EQ_EXTRAS),
        ("for that attack.", "C", "attack_equipment_change", "B5"),
        (None, "C", "attack_equipment_change", "B6"),
    ],
    [(None, "C", "attack_movement_interleave", "B7")],
    [
        # The prerequisite ranges over features the glossary never enumerates;
        # the consequence it governs is typed beside it.
        ("the Attack action,", "P", ("attack_movement_interleave", CTX), "B7"),
        (None, "F", ("attack_movement_interleave", INTERLEAVE), "B7"),
    ],
]

# --- Dash ------------------------------------------------------------------
SPEC["Dash [Action]"] = [
    W,
    [
        ("Dash action,", "C", "dash_movement", "D8"),
        ("extra movement", "F", ("dash_movement", MOVE_OWN), "D1"),
        ("the current turn", "F", ("dash_movement", DUR_END_TURN), "D3"),
        # One fact, two spans, both PRIMARY: the increase's basis is stated
        # twice, once as "extra movement" and once as "equals your Speed".
        ("any modifiers.", "F", ("dash_movement", MOVE_OWN), "D2"),
        (None, "C", "dash_movement", "D4"),
    ],
    [(None, "C", "dash_movement", "D4")],
    [
        ("this turn if you Dash.", "C", "dash_movement", "D4"),
        (None, "F", ("dash_speed_choice", MOVE_SPECIAL, "special_speed"), "D5"),
    ],
    [
        ("take this action.", "F", ("dash_speed_choice", MOVE_SPECIAL, "special_speed"), "D5"),
        (
            "You choose which",
            "A",
            "dash_speed_choice",
            "D6",
            (("f", ("dash_speed_choice", MOVE_OWN, "standard_speed")),),
        ),
    ],
    [(None, "A", "dash_speed_choice", "D6")],
    [(None, "R", None, "D7")],  # 'See also'
    [(None, "X", ("Speed", "glossary.speed"), "D7")],
]

# --- Disengage -------------------------------------------------------------
SPEC["Disengage [Action]"] = [
    W,
    [
        ("Disengage action,", "C", "disengage_movement", "E3"),
        ("Opportunity Attacks", "F", ("disengage_movement", NO_OPPORTUNITY), "E1"),
        # `None` absorbs the sentence's trailing period, which is the one
        # separator in this batch that follows rather than precedes a claim.
        (None, "F", ("disengage_movement", DUR_END_TURN), "E2"),
    ],
]

# --- Dodge -----------------------------------------------------------------
SPEC["Dodge [Action]"] = [
    W,
    [
        ("following benefits:", "R", None, "G6"),
        (
            "your next turn",
            "F",
            ("dodge_duration", DUR_START_TURN),
            "G4",
            (("c", "dodge_attack_disadvantage"), ("c", "dodge_saving_throws")),
        ),
        ("has Disadvantage", "F", ("dodge_attack_disadvantage", DISADV_ATTACKS), "G1"),
        ("see the attacker", "P", ("dodge_attack_disadvantage", CTX), "G2"),
        (", and ", "R", None, "G7"),
        ("with Advantage", "F", ("dodge_saving_throws", ADV_DEX_SAVES), "G3"),
        (
            None,
            "A",
            "dodge_attack_disadvantage",
            "G5",
            (("c", "dodge_saving_throws"),),
        ),
    ],
]

# --- Help ------------------------------------------------------------------
SPEC["Help [Action]"] = [
    W,
    [(None, "A", "help_choice", "H1")],
    [(None, "C", "help_choice", "H1")],  # 'Assist an Ability Check.'
    [(None, "P", ("help_choice", CTX, "assist_ability_check"), "H2")],
    [
        ("an ability check.", "P", ("help_choice", CTX, "assist_ability_check"), "H2"),
        ("skill or tool.", "F", ("help_choice", ADV_ALLY_CHECK, "assist_ability_check"), "H3"),
        ("your next turn.", "F", ("help_choice", DUR_START_TURN, "assist_ability_check"), "H4"),
        # R-help-reason: substantive, and carried under the component's single
        # reason rather than demoted or split onto a false sibling scope.
        (None, "P", ("help_choice", CTX, "assist_ability_check"), "H5"),
    ],
    [(None, "C", "help_choice", "H1")],  # 'Assist an Attack Roll.'
    [
        ("5 feet of you,", "P", ("help_choice", CTX, "assist_attack_roll"), "H6"),
        ("against that enemy.", "F", ("help_choice", ADV_ALLY_ATTACK, "assist_attack_roll"), "H6"),
        (None, "F", ("help_choice", DUR_START_TURN, "assist_attack_roll"), "H7"),
    ],
]

# --- Hide ------------------------------------------------------------------
SPEC["Hide [Action]"] = [
    W,
    [
        ("hide yourself.", "R", None, "I9"),
        ("To do so, ", "C", "hide_check", "I10"),
        ("(Stealth) check", "F", ("hide_check", STEALTH_DC15), "I1"),
        ("Total Cover", "A", "hide_check", "I2"),
        # Line of sight is fiction the projection cannot enumerate, and it
        # conditions whether the rule applies at all.
        ("line of sight", "P", ("hide_check", CTX), "I3"),
        ("it can see you", "P", ("hide_awareness", FDC), "I4"),
        ("successful check,", "Q", ("hide_check", INVISIBLE_APPLIES), "I5"),
        ("while hidden.", "F", ("hide_check", INVISIBLE_APPLIES), "I5"),
        ("(Perception) check.", "F", ("hide_discovery_dc", PERCEPTION_VS_HIDDEN), "I6"),
        ("stop being hidden", "F", ("hide_end", TERMINATION), "I7"),
        (None, "P", ("hide_end", CTX), "I7"),
    ],
]

# --- Influence -------------------------------------------------------------
SPEC["Influence [Action]"] = [
    W,
    [
        ("gently persuade?", "P", ("influence_attempt", OEE), "J1"),
        (None, "P", ("influence_disposition", GML), "J2"),
    ],
    [(None, "C", "influence_willing", "J3")],  # 'Willing.'
    [(None, "P", ("influence_willing", OEE), "J3")],
    [(None, "C", "influence_unwilling", "J4")],  # 'Unwilling.'
    [(None, "P", ("influence_unwilling", CTX), "J4")],
    [(None, "C", "influence_check", "J6")],  # 'Hesitant.'
    [
        ("an ability check,", "F", ("influence_check", INFLUENCE_CHECK), "J6"),
        ("attitude:", "C", "influence_check", "J5"),
        (
            " Indifferent,",
            "X",
            ("Indifferent", "attitude.indifferent", "influence_check"),
            "J5",
        ),
        (" Friendly,", "X", ("Friendly", "attitude.friendly", "influence_check"), "J5"),
        ("Hostile,", "X", ("Hostile", "attitude.hostile", "influence_check"), "J5"),
        ("this glossary.", "C", "influence_check", "J5"),
        # The table suggests and the GM chooses: both are the source delegating
        # the decision, which is the one reason this component carries.
        ("with the monster.", "P", ("influence_check", GML), "J7"),
        ("chooses the check,", "P", ("influence_check", GML), "J8"),
        ("whichever is higher.", "F", ("influence_check", INFLUENCE_CHECK), "J9"),
        ("does as urged.", "P", ("influence_success", OEE), "J10"),
        ("On a failed check,", "Q", ("influence_check", RETRY_24H), "J11"),
        ("same way again.", "F", ("influence_check", RETRY_24H), "J11"),
        (None, "C", "influence_check", "J7"),  # ' Influence Checks' (table title)
    ],
    # The Influence Checks table: exemplars and guidance, not an exhaustive
    # actor list. Supporting authority owned by the check component; the
    # governing sentences J7 and J8 keep their prose bindings above.
    *[[(None, "C", "influence_check", "J7")] for _ in range(12)],
]

# --- Magic -----------------------------------------------------------------
SPEC["Magic [Action]"] = [
    W,
    [
        ("of an action", "F", ("magic_activation", AE_ACTION), "K1"),
        # "a feature or magic item that requires a Magic action" - the effect
        # space of what such a feature does is the whole of the game's features.
        (None, "P", ("magic_activation", OEE), "K1"),
    ],
    [
        ("of that casting,", "F", ("magic_long_casting", RECUR_ACTION_PER_TURN), "K2"),
        ("while you do so.", "F", ("magic_long_casting", SUST_CONC), "K3"),
        ("is broken,", "A", "magic_concentration_break", "K4"),
        ("the spell fails,", "F", ("magic_concentration_break", TERMINATION), "K4"),
        (None, "F", ("magic_concentration_break", NO_SLOT_EXPENDED), "K4"),
    ],
    [(None, "R", None, "K5")],  # 'See also'
    [(None, "X", ("Concentration", "glossary.concentration"), "K5")],
]

# --- Ready -----------------------------------------------------------------
SPEC["Ready [Action]"] = [
    W,
    [
        ("before you act.", "C", "ready_action", "L1"),
        ("on your turn,", "F", ("ready_action", AE_ACTION), "L1"),
        # The grant is what both response arms spend, so both option facts are
        # grounded here CONTEXTUALLY rather than claiming a second PRIMARY.
        (
            "taking a Reaction",
            "F",
            ("ready_reaction_grant", REACTION_GRANT),
            "L2",
            (
                ("f", ("ready_response", AE_REACTION, "chosen_action")),
                ("f", ("ready_response", AE_REACTION, "move_up_to_speed")),
            ),
        ),
        ("your next turn.", "F", ("ready_reaction_grant", DUR_START_TURN), "L2"),
        ("your Reaction.", "P", ("ready_trigger", OEE), "L3"),
        ("to that trigger,", "P", ("ready_response", OEE, "chosen_action"), "L4"),
        ("in response to it.", "F", ("ready_response", MOVE_OWN, "move_up_to_speed"), "L4"),
        (None, "C", "ready_trigger", "L5"),
    ],
    [
        (f"I move away.{RSQ}", "C", "ready_trigger", "L5"),
        ("ignore the trigger.", "F", ("ready_resolution", TRIGGER_RESOLUTION), "L6"),
        ("used to cast it)", "F", ("ready_spell", CASTING_RESOURCES_SPENT), "L7"),
        ("the trigger occurs.", "C", "ready_spell", "L7"),
        ("casting time of an action,", "C", "ready_spell", "L8"),
        ("requires Concentration,", "F", ("ready_spell", SUST_CONC), "L9"),
        ("your next turn.", "F", ("ready_spell", DUR_START_TURN), "L9"),
        ("is broken,", "A", "ready_concentration_break", "L10"),
        (None, "F", ("ready_concentration_break", TERMINATION), "L10"),
    ],
]

# --- Search ----------------------------------------------------------------
SPEC["Search [Action]"] = [
    W,
    [
        ("a Wisdom check", "F", ("search_check", SEARCH_CHECK), "M1"),
        ("obvious.", "P", ("search_check", SUBJ), "M2"),
        ("trying to detect.", "P", ("search_check", SUBJ), "M3"),
        (None, "C", "search_check", "M3"),  # ' Search' (table title)
    ],
    *[[(None, "C", "search_check", "M3")] for _ in range(10)],
]

# --- Study -----------------------------------------------------------------
SPEC["Study [Action]"] = [
    W,
    [
        ("an Intelligence check", "F", ("study_check", STUDY_CHECK), "N1"),
        ("information about it.", "P", ("study_check", OEE), "N1"),
        (None, "P", ("study_areas", SUBJ), "N2"),
    ],
    *[[(None, "C", "study_areas", "N2")] for _ in range(13)],
]

# --- Utilize ---------------------------------------------------------------
SPEC["Utilize [Action]"] = [
    W,
    [
        ("the Attack action.", "C", "utilize_action", "O1"),
        ("for its use,", "F", ("utilize_action", OBJECT_NEEDS_ACTION), "O2"),
        (None, "F", ("utilize_action", AE_ACTION), "O2"),
    ],
]

#: The discovery ledger's obligation ids, in full. Every one must be discharged
#: by at least one span, and no span may name an id that is not here. `I8` is
#: absent from the source ledger and is deliberately not invented.
OBLIGATION_IDS = [
    *[f"A{i}" for i in range(1, 5)],
    *[f"B{i}" for i in range(1, 8)],
    *[f"D{i}" for i in range(1, 9)],
    *[f"E{i}" for i in range(1, 4)],
    *[f"G{i}" for i in range(1, 8)],
    *[f"H{i}" for i in range(1, 8)],
    *[f"I{i}" for i in [1, 2, 3, 4, 5, 6, 7, 9, 10]],
    *[f"J{i}" for i in range(1, 12)],
    *[f"K{i}" for i in range(1, 6)],
    *[f"L{i}" for i in range(1, 11)],
    *[f"M{i}" for i in range(1, 4)],
    *[f"N{i}" for i in range(1, 3)],
    *[f"O{i}" for i in range(1, 3)],
]
assert len(OBLIGATION_IDS) == len(set(OBLIGATION_IDS)) == 78, len(OBLIGATION_IDS)

# ---------------------------------------------------------------------------
# Emission
# ---------------------------------------------------------------------------

spans: list[SemanticSpan] = []
proposed: list[ProposedSpan] = []
provenance: list[ProvenanceClaim] = []
references: list[ReferenceDraft] = []
prose_bindings: list[ProseBindingDraft] = []
comp_facts: dict[tuple[str, str], list] = defaultdict(list)
opt_facts: dict[tuple[str, str, str], list] = defaultdict(list)
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
        "names, frames, limits, or exemplifies what a component states; supporting "
        "authority owned by that component"
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
        "states when its component applies, or which axis of an actor choice the "
        "component offers; the owning component is the element that carries the "
        "claim, because no single option states it"
    ),
    "Q": (
        "states the condition on one fact of a component that its siblings do not "
        "share; carried by that fact's own qualifier"
    ),
    "P": (
        "affirmatively irreducible under a closed reason code: the predicate "
        "ranges over fiction the projection cannot enumerate, or the effect space "
        "is unbounded, and whatever mechanic it governs is typed beside it"
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


def _fact_arg(arg: tuple) -> tuple[str, object, str]:
    """`(comp, fact)` or `(comp, fact, option_key)`, normalized."""
    return (arg[0], arg[1], arg[2] if len(arg) > 2 else "")


def _add_fact(rkey: str, comp: str, fact: object, option: str) -> None:
    """Hold each distinct fact once per owner, however many spans state it."""
    bucket = opt_facts[(rkey, comp, option)] if option else comp_facts[(rkey, comp)]
    key = fact_key(fact)
    if all(fact_key(f) != key for f in bucket):
        bucket.append(fact)


def _fact_edge(
    rkey: str, arg: tuple, sid: str, role: ProvenanceRole
) -> ProvenanceClaim:
    comp, fact, option = _fact_arg(arg)
    _add_fact(rkey, comp, fact, option)
    return ProvenanceClaim(
        ProvenanceTargetKind.FACT,
        fact_target_key(rkey, comp, fact, option),
        sid,
        role,
    )


ORIGIN = "issue-5d-actions-1-schema6-PROPOSAL-generator.py"
leaf_content: dict[str, str] = {}
obligation_spans: dict[str, list[str]] = defaultdict(list)
extra_edges = 0

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
        for seg in segs:
            marker, kind, arg, obligation = seg[:4]
            extras = seg[4] if len(seg) > 4 else ()
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
            if obligation is not None:
                assert obligation in OBLIGATION_IDS, obligation
                obligation_spans[obligation].append(sid)

            if kind in ("F", "Q"):
                _c, _f, _o = _fact_arg(arg)
                claimant = f"{rkey}/{_c}{('#' + _o) if _o else ''}/{fact_key(_f)}"
            elif kind in ("C", "A"):
                claimant = f"{rkey}/{arg}"
            elif kind == "P":
                _o = arg[2] if len(arg) > 2 else ""
                claimant = f"{rkey}/{arg[0]}{('#' + _o) if _o else ''} ({arg[1]})"
            elif kind == "X":
                claimant = f"{rkey} -> {arg[1]}"
            else:
                claimant = rkey
            audit.append(
                {
                    "record": rkey,
                    "obligation": obligation,
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
                    "also_grounds": [
                        (
                            f"{rkey}/{e[1]}"
                            if e[0] == "c"
                            else "{}/{}{}/{}".format(
                                rkey,
                                _fact_arg(e[1])[0],
                                ("#" + _fact_arg(e[1])[2])
                                if _fact_arg(e[1])[2]
                                else "",
                                fact_key(_fact_arg(e[1])[1]),
                            )
                        )
                        for e in extras
                    ],
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
                text, target = arg[0], arg[1]
                owner = arg[2] if len(arg) > 2 else RECORD_OWNED_REFERENCE
                ref = ReferenceDraft(
                    from_record_key=rkey,
                    from_component_key=owner,
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
                provenance.append(
                    _fact_edge(rkey, arg, sid, ProvenanceRole.PRIMARY)
                )
            elif kind == "Q":
                comp, fact, option = _fact_arg(arg)
                provenance.append(
                    ProvenanceClaim(
                        ProvenanceTargetKind.FACT_QUALIFIER,
                        fact_qualifier_target_key(rkey, comp, fact_key(fact), option),
                        sid,
                        ProvenanceRole.PRIMARY,
                    )
                )
            elif kind == "P":
                comp, reason = arg[0], arg[1]
                option = arg[2] if len(arg) > 2 else ""
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
                    option_key=option,
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

            for ekind, earg in extras:
                extra_edges += 1
                if ekind == "f":
                    provenance.append(
                        _fact_edge(rkey, earg, sid, ProvenanceRole.CONTEXTUAL)
                    )
                elif ekind == "c":
                    provenance.append(
                        ProvenanceClaim(
                            ProvenanceTargetKind.COMPONENT,
                            (rkey, earg),
                            sid,
                            ProvenanceRole.CONTEXTUAL,
                        )
                    )
                else:  # pragma: no cover - guarded by the table above
                    raise AssertionError(f"unknown extra kind {ekind!r}")

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
        options=tuple(
            ComponentOption(
                semantic_key=okey, facts=tuple(opt_facts[(rkey, ckey, okey)])
            )
            for okey in spec.get("options", ())
        ),
        fact_qualifiers=spec.get("fact_qualifiers", ()),
        recurs=spec.get("recurs"),
    )
    for (rkey, ckey), spec in COMPONENTS.items()
)
#: No component may be declared and then left empty by the clause table, and no
#: declared option may end up with no fact of its own.
for _c in components:
    assert _c.facts or _c.options or _c.handling is ComponentHandling.PROSE_BOUND, _c
    for _o in _c.options:
        assert _o.facts, f"{_c.record_key}/{_c.semantic_key}#{_o.semantic_key} is empty"
#: Every fact this run emits satisfies its own invariants before any collection
#: level rule is run, so a constructor mistake fails here and not as a confusing
#: downstream finding.
for _c in components:
    for _f in (*_c.facts, *(of for o in _c.options for of in o.facts)):
        assert not fact_invariant_violations(_f), (
            f"{_c.record_key}/{_c.semantic_key}",
            type(_f).__name__,
            fact_invariant_violations(_f),
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
    "records": (len(records), 13),
    "represented_leaves": (len(touched), 92),
    "policy_exclusions": (len(POLICY_EXCLUDED), 2),
    "container_leaves": (len(touched) + len(POLICY_EXCLUDED), 94),
}
CANARY_MISMATCH = {k: v for k, v in CANARIES.items() if v[0] != v[1]}
assert not CANARY_MISMATCH, (
    "the bound source no longer yields the recorded boundary; stop and explain "
    f"rather than adjusting the batch: {CANARY_MISMATCH}"
)

# --- The classification partition, reconstructed rather than trusted --------
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

# --- Obligation closure, derived from the emitted spans ---------------------
OBLIGATION_CLOSURE = {
    oid: {
        "spans": obligation_spans[oid],
        "claimants": sorted(
            {a["claimant"] for a in audit if a["obligation"] == oid}
        ),
        "dispositions": sorted(
            {a["disposition"] for a in audit if a["obligation"] == oid}
        ),
        "text": [a["text"] for a in audit if a["obligation"] == oid],
    }
    for oid in OBLIGATION_IDS
}
_open_obligations = [oid for oid in OBLIGATION_IDS if not obligation_spans[oid]]
assert not _open_obligations, f"obligations with no span: {_open_obligations}"
_unknown = sorted(set(obligation_spans) - set(OBLIGATION_IDS))
assert not _unknown, f"spans naming an obligation the ledger does not have: {_unknown}"

# --- Merged verification, exactly the shape acceptance would validate -------
#
# `validate_representation` is only ever called on the post-merge candidate
# (`projection.build_candidate_findings`), never on a proposal's draft in
# isolation. Reproducing that merge here - without accepting anything - is what
# shows which findings are cross-batch and which are this batch's own.
#
# The review prior is READ ONLY and frozen; the live oracle is READ ONLY and is
# only a sentinel. Nothing here writes either, and the lift is verified rather
# than applied.
def _review_prior_identifiers() -> tuple[str, str, str]:
    """The review prior's raw, canonical, and Git identities."""
    raw = REVIEW_PRIOR_PATH.read_bytes()
    canonical = raw.replace(b"\r\n", b"\n")
    blob = hashlib.sha1(  # noqa: S324 - Git's object id, not a security digest
        b"blob " + str(len(canonical)).encode() + b"\x00" + canonical
    ).hexdigest()
    return (
        hashlib.sha256(raw).hexdigest(),
        hashlib.sha256(canonical).hexdigest(),
        blob,
    )


(
    _prior_raw_before,
    _prior_content_before,
    _prior_blob_before,
) = _review_prior_identifiers()
assert _prior_content_before == REVIEW_PRIOR_CONTENT_SHA256, _prior_content_before
assert _prior_blob_before == REVIEW_PRIOR_BLOB, _prior_blob_before

_LIVE_ORACLE_BYTES_BEFORE = LIVE_ORACLE_PATH.read_bytes()

PRIOR = load_accepted_inputs(REVIEW_PRIOR_PATH)
assert [b.batch_id for b in PRIOR.batches] == REVIEW_PRIOR_BATCH_IDS, PRIOR.batches
assert {a.batch_id for a in PRIOR.acceptances} == set(REVIEW_PRIOR_BATCH_IDS)
assert (
    PRIOR.oracle.schema_version == REVIEW_PRIOR_SCHEMA_VERSION
), PRIOR.oracle.schema_version
STEPS = lift_path((PRIOR.oracle.schema_version, PRIOR.oracle.schema_hash), SCHEMA)
LIFT_RECORDS = verify_lift_path(STEPS, PRIOR.oracle.representation)
assert [r.lift_id for r in LIFT_RECORDS] == ["5d-lift-schema-5-to-6"], LIFT_RECORDS

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
#
# This is the honest limit of the batch, named precisely rather than softened.
# Unlike hazards-1 - whose one cross-batch citation resolved into already
# accepted conditions-1 authority - none of these five targets exists yet in
# any accepted batch. So the merged column is NOT empty, and this batch is not
# publishable until the glossary and attitude batches land.
UNRESOLVED_EXPECTED = {
    (DASH, "glossary.speed"),
    (MAGI, "glossary.concentration"),
    (INFL, "attitude.friendly"),
    (INFL, "attitude.hostile"),
    (INFL, "attitude.indifferent"),
}
_batch_records = {rec.semantic_key for rec in records}
_cross_batch = {
    (r.from_record_key, r.target_record_key)
    for r in references
    if r.target_record_key not in _batch_records
}
assert _cross_batch == UNRESOLVED_EXPECTED, _cross_batch
_prior_records = {r.semantic_key for r in PRIOR.oracle.representation.records}
_still_missing = sorted(t for _f, t in _cross_batch if t not in _prior_records)
assert _still_missing == sorted(t for _f, t in UNRESOLVED_EXPECTED), _still_missing
UNRESOLVED = {
    "expected_missing_targets": sorted(
        f"{f} -> {t}" for f, t in sorted(_cross_batch)
    ),
    "standalone_findings": standalone,
    "merged_findings": merged_findings,
    "resolved_by_the_accepted_prior": [],
    "still_missing_after_the_merge": _still_missing,
    "publishable_alone": False,
    "note": (
        "Every one of the five targets is absent from this batch AND from the "
        "accepted conditions-1 + hazards-1 prior, so the standalone and merged "
        "finding sets are identical and non-empty. glossary.speed and "
        "glossary.concentration belong to a later glossary batch; "
        "attitude.friendly, attitude.hostile and attitude.indifferent belong to "
        "the monster-attitude batch. This batch is material for semantic "
        "review, not a publishable unit."
    ),
}
#: Set equality on both columns, not a count. A finding that happened to be
#: about something else would have to coincide with one of these five strings.
_expected_finding_targets = sorted(t for _f, t in _cross_batch)
for _column, _found in (("standalone", standalone), ("merged", merged_findings)):
    assert len(_found) == len(_expected_finding_targets), (_column, _found)
    for _target in _expected_finding_targets:
        assert any(_target in f for f in _found), (_column, _target, _found)

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
        return (element.from_record_key, element.to_record_key, element.kind.value)
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

# --- Schema-6 legality at every authority-bearing seam ----------------------
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
    _component_rules.extend(option_set_violations(_c.facts, _c.options, _tag))

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
    "schema-6 component rules (damage + roll outcome + option sets)": len(
        _component_rules
    ),
    "declared schema binding (schema_binding_violations)": len(schema_binding),
    "representation gate, standalone (validate_representation)": len(standalone),
    "representation gate, merged with accepted conditions-1 + hazards-1": len(
        merged_findings
    ),
    "committed-loader round trip (representation_payload -> _representation)": (
        0 if WIRE_ROUND_TRIP else 1
    ),
}
SEAMS_THAT_RAISE = {
    "acceptance merge (_merge_representation)": {"raised": False},
    "succession (lift_path + verify_lift_path, 5 -> 6)": {
        "raised": False,
        "steps": [r.lift_id for r in LIFT_RECORDS],
    },
    "proposal identity (proposal_payload + proposal_identity)": {"raised": False},
}
#: The two seams that are expected to be non-silent, and why. Both report
#: exactly the five cross-batch citations enumerated above - the standalone
#: column because a draft is never validated alone in production, and the
#: merged column because the targets do not exist in accepted authority yet.
_EXPECTED_NONZERO = {
    "representation gate, standalone (validate_representation)",
    "representation gate, merged with accepted conditions-1 + hazards-1",
}
for _seam in _EXPECTED_NONZERO:
    assert SEAMS[_seam] == len(_cross_batch) == 5, (SEAMS, _seam)
assert all(v == 0 for k, v in SEAMS.items() if k not in _EXPECTED_NONZERO), SEAMS
assert not _component_rules, _component_rules

# --- Shape claims this batch must satisfy by construction -------------------
_comp = {(c.record_key, c.semantic_key): c for c in components}
SHAPE_CLAIMS = {
    "no_component_holds_both_facts_and_options": [
        f"{c.record_key}/{c.semantic_key}" for c in components if c.facts and c.options
    ],
    "no_detached_or_ambiguous_roll_outcome": _component_rules,
    "structured_components_carry_no_prose_or_reason": [
        f"{c.record_key}/{c.semantic_key}"
        for c in components
        if c.handling is ComponentHandling.STRUCTURED
        and (
            c.irreducibility_reason_code is not None
            or any(
                (b.record_key, b.component_key) == (c.record_key, c.semantic_key)
                for b in prose_bindings
            )
        )
    ],
    "prose_bound_components_carry_no_typed_fact": [
        f"{c.record_key}/{c.semantic_key}"
        for c in components
        if c.handling is ComponentHandling.PROSE_BOUND
        and (c.facts or any(o.facts for o in c.options))
    ],
    "every_non_structured_component_has_bound_prose": [
        f"{c.record_key}/{c.semantic_key}"
        for c in components
        if c.handling is not ComponentHandling.STRUCTURED
        and not any(
            (b.record_key, b.component_key) == (c.record_key, c.semantic_key)
            for b in prose_bindings
        )
    ],
    "every_prose_binding_agrees_with_its_component": [
        f"{b.record_key}/{b.component_key}"
        for b in prose_bindings
        if _comp[(b.record_key, b.component_key)].irreducibility_reason_code
        != b.irreducibility_reason_code
    ],
    "option_grain_prose_bindings": sorted(
        f"{b.record_key}/{b.component_key}#{b.option_key}"
        for b in prose_bindings
        if b.option_key
    ),
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
for _claim in (
    "no_component_holds_both_facts_and_options",
    "no_detached_or_ambiguous_roll_outcome",
    "structured_components_carry_no_prose_or_reason",
    "prose_bound_components_carry_no_typed_fact",
    "every_non_structured_component_has_bound_prose",
    "every_prose_binding_agrees_with_its_component",
):
    assert not SHAPE_CLAIMS[_claim], (_claim, SHAPE_CLAIMS[_claim])
for _row in SHAPE_CLAIMS["roll_outcome_scopes"]:
    assert _row["rolls_established_in_scope"] == 1, _row
assert SHAPE_CLAIMS["roll_outcome_scopes"], "no roll-outcome scope was exercised"
assert SHAPE_CLAIMS["option_grain_prose_bindings"], "no option-grain binding emitted"

# --- Sibling components holding an equivalent fact --------------------------
# `_validate_duplicated_fact_authority` requires all three of different
# components, an equivalent fact key, AND a shared substantive span. Stated in
# the artifact rather than left as a code comment.
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
            "legal: two rules state the same mechanic from different spans; the "
            "refusal requires a SHARED substantive span and there is none"
        ),
    }
    for (_rk, _fk), _holders in sorted(_by_record_fact.items())
    if len(_holders) > 1
]
for _pair in SIBLING_PAIRS:
    assert not _pair["shares_a_substantive_span"], _pair

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
    "spans_carrying_more_than_one_claim": sorted(
        {
            _text_of[sid]: len(cls) for sid, cls in _by_span.items() if len(cls) > 1
        }.items()
    ),
    "extra_contextual_edges": extra_edges,
}
assert (
    OWNERSHIP["substantive_with_exactly_one_primary_claimant"]
    == OWNERSHIP["substantive_spans"]
), OWNERSHIP
assert OWNERSHIP["supporting_spans_carrying_a_primary_claim"] == 0, OWNERSHIP
assert OWNERSHIP["prose_bindings_over_supporting_text"] == 0, OWNERSHIP
assert OWNERSHIP["spans_with_no_claim_at_all"] == 0, OWNERSHIP

# --- Schema-6 structures demonstrated, derived from the emitted draft --------
_sites: dict[str, list[str]] = defaultdict(list)
for _c in components:
    _at = f"{_c.record_key}/{_c.semantic_key}"
    if _c.options:
        _sites["actor choice (ComponentOption)"].append(_at)
    if _c.applies_when is not None:
        _sites[f"applicability ({_c.applies_when.kind.value})"].append(_at)
        for _t in _c.applies_when.any_of_terms:
            _sites[f"any_of term ({_t.kind.value})"].append(_at)
    for _q in _c.fact_qualifiers:
        _sites[f"fact qualifier ({_q.applies_when.kind.value})"].append(_at)
for _b in prose_bindings:
    if _b.option_key:
        _sites["option-grain prose binding"].append(
            f"{_b.record_key}/{_b.component_key}#{_b.option_key}"
        )
SCHEMA6_STRUCTURES = {k: sorted(set(v)) for k, v in sorted(_sites.items())}
for _needed in (
    "actor choice (ComponentOption)",
    "applicability (any_of)",
    "any_of term (condition_state)",
    "any_of term (obscurement)",
    "any_of term (cover)",
    "applicability (effect_state)",
    "option-grain prose binding",
):
    assert SCHEMA6_STRUCTURES.get(_needed), f"{_needed} is exercised nowhere"

# --- Substantive judgment changes from discovery ----------------------------
# Named because the Owner asked for them, and stated as reasons rather than as
# a diff of counts. The discovery ledger was a first pass over the source; it is
# evidence, not a target.
JUDGMENT_CHANGES = [
    {
        "id": "JC-1",
        "what": "reference source_text is the bare name, with no trailing period",
        "was": 'the checkpoint wrote "Speed." / "Concentration." with the period',
        "now": "'Speed', 'Concentration', 'Indifferent', 'Friendly', 'Hostile'",
        "why": (
            "the accepted conditions-1 + hazards-1 prior settles the convention: "
            "every one of its 22 references carries a bare name. A citation names "
            "a rule; the punctuation belongs to the sentence, not to the name."
        ),
    },
    {
        "id": "JC-2",
        "what": "the Influence, Search and Study table cells are supporting authority",
        "was": "the discovery ledger dispositioned the cells as prose-bound (P)",
        "now": "supporting authority owned by the component the table serves (C)",
        "why": (
            "the Owner's clarification that suggested skill/ability tables are "
            "exemplars and guidance, read against SUPPORTING_AUTHORITY's own "
            "definition - identifies, limits, explains, exemplifies, or "
            "contextualizes. The governing sentences (J7, J8, M3, N2) keep their "
            "prose bindings, so nothing that governs play was demoted; what moved "
            "is the exemplar rows the sentences point at."
        ),
    },
    {
        "id": "JC-3",
        "what": "J10 is prose-bound rather than a typed outcome gate",
        "was": "typed + prose (T+P) under a ROLL_OUTCOME applicability",
        "now": "PROSE_BOUND under open_ended_effect",
        "why": (
            "a ROLL_OUTCOME applicability requires exactly one roll-establishing "
            "fact in the component's scope. A component that publishes no fact "
            "establishes none, so the gate would name the outcome of nothing. The "
            "effect - a monster doing as urged - is unbounded anyway."
        ),
    },
    {
        "id": "JC-4",
        "what": "B2 is supporting authority, not a cross-reference",
        "was": "cross-reference (X)",
        "now": "supporting authority owned by attack_allowance (C)",
        "why": (
            "'with a weapon or an Unarmed Strike' names no glossary record this "
            "batch can resolve; it identifies and limits the instrument of the "
            "attack the component already grants."
        ),
    },
    {
        "id": "JC-5",
        "what": "Help carries one irreducibility reason for both arms",
        "was": "H5 dispositioned toward gamemaster_latitude",
        "now": "the component carries contextual_applicability (residue R-help-reason)",
        "why": (
            "an option set cannot span components and a component holds exactly "
            "one reason. contextual_applicability is true of H5 - whether the "
            "assistance applies depends on fiction the projection cannot "
            "enumerate - and only less specific. A coarsening, recorded rather "
            "than hidden; not a falsehood, so not a stop."
        ),
    },
    {
        "id": "JC-6",
        "what": "Dodge is three components, including a standalone duration",
        "was": "one benefits component",
        "now": "dodge_attack_disadvantage, dodge_saving_throws, dodge_duration",
        "why": (
            "one duration governs two benefits. Duplicating the duration fact "
            "across both would place an equivalent fact of two components on one "
            "substantive span, which the duplicated-authority rule refuses. And "
            "only the attack benefit carries a prose condition, while a component "
            "holds one reason."
        ),
    },
    {
        "id": "JC-7",
        "what": "Study splits into study_check and study_areas",
        "was": "one component",
        "now": "two, by reason",
        "why": (
            "N1's effect space is unbounded (open_ended_effect) while N2 is a "
            "judgement call about which skill applies (subjective_judgment). Two "
            "reasons cannot live in one component."
        ),
    },
    {
        "id": "JC-8",
        "what": "Utilize is fully structured",
        "was": "mixed, with a prose binding",
        "now": "STRUCTURED, no reason code, no binding",
        "why": (
            "'when an object requires an action for its use' is exactly "
            "ActivationCostEligibilityFact and 'you take the Utilize action' is "
            "exactly ActionEconomyFact. Nothing in the entry is irreducible, and "
            "a reason code invented to justify a binding would be false."
        ),
    },
    {
        "id": "JC-9",
        "what": "the 13 heading leaves are represented, not policy-excluded",
        "was": "carried forward as the expected policy exclusions",
        "now": (
            "the two policy exclusions are the running header/footer leaves on "
            "the Help and Ready pages; the headings carry whole-leaf supporting "
            "authority exactly as in hazards-1"
        ),
        "why": "re-derived from `exclusion_reason_for` against the bound ledger",
    },
]

DISCLOSED_LIMITS = [
    {
        "id": "L-1",
        "where": "action.attack/attack_equipment_change",
        "limit": (
            "EquipmentChangeFact carries change and timing in one fact, while the "
            "source states the two axes in two separate sentences. The option set "
            "is therefore the cross product of the two axes, and no single span "
            "states any one of the four combinations."
        ),
        "how_it_is_accounted": (
            "Each axis sentence is claimed PRIMARY by the owning component - the "
            "element that holds the choice - and each of the four option facts "
            "takes a CONTEXTUAL edge on both axis spans. Nothing is invented and "
            "nothing is dropped; what is disclosed is that the typed shape is "
            "more specific than any one span of the source."
        ),
        "not_a_stop_because": (
            "the cross product is entailed by the two sentences read together, so "
            "no schema meaning is changed and no claim is made that the source "
            "does not support."
        ),
    },
    {
        "id": "R-help-reason",
        "where": "action.help/help_choice",
        "limit": (
            "H5 ('The GM has final say on whether your assistance is possible') "
            "would take gamemaster_latitude on its own; the component carries "
            "contextual_applicability, which both other bindings need."
        ),
        "how_it_is_accounted": (
            "carried as residue rather than resolved by demoting H5 to supporting "
            "authority (it is substantive) or by a sibling PROSE_BOUND component "
            "(which would falsely claim to govern both arms - no ApplicabilityKind "
            "can scope a component to one arm of a choice)"
        ),
        "not_a_stop_because": (
            "contextual_applicability is true of H5, only less specific. A "
            "coarsening of a label, not a false statement about the rule."
        ),
    },
]

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
        f"{ORIGIN} (CRD Issue 5d batch actions-1, representation schema 6)"
    ),
)
payload = proposal_payload(PROPOSAL)
ident = proposal_identity(PROPOSAL)
#: No pinned expectation: this is a *fresh* proposal, so its identity is
#: reported for review rather than asserted against a value chosen in advance.
#: What is asserted is that it is not the superseded schema-1 artifact.
assert ident != SUPERSEDED_IDENTITY, "the new proposal is the superseded one"

counts: dict[str, int] = defaultdict(int)
for s in spans:
    counts[s.disposition.value] += 1
per_record: dict[str, dict] = defaultdict(lambda: {"leaves": set(), "spans": 0})
for a in audit:
    rec = per_record[a["record"]]
    rec["leaves"].add(a["leaf"])
    rec["spans"] += 1

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
    "components_with_options": sum(1 for c in components if c.options),
    "options": sum(len(c.options) for c in components),
    "facts": sum(
        len(c.facts) + sum(len(o.facts) for o in c.options) for c in components
    ),
    "component_grain_facts": sum(len(c.facts) for c in components),
    "option_grain_facts": sum(
        len(o.facts) for c in components for o in c.options
    ),
    "fact_qualifiers": sum(len(c.fact_qualifiers) for c in components),
    "prose_bindings": len(prose_bindings),
    "option_grain_prose_bindings": sum(1 for b in prose_bindings if b.option_key),
    "references": len(references),
    "record_owned_references": sum(
        1 for r in references if r.from_component_key == RECORD_OWNED_REFERENCE
    ),
    "relationships": 0,
    "provenance_edges": len(provenance),
    "extra_contextual_edges": extra_edges,
    "obligations": len(OBLIGATION_IDS),
}
assert COUNTS["spans"] == len(audit) == len(proposed), COUNTS
assert COUNTS["provenance_edges"] == len(spans) + extra_edges, COUNTS
assert (
    COUNTS["substantive"]
    + COUNTS["supporting_authority"]
    + COUNTS["non_mechanical"]
    + COUNTS["unresolved"]
    == COUNTS["spans"]
), COUNTS
assert COUNTS["references"] == 17, COUNTS

COUNT_DERIVATION = {
    "records": (
        "one per source entry in the boundary: the Action umbrella plus the "
        "twelve [Action] entries"
    ),
    "represented_leaves": (
        "distinct leaf ids the spans cover; 92 of the boundary's 94 container "
        "leaves, the other two being the enumerated 5c policy exclusions"
    ),
    "spans": (
        "one per segment of the run-time cut; the segments of each leaf "
        "reconstruct it byte for byte"
    ),
    "substantive": "F + A + Q + P segments",
    "supporting_authority": "R + C + X segments",
    "facts": (
        "distinct fact keys per owner, counting option-grain facts; a fact stated "
        "by several spans is held once"
    ),
    "provenance_edges": (
        "one claim per span, plus the enumerated CONTEXTUAL extras that ground a "
        "shared statement without minting a second PRIMARY"
    ),
    "obligations": (
        "the discovery ledger's own ids; I8 is absent there and is not invented "
        "here. Every one is discharged by at least one emitted span."
    ),
    "relation_to_the_superseded_schema_1_artifact": (
        "Deliberately not tabulated. The superseded proposal was authored under "
        "representation schema 1, before options, ANY_OF, condition/effect state, "
        "obscurement and cover existed, so a count-by-count diff would compare "
        "two different vocabularies and invite the older numbers to act as "
        "targets. It is named only to prove this proposal is not it."
    ),
}

AUDIT_DOC = {
    "_": (
        "CRD Issue 5d batch actions-1, representation schema 6. Proposal and "
        "audit only: nothing accepted, published, activated or retired. Zero "
        "validator findings would be necessary and insufficient - and this batch "
        "does not even have zero: it cites five records no accepted batch "
        "defines, so it is explicitly NOT publishable on its own."
    ),
    "proposal_identity": ident,
    "identity_is_pinned": False,
    "superseded_predecessor": {
        "identity": SUPERSEDED_IDENTITY,
        "schema": "5d-representation-schema-1",
        "artifact": "issue-5d-batch-actions-1-PROPOSAL.json",
        "differs": ident != SUPERSEDED_IDENTITY,
        "use": (
            "historical evidence only. Its payload was not imported, edited, "
            "translated, restamped, cloned, or read as generator input; this "
            "proposal is derived from the bound source."
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
        "container_leaves": len(touched) + len(POLICY_EXCLUDED),
        "policy_exclusions": POLICY_EXCLUSION_DETAIL,
        "canaries": {
            k: {"derived": v[0], "expected": v[1]} for k, v in CANARIES.items()
        },
        "derivation": (
            "the source's own [Action] entry class under Rules Definitions plus "
            "the umbrella Action glossary rule; the twelve names are re-checked "
            "against the umbrella's own printed list"
        ),
    },
    "counts": COUNTS,
    "count_derivation": COUNT_DERIVATION,
    "per_record": {
        r: {"leaves": len(d["leaves"]), "spans": d["spans"]}
        for r, d in sorted(per_record.items())
    },
    "record_shapes": {
        f"{c.record_key}/{c.semantic_key}": {
            "handling": c.handling.value,
            "irreducibility_reason_code": c.irreducibility_reason_code,
            "facts": [type(f).__name__ for f in c.facts],
            "options": {
                o.semantic_key: [type(f).__name__ for f in o.facts] for o in c.options
            },
            "applies_when": (
                None if c.applies_when is None else c.applies_when.kind.value
            ),
            "applies_when_negated": (
                None if c.applies_when is None else c.applies_when.negated
            ),
            "fact_qualifiers": [q.applies_when.kind.value for q in c.fact_qualifiers],
        }
        for c in components
    },
    "validation": {
        "partition": partition,
        "structural": STRUCTURAL,
        "component_rules_schema_6": _component_rules,
        "wire_round_trip": WIRE_ROUND_TRIP,
        "reason_codes": reason_codes,
        "schema_binding": schema_binding,
        "representation_standalone": standalone,
        "representation_merged_with_accepted_prior": merged_findings,
        "seams_reporting_findings": SEAMS,
        "seams_that_answer_by_raising": SEAMS_THAT_RAISE,
        "seams_not_exercised_here": [
            "persistence round trip and override application need a database; "
            "they are covered by the schema-6 test modules on main, not by this "
            "generator, which touches no database by design"
        ],
        "note": (
            "Both representation columns report exactly the five cross-batch "
            "citations, asserted by set equality on the target keys rather than "
            "by count. Unlike hazards-1, the merged column is NOT empty: this "
            "batch is not publishable alone."
        ),
    },
    "classification_partitions": PARTITIONS,
    "cross_batch_references": UNRESOLVED,
    "publishability": {
        "publishable_alone": False,
        "blocked_on": sorted(t for _f, t in _cross_batch),
        "statement": (
            "actions-1 is complete as a batch of its own boundary - every one of "
            "the 92 represented leaves is partitioned and claimed, and every one "
            "of the 78 discovery obligations is discharged - and it is not a "
            "publishable unit, because five source-authored citations point at "
            "records no accepted batch defines yet. Naming that precisely is the "
            "point; calling this batch clean would not be."
        ),
    },
    "disjointness_from_the_accepted_prior": DISJOINT,
    "shape_claims": SHAPE_CLAIMS,
    "sibling_fact_pairs": SIBLING_PAIRS,
    "ownership_integrity": OWNERSHIP,
    "schema_6_structures_demonstrated": SCHEMA6_STRUCTURES,
    "substantive_judgment_changes": JUDGMENT_CHANGES,
    "disclosed_representation_limits": DISCLOSED_LIMITS,
    "obligation_closure": OBLIGATION_CLOSURE,
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
        "review_prior": REVIEW_PRIOR_PATH.relative_to(REPO).as_posix(),
        "review_prior_batch_ids": REVIEW_PRIOR_BATCH_IDS,
        "review_prior_schema_version": REVIEW_PRIOR_SCHEMA_VERSION,
        "review_prior_content_sha256_before": _prior_content_before,
        "review_prior_content_sha256_after": None,  # filled in after the write
        "review_prior_blob_id": _prior_blob_before,
        "review_prior_unchanged": None,
        "review_prior_identity_note": (
            "The frozen conditions-1 + hazards-1 review prior, read only and "
            "unchanged. The live accepted-authority oracle is NOT an input: it "
            "accumulates, so reading it would couple this artifact to authority "
            "accepted later. This run reads it only as a read-only mutation "
            "sentinel - bytes captured before generation and asserted identical "
            "afterwards - and its digest is deliberately not recorded here. The "
            "prior is identified by content, not by the bytes one working copy "
            "holds: .gitattributes declares 'text=auto eol=lf', so the content "
            "digest normalizes CRLF to LF and the blob id is derived from those "
            "same normalized bytes. The raw on-disk digest goes to stdout only."
        ),
        "note": "one registered crossing, 5 -> 6, verified rather than applied",
    },
    "review_disposition": {
        "open_semantic_questions": [],
        "residues": ["R-help-reason"],
        "disclosed_representation_limits": [d["id"] for d in DISCLOSED_LIMITS],
        "statement": (
            "Prepared for semantic review, not recommended for acceptance. "
            "Acceptance is a separate Owner step and is not performed here, and "
            "this batch cannot be published until its five cross-batch citations "
            "have targets."
        ),
    },
    "repository_inputs": INPUT_PATHS,
    "spans": audit,
}

assert AUDIT_DOC["review_disposition"]["open_semantic_questions"] == [], AUDIT_DOC[
    "review_disposition"
]
assert AUDIT_DOC["proposal_identity"] == ident
assert (
    AUDIT_DOC["schema_succession"]["review_prior_content_sha256_before"]
    == REVIEW_PRIOR_CONTENT_SHA256
), AUDIT_DOC["schema_succession"]
assert (
    AUDIT_DOC["schema_succession"]["review_prior_blob_id"] == REVIEW_PRIOR_BLOB
), AUDIT_DOC["schema_succession"]
assert not AUDIT_DOC["publishability"]["publishable_alone"]


def _write_artifact(name: str, document: object, *, sort_keys: bool = False) -> bytes:
    """Write one artifact as UTF-8 with **LF** newlines, and return its bytes.

    ``newline="\n"`` is the whole point. Left to the default, Python translates
    ``\n`` to ``os.linesep`` on write, so the same generator emitted CRLF on
    Windows and LF on Linux - two files, two digests, one computation.
    """
    text = json.dumps(document, indent=1, sort_keys=sort_keys, ensure_ascii=False)
    path = OUT / name
    path.write_text(text, encoding="utf-8", newline="\n")
    written = path.read_bytes()
    assert b"\r\n" not in written, f"{name} was written with CRLF"
    assert b"\r" not in written, f"{name} contains a carriage return"
    return written


_proposal_bytes = _write_artifact(PROPOSAL_FILE, payload, sort_keys=True)

#: Built before the audit is written so that parent and child produce the same
#: final audit, which is what makes a byte comparison a statement about the
#: artifact that ships.
DETERMINISM_SECTION = {
    "procedure": (
        "The parent writes both artifacts in their final form, then re-executes "
        "this generator in a separate process, then compares the final bytes of "
        "both files and asserts the child minted the same proposal identity."
    ),
    "newlines": "LF, written explicitly, on every platform",
    "proposal_sha256": hashlib.sha256(_proposal_bytes).hexdigest(),
    "audit_self_hash": (
        "omitted: an audit cannot state its own final digest without changing "
        "the bytes that digest describes. The run asserts instead that the "
        "parent's and the child's final audits are byte-identical, and reports "
        "the resulting digest to stdout."
    ),
}

_, _prior_content_after, _prior_blob_after = _review_prior_identifiers()
assert _prior_content_after == _prior_content_before, "the review prior changed"
assert _prior_blob_after == _prior_blob_before, "the review prior's blob id moved"
AUDIT_DOC["schema_succession"][
    "review_prior_content_sha256_after"
] = _prior_content_after
AUDIT_DOC["schema_succession"]["review_prior_unchanged"] = (
    _prior_content_after == _prior_content_before == REVIEW_PRIOR_CONTENT_SHA256
    and _prior_blob_after == REVIEW_PRIOR_BLOB
)

AUDIT_DOC["determinism"] = DETERMINISM_SECTION
_audit_bytes = _write_artifact(AUDIT_FILE, AUDIT_DOC)

# Retained evidence, the review prior, and the live oracle must all be
# untouched by this run.
for _n, _before in _RETAINED_BEFORE.items():
    _after = hashlib.sha256((OUT / _n).read_bytes()).hexdigest()
    assert _after == _before, f"retained evidence {_n} changed"
_raw_end, _prior_end, _blob_end = _review_prior_identifiers()
assert _prior_end == _prior_content_before == REVIEW_PRIOR_CONTENT_SHA256, _prior_end
assert _blob_end == _prior_blob_before == REVIEW_PRIOR_BLOB, _blob_end
assert _raw_end == _prior_raw_before, "the review prior's bytes changed"
assert AUDIT_DOC["schema_succession"]["review_prior_unchanged"], AUDIT_DOC[
    "schema_succession"
]

LIVE_ORACLE_UNCHANGED = LIVE_ORACLE_PATH.read_bytes() == _LIVE_ORACLE_BYTES_BEFORE
assert LIVE_ORACLE_UNCHANGED, "this run modified the live accepted-authority oracle"

# ---------------------------------------------------------------------------
# Determinism: a clean rerun must reproduce identical bytes and identity
# ---------------------------------------------------------------------------
RERUN = os.environ.get("ACTIONS6_RERUN") == "1"
FINAL_SHA256 = {
    PROPOSAL_FILE: hashlib.sha256(_proposal_bytes).hexdigest(),
    AUDIT_FILE: hashlib.sha256(_audit_bytes).hexdigest(),
}
DETERMINISTIC: bool | None = None
if not RERUN:
    _child = subprocess.run(
        [sys.executable, str(Path(__file__).resolve())],
        env={**os.environ, "ACTIONS6_RERUN": "1"},
        capture_output=True,
        text=True,
    )
    assert _child.returncode == 0, _child.stderr[-4000:]
    _after_bytes = {
        n: hashlib.sha256((OUT / n).read_bytes()).hexdigest() for n in sorted(WRITES)
    }
    DETERMINISTIC = _after_bytes == FINAL_SHA256
    assert DETERMINISTIC, (FINAL_SHA256, _after_bytes)
    assert ident in _child.stdout, "the rerun minted a different proposal identity"
    for _name in sorted(WRITES):
        assert b"\r" not in (OUT / _name).read_bytes(), f"{_name} came back with CR"

# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

# Absolute paths go to stdout, never into an artifact.
print(f"repo root      {REPO}")
print(f"imported from  {IMPORTED_FROM}")
print(f"source pdf     {SOURCE_PDF}")
print(f"review prior   {REVIEW_PRIOR_PATH}")
print(f"live oracle    {LIVE_ORACLE_PATH}  (sentinel only, not an input)")
print(f"output dir     {OUT}")
print(f"schema         {SCHEMA[0]} / {SCHEMA[1]}")
print(f"policy         {SEMANTIC_POLICY_VERSION} / {semantic_policy_hash()}")
print(f"identity       {ident}")
print(f"superseded     {SUPERSEDED_IDENTITY}  differs={ident != SUPERSEDED_IDENTITY}")
print(f"records        {len(records)}")
print(
    f"leaves         {len(touched)} represented + {len(POLICY_EXCLUDED)} policy "
    f"exclusions = {len(touched) + len(POLICY_EXCLUDED)} container leaves"
)
for _row in POLICY_EXCLUSION_DETAIL:
    print(f"  excluded     {_row['leaf'][:8]} p{_row['printed_page']} {_row['text']!r}")
print(f"spans          {len(spans)}")
for k in ("substantive", "supporting_authority", "non_mechanical", "unresolved"):
    print(f"  {k:22} {counts[k]}")
print(f"components     {len(components)}")
for c in components:
    bits = []
    if c.applies_when is not None:
        neg = "not " if c.applies_when.negated else ""
        bits.append(f"applies_when={neg}{c.applies_when.kind.value}")
    if c.options:
        bits.append("options=" + "|".join(o.semantic_key for o in c.options))
    if c.fact_qualifiers:
        bits.append(f"qualifiers={len(c.fact_qualifiers)}")
    print(
        f"  {c.record_key}/{c.semantic_key}: {c.handling.value}, "
        f"{len(c.facts)} facts, reason={c.irreducibility_reason_code}"
        + (("  " + " ".join(bits)) if bits else "")
    )
print(
    f"facts          {COUNTS['facts']} "
    f"({COUNTS['component_grain_facts']} component + "
    f"{COUNTS['option_grain_facts']} option grain)"
)
print(
    f"prose bindings {len(prose_bindings)} "
    f"({COUNTS['option_grain_prose_bindings']} option grain)"
)
print(
    f"references     {len(references)} "
    f"({COUNTS['record_owned_references']} record owned)"
)
print(f"provenance     {len(provenance)}  ({extra_edges} contextual extras)")
print("relationships  0")
print()
print(f"{'record':24} {'leaves':>6} {'spans':>6}")
for r in sorted(per_record):
    d = per_record[r]
    print(f"{r:24} {len(d['leaves']):6} {d['spans']:6}")
print()
for name, found in (
    ("partition", partition),
    ("structural", STRUCTURAL),
    ("schema-6 component rules", _component_rules),
    ("reason codes", reason_codes),
    ("schema binding", schema_binding),
    ("representation (standalone)", standalone),
    ("representation (merged w/ accepted prior)", merged_findings),
):
    print(f"{name:44} {len(found)}")
    for f in found:
        print("   -", f)
print()
print(f"wire trip      {WIRE_ROUND_TRIP}")
print(f"obligations    {len(OBLIGATION_IDS)} declared, all discharged, 0 open")
print(f"missing refs   {sorted(t for _f, t in _cross_batch)}")
print("publishable    False  (five cross-batch citations have no target yet)")
print(f"sibling pairs  {len(SIBLING_PAIRS)} (all legal: no shared substantive span)")
print(f"ownership      {json.dumps({k: v for k, v in OWNERSHIP.items() if k != 'spans_carrying_more_than_one_claim'})}")
print(f"residues       {AUDIT_DOC['review_disposition']['residues']}")
print(f"disclosed      {[d['id'] for d in DISCLOSED_LIMITS]}")
print(f"judgment chg   {[j['id'] for j in JUDGMENT_CHANGES]}")
for _rec in LIFT_RECORDS:
    print(
        f"lift           {_rec.lift_id}: "
        f"{len(_rec.verified_collections)} collections verified"
    )
print(f"prior content sha    {_prior_content_before} -> {_prior_content_after}")
print(f"prior blob id        {_prior_blob_before} -> {_prior_blob_after}")
print(f"prior raw sha        {_prior_raw_before}")
print(f"live oracle unchanged {LIVE_ORACLE_UNCHANGED}  (read as a sentinel only)")
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
_inputs_line = json.dumps({k: v for k, v in INPUT_PATHS.items() if k != "note"})
print(f"inputs         {_inputs_line}")
print(f"final proposal sha256  {FINAL_SHA256[PROPOSAL_FILE]}")
print(f"final audit    sha256  {FINAL_SHA256[AUDIT_FILE]}")
print("newlines       LF (asserted: no CR byte in either artifact)")
if DETERMINISTIC is not None:
    print(f"deterministic  {DETERMINISTIC}  (final bytes, parent vs separate process)")
