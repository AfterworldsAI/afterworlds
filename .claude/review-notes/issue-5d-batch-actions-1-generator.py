"""Machine proposal generator — CRD Issue 5d content batch candidate `actions-1`.

DISPOSABLE REVIEW MATERIAL. Emits a `MechanicalProposal` payload and an audit
trail only. Never writes to `oracles/`, never calls `accept_proposal`, never
touches the database, never publishes or activates anything.

Batch boundary: the Rules Glossary's source-tagged `[Action]` entry class plus
its umbrella `Action` glossary rule — 13 entry containers, 94 ledger leaves,
92 represented. Exactly the structural shape conditions-1 took over
`[Condition]`.

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
    AbilityScore,
    ActionCost,
    ActionEconomyFact,
    AdvantageFact,
    AdvantageState,
    AutomaticOutcome,
    AutomaticOutcomeFact,
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
#
# Per record: one list of leaf specs, in document order, one per represented
# leaf. Each leaf spec is a list of segments: (cut_marker | None, kind, arg).
# A segment runs from the cursor to the end of `cut_marker`; None runs to the
# end of the leaf.
#
#   "R"   SUPPORTING_AUTHORITY, contextually linked to the record
#   "C"   SUPPORTING_AUTHORITY, contextually linked to component `arg`
#   "REF" SUPPORTING_AUTHORITY, a source-authored reference to record `arg`
#   "U"   UNRESOLVED  — the closed typed union cannot carry this faithfully
#   "F"   SUBSTANTIVE, typed fact  arg = (component_key, fact)
#   "P"   SUBSTANTIVE, prose binding  arg = (component_key, reason_code)

W = [(None, "R", None)]  # whole leaf, supporting authority, linked to the record
U = [(None, "U", None)]  # whole leaf, unresolved

ACT = ActionEconomyFact(cost=ActionCost.ACTION)

SPEC: dict[str, list] = {}
RECORD_KEY: dict[str, str] = {}
RECORD_KIND: dict[str, RecordKind] = {}

ACTION_LABELS = [
    "Attack [Action]",
    "Dash [Action]",
    "Disengage [Action]",
    "Dodge [Action]",
    "Help [Action]",
    "Hide [Action]",
    "Influence [Action]",
    "Magic [Action]",
    "Ready [Action]",
    "Search [Action]",
    "Study [Action]",
    "Utilize [Action]",
]
for lab in ACTION_LABELS:
    RECORD_KEY[lab] = "action." + lab.split(" [")[0].lower()
    RECORD_KIND[RECORD_KEY[lab]] = RecordKind.GLOSSARY_RULE
RECORD_KEY["Action"] = "glossary.action"
RECORD_KIND["glossary.action"] = RecordKind.GLOSSARY_RULE

# --- Action (umbrella glossary rule) ---------------------------------------
SPEC["Action"] = [
    W,  # 'Action'
    [
        # An allowance of one action per turn. ActionEconomyFact states what an
        # effect *consumes*; nothing in the union states a per-turn quantity.
        ("one action.", "U", None),
        (None, "P", ("action_list", "open_ended_effect")),
    ],
    W,  # 'See also'
    W,  # cross-reference framing
    [("Attack", "REF", "action.attack"), ("Dash", "REF", "action.dash"),
     (None, "REF", "action.disengage")],
    [("Dodge", "REF", "action.dodge"), ("Help", "REF", "action.help"),
     (None, "REF", "action.hide")],
    [("Influence", "REF", "action.influence"), ("Magic", "REF", "action.magic"),
     (None, "REF", "action.ready")],
    [("Search", "REF", "action.search"), ("Study", "REF", "action.study"),
     (None, "REF", "action.utilize")],
]

# --- Attack ----------------------------------------------------------------
SPEC["Attack [Action]"] = [
    W,
    [
        ("When you take the Attack action,", "F", ("attack_action", ACT)),
        # "one attack roll" is an allowance quantity; AttackRollFact states a
        # to-hit bonus this clause does not give.
        (None, "U", None),
    ],
    W,  # sub-heading; its body is unresolved, so no component exists to link to
    [
        ("you do not need to use it for that attack.".replace("do not", "don\u2019t"),
         "U", None),
        (None, "R", None),
    ],
    W,  # sub-heading; body unresolved
    U,  # interleaving movement with attacks
]

# --- Dash ------------------------------------------------------------------
SPEC["Dash [Action]"] = [
    W,
    [
        ("When you take the Dash action,", "F", ("dash_action", ACT)),
        # A movement *grant* — the polar inverse of a movement cost.
        ("after applying any modifiers.", "U", None),
        (None, "R", None),
    ],
    W,  # worked example continued
    [
        ("this turn if you Dash.", "R", None),
        (None, "U", None),  # special-speed substitution begins
    ],
    U,  # substitution continues; "You choose which"
    U,  # "speed to use each time you take it."
    W,  # 'See also'
    W,  # '"Speed."'
]

# --- Disengage -------------------------------------------------------------
SPEC["Disengage [Action]"] = [
    W,
    [
        ("If you take the Disengage action,", "F", ("disengage_action", ACT)),
        (None, "U", None),  # Opportunity Attack immunity
    ],
]

# --- Dodge -----------------------------------------------------------------
SPEC["Dodge [Action]"] = [
    W,
    [
        ("If you take the Dodge action,", "F", ("dodge_action", ACT)),
        ("until the start of your next turn,", "U", None),  # benefit duration
        (
            "any attack roll made against you has Disadvantage",
            "F",
            (
                "dodge_benefits",
                AdvantageFact(
                    state=AdvantageState.DISADVANTAGE,
                    roll=RollSpec(
                        actor=RollActor.AGAINST_SUBJECT,
                        context=RollContext.ATTACK_ROLL,
                    ),
                ),
            ),
        ),
        ("if you can see the attacker,", "P",
         ("dodge_benefits", "contextual_applicability")),
        (
            "with Advantage.",
            "F",
            (
                "dodge_benefits",
                AdvantageFact(
                    state=AdvantageState.ADVANTAGE,
                    roll=RollSpec(
                        actor=RollActor.SUBJECT,
                        context=RollContext.SAVING_THROW,
                        ability=AbilityScore.DEXTERITY,
                    ),
                ),
            ),
        ),
        # Benefit-loss predicate; the direct sibling of Prone's Speed-0 clause.
        (None, "U", None),
    ],
]

# --- Help ------------------------------------------------------------------
SPEC["Help [Action]"] = [
    W,
    [
        ("When you take the Help action,", "F", ("help_action", ACT)),
        (None, "U", None),  # exclusive choice between two modes
    ],
    [(None, "C", "assist_ability_check")],
    U,  # proficiency + ally proximity eligibility (continues into next leaf)
    [
        ("when they make an ability check.", "U", None),
        # The beneficiary is an ally: neither SUBJECT nor AGAINST_SUBJECT.
        ("with the chosen skill or tool.", "U", None),
        ("before the start of your next turn.", "U", None),  # benefit expiry
        (None, "P", ("assist_ability_check", "gamemaster_latitude")),
    ],
    W,  # sub-heading; body unresolved
    [
        ("within 5 feet of you,", "U", None),  # range eligibility
        ("against that enemy.", "U", None),  # third-party beneficiary
        (None, "U", None),  # benefit expiry
    ],
]

# --- Hide ------------------------------------------------------------------
SPEC["Hide [Action]"] = [
    W,
    [
        ("With the Hide action,", "F", ("hide_action", ACT)),
        ("you try to hide yourself.", "R", None),
        # A skill-qualified check: AbilityCheckFact carries no skill, and a bare
        # Dexterity check drops a proficiency that changes the roll.
        ("Dexterity (Stealth) check", "U", None),
        ("out of any enemy\u2019s line of sight;", "U", None),  # eligibility
        ("whether it can see you.", "U", None),  # reciprocal perception
        ("the Invisible condition while hidden.", "U", None),  # outcome-conditional
        ("Wisdom (Perception) check.", "U", None),  # derived DC + skill
        (None, "U", None),  # enumerated exit triggers
    ],
]

# --- Influence -------------------------------------------------------------
SPEC["Influence [Action]"] = [
    W,
    [
        ("With the Influence action,", "F", ("influence_action", ACT)),
        ("gently persuade?", "R", None),
        (None, "P", ("influence_disposition", "gamemaster_latitude")),
    ],
    [(None, "C", "willing")],
    [
        ("no ability check is necessary;", "F",
         ("willing",
          AutomaticOutcomeFact(
              roll=RollSpec(actor=RollActor.SUBJECT,
                            context=RollContext.ABILITY_CHECK),
              outcome=AutomaticOutcome.SUCCESS))),
        (None, "P", ("willing", "contextual_applicability")),
    ],
    [(None, "C", "unwilling")],
    [
        ("no ability check is necessary;", "F",
         ("unwilling",
          AutomaticOutcomeFact(
              roll=RollSpec(actor=RollActor.SUBJECT,
                            context=RollContext.ABILITY_CHECK),
              outcome=AutomaticOutcome.FAILURE))),
        (None, "P", ("unwilling", "contextual_applicability")),
    ],
    W,  # sub-heading; body unresolved
    [
        ("defined in this glossary.", "U", None),  # attitude-modified check
        ("interacting with the monster.", "R", None),
        ("whichever is higher.", "U", None),  # derived DC with a floor
        ("in the same way again.", "U", None),  # outcome branches + cooldown
        (None, "R", None),  # table caption
    ],
    W, W, W, W, W, W, W, W, W, W, W, W,  # advisory table
]

# --- Magic -----------------------------------------------------------------
SPEC["Magic [Action]"] = [
    W,
    [
        ("When you take the Magic action,", "F", ("magic_action", ACT)),
        (None, "U", None),  # activation eligibility over spell/feature/item
    ],
    [
        ("while you do so.", "U", None),  # repeated-action + upkeep requirement
        (None, "U", None),  # concentration-broken consequence
    ],
    W,
    W,
]

# --- Ready -----------------------------------------------------------------
SPEC["Ready [Action]"] = [
    W,
    [
        ("You take the Ready action", "F", ("ready_action", ACT)),
        ("before the start of your next turn.", "U", None),  # action to Reaction
        # The trigger space is unbounded by construction: an affirmative
        # PROSE_BOUND judgement, not a backlog state.
        ("will trigger your Reaction.", "P",
         ("ready_trigger", "open_ended_effect")),
        ("in response to it.", "U", None),  # choice of response
        (None, "R", None),  # example begins
    ],
    [
        ("I move away.\u201d", "R", None),  # example continues
        ("or ignore the trigger.", "U", None),  # choice on trigger
        ("when the trigger occurs.", "U", None),  # readied-spell hold
        ("start of your next turn.", "U", None),  # eligibility + upkeep
        (None, "U", None),  # concentration-broken consequence
    ],
]

# --- Search ----------------------------------------------------------------
SPEC["Search [Action]"] = [
    W,
    [
        ("When you take the Search action,", "F", ("search_action", ACT)),
        # A check with no stated DC: every DcKind member is a positive claim.
        ("that isn\u2019t obvious.", "U", None),
        (None, "R", None),
    ],
    W, W, W, W, W, W, W, W, W, W,  # advisory table
]

# --- Study -----------------------------------------------------------------
SPEC["Study [Action]"] = [
    W,
    [
        ("When you take the Study action,", "F", ("study_action", ACT)),
        ("piece of information about it.", "U", None),  # unstated-DC check
        (None, "R", None),
    ],
    W, W, W, W, W, W, W, W, W, W, W, W, W,  # advisory table
]

# --- Utilize ---------------------------------------------------------------
SPEC["Utilize [Action]"] = [
    W,
    [
        ("part of the Attack action.", "R", None),
        ("When an object requires an action for its use,", "R", None),
        (None, "F", ("utilize_action", ACT)),
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
    "REF": SemanticDisposition.SUPPORTING_AUTHORITY,
    "U": SemanticDisposition.UNRESOLVED,
    "F": SemanticDisposition.SUBSTANTIVE,
    "P": SemanticDisposition.SUBSTANTIVE,
}
RATIONALE = {
    "R": "identifies, frames, or exemplifies the mechanic; preserved as supporting "
    "authority rather than discarded",
    "C": "sub-heading naming the effect it labels; preserved as supporting authority",
    "REF": "names one action this glossary defines; source-authored reference target",
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
                    origin="issue-5d-batch-actions-1-generator.py",
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
                    from_component_key="action_list",
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
        "issue-5d-batch-actions-1-generator.py "
        "(CRD Issue 5d batch candidate actions-1)"
    ),
)

payload = proposal_payload(PROPOSAL)
ident = proposal_identity(PROPOSAL)

(OUT / "issue-5d-batch-actions-1-PROPOSAL.json").write_text(
    json.dumps(payload, indent=1, sort_keys=True, ensure_ascii=False), encoding="utf-8"
)
(OUT / "issue-5d-batch-actions-1-audit.json").write_text(
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
print("CRD Issue 5d — batch candidate actions-1")
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
