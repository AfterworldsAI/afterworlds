"""CRD Issue 5d — batch `speed-1`, representation schema 11.

Executable generator for the speed-1 proposal and its audit. It reads the
committed SRD through the 5c pipeline, re-derives the Speed population from the
source's own reciprocal citation, takes the reviewed clause coordinates from the
committed discovery manifest, re-proves that those coordinates cut the *bound*
leaves gap-free and byte-for-byte, assigns every clause to the element or
elements that state it, and writes two deterministic LF artifacts. It accepts
nothing, publishes nothing, activates nothing, retires nothing and touches no
database.

The label is not the query
--------------------------
Four entry containers in the bound release are labeled ``Speed``: a character
species pointer, a vehicle-speed homonym, a stat-block pointer, and the Rules
Glossary definition. Three of them are not this rule. So membership here is the
**printed reciprocal citation**, asserted rather than assumed: the glossary
entry's *See also* leaf names ``"Playing the Game" ("Combat")``, and exactly one
leaf in the whole release prints ``See "Rules Glossary" for more about Speed``
back at it. That leaf's own container — labeled ``Movement and Position``, not
``Speed`` — is the second site. A release in which that structure moved fails
this run rather than being silently re-cut.

A co-occurrence test over the same subsection would have matched three entries.
``Movement and Position`` *is* the second site, so it is a member; the two the
naive test **adds**, ``Dropping Prone`` and ``Mounting and Dismounting``, cite
the glossary for something other than Speed and are asserted non-members here.

Printing the word is use, not definition. 557 other leaves in the bound release
contain ``speed`` in any case — 288 of them in ``Monsters A–Z`` stat blocks
alone — and every one of them is already represented by 5c. The boundary is
re-derived here with the discovery script's exact rule and checked against the
reviewed manifest's enumeration rather than transcribed.

One composite record, two printed sites
---------------------------------------
``glossary.speed`` is **one** record assembled from both sites, the second such
record in this build after ``glossary.cover``. Three of its sentences are
printed **across a leaf boundary** — the special-speeds sentence spans
``glossary/5/0``, ``6/0`` and ``7/0``; the halving example spans ``glossary/9/2``,
``10/0`` and ``11/0``; the base allowance spans ``combat/1/0`` and ``2/0``. This
run reconstructs each and asserts it against the reviewed manifest, because a
clause that only means something in company must be shown to keep that company.

Nine outgoing references, one of them split
-------------------------------------------
The glossary *See also* cites five entries by name, and the definition sentence
names four special speeds it says are *"each of which is defined in this
glossary"*. That is nine references. **``Fly Speed`` is printed across the
``glossary/5/0``–``6/0`` leaf boundary**, so its one reference carries two
provenance claims rather than one: ``_validate_provenance`` rejects only exact
duplicate edges, so two distinct spans claiming one reference is admissible, and
it is what the source did — it printed the term once, across a break.

None of the nine targets exists in the frozen six-batch prior, and the prior
carries two unresolved targets of its own (``glossary.concentration`` and
``glossary.speed``). This batch **defines** ``glossary.speed``. So standalone it
produces nine unresolved findings over nine targets, and merged with the lifted
prior, ten over ten. That combined figure is **measured here** through
``acceptance._merge_representation`` and ``oracle.candidate_from_accepted_inputs``
rather than computed as arithmetic over two sets: the merge seam exists and this
run executes it in memory.

Nothing is accepted by that. Current accepted authority still carries exactly
two unresolved targets; the resolution of ``glossary.speed`` becomes a property
of accepted authority only at an acceptance that has not happened.

Expected obligations, and what they are derived from
----------------------------------------------------
``EXPECTED_OBLIGATIONS`` is one literal row per printed clause, typed from the
**reviewed source record** — §3 of the discovery checkpoint for the 5c
disposition, §4's gap table for the gap ids and its witness lists. Unlike the
five accepted batches, a row here carries a **tuple** of carriers: this
population prints sentences that state a fact *and* cite an entry in the same
breath, and ``glossary/5/0`` alone claims seven targets. The table is
deliberately *not* computed from anything this file emits, and the manifest
carries no disposition at all, so this table is the only place the review's
judgment enters. The emission is then checked three ways: **omission** (every
one of the thirty-six discharged), **duplication** (by exactly one span, at
exactly the manifest's extent) and **semantic loss** (carried by exactly the
elements the review names).

Schema
------
**Representation schema 11**, seven new fact families over eleven new closed
vocabularies plus **one member added to an accepted one**: ``MovementMode``
carried six of its seven members from schema 3 and gains ``jump`` here. Two
families are reused rather than minted — ``movement_allowance`` (schema 6, which
gains one optional ``window`` field) and ``movement_permission`` (schema 3).

The crossing is the registered transition ``5d-lift-schema-10-to-11``, exercised
below against the frozen accepted six-batch prior.

What this run is, and is not
----------------------------
* It is *proposal preparation*. It is material for semantic review. Span
  granularity is **proposed**, not final.
* Nothing here is accepted, activated, published or retired. ``accept_proposal``
  is never called and the publication gate is not executed.
* The accepted six-batch prior is read **only** as a frozen review prior, by
  content identity, and asserted unchanged afterwards. The live oracle is read
  as a mutation sentinel and is never an input.
* No geometry is computed and no number is invented. ``SpeedDefinitionFact``
  names the foot that *"the distance in feet"* prints and carries no quantity;
  no schema-11 vocabulary mentions a square, a segment or a corner.
* One record of the corpus #137 governs. The full-corpus obligation is untouched
  and undischarged.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
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
#: review: conditions-1, hazards-1, actions-1, attitudes-1, areas-of-effect-1 and
#: cover-1, representation schema 10. Read only, by content identity, and
#: asserted unchanged at the end.
REVIEW_PRIOR_PATH = (
    REPO
    / "tests/ingestion/mechanical/data"
    / (
        "accepted_prior_conditions_1_hazards_1_actions_1"
        "_attitudes_1_areas_of_effect_1_cover_1.json"
    )
)

#: **The reviewed clause inventory.** Discovery output, committed, and pinned by
#: digest below: coordinates only, no disposition.
MANIFEST_PATH = OUT / "issue-5d-speed-1-source-manifest.json"

#: **A mutation sentinel, never an input.**
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
#: bytes a working copy holds.
REVIEW_PRIOR_CONTENT_SHA256 = "391c71b72d7fa9406890c74eed9a505278ea4f8f4536a01cd3db1edf403f6407"  # noqa: E501  # pragma: allowlist secret
REVIEW_PRIOR_BLOB = (
    "b7c0149432072d4a3b151d0f9b2c458252e584da"  # pragma: allowlist secret
)
#: The identity the Owner accepted, at the scope it holds: the frozen file on
#: disk. The lifted copy's identity is a different value at a different scope and
#: is computed and reported below rather than pinned here.
REVIEW_PRIOR_IDENTITY = "86cd11c2be330f5962982d8d87dfc1847815710868223257529f30bef8cdb500"  # noqa: E501  # pragma: allowlist secret
REVIEW_PRIOR_BATCH_IDS = [
    "actions-1",
    "areas-of-effect-1",
    "attitudes-1",
    "conditions-1",
    "cover-1",
    "hazards-1",
]
REVIEW_PRIOR_SCHEMA_VERSION = "5d-representation-schema-10"
REVIEW_PRIOR_SCHEMA_HASH = "c39e3a35e197a1d1db5c2c2b3445ff0cbf03395c91e3426353a4bce589be4be0"  # noqa: E501  # pragma: allowlist secret
#: What the six accepted batches hold together, named collection by collection so
#: one that silently gained or lost an element fails by name, not by total.
REVIEW_PRIOR_COLLECTIONS = {
    "records": 47,
    "components": 136,
    "prose_bindings": 49,
    "relationships": 0,
    "references": 53,
    "provenance": 575,
}
REVIEW_PRIOR_SPANS = 558
REVIEW_PRIOR_OBLIGATIONS = 47
#: Each accepted batch keeps the hash it was reviewed under.
REVIEW_PRIOR_ANCHORS = {
    "conditions-1": "5d-representation-schema-3",
    "hazards-1": "5d-representation-schema-5",
    "actions-1": "5d-representation-schema-7",
    "attitudes-1": "5d-representation-schema-8",
    "areas-of-effect-1": "5d-representation-schema-9",
    "cover-1": "5d-representation-schema-10",
}
#: The prior's own unresolved cross-batch reference targets, before this batch.
REVIEW_PRIOR_UNRESOLVED = ("glossary.concentration", "glossary.speed")

#: The reviewed inventory, pinned. Checked before the file is parsed.
MANIFEST_SHA256 = "8c8ea8eed38feaeb28d74386690b5ee28e43872b1316517b922fb89afa016b20"  # noqa: E501  # pragma: allowlist secret

# --- Retained-evidence guard ------------------------------------------------
PROPOSAL_FILE = "issue-5d-batch-speed-1-PROPOSAL.json"
AUDIT_FILE = "issue-5d-batch-speed-1-audit.json"
WRITES = {PROPOSAL_FILE, AUDIT_FILE}
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
    release_binding_payload,
    representation_payload,
    validate_candidate,
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
    ComponentDraft,
    DistanceUnit,
    FactFamily,
    MechanicalFact,
    MovementAllowanceBasis,
    MovementAllowanceFact,
    MovementComposition,
    MovementCompositionFact,
    MovementDepletionFact,
    MovementDepletionResolution,
    MovementDepletionTerminator,
    MovementMode,
    MovementPermissionFact,
    MovementWindow,
    ProvenanceClaim,
    ProvenanceRole,
    ProvenanceTargetKind,
    RecordDraft,
    RecordKind,
    ReferenceDraft,
    RepresentationDraft,
    SpecialSpeedFact,
    SpecialSpeedListing,
    SpeedChangePropagationFact,
    SpeedDefinitionFact,
    SpeedPropagationDuration,
    SpeedPropagationMagnitude,
    SpeedPropagationScope,
    SpeedSelection,
    SpeedSelectionFact,
    SpeedSwitchAccounting,
    SpeedSwitchLimitFact,
    SpeedSwitchOutcome,
    component_damage_composition_violations,
    component_roll_outcome_violations,
    component_target_key,
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

#: **Schema 11's exact declared pin.** Asserted against the value the schema
#: computes at this head, so a payload edit that moved the hash fails here rather
#: than minting a proposal under a contract nobody reviewed.
SCHEMA = (REPRESENTATION_SCHEMA_VERSION, representation_schema_hash())
assert SCHEMA[0] == "5d-representation-schema-11", SCHEMA
assert SCHEMA[1] == (
    "605e8b4cfdaf0cb6d4f0b65fcf0d23f3e45c4734404c9568f41dc4261eefd037"  # noqa: E501  # pragma: allowlist secret
), SCHEMA

# ---------------------------------------------------------------------------
# Bound release - derived from the committed PDF, asserted against production
# ---------------------------------------------------------------------------

PACKAGE_UUID = "4458fa10-4a66-5e0e-9ecc-ea37530ad2b4"
RELEASE_VERSION = "5.2.1-corpus.36b786d8-fa2"
SOURCE_SHA256 = "8974902d109d6e63672d7c490bde9ccf052410503d9cfa768237154fbc5e3d87"  # noqa: E501  # pragma: allowlist secret
TRANSFORM_CONFIG_HASH = "77720c2f3b8c9b88363d48050466fb8e3a26f8476b63145d1b5928ff2581ef3e"  # noqa: E501  # pragma: allowlist secret
BUNDLE_ROOT_HASH = "03353dfb79790aee7260b9ed96055b7296cd6f70e3e6f97d6cbe0a2484279685"  # noqa: E501  # pragma: allowlist secret

#: The only binding value not rederived from the PDF here. Recomputing it needs a
#: session over the persisted `rp_sources` rows plus read-back vector state
#: (`persistence.recompute_persisted_digest`); verifying a published release
#: against declared values is `operational.load_verified_operational_corpus`, the
#: narrower downstream trust seam. Neither requires a publish; this run performs
#: neither, and produced no operational database evidence at all.
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

# --- The six-part binding, through the seam that defines it -----------------
BINDING_PARTS = release_binding_payload(BINDING)
BINDING_REDERIVED_HERE = {
    "package_uuid": CAND.package_uuid,
    "release_version": CAND.release_version,
    "authoritative_source_hash": CAND.authoritative_source_hash,
    "transform_config_hash": CAND.transform_config_hash,
    "bundle_root_hash": CAND.bundle.bundle_root_hash,
}
BINDING_DISCLOSED = {"persisted_corpus_digest": PERSISTED_CORPUS_DIGEST}
assert len(BINDING_PARTS) == 6, BINDING_PARTS
assert BINDING_PARTS == {**BINDING_REDERIVED_HERE, **BINDING_DISCLOSED}, BINDING_PARTS
assert BINDING_REDERIVED_HERE == {
    "package_uuid": PACKAGE_UUID,
    "release_version": RELEASE_VERSION,
    "authoritative_source_hash": SOURCE_SHA256,
    "transform_config_hash": TRANSFORM_CONFIG_HASH,
    "bundle_root_hash": BUNDLE_ROOT_HASH,
}, BINDING_REDERIVED_HERE
assert BINDING_PARTS["package_uuid"] == CORPUS.package_uuid
assert BINDING_PARTS["release_version"] == CORPUS.release_version


def _ancestry(cid: str) -> list[str]:
    out, cur = [], CONTAINERS.get(cid)
    while cur:
        out.append(cur.container_id)
        cur = CONTAINERS.get(cur.parent_id) if cur.parent_id else None
    return out


def _path_of(cid: str) -> str:
    return " > ".join(LABELS[c] for c in reversed(_ancestry(cid)))


by_container: dict[str, list] = defaultdict(list)
for _leaf_obj in LEDGER_OBJ.leaves:
    for _cid in _leaf_obj.container_path:
        by_container[_cid].append(_leaf_obj)
for _group in by_container.values():
    _group.sort(key=lambda x: (x.page_index, x.char_start))

# ---------------------------------------------------------------------------
# The reviewed inventory, read rather than retyped — then re-proved
# ---------------------------------------------------------------------------
#
# The manifest is parsed *before* membership is derived, because unlike the six
# accepted batches this population has no label to query: the second site is
# reached through a sentence, and the sentence's leaf id is a coordinate. Every
# coordinate the manifest supplies is re-checked against the live bound corpus
# below, so reading it is not trusting it.

_manifest_raw = MANIFEST_PATH.read_bytes()
_manifest_canonical = _manifest_raw.replace(b"\r\n", b"\n")
MANIFEST_DIGEST = hashlib.sha256(_manifest_canonical).hexdigest()
assert MANIFEST_DIGEST == MANIFEST_SHA256, MANIFEST_DIGEST
MANIFEST = json.loads(_manifest_canonical.decode("utf-8"))
assert MANIFEST["artifact_kind"] == "source_discovery_manifest", MANIFEST[
    "artifact_kind"
]
assert MANIFEST["batch_id"] == "speed-1", MANIFEST["batch_id"]
#: The manifest carries coordinates, never dispositions, and never a candidate
#: record key. Asserted, because the obligation table below is only independent
#: evidence if the manifest is not quietly carrying the same judgment.
assert not any(
    "disposition" in row for row in MANIFEST["clauses"]
), "the manifest must not carry dispositions"
assert "records" not in MANIFEST, "the manifest must not carry a record assignment"

# --- Membership, re-derived from the source's own reciprocal citation -------
#
# Four entry containers are labeled `Speed`; three of them are a species
# pointer, a vehicle-speed homonym and a stat-block pointer. The join the source
# itself prints is asserted instead.
SPEED_LABELED = sorted(
    (
        c
        for c in LEDGER_OBJ.containers
        if c.container_type == "entry" and c.label == "Speed"
    ),
    key=lambda c: _path_of(c.container_id),
)
SPEED_LABELED_PATHS = [_path_of(c.container_id) for c in SPEED_LABELED]
assert len(SPEED_LABELED) == 4, SPEED_LABELED_PATHS
assert (
    SPEED_LABELED_PATHS == MANIFEST["membership"]["containers_labeled_speed"]
), SPEED_LABELED_PATHS
_glossary_matches = [
    c
    for c in SPEED_LABELED
    if _path_of(c.container_id) == "Rules Glossary > Rules Definitions > Speed"
]
assert len(_glossary_matches) == 1, SPEED_LABELED_PATHS
GLOSSARY_ENTRY = _glossary_matches[0]

#: **The second site is reached through a printed sentence, not through a
#: label.** Its container is labeled `Movement and Position`, so a label query
#: would have missed it while matching three entries that are not this rule. The
#: sentence is asserted unique release-wide: if a second leaf printed it, the
#: derivation would be ambiguous and this run stops.
INBOUND = MANIFEST["direction"]["inbound"]
INBOUND_SENTENCE = str(INBOUND["sentence"])
_inbound_leaves = sorted(
    leaf.leaf_id for leaf in LEDGER_OBJ.leaves if INBOUND_SENTENCE in leaf.content
)
assert _inbound_leaves == [INBOUND["leaf_id"]], _inbound_leaves
assert int(INBOUND["occurrences_in_the_whole_release"]) == 1, INBOUND
COMBAT_ENTRY = CONTAINERS[LEAF_BY_ID[INBOUND["leaf_id"]].container_path[-1]]
assert LABELS[COMBAT_ENTRY.container_id] == "Movement and Position", LABELS[
    COMBAT_ENTRY.container_id
]
assert (
    _path_of(COMBAT_ENTRY.container_id)
    == "Playing the Game > Combat > Movement and Position"
), _path_of(COMBAT_ENTRY.container_id)

SITES = (
    ("glossary", GLOSSARY_ENTRY.container_id),
    ("combat", COMBAT_ENTRY.container_id),
)
SITE_OF_CONTAINER = {cid: site for site, cid in SITES}

#: And the citation in the other direction: the glossary entry's own *See also*
#: leaf, and the leaf that names the second site's section and subsection.
OUTBOUND = MANIFEST["direction"]["outbound"]
assert (
    LEAF_BY_ID[OUTBOUND["see_also_leaf_id"]].content == "See also"
), OUTBOUND["see_also_leaf_id"]
_CITATION_TEXT = LEAF_BY_ID[OUTBOUND["citation_leaf_id"]].content
assert _CITATION_TEXT == OUTBOUND["citation_text"], OUTBOUND["citation_leaf_id"]
assert LABELS[_ancestry(COMBAT_ENTRY.container_id)[2]] in _CITATION_TEXT
assert LABELS[_ancestry(COMBAT_ENTRY.container_id)[1]] in _CITATION_TEXT
assert OUTBOUND["names_section"] == LABELS[_ancestry(COMBAT_ENTRY.container_id)[2]]
assert OUTBOUND["names_subsection"] == LABELS[_ancestry(COMBAT_ENTRY.container_id)[1]]

#: The corroborating sentence, from outside the population: `Your Turn` points
#: forward to `Movement and Position` for the movement rules. It is direction
#: evidence, not membership — it is asserted to be outside the population.
CORROBORATION = MANIFEST["direction"]["corroboration"]
_corr_leaves = sorted(
    leaf.leaf_id
    for leaf in LEDGER_OBJ.leaves
    if str(CORROBORATION["sentence"]) in leaf.content
)
assert _corr_leaves == [CORROBORATION["leaf_id"]], _corr_leaves
assert CORROBORATION["in_the_population"] is False

DIRECTION = {
    "outbound": {
        "from_site": "glossary",
        "see_also_leaf_id": OUTBOUND["see_also_leaf_id"],
        "citation_leaf_id": OUTBOUND["citation_leaf_id"],
        "names_section": OUTBOUND["names_section"],
        "names_subsection": OUTBOUND["names_subsection"],
        "to_site": "combat",
    },
    "inbound": {
        "from_site": "combat",
        "leaf_id": INBOUND["leaf_id"],
        "clause_id": INBOUND["clause_id"],
        "occurrences_in_the_whole_release": 1,
        "to_site": "glossary",
    },
    "corroboration_outside_the_population": {
        "from_container": CORROBORATION["from_container"],
        "leaf_id": CORROBORATION["leaf_id"],
        "occurrences_in_the_whole_release": 1,
        "in_the_population": False,
    },
    "note": (
        "the two sites are one population because the source joins them, not "
        "because a reader judges them related. This is the printed join, "
        "re-derived rather than recalled, and the second site's container is "
        "not labeled 'Speed' at all."
    ),
}

#: **What a naive co-occurrence test would have added, and why it is wrong.**
#: Three entries beneath `Playing the Game > Combat` mention the glossary and
#: Speed together. One of them *is* the second site. The two the naive test
#: adds are asserted non-members here: each cites the glossary for some other
#: rule.
NAIVE_WOULD_HAVE_MATCHED = list(MANIFEST["direction"]["naive_cooccurrence_would_have_matched"])
NAIVE_ADDS = [
    label
    for label in NAIVE_WOULD_HAVE_MATCHED
    if label != LABELS[COMBAT_ENTRY.container_id]
]
assert NAIVE_ADDS == ["Dropping Prone", "Mounting and Dismounting"], NAIVE_ADDS
for _label in NAIVE_ADDS:
    _matches = [
        c
        for c in LEDGER_OBJ.containers
        if c.container_type == "entry" and c.label == _label
    ]
    assert len(_matches) == 1, (_label, len(_matches))
    assert _matches[0].container_id not in SITE_OF_CONTAINER, _label

#: **The adjudicated boundary**: the twenty-one containers a reader would
#: actually question — the three other entries labeled `Speed`, the four
#: special-speed glossary entries this population's prose names, the five
#: entries its *See also* names, the Combat siblings that spend Speed, and the
#: two sites that convert it into a travel rate. None of them is a member, none
#: prints the reciprocal citation, and none was already accepted as a Speed
#: rule. What each one *is* — an outbound reference, an incidental use, or a
#: sibling record for a later batch — is the checkpoint's judgment, not this
#: run's.
ADJUDICATED_BOUNDARY = [
    {
        "container_path": row["container_path"],
        "leaf_count": row["leaf_count"],
        "prints_the_reciprocal_citation": row["prints_the_reciprocal_citation"],
        "defers_the_movement_rules_to_the_population": row[
            "defers_the_movement_rules_to_the_population"
        ],
        "cites_the_glossary_speed_entry_in_a_see_also": row[
            "cites_the_glossary_speed_entry_in_a_see_also"
        ],
        "already_accepted_as": row["already_accepted_as"],
    }
    for row in MANIFEST["adjudicated_boundary"]
]
assert len(ADJUDICATED_BOUNDARY) == 21, len(ADJUDICATED_BOUNDARY)
for _row in MANIFEST["adjudicated_boundary"]:
    assert _row["container_id"] in CONTAINERS, _row["container_path"]
    assert _path_of(_row["container_id"]) == _row["container_path"], _row[
        "container_path"
    ]
    assert _row["container_id"] not in SITE_OF_CONTAINER, _row["container_path"]
    assert _row["prints_the_reciprocal_citation"] is False, _row["container_path"]
    assert _row["already_accepted_as"] == [], _row["container_path"]
#: The three sibling `Speed` labels are all there, so the label collision is
#: adjudicated rather than merely noticed.
_adjudicated_paths = {row["container_path"] for row in ADJUDICATED_BOUNDARY}
assert (
    set(SPEED_LABELED_PATHS) - {_path_of(GLOSSARY_ENTRY.container_id)}
    <= _adjudicated_paths
), sorted(set(SPEED_LABELED_PATHS) - _adjudicated_paths)
#: Exactly one adjudicated container defers the movement rules to this
#: population — `Your Turn`, the corroborating pointer — and it is not a member.
_defers = [
    row["container_path"]
    for row in ADJUDICATED_BOUNDARY
    if row["defers_the_movement_rules_to_the_population"]
]
assert _defers == ["Playing the Game > Combat > Your Turn"], _defers

#: Policy exclusions inside this boundary. There are none, and that is asserted
#: rather than assumed: a site that silently lost a body leaf would otherwise
#: look identical to one that lost a running header.
POLICY_EXCLUDED = sorted(
    leaf.leaf_id
    for _, cid in SITES
    for leaf in by_container[cid]
    if leaf.leaf_id not in REPRESENTED
)
assert POLICY_EXCLUDED == [], POLICY_EXCLUDED
assert MANIFEST["membership"]["policy_excluded"] == [], MANIFEST["membership"]

#: The one record. `glossary.speed` is already cited by name in accepted
#: authority (`action.dash`), so the key is not chosen here — it is the target
#: an accepted reference has been pointing at since actions-1.
SPEED = "glossary.speed"
RECORDS_IN_ORDER = (SPEED,)
RECORD_KIND = {SPEED: RecordKind.GLOSSARY_RULE}

# --- The reviewed clause table, tied back to the live corpus ----------------

#: `clause_id -> the manifest's clause row`, in printed order.
CLAUSE = {row["clause_id"]: row for row in MANIFEST["clauses"]}
CLAUSE_ORDER = tuple(row["clause_id"] for row in MANIFEST["clauses"])
assert len(CLAUSE) == len(CLAUSE_ORDER) == 36, len(CLAUSE_ORDER)

#: The manifest's own leaf table, and the tie to the live bound corpus: every
#: reviewed leaf must still exist and still hold byte-identical content.
MANIFEST_LEAVES: dict[str, str] = {}
LEAF_SITE: dict[str, str] = {}
for _site in MANIFEST["source_sites"]:
    assert _site["site"] in {s for s, _ in SITES}, _site["site"]
    assert _site["container_id"] == dict(SITES)[_site["site"]], _site["site"]
    assert _site["container_path"] == _path_of(_site["container_id"]), _site["site"]
    for _leafrow in _site["leaves"]:
        _lid = _leafrow["leaf_id"]
        assert _lid in LEAF_BY_ID, f"the reviewed leaf {_lid} is not in the bound corpus"
        assert (
            LEAF_BY_ID[_lid].content == _leafrow["content"]
        ), f"leaf {_lid} moved under the bound source"
        MANIFEST_LEAVES[_lid] = _leafrow["content"]
        LEAF_SITE[_lid] = str(_site["site"])
assert len(MANIFEST_LEAVES) == 16, len(MANIFEST_LEAVES)

#: And the tie in the other direction: the boundary this run re-derived from the
#: two containers holds exactly the leaves the reviewed inventory covers.
BOUNDARY_LEAVES = {leaf.leaf_id for _, cid in SITES for leaf in by_container[cid]}
assert BOUNDARY_LEAVES == set(MANIFEST_LEAVES), sorted(
    BOUNDARY_LEAVES ^ set(MANIFEST_LEAVES)
)
assert BOUNDARY_LEAVES <= REPRESENTED, "a boundary leaf is policy-excluded"

#: **The exclusion, re-derived rather than transcribed**, with the discovery
#: script's exact rule: every leaf in the bound release whose content matches
#: `speed` case-insensitively and which is not a member leaf. 557 of them, and
#: every one already represented by 5c — printing the word is use, and this
#: batch takes none of it.
_WORD = re.compile(r"speed", re.IGNORECASE)
BOUNDARY_REDERIVED = sorted(
    leaf.leaf_id
    for leaf in LEDGER_OBJ.leaves
    if _WORD.search(leaf.content) and leaf.leaf_id not in BOUNDARY_LEAVES
)
BOUNDARY_IN_MANIFEST = sorted(row["leaf_id"] for row in MANIFEST["boundary"])
assert BOUNDARY_REDERIVED == BOUNDARY_IN_MANIFEST, sorted(
    set(BOUNDARY_REDERIVED) ^ set(BOUNDARY_IN_MANIFEST)
)
assert len(BOUNDARY_REDERIVED) == MANIFEST["boundary_count"] == 557, len(
    BOUNDARY_REDERIVED
)
BOUNDARY_ALL_REPRESENTED = all(lid in REPRESENTED for lid in BOUNDARY_REDERIVED)
assert BOUNDARY_ALL_REPRESENTED is True
assert MANIFEST["boundary_all_represented_by_5c"] is True
#: No excluded leaf is attached to either site, and none was already represented
#: by accepted authority as a Speed rule.
for _row in MANIFEST["boundary"]:
    assert _row["leaf_id"] not in BOUNDARY_LEAVES, _row["leaf_id"]
BOUNDARY_BY_SECTION = dict(MANIFEST["boundary_by_section"])
assert sum(BOUNDARY_BY_SECTION.values()) == len(BOUNDARY_REDERIVED), BOUNDARY_BY_SECTION


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


def _site(clause_id: str) -> str:
    return LEAF_SITE[_leaf(clause_id)]


#: **The full source boundary, gap-free, proved rather than promised.** Every one
#: of the sixteen bound leaves is partitioned end to end by the reviewed clause
#: extents: the first clause starts at 0, each next starts where the last
#: stopped, the last stops at the leaf's length, and the concatenation is the
#: leaf byte for byte.
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

#: **Three sentences are printed across a leaf boundary.** A clause that only
#: means something in company must be shown to keep that company, so each is
#: reconstructed here from its own clause texts and asserted against the
#: reviewed sentence. The join is one space per crossing with runs collapsed,
#: because the extractor drops the break the page printed.
CROSS_LEAF_SENTENCES = []
for _row in MANIFEST["cross_leaf_sentences"]:
    _ids = list(_row["clause_ids"])
    _reconstructed = re.sub(r"\s+", " ", " ".join(_text(c) for c in _ids)).strip()
    assert _reconstructed == _row["reconstructed_sentence"], _ids
    assert sorted({_leaf(c) for c in _ids}) == sorted(_row["leaf_ids"]), _ids
    assert len({_leaf(c) for c in _ids}) == len(_ids), f"{_ids}: not actually split"
    CROSS_LEAF_SENTENCES.append(
        {
            "clause_ids": _ids,
            "leaf_ids": [_leaf(c) for c in _ids],
            "sites": sorted({_site(c) for c in _ids}),
            "reconstructed_here": _reconstructed,
        }
    )
assert len(CROSS_LEAF_SENTENCES) == 3, len(CROSS_LEAF_SENTENCES)

# ---------------------------------------------------------------------------
# The sixteen substantive clauses, as nine components and seventeen facts
# ---------------------------------------------------------------------------
#
# One component per rule the source states about Speed, named for that rule.
# Three of them hold several facts that one sentence states together — the four
# special speeds it lists, the four modes it names, the two ways a mode may
# compose with regular movement. For those the sentence claims the *component*,
# because a span may carry only one PRIMARY owner and the sentence is about the
# whole group rather than about any one member of it; each fact then carries the
# same span at CONTEXTUAL. That is the shape `action.attack`'s
# `attack_equipment_change` already uses in accepted authority, and the frozen
# prior holds twenty `component/primary` claims.

SCOPE_KEY = "srd-5.2.1/rules-glossary"

DEFINITION = "speed_definition"
ALLOWANCE = "movement_allowance"
DEPLETION = "movement_depletion"
SELECTION = "speed_selection"
SWITCH = "speed_switch_limit"
PROPAGATION = "speed_change_propagation"
SPECIAL = "special_speeds"
MODES = "movement_modes"
COMPOSING = "movement_composition"

COMPONENTS = (
    DEFINITION,
    ALLOWANCE,
    DEPLETION,
    SELECTION,
    SWITCH,
    PROPAGATION,
    SPECIAL,
    MODES,
    COMPOSING,
)

LISTED = SpecialSpeedListing.NAMED_IN_A_NON_EXHAUSTIVE_LIST

#: `(component, fact, clause ids)` — every fact, with the clauses that
#: PRIMARY-claim it. An empty tuple means the sentence claims the component
#: instead, and the fact's own citation of it is in :data:`FACT_DETAIL`.
COMPOSITION: tuple[tuple[str, MechanicalFact, tuple[str, ...]], ...] = (
    # G1. "A creature has a Speed, which is the distance in feet the creature
    # can cover when it moves on its turn." The unit and the window are the
    # whole of what the definition states; no number is printed, so none is
    # represented.
    (
        DEFINITION,
        SpeedDefinitionFact(unit=DistanceUnit.FOOT, window=MovementWindow.OWN_TURN),
        ("glossary/1/1",),
    ),
    # G2. "On your turn, you can move a distance equal to your Speed or less."
    # + "Or you can decide not to move." One ceiling, stated across a leaf
    # boundary and then restated at its floor.
    (
        ALLOWANCE,
        MovementAllowanceFact(
            basis=MovementAllowanceBasis.OWN_SPEED, window=MovementWindow.OWN_TURN
        ),
        ("combat/1/0", "combat/2/0", "combat/2/1"),
    ),
    # G3. "However you're moving with your Speed, you deduct the distance of
    # each part of your move from it until it is used up or until you are done
    # moving, whichever comes first."
    (
        DEPLETION,
        MovementDepletionFact(
            depletes=MovementAllowanceBasis.OWN_SPEED,
            until=(
                MovementDepletionTerminator.ALLOWANCE_USED_UP,
                MovementDepletionTerminator.DONE_MOVING,
            ),
            resolution=MovementDepletionResolution.WHICHEVER_COMES_FIRST,
        ),
        ("combat/3/2",),
    ),
    # G4a. "If you have more than one speed, choose which one to use when you
    # move;"
    (
        SELECTION,
        SpeedSelectionFact(permits=SpeedSelection.CHOOSE_BEFORE_MOVING),
        ("glossary/7/1",),
    ),
    # G4b. "you can switch between the speeds during your move."
    (
        SELECTION,
        SpeedSelectionFact(permits=SpeedSelection.SWITCH_DURING_MOVE),
        ("glossary/7/2",),
    ),
    # G4c. "Whenever you switch, subtract the distance already moved from the
    # new speed." + "The result determines how much farther you can move." +
    # "If the result is 0 or less, you can't use the new speed during the
    # current move." Nothing is subtracted here.
    (
        SWITCH,
        SpeedSwitchLimitFact(
            accounting=SpeedSwitchAccounting.SUBTRACT_DISTANCE_ALREADY_MOVED,
            when_nonpositive=SpeedSwitchOutcome.FORBIDS_USING_THE_NEW_SPEED,
        ),
        ("glossary/7/3", "glossary/7/4", "glossary/7/5"),
    ),
    # G5. "If an effect increases or decreases your Speed for a time, any
    # special speed you have increases or decreases by an equal amount for the
    # same duration."
    (
        PROPAGATION,
        SpeedChangePropagationFact(
            to=SpeedPropagationScope.EVERY_SPECIAL_SPEED,
            magnitude=SpeedPropagationMagnitude.EQUAL_AMOUNT,
            duration=SpeedPropagationDuration.SAME_DURATION,
        ),
        ("glossary/9/0",),
    ),
    # G6a. "Some creatures have special speeds, such as a Burrow Speed, Climb
    # Speed, Fly Speed, or Swim Speed, each of which is defined in this
    # glossary." Four named members of an open list; "such as" stays open
    # because `listing` says the list is non-exhaustive rather than the
    # vocabulary being closed to these four.
    (SPECIAL, SpecialSpeedFact(mode=MovementMode.BURROW, listing=LISTED), ()),
    (SPECIAL, SpecialSpeedFact(mode=MovementMode.CLIMB, listing=LISTED), ()),
    (SPECIAL, SpecialSpeedFact(mode=MovementMode.FLY, listing=LISTED), ()),
    (SPECIAL, SpecialSpeedFact(mode=MovementMode.SWIM, listing=LISTED), ()),
    # G6b. "Your movement can include climbing, crawling, jumping, and swimming
    # (each explained in "Rules Glossary")." Four modes in one sentence, on the
    # family schema 3 already had for exactly this.
    (MODES, MovementPermissionFact(mode=MovementMode.CLIMB), ()),
    (MODES, MovementPermissionFact(mode=MovementMode.CRAWL), ()),
    (MODES, MovementPermissionFact(mode=MovementMode.JUMP), ()),
    (MODES, MovementPermissionFact(mode=MovementMode.SWIM), ()),
    # G6c. "These different modes of movement can be combined with your regular
    # movement, or they can constitute your entire move."
    (
        COMPOSING,
        MovementCompositionFact(
            composes=MovementComposition.COMBINED_WITH_REGULAR_MOVEMENT
        ),
        (),
    ),
    (COMPOSING, MovementCompositionFact(composes=MovementComposition.ENTIRE_MOVE), ()),
)
assert len(COMPOSITION) == 17, len(COMPOSITION)

#: Substantive clauses that claim a *component* rather than a fact.
COMPONENT_PRIMARY: tuple[tuple[str, str], ...] = (
    (SPECIAL, "glossary/5/0"),
    (SPECIAL, "glossary/6/0"),
    (SPECIAL, "glossary/7/0"),
    (MODES, "combat/3/0"),
    (COMPOSING, "combat/3/1"),
)

#: Every substantive clause id, derived from the composition rather than listed
#: beside it, so a clause represented twice or not at all is visible.
SUBSTANTIVE_CLAUSES = tuple(
    clause for _, _, clauses in COMPOSITION for clause in clauses
) + tuple(clause for _, clause in COMPONENT_PRIMARY)
assert len(SUBSTANTIVE_CLAUSES) == len(set(SUBSTANTIVE_CLAUSES)) == 16, len(
    SUBSTANTIVE_CLAUSES
)

# ---------------------------------------------------------------------------
# The nine outgoing references
# ---------------------------------------------------------------------------
#
# Five come from the *See also* leaf. Four more come from "each of which is
# defined in this glossary", an explicit printed pointer at the four entries the
# sentence names. `Fly Speed` is printed across the glossary/5/0 - 6/0 leaf
# boundary and so cites two clauses: one reference, two provenance claims.
# `_validate_provenance` rejects only exact duplicate edges, so two distinct
# spans claiming one reference is admissible, and it is what the source did.
#
# `action.dash`'s bare "such as a Fly Speed or Swim Speed" is not this pointer
# and its accepted artifact is unchanged by any of it.
CITATIONS: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("Climbing", "glossary.climbing", ("glossary/3/0",)),
    ("Crawling", "glossary.crawling", ("glossary/3/1",)),
    ("Flying", "glossary.flying", ("glossary/3/2",)),
    ("Jumping", "glossary.jumping", ("glossary/3/3",)),
    ("Swimming", "glossary.swimming", ("glossary/3/4",)),
    ("Burrow Speed", "glossary.burrow_speed", ("glossary/5/0",)),
    ("Climb Speed", "glossary.climb_speed", ("glossary/5/0",)),
    ("Fly Speed", "glossary.fly_speed", ("glossary/5/0", "glossary/6/0")),
    ("Swim Speed", "glossary.swim_speed", ("glossary/6/0",)),
)
REFERENCES = tuple(
    ReferenceDraft(
        from_record_key=SPEED,
        from_component_key=RECORD_OWNED_REFERENCE,
        source_text=text,
        scope_key=SCOPE_KEY,
        target_record_key=target,
    )
    for text, target, _ in CITATIONS
)
assert len(REFERENCES) == 9, len(REFERENCES)
#: The split is a property of the source, not of the emission: exactly one
#: reference cites two clauses, and its two clauses sit on two different leaves.
SPLIT_REFERENCES = [
    (text, target, clauses) for text, target, clauses in CITATIONS if len(clauses) > 1
]
assert SPLIT_REFERENCES == [
    ("Fly Speed", "glossary.fly_speed", ("glossary/5/0", "glossary/6/0"))
], SPLIT_REFERENCES
assert len({_leaf(c) for c in SPLIT_REFERENCES[0][2]}) == 2, SPLIT_REFERENCES
#: Every reference carries the one scope every accepted reference carries. No
#: second scope arises for this batch.
assert {r.scope_key for r in REFERENCES} == {SCOPE_KEY}
assert all(r.from_component_key == RECORD_OWNED_REFERENCE for r in REFERENCES)
assert len({reference_target_key(r) for r in REFERENCES}) == 9

# ---------------------------------------------------------------------------
# The twenty supporting clauses, each linked to what it actually supports
# ---------------------------------------------------------------------------

#: Supporting clauses the *record* carries: the three headings at the glossary
#: site, the combat heading, the possession clause, the *See also* label, the
#: two sourcing sentences, and the two chapter navigations.
#:
#: The navigations emit nothing. `and "Playing the Game" ("Combat").` names a
#: chapter — for which there is no record — and names this record's own second
#: site; `See "Rules Glossary" for more about Speed ...` points back at this very
#: entry and re-names three targets the glossary site already cites.
#: Record-owned supporting authority is the honest scope for both.
RECORD_CONTEXT: tuple[str, ...] = (
    "glossary/0/0",
    "glossary/1/0",
    "glossary/2/0",
    "glossary/3/5",
    "glossary/4/0",
    "glossary/8/0",
    "combat/0/0",
    "combat/3/3",
    "combat/3/4",
    "combat/3/5",
)

#: Supporting clauses a *fact* carries, because they bound that fact and state
#: no rule of their own. The switch example works one case of the switch limit;
#: the four propagation clauses are the printed zero and halving illustrations,
#: the second of them spanning three leaves. Represented as evidence for the
#: rule rather than as arithmetic: no number here becomes a value.
FACT_CONTEXT: tuple[tuple[str, MechanicalFact, str], ...] = tuple(
    (SWITCH, _f, "glossary/7/6") for _c, _f, _cl in COMPOSITION if _c == SWITCH
) + tuple(
    (PROPAGATION, _f, clause)
    for _c, _f, _cl in COMPOSITION
    if _c == PROPAGATION
    for clause in ("glossary/9/1", "glossary/9/2", "glossary/10/0", "glossary/11/0")
)
assert len(FACT_CONTEXT) == 5, len(FACT_CONTEXT)

#: CONTEXTUAL fact claims on clauses that are already *substantive*: each fact in
#: a group cites the part of the group's sentence that names it, while the
#: sentence as a whole claims the component. `Fly Speed` is named across two
#: leaves, so its fact cites both.
FACT_DETAIL: tuple[tuple[str, MechanicalFact, str], ...] = (
    (
        (
            SPECIAL,
            SpecialSpeedFact(mode=MovementMode.BURROW, listing=LISTED),
            "glossary/5/0",
        ),
        (
            SPECIAL,
            SpecialSpeedFact(mode=MovementMode.CLIMB, listing=LISTED),
            "glossary/5/0",
        ),
        (
            SPECIAL,
            SpecialSpeedFact(mode=MovementMode.FLY, listing=LISTED),
            "glossary/5/0",
        ),
        (
            SPECIAL,
            SpecialSpeedFact(mode=MovementMode.FLY, listing=LISTED),
            "glossary/6/0",
        ),
        (
            SPECIAL,
            SpecialSpeedFact(mode=MovementMode.SWIM, listing=LISTED),
            "glossary/6/0",
        ),
    )
    + tuple((_c, _f, "combat/3/0") for _c, _f, _cl in COMPOSITION if _c == MODES)
    + tuple((_c, _f, "combat/3/1") for _c, _f, _cl in COMPOSITION if _c == COMPOSING)
)
assert len(FACT_DETAIL) == 11, len(FACT_DETAIL)

#: A citation printed inside a *substantive* clause does not make that clause
#: supporting authority: the sentence still states a rule. Only the five *See
#: also* clauses, whose whole content is the citation, land here.
SUPPORTING_CLAUSES = (
    RECORD_CONTEXT
    + tuple(
        clause
        for _, _, clauses in CITATIONS
        for clause in clauses
        if clause not in SUBSTANTIVE_CLAUSES
    )
    + tuple(clause for _, _, clause in FACT_CONTEXT)
)
assert len(SUPPORTING_CLAUSES) == len(set(SUPPORTING_CLAUSES)) == 20, len(
    SUPPORTING_CLAUSES
)
#: Together, and only together, they are the reviewed inventory: no clause is
#: both, and none is neither.
assert set(SUBSTANTIVE_CLAUSES) | set(SUPPORTING_CLAUSES) == set(CLAUSE_ORDER)
assert not set(SUBSTANTIVE_CLAUSES) & set(SUPPORTING_CLAUSES)

# ---------------------------------------------------------------------------
# The composed draft
# ---------------------------------------------------------------------------

#: `component -> its facts, in printed order`.
FACTS_BY_COMPONENT: dict[str, tuple[MechanicalFact, ...]] = {
    component: tuple(f for c, f, _ in COMPOSITION if c == component)
    for component in COMPONENTS
}
assert sum(len(v) for v in FACTS_BY_COMPONENT.values()) == 17

COMPONENT_DRAFTS = tuple(
    ComponentDraft(
        record_key=SPEED,
        semantic_key=component_key,
        handling=ComponentHandling.STRUCTURED,
        facts=FACTS_BY_COMPONENT[component_key],
    )
    for component_key in COMPONENTS
)
COMPONENT_BY_KEY = {c.semantic_key: c for c in COMPONENT_DRAFTS}

PROVENANCE = (
    tuple(
        ProvenanceClaim(
            ProvenanceTargetKind.RECORD,
            (SPEED,),
            _span_id(clause),
            ProvenanceRole.CONTEXTUAL,
        )
        for clause in RECORD_CONTEXT
    )
    + tuple(
        ProvenanceClaim(
            ProvenanceTargetKind.COMPONENT,
            component_target_key(COMPONENT_BY_KEY[component_key]),
            _span_id(clause),
            ProvenanceRole.PRIMARY,
        )
        for component_key, clause in COMPONENT_PRIMARY
    )
    + tuple(
        ProvenanceClaim(
            ProvenanceTargetKind.FACT,
            fact_target_key(SPEED, component_key, fact),
            _span_id(clause),
            ProvenanceRole.PRIMARY,
        )
        for component_key, fact, clauses in COMPOSITION
        for clause in clauses
    )
    + tuple(
        ProvenanceClaim(
            ProvenanceTargetKind.FACT,
            fact_target_key(SPEED, component_key, fact),
            _span_id(clause),
            ProvenanceRole.CONTEXTUAL,
        )
        for component_key, fact, clause in FACT_DETAIL + FACT_CONTEXT
    )
    + tuple(
        ProvenanceClaim(
            ProvenanceTargetKind.REFERENCE,
            reference_target_key(reference),
            _span_id(clause),
            ProvenanceRole.CONTEXTUAL,
        )
        for reference, (_, _, clauses) in zip(REFERENCES, CITATIONS, strict=True)
        for clause in clauses
    )
)
DRAFT = RepresentationDraft(
    records=(RecordDraft(semantic_key=SPEED, kind=RecordKind.GLOSSARY_RULE),),
    components=COMPONENT_DRAFTS,
    prose_bindings=(),
    relationships=(),
    references=REFERENCES,
    provenance=PROVENANCE,
)

#: **Fifty-two claims over thirty-six spans.** This population prints sentences
#: that state a rule *and* cite an entry in one breath, so a claim count equal to
#: the span count would have been the wrong shape here: `glossary/5/0` alone
#: carries seven. The breakdown is derived, not typed.
PROVENANCE_SHAPES: dict[str, int] = defaultdict(int)
for _claim in PROVENANCE:
    PROVENANCE_SHAPES[f"{_claim.target_kind.value}/{_claim.role.value}"] += 1
PROVENANCE_SHAPES = dict(sorted(PROVENANCE_SHAPES.items()))
assert PROVENANCE_SHAPES == {
    "component/primary": 5,
    "fact/contextual": 16,
    "fact/primary": 11,
    "record/contextual": 10,
    "reference/contextual": 10,
}, PROVENANCE_SHAPES
assert len(PROVENANCE) == 52, len(PROVENANCE)
CLAIMS_PER_CLAUSE: dict[str, int] = defaultdict(int)
_SPAN_TO_CLAUSE = {_span_id(c): c for c in CLAUSE_ORDER}
assert len(_SPAN_TO_CLAUSE) == 36, len(_SPAN_TO_CLAUSE)
for _claim in PROVENANCE:
    CLAIMS_PER_CLAUSE[_SPAN_TO_CLAUSE[_claim.span_id]] += 1
assert CLAIMS_PER_CLAUSE["glossary/5/0"] == 7, CLAIMS_PER_CLAUSE["glossary/5/0"]
assert CLAIMS_PER_CLAUSE["glossary/6/0"] == 5, CLAIMS_PER_CLAUSE["glossary/6/0"]
assert CLAIMS_PER_CLAUSE["combat/3/0"] == 5, CLAIMS_PER_CLAUSE["combat/3/0"]
assert CLAIMS_PER_CLAUSE["combat/3/1"] == 3, CLAIMS_PER_CLAUSE["combat/3/1"]
#: Every clause carries at least one claim: nothing printed inside the boundary
#: is dropped on the floor.
assert set(CLAIMS_PER_CLAUSE) == set(CLAUSE_ORDER), sorted(
    set(CLAUSE_ORDER) - set(CLAIMS_PER_CLAUSE)
)

# ---------------------------------------------------------------------------
# The reviewed obligation table
# ---------------------------------------------------------------------------
#
# One literal row per printed clause, typed from the reviewed source record —
# §3 of the discovery checkpoint for the 5c disposition, §4's gap table for the
# gap ids and their witness lists. Nothing here is computed from what this file
# emits, and the manifest carries no disposition at all, so this table is the
# only place the review's judgment enters.
#
# A row carries a **tuple** of carriers, which is new in this batch. The five
# accepted batches each had one carrier per clause; this population prints
# sentences that state a rule *and* cite an entry in the same breath, so
# `glossary/5/0` discharges seven obligations at once: the component the whole
# sentence claims, the three special speeds it names, and the three glossary
# entries it points at.
#
# Carrier kinds, and the claim each produces:
#
#   ("record", key)                  RECORD/CONTEXTUAL
#   ("component", component)         COMPONENT/PRIMARY
#   ("fact", component, label)       FACT/PRIMARY
#   ("fact_detail", component, lbl)  FACT/CONTEXTUAL on a *substantive* clause
#   ("fact_context", component, lbl) FACT/CONTEXTUAL on a *supporting* clause
#   ("reference", target)            REFERENCE/CONTEXTUAL

#: The seventeen facts, each behind a stable label, so the obligation table can
#: name a fact without retyping its payload.
FACT_BY_LABEL: dict[str, tuple[str, MechanicalFact]] = {
    "definition": (DEFINITION, FACTS_BY_COMPONENT[DEFINITION][0]),
    "allowance": (ALLOWANCE, FACTS_BY_COMPONENT[ALLOWANCE][0]),
    "depletion": (DEPLETION, FACTS_BY_COMPONENT[DEPLETION][0]),
    "selection_choose": (SELECTION, FACTS_BY_COMPONENT[SELECTION][0]),
    "selection_switch": (SELECTION, FACTS_BY_COMPONENT[SELECTION][1]),
    "switch_limit": (SWITCH, FACTS_BY_COMPONENT[SWITCH][0]),
    "propagation": (PROPAGATION, FACTS_BY_COMPONENT[PROPAGATION][0]),
    "special_burrow": (SPECIAL, FACTS_BY_COMPONENT[SPECIAL][0]),
    "special_climb": (SPECIAL, FACTS_BY_COMPONENT[SPECIAL][1]),
    "special_fly": (SPECIAL, FACTS_BY_COMPONENT[SPECIAL][2]),
    "special_swim": (SPECIAL, FACTS_BY_COMPONENT[SPECIAL][3]),
    "mode_climb": (MODES, FACTS_BY_COMPONENT[MODES][0]),
    "mode_crawl": (MODES, FACTS_BY_COMPONENT[MODES][1]),
    "mode_jump": (MODES, FACTS_BY_COMPONENT[MODES][2]),
    "mode_swim": (MODES, FACTS_BY_COMPONENT[MODES][3]),
    "compose_combined": (COMPOSING, FACTS_BY_COMPONENT[COMPOSING][0]),
    "compose_entire": (COMPOSING, FACTS_BY_COMPONENT[COMPOSING][1]),
}
assert len(FACT_BY_LABEL) == 17, len(FACT_BY_LABEL)
#: The labels address every fact exactly once — a label that named the wrong
#: member would otherwise silently re-point an obligation.
assert sorted(fact_key(f) for _, f in FACT_BY_LABEL.values()) == sorted(
    fact_key(f) for _, f, _ in COMPOSITION
), "the label index does not address the composition one to one"

_REC = ("record", SPEED)

EXPECTED_OBLIGATIONS: dict[str, dict[str, object]] = {
    # --- Rules Glossary > Rules Definitions > Speed -------------------------
    "glossary/0/0": {"gap": None, "carriers": (_REC,)},
    "glossary/1/0": {"gap": None, "carriers": (_REC,)},
    "glossary/1/1": {"gap": "G1", "carriers": (("fact", DEFINITION, "definition"),)},
    "glossary/2/0": {"gap": None, "carriers": (_REC,)},
    "glossary/3/0": {"gap": None, "carriers": (("reference", "glossary.climbing"),)},
    "glossary/3/1": {"gap": None, "carriers": (("reference", "glossary.crawling"),)},
    "glossary/3/2": {"gap": None, "carriers": (("reference", "glossary.flying"),)},
    "glossary/3/3": {"gap": None, "carriers": (("reference", "glossary.jumping"),)},
    "glossary/3/4": {"gap": None, "carriers": (("reference", "glossary.swimming"),)},
    # Names a chapter, for which there is no record, and names this record's own
    # second site. Record-owned supporting authority is the honest scope.
    "glossary/3/5": {"gap": None, "carriers": (_REC,)},
    "glossary/4/0": {"gap": None, "carriers": (_REC,)},
    # The definition sentence's first two thirds: it states that special speeds
    # are a named category in an open list, names three of them, and points at
    # three glossary entries, all in one printed fragment.
    "glossary/5/0": {
        "gap": "G6",
        "carriers": (
            ("component", SPECIAL),
            ("fact_detail", SPECIAL, "special_burrow"),
            ("fact_detail", SPECIAL, "special_climb"),
            ("fact_detail", SPECIAL, "special_fly"),
            ("reference", "glossary.burrow_speed"),
            ("reference", "glossary.climb_speed"),
            ("reference", "glossary.fly_speed"),
        ),
    },
    # `Fly Speed` straddles this boundary, which is why its one reference claims
    # both fragments and its fact does too.
    "glossary/6/0": {
        "gap": "G6",
        "carriers": (
            ("component", SPECIAL),
            ("fact_detail", SPECIAL, "special_fly"),
            ("fact_detail", SPECIAL, "special_swim"),
            ("reference", "glossary.fly_speed"),
            ("reference", "glossary.swim_speed"),
        ),
    },
    "glossary/7/0": {"gap": "G6", "carriers": (("component", SPECIAL),)},
    "glossary/7/1": {
        "gap": "G4",
        "carriers": (("fact", SELECTION, "selection_choose"),),
    },
    "glossary/7/2": {
        "gap": "G4",
        "carriers": (("fact", SELECTION, "selection_switch"),),
    },
    "glossary/7/3": {"gap": "G4", "carriers": (("fact", SWITCH, "switch_limit"),)},
    "glossary/7/4": {"gap": "G4", "carriers": (("fact", SWITCH, "switch_limit"),)},
    "glossary/7/5": {"gap": "G4", "carriers": (("fact", SWITCH, "switch_limit"),)},
    "glossary/7/6": {
        "gap": None,
        "carriers": (("fact_context", SWITCH, "switch_limit"),),
    },
    "glossary/8/0": {"gap": None, "carriers": (_REC,)},
    "glossary/9/0": {
        "gap": "G5",
        "carriers": (("fact", PROPAGATION, "propagation"),),
    },
    # The printed zero and halving illustrations. Evidence for the rule, not
    # arithmetic: no number here becomes a value.
    "glossary/9/1": {
        "gap": None,
        "carriers": (("fact_context", PROPAGATION, "propagation"),),
    },
    "glossary/9/2": {
        "gap": None,
        "carriers": (("fact_context", PROPAGATION, "propagation"),),
    },
    "glossary/10/0": {
        "gap": None,
        "carriers": (("fact_context", PROPAGATION, "propagation"),),
    },
    "glossary/11/0": {
        "gap": None,
        "carriers": (("fact_context", PROPAGATION, "propagation"),),
    },
    # --- Playing the Game > Combat > Movement and Position ------------------
    "combat/0/0": {"gap": None, "carriers": (_REC,)},
    "combat/1/0": {"gap": "G2", "carriers": (("fact", ALLOWANCE, "allowance"),)},
    "combat/2/0": {"gap": "G2", "carriers": (("fact", ALLOWANCE, "allowance"),)},
    "combat/2/1": {"gap": "G2", "carriers": (("fact", ALLOWANCE, "allowance"),)},
    "combat/3/0": {
        "gap": "G6",
        "carriers": (
            ("component", MODES),
            ("fact_detail", MODES, "mode_climb"),
            ("fact_detail", MODES, "mode_crawl"),
            ("fact_detail", MODES, "mode_jump"),
            ("fact_detail", MODES, "mode_swim"),
        ),
    },
    "combat/3/1": {
        "gap": "G6",
        "carriers": (
            ("component", COMPOSING),
            ("fact_detail", COMPOSING, "compose_combined"),
            ("fact_detail", COMPOSING, "compose_entire"),
        ),
    },
    "combat/3/2": {"gap": "G3", "carriers": (("fact", DEPLETION, "depletion"),)},
    "combat/3/3": {"gap": None, "carriers": (_REC,)},
    "combat/3/4": {"gap": None, "carriers": (_REC,)},
    # The inbound citation: it points back at this very entry and re-names three
    # targets the glossary site already cites, so it emits no reference.
    "combat/3/5": {"gap": None, "carriers": (_REC,)},
}
assert len(EXPECTED_OBLIGATIONS) == 36, len(EXPECTED_OBLIGATIONS)
assert set(EXPECTED_OBLIGATIONS) == set(CLAUSE_ORDER), sorted(
    set(CLAUSE_ORDER) ^ set(EXPECTED_OBLIGATIONS)
)

#: §4's gap table, transcribed with its witnesses. G1's §4 entry also names
#: `glossary/1/0` parenthetically; that clause states possession rather than the
#: definition and is emitted as record-owned supporting authority, so it is not
#: a witness here.
CHECKPOINT_GAP_WITNESSES = {
    "G1": ("glossary/1/1",),
    "G2": ("combat/1/0", "combat/2/0", "combat/2/1"),
    "G3": ("combat/3/2",),
    "G4": (
        "glossary/7/1",
        "glossary/7/2",
        "glossary/7/3",
        "glossary/7/4",
        "glossary/7/5",
    ),
    "G5": ("glossary/9/0",),
    "G6": (
        "glossary/5/0",
        "glossary/6/0",
        "glossary/7/0",
        "combat/3/0",
        "combat/3/1",
    ),
}
_gap_from_table: dict[str, list[str]] = defaultdict(list)
for _cid in CLAUSE_ORDER:
    _gap = EXPECTED_OBLIGATIONS[_cid]["gap"]
    if _gap is not None:
        _gap_from_table[str(_gap)].append(_cid)
assert {k: tuple(sorted(v)) for k, v in _gap_from_table.items()} == {
    k: tuple(sorted(v)) for k, v in CHECKPOINT_GAP_WITNESSES.items()
}, dict(_gap_from_table)

# ---------------------------------------------------------------------------
# Emission — one span per printed clause, and the claims each discharges
# ---------------------------------------------------------------------------

ORIGIN_LABEL = "issue-5d-batch-speed-1-generator.py"

RATIONALE = {
    "record": (
        "identifies, frames, or defines the mechanic; preserved as supporting "
        "authority owned by the record rather than discarded"
    ),
    "component": (
        "states something true of a whole group of facts and of no single fact "
        "in it, so it is claimed PRIMARY on the component; each fact the "
        "sentence names then cites the same span CONTEXTUAL, which is the "
        "carrier accepted authority already uses for this shape"
    ),
    "fact": (
        "states a mechanic the closed typed union carries exactly, with every "
        "qualifier that narrows it carried by a structure of this schema rather "
        "than left implicit; where the source prints one rule across several "
        "clauses, each printing claims the one fact PRIMARY"
    ),
    "fact_detail": (
        "names one member of a group whose sentence claims the component; "
        "CONTEXTUAL on that member, because a span admits one PRIMARY owner"
    ),
    "fact_context": (
        "bounds exactly one typed fact and states no rule of its own; supporting "
        "authority claimed CONTEXTUAL by that fact rather than by the record"
    ),
    "reference": (
        "an explicit printed pointer at another entry; carried as an outgoing "
        "reference with the source's own scope, CONTEXTUAL on the reference"
    ),
}

#: Which carrier names a clause's disposition when several apply. A clause is
#: SUBSTANTIVE exactly when some carrier claims PRIMARY.
_PRIMARY_KINDS = ("fact", "component")
_STRENGTH = {
    "fact": 0,
    "component": 1,
    "reference": 2,
    "fact_context": 3,
    "fact_detail": 4,
    "record": 5,
}

spans: list[SemanticSpan] = []
proposed: list[ProposedSpan] = []
emitted_claims: list[ProvenanceClaim] = []
audit: list[dict] = []

for clause_id in CLAUSE_ORDER:
    row = EXPECTED_OBLIGATIONS[clause_id]
    carriers = tuple(row["carriers"])  # type: ignore[arg-type]
    assert carriers, clause_id
    kinds = [str(c[0]) for c in carriers]
    disposition = (
        SemanticDisposition.SUBSTANTIVE
        if any(k in _PRIMARY_KINDS for k in kinds)
        else SemanticDisposition.SUPPORTING_AUTHORITY
    )
    strongest = min(kinds, key=lambda k: _STRENGTH[k])
    leaf_id, (start, end) = _leaf(clause_id), _extent(clause_id)
    sid = _span_id(clause_id)
    span = SemanticSpan(
        span_id=sid,
        leaf_id=leaf_id,
        char_start=start,
        char_end=end,
        disposition=disposition,
        review_state=ReviewState.PROPOSED,
    )
    spans.append(span)
    proposed.append(
        ProposedSpan(span=span, origin=ORIGIN_LABEL, rationale=RATIONALE[strongest])
    )

    claimants: list[str] = []
    for carrier in carriers:
        kind = str(carrier[0])
        if kind == "record":
            emitted_claims.append(
                ProvenanceClaim(
                    ProvenanceTargetKind.RECORD,
                    (str(carrier[1]),),
                    sid,
                    ProvenanceRole.CONTEXTUAL,
                )
            )
            claimants.append(str(carrier[1]))
        elif kind == "component":
            component_key = str(carrier[1])
            emitted_claims.append(
                ProvenanceClaim(
                    ProvenanceTargetKind.COMPONENT,
                    component_target_key(COMPONENT_BY_KEY[component_key]),
                    sid,
                    ProvenanceRole.PRIMARY,
                )
            )
            claimants.append(f"{SPEED}/{component_key}")
        elif kind == "reference":
            target = str(carrier[1])
            reference = next(r for r in REFERENCES if r.target_record_key == target)
            emitted_claims.append(
                ProvenanceClaim(
                    ProvenanceTargetKind.REFERENCE,
                    reference_target_key(reference),
                    sid,
                    ProvenanceRole.CONTEXTUAL,
                )
            )
            claimants.append(f"{SPEED} -> {target}")
        else:
            component_key, label = str(carrier[1]), str(carrier[2])
            owner, fact = FACT_BY_LABEL[label]
            assert owner == component_key, (clause_id, label)
            emitted_claims.append(
                ProvenanceClaim(
                    ProvenanceTargetKind.FACT,
                    fact_target_key(SPEED, component_key, fact),
                    sid,
                    ProvenanceRole.PRIMARY
                    if kind == "fact"
                    else ProvenanceRole.CONTEXTUAL,
                )
            )
            claimants.append(f"{SPEED}/{component_key}/{fact_key(fact)}")

    audit.append(
        {
            "clause_id": clause_id,
            "site": _site(clause_id),
            "page_index": int(CLAUSE[clause_id]["page_index"]),
            "leaf_id": leaf_id,
            "char_start": start,
            "char_end": end,
            "span_id": sid,
            "text": _text(clause_id),
            "disposition": disposition.value,
            "review_state": ReviewState.PROPOSED.value,
            "gap_id": row["gap"],
            "carriers": [
                {"kind": str(c[0]), "target": claimant}
                for c, claimant in zip(carriers, claimants, strict=True)
            ],
            "claims": len(carriers),
            "rationale": RATIONALE[strongest],
        }
    )

assert len(spans) == len(proposed) == len(audit) == 36, len(spans)
assert len(emitted_claims) == 52, len(emitted_claims)

# --- The two-statement agreement --------------------------------------------
#
# The draft's provenance was built from the composition literals; the claims
# above were built from the reviewed obligation table. Neither is computed from
# the other, and they must be the same multiset. A carrier typed at the wrong
# element, a fact named by the wrong label, or a clause whose obligation the
# composition never discharges fails here.
def _claim_key(claim: ProvenanceClaim) -> tuple[str, tuple[str, ...], str, str]:
    return (
        claim.target_kind.value,
        tuple(claim.target_key),
        claim.span_id,
        claim.role.value,
    )


assert sorted(_claim_key(c) for c in emitted_claims) == sorted(
    _claim_key(c) for c in PROVENANCE
), "the obligation table and the composition do not agree"

#: Omission: every clause the review recorded is discharged, by exactly one span,
#: at exactly the manifest's extent.
assert {s.span_id for s in spans} == {_span_id(c) for c in CLAUSE_ORDER}
assert len({s.span_id for s in spans}) == 36
for _span in spans:
    _clause = _SPAN_TO_CLAUSE[_span.span_id]
    assert (_span.leaf_id, _span.char_start, _span.char_end) == (
        _leaf(_clause),
        *_extent(_clause),
    ), _clause

#: Disposition drift: the table's dispositions and the composition's are the
#: same partition, stated twice.
_TABLE_SUBSTANTIVE = {
    s.span_id for s in spans if s.disposition is SemanticDisposition.SUBSTANTIVE
}
assert _TABLE_SUBSTANTIVE == {_span_id(c) for c in SUBSTANTIVE_CLAUSES}
assert len(_TABLE_SUBSTANTIVE) == 16, len(_TABLE_SUBSTANTIVE)
assert len(spans) - len(_TABLE_SUBSTANTIVE) == 20

#: Every SUBSTANTIVE span carries at least one PRIMARY claim and at most one
#: distinct PRIMARY target, which is what `validation.py` requires; asserted here
#: so a mis-typed carrier fails at its own line rather than in a finding list.
_primary_targets: dict[str, set[tuple[str, tuple[str, ...]]]] = defaultdict(set)
for _claim in emitted_claims:
    if _claim.role is ProvenanceRole.PRIMARY:
        _primary_targets[_claim.span_id].add(
            (_claim.target_kind.value, tuple(_claim.target_key))
        )
for _sid in _TABLE_SUBSTANTIVE:
    assert len(_primary_targets[_sid]) == 1, (_sid, _primary_targets[_sid])
for _span in spans:
    if _span.disposition is SemanticDisposition.SUPPORTING_AUTHORITY:
        assert not _primary_targets[_span.span_id], _span.span_id

#: **Accounting by strongest carrier.** Every clause lands in exactly one bucket,
#: and the two typed buckets are exactly the sixteen substantive clauses.
ACCOUNTING: dict[str, int] = defaultdict(int)
_BUCKET = {
    "fact": "typed",
    "component": "typed_at_component_scope",
    "reference": "supporting_authority_reference_owned",
    "fact_context": "supporting_authority_bounding_a_fact",
    "record": "supporting_authority_record_owned",
}
for _cid in CLAUSE_ORDER:
    _kinds = [str(c[0]) for c in EXPECTED_OBLIGATIONS[_cid]["carriers"]]  # type: ignore[union-attr]
    ACCOUNTING[_BUCKET[min(_kinds, key=lambda k: _STRENGTH[k])]] += 1
ACCOUNTING = dict(sorted(ACCOUNTING.items()))
assert ACCOUNTING == {
    "supporting_authority_bounding_a_fact": 5,
    "supporting_authority_record_owned": 10,
    "supporting_authority_reference_owned": 5,
    "typed": 11,
    "typed_at_component_scope": 5,
}, ACCOUNTING
assert sum(ACCOUNTING.values()) == 36
assert ACCOUNTING["typed"] + ACCOUNTING["typed_at_component_scope"] == 16

# ---------------------------------------------------------------------------
# Self-checks: pure validators only. No persistence, no gate, no acceptance.
# ---------------------------------------------------------------------------

LEDGER = ClassificationLedger(
    package_uuid=BINDING.package_uuid,
    release_version=BINDING.release_version,
    policy_version=SEMANTIC_POLICY_VERSION,
    policy_hash=semantic_policy_hash(),
    spans=tuple(spans),
    batches=(),
    acceptances=(),
)

touched = sorted({s.leaf_id for s in spans})
partition: list[str] = []
for lid in touched:
    partition.extend(validate_partition(lid, CORPUS.leaf_lengths[lid], tuple(spans)))
reason_codes = validate_reason_codes(tuple(spans))
standalone = list(validate_representation(DRAFT, LEDGER, CORPUS))

# --- Source canaries: derived, then compared. A mismatch is stop-and-explain -
CANARIES = {
    "records": (len(DRAFT.records), 1),
    "source_sites": (len(SITES), 2),
    "represented_leaves": (len(touched), 16),
    "policy_exclusions": (len(POLICY_EXCLUDED), 0),
    "container_leaves": (len(touched) + len(POLICY_EXCLUDED), 16),
    "clauses": (len(CLAUSE_ORDER), 36),
    "substantive_clauses": (
        sum(1 for s in spans if s.disposition is SemanticDisposition.SUBSTANTIVE),
        16,
    ),
    "components": (len(COMPONENT_DRAFTS), 9),
    "facts": (sum(len(c.facts) for c in COMPONENT_DRAFTS), 17),
    "references": (len(DRAFT.references), 9),
    "provenance_claims": (len(DRAFT.provenance), 52),
    "boundary_leaves_outside_this_batch": (len(BOUNDARY_REDERIVED), 557),
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

#: "All 36 discharged" is true and, alone, misleading: it counts a clause whose
#: text was handed to a supporting-authority span the same as one whose mechanic
#: entered the typed vocabulary. `audit` above already carries the per-clause
#: closure, so the obligation view here is that list keyed by clause rather than
#: a second copy of it, and `ACCOUNTING` classifies by strongest carrier.
OBLIGATION_CLOSURE = {row["clause_id"]: row for row in audit}
assert sorted(OBLIGATION_CLOSURE) == sorted(CLAUSE_ORDER)
assert sum(int(row["claims"]) for row in audit) == len(emitted_claims)

#: The closed irreducibility catalog, one line each, saying why *that* code is
#: false of this population rather than asserting a blanket "none of them fit".
#: Keys are checked against the live catalog, so a code added or renamed makes
#: this disclosure fail rather than quietly go stale.
REASON_DISPOSITION = {
    "contextual_applicability": (
        "false of all sixteen: each states its rule outright. 'on your turn' "
        "and 'while moving' are printed windows carried by MovementWindow and "
        "MovementComposition fields, not applicability prose the projection "
        "cannot enumerate."
    ),
    "subjective_judgment": (
        "false: nothing is left to anyone's assessment. 'whichever comes "
        "first', 'subtract the distance you already moved' and 'you can't use "
        "the new speed' are exact printed rules, and every distance the page "
        "prints stays a number on a creature's sheet rather than a field of "
        "any fact here."
    ),
    "open_ended_effect": (
        "false: every effect here is closed. The special-speed list is "
        "deliberately typed as a LISTING - named_in_a_non_exhaustive_list - "
        "which records that the source's enumeration is open WITHOUT inventing "
        "the members it does not print."
    ),
    "gamemaster_latitude": (
        "false: the source delegates nothing in this population. Choosing a "
        "speed, switching mid-move, the subtraction, the nonpositive outcome "
        "and the propagation are all printed rules."
    ),
    "natural_language_exception": (
        "false: these are the rules, not exceptions carved out of one. The "
        "nonpositive case is a required field beside the accounting rule, not "
        "prose qualifying it."
    ),
    "fiction_dependent_consequence": (
        "false: each consequence is mechanical and stated. Tracking remaining "
        "movement, resolving a mid-move switch and applying a speed change to "
        "a creature's numbers are adapter and adjudication work the record "
        "never claims to do."
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
assert len(_INTRO_ROWS) == 22, len(_INTRO_ROWS)
assert {r["kind"] for r in _INTRO_ROWS} == {"fact_family", "vocabulary_member"}, sorted(
    {str(r["kind"]) for r in _INTRO_ROWS}
)
NEW_FAMILIES = sorted(
    {str(r["name"]) for r in _INTRO_ROWS if r["kind"] == "fact_family"}
)
assert len(NEW_FAMILIES) == 7, NEW_FAMILIES
_MEMBER_ROWS = [r for r in _INTRO_ROWS if r["kind"] == "vocabulary_member"]
assert len(_MEMBER_ROWS) == 15, len(_MEMBER_ROWS)
#: A member row's `vocabulary` field is the vocabulary's SORTED member list, not
#: a vocabulary name, so the widened one is recognised by its member list.
_VOCABULARIES = sorted({tuple(r["vocabulary"]) for r in _MEMBER_ROWS})
assert len(_VOCABULARIES) == 12, _VOCABULARIES
#: **One of those twelve is not new.** `MovementMode` predates the introduction
#: manifest - it first appears under representation schema 2, before schema 3
#: registered the earliest contract, which is why it carries no introduction row
#: of its own - and it gains exactly one member here. Separated rather than
#: counted together, because widening an accepted vocabulary and minting a new
#: one are different acts with different review weight.
_MOVEMENT_MODE_VOCABULARY = tuple(sorted(m.value for m in MovementMode))
assert _MOVEMENT_MODE_VOCABULARY in _VOCABULARIES, _VOCABULARIES
NEW_VOCABULARIES = [v for v in _VOCABULARIES if v != _MOVEMENT_MODE_VOCABULARY]
assert len(NEW_VOCABULARIES) == 11, NEW_VOCABULARIES
WIDENED_MEMBERS = sorted(
    str(r["name"])
    for r in _MEMBER_ROWS
    if tuple(r["vocabulary"]) == _MOVEMENT_MODE_VOCABULARY
)
assert WIDENED_MEMBERS == ["jump"], WIDENED_MEMBERS
#: `MovementAllowanceBasis` is absent from this list on purpose: `DistanceUnit`
#: arrived at schema 5 and `movement_allowance` with its basis vocabulary at
#: schema 6. This batch reuses both rather than minting them.
assert tuple(sorted(u.value for u in DistanceUnit)) not in _VOCABULARIES
assert tuple(sorted(b.value for b in MovementAllowanceBasis)) not in _VOCABULARIES
_REUSED_FAMILIES = sorted(
    {
        str(row["name"]): str(row["introduced_in"])
        for row in introduction_manifest()
        if row["kind"] == "fact_family" and row["name"] == "movement_allowance"
    }.items()
)
assert _REUSED_FAMILIES == [
    ("movement_allowance", "5d-representation-schema-6")
], _REUSED_FAMILIES

#: The families this batch actually uses are the seven the schema introduced
#: plus the two it reuses: an admitted-but-unused family would be speculation,
#: and a reused one is evidence the crossing is an extension rather than a
#: parallel vocabulary.
_FAMILIES_USED = sorted({fact.FAMILY.value for _, fact in FACT_BY_LABEL.values()})
assert set(NEW_FAMILIES) <= set(_FAMILIES_USED), NEW_FAMILIES
REUSED_ACCEPTED_FAMILIES = sorted(set(_FAMILIES_USED) - set(NEW_FAMILIES))
assert REUSED_ACCEPTED_FAMILIES == [
    "movement_allowance",
    "movement_permission",
], REUSED_ACCEPTED_FAMILIES

#: Decision 4 binds `invariant_manifest()` into schema identity. This schema
#: declares **two** intrinsic invariant rows, read back rather than asserted
#: from memory. Both constrain `movement_depletion`, a family this schema mints,
#: so neither reaches an accepted element.
INTRINSIC_INVARIANTS = [
    dict(row)
    for row in invariant_manifest()
    if str(row["locus"]).removeprefix("fact:") in NEW_FAMILIES
]
assert [row["id"] for row in INTRINSIC_INVARIANTS] == [
    "movement_depletion.until.at-least-one",
    "movement_depletion.until.no-repeats",
], INTRINSIC_INVARIANTS
assert {str(row["locus"]) for row in INTRINSIC_INVARIANTS} == {
    "fact:movement_depletion"
}, INTRINSIC_INVARIANTS
_ACCEPTED_LOCI = {
    str(row["locus"]).removeprefix("fact:")
    for row in invariant_manifest()
    if str(row["locus"]).removeprefix("fact:") not in NEW_FAMILIES
}
assert "movement_depletion" not in _ACCEPTED_LOCI

#: **The widened member's witness is derived, not quoted.** `jump` enters
#: `MovementMode` because a clause carries a `movement_permission` fact naming
#: it; the obligation table already records which clause that is, so the
#: witness is read back out of the table instead of being named in prose. The
#: glossary *See also* list mentions Jumping, but it does so as a REFERENCE
#: target to another entry, not as a mode this record permits.
_JUMP_WITNESS_CLAUSES = sorted(
    clause
    for clause, row in EXPECTED_OBLIGATIONS.items()
    if ("fact_detail", MODES, "mode_jump") in row["carriers"]
)
assert _JUMP_WITNESS_CLAUSES == ["combat/3/0"], _JUMP_WITNESS_CLAUSES
_JUMP_WITNESS_TEXT = _text(_JUMP_WITNESS_CLAUSES[0])
assert "jumping" in _JUMP_WITNESS_TEXT, _JUMP_WITNESS_TEXT
assert not any(
    c in _JUMP_WITNESS_CLAUSES for _, _, clauses in CITATIONS for c in clauses
), _JUMP_WITNESS_CLAUSES

SCHEMA_EXTENSION = {
    "extends_the_schema": True,
    "from_schema": REVIEW_PRIOR_SCHEMA_VERSION,
    "to_schema": SCHEMA[0],
    "new_fact_families": NEW_FAMILIES,
    "new_vocabularies": {
        "count": len(NEW_VOCABULARIES),
        "members": [list(v) for v in NEW_VOCABULARIES],
    },
    "accepted_vocabulary_widened": {
        "MovementMode": list(_MOVEMENT_MODE_VOCABULARY),
        "members_added_here": WIDENED_MEMBERS,
        "witness_clauses": _JUMP_WITNESS_CLAUSES,
        "witness_text": _JUMP_WITNESS_TEXT,
        "why": (
            "MovementMode predates the introduction manifest: it first appears "
            "in f6d2813 under representation schema 2, so it carries no "
            "introduction row and was already statable under schema 3, the "
            "earliest registered contract. It carried walk, burrow, climb, "
            "crawl, fly and swim. The member added here is jump, and its "
            "witness is derived from the obligation table above rather than "
            "named in prose: the only clause carrying a movement_permission "
            "fact for JUMP is the one in witness_clauses, whose printed text "
            "is in witness_text. That clause is not a citation clause - the "
            "glossary's 'Climbing, Crawling, Flying, Jumping, and Swimming' "
            "See-also list names Jumping as a REFERENCE target to another "
            "entry, not as a mode this record permits, and it carries no fact. "
            "representation_schema_payload emits vocabularies by their sorted "
            "admitted values, so this one member moves the schema hash by "
            "itself, independent of the seven new families."
        ),
    },
    "accepted_families_reused_unchanged": {
        "movement_allowance": (
            "introduced at 5d-representation-schema-6 and carried unchanged. "
            "Schema 11 adds an OPTIONAL window field; the two accepted "
            "action.dash facts and the one action.ready fact carry no window "
            "key and their canonical form is identical under both contracts."
        ),
        "movement_permission": (
            "predates the manifest, like MovementMode. The one accepted "
            "instance is condition.prone::restricted_movement/options[0]/"
            "facts[0], mode=crawl. Nothing about it changes here."
        ),
    },
    "intrinsic_invariants_declared": INTRINSIC_INVARIANTS,
    "accepted_families_changed": [],
    "registered_transitions_touched": ["5d-lift-schema-10-to-11"],
    "note": (
        "Seven families over eleven new closed vocabularies plus one member "
        "added to an accepted one, and two accepted families reused rather "
        "than re-minted. The only field added to an accepted family is "
        "movement_allowance.window, which is optional and defaults to None, so "
        "every accepted fact key, component key and provenance coordinate has "
        "the same canonical form under both contracts. No ownership form "
        "changes and no field is made required on an accepted family, which is "
        "what makes the crossing a re-declaration rather than a rewrite."
    ),
    "no_runtime_geometry": (
        "Nothing here computes movement. DistanceUnit.FOOT names the foot the "
        "page prints in 'the distance in feet' - schema 5's member, reproduced "
        "rather than invented. No schema-11 vocabulary mentions a square, a "
        "segment, a diagonal or a corner; no fact carries a number; and "
        "subtracting the distance already moved, tracking a remaining "
        "allowance and applying a speed change to a creature's numbers are all "
        "runtime computation outside 5d. The excluded work is the computation, "
        "not the subject matter."
    ),
    "no_rank_over_the_modes": (
        "no order over the seven movement modes is printed, recorded or "
        "implied, and SpecialSpeedListing records that the source's list is "
        "non-exhaustive instead of closing it."
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

#: Schema 11 appears in none of the six anchors. The prior is a schema-10
#: object through and through, which is what makes the crossing necessary
#: rather than cosmetic.
assert SCHEMA[0] not in set(REVIEW_PRIOR_ANCHORS.values()), REVIEW_PRIOR_ANCHORS

#: **One registered crossing.** The prior is anchored at schema 10; this batch
#: proposes under schema 11, which the sixteen substantive clauses required. The
#: step is looked up in the registry rather than named, and `verify_lift_path`
#: re-proves the accepted content element by element under the new contract
#: instead of asserting it. Accepted bytes are never restamped: the frozen prior
#: still declares schema 10 after this run, and is asserted unchanged below.
STEPS = lift_path((PRIOR.oracle.schema_version, PRIOR.oracle.schema_hash), SCHEMA)
LIFT_RECORDS = verify_lift_path(STEPS, PRIOR.oracle.representation)
assert [r.lift_id for r in LIFT_RECORDS] == ["5d-lift-schema-10-to-11"], LIFT_RECORDS

#: Reading a superseded prior as current is a *finding*, not a silent pass, and
#: the lift is what clears it.
_unlifted_findings = validate_schema_binding(candidate_from_accepted_inputs(PRIOR))
assert _unlifted_findings, "a superseded prior must not read as current"
LIFTED, _lift_records = lift_accepted_inputs(PRIOR, SCHEMA)
assert [r.lift_id for r in _lift_records] == ["5d-lift-schema-10-to-11"]
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
#: most - each batch's accepted-under hash is what keeps schema 11 from
#: restamping six batches as one.
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
        "a DIFFERENT object: the in-memory copy this run lifts to schema 11. "
        "Reported rather than pinned, because oracle_payload carries the "
        "representation binding and the lift re-declares exactly that, so this "
        "value moves with every destination-pin change."
    ),
    "payload_keys_that_moved": _moved_keys,
    "inherited_authority_unchanged": {
        "representation_object_is_the_same_object": True,
        "spans_obligations_batches_acceptances_anchors_cross_by_identity": True,
        "per_batch_schema_anchors": REVIEW_PRIOR_ANCHORS,
        "schema_11_appears_in_no_anchor": True,
        "why_anchors_matter": (
            "each accepted batch keeps the hash it was reviewed under. A lift "
            "that re-derived anchors would restamp six batches as one and "
            "erase the distinction succession depends on."
        ),
    },
    "unlifted_prior_read_as_current_is_a_finding": list(_unlifted_findings),
    "note": (
        "the accepted prior is anchored at 5d-representation-schema-10 and "
        "this batch proposes under 5d-representation-schema-11, which the "
        "population's sixteen substantive clauses required. Exactly one "
        "registered transition separates them and it is exercised here rather "
        "than described. The transition adds fact families and vocabularies, "
        "widens one accepted vocabulary by one member and adds one optional "
        "field to movement_allowance; it adds no required field, no ownership "
        "form and no nullable-to-required change, so every accepted fact key, "
        "component key and provenance coordinate has the same canonical form "
        "under both contracts."
    ),
}

MERGED = _merge_representation(LIFTED.oracle.representation, DRAFT)
MERGED_LEDGER = ClassificationLedger(
    package_uuid=BINDING.package_uuid,
    release_version=BINDING.release_version,
    policy_version=SEMANTIC_POLICY_VERSION,
    policy_hash=semantic_policy_hash(),
    spans=tuple(LIFTED.oracle.spans) + tuple(spans),
    # The prior's acceptance evidence is carried, not dropped. Carrying it is
    # what makes the unaccepted set readable: every span validate_candidate
    # reports as unaccepted below is one of this batch's thirty-six proposed
    # rows, and none of the prior's five hundred and fifty-eight accepted ones.
    batches=tuple(LIFTED.batches),
    acceptances=tuple(LIFTED.acceptances),
)
merged_findings = list(validate_representation(MERGED, MERGED_LEDGER, CORPUS))

# --- Reference scope: standalone and combined, kept apart -------------------
#
# This batch emits nine outgoing references and none of them resolves inside the
# batch: all nine name glossary entries no accepted batch has ingested. What
# ALSO changes at the merge is that somebody else's citation - Dash's "Speed" -
# acquires a target, and that is a property of the merged candidate rather than
# of accepted authority.
_batch_records = {rec.semantic_key for rec in DRAFT.records}
_prior_records = {r.semantic_key for r in PRIOR.oracle.representation.records}
_merged_records = {r.semantic_key for r in MERGED.records}
assert SPEED not in _prior_records, "Speed is already in accepted authority"
assert SPEED in _merged_records, "the merge does not define Speed"

_cross_batch = sorted(
    {
        (r.from_record_key, r.target_record_key)
        for r in REFERENCES
        if r.target_record_key not in _batch_records
    }
)
#: All nine citations point outside this batch, and none of them resolves.
assert _cross_batch == [(SPEED, target) for _, target, _ in sorted(CITATIONS, key=lambda c: c[1])]
assert len(_cross_batch) == 9, _cross_batch
assert not {t for _, t in _cross_batch} & _prior_records, _cross_batch

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
#: **Ten, measured.** The nine this batch adds plus the one it inherits and does
#: not touch; `glossary.speed` leaves the list because this batch defines it.
#: This is a MEASURED result of running `acceptance._merge_representation` over
#: the lifted prior and this draft, not arithmetic over two pinned sets.
assert _merged_missing == sorted(
    {t for _, t, _ in CITATIONS} | {"glossary.concentration"}
), _merged_missing
assert len(_merged_missing) == 10, _merged_missing
assert sorted(set(_prior_missing) - set(_merged_missing)) == [SPEED], _prior_missing

#: The citing tuple, read out of the prior rather than described: who cites
#: Speed, from which component, in which scope, with which printed text.
INBOUND_CITATIONS = sorted(
    (
        {
            "from_record_key": ref.from_record_key,
            "from_component_key": ref.from_component_key,
            "scope_key": ref.scope_key,
            "source_text": ref.source_text,
            "target_record_key": ref.target_record_key,
        }
        for ref in PRIOR.oracle.representation.references
        if ref.target_record_key == SPEED
    ),
    key=lambda r: (str(r["from_record_key"]), str(r["source_text"])),
)
assert len(INBOUND_CITATIONS) == 1, INBOUND_CITATIONS
assert INBOUND_CITATIONS[0] == {
    "from_record_key": "action.dash",
    "from_component_key": "",
    "scope_key": "srd-5.2.1/rules-glossary",
    "source_text": "Speed",
    "target_record_key": SPEED,
}, INBOUND_CITATIONS

#: **The special-speed citations come from ONE sentence, not two.** It is the
#: sentence the reviewed manifest already records as split across leaves, and
#: the split is exactly why the Fly Speed reference carries two provenance
#: claims. Read it back rather than restating it: every clause the four
#: special-speed citations cite must fall inside that one reconstructed
#: sentence.
_SPECIAL_SPEED_SENTENCE = next(
    row for row in CROSS_LEAF_SENTENCES if "glossary/5/0" in row["clause_ids"]
)
_SPECIAL_SPEED_CITED = sorted({c for _, _, cl in CITATIONS[5:] for c in cl})
assert set(_SPECIAL_SPEED_CITED) <= set(
    _SPECIAL_SPEED_SENTENCE["clause_ids"]
), _SPECIAL_SPEED_CITED
assert len(_SPECIAL_SPEED_CITED) == 2, _SPECIAL_SPEED_CITED

REFERENCE_SCOPE = {
    "references_emitted": len(REFERENCES),
    "record_owned": sum(
        1 for r in REFERENCES if r.from_component_key == RECORD_OWNED_REFERENCE
    ),
    "from_the_see_also_citation": [
        f"{clauses[0]} -> {target}" for _, target, clauses in CITATIONS[:5]
    ],
    "from_the_special_speed_sentence": [
        f"{'+'.join(clauses)} -> {target}" for _, target, clauses in CITATIONS[5:]
    ],
    "the_special_speed_sentence": _SPECIAL_SPEED_SENTENCE["reconstructed_here"],
    "the_special_speed_sentence_clauses": _SPECIAL_SPEED_SENTENCE["clause_ids"],
    "split_across_two_clauses": [
        {"source_text": text, "target_record_key": target, "clauses": list(clauses)}
        for text, target, clauses in CITATIONS
        if len(clauses) > 1
    ],
    "cross_batch_citations": [f"{f} -> {t}" for f, t in _cross_batch],
    "cross_batch_citations_all_resolve_into_the_accepted_prior": False,
    "targets_defined_by_this_batch": [],
    "unresolved_targets_before_this_batch": _prior_missing,
    "unresolved_targets_after_the_merge": _merged_missing,
    "resolved_by_this_batch": [SPEED],
    "resolving_citation": INBOUND_CITATIONS[0],
    "publishable_alone": False,
    "note": (
        "This batch ADDS NINE unresolved citations and RESOLVES ONE. The nine "
        "are the five entries the See-also citation names - Climbing, "
        "Crawling, Flying, Jumping, Swimming - and the four special-speed "
        "entries named by the ONE sentence in the_special_speed_sentence: "
        "Burrow Speed, Climb Speed, Fly Speed and Swim Speed. That sentence "
        "is printed across a leaf boundary, which is why the Fly Speed "
        "reference straddles two clauses and carries two provenance claims. "
        "None of the nine is ingested by any accepted batch and this batch "
        "does not ingest them. The one it resolves is its own: action.dash "
        "already carries a reference whose source text is 'Speed' in the "
        "frozen accepted prior loaded by this run, where the target record "
        "did not exist; which batch first emitted that reference is not "
        "measured here. Combined with the prior's remaining "
        "glossary.concentration, the missing targets after this batch are ten."
    ),
    "resolution_scope": (
        "The Dash citation resolves in the MERGED CANDIDATE this run builds in "
        "memory - the lifted six-batch prior plus this proposal. It does NOT "
        "mean current accepted authority has changed: accepted authority is "
        "the frozen prior, it still carries two unresolved targets, nothing "
        "here is accepted, and the resolution becomes a property of accepted "
        "authority only at an acceptance that has not happened."
    ),
}

#: Both columns checked against a count DERIVED from the drafts rather than a
#: number chosen in advance: the validator reports one finding per unresolved
#: reference, not one per unresolved target. The two happen to coincide here
#: because no target is cited twice - the split reference is one reference with
#: two provenance claims, not two references.
UNRESOLVED_FINDINGS = {}
for _column, _found, _refs, _known in (
    ("standalone", standalone, DRAFT.references, _batch_records),
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

#: **Both finding lists asserted as exact tuples**, so a tenth standalone or an
#: eleventh merged finding cannot hide behind the expected ones.
STANDALONE_FINDINGS_EXACT = tuple(
    sorted(
        f"reference {SCOPE_KEY}:{text!r}: unknown target record {target}"
        for text, target, _ in CITATIONS
    )
)
assert tuple(sorted(standalone)) == STANDALONE_FINDINGS_EXACT, standalone
assert len(standalone) == 9, standalone
assert UNRESOLVED_FINDINGS["standalone"]["distinct_targets"] == sorted(
    {t for _, t, _ in CITATIONS}
)
MERGED_FINDINGS_EXACT = tuple(
    sorted(
        STANDALONE_FINDINGS_EXACT
        + (
            f"reference {SCOPE_KEY}:'Concentration': unknown target record "
            "glossary.concentration",
        )
    )
)
assert tuple(sorted(merged_findings)) == MERGED_FINDINGS_EXACT, merged_findings
assert len(merged_findings) == 10, merged_findings
assert UNRESOLVED_FINDINGS["merged"]["distinct_targets"] == _merged_missing
assert not any(
    f"unknown target record {SPEED}" in f for f in merged_findings
), merged_findings
REFERENCE_SCOPE["validator_findings"] = UNRESOLVED_FINDINGS
REFERENCE_SCOPE["standalone_findings_exact"] = list(STANDALONE_FINDINGS_EXACT)
REFERENCE_SCOPE["merged_findings_exact"] = list(MERGED_FINDINGS_EXACT)

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
#: Every accepted span, record, component, fact, provenance coordinate,
#: acceptance record and batch anchor is preserved: the merge's prefix is the
#: prior object element for element, the ledger's span prefix is the prior's
#: spans, and the acceptance metadata crossed the lift by object identity.
assert MERGED_LEDGER.spans[: len(PRIOR.oracle.spans)] == tuple(PRIOR.oracle.spans)
assert len(MERGED_LEDGER.spans) == REVIEW_PRIOR_SPANS + len(spans)

# --- Schema legality at every authority-bearing seam ------------------------
STRUCTURAL = [
    *representation_draft_violations(DRAFT),
    *held_structure_violations(DRAFT),
]
_component_rules: list[str] = []
for _c in COMPONENT_DRAFTS:
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
    "representation gate, merged with the lifted six-batch prior": len(merged_findings),
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
    "representation gate, merged with the lifted six-batch prior": (
        UNRESOLVED_FINDINGS["merged"]["findings"]
    ),
}
for _seam, _n in _EXPECTED_NONZERO.items():
    assert SEAMS[_seam] == _n, (SEAMS, _seam)
assert all(v == 0 for k, v in SEAMS.items() if k not in _EXPECTED_NONZERO), SEAMS
assert not _component_rules, _component_rules
assert not _declared_meaning, _declared_meaning
assert not STRUCTURAL, STRUCTURAL

# --- The candidate seam -----------------------------------------------------
CANDIDATE = ProjectionCandidate(
    binding=BINDING,
    classification=MERGED_LEDGER,
    representation=MERGED,
    schema_version=SCHEMA[0],
    schema_hash=SCHEMA[1],
)

#: **The six-part binding through the repository's own seam.** `validate_candidate`
#: is what checks that the binding, the classification ledger and the bound
#: corpus snapshot all name one release - two of three agreeing is not
#: agreement. It is run here in full and its findings are reported honestly: the
#: binding-class subset must be empty, and the rest are the acceptance-class
#: findings a PROPOSED batch is supposed to produce, because nothing here is
#: accepted. Filtering them away would be the dishonest move.
CANDIDATE_FINDINGS = list(validate_candidate(CANDIDATE, CORPUS))

_BINDING_PREFIXES = (
    "binding names package ",
    "binding names release ",
    "classification names package ",
    "classification names release ",
    "ledger declares semantic policy ",
    "ledger declares semantic policy hash ",
    "candidate declares representation schema ",
    "candidate declares representation schema hash ",
)


def _finding_class(finding: str) -> str:
    if finding.startswith(_BINDING_PREFIXES):
        return "release_binding_disagreement"
    if finding.endswith("no semantic spans"):
        return "corpus_leaf_not_yet_classified"
    if finding.endswith("no acceptance record"):
        return "span_not_accepted"
    if "unknown target record" in finding:
        return "unresolved_reference"
    return "other"


CANDIDATE_FINDINGS_BY_CLASS: dict[str, list[str]] = defaultdict(list)
for _f in CANDIDATE_FINDINGS:
    CANDIDATE_FINDINGS_BY_CLASS[_finding_class(_f)].append(_f)
BINDING_CLASS_FINDINGS = CANDIDATE_FINDINGS_BY_CLASS["release_binding_disagreement"]
#: **The binding check is the one that must be clean**, and it is.
assert BINDING_CLASS_FINDINGS == [], BINDING_CLASS_FINDINGS
assert CANDIDATE_FINDINGS_BY_CLASS["other"] == [], CANDIDATE_FINDINGS_BY_CLASS["other"][
    :20
]
assert sorted(k for k, v in CANDIDATE_FINDINGS_BY_CLASS.items() if v) == [
    "corpus_leaf_not_yet_classified",
    "span_not_accepted",
    "unresolved_reference",
], sorted(k for k, v in CANDIDATE_FINDINGS_BY_CLASS.items() if v)
assert sum(len(v) for v in CANDIDATE_FINDINGS_BY_CLASS.values()) == len(
    CANDIDATE_FINDINGS
), len(CANDIDATE_FINDINGS)
#: validate_candidate runs validate_representation too, so its reference
#: findings must be exactly the ten the merged gate already reported - no more.
assert sorted(CANDIDATE_FINDINGS_BY_CLASS["unresolved_reference"]) == sorted(
    merged_findings
), CANDIDATE_FINDINGS_BY_CLASS["unresolved_reference"]
#: Derived, so the counts cannot drift: one per unclassified leaf of the bound
#: release, and one per span in the merged ledger that carries no acceptance.
_classified_leaves = {s.leaf_id for s in MERGED_LEDGER.spans}
assert len(CANDIDATE_FINDINGS_BY_CLASS["corpus_leaf_not_yet_classified"]) == len(
    set(CORPUS.leaf_lengths) - _classified_leaves
), len(CANDIDATE_FINDINGS_BY_CLASS["corpus_leaf_not_yet_classified"])
assert len(CANDIDATE_FINDINGS_BY_CLASS["span_not_accepted"]) == len(spans), len(
    CANDIDATE_FINDINGS_BY_CLASS["span_not_accepted"]
)
#: Not merely the same count - the same span ids. This is the machine-readable
#: form of "keep machine rows PROPOSED": the unaccepted set is exactly this
#: batch's proposal and the accepted prior is untouched by it.
assert {s.span_id for s in spans} == {
    f.split()[1].rstrip(":") for f in CANDIDATE_FINDINGS_BY_CLASS["span_not_accepted"]
}, CANDIDATE_FINDINGS_BY_CLASS["span_not_accepted"][:5]
CANDIDATE_FINDING_CLASSES = {
    "release_binding_disagreement": {
        "count": 0,
        "example": None,
        "meaning": (
            "the binding, the classification ledger and the bound corpus "
            "snapshot all name one release; the ledger declares the semantic "
            "policy this build uses; the candidate declares the representation "
            "schema and hash this build implements. Matched by the literal "
            "prefixes the three validators emit. This is the class this run "
            "has to be clean at, and it is."
        ),
    },
    "corpus_leaf_not_yet_classified": {
        "count": len(CANDIDATE_FINDINGS_BY_CLASS["corpus_leaf_not_yet_classified"]),
        "example": CANDIDATE_FINDINGS_BY_CLASS["corpus_leaf_not_yet_classified"][0],
        "meaning": (
            "one per leaf of the bound release that no accepted or proposed "
            "span covers. This is the full-corpus obligation #137 governs, "
            f"reported honestly: the six accepted batches plus this proposal "
            f"cover {len(_classified_leaves)} leaves of the "
            f"{len(CORPUS.leaf_lengths)}-leaf release and the rest are "
            "undischarged. It is not a defect of this proposal and this "
            "proposal does not reduce it beyond its own sixteen leaves."
        ),
    },
    "span_not_accepted": {
        "count": len(CANDIDATE_FINDINGS_BY_CLASS["span_not_accepted"]),
        "example": CANDIDATE_FINDINGS_BY_CLASS["span_not_accepted"][0],
        "meaning": (
            "one per span of this proposal, because no acceptance record "
            "exists for them - which is the correct state for a proposal the "
            "Owner has not accepted. Asserted to be exactly this batch's "
            "thirty-six span ids, so none of the prior's five hundred and "
            "fifty-eight accepted spans is in this class."
        ),
    },
    "unresolved_reference": {
        "count": len(CANDIDATE_FINDINGS_BY_CLASS["unresolved_reference"]),
        "example": sorted(CANDIDATE_FINDINGS_BY_CLASS["unresolved_reference"])[0],
        "meaning": (
            "the ten dangling targets the merged representation gate already "
            "reported: this batch's nine outgoing citations plus the prior's "
            "inherited glossary.concentration. Asserted equal to that list "
            "rather than counted independently."
        ),
    },
}

# --- The consumer boundary: what a reader of this authority actually sees ----
#
# `_base_records` is the function every consumer of mechanical authority goes
# through. It is applied to the merged candidate IN MEMORY - nothing is
# persisted, published or activated - and every value below is read back off the
# resulting objects rather than off this run's own dictionaries.
BASE = _base_records(CANDIDATE)
assert SPEED in BASE, sorted(BASE)


def _component_of(record_key: str, component_key: str) -> object:
    return next(
        c for c in BASE[record_key].components if c.semantic_key == component_key
    )


def _held(record_key: str, component_key: str, label: str) -> object:
    component = _component_of(record_key, component_key)
    assert component.handling is ComponentHandling.STRUCTURED, component
    assert component.irreducibility_reason_code is None, component
    assert len(component.governing_prose) == 0, component
    _owner, _fact = FACT_BY_LABEL[label]
    assert _owner == component_key, (component_key, label)
    target = fact_key(_fact)
    return next(h for h in component.facts if fact_key(h.fact) == target)


def _clauses(span_ids: object) -> list[str]:
    """Derived span ids read back as the clause ids a reviewer can look up."""
    return sorted(_SPAN_TO_CLAUSE[s] for s in span_ids)


def _roles(target_kind: ProvenanceTargetKind, target_key: tuple[str, ...]) -> dict:
    """Role split for one merged-representation provenance target, by clause."""
    rows = [
        c
        for c in MERGED.provenance
        if c.target_kind is target_kind and tuple(c.target_key) == tuple(target_key)
    ]
    return {
        role.value: _clauses(c.span_id for c in rows if c.role is role)
        for role in (ProvenanceRole.PRIMARY, ProvenanceRole.CONTEXTUAL)
    }


CONSUMER_VIEW: dict[str, object] = {
    SPEED: {
        "kind": BASE[SPEED].kind.value,
        "component_keys": sorted(c.semantic_key for c in BASE[SPEED].components),
        "record_scope_span_ids": len(BASE[SPEED].span_ids),
        "clauses_carried_by_the_whole_record": len(spans),
        "assembled_from_sites": sorted({_site(c) for c in CLAUSE_ORDER}),
        "all_components_structured": sorted(
            {c.handling.value for c in BASE[SPEED].components}
        ),
        "note": (
            "one record assembled from two printed sites in two chapters - "
            "#137 contract 3's composite case. The second site is not reached "
            "by a label: nothing in Combat is labelled Speed. It is reached by "
            "the reciprocal citation the glossary entry prints, which is the "
            "membership rule the discovery manifest records."
        ),
    }
}
assert CONSUMER_VIEW[SPEED]["component_keys"] == sorted(COMPONENTS)
assert CONSUMER_VIEW[SPEED]["all_components_structured"] == ["structured"]
#: A base record carries the spans claimed at RECORD scope; the other
#: twenty-six hang off the components, facts and references that carry them,
#: which is the point of putting them there.
assert CONSUMER_VIEW[SPEED]["record_scope_span_ids"] == len(RECORD_CONTEXT) == 10

#: **The printed unit, reproduced.** `SpeedDefinitionFact` carries the foot the
#: page prints in "the distance in feet" and the window it prints in "when it
#: moves on its turn". No number is printed in this population and none is
#: carried: a creature's 30 lives on its sheet, not in this authority.
_definition = _held(SPEED, DEFINITION, "definition")
assert _definition.fact.unit is DistanceUnit.FOOT, _definition
assert _definition.fact.window is MovementWindow.OWN_TURN, _definition
#: The "no number" claim is checked against the dataclass itself, not against a
#: string comparison over annotations that a future `from __future__` import
#: would quietly make vacuous.
assert sorted(SpeedDefinitionFact.__dataclass_fields__) == [
    "FAMILY",
    "unit",
    "window",
], sorted(SpeedDefinitionFact.__dataclass_fields__)
CONSUMER_VIEW["speed_definition"] = {
    "family": _definition.fact.FAMILY.value,
    "unit": _definition.fact.unit.value,
    "window": _definition.fact.window.value,
    "clauses": _clauses(_definition.span_ids),
    "stated_by": _text("glossary/1/1"),
    "the_whole_fact_is": sorted(SpeedDefinitionFact.__dataclass_fields__),
    "no_number_is_carried": (
        "the two fields above are the whole of SpeedDefinitionFact; there is "
        "no distance field to carry a number in"
    ),
    "printed_unit_is_not_invented_geometry": (
        "DistanceUnit.FOOT is schema 5's member and names the foot the source "
        "prints. No schema-11 vocabulary mentions a square, a grid, a diagonal "
        "or a corner, and no fact in this batch carries a number. Reproducing "
        "a printed unit is the opposite of inventing geometry."
    ),
}

#: **Depletion, in printed order.** `until` is a tuple and the intrinsic
#: invariant forbids repeats without imposing a sort, so the order below is the
#: source's: used up, then done moving, and the resolution between them.
_depletion = _held(SPEED, DEPLETION, "depletion")
assert tuple(t.value for t in _depletion.fact.until) == (
    "allowance_used_up",
    "done_moving",
), _depletion
CONSUMER_VIEW["movement_depletion"] = {
    "family": _depletion.fact.FAMILY.value,
    "depletes": _depletion.fact.depletes.value,
    "until_in_printed_order": [t.value for t in _depletion.fact.until],
    "resolution": _depletion.fact.resolution.value,
    "clauses": _clauses(_depletion.span_ids),
    "stated_by": _text("combat/3/2"),
    "intrinsic_invariants_that_bind_it": [
        str(row["id"]) for row in INTRINSIC_INVARIANTS
    ],
    "note": (
        "the two terminators are the source's 'until it is used up or until "
        "you are done moving' and the resolution is its 'whichever comes "
        "first'. Nothing subtracts anything here: the accounting rule is named "
        "as a closed member, not performed."
    ),
}

#: **The propagation example the brief names.** One fact, one PRIMARY clause,
#: and four CONTEXTUAL clauses that bound it - the two halving sentences, the
#: zero floor and the reversal - so the rule a consumer reads carries every
#: printed sentence that narrows it.
_propagation = _held(SPEED, PROPAGATION, "propagation")
_prop_roles = _roles(
    ProvenanceTargetKind.FACT, fact_target_key(SPEED, PROPAGATION, _propagation.fact)
)
assert _prop_roles["primary"] == ["glossary/9/0"], _prop_roles
assert len(_prop_roles["contextual"]) == 4, _prop_roles
assert _clauses(_propagation.span_ids) == sorted(
    _prop_roles["primary"] + _prop_roles["contextual"]
), _propagation.span_ids
CONSUMER_VIEW["speed_change_propagation"] = {
    "family": _propagation.fact.FAMILY.value,
    "to": _propagation.fact.to.value,
    "magnitude": _propagation.fact.magnitude.value,
    "duration": _propagation.fact.duration.value,
    "primary_span": _prop_roles["primary"],
    "contextual_spans": _prop_roles["contextual"],
    "stated_by": _text("glossary/9/0"),
    "bounded_by": {cid: _text(cid) for cid in _prop_roles["contextual"]},
    "note": (
        "the four bounding clauses are printed examples and consequences of "
        "the one rule, not four more rules: halving a Speed halves each "
        "special speed, a special speed that drops to 0 cannot be used, and "
        "the reversal restores it. Each is claimed CONTEXTUAL on the one fact "
        "rather than typed as its own, because none states a mechanic the "
        "propagation fact does not already carry."
    ),
}

#: **The split reference, read off the merged representation.** `_base_records`
#: surfaces no references, so this is read from `MERGED.references` and
#: `MERGED.provenance` directly. One reference, two provenance claims, because
#: the source names Fly Speed in two sentences on two leaves - and
#: `_validate_provenance` rejects only exact duplicate edges, so two claims on
#: one reference is legal and two references would be the misrepresentation.
_fly = next(r for r in MERGED.references if r.target_record_key == "glossary.fly_speed")
_fly_roles = _roles(ProvenanceTargetKind.REFERENCE, reference_target_key(_fly))
assert _fly_roles["primary"] == [], _fly_roles
assert _fly_roles["contextual"] == ["glossary/5/0", "glossary/6/0"], _fly_roles
assert (
    sum(1 for r in MERGED.references if r.target_record_key == "glossary.fly_speed") == 1
)
CONSUMER_VIEW["split_reference"] = {
    "from_record_key": _fly.from_record_key,
    "from_component_key": _fly.from_component_key,
    "record_owned": _fly.from_component_key == RECORD_OWNED_REFERENCE,
    "scope_key": _fly.scope_key,
    "source_text": _fly.source_text,
    "target_record_key": _fly.target_record_key,
    "references_emitted_for_this_target": 1,
    "provenance_claims": _fly_roles["contextual"],
    "clause_texts": {cid: _text(cid) for cid in _fly_roles["contextual"]},
    "why_one_reference_and_two_claims": (
        "the source prints the same pointer twice - 'such as a Burrow Speed, "
        "Climb Speed, Fly Speed, or Swim Speed' runs across a leaf boundary, "
        "so Fly Speed is named on glossary/5/0 and again on glossary/6/0. One "
        "citation of one entry is one reference; the two printings are two "
        "provenance claims on it. Emitting two references would assert the "
        "source cited Fly Speed twice, which it did not."
    ),
    "every_other_reference_carries_exactly_one_claim": {
        target: len(_roles(ProvenanceTargetKind.REFERENCE, reference_target_key(r))[
            "contextual"
        ])
        for target, r in sorted(
            (r.target_record_key, r) for r in MERGED.references
            if r.from_record_key == SPEED
        )
    },
}
assert sorted(
    CONSUMER_VIEW["split_reference"]["every_other_reference_carries_exactly_one_claim"]
    .values()
) == [1] * 8 + [2]

#: **The inbound citation, resolved in the merged candidate only.** Dash has
#: cited "Speed" since actions-1 and the target did not exist. Read back off
#: the consumer view rather than asserted: Dash's outgoing targets now include
#: this record.
_dash_targets = sorted(
    {
        r.target_record_key
        for r in MERGED.references
        if r.from_record_key == "action.dash"
    }
)
assert SPEED in _dash_targets, _dash_targets
CONSUMER_VIEW["inbound_citation_resolution"] = {
    "citation": INBOUND_CITATIONS[0],
    "dash_outgoing_targets_in_the_merged_candidate": _dash_targets,
    "resolves_in": "the merged candidate this run builds in memory",
    "does_not_resolve_in": (
        "accepted authority, which is the frozen prior and is unchanged by "
        "this run. The resolution becomes a property of accepted authority "
        "only at an acceptance that has not happened."
    ),
    "accepted_movement_facts_that_already_exist": MANIFEST["prior_movement_facts"],
}

#: The nine components a consumer sees, with the family of every fact in each.
CONSUMER_VIEW["components"] = {
    c.semantic_key: {
        "handling": c.handling.value,
        "facts": [h.fact.FAMILY.value for h in c.facts],
        "fact_clauses": _clauses({s for h in c.facts for s in h.span_ids}),
        "component_scope_clauses": _clauses(c.span_ids),
    }
    for c in sorted(BASE[SPEED].components, key=lambda c: c.semantic_key)
}
assert sum(
    len(row["facts"]) for row in CONSUMER_VIEW["components"].values()
) == 17, CONSUMER_VIEW["components"]
#: Five components carry a component-scope span and four do not: a component
#: claims a span only when the source printed a sentence about the whole group.
assert sorted(
    k
    for k, v in CONSUMER_VIEW["components"].items()
    if v["component_scope_clauses"]
) == sorted({c for c, _ in COMPONENT_PRIMARY})

# ---------------------------------------------------------------------------
# The proposal
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
        f"{ORIGIN_LABEL} (CRD Issue 5d batch speed-1, representation schema 11)"
    ),
)
payload = proposal_payload(PROPOSAL)
ident = proposal_identity(PROPOSAL)
#: No pinned expectation: this is a fresh proposal, so its identity is reported
#: for review rather than asserted against a value chosen in advance.
assert ident != REVIEW_PRIOR_IDENTITY, "the proposal is not the accepted prior"
assert ident != LIFTED_IDENTITY, "the proposal is not the lifted prior"
#: **Every machine row stays PROPOSED.** Read back off the proposal object,
#: because `span_payload` deliberately omits review state - a span set that
#: means the same thing must compare equal however it was reviewed - so the
#: artifact cannot carry this claim and the object must.
assert {p.span.review_state for p in PROPOSAL.proposed_spans} == {
    ReviewState.PROPOSED
}, "a proposed span is not PROPOSED"
#: And the artifact is a proposal, not accepted inputs. `load_accepted_inputs`
#: rejects on this key first, so it is the boundary a reviewer can see.
assert payload["artifact_kind"] == "machine_proposal", payload["artifact_kind"]
assert "acceptance" not in payload and "obligations" not in payload, sorted(payload)
#: The proposed representation is exactly the draft this file composed, through
#: the committed payload function rather than by object comparison.
assert payload["proposed_representation"] == representation_payload(DRAFT)

counts: dict[str, int] = defaultdict(int)
for s in spans:
    counts[s.disposition.value] += 1

COUNTS = {
    "records": len(DRAFT.records),
    "source_sites": len(SITES),
    "represented_leaves": len(touched),
    "policy_exclusions": len(POLICY_EXCLUDED),
    "clauses": len(CLAUSE_ORDER),
    "spans": len(spans),
    "substantive": counts["substantive"],
    "supporting_authority": counts["supporting_authority"],
    "non_mechanical": counts["non_mechanical"],
    "unresolved": counts["unresolved"],
    "components": len(COMPONENT_DRAFTS),
    "facts": sum(len(c.facts) for c in COMPONENT_DRAFTS),
    "prose_bindings": len(DRAFT.prose_bindings),
    "relationships": len(DRAFT.relationships),
    "references": len(DRAFT.references),
    "provenance": len(DRAFT.provenance),
    "cross_leaf_sentences": len(CROSS_LEAF_SENTENCES),
    "boundary_leaves_outside_this_batch": len(BOUNDARY_REDERIVED),
}
assert COUNTS["substantive"] + COUNTS["supporting_authority"] == COUNTS["clauses"]
assert COUNTS["non_mechanical"] == COUNTS["unresolved"] == 0, COUNTS
assert COUNTS["substantive"] == 16 and COUNTS["supporting_authority"] == 20, COUNTS

COUNT_DERIVATION = {
    "clauses": (
        "the reviewed inventory in the committed discovery manifest, "
        "re-proved gap-free against the live corpus in this run"
    ),
    "substantive": (
        "a clause is SUBSTANTIVE exactly when some carrier in the reviewed "
        "obligation table claims PRIMARY - a fact or a component. Derived from "
        "the table, then checked against the composition's own partition."
    ),
    "facts": (
        "counted off the component drafts, not off the obligation table. "
        "Seventeen facts over sixteen substantive clauses is not a mismatch: "
        "four sentences each name several members of one group, and three "
        "rules are each printed across more than one clause."
    ),
    "provenance": (
        "one claim per (element, span, role) edge. Fifty-two edges over "
        "thirty-six clauses, because a clause that states a rule and cites an "
        "entry in the same breath discharges both at once."
    ),
    "references": (
        "one per distinct printed pointer, not one per printing. Nine "
        "pointers, ten reference-scope provenance claims, because Fly Speed is "
        "named on two leaves."
    ),
    "test_counts_are_not_this_count": (
        "the schema-11 test module's composition is the same composition and "
        "is asserted equal to this proposal's payload. It is corroboration, "
        "not the measure: completeness here is judged against the thirty-six "
        "printed clauses of the bound source, which is what the partition "
        "proof and the obligation table check."
    ),
}

GAPS_WITNESSED = sorted(CHECKPOINT_GAP_WITNESSES)

# ---------------------------------------------------------------------------
# The audit artifact
# ---------------------------------------------------------------------------
AUDIT_DOC: dict[str, object] = {
    "_": (
        "Review artifact for CRD Issue 5d batch speed-1. Regenerate with "
        f"`python .claude/review-notes/{ORIGIN_LABEL}` from the repository "
        "root. Nothing here is accepted, published, activated or persisted."
    ),
    "issue": "#137 / CRD Issue 5d",
    "batch_id": "speed-1",
    "proposal_identity": ident,
    "proposal_identity_scope": (
        "the identity of THIS proposal artifact: binding, policy, schema, "
        "proposed spans and proposed representation. It is not an oracle "
        "identity, not a projection identity and not an acceptance. It becomes "
        "authority only at an acceptance that has not happened."
    ),
    "batch_selection": {
        "record": SPEED,
        "membership_rule": MANIFEST["membership_rule"],
        "sites": [
            {
                "site": site,
                "container_path": _path_of(cid),
                "label": LABELS[cid],
                "leaves": sum(1 for lid in touched if LEAF_SITE[lid] == site),
            }
            for site, cid in SITES
        ],
        "the_label_is_not_the_query": {
            "entries_labelled_speed_in_the_release": len(SPEED_LABELED),
            "entries_labelled_speed_that_are_members": 1,
            "the_member_is_selected_by_path": _path_of(GLOSSARY_ENTRY.container_id),
            "entries_labelled_speed_that_are_not_members": [
                p
                for p in SPEED_LABELED_PATHS
                if p != _path_of(GLOSSARY_ENTRY.container_id)
            ],
            "second_site_label": LABELS[COMBAT_ENTRY.container_id],
            "note": (
                "four entries in the bound release are labelled 'Speed' and "
                "only one of them is this rule; the other three are listed "
                "above by their full container paths and are adjudicated out. "
                "Meanwhile the second site is labelled 'Movement and Position'. "
                "A label query would have been wrong in both directions at "
                "once, which is why the glossary member is selected by its "
                "full container path and the second site is derived from the "
                "printed reciprocal citation instead."
            ),
        },
        "direction": DIRECTION,
        "naive_cooccurrence_would_have_added": NAIVE_ADDS,
        "naive_cooccurrence_note": (
            "three entries beneath Playing the Game > Combat mention the "
            "glossary and Speed together. One of them IS the second site; the "
            "other two cite the glossary for some other rule and are asserted "
            "non-members here."
        ),
        "adjudicated_boundary": ADJUDICATED_BOUNDARY,
        "adjudicated_boundary_note": MANIFEST["adjudicated_boundary_note"],
        "cross_leaf_sentences": CROSS_LEAF_SENTENCES,
    },
    "representation_schema": {"version": SCHEMA[0], "hash": SCHEMA[1]},
    "schema_extension": SCHEMA_EXTENSION,
    "semantic_policy": {
        "version": SEMANTIC_POLICY_VERSION,
        "hash": semantic_policy_hash(),
    },
    "release_binding": {
        **BINDING_PARTS,
        "parts": len(BINDING_PARTS),
        "read_through": (
            "projection.release_binding_payload - the canonical payload of "
            "ReleaseBinding, which is what every downstream identity is "
            "computed over"
        ),
        "verified_at_the_seam": (
            "projection.validate_candidate, run over the merged candidate. It "
            "is the repository's own check that the binding, the "
            "classification ledger and the bound corpus snapshot all name one "
            "release - two of three agreeing is not agreement. Its "
            "binding-class findings are empty."
        ),
        "binding_class_findings": BINDING_CLASS_FINDINGS,
        "all_candidate_findings_by_class": CANDIDATE_FINDING_CLASSES,
        "other_candidate_findings_note": (
            "reported, not filtered. validate_candidate also enforces the "
            "explicit-acceptance rule, and nothing in this batch is accepted - "
            "every span is PROPOSED - so those findings are the correct result "
            "for a proposal and would be cleared by an acceptance that has not "
            "happened."
        ),
        "source_rederivation": {
            "rederived_from_the_committed_pdf_in_this_process": sorted(
                BINDING_REDERIVED_HERE
            ),
            "disclosed_from_the_published_5c_release_record": sorted(
                BINDING_DISCLOSED
            ),
            "why_the_sixth_is_disclosed": (
                "The five values above are re-derived from the committed PDF "
                "by this run and asserted. This sixth is carried from the "
                "published CRD Issue 5c release record and disclosed as "
                "carried: recomputing it needs a session over the persisted "
                "rp_sources rows plus read-back vector state "
                "(persistence.recompute_persisted_digest), and verifying a "
                "published release against declared values is "
                "operational.load_verified_operational_corpus, the narrower "
                "downstream trust seam. Neither requires a publish; this run "
                "performs neither, and no operational database evidence was "
                "produced by it -- no session, no rp_sources, no Chroma, no "
                "persistence layer was touched."
            ),
        },
        "operational_database_evidence": {
            "performed_by_this_run": [],
            "note": (
                "NONE. This run opens no session, reads no rp_sources row, "
                "queries no vector store and persists nothing. The five "
                "re-derived values are source rederivation from the committed "
                "PDF; the sixth is a disclosed carry. No claim in this "
                "artifact rests on operational database evidence."
            ),
        },
    },
    "boundary": {
        "derived_from": (
            "the glossary entry the bound release labels 'Speed' beneath "
            "'Rules Definitions', plus the Combat entry its See-also citation "
            "points at, which the release labels 'Movement and Position'"
        ),
        "printed_pages": sorted({LEAF_BY_ID[lid].page_index + 1 for lid in touched}),
        "page_index_note": (
            "printed_page is page_index + 1, the same convention the accepted "
            "batches use"
        ),
        "policy_exclusions": POLICY_EXCLUDED,
        "leaves_that_print_the_word_and_stay_outside": {
            "count": len(BOUNDARY_REDERIVED),
            "by_section": BOUNDARY_BY_SECTION,
            "lowercase_only_leaf_count": MANIFEST[
                "boundary_lowercase_only_leaf_count"
            ],
            "standalone_token_leaf_count": MANIFEST[
                "boundary_standalone_token_leaf_count"
            ],
            "all_represented_by_5c": MANIFEST["boundary_all_represented_by_5c"],
            "rederived_and_checked_against_the_manifest": True,
            "note": MANIFEST["boundary_note"],
        },
        "canaries": {
            k: {"derived": v[0], "expected": v[1]} for k, v in CANARIES.items()
        },
        "extraction_artifacts_carried_verbatim": MANIFEST["extraction_artifacts"],
        "no_grid_language_in_the_source": (
            "the population prints no 'square', 'grid', 'battle map' or "
            "'token', and prints no number. The only unit it prints is the "
            "foot, which DistanceUnit.FOOT reproduces. Recorded here as a "
            "boundary of the source, not a decision of this run."
        ),
    },
    "source_inventory": {
        "manifest": MANIFEST_PATH.relative_to(REPO).as_posix(),
        "manifest_sha256": MANIFEST_DIGEST,
        "generated_by": MANIFEST["generated_by"],
        "carries_dispositions": False,
        "carries_a_record_assignment": False,
        "leaves": len(MANIFEST_LEAVES),
        "clauses": len(CLAUSE_ORDER),
        "tie_to_the_bound_source": (
            "every reviewed leaf id exists in the corpus this run just built "
            "from the PDF and holds byte-identical content; the reviewed "
            "clause extents partition each of the sixteen leaves end to end, "
            "starting at 0 and stopping at the leaf's length, and the "
            "concatenation reconstructs the leaf byte for byte. The manifest "
            "supplies the reviewed coordinates; the PDF supplies the content."
        ),
    },
    "counts": COUNTS,
    "count_derivation": COUNT_DERIVATION,
    "provenance_shapes": PROVENANCE_SHAPES,
    "prior_provenance_shapes": MANIFEST["prior_provenance_shapes"],
    "prior_provenance_shapes_note": (
        "the accepted six-batch prior's own shape tally, carried from the "
        "discovery manifest. It records component/primary: 20, which is the "
        "precedent for claiming a sentence about a whole group on the "
        "component rather than splitting it across the group's members."
    ),
    "record_shapes": {
        SPEED: {
            "kind": RECORD_KIND[SPEED].value,
            "components": [c.semantic_key for c in COMPONENT_DRAFTS],
            "facts": {
                c.semantic_key: [f.FAMILY.value for f in c.facts]
                for c in COMPONENT_DRAFTS
            },
            "prose_bindings": 0,
            "references": len(REFERENCES),
            "relationships": 0,
        }
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
        "standalone_findings_asserted_as_a_tuple": list(STANDALONE_FINDINGS_EXACT),
        "merged_findings": merged_findings,
        "merged_findings_asserted_as_a_tuple": list(MERGED_FINDINGS_EXACT),
        "candidate_findings_binding_class": BINDING_CLASS_FINDINGS,
        "candidate_findings_by_class": CANDIDATE_FINDING_CLASSES,
        "candidate_findings_note": (
            f"{len(CANDIDATE_FINDINGS)} findings, every one of them in one of "
            "three classes, all of them the correct result for a proposal of "
            "one record: leaves of the release no batch has classified yet, "
            "spans no acceptance has accepted, and the ten unresolved "
            "reference targets. They are counted and classed rather than "
            "listed, with one example each, because a full dump would be tens "
            "of megabytes of the same two sentences. Nothing is filtered: the "
            "class tally sums to the total and the 'other' class is asserted "
            "empty."
        ),
        "what_zero_would_not_prove": (
            "these judge shape, not fidelity. Neither column is zero here and "
            "both are asserted as exact tuples: nine standalone findings, one "
            "per outgoing citation, and ten merged, the nine plus the prior's "
            "inherited glossary.concentration. A clean run would not have "
            "meant the meanings are right - that is what semantic review is "
            "for."
        ),
    },
    "classification_partitions": {
        lid: {
            "record": SPEED,
            "site": LEAF_SITE[lid],
            "printed_page": LEAF_BY_ID[lid].page_index + 1,
            "content": MANIFEST_LEAVES[lid],
            "cells": PARTITIONS[lid],
        }
        for lid in touched
    },
    "reference_scope": REFERENCE_SCOPE,
    "schema_stops": [],
    "schema_stops_note": (
        "none open. The six gaps the discovery checkpoint found are all closed "
        "by schema 11, every one of them witnessed by at least one clause in "
        "this batch, and no span is emitted UNRESOLVED."
    ),
    "gaps_closed": GAPS_WITNESSED,
    "gap_witnesses": {g: list(v) for g, v in sorted(CHECKPOINT_GAP_WITNESSES.items())},
    "irreducibility_catalog_disposition": dict(REASON_DISPOSITION)
    | {
        "conclusion": (
            "none of the six closed reasons is affirmatively true of any of "
            "the sixteen substantive clauses, so this batch emits ZERO prose "
            "bindings. That is a positive claim, not an omission: binding one "
            "anyway would record a vocabulary gap as an irreducibility, which "
            "is exactly the misfiling the closed catalog exists to prevent."
        )
    },
    "obligation_closure": OBLIGATION_CLOSURE,
    "obligation_accounting": ACCOUNTING,
    "obligation_derivation": (
        "The obligation table is typed from the reviewed discovery checkpoint "
        "- section 3's dispositions and section 4's gap table - and carries a "
        "TUPLE of carriers per clause, which is new in this batch. Nothing in "
        "it is computed from what this file emits. The emission loop then "
        "builds spans and provenance claims from the table, and those claims "
        "are asserted to be the same multiset as the composition's own "
        "provenance, which was written independently from the schema-11 "
        "composition. Two statements of the same judgment, checked against "
        "each other; neither derived from the other."
    ),
    "span_granularity": (
        "PROPOSED, not final. Thirty-six spans is the granularity the reviewed "
        "inventory records and this run proves gap-free; it is not an Owner "
        "decision about how finely this population should be cut. A reviewer "
        "who would merge or split clauses is disagreeing with the proposal, "
        "not finding a defect in it."
    ),
    "evidence_classes": [
        {
            "class": "source extraction and partition reconstruction",
            "executed_here": True,
            "strength": (
                "strong for coverage and span boundaries: the reviewed clause "
                "extents are re-proved gap-free against the sixteen leaves "
                "this run just extracted from the PDF, and the 557-leaf "
                "exclusion is re-derived rather than transcribed. Says nothing "
                "about whether the meaning assigned to a span is right - that "
                "is what semantic review is for"
            ),
        },
        {
            "class": "obligation closure against the reviewed inventory",
            "executed_here": True,
            "strength": (
                "exposes omission, duplication and carrier drift against a "
                "table typed from the checkpoint rather than from the "
                "emission, including which fact of a multi-fact component "
                "carries a clause and which of a clause's several carriers "
                "names its disposition. It does not prove the checkpoint's "
                "judgment is right; it proves the proposal states that "
                "judgment and no other"
            ),
        },
        {
            "class": "structural validation",
            "executed_here": True,
            "strength": (
                "the repository's own checkers over the emitted draft and over "
                "the merge acceptance would validate. These judge shape, not "
                "fidelity"
            ),
        },
        {
            "class": "release-binding agreement",
            "executed_here": True,
            "strength": (
                "all six parts read through release_binding_payload and "
                "checked at validate_candidate, the seam that requires the "
                "binding, the classification ledger and the bound corpus "
                "snapshot to name one release. Five values are source "
                "rederivation from the committed PDF; the sixth is a disclosed "
                "carry and no operational database evidence was performed"
            ),
        },
        {
            "class": "consumer projection assertion",
            "executed_here": True,
            "strength": (
                "_base_records is applied to the merged candidate in memory "
                "and every distinction the source prints is read back off "
                "those objects - the printed unit, the depletion terminators "
                "in printed order, the propagation fact's one PRIMARY and four "
                "CONTEXTUAL clauses, and Dash's citation acquiring a target. "
                "Nothing is persisted"
            ),
        },
        {
            "class": "schema succession",
            "executed_here": True,
            "strength": (
                "one registered crossing, 5d-lift-schema-10-to-11, exercised "
                "element by element, with the inherited acceptance record "
                "asserted to cross by object identity. Proves the crossing; "
                "performs none of it"
            ),
        },
        {
            "class": "cross-batch reference resolution",
            "executed_here": True,
            "strength": (
                "stated at two scopes and MEASURED at both by running "
                "acceptance._merge_representation over the lifted prior and "
                "this draft, not by arithmetic over two pinned sets. "
                "Standalone: nine findings, one per outgoing citation, none of "
                "which this batch defines. Combined with the lifted prior: "
                "ten, the nine plus the prior's inherited "
                "glossary.concentration, with glossary.speed dropping out "
                "because this batch defines it. Accepted authority is "
                "unchanged"
            ),
        },
        {
            "class": "full-corpus completeness",
            "executed_here": False,
            "strength": (
                "NOT claimed. This is one record of the Rules Glossary and its "
                "governing Combat section. The corpus #137 governs is "
                "untouched and undischarged"
            ),
        },
        {
            "class": "PDF rederivation is not operational-database proof",
            "executed_here": True,
            "strength": (
                "what this run proves is that the committed PDF plus the "
                "committed transform config reproduce the bound corpus and "
                "five of the six binding values. It proves nothing about any "
                "persisted rp_sources row, vector store or published release, "
                "because it touches none of them"
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
    "consumer_boundary_proofs": CONSUMER_VIEW,
    "schema_succession": SUCCESSION,
    "accepted_prior": {
        "path": REVIEW_PRIOR_PATH.relative_to(REPO).as_posix(),
        "content_sha256_before": _prior_content_before,
        "blob": _prior_blob_before,
        "identity": PRIOR_IDENTITY,
        "schema_version": PRIOR.oracle.schema_version,
        "batches": sorted(b.batch_id for b in PRIOR.batches),
        "spans": len(PRIOR.oracle.spans),
        "obligations": len(PRIOR.oracle.obligations),
        "read_only": (
            "this run reads the frozen prior and never writes it. Its bytes, "
            "its Git blob id and its accepted identity are asserted unchanged "
            "before and after every write this run performs."
        ),
    },
    "disjointness_from_the_accepted_prior": DISJOINT,
    "review_disposition": {
        "open_schema_stops": [],
        "residues": [
            "the nine entries this batch cites - Climbing, Crawling, Flying, "
            "Jumping, Swimming, Burrow Speed, Climb Speed, Fly Speed and Swim "
            "Speed - are unresolved and belong to later glossary batches. This "
            "batch does not ingest them",
            "glossary.concentration remains unresolved from the accepted "
            "prior and is untouched here",
            "Dash's Speed citation resolves in the merged candidate only. "
            "Accepted authority still carries two unresolved targets and does "
            "so until an acceptance that has not happened",
            "span granularity is proposed, not settled",
            "the full-corpus obligation #137 governs is undischarged: this is "
            "one record",
        ],
        "requires_owner_authorization_before": [
            "any acceptance of this batch into committed authority",
            "any acceptance is also what would carry the accepted prior across "
            "5d-lift-schema-10-to-11; this run proves the crossing and "
            "performs none of it",
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
        "The parent writes both artifacts in their final form, then "
        "re-executes this generator in a separate process, then compares the "
        "final bytes of both files and asserts the child minted the same "
        "proposal identity."
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
        "python .claude/review-notes/" + ORIGIN_LABEL + "   (from the "
        "repository root). Every input is repository-retained: the committed "
        "PDF, the committed discovery manifest, the committed frozen prior and "
        "the package under src/."
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
RERUN = os.environ.get("SPEED1_RERUN") == "1"
FINAL_SHA256 = {
    PROPOSAL_FILE: hashlib.sha256(_proposal_bytes).hexdigest(),
    AUDIT_FILE: hashlib.sha256(_audit_bytes).hexdigest(),
}
DETERMINISTIC: bool | None = None
if not RERUN:
    _child = subprocess.run(
        [sys.executable, str(Path(__file__).resolve())],
        env={**os.environ, "SPEED1_RERUN": "1"},
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
print(f"batch          speed-1: one composite record {SPEED}")
print(f"sites          {[s for s, _ in SITES]}  "
      f"(glossary by container path; combat by the printed reciprocal citation)")
print(f"records        {COUNTS['records']}")
print(f"leaves         {COUNTS['represented_leaves']}  "
      f"(policy exclusions {COUNTS['policy_exclusions']})")
print(f"clauses        {COUNTS['clauses']} (reviewed inventory, re-proved gap-free)")
print(f"spans          {COUNTS['spans']}")
print(f"  substantive  {COUNTS['substantive']}")
print(f"  supporting   {COUNTS['supporting_authority']}")
print(f"components     {COUNTS['components']}  (all STRUCTURED)")
print(f"facts          {COUNTS['facts']} over {COUNTS['substantive']} substantive clauses")
print(f"prose bindings {COUNTS['prose_bindings']}  (none; no closed reason is true)")
print(f"references     {COUNTS['references']}  "
      f"(Fly Speed carries two provenance claims)")
print(f"provenance     {COUNTS['provenance']}  {json.dumps(PROVENANCE_SHAPES)}")
print(f"relationships  {COUNTS['relationships']}")
print(f"accounting     {json.dumps(ACCOUNTING)}")
print()
for _seam, _n in SEAMS.items():
    print(f"{_seam:74} {_n}")
print(f"{'candidate findings, all classes':74} {len(CANDIDATE_FINDINGS)}")
print(f"{'  of which binding class':74} {len(BINDING_CLASS_FINDINGS)}")
print()
print(f"wire trip      {WIRE_ROUND_TRIP}")
print(f"binding parts  {len(BINDING_PARTS)} via release_binding_payload; "
      f"{len(BINDING_REDERIVED_HERE)} rederived from the PDF, "
      f"{len(BINDING_DISCLOSED)} disclosed as carried")
print("db evidence    none performed by this run")
print(f"gaps closed    {GAPS_WITNESSED}")
print()
print(f"prior identity (frozen file)   {PRIOR_IDENTITY}")
print(f"lifted identity (this head)    {LIFTED_IDENTITY}")
print(f"lift steps                     {[r.lift_id for r in LIFT_RECORDS]}")
print(f"prior unchanged                {AUDIT_DOC['accepted_prior']['unchanged']}")
print(f"live oracle unchanged          {LIVE_ORACLE_UNCHANGED}")
print()
print(f"unresolved, standalone  {UNRESOLVED_FINDINGS['standalone']['findings']} "
      f"findings / {len(UNRESOLVED_FINDINGS['standalone']['distinct_targets'])} targets")
print(f"unresolved, combined    {UNRESOLVED_FINDINGS['merged']['findings']} "
      f"findings / {len(_merged_missing)} targets  {_merged_missing}")
print(f"resolved by this batch  {REFERENCE_SCOPE['resolved_by_this_batch']} "
      f"(in the merged candidate only)")
print()
print(f"proposal       {(OUT / PROPOSAL_FILE).relative_to(REPO).as_posix()}  "
      f"({FINAL_SHA256[PROPOSAL_FILE]})")
print(f"audit          {(OUT / AUDIT_FILE).relative_to(REPO).as_posix()}  "
      f"({FINAL_SHA256[AUDIT_FILE]})")
print(f"deterministic  {DETERMINISTIC}")
print()
print("NOT accepted, NOT published, NOT activated, NOT persisted. "
      "accept_proposal was not called; Owner acceptance is still required.")
