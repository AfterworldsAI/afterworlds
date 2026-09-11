"""CRD Issue 5d — batch `areas-of-effect-1`, representation schema 9.

Executable generator for the areas-of-effect-1 proposal and its audit. It reads
the committed SRD through the 5c pipeline, re-derives the Area of Effect
boundary from the source's own entry tag, takes the reviewed clause coordinates
from the committed discovery manifest, re-proves that those coordinates cut the
*bound* leaves gap-free and byte-for-byte, assigns each clause to the element
that states it, and writes two deterministic LF artifacts. It accepts nothing,
publishes nothing, activates nothing, retires nothing and touches no database.

Why this batch, and what its membership is
------------------------------------------
The batch is chosen by **complete source membership**, on the shape the four
accepted batches established: a source-tagged entry class *plus* the untagged
umbrella glossary rule that defines the tag. conditions-1 was the 15
``[Condition]`` entries plus ``Condition``; hazards-1 the 5 ``[Hazard]``
entries plus ``Hazard``; actions-1 the 12 ``[Action]`` entries plus ``Action``;
attitudes-1 the 3 ``[Attitude]`` entries plus ``Attitude``.

``[Area of Effect]`` is the last unaccepted class under that rule: Cone, Cube,
Cylinder, Emanation, Line and Sphere, plus the umbrella ``Area of Effect``.
**Seven records, twenty leaves, twenty represented, zero policy exclusions,
forty-three printed clauses.** The boundary is re-derived below from the tag
itself and cross-checked against the six names the umbrella's own enumeration
prints, so a shape added or renamed upstream fails this run rather than
silently dropping out of the batch.

Where the inventory comes from, and why it is not retyped here
--------------------------------------------------------------
The clause inventory is the one that passed independent review: leaf ids,
half-open ``[char_start, char_end)`` extents and clause text are read out of
``issue-5d-areas-of-effect-1-source-manifest.json`` rather than re-authored in
this file. That manifest is itself a product of the source, so this run closes
the loop rather than trusting it:

* the manifest's digest is pinned here and checked before anything is read;
* every manifest leaf id must exist in the *live* bound corpus, and its content
  must be byte-identical to what the pipeline just extracted from the PDF;
* the manifest's clause extents must partition each of the twenty bound leaves
  end to end — no gap, no overlap, starting at 0 and stopping at the leaf's
  length — and the concatenation must reconstruct the leaf byte for byte.

So the manifest supplies the *reviewed coordinates* and the PDF supplies the
*content*; a clause that drifted from the reviewed inventory, or a leaf that
moved under a re-extraction, fails this run instead of being quietly re-cut
under a judgment written about the old text.

Expected obligations, and what they are derived from
----------------------------------------------------
``EXPECTED_OBLIGATIONS`` is one literal row per printed clause, typed from the
**reviewed source record** — §3 of the discovery checkpoint for the 5c
disposition and the gap ids, §9's clause-to-fact table for the carrier. It is
deliberately *not* computed from anything this file emits. The manifest carries
no disposition at all, by design, so this table is the only place the review's
judgment enters, and the emission is then checked against it three ways:

* **omission** — every one of the forty-three obligations must be discharged;
* **duplication** — by exactly one span, at exactly the manifest's extent;
* **semantic loss** — carried by exactly the element the review says carries
  it: a record, a reference to a named target, a typed fact of a named family
  claimed PRIMARY, or a supporting clause claimed CONTEXTUAL on a named fact.

A composition that dropped Emanation's second movement exception, or collapsed
Cylinder's two parameters into one, or let a clause fall through to supporting
authority, changes a carrier row and fails here rather than reading as a clean
run with a quieter meaning.

Schema
------
**Representation schema 9**, seven fact families over eleven closed
vocabularies. Twenty-four of the forty-three clauses state mechanics schema 8
had no shape for, and no composition of accepted families states any of them: a
point of origin is not an effect, a duration, an allowance, a roll, a state
transition or a default. Contract 3's other branch is unavailable too — none of
the six closed irreducibility reasons is affirmatively true of any of the
twenty-four, so this batch emits **zero prose bindings**, and that is a
positive claim rather than an omission.

The crossing is the registered transition ``5d-lift-schema-8-to-9``, exercised
below against the frozen accepted prior. Five intrinsic invariant rows are
declared with the schema and bound into its hash; they are listed in the audit
and re-read from ``invariant_manifest()`` rather than narrated.

Two identities, two scopes
--------------------------
The frozen prior on disk is untouched and keeps the identity the Owner accepted,
``c3b4d4b7…5c74fa``. Its **lifted copy** is a different object with a different
identity, because ``oracle_payload`` carries the representation binding and the
lift re-declares exactly that. The lifted identity is *computed and reported*,
never pinned: it moves with the destination pin. What survives the crossing is
the content, and identically rather than equally — the lifted copy holds the
same representation object and ``representation_schema`` is the only top-level
payload key that moves.

Reference siting, and what stays open
-------------------------------------
A source-authored reference is emitted where the source **cites a record as a
defined term**, not at every place it says the word. That is the rule the
accepted batches already follow: ``glossary.hazard`` emits its five references
from its quoted "See also" list; ``glossary.condition`` and ``glossary.action``
emit from their printed enumerations.

So this batch emits **seven** references, all record-owned by the umbrella: six
from the printed enumeration ``Area of Effect/2/0`` … ``4/1`` to the six shapes
it defines, and one from *See also* to ``glossary.cover``, whose target this
batch does not define. None of the six shapes prints a "See also" leaf, so no
back-reference to the umbrella is derivable and none is invented. "Total Cover"
inside ``Area of Effect/5/3`` is a typed ``CoverDegree`` member on the
blocked-line fact, not a second citation.

**This batch does not validate clean, and says so.** Standalone it produces
exactly one finding — ``reference srd-5.2.1/rules-glossary:'Cover': unknown
target record glossary.cover`` — asserted as that exact tuple rather than
filtered, so a second finding cannot hide behind the first. Merged with the
lifted four-batch prior it produces exactly three, of exactly that class:
``glossary.concentration``, ``glossary.speed`` and ``glossary.cover``. This
batch **adds one unresolved target and resolves none.** Cover ingestion is not
in this batch and nothing here reaches into it.

What this run is, and is not
----------------------------
* It is *proposal preparation*. It is material for semantic review.
* Nothing here is accepted, activated, published or retired. The publication
  gate is not executed by this run at all — there is no persisted projection to
  run it over.
* The accepted four-batch prior is read **only** as a frozen review prior, by
  content identity, and asserted unchanged afterwards. The live oracle is read
  as a mutation sentinel and is never an input.
* One tagged class of the corpus #137 governs. The full-corpus obligation is
  untouched and undischarged.
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
#: review: conditions-1, hazards-1, actions-1 and attitudes-1, representation
#: schema 8. Read only, by content identity, and asserted unchanged at the end.
REVIEW_PRIOR_PATH = (
    REPO
    / "tests/ingestion/mechanical/data"
    / "accepted_prior_conditions_1_hazards_1_actions_1_attitudes_1.json"
)

#: **The reviewed clause inventory.** Discovery output, committed, and pinned by
#: digest below: coordinates only, no disposition.
MANIFEST_PATH = OUT / "issue-5d-areas-of-effect-1-source-manifest.json"

#: **A mutation sentinel, never an input.** Bytes captured before generation and
#: asserted identical afterwards. Never loaded, lifted, merged, or recorded.
LIVE_ORACLE_PATH = (
    REPO
    / "src/afterworlds/ingestion/mechanical/oracles"
    / "srd-5-2-1-corpus-36b786d8-fa2.json"
)
PACKAGE_ROOT = REPO / "src/afterworlds"
for _required in (
    SOURCE_PDF,
    REVIEW_PRIOR_PATH,
    MANIFEST_PATH,
    LIVE_ORACLE_PATH,
    PACKAGE_ROOT,
):
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

#: The frozen review prior, identified by **content** rather than by whatever
#: bytes a working copy holds. `.gitattributes` declares `* text=auto eol=lf`,
#: so a raw digest is a property of a checkout; the canonical (CRLF -> LF)
#: SHA-256 and the Git blob id are properties of the authority.
REVIEW_PRIOR_CONTENT_SHA256 = "fd390d95dde74498142035d9dde00ccf7effadb372fc13f9662154841bb787ab"  # noqa: E501  # pragma: allowlist secret
REVIEW_PRIOR_BLOB = (
    "2346404005618b0389b4e4f66d2e96c5c35b200f"  # pragma: allowlist secret
)
#: The identity the Owner accepted, at the scope it holds: the frozen file on
#: disk. The lifted copy's identity is a different value at a different scope
#: and is computed and reported below rather than pinned here.
REVIEW_PRIOR_IDENTITY = "c3b4d4b759441b05418fcbe1d90811e0d7c2535319aa005e64201ce29b5c74fa"  # noqa: E501  # pragma: allowlist secret
REVIEW_PRIOR_BATCH_IDS = ["actions-1", "attitudes-1", "conditions-1", "hazards-1"]
REVIEW_PRIOR_SCHEMA_VERSION = "5d-representation-schema-8"
REVIEW_PRIOR_SCHEMA_HASH = "8a125f6c4c9929109879ad98a8f14a4ec1d0c7f5fe56fe4f894dafbdf707afff"  # noqa: E501  # pragma: allowlist secret
#: What the four accepted batches hold together, named collection by collection
#: so one that silently gained or lost an element fails by name, not by total.
REVIEW_PRIOR_COLLECTIONS = {
    "records": 39,
    "components": 109,
    "prose_bindings": 49,
    "relationships": 0,
    "references": 46,
    "provenance": 504,
}
REVIEW_PRIOR_SPANS = 487
REVIEW_PRIOR_OBLIGATIONS = 39
#: Each accepted batch keeps the hash it was reviewed under. Schema 9 does not
#: restamp four batches as one, and the crossing is asserted to carry these
#: across by identity rather than re-derive them.
REVIEW_PRIOR_ANCHORS = {
    "conditions-1": "5d-representation-schema-3",
    "hazards-1": "5d-representation-schema-5",
    "actions-1": "5d-representation-schema-7",
    "attitudes-1": "5d-representation-schema-8",
}

#: The reviewed inventory, pinned. Checked before the file is parsed, so a
#: manifest edited after review cannot enter this proposal unnoticed.
MANIFEST_SHA256 = "5932c353dfd7d67756eeac72876705f5a60c5f2fe8175a7e78fdc0eb8c0d8b9c"  # noqa: E501  # pragma: allowlist secret

# --- Retained-evidence guard ------------------------------------------------
# Every artifact of the accepted batches and of this batch's discovery records
# authority or the review this run derives its brief from. Refuse to run if
# this file would overwrite one, and assert afterwards that none of them moved.
PROPOSAL_FILE = "issue-5d-batch-areas-of-effect-1-PROPOSAL.json"
AUDIT_FILE = "issue-5d-batch-areas-of-effect-1-audit.json"
WRITES = {PROPOSAL_FILE, AUDIT_FILE}
#: This run's own two outputs are excluded, and only those two: on the
#: determinism rerun they already exist from the parent, and a rerun that
#: refused to overwrite them could not prove anything about reproducibility.
RETAINED = tuple(
    sorted(
        p.name
        for p in OUT.iterdir()
        if p.is_file()
        and p.name != Path(__file__).name
        and p.name not in WRITES
        and p.suffix != ".tmp"
    )
)
assert not (WRITES & set(RETAINED)), "would overwrite retained evidence"
assert MANIFEST_PATH.name in RETAINED, "the reviewed manifest must be retained evidence"
_RETAINED_BEFORE = {
    n: hashlib.sha256((OUT / n).read_bytes()).hexdigest() for n in RETAINED
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
    candidate_from_accepted_inputs,
    load_accepted_inputs,
    oracle_identity,
    oracle_payload,
)
from afterworlds.ingestion.mechanical.policy import (  # noqa: E402
    IRREDUCIBILITY_REASONS,
    SEMANTIC_POLICY_VERSION,
    semantic_policy_hash,
)
from afterworlds.ingestion.mechanical.projection import (  # noqa: E402
    ProjectionCandidate,
    ReleaseBinding,
    representation_payload,
    validate_schema_binding,
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
    AreaDimension,
    AreaDimensionRequirementFact,
    AreaExtentPattern,
    AreaMovementSuspension,
    AreaOriginFact,
    AreaOriginInclusion,
    AreaOriginInclusionFact,
    AreaOriginKind,
    AreaOriginMovementFact,
    AreaOriginPlacement,
    AreaWidthRelation,
    AreaWidthRelationFact,
    BlockedLineExclusionFact,
    BlockedLineQuantifier,
    ComponentDraft,
    CoverDegree,
    FactFamily,
    MechanicalFact,
    ProvenanceClaim,
    ProvenanceRole,
    ProvenanceTargetKind,
    RecordDraft,
    RecordKind,
    ReferenceDraft,
    RelocatedOrigin,
    RepresentationDraft,
    UnseenOriginRelocationFact,
    UnseenPlacement,
    component_damage_composition_violations,
    component_roll_outcome_violations,
    declared_meaning_violations,
    fact_invariant_violations,
    fact_key,
    fact_target_key,
    held_structure_violations,
    introduction_manifest,
    invariant_manifest,
    option_set_violations,
    prose_binding_target_key,
    reference_target_key,
    representation_draft_violations,
    representation_schema_hash,
)
from afterworlds.ingestion.mechanical.representation import (  # noqa: E402
    InterveningObstruction,
)
from afterworlds.ingestion.mechanical.schema_lift import (  # noqa: E402
    lift_accepted_inputs,
    lift_path,
    verify_lift_path,
)
from afterworlds.ingestion.mechanical.validation import (  # noqa: E402
    validate_representation,
)
from afterworlds.pipeline.retrieval.config import RetrievalMemoryConfig  # noqa: E402
from afterworlds.services.rules_authority.application import (  # noqa: E402
    _base_records,
)

import afterworlds  # noqa: E402  # isort: skip

IMPORTED_FROM = Path(afterworlds.__file__).resolve().parent
assert PACKAGE_ROOT.resolve() == IMPORTED_FROM, (IMPORTED_FROM, PACKAGE_ROOT)
INPUT_PATHS = {
    "repository_root_derived_from": "Path(__file__).resolve().parents[2]",
    "source_pdf": SOURCE_PDF.relative_to(REPO).as_posix(),
    "source_manifest": MANIFEST_PATH.relative_to(REPO).as_posix(),
    "review_prior": REVIEW_PRIOR_PATH.relative_to(REPO).as_posix(),
    "afterworlds_package": IMPORTED_FROM.relative_to(REPO).as_posix(),
    "output_directory": OUT.relative_to(REPO).as_posix(),
    "note": (
        "Recorded relative to the derived root on purpose: an absolute path "
        "would make this artifact differ between two checkouts that produced "
        "identical content. Every path above is repository-retained, so this "
        "proposal is reproducible from the repository alone. The live "
        "accepted-authority oracle is deliberately absent: it is not an input. "
        "This run reads it only as a mutation sentinel and records neither its "
        "path nor its digest, because an accumulating artifact's identity goes "
        "stale at the next acceptance."
    ),
}

SCHEMA = (REPRESENTATION_SCHEMA_VERSION, representation_schema_hash())
assert SCHEMA[0] == "5d-representation-schema-9", SCHEMA
assert SCHEMA[1] == (
    "f5a5e30817e64f019e31aa7f4692d72611215e4294e7da36242e492bca6b336e"  # noqa: E501  # pragma: allowlist secret
), SCHEMA

# ---------------------------------------------------------------------------
# Bound release - derived from the committed PDF, asserted against production
# ---------------------------------------------------------------------------

PACKAGE_UUID = "4458fa10-4a66-5e0e-9ecc-ea37530ad2b4"
RELEASE_VERSION = "5.2.1-corpus.36b786d8-fa2"
SOURCE_SHA256 = "8974902d109d6e63672d7c490bde9ccf052410503d9cfa768237154fbc5e3d87"  # noqa: E501  # pragma: allowlist secret
TRANSFORM_CONFIG_HASH = "77720c2f3b8c9b88363d48050466fb8e3a26f8476b63145d1b5928ff2581ef3e"  # noqa: E501  # pragma: allowlist secret
BUNDLE_ROOT_HASH = "03353dfb79790aee7260b9ed96055b7296cd6f70e3e6f97d6cbe0a2484279685"  # noqa: E501  # pragma: allowlist secret

#: The only binding value NOT independently derivable here: a function of the
#: persisted `rp_sources` rows and verified Chroma state, so reproducing it
#: requires an actual publish, which this generator must not do. Taken from the
#: published CRD Issue 5c release record and disclosed as such.
PERSISTED_CORPUS_DIGEST = "c1f547962b7d9096986f0b8e75624f9f8803dfc281c16033e1c2250cad5a929b"  # noqa: E501  # pragma: allowlist secret

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
    for _cid in _leaf.container_path:
        by_container[_cid].append(_leaf)
for _group in by_container.values():
    _group.sort(key=lambda x: (x.page_index, x.char_start))

# --- Boundary, re-derived from the source rather than asserted --------------
# The source's own entry class: `[Area of Effect]`-tagged entries under Rules
# Definitions, plus the untagged `Area of Effect` umbrella. Derived by scanning
# the labels, then cross-checked against the six names the umbrella's own
# enumeration prints, so a shape added or renamed upstream fails here rather
# than silently dropping out of the batch.
TAG_CLASSES = {
    tag: sorted(lab for lab in ENTRY_BY_LABEL if lab.endswith(f" [{tag}]"))
    for tag in ("Action", "Area of Effect", "Attitude", "Condition", "Hazard")
}
assert {t: len(v) for t, v in TAG_CLASSES.items()} == {
    "Action": 12,
    "Area of Effect": 6,
    "Attitude": 3,
    "Condition": 15,
    "Hazard": 5,
}, {t: len(v) for t, v in TAG_CLASSES.items()}

UMBRELLA_LABEL = "Area of Effect"
assert UMBRELLA_LABEL in ENTRY_BY_LABEL, "the untagged umbrella entry is missing"
SHAPE_LABELS = TAG_CLASSES[UMBRELLA_LABEL]
SHAPE_NAMES = [lab.split(" [")[0] for lab in SHAPE_LABELS]
assert SHAPE_NAMES == ["Cone", "Cube", "Cylinder", "Emanation", "Line", "Sphere"]
BATCH_LABELS = [UMBRELLA_LABEL, *SHAPE_LABELS]

#: The umbrella's own enumeration leaves — "These shapes are defined elsewhere
#: in this glossary:" followed by a flattened two-column list. Checked in both
#: directions against the tag-derived membership: the tag may not name a shape
#: the umbrella does not print, and the umbrella may not print one the tag does
#: not name.
_UMBRELLA_LEAVES = by_container[ENTRY_BY_LABEL[UMBRELLA_LABEL]]
_ENUMERATED = " ".join(lf.content for lf in _UMBRELLA_LEAVES[2:5]).split()
assert sorted(_ENUMERATED) == sorted(SHAPE_NAMES), (_ENUMERATED, SHAPE_NAMES)

#: Policy exclusions inside this boundary. There are none — every leaf of every
#: member is represented — and that is asserted rather than assumed, because a
#: batch that silently lost a body leaf would look the same as one that lost a
#: running header.
POLICY_EXCLUDED = sorted(
    leaf.leaf_id
    for lab in BATCH_LABELS
    for cid in [ENTRY_BY_LABEL[lab]]
    for leaf in by_container[cid]
    if leaf.leaf_id not in REPRESENTED
)
assert POLICY_EXCLUDED == [], POLICY_EXCLUDED

SCOPE_KEY = "srd-5.2.1/rules-glossary"

UMBRELLA = "glossary.area_of_effect"
CONE = "area_of_effect.cone"
CUBE = "area_of_effect.cube"
CYLINDER = "area_of_effect.cylinder"
EMANATION = "area_of_effect.emanation"
LINE = "area_of_effect.line"
SPHERE = "area_of_effect.sphere"
#: Cited by the umbrella's *See also* and defined by no batch yet. Named here so
#: the dangling target is an explicit constant rather than a string that only
#: appears inside a validator message.
COVER = "glossary.cover"

RECORD_KEY: dict[str, str] = {UMBRELLA_LABEL: UMBRELLA}
for lab in SHAPE_LABELS:
    RECORD_KEY[lab] = "area_of_effect." + lab.split(" [")[0].lower()
RECORDS_IN_ORDER = (UMBRELLA, CONE, CUBE, CYLINDER, EMANATION, LINE, SPHERE)
assert sorted(RECORD_KEY.values()) == sorted(RECORDS_IN_ORDER), RECORD_KEY
#: `RecordKind` is a closed vocabulary and has no area member. The umbrella and
#: its six shapes are all Rules Glossary definitions, which is what
#: `GLOSSARY_RULE` means, and it is the kind the four accepted batches gave both
#: their umbrellas and their entries. Minting a kind for one class would widen a
#: closed vocabulary for one batch's convenience.
RECORD_KIND = {k: RecordKind.GLOSSARY_RULE for k in RECORDS_IN_ORDER}

# ---------------------------------------------------------------------------
# The reviewed inventory, read rather than retyped — then re-proved
# ---------------------------------------------------------------------------

_manifest_raw = MANIFEST_PATH.read_bytes()
_manifest_canonical = _manifest_raw.replace(b"\r\n", b"\n")
MANIFEST_DIGEST = hashlib.sha256(_manifest_canonical).hexdigest()
assert MANIFEST_DIGEST == MANIFEST_SHA256, MANIFEST_DIGEST
MANIFEST = json.loads(_manifest_canonical.decode("utf-8"))
assert MANIFEST["artifact_kind"] == "source_discovery_manifest", MANIFEST["artifact_kind"]
assert MANIFEST["batch_id"] == "areas-of-effect-1", MANIFEST["batch_id"]
#: The manifest carries coordinates, never dispositions. Asserted, because the
#: obligation table below is only independent evidence if the manifest is not
#: quietly carrying the same judgment.
assert not any(
    "disposition" in row for row in MANIFEST["clauses"]
), "the manifest must not carry dispositions"

#: `clause_id -> the manifest's clause row`, in printed order.
CLAUSE = {row["clause_id"]: row for row in MANIFEST["clauses"]}
CLAUSE_ORDER = tuple(row["clause_id"] for row in MANIFEST["clauses"])
assert len(CLAUSE) == len(CLAUSE_ORDER) == 43, len(CLAUSE_ORDER)

#: The manifest's own leaf table, and the tie to the live bound corpus: every
#: reviewed leaf must still exist and still hold byte-identical content.
MANIFEST_LEAVES: dict[str, str] = {}
for _record in MANIFEST["records"]:
    assert _record["candidate_record_key"] in RECORDS_IN_ORDER, _record
    for _leafrow in _record["leaves"]:
        _lid = _leafrow["leaf_id"]
        assert _lid in LEAF_BY_ID, f"the reviewed leaf {_lid} is not in the bound corpus"
        assert (
            LEAF_BY_ID[_lid].content == _leafrow["content"]
        ), f"leaf {_lid} moved under the bound source"
        MANIFEST_LEAVES[_lid] = _leafrow["content"]
assert len(MANIFEST_LEAVES) == 20, len(MANIFEST_LEAVES)

#: And the tie in the other direction: the boundary this run re-derived from the
#: tag holds exactly the leaves the reviewed inventory covers. A member that
#: gained a leaf upstream fails here rather than emitting a proposal that covers
#: less of the source than the source prints.
BOUNDARY_LEAVES = {
    leaf.leaf_id
    for lab in BATCH_LABELS
    for cid in [ENTRY_BY_LABEL[lab]]
    for leaf in by_container[cid]
}
assert BOUNDARY_LEAVES == set(MANIFEST_LEAVES), sorted(
    BOUNDARY_LEAVES ^ set(MANIFEST_LEAVES)
)
assert BOUNDARY_LEAVES <= REPRESENTED, "a boundary leaf is policy-excluded"

LEAF_RECORD = {
    _leafrow["leaf_id"]: _record["candidate_record_key"]
    for _record in MANIFEST["records"]
    for _leafrow in _record["leaves"]
}


def _leaf(clause_id: str) -> str:
    return str(CLAUSE[clause_id]["leaf_id"])


def _extent(clause_id: str) -> tuple[int, int]:
    row = CLAUSE[clause_id]
    return int(row["char_start"]), int(row["char_end"])


def _text(clause_id: str) -> str:
    start, end = _extent(clause_id)
    return MANIFEST_LEAVES[_leaf(clause_id)][start:end]


def _span_id(clause_id: str) -> str:
    return derive_span_id(_leaf(clause_id), *_extent(clause_id))


#: **The full source boundary, gap-free, proved rather than promised.** Every
#: one of the twenty bound leaves is partitioned end to end by the reviewed
#: clause extents: the first clause starts at 0, each next starts where the last
#: stopped, the last stops at the leaf's length, and the concatenation is the
#: leaf byte for byte. A dropped clause, an overlap, or a leaf that moved under
#: a re-extraction fails here.
CLAUSES_BY_LEAF: dict[str, list[str]] = defaultdict(list)
for _cid in CLAUSE_ORDER:
    CLAUSES_BY_LEAF[_leaf(_cid)].append(_cid)
assert sorted(CLAUSES_BY_LEAF) == sorted(MANIFEST_LEAVES), "a bound leaf has no clause"
for _lid, _cids in CLAUSES_BY_LEAF.items():
    _cursor = 0
    for _cid in _cids:
        _start, _end = _extent(_cid)
        assert _start == _cursor, f"{_cid}: gap or overlap at {_start} (want {_cursor})"
        assert _end > _start, f"{_cid}: empty clause"
        assert (
            CLAUSE[_cid]["text"] == MANIFEST_LEAVES[_lid][_start:_end]
        ), f"{_cid}: recorded text is not the text at its extent"
        _cursor = _end
    assert _cursor == len(MANIFEST_LEAVES[_lid]), f"{_lid}: partition stops short"
    assert (
        "".join(_text(c) for c in _cids) == MANIFEST_LEAVES[_lid]
    ), f"{_lid}: partition does not reconstruct the leaf"

# ---------------------------------------------------------------------------
# The twenty-four substantive clauses, as twenty-three facts
# ---------------------------------------------------------------------------
#
# One component per family per record, named for the rule it holds. Every fact
# names the clause ids it is the representation of; the blocked-line rule names
# two, because the source states the exclusion in one sentence and the
# threshold that makes a line blocked in the next, and both claim it PRIMARY on
# their own spans.
#
# No parameter value, unit, coordinate or grid semantic appears anywhere: the
# source prints none in this class. A Cone's maximum length is a name the
# creating effect supplies, and this schema says only that.

ORIGIN = "area_origin"
DIMENSIONS = "area_dimension_requirement"
INCLUSION = "area_origin_inclusion"
WIDTH = "area_width_relation"
MOVEMENT = "area_origin_movement"
BLOCKED = "blocked_line_exclusion"
UNSEEN = "unseen_origin_relocation"

EXCLUDED = AreaOriginInclusion.EXCLUDED_UNLESS_ITS_CREATOR_DECIDES_OTHERWISE
ALL_BLOCKED = BlockedLineQuantifier.ALL_STRAIGHT_LINES_FROM_THE_POINT_OF_ORIGIN
LINE_EXTENT = (
    AreaExtentPattern.STRAIGHT_PATH_ALONG_ITS_LENGTH_COVERING_THE_AREA_ITS_WIDTH_DEFINES
)
CONE_WIDTH = AreaWidthRelation.EQUAL_TO_THAT_POINTS_DISTANCE_FROM_THE_POINT_OF_ORIGIN

#: `(record, component, fact, clause ids)` — the whole substantive composition,
#: in printed order, record by record.
COMPOSITION: tuple[tuple[str, str, MechanicalFact, tuple[str, ...]], ...] = (
    # -- Area of Effect (p176): the general rules every shape inherits --------
    # "An area of effect has a point of origin, a location from which the
    # effect's energy erupts." The umbrella states *that* there is a point of
    # origin and nothing about how it extends or where it sits, so extent and
    # placement are unstated here rather than guessed from the shapes.
    (
        UMBRELLA,
        ORIGIN,
        AreaOriginFact(origin=AreaOriginKind.POINT),
        ("Area of Effect/5/0",),
    ),
    # The all-lines rule and its threshold. The quantifier is the whole rule:
    # one blocked line among many excludes nothing.
    (
        UMBRELLA,
        BLOCKED,
        BlockedLineExclusionFact(blocked=ALL_BLOCKED, blocking_cover=CoverDegree.TOTAL),
        ("Area of Effect/5/2", "Area of Effect/5/3"),
    ),
    # The unseen-origin conjunction and its near-side result.
    (
        UMBRELLA,
        UNSEEN,
        UnseenOriginRelocationFact(
            placement=UnseenPlacement.AT_AN_UNSEEN_POINT,
            obstruction=InterveningObstruction.BETWEEN_THE_CREATOR_AND_THE_POINT,
            relocated_to=RelocatedOrigin.NEAR_SIDE_OF_THE_OBSTRUCTION,
        ),
        ("Area of Effect/7/1",),
    ),
    # -- Cone (p178) ---------------------------------------------------------
    (
        CONE,
        ORIGIN,
        AreaOriginFact(
            origin=AreaOriginKind.POINT,
            extent=AreaExtentPattern.STRAIGHT_LINES_IN_A_DIRECTION_ITS_CREATOR_CHOOSES,
        ),
        ("Cone/1/0",),
    ),
    (CONE, WIDTH, AreaWidthRelationFact(relation=CONE_WIDTH), ("Cone/1/1",)),
    (
        CONE,
        DIMENSIONS,
        AreaDimensionRequirementFact(dimensions=(AreaDimension.MAXIMUM_LENGTH,)),
        ("Cone/1/3",),
    ),
    (CONE, INCLUSION, AreaOriginInclusionFact(inclusion=EXCLUDED), ("Cone/1/4",)),
    # -- Cube (p178) ---------------------------------------------------------
    (
        CUBE,
        ORIGIN,
        AreaOriginFact(
            origin=AreaOriginKind.POINT,
            extent=AreaExtentPattern.STRAIGHT_LINES,
            placement=AreaOriginPlacement.ANYWHERE_ON_A_FACE_OF_THE_CUBE,
        ),
        ("Cube/1/0",),
    ),
    (
        CUBE,
        DIMENSIONS,
        AreaDimensionRequirementFact(
            dimensions=(AreaDimension.SIZE_THE_LENGTH_OF_EACH_SIDE,)
        ),
        ("Cube/1/1",),
    ),
    (CUBE, INCLUSION, AreaOriginInclusionFact(inclusion=EXCLUDED), ("Cube/1/2",)),
    # -- Cylinder (p179) -----------------------------------------------------
    (
        CYLINDER,
        ORIGIN,
        AreaOriginFact(
            origin=AreaOriginKind.POINT,
            extent=AreaExtentPattern.STRAIGHT_LINES,
            placement=AreaOriginPlacement.CENTER_OF_THE_CIRCULAR_TOP_OR_BOTTOM,
        ),
        ("Cylinder/1/0",),
    ),
    # Two parameters, in the order the sentence prints them.
    (
        CYLINDER,
        DIMENSIONS,
        AreaDimensionRequirementFact(
            dimensions=(AreaDimension.RADIUS_OF_THE_BASE, AreaDimension.HEIGHT)
        ),
        ("Cylinder/1/1",),
    ),
    (
        CYLINDER,
        INCLUSION,
        AreaOriginInclusionFact(inclusion=AreaOriginInclusion.INCLUDED),
        ("Cylinder/1/2",),
    ),
    # -- Emanation (p180) ----------------------------------------------------
    # The one shape whose origin is not a point.
    (
        EMANATION,
        ORIGIN,
        AreaOriginFact(
            origin=AreaOriginKind.CREATURE_OR_OBJECT,
            extent=AreaExtentPattern.STRAIGHT_LINES_IN_ALL_DIRECTIONS,
        ),
        ("Emanation/1/0",),
    ),
    (
        EMANATION,
        DIMENSIONS,
        AreaDimensionRequirementFact(dimensions=(AreaDimension.DISTANCE_IT_EXTENDS,)),
        ("Emanation/1/1",),
    ),
    # Both printed exceptions, not one.
    (
        EMANATION,
        MOVEMENT,
        AreaOriginMovementFact(
            suspended_by_any_of=(
                AreaMovementSuspension.INSTANTANEOUS_EFFECT,
                AreaMovementSuspension.STATIONARY_EFFECT,
            )
        ),
        ("Emanation/1/2",),
    ),
    (
        EMANATION,
        INCLUSION,
        AreaOriginInclusionFact(inclusion=EXCLUDED),
        ("Emanation/1/3",),
    ),
    # -- Line (p183) ---------------------------------------------------------
    (
        LINE,
        ORIGIN,
        AreaOriginFact(origin=AreaOriginKind.POINT, extent=LINE_EXTENT),
        ("Line/1/0",),
    ),
    (
        LINE,
        DIMENSIONS,
        AreaDimensionRequirementFact(
            dimensions=(AreaDimension.LENGTH, AreaDimension.WIDTH)
        ),
        ("Line/1/1",),
    ),
    (LINE, INCLUSION, AreaOriginInclusionFact(inclusion=EXCLUDED), ("Line/1/2",)),
    # -- Sphere (p187) -------------------------------------------------------
    (
        SPHERE,
        ORIGIN,
        AreaOriginFact(
            origin=AreaOriginKind.POINT,
            extent=AreaExtentPattern.STRAIGHT_LINES_OUTWARD_IN_ALL_DIRECTIONS,
        ),
        ("Sphere/1/0",),
    ),
    (
        SPHERE,
        DIMENSIONS,
        AreaDimensionRequirementFact(
            dimensions=(AreaDimension.DISTANCE_IT_EXTENDS_AS_THE_RADIUS,)
        ),
        ("Sphere/1/1",),
    ),
    (
        SPHERE,
        INCLUSION,
        AreaOriginInclusionFact(inclusion=AreaOriginInclusion.INCLUDED),
        ("Sphere/1/2",),
    ),
)
FACT_OF: dict[tuple[str, str], MechanicalFact] = {
    (record, component): fact for record, component, fact, _ in COMPOSITION
}
assert len(FACT_OF) == len(COMPOSITION) == 23, len(COMPOSITION)

# ---------------------------------------------------------------------------
# The nineteen supporting clauses, each linked to what it actually supports
# ---------------------------------------------------------------------------

#: `(source_text, target, clause)`. Six from the umbrella's printed enumeration,
#: one from *See also*. All record-owned: no component of the umbrella states
#: the naming, the record does, which is `glossary.hazard`'s accepted shape.
CITATIONS: tuple[tuple[str, str, str], ...] = (
    ("Cone", CONE, "Area of Effect/2/0"),
    ("Cube", CUBE, "Area of Effect/2/1"),
    ("Cylinder", CYLINDER, "Area of Effect/3/0"),
    ("Emanation", EMANATION, "Area of Effect/3/1"),
    ("Line", LINE, "Area of Effect/4/0"),
    ("Sphere", SPHERE, "Area of Effect/4/1"),
    # Cited and not defined here: the blocked-line rule leans on Total Cover,
    # and the Cover entry is not in this batch.
    ("Cover", COVER, "Area of Effect/7/0"),
)
REFERENCES = tuple(
    ReferenceDraft(
        from_record_key=UMBRELLA,
        from_component_key=RECORD_OWNED_REFERENCE,
        source_text=text,
        scope_key=SCOPE_KEY,
        target_record_key=target,
    )
    for text, target, _ in CITATIONS
)
REFERENCE_OF_CLAUSE = {
    clause: reference
    for reference, (_, _, clause) in zip(REFERENCES, CITATIONS, strict=True)
}

#: Supporting clauses the *record* carries: each entry's heading, the umbrella's
#: two framing sentences, and the *See also* label.
RECORD_CONTEXT: tuple[tuple[str, str], ...] = (
    (UMBRELLA, "Area of Effect/0/0"),
    (UMBRELLA, "Area of Effect/1/0"),
    (UMBRELLA, "Area of Effect/1/1"),
    (UMBRELLA, "Area of Effect/6/0"),
    (CONE, "Cone/0/0"),
    (CUBE, "Cube/0/0"),
    (CYLINDER, "Cylinder/0/0"),
    (EMANATION, "Emanation/0/0"),
    (LINE, "Line/0/0"),
    (SPHERE, "Sphere/0/0"),
)

#: Supporting clauses a *fact* carries, because they bound that fact and nothing
#: else. "The rules for each shape specify how to position its point of origin."
#: is what makes the umbrella's origin fact silent on placement; the 15-foot
#: worked example illustrates the Cone width relation and states no rule of its
#: own — which is why it is contextual rather than a second fact with an
#: invented value in it.
FACT_CONTEXT: tuple[tuple[str, str, str], ...] = (
    (UMBRELLA, ORIGIN, "Area of Effect/5/1"),
    (CONE, WIDTH, "Cone/1/2"),
)

# ---------------------------------------------------------------------------
# Expected obligations — typed from the reviewed source, not from the emission
# ---------------------------------------------------------------------------
#
# One row per printed clause. The disposition column is §3 of the discovery
# checkpoint; the carrier column is §9's clause-to-fact table and §5's
# reference buckets; the gap column is §4. Nothing here is computed from the
# composition above, and the manifest carries no disposition, so this is the
# independent statement of what the proposal owes the source.
#
# Carrier shapes:
#   ("record", record)                     supporting authority owned by the record
#   ("reference", record, target)          supporting authority owned by a citation
#   ("fact", record, component, family)    substantive, claimed PRIMARY
#   ("fact_context", record, component)    supporting authority bounding one fact

SUB = "substantive"
SUP = "supporting_authority"
F_ORIGIN = FactFamily.AREA_ORIGIN.value
F_DIM = FactFamily.AREA_DIMENSION_REQUIREMENT.value
F_INCL = FactFamily.AREA_ORIGIN_INCLUSION.value
F_WIDTH = FactFamily.AREA_WIDTH_RELATION.value
F_MOVE = FactFamily.AREA_ORIGIN_MOVEMENT.value
F_BLOCK = FactFamily.BLOCKED_LINE_EXCLUSION.value
F_UNSEEN = FactFamily.UNSEEN_ORIGIN_RELOCATION.value

EXPECTED_OBLIGATIONS: tuple[tuple[str, str, tuple[object, ...], tuple[str, ...]], ...] = (
    # --- glossary.area_of_effect, p176 --------------------------------------
    ("Area of Effect/0/0", SUP, ("record", UMBRELLA), ()),
    ("Area of Effect/1/0", SUP, ("record", UMBRELLA), ()),
    ("Area of Effect/1/1", SUP, ("record", UMBRELLA), ()),
    ("Area of Effect/2/0", SUP, ("reference", UMBRELLA, CONE), ()),
    ("Area of Effect/2/1", SUP, ("reference", UMBRELLA, CUBE), ()),
    ("Area of Effect/3/0", SUP, ("reference", UMBRELLA, CYLINDER), ()),
    ("Area of Effect/3/1", SUP, ("reference", UMBRELLA, EMANATION), ()),
    ("Area of Effect/4/0", SUP, ("reference", UMBRELLA, LINE), ()),
    ("Area of Effect/4/1", SUP, ("reference", UMBRELLA, SPHERE), ()),
    ("Area of Effect/5/0", SUB, ("fact", UMBRELLA, ORIGIN, F_ORIGIN), ("G1",)),
    ("Area of Effect/5/1", SUP, ("fact_context", UMBRELLA, ORIGIN), ()),
    ("Area of Effect/5/2", SUB, ("fact", UMBRELLA, BLOCKED, F_BLOCK), ("G7",)),
    ("Area of Effect/5/3", SUB, ("fact", UMBRELLA, BLOCKED, F_BLOCK), ("G7",)),
    ("Area of Effect/6/0", SUP, ("record", UMBRELLA), ()),
    ("Area of Effect/7/0", SUP, ("reference", UMBRELLA, COVER), ()),
    ("Area of Effect/7/1", SUB, ("fact", UMBRELLA, UNSEEN, F_UNSEEN), ("G8",)),
    # --- area_of_effect.cone, p178 ------------------------------------------
    ("Cone/0/0", SUP, ("record", CONE), ()),
    ("Cone/1/0", SUB, ("fact", CONE, ORIGIN, F_ORIGIN), ("G1", "G2")),
    ("Cone/1/1", SUB, ("fact", CONE, WIDTH, F_WIDTH), ("G5",)),
    ("Cone/1/2", SUP, ("fact_context", CONE, WIDTH), ()),
    ("Cone/1/3", SUB, ("fact", CONE, DIMENSIONS, F_DIM), ("G3",)),
    ("Cone/1/4", SUB, ("fact", CONE, INCLUSION, F_INCL), ("G4",)),
    # --- area_of_effect.cube, p178 ------------------------------------------
    ("Cube/0/0", SUP, ("record", CUBE), ()),
    ("Cube/1/0", SUB, ("fact", CUBE, ORIGIN, F_ORIGIN), ("G1", "G2")),
    ("Cube/1/1", SUB, ("fact", CUBE, DIMENSIONS, F_DIM), ("G3",)),
    ("Cube/1/2", SUB, ("fact", CUBE, INCLUSION, F_INCL), ("G4",)),
    # --- area_of_effect.cylinder, p179 --------------------------------------
    ("Cylinder/0/0", SUP, ("record", CYLINDER), ()),
    ("Cylinder/1/0", SUB, ("fact", CYLINDER, ORIGIN, F_ORIGIN), ("G1", "G2")),
    ("Cylinder/1/1", SUB, ("fact", CYLINDER, DIMENSIONS, F_DIM), ("G3",)),
    ("Cylinder/1/2", SUB, ("fact", CYLINDER, INCLUSION, F_INCL), ("G4",)),
    # --- area_of_effect.emanation, p180 -------------------------------------
    ("Emanation/0/0", SUP, ("record", EMANATION), ()),
    ("Emanation/1/0", SUB, ("fact", EMANATION, ORIGIN, F_ORIGIN), ("G1", "G2")),
    ("Emanation/1/1", SUB, ("fact", EMANATION, DIMENSIONS, F_DIM), ("G3",)),
    ("Emanation/1/2", SUB, ("fact", EMANATION, MOVEMENT, F_MOVE), ("G6",)),
    ("Emanation/1/3", SUB, ("fact", EMANATION, INCLUSION, F_INCL), ("G4",)),
    # --- area_of_effect.line, p183 ------------------------------------------
    ("Line/0/0", SUP, ("record", LINE), ()),
    ("Line/1/0", SUB, ("fact", LINE, ORIGIN, F_ORIGIN), ("G1", "G2")),
    ("Line/1/1", SUB, ("fact", LINE, DIMENSIONS, F_DIM), ("G3",)),
    ("Line/1/2", SUB, ("fact", LINE, INCLUSION, F_INCL), ("G4",)),
    # --- area_of_effect.sphere, p187 ----------------------------------------
    ("Sphere/0/0", SUP, ("record", SPHERE), ()),
    ("Sphere/1/0", SUB, ("fact", SPHERE, ORIGIN, F_ORIGIN), ("G1", "G2")),
    ("Sphere/1/1", SUB, ("fact", SPHERE, DIMENSIONS, F_DIM), ("G3",)),
    ("Sphere/1/2", SUB, ("fact", SPHERE, INCLUSION, F_INCL), ("G4",)),
)

#: What each substantive obligation must *state*, in the words the review used.
#: Not machine-checked — a reviewer reads this beside the fact payload — but
#: keyed to the clause id so it cannot drift onto a different clause.
OBLIGATION_TEXT = {
    "Area of Effect/5/0": "an area of effect has a point of origin",
    "Area of Effect/5/2": (
        "a location is excluded when ALL straight lines from the point of "
        "origin to it are blocked"
    ),
    "Area of Effect/5/3": "Total Cover is the threshold that blocks a line",
    "Area of Effect/7/1": (
        "placed at an unseen point AND an obstruction between the creator and "
        "that point: the origin comes into being on the near side"
    ),
    "Cone/1/0": "a Cone extends in straight lines in a direction its creator chooses",
    "Cone/1/1": (
        "a Cone's width at a point equals that point's distance from the origin"
    ),
    "Cone/1/3": "the creating effect specifies a Cone's maximum length",
    "Cone/1/4": "a Cone's origin is excluded unless its creator decides otherwise",
    "Cube/1/0": "a Cube's origin sits anywhere on a face of the Cube",
    "Cube/1/1": "the creating effect specifies a Cube's size: the length of each side",
    "Cube/1/2": "a Cube's origin is excluded unless its creator decides otherwise",
    "Cylinder/1/0": "a Cylinder's origin sits at the center of the circular top or bottom",
    "Cylinder/1/1": (
        "the creating effect specifies TWO parameters: the base radius and the height"
    ),
    "Cylinder/1/2": "a Cylinder's origin is included",
    "Emanation/1/0": (
        "an Emanation extends from a CREATURE OR AN OBJECT in all directions - "
        "the one origin in this class that is not a point"
    ),
    "Emanation/1/1": "the creating effect specifies the distance an Emanation extends",
    "Emanation/1/2": (
        "an Emanation moves with its origin unless the effect is instantaneous "
        "OR stationary - both exceptions, not one"
    ),
    "Emanation/1/3": "an Emanation's origin is excluded unless its creator decides otherwise",
    "Line/1/0": "a Line extends in a straight path along its length, covering its width",
    "Line/1/1": "the creating effect specifies TWO parameters: length and width",
    "Line/1/2": "a Line's origin is excluded unless its creator decides otherwise",
    "Sphere/1/0": "a Sphere extends outward in all directions",
    "Sphere/1/1": (
        "the creating effect specifies the distance it extends as the radius"
    ),
    "Sphere/1/2": "a Sphere's origin is included",
}

# --- The obligation ledger, checked against the reviewed inventory ----------
EXPECTED = {row[0]: row for row in EXPECTED_OBLIGATIONS}
assert len(EXPECTED) == len(EXPECTED_OBLIGATIONS), "an obligation is listed twice"
#: Every printed clause is an obligation, and no obligation names a clause the
#: reviewed inventory does not print.
assert set(EXPECTED) == set(CLAUSE), sorted(set(EXPECTED) ^ set(CLAUSE))
_expected_dispositions = defaultdict(int)
for _row in EXPECTED_OBLIGATIONS:
    _expected_dispositions[_row[1]] += 1
assert dict(_expected_dispositions) == {SUP: 19, SUB: 24}, dict(_expected_dispositions)
assert sorted(OBLIGATION_TEXT) == sorted(
    cid for cid, disp, _, _ in EXPECTED_OBLIGATIONS if disp == SUB
), "every substantive obligation states what it owes"
#: The eight gaps §4 found, each still witnessed by at least one clause.
GAPS_WITNESSED = sorted({g for _, _, _, gaps in EXPECTED_OBLIGATIONS for g in gaps})
assert GAPS_WITNESSED == ["G1", "G2", "G3", "G4", "G5", "G6", "G7", "G8"], GAPS_WITNESSED

# ---------------------------------------------------------------------------
# Emission
# ---------------------------------------------------------------------------

ORIGIN_LABEL = "issue-5d-batch-areas-of-effect-1-generator.py"

DISPOSITION_OF = {SUB: SemanticDisposition.SUBSTANTIVE, SUP: SemanticDisposition.SUPPORTING_AUTHORITY}
RATIONALE = {
    "record": (
        "identifies, frames, or defines the mechanic; preserved as supporting "
        "authority owned by the record rather than discarded"
    ),
    "reference": (
        "a source-authored mechanical reference, sited on the record that prints "
        "it and naming a target record key within a committed scope; whether that "
        "key resolves to an ingested record is a validator finding, not a property "
        "of the citation; supporting authority, because naming a rule is not "
        "stating one"
    ),
    "fact": (
        "states a mechanic the closed typed union carries exactly, with every "
        "qualifier that narrows or multiplies it carried by a structure of this "
        "schema rather than left implicit"
    ),
    "fact_context": (
        "bounds exactly one typed fact and states no rule of its own; supporting "
        "authority claimed CONTEXTUAL by that fact rather than by the record, so "
        "the link a reviewer needs is in the provenance instead of in prose"
    ),
}

spans: list[SemanticSpan] = []
proposed: list[ProposedSpan] = []
provenance: list[ProvenanceClaim] = []
audit: list[dict] = []
#: What the emission actually did, one row per clause, in the same shape as
#: `EXPECTED_OBLIGATIONS`'s carrier column. Built from the emitted objects, then
#: compared; never copied from the table it is checked against.
DERIVED: dict[str, tuple[object, ...]] = {}

for clause_id in CLAUSE_ORDER:
    _, disposition, carrier, gaps = EXPECTED[clause_id]
    leaf_id = _leaf(clause_id)
    start, end = _extent(clause_id)
    sid = _span_id(clause_id)
    span = SemanticSpan(
        span_id=sid,
        leaf_id=leaf_id,
        char_start=start,
        char_end=end,
        disposition=DISPOSITION_OF[disposition],
        review_state=ReviewState.PROPOSED,
    )
    spans.append(span)
    kind = str(carrier[0])
    proposed.append(ProposedSpan(span=span, origin=ORIGIN_LABEL, rationale=RATIONALE[kind]))

    if kind == "record":
        record_key = str(carrier[1])
        claim = ProvenanceClaim(
            ProvenanceTargetKind.RECORD, (record_key,), sid, ProvenanceRole.CONTEXTUAL
        )
        claimant = record_key
    elif kind == "reference":
        reference = REFERENCE_OF_CLAUSE[clause_id]
        claim = ProvenanceClaim(
            ProvenanceTargetKind.REFERENCE,
            reference_target_key(reference),
            sid,
            ProvenanceRole.CONTEXTUAL,
        )
        record_key = reference.from_record_key
        claimant = f"{reference.from_record_key} -> {reference.target_record_key}"
    elif kind == "fact":
        record_key, component_key = str(carrier[1]), str(carrier[2])
        fact = FACT_OF[(record_key, component_key)]
        claim = ProvenanceClaim(
            ProvenanceTargetKind.FACT,
            fact_target_key(record_key, component_key, fact),
            sid,
            ProvenanceRole.PRIMARY,
        )
        claimant = f"{record_key}/{component_key}/{fact_key(fact)}"
    else:
        record_key, component_key = str(carrier[1]), str(carrier[2])
        fact = FACT_OF[(record_key, component_key)]
        claim = ProvenanceClaim(
            ProvenanceTargetKind.FACT,
            fact_target_key(record_key, component_key, fact),
            sid,
            ProvenanceRole.CONTEXTUAL,
        )
        claimant = f"{record_key}/{component_key} (bounds the fact)"
    provenance.append(claim)

    # Read the carrier back off the emitted claim rather than off the table it
    # is about to be compared with.
    if claim.target_kind is ProvenanceTargetKind.RECORD:
        derived: tuple[object, ...] = ("record", claim.target_key[0])
    elif claim.target_kind is ProvenanceTargetKind.REFERENCE:
        derived = ("reference", claim.target_key[0], claim.target_key[-1])
    else:
        emitted = FACT_OF[(claim.target_key[0], claim.target_key[1])]
        derived = (
            ("fact", claim.target_key[0], claim.target_key[1], emitted.FAMILY.value)
            if claim.role is ProvenanceRole.PRIMARY
            else ("fact_context", claim.target_key[0], claim.target_key[1])
        )
    DERIVED[clause_id] = derived

    audit.append(
        {
            "clause": clause_id,
            "record": LEAF_RECORD[leaf_id],
            "leaf": leaf_id,
            "printed_page": LEAF_BY_ID[leaf_id].page_index + 1,
            "span_id": sid,
            "range": [start, end],
            "text": _text(clause_id),
            "disposition": span.disposition.value,
            "claimant_kind": kind,
            "claimant": claimant,
            "role": claim.role.value,
            "gaps": list(gaps),
            "states": OBLIGATION_TEXT.get(clause_id),
            "rationale": RATIONALE[kind],
        }
    )

#: **Omission, duplication, semantic loss** — the three ways a composition can
#: be wrong while still validating, checked against the reviewed table.
assert len(spans) == len(CLAUSE_ORDER) == 43, len(spans)
assert len({s.span_id for s in spans}) == 43, "a span id repeats"
for _cid in CLAUSE_ORDER:
    _mine = [s for s in spans if s.span_id == _span_id(_cid)]
    assert len(_mine) == 1, f"{_cid}: discharged by {len(_mine)} spans"
    assert (_mine[0].char_start, _mine[0].char_end) == _extent(_cid), _cid
    assert _mine[0].leaf_id == _leaf(_cid), _cid
_carrier_drift = {
    cid: (EXPECTED[cid][2], DERIVED[cid])
    for cid in CLAUSE_ORDER
    if EXPECTED[cid][2] != DERIVED[cid]
}
assert not _carrier_drift, f"the emission does not carry what the review says: {_carrier_drift}"
_disposition_drift = {
    a["clause"]: a["disposition"]
    for a in audit
    if a["disposition"] != DISPOSITION_OF[EXPECTED[a["clause"]][1]].value
}
assert not _disposition_drift, _disposition_drift

# --- The drafted representation --------------------------------------------
#
# Every component is STRUCTURED and holds exactly one fact: each of the twenty-
# four substantive clauses states one closed printed rule, and nothing is left
# over for governing prose to carry. **Zero prose bindings**, and that is a
# positive claim: `ProseBindingDraft` requires one of the six closed reasons in
# `policy.IRREDUCIBILITY_REASONS`, and none is affirmatively true of any clause
# in this class. Binding one anyway would record a vocabulary gap as an
# irreducibility, which is the misfiling the closed catalog exists to prevent.
COMPONENTS = tuple(
    ComponentDraft(
        record_key=record_key,
        semantic_key=component_key,
        handling=ComponentHandling.STRUCTURED,
        facts=(fact,),
    )
    for record_key, component_key, fact, _ in COMPOSITION
)
for _c in COMPONENTS:
    assert _c.facts, _c
    for _f in _c.facts:
        assert not fact_invariant_violations(_f), (
            f"{_c.record_key}/{_c.semantic_key}",
            type(_f).__name__,
            fact_invariant_violations(_f),
        )

DRAFT = RepresentationDraft(
    records=tuple(
        RecordDraft(semantic_key=key, kind=RECORD_KIND[key]) for key in RECORDS_IN_ORDER
    ),
    components=COMPONENTS,
    prose_bindings=(),
    relationships=(),
    references=REFERENCES,
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
standalone = list(validate_representation(DRAFT, LEDGER, CORPUS))

# --- Source canaries: derived, then compared. A mismatch is stop-and-explain -
CANARIES = {
    "records": (len(DRAFT.records), 7),
    "represented_leaves": (len(touched), 20),
    "policy_exclusions": (len(POLICY_EXCLUDED), 0),
    "container_leaves": (len(touched) + len(POLICY_EXCLUDED), 20),
    "clauses": (len(CLAUSE_ORDER), 43),
    "substantive_clauses": (
        sum(1 for s in spans if s.disposition is SemanticDisposition.SUBSTANTIVE),
        24,
    ),
    "facts": (sum(len(c.facts) for c in COMPONENTS), 23),
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
    content = MANIFEST_LEAVES[lid]
    rebuilt = "".join(content[s.char_start : s.char_end] for s in ordered)
    assert rebuilt == content, f"{lid}: partition does not reproduce the leaf"
    prev = 0
    for s in ordered:
        assert s.char_start == prev, f"{lid}: gap or overlap at {s.char_start}"
        prev = s.char_end
    assert prev == CORPUS.leaf_lengths[lid], f"{lid}: partition stops short"
    PARTITIONS[lid] = [
        {
            "range": [s.char_start, s.char_end],
            "text": content[s.char_start : s.char_end],
            "disposition": s.disposition.value,
        }
        for s in ordered
    ]

# --- Obligation closure and accounting, derived from the emitted spans ------
OBLIGATION_CLOSURE = {
    cid: {
        "text": _text(cid),
        "disposition": EXPECTED[cid][1],
        "expected_carrier": [str(x) for x in EXPECTED[cid][2]],
        "derived_carrier": [str(x) for x in DERIVED[cid]],
        "agrees": EXPECTED[cid][2] == DERIVED[cid],
        "span": _span_id(cid),
        "range": list(_extent(cid)),
        "gaps": list(EXPECTED[cid][3]),
        "states": OBLIGATION_TEXT.get(cid),
    }
    for cid in CLAUSE_ORDER
}
assert all(row["agrees"] for row in OBLIGATION_CLOSURE.values())

#: "All 43 discharged" is true and, alone, misleading: it counts a clause whose
#: text was handed to a supporting-authority span the same as one whose mechanic
#: entered the typed vocabulary. Classified by CARRIAGE — what the span
#: contributes — not by which element happens to own it.
OBLIGATION_ACCOUNTING: dict[str, object] = defaultdict(list)
for cid in CLAUSE_ORDER:
    bucket = {
        "fact": "typed",
        "record": "supporting_authority_record_owned",
        "reference": "supporting_authority_reference_owned",
        "fact_context": "supporting_authority_bounding_a_fact",
    }[str(DERIVED[cid][0])]
    OBLIGATION_ACCOUNTING[bucket].append(cid)  # type: ignore[union-attr]
OBLIGATION_ACCOUNTING = dict(sorted(OBLIGATION_ACCOUNTING.items()))
OBLIGATION_ACCOUNTING["tally"] = {
    k: len(v) for k, v in OBLIGATION_ACCOUNTING.items() if isinstance(v, list)
}
OBLIGATION_ACCOUNTING["prose_bound"] = []
OBLIGATION_ACCOUNTING["unresolved"] = []
assert sum(
    OBLIGATION_ACCOUNTING["tally"].values()  # type: ignore[union-attr]
) == len(CLAUSE_ORDER), OBLIGATION_ACCOUNTING
assert (
    len(OBLIGATION_ACCOUNTING["typed"]) == 24  # type: ignore[arg-type]
), OBLIGATION_ACCOUNTING["tally"]

#: The closed irreducibility catalog, one line each, saying why *that* code is
#: false of this class rather than asserting a blanket "none of them fit". Keys
#: are checked against the live catalog, so a code added or renamed makes this
#: disclosure fail rather than quietly go stale.
REASON_DISPOSITION = {
    "contextual_applicability": (
        "false of all twenty-four: each states its rule outright. Where a "
        "condition is printed — the unseen-origin conjunction, the two "
        "Emanation movement exceptions, the creator's inclusion override — it "
        "is a closed printed term carried by a field of the fact, not "
        "applicability prose the projection cannot enumerate."
    ),
    "subjective_judgment": (
        "false: nothing is left to anyone's assessment. Every value is a named "
        "member of a closed class the source prints."
    ),
    "open_ended_effect": (
        "false: every effect here is closed. 'Such as a wall' is inline "
        "exemplification inside a substantive clause, and it is deliberately "
        "NOT read as an obstruction vocabulary."
    ),
    "gamemaster_latitude": (
        "false: the source delegates nothing here. The one discretion it prints "
        "belongs to the area's creator, and it is typed — "
        "'excluded unless its creator decides otherwise' is a member, not a "
        "gap."
    ),
    "natural_language_exception": (
        "false: these are the rules, not exceptions carved out of one. "
        "Emanation's two suspensions are printed members of the rule's own "
        "field rather than prose exceptions to it."
    ),
    "fiction_dependent_consequence": (
        "false: each consequence is mechanical and stated. Computing which "
        "lines are blocked, or where the near side of an obstruction is, is "
        "adapter geometry the record never claims to do."
    ),
}
assert sorted(REASON_DISPOSITION) == sorted(
    reason.code for reason in IRREDUCIBILITY_REASONS
), sorted(REASON_DISPOSITION)

# ---------------------------------------------------------------------------
# The schema extension, read off the schema rather than described
# ---------------------------------------------------------------------------

_INTRO_ROWS = [
    row for row in introduction_manifest() if row["introduced_in"] == SCHEMA[0]
]
NEW_FAMILIES = sorted({str(r["name"]) for r in _INTRO_ROWS if r["kind"] == "fact_family"})
_VOCABULARIES = sorted(
    {tuple(r["vocabulary"]) for r in _INTRO_ROWS if r["kind"] == "vocabulary_member"}
)
assert {r["kind"] for r in _INTRO_ROWS} == {"fact_family", "vocabulary_member"}, sorted(
    {str(r["kind"]) for r in _INTRO_ROWS}
)
assert len(NEW_FAMILIES) == 7, NEW_FAMILIES
assert len(_VOCABULARIES) == 11, len(_VOCABULARIES)
#: `CoverDegree` is schema 6's and is reused exactly as schema 6 declared it.
#: Re-minting it would be a second declaration of the same closure, so it is
#: deliberately not a schema-9 vocabulary and that is asserted.
assert tuple(m.value for m in CoverDegree) not in _VOCABULARIES
#: The families this batch actually uses are exactly the families the schema
#: introduced: an admitted-but-unused family would be speculation.
assert NEW_FAMILIES == sorted(
    {fact.FAMILY.value for _, _, fact, _ in COMPOSITION}
), NEW_FAMILIES

#: Decision 4 binds `invariant_manifest()` into schema identity, so this batch's
#: settled intrinsic rules are declared with the schema rather than living only
#: in the validators. Read back here rather than restated.
INTRINSIC_INVARIANTS = [
    dict(row)
    for row in invariant_manifest()
    if str(row["locus"]).removeprefix("fact:") in NEW_FAMILIES
]
assert [row["id"] for row in INTRINSIC_INVARIANTS] == [
    "area_dimension_requirement.dimensions.at-least-one",
    "area_dimension_requirement.dimensions.no-repeats",
    "area_origin.placement.requires-a-stated-extent",
    "area_origin_movement.suspended_by_any_of.at-least-one",
    "area_origin_movement.suspended_by_any_of.no-repeats",
], [row["id"] for row in INTRINSIC_INVARIANTS]

SCHEMA_EXTENSION = {
    "extends_the_schema": True,
    "from_schema": REVIEW_PRIOR_SCHEMA_VERSION,
    "to_schema": SCHEMA[0],
    "new_fact_families": NEW_FAMILIES,
    "new_vocabularies": {
        "count": len(_VOCABULARIES),
        "members": [list(v) for v in _VOCABULARIES],
    },
    "reused_without_re_minting": {
        "CoverDegree": [m.value for m in CoverDegree],
        "why": (
            "the blocked-line rule's threshold is schema 6's vocabulary used "
            "exactly as schema 6 declared it. blocking_cover is typed as the "
            "whole CoverDegree rather than pinned to TOTAL, because the field's "
            "type is the KIND of thing that blocks and the printed threshold is "
            "the VALUE."
        ),
    },
    "intrinsic_invariants_declared": INTRINSIC_INVARIANTS,
    "accepted_families_changed": [],
    "registered_transitions_touched": ["5d-lift-schema-8-to-9"],
    "note": (
        "Seven families over eleven closed vocabularies, one family per gap in "
        "the discovery checkpoint's section 4 except that G1 and G2 share "
        "area_origin: the general point-of-origin rule and the per-shape "
        "placement rule are one fact's fields, so they coexist on a shape "
        "record without either restating the other, and Emanation states a "
        "creature-or-object origin in the same field where the other five "
        "state a point. No field is added to, made required on, or made "
        "nullable on any accepted family and no ownership form changes, which "
        "is what makes the crossing a re-declaration rather than a rewrite."
    ),
    "no_values_no_geometry": (
        "No parameter value, unit, coordinate or grid semantic is represented "
        "anywhere. The source prints none in this class: AreaDimension names "
        "the parameters and says the creating effect supplies them, and "
        "Cylinder's two and Line's two arrive as an ordered tuple rather than "
        "fixed slots. The only 'feet' in the class is Cone's worked example, "
        "which is supporting authority."
    ),
}

# ---------------------------------------------------------------------------
# The frozen review prior, the crossing, and the merge acceptance would validate
# ---------------------------------------------------------------------------


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
assert sorted(b.batch_id for b in PRIOR.batches) == REVIEW_PRIOR_BATCH_IDS, PRIOR.batches
assert {a.batch_id for a in PRIOR.acceptances} == set(REVIEW_PRIOR_BATCH_IDS)
assert (
    PRIOR.oracle.schema_version == REVIEW_PRIOR_SCHEMA_VERSION
), PRIOR.oracle.schema_version
assert PRIOR.oracle.schema_hash == REVIEW_PRIOR_SCHEMA_HASH, PRIOR.oracle.schema_hash
assert (PRIOR.oracle.schema_version, PRIOR.oracle.schema_hash) != SCHEMA
assert {
    coll: len(getattr(PRIOR.oracle.representation, coll))
    for coll in REVIEW_PRIOR_COLLECTIONS
} == REVIEW_PRIOR_COLLECTIONS
assert len(PRIOR.oracle.spans) == REVIEW_PRIOR_SPANS
assert len(PRIOR.oracle.obligations) == REVIEW_PRIOR_OBLIGATIONS
assert {
    a.batch_id: a.schema_version for a in PRIOR.schema_anchors
} == REVIEW_PRIOR_ANCHORS, PRIOR.schema_anchors
#: The identity the Owner accepted, at the scope it holds.
PRIOR_IDENTITY = oracle_identity(PRIOR.oracle)
assert PRIOR_IDENTITY == REVIEW_PRIOR_IDENTITY, PRIOR_IDENTITY

#: **One registered crossing.** The prior is anchored at schema 8; this batch
#: proposes under schema 9, which the twenty-four substantive clauses required.
#: The step is looked up in the registry rather than named, and `verify_lift_path`
#: re-proves the accepted content element by element under the new contract
#: instead of asserting it. Accepted bytes are never restamped: the frozen prior
#: still declares schema 8 after this run, and is asserted unchanged below.
STEPS = lift_path((PRIOR.oracle.schema_version, PRIOR.oracle.schema_hash), SCHEMA)
LIFT_RECORDS = verify_lift_path(STEPS, PRIOR.oracle.representation)
assert [r.lift_id for r in LIFT_RECORDS] == ["5d-lift-schema-8-to-9"], LIFT_RECORDS

#: Reading a superseded prior as current is a *finding*, not a silent pass, and
#: the lift is what clears it.
_unlifted_findings = validate_schema_binding(candidate_from_accepted_inputs(PRIOR))
assert _unlifted_findings, "a superseded prior must not read as current"
LIFTED, _lift_records = lift_accepted_inputs(PRIOR, SCHEMA)
assert [r.lift_id for r in _lift_records] == ["5d-lift-schema-8-to-9"]
assert validate_schema_binding(candidate_from_accepted_inputs(LIFTED)) == ()

#: **Two identities, two scopes.** The frozen file keeps the accepted identity.
#: The lifted copy is a new object with a new identity, because `oracle_payload`
#: carries the representation binding and the lift re-declares exactly that. It
#: is computed and reported, never pinned: it moves with the destination pin.
LIFTED_IDENTITY = oracle_identity(LIFTED.oracle)
assert LIFTED_IDENTITY != PRIOR_IDENTITY
_before_payload = oracle_payload(PRIOR.oracle)
_after_payload = oracle_payload(LIFTED.oracle)
_moved_keys = sorted(
    k
    for k in set(_before_payload) | set(_after_payload)
    if _before_payload.get(k) != _after_payload.get(k)
)
assert _moved_keys == ["representation_schema"], _moved_keys
#: What survives the crossing is the content, and identically rather than
#: equally: the lift rebinds, it does not rebuild. `schema_anchors` matters
#: most — each batch's accepted-under hash is what keeps schema 9 from
#: restamping four batches as one.
assert LIFTED.oracle.representation is PRIOR.oracle.representation
for _field in ("batches", "acceptances", "schema_anchors"):
    assert getattr(LIFTED, _field) is getattr(PRIOR, _field), _field
assert LIFTED.oracle.spans is PRIOR.oracle.spans
assert LIFTED.oracle.obligations is PRIOR.oracle.obligations

SUCCESSION = {
    "prior_schema": PRIOR.oracle.schema_version,
    "batch_schema": SCHEMA[0],
    "lift_required": True,
    "steps": [r.lift_id for r in LIFT_RECORDS],
    "verified_collections": [list(r.verified_collections) for r in LIFT_RECORDS],
    "frozen_prior_identity": PRIOR_IDENTITY,
    "frozen_prior_identity_scope": (
        "the file on disk, which this run reads and never writes. It is the "
        "identity the Owner accepted and it does not move."
    ),
    "lifted_copy_identity_at_this_head": LIFTED_IDENTITY,
    "lifted_copy_identity_scope": (
        "a DIFFERENT object: the in-memory copy this run lifts to schema 9. "
        "Reported rather than pinned, because oracle_payload carries the "
        "representation binding and the lift re-declares exactly that, so this "
        "value moves with every destination-pin change."
    ),
    "payload_keys_that_moved": _moved_keys,
    "inherited_authority_unchanged": {
        "representation_object_is_the_same_object": True,
        "spans_obligations_batches_acceptances_anchors_cross_by_identity": True,
        "per_batch_schema_anchors": REVIEW_PRIOR_ANCHORS,
        "why_anchors_matter": (
            "each accepted batch keeps the hash it was reviewed under. A lift "
            "that re-derived anchors would restamp four batches as one and "
            "erase the distinction succession depends on."
        ),
    },
    "unlifted_prior_read_as_current_is_a_finding": list(_unlifted_findings),
    "note": (
        "the accepted prior is anchored at 5d-representation-schema-8 and this "
        "batch proposes under 5d-representation-schema-9, which the class's "
        "twenty-four substantive clauses required. Exactly one registered "
        "transition separates them and it is exercised here rather than "
        "described. The transition adds fact families and vocabularies; it adds "
        "no field to an accepted family, no ownership form, no nullable field "
        "and no required field, so every accepted fact key, component key and "
        "provenance coordinate has the same canonical form under both "
        "contracts."
    ),
}

MERGED = _merge_representation(LIFTED.oracle.representation, DRAFT)
MERGED_LEDGER = ClassificationLedger(
    package_uuid=BINDING.package_uuid,
    release_version=BINDING.release_version,
    policy_version=SEMANTIC_POLICY_VERSION,
    policy_hash=semantic_policy_hash(),
    spans=tuple(LIFTED.oracle.spans) + tuple(spans),
    batches=(),
    acceptances=(),
)
merged_findings = list(validate_representation(MERGED, MERGED_LEDGER, CORPUS))

# --- Reference scope, enumerated exactly ------------------------------------
#
# What this batch cites, what it resolves, and what is still missing after the
# merge. The last column is the honest one and it is not empty.
_batch_records = {rec.semantic_key for rec in DRAFT.records}
_prior_records = {r.semantic_key for r in PRIOR.oracle.representation.records}
_merged_records = {r.semantic_key for r in MERGED.records}
_cross_batch = sorted(
    {
        (r.from_record_key, r.target_record_key)
        for r in REFERENCES
        if r.target_record_key not in _batch_records
    }
)
#: The only citation this batch makes outside itself, and it does not resolve.
assert _cross_batch == [(UMBRELLA, COVER)], _cross_batch
assert COVER not in _prior_records, "Cover is not in accepted authority"

_prior_missing = sorted(
    {
        r.target_record_key
        for r in PRIOR.oracle.representation.references
        if r.target_record_key not in _prior_records
    }
)
_merged_missing = sorted(
    {
        r.target_record_key
        for r in MERGED.references
        if r.target_record_key not in _merged_records
    }
)
assert _prior_missing == ["glossary.concentration", "glossary.speed"], _prior_missing
assert _merged_missing == [
    "glossary.concentration",
    "glossary.cover",
    "glossary.speed",
], _merged_missing
assert sorted(set(_prior_missing) - set(_merged_missing)) == [], "nothing is resolved"

REFERENCE_SCOPE = {
    "references_emitted": len(REFERENCES),
    "record_owned": sum(
        1 for r in REFERENCES if r.from_component_key == RECORD_OWNED_REFERENCE
    ),
    "from_the_printed_enumeration": [
        f"{clause} -> {target}" for _, target, clause in CITATIONS[:6]
    ],
    "from_see_also": ["Area of Effect/7/0 -> glossary.cover"],
    "targets_defined_by_this_batch": sorted(
        {r.target_record_key for r in REFERENCES if r.target_record_key in _batch_records}
    ),
    "cross_batch_citations": [f"{f} -> {t}" for f, t in _cross_batch],
    "cross_batch_citations_all_resolve_into_the_accepted_prior": False,
    "unresolved_targets_before_this_batch": _prior_missing,
    "unresolved_targets_after_the_merge": _merged_missing,
    "resolved_by_this_batch": [],
    "publishable_alone": False,
    "note": (
        "This batch ADDS ONE unresolved citation and RESOLVES NONE. Six of its "
        "seven references target shapes it defines itself; the seventh is the "
        "umbrella's See-also citation of Cover, which no accepted batch "
        "defines and which this batch does not ingest. Combined with the "
        "accepted prior's two, the missing targets after this batch are "
        "glossary.concentration, glossary.speed and glossary.cover. No "
        "reference closure is invented and nothing here expands into Cover "
        "ingestion."
    ),
    "why_no_back_references": (
        "none of the six shape entries prints a 'See also' leaf, so no citation "
        "of the umbrella is derivable from the source and none is emitted. "
        "'Total Cover' inside Area of Effect/5/3 is a typed CoverDegree member "
        "on the blocked-line fact, not a second citation."
    ),
}

#: Both columns checked against a count DERIVED from the drafts rather than a
#: number chosen in advance: the validator reports one finding per unresolved
#: reference, not one per unresolved target.
UNRESOLVED_FINDINGS = {}
for _column, _found, _refs, _known in (
    ("standalone", standalone, REFERENCES, _batch_records),
    ("merged", merged_findings, MERGED.references, _merged_records),
):
    _dangling = [r for r in _refs if r.target_record_key not in _known]
    assert len(_found) == len(_dangling), (_column, len(_found), len(_dangling))
    for _t in {r.target_record_key for r in _dangling}:
        assert any(_t in f for f in _found), (_column, _t, _found)
    UNRESOLVED_FINDINGS[_column] = {
        "findings": len(_found),
        "distinct_targets": sorted({r.target_record_key for r in _dangling}),
        "citations_per_target": {
            _t: sum(1 for r in _dangling if r.target_record_key == _t)
            for _t in sorted({r.target_record_key for r in _dangling})
        },
        "exact": sorted(_found),
    }

#: **The one standalone finding, asserted as a tuple rather than filtered**, so
#: a second finding cannot hide behind the first.
COVER_FINDING = (
    "reference srd-5.2.1/rules-glossary:'Cover': unknown target record glossary.cover"
)
assert tuple(standalone) == (COVER_FINDING,), standalone
assert UNRESOLVED_FINDINGS["standalone"]["distinct_targets"] == [COVER]
assert len(merged_findings) == 3, merged_findings
assert UNRESOLVED_FINDINGS["merged"]["distinct_targets"] == _merged_missing
assert all("unknown target record" in f for f in merged_findings), merged_findings
assert COVER_FINDING in merged_findings, merged_findings
REFERENCE_SCOPE["validator_findings"] = UNRESOLVED_FINDINGS

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
    _prior_c = getattr(PRIOR.oracle.representation, _coll)
    _new = getattr(DRAFT, _coll)
    _merged_c = getattr(MERGED, _coll)
    OVERLAP[_coll] = sorted(
        str(k)
        for k in (
            {_identity(_coll, e) for e in _prior_c} & {_identity(_coll, e) for e in _new}
        )
    )
    _prior_payload = representation_payload(PRIOR.oracle.representation)[_coll]
    _new_payload = representation_payload(DRAFT)[_coll]
    _merged_payload = representation_payload(MERGED)[_coll]
    ZERO_MOVEMENT[_coll] = {
        "prior_elements": len(_prior_c),
        "prefix_is_byte_identical": _merged_c[: len(_prior_c)] == _prior_c,
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
    "prior_obligations_retained": len(LIFTED.oracle.obligations),
    "zero_movement": ZERO_MOVEMENT,
}
assert not DISJOINT["span_overlap"], DISJOINT["span_overlap"]
assert not DISJOINT["leaf_overlap"], DISJOINT["leaf_overlap"]

# --- Schema legality at every authority-bearing seam ------------------------
STRUCTURAL = [
    *representation_draft_violations(DRAFT),
    *held_structure_violations(DRAFT),
]
_component_rules: list[str] = []
for _c in COMPONENTS:
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
_declared_meaning = list(declared_meaning_violations(DRAFT, SCHEMA[0]))

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
    "declared meaning under this schema (declared_meaning_violations)": len(
        _declared_meaning
    ),
    "component rules (damage + roll outcome + option sets)": len(_component_rules),
    "representation gate, standalone (validate_representation)": len(standalone),
    "representation gate, merged with the lifted four-batch prior": len(
        merged_findings
    ),
    "committed-loader round trip (representation_payload -> _representation)": (
        0 if WIRE_ROUND_TRIP else 1
    ),
    "partition accounting (validate_partition)": len(partition),
    "reason codes (validate_reason_codes)": len(reason_codes),
}
#: Derived from the reference scope above, not pinned: the only findings either
#: gate is permitted to report are unresolved reference targets, and exactly as
#: many as there are dangling citations.
_EXPECTED_NONZERO = {
    "representation gate, standalone (validate_representation)": (
        UNRESOLVED_FINDINGS["standalone"]["findings"]
    ),
    "representation gate, merged with the lifted four-batch prior": (
        UNRESOLVED_FINDINGS["merged"]["findings"]
    ),
}
for _seam, _n in _EXPECTED_NONZERO.items():
    assert SEAMS[_seam] == _n, (SEAMS, _seam)
assert all(v == 0 for k, v in SEAMS.items() if k not in _EXPECTED_NONZERO), SEAMS
assert not _component_rules, _component_rules
assert not _declared_meaning, _declared_meaning

# --- The consumer boundary: what a reader of this authority actually sees ----
#
# `_base_records` is the function every consumer of mechanical authority goes
# through. It is applied to the merged candidate IN MEMORY — nothing is
# persisted, published or activated — and every value below is read back off the
# resulting objects rather than off this run's own dictionaries. This is where
# the distinctions the source prints are proved to survive composition.
CANDIDATE = ProjectionCandidate(
    binding=BINDING,
    classification=MERGED_LEDGER,
    representation=MERGED,
    schema_version=SCHEMA[0],
    schema_hash=SCHEMA[1],
)
_span_text = {a["span_id"]: a["text"] for a in audit}
BASE = _base_records(CANDIDATE)
for _k in RECORDS_IN_ORDER:
    assert _k in BASE, sorted(BASE)


def _effective(record_key: str, component_key: str) -> object:
    component = next(
        c for c in BASE[record_key].components if c.semantic_key == component_key
    )
    (held,) = list(component.facts)
    assert component.handling is ComponentHandling.STRUCTURED, component
    assert component.irreducibility_reason_code is None, component
    assert len(component.governing_prose) == 0, component
    return held


CONSUMER_VIEW: dict[str, object] = {
    key: {
        "kind": BASE[key].kind.value,
        "component_keys": sorted(c.semantic_key for c in BASE[key].components),
        "span_ids": len(BASE[key].span_ids),
    }
    for key in RECORDS_IN_ORDER
}

#: **Per-shape origin, extent and placement**, read back off the projection. The
#: umbrella states only that an origin exists; each shape states how it extends;
#: three state where it sits. Emanation is the discriminating witness: its
#: origin is a creature or an object, not a point.
_origins: dict[str, dict] = {}
for _k in RECORDS_IN_ORDER:
    _held = _effective(_k, ORIGIN)
    _f = _held.fact
    _origins[_k] = {
        "origin": _f.origin.value,
        "extent": None if _f.extent is None else _f.extent.value,
        "placement": None if _f.placement is None else _f.placement.value,
        "fact_span_text": [_span_text.get(x, "<prior>") for x in _held.span_ids],
    }
assert _origins[EMANATION]["origin"] == "creature_or_object", _origins
assert all(
    _origins[k]["origin"] == "point" for k in RECORDS_IN_ORDER if k != EMANATION
), _origins
assert _origins[UMBRELLA]["extent"] is None and _origins[UMBRELLA]["placement"] is None
assert all(_origins[k]["extent"] is not None for k in RECORDS_IN_ORDER if k != UMBRELLA)
assert {k for k in _origins if _origins[k]["placement"]} == {CUBE, CYLINDER}, _origins
#: Every shape is distinguishable from every other, which is the point of a
#: per-shape rule. Cube and Cylinder share an extent - both extend in straight
#: lines - and are told apart by where the source puts their origin, so the
#: discriminating key is the pair, not the extent alone.
assert (
    len({(str(v["extent"]), str(v["placement"])) for k, v in _origins.items() if k != UMBRELLA})
    == 6
), _origins
CONSUMER_VIEW["per_shape_origin_extent_and_placement"] = _origins

#: **Dimension parameters, names in printed order and correct arity.** Cylinder
#: and Line each need two; the other four need one; the umbrella declares none.
_dimensions = {
    _k: [d.value for d in _effective(_k, DIMENSIONS).fact.dimensions]
    for _k in (CONE, CUBE, CYLINDER, EMANATION, LINE, SPHERE)
}
assert _dimensions[CYLINDER] == ["radius_of_the_base", "height"], _dimensions
assert _dimensions[LINE] == ["length", "width"], _dimensions
assert {k: len(v) for k, v in _dimensions.items()} == {
    CONE: 1,
    CUBE: 1,
    CYLINDER: 2,
    EMANATION: 1,
    LINE: 2,
    SPHERE: 1,
}, _dimensions
assert not any(c.semantic_key == DIMENSIONS for c in BASE[UMBRELLA].components)
CONSUMER_VIEW["dimension_parameters_in_printed_order"] = _dimensions

#: **Creator-controlled inclusion**, both polarities, complete over the class.
_inclusion = {
    _k: _effective(_k, INCLUSION).fact.inclusion.value
    for _k in (CONE, CUBE, CYLINDER, EMANATION, LINE, SPHERE)
}
assert {k for k, v in _inclusion.items() if v == "included"} == {
    CYLINDER,
    SPHERE,
}, _inclusion
assert {
    k for k, v in _inclusion.items() if v == "excluded_unless_its_creator_decides_otherwise"
} == {CONE, CUBE, EMANATION, LINE}, _inclusion
CONSUMER_VIEW["origin_inclusion_polarity"] = _inclusion

#: **Both Emanation movement exceptions**, in the order the sentence prints
#: them. One exception is a different and weaker rule.
_movement = [
    m.value for m in _effective(EMANATION, MOVEMENT).fact.suspended_by_any_of
]
assert _movement == ["instantaneous_effect", "stationary_effect"], _movement
CONSUMER_VIEW["emanation_movement_exceptions"] = {
    "suspended_by_any_of": _movement,
    "note": (
        "both printed exceptions. 'stationary effect' had no vocabulary member "
        "anywhere in schema 8 and is a distinct printed kind, not a synonym "
        "for instantaneous."
    ),
}

#: **Cone's width relation**, a named closed member — not a formula the
#: projection evaluates.
_width = _effective(CONE, WIDTH).fact.relation.value
assert _width == "equal_to_that_points_distance_from_the_point_of_origin", _width
CONSUMER_VIEW["cone_width_relation"] = {
    "relation": _width,
    "worked_example_is_supporting_authority": _text("Cone/1/2"),
    "note": (
        "a named closed member a hand-authored adapter interprets, which is the "
        "'approved and bounded typed mechanic shape' ADR-005c Decision 3 and "
        "ADR-005d Decision 4 describe. Encoding the taper as an evaluated "
        "expression would be the forbidden thing; the 15-foot example stays "
        "supporting authority rather than becoming a fact with a value in it."
    ),
}

#: **The all-lines rule and its Total Cover threshold.** The quantifier is the
#: whole rule: one blocked line among many excludes nothing.
_blocked = _effective(UMBRELLA, BLOCKED).fact
assert _blocked.blocked is ALL_BLOCKED, _blocked
assert _blocked.blocking_cover is CoverDegree.TOTAL, _blocked
_blocked_spans = sorted(_effective(UMBRELLA, BLOCKED).span_ids)
assert len(_blocked_spans) == 2, _blocked_spans
CONSUMER_VIEW["blocked_line_rule"] = {
    "blocked": _blocked.blocked.value,
    "blocking_cover": _blocked.blocking_cover.value,
    "claimed_primary_by": [_span_text[s] for s in _blocked_spans],
    "note": (
        "two clauses, one rule, both PRIMARY on their own spans: the source "
        "states the exclusion in one sentence and the threshold that makes a "
        "line blocked in the next. WHICH lines are blocked in a given "
        "situation is adapter geometry and is explicitly outside 5d."
    ),
}

#: **The unseen-origin conjunction and its near-side result.** Three fields,
#: all three required: an unseen point AND an intervening obstruction gives a
#: near-side origin.
_unseen = _effective(UMBRELLA, UNSEEN).fact
assert _unseen.placement is UnseenPlacement.AT_AN_UNSEEN_POINT
assert _unseen.obstruction is InterveningObstruction.BETWEEN_THE_CREATOR_AND_THE_POINT
assert _unseen.relocated_to is RelocatedOrigin.NEAR_SIDE_OF_THE_OBSTRUCTION
CONSUMER_VIEW["unseen_origin_relocation"] = {
    "placement": _unseen.placement.value,
    "obstruction": _unseen.obstruction.value,
    "relocated_to": _unseen.relocated_to.value,
    "note": (
        "a closed conjunction. 'such as a wall' is inline exemplification "
        "inside the substantive clause and is deliberately not read as an "
        "obstruction vocabulary."
    ),
}

#: The umbrella's six citations now resolve into records this batch defines;
#: the seventh does not and is named. References live on the representation
#: rather than the effective record, so the reachability claim is made where the
#: citations are and checked against what the projection assembles.
_umbrella_targets = sorted(
    {r.target_record_key for r in MERGED.references if r.from_record_key == UMBRELLA}
)
assert _umbrella_targets == sorted(
    [CONE, CUBE, CYLINDER, EMANATION, LINE, SPHERE, COVER]
), _umbrella_targets
CONSUMER_VIEW["umbrella_citations"] = {
    "cited": _umbrella_targets,
    "assembled_by_the_projection": sorted(t for t in _umbrella_targets if t in BASE),
    "not_assembled": sorted(t for t in _umbrella_targets if t not in BASE),
    "note": (
        "six of seven resolve into records this batch defines. glossary.cover "
        "does not and is not ingested here."
    ),
}
assert CONSUMER_VIEW["umbrella_citations"]["not_assembled"] == [COVER]

#: The accepted `glossary.hazard` shape this batch reuses for its citations,
#: read off the same projection so "record-owned See-also references" is
#: comparable rather than asserted.
_hazard_refs = [
    r for r in MERGED.references if r.from_record_key == "glossary.hazard"
]
PRECEDENT = {
    "accepted": {
        "record": "glossary.hazard",
        "references": len(_hazard_refs),
        "all_record_owned": all(
            r.from_component_key == RECORD_OWNED_REFERENCE for r in _hazard_refs
        ),
        "components_holding_references": 0,
    },
    "this_batch": {
        "record": UMBRELLA,
        "references": len(REFERENCES),
        "all_record_owned": all(
            r.from_component_key == RECORD_OWNED_REFERENCE for r in REFERENCES
        ),
        "components_holding_references": 0,
    },
    "identical_axes": [
        "from_component_key == RECORD_OWNED_REFERENCE",
        "the definitional framing sentence stays supporting authority",
        "the citation list is the only place the record cites its members",
    ],
    "differing_axis": (
        "glossary.hazard's five targets all exist; one of this umbrella's seven "
        "does not"
    ),
    "note": (
        "glossary.hazard emits its five references from its quoted See-also "
        "list and classifies 'A hazard is an environmental danger.' as "
        "supporting authority. This umbrella does the same with its printed "
        "enumeration and its See-also, and its two framing sentences stay "
        "supporting authority."
    ),
}
assert _hazard_refs, "the accepted precedent record is missing from the merge"
assert PRECEDENT["accepted"]["all_record_owned"], PRECEDENT
assert PRECEDENT["this_batch"]["all_record_owned"], PRECEDENT

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
        f"{ORIGIN_LABEL} (CRD Issue 5d batch areas-of-effect-1, "
        "representation schema 9)"
    ),
)
payload = proposal_payload(PROPOSAL)
ident = proposal_identity(PROPOSAL)
#: No pinned expectation: this is a fresh proposal, so its identity is reported
#: for review rather than asserted against a value chosen in advance.
assert ident != REVIEW_PRIOR_IDENTITY, "the proposal is not the accepted prior"
assert ident != LIFTED_IDENTITY, "the proposal is not the lifted prior"

counts: dict[str, int] = defaultdict(int)
for s in spans:
    counts[s.disposition.value] += 1
per_record: dict[str, dict] = defaultdict(lambda: {"leaves": set(), "spans": 0})
for a in audit:
    rec = per_record[a["record"]]
    rec["leaves"].add(a["leaf"])
    rec["spans"] += 1

COUNTS = {
    "records": len(DRAFT.records),
    "represented_leaves": len(touched),
    "policy_exclusions": len(POLICY_EXCLUDED),
    "clauses": len(CLAUSE_ORDER),
    "spans": len(spans),
    "substantive": counts["substantive"],
    "supporting_authority": counts["supporting_authority"],
    "non_mechanical": counts["non_mechanical"],
    "unresolved": counts["unresolved"],
    "components": len(COMPONENTS),
    "components_structured": sum(
        1 for c in COMPONENTS if c.handling is ComponentHandling.STRUCTURED
    ),
    "components_mixed": sum(
        1 for c in COMPONENTS if c.handling is ComponentHandling.MIXED
    ),
    "components_prose_bound": sum(
        1 for c in COMPONENTS if c.handling is ComponentHandling.PROSE_BOUND
    ),
    "facts": sum(len(c.facts) for c in COMPONENTS),
    "fact_families_used": len({f.FAMILY.value for _, _, f, _ in COMPOSITION}),
    "prose_bindings": len(DRAFT.prose_bindings),
    "references": len(REFERENCES),
    "record_owned_references": sum(
        1 for r in REFERENCES if r.from_component_key == RECORD_OWNED_REFERENCE
    ),
    "relationships": 0,
    "provenance_edges": len(provenance),
    "obligations": len(EXPECTED_OBLIGATIONS),
}
assert COUNTS["spans"] == len(audit) == len(proposed) == 43, COUNTS
assert COUNTS["provenance_edges"] == len(spans), COUNTS
assert (
    COUNTS["substantive"]
    + COUNTS["supporting_authority"]
    + COUNTS["non_mechanical"]
    + COUNTS["unresolved"]
    == COUNTS["spans"]
), COUNTS
assert COUNTS["substantive"] == 24 and COUNTS["supporting_authority"] == 19, COUNTS
assert COUNTS["references"] == COUNTS["record_owned_references"] == 7, COUNTS
assert COUNTS["facts"] == 23 and COUNTS["components"] == 23, COUNTS
assert COUNTS["components_structured"] == 23, COUNTS
assert COUNTS["components_mixed"] == COUNTS["components_prose_bound"] == 0, COUNTS
assert COUNTS["prose_bindings"] == 0, COUNTS
assert COUNTS["unresolved"] == COUNTS["non_mechanical"] == 0, COUNTS
assert COUNTS["fact_families_used"] == 7, COUNTS

COUNT_DERIVATION = {
    "records": (
        "one per source entry in the boundary: the Area of Effect umbrella plus "
        "the six [Area of Effect] entries"
    ),
    "represented_leaves": (
        "distinct leaf ids the spans cover; all 20 of the boundary's 20 "
        "container leaves, because this boundary has no policy exclusion"
    ),
    "clauses": (
        "the reviewed inventory's partition cells, read from the committed "
        "discovery manifest and re-proved gap-free against the bound leaves"
    ),
    "spans": "one per printed clause, at the clause's exact reviewed extent",
    "facts": (
        "23 over 24 substantive clauses: Area of Effect/5/2 and 5/3 jointly "
        "state one BlockedLineExclusionFact and both claim it PRIMARY"
    ),
    "components": (
        "one per family per record, all STRUCTURED, each holding exactly one "
        "fact. The umbrella holds three; Cone and Emanation four each; Cube, "
        "Cylinder, Line and Sphere three each"
    ),
    "references": (
        "six from the umbrella's printed enumeration plus one from its See "
        "also; every one record-owned, because no component of this batch is "
        "the thing doing the citing. None of the six shapes prints a See also, "
        "so no back-reference is derivable"
    ),
    "prose_bindings": (
        "none. No clause in this class matches one of the six closed "
        "irreducibility reasons, so binding any of them would record a "
        "vocabulary gap as an irreducibility"
    ),
    "unresolved": (
        "none. Schema 9 carries all twenty-four substantive clauses, so no "
        "span is emitted UNRESOLVED"
    ),
}

# ---------------------------------------------------------------------------
# Audit document
# ---------------------------------------------------------------------------

AUDIT_DOC: dict[str, object] = {
    "_": (
        "DISPOSABLE REVIEW MATERIAL for CRD Issue 5d batch areas-of-effect-1. "
        "Emitted by " + ORIGIN_LABEL + ". This run accepts nothing, publishes "
        "nothing, activates nothing, retires nothing, writes no database and "
        "never executes the publication gate. It is material for semantic "
        "review."
    ),
    "proposal_identity": ident,
    "batch_selection": {
        "batch_id": "areas-of-effect-1",
        "chosen_by": "complete source membership",
        "rule": (
            "the shape the four accepted batches established: a source-tagged "
            "entry class plus the untagged umbrella glossary rule that defines "
            "the tag. conditions-1 = 15 + Condition; hazards-1 = 5 + Hazard; "
            "actions-1 = 12 + Action; attitudes-1 = 3 + Attitude; "
            "areas-of-effect-1 = 6 + Area of Effect."
        ),
        "membership": {lab: RECORD_KEY[lab] for lab in BATCH_LABELS},
        "tag_classes_in_the_source": {t: len(v) for t, v in TAG_CLASSES.items()},
        "accepted_classes": ["Condition", "Hazard", "Action", "Attitude"],
        "this_class": "Area of Effect",
        "remaining_unaccepted_tagged_classes": [],
        "cross_check": (
            "the tag-derived membership and the six names the umbrella's own "
            "enumeration prints agree in both directions, and the boundary's "
            "twenty leaves are exactly the twenty the reviewed inventory covers"
        ),
        "what_this_is_not": (
            "the corpus #137 governs. This is ONE tagged class of the Rules "
            "Glossary. The full-corpus obligation is untouched and "
            "undischarged, and no count in this artifact is evidence about it."
        ),
    },
    "representation_schema": {"version": SCHEMA[0], "hash": SCHEMA[1]},
    "schema_extension": SCHEMA_EXTENSION,
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
            "five of six values re-derived from the committed PDF by the 5c "
            "pipeline and asserted; persisted_corpus_digest is a function of "
            "persisted rows and verified vector state, so it is carried from "
            "the published CRD Issue 5c release record and disclosed as such."
        ),
    },
    "boundary": {
        "derived_from": (
            "'[Area of Effect]'-tagged entries under Rules Definitions, plus "
            "the untagged 'Area of Effect' umbrella, cross-checked against the "
            "six names the umbrella's own enumeration prints"
        ),
        "labels": BATCH_LABELS,
        "printed_pages": sorted({LEAF_BY_ID[lid].page_index + 1 for lid in touched}),
        "policy_exclusions": POLICY_EXCLUDED,
        "canaries": {
            k: {"derived": v[0], "expected": v[1]} for k, v in CANARIES.items()
        },
        "no_grid_language_in_the_source": (
            "the class prints no 'square', 'grid', 'battle map', 'token' or "
            "'space', so no grid semantic is represented. Recorded here as a "
            "boundary of the source, not a decision of this run."
        ),
    },
    "source_inventory": {
        "manifest": MANIFEST_PATH.relative_to(REPO).as_posix(),
        "manifest_sha256": MANIFEST_DIGEST,
        "generated_by": MANIFEST["generated_by"],
        "carries_dispositions": False,
        "leaves": len(MANIFEST_LEAVES),
        "clauses": len(CLAUSE_ORDER),
        "tie_to_the_bound_source": (
            "every reviewed leaf id exists in the corpus this run just built "
            "from the PDF and holds byte-identical content; the reviewed clause "
            "extents partition each of the twenty leaves end to end, starting "
            "at 0 and stopping at the leaf's length, and the concatenation "
            "reconstructs the leaf byte for byte. The manifest supplies the "
            "reviewed coordinates; the PDF supplies the content."
        ),
    },
    "counts": COUNTS,
    "count_derivation": COUNT_DERIVATION,
    "per_record": {
        r: {"leaves": len(d["leaves"]), "spans": d["spans"]}
        for r, d in sorted(per_record.items())
    },
    "record_shapes": {
        rec.semantic_key: {
            "kind": rec.kind.value,
            "components": sorted(
                c.semantic_key for c in COMPONENTS if c.record_key == rec.semantic_key
            ),
            "facts": {
                c.semantic_key: c.facts[0].FAMILY.value
                for c in COMPONENTS
                if c.record_key == rec.semantic_key
            },
            "prose_bindings": 0,
            "references": sum(
                1 for r in REFERENCES if r.from_record_key == rec.semantic_key
            ),
        }
        for rec in DRAFT.records
    },
    "validation": {
        "seams_reporting_findings": SEAMS,
        "expected_nonzero": _EXPECTED_NONZERO,
        "wire_round_trip": WIRE_ROUND_TRIP,
        "partition": partition,
        "reason_codes": reason_codes,
        "structural": STRUCTURAL,
        "component_rules": _component_rules,
        "declared_meaning": _declared_meaning,
        "standalone_findings": standalone,
        "standalone_findings_asserted_as_a_tuple": [COVER_FINDING],
        "merged_findings": merged_findings,
        "what_zero_would_not_prove": (
            "these judge shape, not fidelity. This batch does not validate "
            "clean and says so: exactly one standalone finding, exactly three "
            "merged, all of the unresolved-reference class."
        ),
    },
    "classification_partitions": {
        lid: {
            "record": LEAF_RECORD[lid],
            "printed_page": LEAF_BY_ID[lid].page_index + 1,
            "content": MANIFEST_LEAVES[lid],
            "cells": PARTITIONS[lid],
        }
        for lid in touched
    },
    "reference_scope": REFERENCE_SCOPE,
    "reference_siting": {
        "rule": (
            "a reference is emitted where the source cites a record as a "
            "defined term, not at every place it says the word"
        ),
        "accepted_precedent": [
            "glossary.hazard emits its five references from its quoted See-also "
            "list; 'A hazard is an environmental danger.' is supporting authority",
            "glossary.condition and glossary.action emit from their printed "
            "enumerations, the only place they cite their members",
        ],
        "applied_here": (
            "the umbrella's six enumeration clauses and its one See-also "
            "citation are the seven references. Its two framing sentences are "
            "the record's own definitional framing and stay supporting "
            "authority. 'Total Cover' in Area of Effect/5/3 is a typed "
            "CoverDegree member inside the blocked-line fact, not a second "
            "citation, and none of the six shapes prints a See also, so no "
            "back-reference to the umbrella is derivable."
        ),
        "reference_keys_are_distinct": len({reference_target_key(r) for r in REFERENCES})
        == len(REFERENCES),
    },
    "schema_stops": [],
    "schema_stops_note": (
        "none open. The eight gaps the discovery checkpoint found are all "
        "closed by schema 9, every one of them witnessed by at least one clause "
        "in this batch, and no span is emitted UNRESOLVED."
    ),
    "gaps_closed": GAPS_WITNESSED,
    "irreducibility_catalog_disposition": dict(REASON_DISPOSITION)
    | {
        "conclusion": (
            "none of the six closed reasons is affirmatively true of any of the "
            "twenty-four substantive clauses, so this batch emits ZERO prose "
            "bindings. That is a positive claim, not an omission: binding one "
            "anyway would record a vocabulary gap as an irreducibility, which "
            "is exactly the misfiling the closed catalog exists to prevent."
        )
    },
    "typed_prose_dispositions": {
        "typed": [
            {
                "record": record_key,
                "component": component_key,
                "family": fact.FAMILY.value,
                "fact": fact_key(fact),
                "clauses": list(clauses),
                "text": [_text(c) for c in clauses],
                "states": OBLIGATION_TEXT[clauses[0]],
            }
            for record_key, component_key, fact, clauses in COMPOSITION
        ],
        "prose_bound": [],
        "supporting_authority": [
            {
                "record": a["record"],
                "clause": a["clause"],
                "carried_by": a["claimant_kind"],
                "claimant": a["claimant"],
                "text": a["text"],
            }
            for a in audit
            if a["disposition"] == "supporting_authority"
        ],
        "unresolved": [],
    },
    "precedent": PRECEDENT,
    "consumer_boundary_proofs": CONSUMER_VIEW,
    "schema_succession": SUCCESSION,
    "accepted_prior": {
        "path": REVIEW_PRIOR_PATH.relative_to(REPO).as_posix(),
        "content_sha256": _prior_content_before,
        "blob": _prior_blob_before,
        "identity": PRIOR_IDENTITY,
        "identity_scope": "the frozen file on disk, read and never written",
        "lifted_copy_identity_at_this_head": LIFTED_IDENTITY,
        "lifted_copy_identity_scope": (
            "a different object, reported rather than pinned; it moves with the "
            "destination schema pin"
        ),
        "batch_ids": REVIEW_PRIOR_BATCH_IDS,
        "collections": REVIEW_PRIOR_COLLECTIONS,
        "spans": REVIEW_PRIOR_SPANS,
        "obligations": REVIEW_PRIOR_OBLIGATIONS,
        "schema_version": PRIOR.oracle.schema_version,
        "per_batch_schema_anchors": REVIEW_PRIOR_ANCHORS,
        "read_only": True,
    },
    "disjointness_from_the_accepted_prior": DISJOINT,
    "obligation_closure": OBLIGATION_CLOSURE,
    "obligation_accounting": OBLIGATION_ACCOUNTING,
    "obligation_derivation": (
        "EXPECTED_OBLIGATIONS in the generator is one literal row per printed "
        "clause, typed from the reviewed source record - section 3 of the "
        "discovery checkpoint for the 5c disposition and the gap ids, section "
        "9's clause-to-fact table for the carrier. It is not computed from "
        "anything this run emits, and the discovery manifest deliberately "
        "carries no disposition, so the table is the independent statement of "
        "what the proposal owes the source. The emission is then checked "
        "against it three ways: every obligation discharged (omission), by "
        "exactly one span at exactly the reviewed extent (duplication), and "
        "carried by exactly the element the review names (semantic loss)."
    ),
    "evidence_classes": [
        {
            "class": "source extraction and partition reconstruction",
            "executed_here": True,
            "strength": (
                "strong for coverage and span boundaries: the reviewed clause "
                "extents are re-proved gap-free against the leaves this run "
                "just extracted from the PDF. Says nothing about whether the "
                "meaning assigned to a span is right - that is what semantic "
                "review is for"
            ),
        },
        {
            "class": "obligation closure against the reviewed inventory",
            "executed_here": True,
            "strength": (
                "exposes omission, duplication and carrier drift against a "
                "table typed from the checkpoint rather than from the "
                "emission. It does not prove the checkpoint's judgment is "
                "right; it proves the proposal states that judgment and no "
                "other"
            ),
        },
        {
            "class": "structural validation",
            "executed_here": True,
            "strength": (
                "the repository's own checkers over the emitted draft and over "
                "the merge acceptance would validate. These judge shape, not "
                "fidelity, and this batch does not come back clean"
            ),
        },
        {
            "class": "consumer projection assertion",
            "executed_here": True,
            "strength": (
                "_base_records is applied to the merged candidate in memory and "
                "every distinction the source prints is read back off those "
                "objects. Nothing is persisted"
            ),
        },
        {
            "class": "schema succession",
            "executed_here": True,
            "strength": (
                "one registered crossing, exercised element by element, with "
                "the inherited acceptance record asserted to cross by object "
                "identity. Proves the crossing; performs none of it"
            ),
        },
        {
            "class": "cross-batch reference resolution",
            "executed_here": True,
            "strength": (
                "NEGATIVE result, stated: this batch adds one unresolved target "
                "and resolves none. Combined missing after the merge is "
                "glossary.concentration, glossary.speed, glossary.cover"
            ),
        },
        {
            "class": "full-corpus completeness",
            "executed_here": False,
            "strength": (
                "NOT claimed. This is one tagged class of the Rules Glossary. "
                "The corpus #137 governs is untouched and undischarged"
            ),
        },
        {
            "class": "publication gate",
            "executed_here": False,
            "strength": (
                "NOT run. There is no persisted projection to run it over, and "
                "this generator must not create one"
            ),
        },
        {
            "class": "acceptance",
            "executed_here": False,
            "strength": (
                "NOT run. accept_proposal is never called; the live oracle is "
                "read as a mutation sentinel only"
            ),
        },
    ],
    "review_disposition": {
        "open_schema_stops": [],
        "residues": [
            "glossary.cover is cited by this batch and defined by no batch; "
            "Cover ingestion is not in this batch and nothing here reaches "
            "into it",
            "glossary.concentration and glossary.speed remain unresolved from "
            "the accepted prior; they belong to a later glossary batch",
            "the full-corpus obligation #137 governs is undischarged: this is "
            "one tagged class",
        ],
        "requires_owner_authorization_before": [
            "any acceptance of this batch into committed authority",
            "any acceptance is also what would carry the accepted prior across "
            "5d-lift-schema-8-to-9; this run proves the crossing and performs "
            "none of it",
        ],
    },
    "repository_inputs": INPUT_PATHS,
    "spans": audit,
}
assert AUDIT_DOC["proposal_identity"] == ident
assert AUDIT_DOC["review_disposition"]["open_schema_stops"] == []


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
    "reproduce_from_the_repository": (
        "python .claude/review-notes/" + ORIGIN_LABEL + "   (from the repository "
        "root). Every input is repository-retained: the committed PDF, the "
        "committed discovery manifest, the committed frozen prior and the "
        "package under src/."
    ),
}

_, _prior_content_after, _prior_blob_after = _review_prior_identifiers()
assert _prior_content_after == _prior_content_before, "the review prior changed"
assert _prior_blob_after == _prior_blob_before, "the review prior's blob id moved"
AUDIT_DOC["accepted_prior"]["content_sha256_after"] = _prior_content_after  # type: ignore[index]
AUDIT_DOC["accepted_prior"]["unchanged"] = (  # type: ignore[index]
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
assert AUDIT_DOC["accepted_prior"]["unchanged"], AUDIT_DOC["accepted_prior"]  # type: ignore[index]

LIVE_ORACLE_UNCHANGED = LIVE_ORACLE_PATH.read_bytes() == _LIVE_ORACLE_BYTES_BEFORE
assert LIVE_ORACLE_UNCHANGED, "this run modified the live accepted-authority oracle"

# ---------------------------------------------------------------------------
# Determinism: a clean rerun must reproduce identical bytes and identity
# ---------------------------------------------------------------------------
RERUN = os.environ.get("AREASOFEFFECT1_RERUN") == "1"
FINAL_SHA256 = {
    PROPOSAL_FILE: hashlib.sha256(_proposal_bytes).hexdigest(),
    AUDIT_FILE: hashlib.sha256(_audit_bytes).hexdigest(),
}
DETERMINISTIC: bool | None = None
if not RERUN:
    _child = subprocess.run(
        [sys.executable, str(Path(__file__).resolve())],
        env={**os.environ, "AREASOFEFFECT1_RERUN": "1"},
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
print(f"manifest       {MANIFEST_PATH}  ({MANIFEST_DIGEST})")
print(f"review prior   {REVIEW_PRIOR_PATH}")
print(f"live oracle    {LIVE_ORACLE_PATH}  (sentinel only, not an input)")
print(f"output dir     {OUT}")
print(f"schema         {SCHEMA[0]} / {SCHEMA[1]}")
print(f"policy         {SEMANTIC_POLICY_VERSION} / {semantic_policy_hash()}")
print(f"identity       {ident}")
print()
print(f"batch          areas-of-effect-1: {', '.join(BATCH_LABELS)}")
print(f"tag classes    {json.dumps({t: len(v) for t, v in TAG_CLASSES.items()})}")
print(f"records        {len(DRAFT.records)}")
print(
    f"leaves         {len(touched)} represented + {len(POLICY_EXCLUDED)} policy "
    f"exclusions = {len(touched) + len(POLICY_EXCLUDED)} container leaves"
)
print(f"clauses        {len(CLAUSE_ORDER)} (reviewed inventory, re-proved gap-free)")
print(f"spans          {len(spans)}")
for k in ("substantive", "supporting_authority", "non_mechanical", "unresolved"):
    print(f"  {k:22} {counts[k]}")
print(f"components     {len(COMPONENTS)}  (all STRUCTURED)")
for c in COMPONENTS:
    print(f"  {c.record_key}/{c.semantic_key}: {c.facts[0].FAMILY.value}")
print(f"facts          {COUNTS['facts']} over {COUNTS['substantive']} substantive clauses")
print(f"prose bindings {COUNTS['prose_bindings']}  (none; no closed reason is true)")
print(f"references     {len(REFERENCES)} ({COUNTS['record_owned_references']} record owned)")
print(f"provenance     {len(provenance)}")
print("relationships  0")
print()
print(f"{'record':28} {'leaves':>6} {'spans':>6}")
for r in sorted(per_record):
    d = per_record[r]
    print(f"{r:28} {len(d['leaves']):6} {d['spans']:6}")
print()
for name, found in (
    ("partition", partition),
    ("structural", STRUCTURAL),
    ("component rules", _component_rules),
    ("declared meaning", _declared_meaning),
    ("reason codes", reason_codes),
    ("representation (standalone)", standalone),
    ("representation (merged w/ lifted prior)", merged_findings),
):
    print(f"{name:44} {len(found)}")
    for f in found:
        print("   -", f)
print()
print(f"wire trip      {WIRE_ROUND_TRIP}")
print(
    f"obligations    {len(EXPECTED_OBLIGATIONS)} accounted for; "
    + ", ".join(
        f"{k}={v}"
        for k, v in OBLIGATION_ACCOUNTING["tally"].items()  # type: ignore[union-attr]
    )
)
print(f"gaps closed    {GAPS_WITNESSED}")
print(
    f"schema change  {SCHEMA[0]} (+{len(NEW_FAMILIES)} families, "
    f"+{len(_VOCABULARIES)} vocabularies, "
    f"{len(INTRINSIC_INVARIANTS)} declared invariant rows)"
)
print(
    f"succession     {REVIEW_PRIOR_SCHEMA_VERSION} -> {SCHEMA[0]} via "
    f"{SUCCESSION['steps']}, verified element by element"
)
print(f"prior identity (frozen file)   {PRIOR_IDENTITY}")
print(f"prior identity (lifted copy)   {LIFTED_IDENTITY}  (reported, not pinned)")
print(f"payload keys moved by the lift {_moved_keys}")
print(f"refs cited     {REFERENCE_SCOPE['cross_batch_citations']}")
print(f"unresolved before  {REFERENCE_SCOPE['unresolved_targets_before_this_batch']}")
print(f"unresolved after   {REFERENCE_SCOPE['unresolved_targets_after_the_merge']}")
print(f"resolved by this   {REFERENCE_SCOPE['resolved_by_this_batch']}  (adds one, resolves none)")
print(
    "publishable    False  (proposed only; not accepted, not activated, "
    "publication gate not executed)"
)
print(f"consumer       umbrella cites {len(_umbrella_targets)}; unresolved {CONSUMER_VIEW['umbrella_citations']['not_assembled']}")
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
