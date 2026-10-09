"""Machine proposal generator — CRD Issue 5d content batch candidate `hazards-1`.

DISPOSABLE REVIEW MATERIAL. Emits a `MechanicalProposal` payload and an audit
trail only. Never writes to `oracles/`, never calls `accept_proposal`, never
touches the database, never publishes or activates anything.

Batch boundary: the Rules Glossary's source-tagged `[Hazard]` entry class plus
its umbrella `Hazard` glossary rule — 6 entry containers, 43 ledger leaves,
43 represented (none excluded). The umbrella's own See-also names exactly these
five, so the boundary is the source's, not a selection. The third and final
evidence batch for the consolidated schema-closure checkpoint.

The bound release is **derived** from the committed PDF by the production 5c
pipeline (`build_candidate`), not copied from any earlier artifact. Its
`package_uuid` and `release_version` are asserted against the published values.
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(r"D:\AI\Claude\afterworlds")
sys.path.insert(0, str(REPO / "src"))
OUT = Path(__file__).parent

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
    representation_schema_hash,
    AbilityCheckFact,
    AbilityScore,
    ActionCost,
    ActionEconomyFact,
    ConditionEffectFact,
    ConditionEffectKind,
    ConditionKind,
    DamageFact,
    DamageType,
    DcKind,
    DiceExpression,
    DieSize,
    ComponentDraft,
    ProseBindingDraft,
    ProvenanceClaim,
    ProvenanceRole,
    ProvenanceTargetKind,
    RecordDraft,
    RecordKind,
    ReferenceDraft,
    RepresentationDraft,
    RollActor,
    RollContext,
    RollSpec,
    fact_target_key,
    prose_binding_target_key,
    reference_target_key,
)
from afterworlds.ingestion.mechanical.validation import (  # noqa: E402
    validate_representation,
)
from afterworlds.pipeline.retrieval.config import RetrievalMemoryConfig  # noqa: E402

# ---------------------------------------------------------------------------
# Bound release — derived from the committed PDF, asserted against production
# ---------------------------------------------------------------------------

PACKAGE_UUID = "4458fa10-4a66-5e0e-9ecc-ea37530ad2b4"
RELEASE_VERSION = "5.2.1-corpus.36b786d8-fa2"
SOURCE_SHA256 = "8974902d109d6e63672d7c490bde9ccf052410503d9cfa768237154fbc5e3d87"
TRANSFORM_CONFIG_HASH = "77720c2f3b8c9b88363d48050466fb8e3a26f8476b63145d1b5928ff2581ef3e"
BUNDLE_ROOT_HASH = "03353dfb79790aee7260b9ed96055b7296cd6f70e3e6f97d6cbe0a2484279685"

#: The only binding value that is NOT independently derivable here.
#: `persisted_corpus_digest` is a function of the persisted `rp_sources` rows
#: and the verified Chroma vector state (`bundle.persisted_corpus_digest`), so
#: reproducing it requires an actual publish, which this generator must not do.
#: It is therefore taken from the published CRD Issue 5c release record. The
#: five values above ARE derived from the committed PDF and asserted below; a
#: rebuild that reproduces all five is the same release, which is what makes
#: carrying the sixth forward sound rather than a copy of convenience.
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

# ---------------------------------------------------------------------------
# The proposed batch, stated as an explicit reviewable clause table
# ---------------------------------------------------------------------------

W = [(None, "R", None)]  # whole leaf, supporting authority, linked to the record
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
SPEC["Hazard"] = [
    W,  # 'Hazard'
    W,  # 'A hazard is an environmental danger.' — identifies the category
    W,  # 'See also'
    # STRUCTURAL FINDING, recorded rather than worked around: `ReferenceDraft`
    # requires `from_component_key`, so every typed cross-reference must be owned
    # by a component. This umbrella has no component: its only body sentence,
    # 'A hazard is an environmental danger.', states a category and no mechanic,
    # and there is no closed irreducibility reason under which it could honestly
    # be bound as prose. (conditions-1 avoided this only because its umbrella's
    # definition sentence was genuinely prose-bindable.) The five names are
    # therefore SUPPORTING_AUTHORITY on the record. Nothing is lost from the
    # accounting; what is lost is the typed reference edge, which the model
    # cannot express at record level. See the consolidated checkpoint.
    W,
]

# --- Burning ---------------------------------------------------------------
SPEC["Burning [Hazard]"] = [
    W,
    [
        ("takes 1d4 Fire damage", "F",
         ("burning_damage",
          DamageFact(damage_type=DamageType.FIRE,
                     dice=DiceExpression(count=1, die=DieSize.D4)))),
        # Recurrence: the union states an amount, never a cadence.
        ("at the start of each of its turns.", "U", None),
        (" As an action,", "F", ("extinguish", ActionEconomyFact(cost=ActionCost.ACTION))),
        # The effect is that the hazard ends; no family states hazard termination.
        ("you can extinguish fire on yourself", "U", None),
        ("by giving yourself the Prone condition", "F", ("extinguish", PRONE_APPLIES)),
        ("rolling on the ground.", "R", None),
        (None, "U", None),  # disjunctive exit triggers: doused, submerged, suffocated
    ],
]

# --- Dehydration -----------------------------------------------------------
SPEC["Dehydration [Hazard]"] = [
    W,
    [
        ("Water Needs per Day table.", "U", None),   # size-keyed quantity requirement
        ("required water for a day", "U", None),     # consumption-threshold trigger
        ("gains 1 Exhaustion level at the day\u2019s end.", "U", None),  # level accrual
        (None, "U", None),                            # removal restriction
    ],
    W,  # 'See also'
    W,  # '"Exhaustion." Water Needs per Day'
    W, W, W, W, W, W, W, W, W,  # the Water Needs per Day table
]

# --- Falling ---------------------------------------------------------------
SPEC["Falling [Hazard]"] = [
    W,
    [
        ("takes 1d6 Bludgeoning damage", "F",
         ("fall_damage",
          DamageFact(damage_type=DamageType.BLUDGEONING,
                     dice=DiceExpression(count=1, die=DieSize.D6)))),
        ("for every 10 feet it fell,", "U", None),   # distance-scaled damage
        ("to a maximum of 20d6.", "U", None),        # damage cap
        ("it has the Prone condition", "F", ("landing", PRONE_APPLIES)),
        ("any damage from the fall.", "U", None),    # negative applicability condition
        ("can use its Reaction", "F",
         ("surface_check", ActionEconomyFact(cost=ActionCost.REACTION))),
        # A DISJUNCTION of two skill-qualified checks. Neither a bare Strength
        # nor a bare Dexterity claim is true, and no field admits "either".
        ("head or feet first.", "U", None),
        (None, "U", None),  # outcome-conditional damage halving
    ],
]

# --- Malnutrition ----------------------------------------------------------
SPEC["Malnutrition [Hazard]"] = [
    W,
    [
        ("Food Needs per Day table.", "U", None),    # size-keyed quantity requirement
        ("required food for a day", "U", None),      # consumption-threshold trigger
        ("must succeed on a DC 10 Constitution saving throw", "F",
         ("starvation_save",
          AbilityCheckFact(ability=AbilityScore.CONSTITUTION,
                           dc_kind=DcKind.FIXED, dc_value=10))),
        ("at the day\u2019s end.", "U", None),        # failure-branch level accrual
        ("each subsequent day without food.", "U", None),  # duration threshold + recurrence
        (None, "U", None),                            # removal restriction
    ],
    W,  # 'See also'
    W,  # '"Exhaustion." Food Needs per Day'
    W, W, W, W, W, W, W, W, W, W, W, W, W, W, W, W,  # the Food Needs per Day table
]

# --- Suffocation -----------------------------------------------------------
SPEC["Suffocation [Hazard]"] = [
    W,
    [
        ("before suffocation begins.", "U", None),   # derived duration with a floor
        ("at the end of each of its turns.", "U", None),  # recurring level accrual
        (None, "U", None),                            # conditional full removal
    ],
]

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
    "REF": SemanticDisposition.SUPPORTING_AUTHORITY,
    "U": SemanticDisposition.UNRESOLVED,
    "F": SemanticDisposition.SUBSTANTIVE,
    "P": SemanticDisposition.SUBSTANTIVE,
}
RATIONALE = {
    "R": "identifies, frames, or exemplifies the mechanic; preserved as supporting "
    "authority rather than discarded",
    "C": "sub-heading naming the effect it labels; preserved as supporting authority",
    "REF": "names one hazard this glossary defines; source-authored reference target",
    "U": "no member of the closed typed fact union carries this mechanic faithfully, "
    "and it is not affirmatively irreducible; classifying it PROSE_BOUND would be "
    "a backlog state",
    "F": "states a mechanic the closed typed union carries exactly",
    "P": "affirmatively irreducible under a closed reason code",
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
                assert found >= 0, f"{label}: marker {marker!r} not found in {content!r}"
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
                    origin="issue-5d-batch-hazards-1-generator.py",
                    rationale=RATIONALE[kind],
                )
            )
            audit.append({
                "record": rkey,
                "leaf": lid,
                "span_id": sid,
                "range": [start, end],
                "text": content[start:end],
                "disposition": disp.value,
                "kind": kind,
            })

            if kind == "R":
                provenance.append(ProvenanceClaim(
                    ProvenanceTargetKind.RECORD, (rkey,), sid,
                    ProvenanceRole.CONTEXTUAL))
            elif kind == "C":
                provenance.append(ProvenanceClaim(
                    ProvenanceTargetKind.COMPONENT, (rkey, arg), sid,
                    ProvenanceRole.CONTEXTUAL))
            elif kind == "REF":
                ref = ReferenceDraft(
                    from_record_key=rkey,
                    from_component_key="hazard_list",
                    source_text=content[start:end].strip(),
                    scope_key=SCOPE_KEY,
                    target_record_key=arg,
                )
                references.append(ref)
                provenance.append(ProvenanceClaim(
                    ProvenanceTargetKind.REFERENCE, reference_target_key(ref), sid,
                    ProvenanceRole.CONTEXTUAL))
            elif kind == "F":
                comp, fact = arg
                comp_facts[(rkey, comp)].append(fact)
                provenance.append(ProvenanceClaim(
                    ProvenanceTargetKind.FACT, fact_target_key(rkey, comp, fact), sid,
                    ProvenanceRole.PRIMARY))
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
                provenance.append(ProvenanceClaim(
                    ProvenanceTargetKind.PROSE_BINDING, prose_binding_target_key(pb), sid,
                    ProvenanceRole.PRIMARY))

records = tuple(
    RecordDraft(semantic_key=k, kind=RECORD_KIND[k])
    for k in sorted(set(RECORD_KEY.values()))
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
    components.append(ComponentDraft(
        record_key=rkey,
        semantic_key=ckey,
        handling=handling,
        irreducibility_reason_code=reason,
        facts=tuple(facts),
    ))

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
    proposal_origin=(
        "issue-5d-batch-hazards-1-generator.py "
        "(CRD Issue 5d batch candidate hazards-1)"
    ),
)

payload = proposal_payload(PROPOSAL)
ident = proposal_identity(PROPOSAL)

(OUT / "issue-5d-batch-hazards-1-PROPOSAL.json").write_text(
    json.dumps(payload, indent=1, sort_keys=True, ensure_ascii=False), encoding="utf-8"
)
(OUT / "issue-5d-batch-hazards-1-audit.json").write_text(
    json.dumps(audit, indent=1, ensure_ascii=False), encoding="utf-8"
)

by_disp: dict[str, int] = defaultdict(int)
for row in audit:
    by_disp[row["disposition"]] += 1
fam: dict[str, int] = defaultdict(int)
for c in components:
    for f in c.facts:
        fam[f.FAMILY.value] += 1
handling: dict[str, int] = defaultdict(int)
for c in components:
    handling[c.handling.value] += 1

print("=" * 68)
print("CRD Issue 5d — batch candidate hazards-1")
print("=" * 68)
print(f"package_uuid       {BINDING.package_uuid}")
print(f"release_version    {BINDING.release_version}")
print(f"source_sha256      {BINDING.authoritative_source_hash}")
print(f"transform_cfg_hash {BINDING.transform_config_hash}")
print(f"bundle_root_hash   {BINDING.bundle_root_hash}")
print(f"persisted_digest   {BINDING.persisted_corpus_digest}  (published record)")
print(f"ledger_hash        {CAND.ledger_hash}  (derived)")
print(f"semantic_policy    {SEMANTIC_POLICY_VERSION} / {semantic_policy_hash()}")
print(f"repr schema        {REPRESENTATION_SCHEMA_VERSION} / {representation_schema_hash()}")
print()
print(f"records            {len(records)}")
print(f"leaves touched     {len(touched)}")
print(f"spans              {len(spans)}")
for k in ("substantive", "supporting_authority", "unresolved", "non_mechanical"):
    print(f"  {k:<20} {by_disp.get(k, 0)}")
print(f"components         {len(components)}  {dict(handling)}")
print(f"typed facts        {sum(fam.values())}  {dict(fam)}")
print(f"prose bindings     {len(prose_bindings)}")
print(f"references         {len(references)}")
print()
print(f"validation findings {len(findings)}")
for f in findings:
    print("   !", f)
print()
print(f"proposal identity  {ident}")
print()
print("accept_proposal NOT called; oracles/ untouched; nothing published.")
