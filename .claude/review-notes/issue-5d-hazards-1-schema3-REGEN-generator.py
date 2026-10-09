"""Machine proposal generator - CRD Issue 5d batch `hazards-1`, representation schema 3.

DISPOSABLE REVIEW MATERIAL. Emits a `MechanicalProposal` payload and an audit
trail only. Never writes to `oracles/`, never calls `accept_proposal`, never
touches the database, never publishes or activates anything.

Regeneration, not an edit. The schema-1 artifacts
(`issue-5d-batch-hazards-1-{PROPOSAL,audit}.json`) are retained byte-for-byte as
the record of what was previously concluded; their span cuts, classifications,
components, facts and identity are NOT authoritative here. What IS preserved
from them is the boundary, the leaf accounting, the derivation method, the
release assertions, and the refusal guards.

Batch boundary (the source's, not a selection): the Rules Glossary's
source-tagged `[Hazard]` entry class plus its umbrella `Hazard` glossary rule.
The umbrella's own See-also names exactly those five. 6 entry containers,
43 ledger leaves, 43 represented, none excluded.

THE EMISSION RULE THIS REGENERATION APPLIES, stated once because it is what
moved the counts:

    Emit a typed fact only when the fact's own claim is true as stated and its
    scope is not narrowed or multiplied by a predicate schema 3 cannot carry.
    Refuse when an unrepresentable qualifier would make the fact apply where the
    source does not, or apply once where the source repeats it.

That is the schema-3 fact-scoped-applicability finding (Grappled > Movable)
applied evenly. A qualifier that is genuinely contextual fiction is carried as
an affirmative prose binding instead; a qualifier whose operand is a table, a
quantity, a roll outcome or a damage outcome is crisp, so its span stays
UNRESOLVED rather than becoming PROSE_BOUND as a backlog substitute.
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
# The schema-1 artifacts are the record of a superseded conclusion. Refuse to
# run at all if this file would overwrite one of them, and assert after the run
# that none of them moved.
RETAINED = (
    "issue-5d-batch-hazards-1-PROPOSAL.json",
    "issue-5d-batch-hazards-1-audit.json",
    "issue-5d-batch-hazards-1-generator.py",
)
WRITES = {
    "issue-5d-hazards-1-schema3-REGEN-PROPOSAL.json",
    "issue-5d-hazards-1-schema3-REGEN-audit.json",
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
from afterworlds.ingestion.mechanical.representation import (  # noqa: E402
    REPRESENTATION_SCHEMA_VERSION,
    ActionCost,
    ActionEconomyFact,
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
    fact_target_key,
    prose_binding_target_key,
    representation_schema_hash,
)
from afterworlds.ingestion.mechanical.validation import (  # noqa: E402
    validate_representation,
)
from afterworlds.pipeline.retrieval.config import RetrievalMemoryConfig  # noqa: E402

assert (
    REPRESENTATION_SCHEMA_VERSION == "5d-representation-schema-3"
), REPRESENTATION_SCHEMA_VERSION

# ---------------------------------------------------------------------------
# Bound release - derived from the committed PDF, asserted against production
# ---------------------------------------------------------------------------

PACKAGE_UUID = "4458fa10-4a66-5e0e-9ecc-ea37530ad2b4"
RELEASE_VERSION = "5.2.1-corpus.36b786d8-fa2"
SOURCE_SHA256 = "8974902d109d6e63672d7c490bde9ccf052410503d9cfa768237154fbc5e3d87"
TRANSFORM_CONFIG_HASH = "77720c2f3b8c9b88363d48050466fb8e3a26f8476b63145d1b5928ff2581ef3e"
BUNDLE_ROOT_HASH = "03353dfb79790aee7260b9ed96055b7296cd6f70e3e6f97d6cbe0a2484279685"

#: The only binding value NOT independently derivable here: a function of the
#: persisted `rp_sources` rows and verified Chroma state, so reproducing it
#: requires an actual publish, which this generator must not do. Taken from the
#: published CRD Issue 5c release record. The five values above ARE derived
#: from the committed PDF and asserted below.
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

SCOPE_KEY = "srd_5_2_1"
LSQ = "\u201c"  # left double quote
RSQ = "\u201d"  # right double quote
APOS = "\u2019"

# ---------------------------------------------------------------------------
# The proposed batch, as an explicit reviewable clause table
# ---------------------------------------------------------------------------

W = [(None, "R", None)]  # whole leaf, supporting authority, owned by the record
U = [(None, "U", None)]  # whole leaf, unresolved

SPEC: dict[str, list] = {}
RECORD_KEY: dict[str, str] = {}
RECORD_KIND: dict[str, RecordKind] = {}

HAZARD_LABELS = [
    "Burning [Hazard]",
    "Dehydration [Hazard]",
    "Falling [Hazard]",
    "Malnutrition [Hazard]",
    "Suffocation [Hazard]",
]
for lab in HAZARD_LABELS:
    RECORD_KEY[lab] = "hazard." + lab.split(" [")[0].lower()
    RECORD_KIND[RECORD_KEY[lab]] = RecordKind.GLOSSARY_RULE
RECORD_KEY["Hazard"] = "glossary.hazard"
RECORD_KIND["glossary.hazard"] = RecordKind.GLOSSARY_RULE

PRONE_APPLIES = ConditionEffectFact(
    condition=ConditionKind.PRONE, effect=ConditionEffectKind.APPLIES
)

# --- Hazard (umbrella glossary rule) ---------------------------------------
# The five names are source-authored mechanical references (#137 contract 3 and
# 7, ADR-005d Decision 7). `ReferenceDraft` requires `from_component_key`, and
# this record HAS no component: 'A hazard is an environmental danger.' states a
# category and no mechanic, and no member of the closed irreducibility catalog
# describes it, so it can be bound neither as a fact nor as prose.
#
# The accepted `glossary.condition` sibling owns its 15 references from a
# component that exists for an INDEPENDENT reason - a real rule carrying a
# natural-language exception ("A condition doesn't stack with itself ... The
# Exhaustion condition is an exception to that rule."). The Hazard umbrella has
# no such sentence anywhere in its four leaves, so reproducing that component
# shape here would fabricate a mechanical component.
#
# The five names are therefore UNRESOLVED, not quietly demoted to supporting
# authority: the reference obligation is real, and schema 3 cannot own it.
# See the closure checkpoint, addition H-8.
SPEC["Hazard"] = [
    W,  # 'Hazard'
    W,  # 'A hazard is an environmental danger.' - states the category
    W,  # 'See also'
    [
        (f"{LSQ}Burning,{RSQ}", "U", None),
        (f"{LSQ}Dehydration,{RSQ}", "U", None),
        (f"{LSQ}Falling,{RSQ}", "U", None),
        (f"{LSQ}Malnutrition,{RSQ}", "U", None),
        (" and", "R", None),
        (None, "U", None),  # ' "Suffocation."'
    ],
]

# --- Burning ---------------------------------------------------------------
SPEC["Burning [Hazard]"] = [
    W,
    [
        ("A burning creature or object", "R", None),
        # REFUSED: DamageFact(FIRE, 1d4). The cadence multiplies the fact -
        # once versus every turn - so a bare amount changes the rule. Same
        # standard that refused ConditionEffectFact(EXHAUSTION, APPLIES) for a
        # level gain in the schema-closure work.
        (" takes 1d4 Fire damage", "U", None),
        (" at the start of each of its turns.", "U", None),
        (
            " As an action,",
            "F",
            ("self_extinguish", ActionEconomyFact(cost=ActionCost.ACTION)),
        ),
        # No family states that a hazard or an effect ENDS. Crisp, and the
        # union has no structure for it.
        (" you can extinguish fire on yourself", "U", None),
        (" by giving yourself the Prone condition", "F", ("self_extinguish", PRONE_APPLIES)),
        (" and rolling on the ground.", "C", "self_extinguish"),
        (" The fire also goes out", "U", None),
        (None, "U", None),  # ' if it is doused, submerged, or suffocated.'
    ],
]

# --- Dehydration -----------------------------------------------------------
SPEC["Dehydration [Hazard]"] = [
    W,
    [
        # The operand is the in-batch Water Needs per Day table - closed
        # authority, not world-state judgement. Crisp; schema 3 has no
        # size-keyed quantity structure.
        ("as shown in the Water Needs per Day table.", "U", None),
        (" A creature that drinks less than half the required water for a day", "U", None),
        # REFUSED: ConditionLevelFact(EXHAUSTION, GAIN, 1). The threshold above
        # narrows it; unqualified it asserts every creature gains a level daily.
        (" gains 1 Exhaustion level", "U", None),
        (f" at the day{APOS}s end.", "U", None),
        (" Exhaustion caused by dehydration", "U", None),
        (None, "U", None),  # removal blocked until the full table amount
    ],
    W,  # 'See also'
    [
        (f"{LSQ}Exhaustion.{RSQ}", "U", None),  # reference; no record-level owner
        (None, "R", None),  # ' Water Needs per Day' - names the table
    ],
    W,  # 'Size'  (column header)
    W,  # 'Water' (column header)
    U,  # 'Tiny'
    U,  # '1/4 gallon'
    U,  # 'Small'
    U,  # '1 gallon'
    U,  # 'Medium'
    U,  # '1 gallon'
    [
        ("Size Water", "R", None),  # repeated header
        ("Large", "U", None),
        (" 4 gallons", "U", None),
        (" Huge", "U", None),
        (" 16 gallons", "U", None),
        (" Gargantuan", "U", None),
        (None, "U", None),  # ' 64 gallons'
    ],
]

# --- Falling ---------------------------------------------------------------
SPEC["Falling [Hazard]"] = [
    W,
    [
        ("A creature that falls", "R", None),
        # REFUSED: DamageFact(BLUDGEONING, 1d6). The per-10-feet scaling
        # multiplies it; a bare 1d6 is false for any fall over 10 feet.
        (" takes 1d6 Bludgeoning damage at the end of the fall", "U", None),
        (" for every 10 feet it fell,", "U", None),
        (" to a maximum of 20d6.", "U", None),
        # REFUSED: ConditionEffectFact(PRONE, APPLIES). The exception below
        # narrows it; unqualified it asserts Prone on every landing.
        (" When the creature lands, it has the Prone condition", "U", None),
        (" unless it avoids taking any damage from the fall.", "U", None),
        # AFFIRMATIVE prose binding: whether a substance is "another liquid" is
        # fiction the projection cannot enumerate - contextual_applicability
        # exactly as the closed catalog defines it, and the same disposition
        # accepted for the conditions-1 targeting restrictions.
        (
            " A creature that falls into water or another liquid",
            "P",
            ("surface_check", "contextual_applicability"),
        ),
        (
            " can use its Reaction",
            "F",
            ("surface_check", ActionEconomyFact(cost=ActionCost.REACTION)),
        ),
        # Homogeneous alternation of two skill-qualified checks. Neither a bare
        # Strength nor a bare Dexterity claim is true, and AbilityCheckFact has
        # neither a skill axis nor an alternatives set.
        (" to make a DC 15 Strength (Athletics) or Dexterity (Acrobatics) check", "U", None),
        (" to hit the surface head or feet first.", "C", "surface_check"),
        (" On a successful check,", "U", None),
        (None, "U", None),  # ' any damage resulting from the fall is halved.'
    ],
]

# --- Malnutrition ----------------------------------------------------------
SPEC["Malnutrition [Hazard]"] = [
    W,
    [
        ("as shown in the Food Needs per Day table.", "U", None),
        (
            " A creature that eats but consumes less than half the required food for a day",
            "U",
            None,
        ),
        # REFUSED: AbilityCheckFact(CONSTITUTION, FIXED, 10). Narrowed by the
        # threshold above; unqualified it asserts every creature makes this
        # save every day.
        (" must succeed on a DC 10 Constitution saving throw", "U", None),
        (" or gain 1 Exhaustion level", "U", None),
        (f" at the day{APOS}s end.", "U", None),
        (" A creature that eats nothing for 5 days", "U", None),
        (" automatically gains 1 Exhaustion level at the end of the fifth day", "U", None),
        (
            " as well as an additional level at the end of each subsequent day without food.",
            "U",
            None,
        ),
        (" Exhaustion caused by malnutrition", "U", None),
        (None, "U", None),  # removal blocked until the full table amount
    ],
    W,  # 'See also'
    [
        (f"{LSQ}Exhaustion.{RSQ}", "U", None),
        (None, "R", None),  # ' Food Needs per Day'
    ],
    W,
    W,
    W,
    W,  # 'Size' 'Food' 'Size' 'Food' - column headers
    U,
    U,
    U,
    U,
    U,
    U,
    U,
    U,
    U,
    U,
    U,
    U,  # the twelve data cells
]

# --- Suffocation -----------------------------------------------------------
SPEC["Suffocation [Hazard]"] = [
    W,
    [
        # One sentence, one obligation: a quantity derived from an ability
        # modifier with a stated floor, and the hazard onset it gates.
        (" before suffocation begins.", "U", None),
        (" When a creature runs out of breath or is choking,", "U", None),
        # REFUSED: ConditionLevelFact(EXHAUSTION, GAIN, 1) - narrowed by the
        # trigger above and multiplied by the cadence below.
        (" it gains 1 Exhaustion level", "U", None),
        (" at the end of each of its turns.", "U", None),
        (" When a creature can breathe again,", "U", None),
        # REFUSED: ConditionLevelFact(EXHAUSTION, REMOVE, all_levels=True).
        # The family's own merged docstring cites this exact clause, but the
        # family cannot scope removal to the levels THIS hazard caused, so it
        # would also remove levels caused by dehydration. False, not lossy.
        (None, "U", None),
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
comp_reason: dict[tuple[str, str], str] = {}
audit: list[dict] = []

DISP = {
    "R": SemanticDisposition.SUPPORTING_AUTHORITY,
    "C": SemanticDisposition.SUPPORTING_AUTHORITY,
    "U": SemanticDisposition.UNRESOLVED,
    "F": SemanticDisposition.SUBSTANTIVE,
    "P": SemanticDisposition.SUBSTANTIVE,
}
RATIONALE = {
    "R": (
        "identifies, frames, or exemplifies the mechanic; preserved as supporting "
        "authority rather than discarded"
    ),
    "C": (
        "names or describes the act the component states; supporting authority "
        "owned by that component"
    ),
    "U": (
        "the source states a mechanic whose operand resolves to closed authority "
        "- a table, a quantity, a roll outcome, a damage outcome, a cadence, or a "
        "reference target - that representation schema 3 has no structure for. It "
        "is not affirmatively irreducible, so PROSE_BOUND would be a backlog "
        "state and SUPPORTING_AUTHORITY would hide crisp authority"
    ),
    "F": (
        "states a mechanic the closed typed union carries exactly, with no "
        "qualifier that schema 3 cannot express"
    ),
    "P": (
        "affirmatively irreducible under a closed reason code: the predicate "
        "ranges over fiction the projection cannot enumerate"
    ),
}

for label, leafspecs in SPEC.items():
    entry_id = ENTRY_BY_LABEL[label]
    rkey = RECORD_KEY[label]
    lvs = by_container[entry_id]
    assert len(lvs) == len(leafspecs), f"{label}: {len(lvs)} leaves vs {len(leafspecs)} specs"

    for lf, segs in zip(lvs, leafspecs):
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
                    origin="issue-5d-hazards-1-schema3-REGEN-generator.py",
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
            elif kind == "P":
                comp, reason = arg
                comp_reason[(rkey, comp)] = reason
                comp_facts.setdefault((rkey, comp), [])
                extent = CORPUS.chunk_relative_range(chunk_of_leaf[lid], lid, start, end)
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
    components.append(
        ComponentDraft(
            record_key=rkey,
            semantic_key=ckey,
            handling=handling,
            irreducibility_reason_code=reason,
            facts=tuple(facts),
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

assert len(touched) == 43, f"leaves accounted: {len(touched)}"
assert len(records) == 6, f"records: {len(records)}"

PROPOSAL = MechanicalProposal(
    binding=BINDING,
    policy_version=SEMANTIC_POLICY_VERSION,
    policy_hash=semantic_policy_hash(),
    schema_version=REPRESENTATION_SCHEMA_VERSION,
    schema_hash=representation_schema_hash(),
    proposed_spans=tuple(proposed),
    proposed_representation=DRAFT,
    proposal_origin=(
        "issue-5d-hazards-1-schema3-REGEN-generator.py "
        "(CRD Issue 5d batch hazards-1, representation schema 3)"
    ),
)
payload = proposal_payload(PROPOSAL)
ident = proposal_identity(PROPOSAL)

(OUT / "issue-5d-hazards-1-schema3-REGEN-PROPOSAL.json").write_text(
    json.dumps(payload, indent=1, sort_keys=True, ensure_ascii=False), encoding="utf-8"
)
(OUT / "issue-5d-hazards-1-schema3-REGEN-audit.json").write_text(
    json.dumps(audit, indent=1, ensure_ascii=False), encoding="utf-8"
)

# Retained evidence must be untouched by this run.
for _n, _before in _RETAINED_BEFORE.items():
    _after = hashlib.md5((OUT / _n).read_bytes()).hexdigest()
    assert _after == _before, f"retained evidence {_n} changed"

# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

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

print(f"schema         {REPRESENTATION_SCHEMA_VERSION} / {representation_schema_hash()}")
print(f"policy         {SEMANTIC_POLICY_VERSION} / {semantic_policy_hash()}")
print(f"identity       {ident}")
print(f"records        {len(records)}")
print(f"leaves         {len(touched)}")
print(f"spans          {len(spans)}")
for k in ("substantive", "supporting_authority", "non_mechanical", "unresolved"):
    print(f"  {k:22} {counts[k]}")
print(f"components     {len(components)}")
for c in components:
    print(
        f"  {c.record_key}/{c.semantic_key}: {c.handling.value}, "
        f"{len(c.facts)} facts, reason={c.irreducibility_reason_code}"
    )
print(f"facts          {sum(len(c.facts) for c in components)}")
print(f"prose bindings {len(prose_bindings)}")
print(f"references     {len(references)}")
print("relationships  0")
print()
print(f"{'record':24} {'leaves':>6} {'spans':>6} {'unres':>6}")
for r in sorted(per_record):
    d = per_record[r]
    print(f"{r:24} {len(d['leaves']):6} {d['spans']:6} {d['unresolved']:6}")
print()
print(f"VALIDATION FINDINGS: {len(findings)}")
for f in findings:
    print("  -", f)
