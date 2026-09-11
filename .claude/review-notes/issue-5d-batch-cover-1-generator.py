"""CRD Issue 5d — batch `cover-1`, representation schema 10.

Executable generator for the cover-1 proposal and its audit. It reads the
committed SRD through the 5c pipeline, re-derives the Cover population from the
source's own two entry containers, takes the reviewed clause coordinates from
the committed discovery manifest, re-proves that those coordinates cut the
*bound* leaves gap-free and byte-for-byte, assigns each clause to the element
that states it, and writes two deterministic LF artifacts. It accepts nothing,
publishes nothing, activates nothing, retires nothing and touches no database.

Membership has no tag to read
-----------------------------
The five accepted batches were tagged classes: ``[Condition]``, ``[Hazard]``,
``[Action]``, ``[Attitude]``, ``[Area of Effect]``, each plus its untagged
umbrella. **Cover has no tag.** What the source prints is two entry containers
it labels ``Cover`` — one under *Rules Glossary > Rules Definitions* (page index
178) and one under *Playing the Game > Combat* (page index 14) — and a printed
*See also* citation in the first that names the chapter and subsection of the
second. So membership here is a structural claim and this run states it as one:
exactly two such containers exist, one beneath ``Rules Definitions`` and one
beneath ``Combat``, and the glossary entry's own last two leaves are a bare
``See also`` and the citation that names the other site. A release in which that
structure moved fails this run rather than being silently re-cut.

Printing the word is use, not definition. Thirty other leaves in the bound
release contain ``Cover`` — spells, class features, magic items, monster stat
blocks, ``Making an Attack``, ``Targets``, ``Blindsight``, ``Hide [Action]`` and
the ``Area of Effect`` entry that already cites it in accepted authority. Each
uses Cover while stating some *other* rule, or restates a Cover rule from
outside a Cover entry: ``Targets`` (leaf
``7322a0d0-afaf-5df9-97f6-a0e428c81097``) states the spell-targeting rule that a
caster needs a clear path, so the target cannot be behind Total Cover.
Membership here is the reviewed structural rule — the container labelled
``Cover`` — so those leaves stay outside this reviewed population. The exclusion
is re-derived here and checked against the reviewed manifest rather than
asserted.

One composite record, two printed sites
---------------------------------------
``glossary.cover`` is **one** record assembled from both sites — the first
record in this build whose authority is drawn from two chapters. That is
#137 contract 3's composite case and ADR-005d Decision 3's "records are
assembled from a committed accepted inventory" read literally: a 5c ``ENTRY`` is
structural evidence, not universal semantic authority, and two entries can state
one mechanical entity.

**Four rules are printed at both sites** — the three degree benefits and the
most-protective/no-adding rule. They are represented **once each**, with
``PRIMARY`` provenance from *both* sites' spans, because that is what the source
did: it printed one rule twice. Provenance is per span, so several spans
claiming one target is the ordinary shape, not a workaround. No validator forces
this: ``validation.py:159`` rejects two equal-keyed facts inside one component,
and ``_validate_duplicated_fact_authority`` (``validation.py:652``) rejects
sibling components holding an equivalent fact drawn from the *same* substantive
span, so two components each holding a copy taken from the two *distinct*
printings would pass both. One fact is chosen because both sites state one rule,
and publishing two copies would be two claims where the source made one. Where
the second printing *defers* rather
than states ("As detailed in the Cover table") it is supporting authority linked
to what it defers to, and that asymmetry is deliberate.

The three-degree closure statement — *"There are three degrees of cover, each of
which provides a different benefit to a target:"* — is about no single fact, so
it claims the ``degree_benefit`` **component as a whole**, ``PRIMARY``. That
carrier is precedent, not invention: the frozen prior already holds 19
``component/primary`` claims.

Where the inventory comes from, and why it is not retyped here
--------------------------------------------------------------
Leaf ids, half-open ``[char_start, char_end)`` extents and clause text are read
out of ``issue-5d-cover-1-source-manifest.json`` rather than re-authored here.
That manifest is itself a product of the source, so this run closes the loop:

* the manifest's digest is pinned here and checked before anything is read;
* every manifest leaf id must exist in the *live* bound corpus, and its content
  must be byte-identical to what the pipeline just extracted from the PDF;
* the manifest's clause extents must partition each of the sixteen bound leaves
  end to end — no gap, no overlap, starting at 0 and stopping at the leaf's
  length — and the concatenation must reconstruct the leaf byte for byte.

Expected obligations, and what they are derived from
----------------------------------------------------
``EXPECTED_OBLIGATIONS`` is one literal row per printed clause, typed from the
**reviewed source record** — §3 of the discovery checkpoint for the 5c
disposition, §4's gap table for the gap ids and its witness lists, §4a for the
shared-provenance disposition. It is deliberately *not* computed from anything
this file emits, and the manifest carries no disposition at all, so this table is
the only place the review's judgment enters. The emission is then checked three
ways: **omission** (every one of the twenty-eight discharged), **duplication**
(by exactly one span, at exactly the manifest's extent) and **semantic loss**
(carried by exactly the element the review names — the record, a named typed
fact claimed PRIMARY, a named component claimed PRIMARY, or a supporting clause
claimed CONTEXTUAL on a named component or fact).

Schema
------
**Representation schema 10**, five fact families over eight new closed
vocabularies plus **one member added to an accepted one**: ``CoverDegree``
carried ``THREE_QUARTERS`` and ``TOTAL`` from schema 6 and gains ``HALF`` here,
which is by itself enough to move the schema hash. Schema 9 could already
*consume* a degree of cover — ``Applicability.cover`` and
``BlockedLineExclusionFact.blocking_cover`` both read one — and could not
*define* what a degree is.

The crossing is the registered transition ``5d-lift-schema-9-to-10``, exercised
below against the frozen accepted five-batch prior.

Reference resolution, standalone and combined
----------------------------------------------
This batch emits **zero references**. The population prints exactly one
citation, ``glossary/3/0`` = *"Playing the Game" ("Combat").*, and it names a
**chapter**, not a record; every one of the prior's 53 references targets a
record key and there is no record for a chapter. It is also this record's own
second site, so a reference would be self-directed even if a target existed. No
``scope_key`` decision arises for this batch at all.

So standalone this batch produces **zero findings**. Merged with the lifted
five-batch prior it produces **two** — ``glossary.concentration`` and
``glossary.speed`` — down from the prior's three, because the umbrella's
See-also citation of ``glossary.cover`` now has a target. **That resolution is a
property of the merged candidate this run builds in memory.** Current accepted
authority is unchanged and still carries three unresolved targets; nothing here
is accepted, and the resolution becomes a property of accepted authority only at
an acceptance that has not happened.

What this run is, and is not
----------------------------
* It is *proposal preparation*. It is material for semantic review.
* Nothing here is accepted, activated, published or retired. ``accept_proposal``
  is never called and the publication gate is not executed — there is no
  persisted projection to run it over.
* The accepted five-batch prior is read **only** as a frozen review prior, by
  content identity, and asserted unchanged afterwards. The live oracle is read as
  a mutation sentinel and is never an input.
* No geometry is computed. Measuring how much of a target an obstacle covers,
  deciding which side an effect originated on, and choosing a degree for a scene
  all stay outside; the excluded work is the computation, not the subject matter.
* One record of the corpus #137 governs. The full-corpus obligation is untouched
  and undischarged.
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
#: review: conditions-1, hazards-1, actions-1, attitudes-1 and
#: areas-of-effect-1, representation schema 9. Read only, by content identity,
#: and asserted unchanged at the end.
REVIEW_PRIOR_PATH = (
    REPO
    / "tests/ingestion/mechanical/data"
    / (
        "accepted_prior_conditions_1_hazards_1_actions_1"
        "_attitudes_1_areas_of_effect_1.json"
    )
)

#: **The reviewed clause inventory.** Discovery output, committed, and pinned by
#: digest below: coordinates only, no disposition.
MANIFEST_PATH = OUT / "issue-5d-cover-1-source-manifest.json"

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
REVIEW_PRIOR_CONTENT_SHA256 = "9f3802514298f519120680db4a9a20805f5dcb8a4b00dd8686ed6faddec1e738"  # noqa: E501  # pragma: allowlist secret
REVIEW_PRIOR_BLOB = (
    "467fcc62c8fb64e54cf74e73a6f55c384129eef7"  # pragma: allowlist secret
)
#: The identity the Owner accepted, at the scope it holds: the frozen file on
#: disk. The lifted copy's identity is a different value at a different scope
#: and is computed and reported below rather than pinned here.
REVIEW_PRIOR_IDENTITY = "8e08ac48f2a57a4498557990a07270f9abd855b246c1039da68cc9ec82d44b40"  # noqa: E501  # pragma: allowlist secret
REVIEW_PRIOR_BATCH_IDS = [
    "actions-1",
    "areas-of-effect-1",
    "attitudes-1",
    "conditions-1",
    "hazards-1",
]
REVIEW_PRIOR_SCHEMA_VERSION = "5d-representation-schema-9"
REVIEW_PRIOR_SCHEMA_HASH = "f5a5e30817e64f019e31aa7f4692d72611215e4294e7da36242e492bca6b336e"  # noqa: E501  # pragma: allowlist secret
#: What the five accepted batches hold together, named collection by collection
#: so one that silently gained or lost an element fails by name, not by total.
REVIEW_PRIOR_COLLECTIONS = {
    "records": 46,
    "components": 132,
    "prose_bindings": 49,
    "relationships": 0,
    "references": 53,
    "provenance": 547,
}
REVIEW_PRIOR_SPANS = 530
REVIEW_PRIOR_OBLIGATIONS = 46
#: Each accepted batch keeps the hash it was reviewed under. Schema 10 does not
#: restamp five batches as one, and the crossing is asserted to carry these
#: across by identity rather than re-derive them.
REVIEW_PRIOR_ANCHORS = {
    "conditions-1": "5d-representation-schema-3",
    "hazards-1": "5d-representation-schema-5",
    "actions-1": "5d-representation-schema-7",
    "attitudes-1": "5d-representation-schema-8",
    "areas-of-effect-1": "5d-representation-schema-9",
}

#: The reviewed inventory, pinned. Checked before the file is parsed, so a
#: manifest edited after review cannot enter this proposal unnoticed.
MANIFEST_SHA256 = "f82163ee2fc6b6c1805974e6e7404eca45fd6b48452a64a91f9e6a4f0e0cdcad"  # noqa: E501  # pragma: allowlist secret

# --- Retained-evidence guard ------------------------------------------------
# Every artifact of the accepted batches and of this batch's discovery records
# authority or the review this run derives its brief from. Refuse to run if
# this file would overwrite one, and assert afterwards that none of them moved.
PROPOSAL_FILE = "issue-5d-batch-cover-1-PROPOSAL.json"
AUDIT_FILE = "issue-5d-batch-cover-1-audit.json"
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
    REPRESENTATION_SCHEMA_VERSION,
    AbilityScore,
    BenefitOriginSide,
    ComponentDraft,
    CoverageThreshold,
    CoverBenefitOriginFact,
    CoverDefense,
    CoverDefensiveBonusFact,
    CoverDegree,
    CoverDegreeCombination,
    CoverDegreeSelection,
    CoverDegreeSelectionFact,
    CoveredInteraction,
    CoverOfferor,
    CoverProvisionFact,
    CoverTargetingProhibitionFact,
    FactFamily,
    MechanicalFact,
    ProvenanceClaim,
    ProvenanceRole,
    ProvenanceTargetKind,
    RecordDraft,
    RecordKind,
    RepresentationDraft,
    TargetingProhibition,
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

#: **Schema 10's exact declared pin.** Asserted against the value the schema
#: computes at this head, so a payload edit that moved the hash fails here
#: rather than minting a proposal under a contract nobody reviewed.
SCHEMA = (REPRESENTATION_SCHEMA_VERSION, representation_schema_hash())
assert SCHEMA[0] == "5d-representation-schema-10", SCHEMA
assert SCHEMA[1] == (
    "c39e3a35e197a1d1db5c2c2b3445ff0cbf03395c91e3426353a4bce589be4be0"  # noqa: E501  # pragma: allowlist secret
), SCHEMA

# ---------------------------------------------------------------------------
# Bound release - derived from the committed PDF, asserted against production
# ---------------------------------------------------------------------------

PACKAGE_UUID = "4458fa10-4a66-5e0e-9ecc-ea37530ad2b4"
RELEASE_VERSION = "5.2.1-corpus.36b786d8-fa2"
SOURCE_SHA256 = "8974902d109d6e63672d7c490bde9ccf052410503d9cfa768237154fbc5e3d87"  # noqa: E501  # pragma: allowlist secret
TRANSFORM_CONFIG_HASH = "77720c2f3b8c9b88363d48050466fb8e3a26f8476b63145d1b5928ff2581ef3e"  # noqa: E501  # pragma: allowlist secret
BUNDLE_ROOT_HASH = "03353dfb79790aee7260b9ed96055b7296cd6f70e3e6f97d6cbe0a2484279685"  # noqa: E501  # pragma: allowlist secret

#: The only binding value not rederived from the PDF here: it is a function of
#: the persisted `rp_sources` rows and the read-back vector state, so recomputing
#: it needs a session over that persisted state
#: (`persistence.recompute_persisted_digest`), which this generator does not open.
#: No publish is required to recompute or verify it. Taken from the published CRD
#: Issue 5c release record and disclosed as such.
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
#
# `release_binding_payload` is the canonical payload of `ReleaseBinding` and is
# what every downstream identity is computed over, so the six parts are read
# back through it rather than out of six local names. Five are re-derived from
# the committed PDF by the 5c pipeline in this process; the sixth is disclosed.
# `validate_candidate` is the repository's own authoritative seam for binding
# agreement — it is executed further below, over the merged candidate, and the
# binding-class subset of its findings is asserted empty there.
BINDING_PARTS = release_binding_payload(BINDING)
BINDING_REDERIVED_HERE = {
    "package_uuid": CAND.package_uuid,
    "release_version": CAND.release_version,
    "authoritative_source_hash": CAND.authoritative_source_hash,
    "transform_config_hash": CAND.transform_config_hash,
    "bundle_root_hash": CAND.bundle.bundle_root_hash,
}
BINDING_DISCLOSED = {"persisted_corpus_digest": PERSISTED_CORPUS_DIGEST}
assert sorted(BINDING_PARTS) == sorted(
    {**BINDING_REDERIVED_HERE, **BINDING_DISCLOSED}
), sorted(BINDING_PARTS)
assert len(BINDING_PARTS) == 6, BINDING_PARTS
assert BINDING_PARTS == {**BINDING_REDERIVED_HERE, **BINDING_DISCLOSED}, BINDING_PARTS
#: And the pinned expectations, so a pipeline that silently produced a different
#: release fails here rather than binding this proposal to it.
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

# --- Membership, re-derived from the source's own containers ----------------
# There is no tag. The structural claim is asserted, not assumed: exactly two
# entry containers labeled `Cover`, one beneath `Rules Definitions` and one
# beneath `Combat`, and the glossary entry's own last two leaves are a bare
# `See also` and the citation that names the other site's chapter and section.
COVER_ENTRIES = sorted(
    (
        c
        for c in LEDGER_OBJ.containers
        if c.container_type == "entry" and c.label == "Cover"
    ),
    key=lambda c: min(lf.page_index for lf in by_container[c.container_id]),
)
assert len(COVER_ENTRIES) == 2, [c.container_id for c in COVER_ENTRIES]
COMBAT_ENTRY, GLOSSARY_ENTRY = COVER_ENTRIES
assert "Combat" in _path_of(COMBAT_ENTRY.container_id), _path_of(
    COMBAT_ENTRY.container_id
)
assert "Rules Definitions" in _path_of(GLOSSARY_ENTRY.container_id), _path_of(
    GLOSSARY_ENTRY.container_id
)
SITES = (("glossary", GLOSSARY_ENTRY.container_id), ("combat", COMBAT_ENTRY.container_id))
SITE_OF_CONTAINER = {cid: site for site, cid in SITES}

_glossary_site_leaves = [
    lf for lf in by_container[GLOSSARY_ENTRY.container_id] if lf.leaf_id in REPRESENTED
]
assert _glossary_site_leaves[-2].content == "See also", _glossary_site_leaves[-2].content
_CITATION_TEXT = _glossary_site_leaves[-1].content
assert LABELS[_ancestry(COMBAT_ENTRY.container_id)[1]] in _CITATION_TEXT, _CITATION_TEXT
assert LABELS[_ancestry(COMBAT_ENTRY.container_id)[2]] in _CITATION_TEXT, _CITATION_TEXT
DIRECTION = {
    "from_site": "glossary",
    "see_also_leaf_id": _glossary_site_leaves[-2].leaf_id,
    "citation_leaf_id": _glossary_site_leaves[-1].leaf_id,
    "citation_text": _CITATION_TEXT,
    "names_section": LABELS[_ancestry(COMBAT_ENTRY.container_id)[2]],
    "names_subsection": LABELS[_ancestry(COMBAT_ENTRY.container_id)[1]],
    "to_site": "combat",
    "note": (
        "the two sites are one population because the source joins them, not "
        "because a reader judges them related. This is the printed join, "
        "re-derived rather than recalled."
    ),
}

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

#: The one record. Settled in the checkpoint on evidence rather than taste:
#: accepted authority already cites `glossary.cover` by name, the three degrees
#: are untagged table rows with no entry of their own, and `CoverDegree` is
#: already consumed as a vocabulary by two accepted facts - so a degree is a
#: member, not a record.
COVER = "glossary.cover"
RECORDS_IN_ORDER = (COVER,)
RECORD_KIND = {COVER: RecordKind.GLOSSARY_RULE}

# ---------------------------------------------------------------------------
# The reviewed inventory, read rather than retyped — then re-proved
# ---------------------------------------------------------------------------

_manifest_raw = MANIFEST_PATH.read_bytes()
_manifest_canonical = _manifest_raw.replace(b"\r\n", b"\n")
MANIFEST_DIGEST = hashlib.sha256(_manifest_canonical).hexdigest()
assert MANIFEST_DIGEST == MANIFEST_SHA256, MANIFEST_DIGEST
MANIFEST = json.loads(_manifest_canonical.decode("utf-8"))
assert MANIFEST["artifact_kind"] == "source_discovery_manifest", MANIFEST[
    "artifact_kind"
]
assert MANIFEST["batch_id"] == "cover-1", MANIFEST["batch_id"]
#: The manifest carries coordinates, never dispositions, and never a candidate
#: record key. Asserted, because the obligation table below is only independent
#: evidence if the manifest is not quietly carrying the same judgment.
assert not any(
    "disposition" in row for row in MANIFEST["clauses"]
), "the manifest must not carry dispositions"
assert "records" not in MANIFEST, "the manifest must not carry a record assignment"

#: `clause_id -> the manifest's clause row`, in printed order.
CLAUSE = {row["clause_id"]: row for row in MANIFEST["clauses"]}
CLAUSE_ORDER = tuple(row["clause_id"] for row in MANIFEST["clauses"])
assert len(CLAUSE) == len(CLAUSE_ORDER) == 28, len(CLAUSE_ORDER)

#: The manifest's own leaf table, and the tie to the live bound corpus: every
#: reviewed leaf must still exist and still hold byte-identical content.
MANIFEST_LEAVES: dict[str, str] = {}
LEAF_SITE: dict[str, str] = {}
for _site in MANIFEST["source_sites"]:
    assert _site["site"] in {s for s, _ in SITES}, _site["site"]
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
BOUNDARY_LEAVES = {
    leaf.leaf_id for _, cid in SITES for leaf in by_container[cid]
}
assert BOUNDARY_LEAVES == set(MANIFEST_LEAVES), sorted(
    BOUNDARY_LEAVES ^ set(MANIFEST_LEAVES)
)
assert BOUNDARY_LEAVES <= REPRESENTED, "a boundary leaf is policy-excluded"

#: **The exclusion, re-derived rather than transcribed.** Every other leaf in the
#: bound release whose content contains `Cover`. Membership is attachment to a
#: container labeled `Cover`; printing the word is use. Re-derived here and
#: checked against the reviewed manifest's own enumeration, so a boundary that
#: moved upstream fails rather than going stale in a document.
BOUNDARY_REDERIVED = sorted(
    leaf.leaf_id
    for leaf in LEDGER_OBJ.leaves
    if "Cover" in leaf.content and leaf.leaf_id not in BOUNDARY_LEAVES
)
BOUNDARY_IN_MANIFEST = sorted(row["leaf_id"] for row in MANIFEST["boundary"])
assert BOUNDARY_REDERIVED == BOUNDARY_IN_MANIFEST, sorted(
    set(BOUNDARY_REDERIVED) ^ set(BOUNDARY_IN_MANIFEST)
)
assert len(BOUNDARY_REDERIVED) == MANIFEST["boundary_count"] == 30, len(
    BOUNDARY_REDERIVED
)
for _row in MANIFEST["boundary"]:
    assert LABELS[LEAF_BY_ID[_row["leaf_id"]].container_path[-1]] != "Cover", _row
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
# The sixteen substantive clauses, as four components and eight facts
# ---------------------------------------------------------------------------
#
# The table prints two columns of rule — what each degree *does* and what
# *offers* it — and the prose prints two more rules that qualify every degree.
# That is the grouping: one component per column, one per qualifying rule, and a
# fact per degree inside the two that have one. Grouping the degrees rather than
# giving each its own component is what lets the sentence stating the
# vocabulary's closure — "there are three degrees of cover" — claim a component
# as a whole, which is the carrier the schema has for a statement about no
# single fact.
#
# No coordinate, unit, grid semantic or measurement appears anywhere.
# `CoverageThreshold` names the printed threshold; measuring how much of a
# target an obstacle actually covers is runtime computation and is outside 5d.

BENEFIT = "degree_benefit"
PROVISION = "degree_provision"
ORIGIN = "benefit_origin"
SELECTION = "degree_selection"
COMPONENTS_IN_ORDER = (BENEFIT, PROVISION, ORIGIN, SELECTION)

#: `label -> (component, fact)`. The label is a **typed** handle: the obligation
#: table below names a carrier by label, and the emission's carrier is read back
#: off the emitted claim and mapped through this same table, so a clause that
#: ended up on the wrong fact of the right component still fails.
FACTS: dict[str, tuple[str, MechanicalFact]] = {
    "half_benefit": (
        BENEFIT,
        CoverDefensiveBonusFact(
            degree=CoverDegree.HALF,
            bonus=2,
            to_defense=CoverDefense.ARMOR_CLASS,
            to_saving_throw=AbilityScore.DEXTERITY,
        ),
    ),
    "three_quarters_benefit": (
        BENEFIT,
        CoverDefensiveBonusFact(
            degree=CoverDegree.THREE_QUARTERS,
            bonus=5,
            to_defense=CoverDefense.ARMOR_CLASS,
            to_saving_throw=AbilityScore.DEXTERITY,
        ),
    ),
    # Total Cover's benefit is a prohibition, not a bonus. A shape that forced it
    # into the bonus family would have to invent a number for it.
    "total_prohibition": (
        BENEFIT,
        CoverTargetingProhibitionFact(
            degree=CoverDegree.TOTAL,
            prohibits=TargetingProhibition.DIRECT_TARGETING,
        ),
    ),
    # The printed asymmetry is the rule: Half admits a creature OR an object,
    # the other two admit an object only.
    "half_provision": (
        PROVISION,
        CoverProvisionFact(
            degree=CoverDegree.HALF,
            offered_by=CoverOfferor.ANOTHER_CREATURE_OR_AN_OBJECT,
            coverage=CoverageThreshold.AT_LEAST_HALF,
        ),
    ),
    "three_quarters_provision": (
        PROVISION,
        CoverProvisionFact(
            degree=CoverDegree.THREE_QUARTERS,
            offered_by=CoverOfferor.AN_OBJECT,
            coverage=CoverageThreshold.AT_LEAST_THREE_QUARTERS,
        ),
    ),
    "total_provision": (
        PROVISION,
        CoverProvisionFact(
            degree=CoverDegree.TOTAL,
            offered_by=CoverOfferor.AN_OBJECT,
            coverage=CoverageThreshold.WHOLE_TARGET,
        ),
    ),
    # Printed at one site only, and it is a precondition on the benefit rather
    # than a property of any degree.
    "opposite_side": (
        ORIGIN,
        CoverBenefitOriginFact(
            interaction=CoveredInteraction.AN_ATTACK_OR_OTHER_EFFECT,
            requires_origin=BenefitOriginSide.OPPOSITE_SIDE_OF_THE_COVER,
        ),
    ),
    # One rule, stated positively at the glossary and negatively in Combat. No
    # rank over the three degrees is printed, recorded or implied.
    "most_protective": (
        SELECTION,
        CoverDegreeSelectionFact(
            selects=CoverDegreeSelection.MOST_PROTECTIVE,
            combination=CoverDegreeCombination.NOT_ADDED_TOGETHER,
        ),
    ),
}

#: `label -> the clause ids that state it`, in printed order. Four labels name
#: **two** clauses from **two different sites**: that is the shared provenance
#: §4a settles, one fact claimed PRIMARY from both printings.
COMPOSITION: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("half_benefit", ("glossary/1/2", "combat/6/0")),
    ("three_quarters_benefit", ("glossary/1/3", "combat/8/0")),
    ("total_prohibition", ("glossary/1/4", "combat/11/0")),
    ("half_provision", ("combat/5/0", "combat/6/1")),
    ("three_quarters_provision", ("combat/7/0", "combat/9/0")),
    ("total_provision", ("combat/10/0", "combat/11/1")),
    ("opposite_side", ("combat/1/2",)),
    ("most_protective", ("glossary/1/5", "combat/1/3")),
)
assert sorted(label for label, _ in COMPOSITION) == sorted(FACTS), COMPOSITION

#: The closure statement. It is about the component as a whole — no single fact
#: is "there are three degrees" — so it claims the component, PRIMARY. The
#: frozen prior already holds 19 component/PRIMARY claims, so the carrier is
#: precedent rather than invention.
CLOSURE_CLAUSE = "glossary/1/1"

FACTS_BY_COMPONENT: dict[str, tuple[MechanicalFact, ...]] = {
    component: tuple(
        FACTS[label][1] for label, _ in COMPOSITION if FACTS[label][0] == component
    )
    for component in COMPONENTS_IN_ORDER
}
assert {k: len(v) for k, v in FACTS_BY_COMPONENT.items()} == {
    BENEFIT: 3,
    PROVISION: 3,
    ORIGIN: 1,
    SELECTION: 1,
}, {k: len(v) for k, v in FACTS_BY_COMPONENT.items()}

FACT_OF_LABEL = {label: fact for label, (_, fact) in FACTS.items()}
COMPONENT_OF_LABEL = {label: component for label, (component, _) in FACTS.items()}
#: Reverse map used to read a carrier back off an emitted claim. Fact keys are
#: content-derived, so this is keyed by what the schema itself computes.
LABEL_OF_FACT_KEY = {
    fact_key(fact): label for label, (_, fact) in FACTS.items()
}
assert len(LABEL_OF_FACT_KEY) == len(FACTS), "two facts share a fact key"

# ---------------------------------------------------------------------------
# The twelve supporting clauses, each linked to what it actually supports
# ---------------------------------------------------------------------------

#: Supporting clauses the *record* carries: both headings, the glossary's
#: framing sentence, the See-also label and its chapter citation, Combat's
#: framing sentence, the table caption, and the `Degree` column header — which
#: names the vocabulary the component already closes rather than qualifying any
#: one column of rule.
RECORD_CONTEXT: tuple[str, ...] = (
    "glossary/0/0",
    "glossary/1/0",
    "glossary/2/0",
    "glossary/3/0",
    "combat/0/0",
    "combat/1/0",
    "combat/1/5",
    "combat/2/0",
)

#: Supporting clauses a *component* carries, because they bound that whole
#: column of rule and no single fact in it. `combat/1/1` defers to the table
#: rather than stating a rule ("As detailed in the Cover table"); `combat/3/0`
#: and `combat/4/0` are the two column headers that name what each column holds.
COMPONENT_CONTEXT: tuple[tuple[str, str], ...] = (
    (BENEFIT, "combat/1/1"),
    (BENEFIT, "combat/3/0"),
    (PROVISION, "combat/4/0"),
)

#: A supporting clause a *fact* carries, because it bounds that fact and nothing
#: else: the worked example illustrates the most-protective rule and states no
#: rule of its own, which is why it is contextual rather than a second fact with
#: an invented ranking in it.
FACT_CONTEXT: tuple[tuple[str, str], ...] = (("most_protective", "combat/1/4"),)

# ---------------------------------------------------------------------------
# Expected obligations — typed from the reviewed source, not from the emission
# ---------------------------------------------------------------------------
#
# One row per printed clause. The disposition column is §3 of the discovery
# checkpoint; the carrier column is §4a's shared-provenance disposition and
# §4c's one-record finding; the gap column is §4's witness lists, transcribed
# from that table rather than inferred. Nothing here is computed from the
# composition above, and the manifest carries no disposition, so this is the
# independent statement of what the proposal owes the source.
#
# Carrier shapes:
#   ("record", record)                          supporting authority, record-owned
#   ("component", record, component)            substantive, claimed PRIMARY on a
#                                               whole component
#   ("component_context", record, component)    supporting authority bounding one
#                                               whole component
#   ("fact", record, component, family, label)  substantive, claimed PRIMARY
#   ("fact_context", record, component, label)  supporting authority bounding one
#                                               fact

SUB = "substantive"
SUP = "supporting_authority"
F_BONUS = FactFamily.COVER_DEFENSIVE_BONUS.value
F_PROHIB = FactFamily.COVER_TARGETING_PROHIBITION.value
F_PROV = FactFamily.COVER_PROVISION.value
F_ORIGIN = FactFamily.COVER_BENEFIT_ORIGIN.value
F_SELECT = FactFamily.COVER_DEGREE_SELECTION.value

EXPECTED_OBLIGATIONS: tuple[
    tuple[str, str, tuple[object, ...], tuple[str, ...]], ...
] = (
    # --- glossary site: Rules Glossary > Rules Definitions > Cover, p179 -----
    ("glossary/0/0", SUP, ("record", COVER), ()),
    ("glossary/1/0", SUP, ("record", COVER), ()),
    # The closure statement. G1's "represented distinction" column names this
    # clause as the one that states the three-member vocabulary outright.
    ("glossary/1/1", SUB, ("component", COVER, BENEFIT), ("G1",)),
    (
        "glossary/1/2",
        SUB,
        ("fact", COVER, BENEFIT, F_BONUS, "half_benefit"),
        ("G1", "G2"),
    ),
    (
        "glossary/1/3",
        SUB,
        ("fact", COVER, BENEFIT, F_BONUS, "three_quarters_benefit"),
        ("G2",),
    ),
    (
        "glossary/1/4",
        SUB,
        ("fact", COVER, BENEFIT, F_PROHIB, "total_prohibition"),
        ("G3",),
    ),
    (
        "glossary/1/5",
        SUB,
        ("fact", COVER, SELECTION, F_SELECT, "most_protective"),
        ("G6",),
    ),
    ("glossary/2/0", SUP, ("record", COVER), ()),
    ("glossary/3/0", SUP, ("record", COVER), ()),
    # --- combat site: Playing the Game > Combat > Cover, p15 -----------------
    ("combat/0/0", SUP, ("record", COVER), ()),
    ("combat/1/0", SUP, ("record", COVER), ()),
    ("combat/1/1", SUP, ("component_context", COVER, BENEFIT), ()),
    (
        "combat/1/2",
        SUB,
        ("fact", COVER, ORIGIN, F_ORIGIN, "opposite_side"),
        ("G5",),
    ),
    (
        "combat/1/3",
        SUB,
        ("fact", COVER, SELECTION, F_SELECT, "most_protective"),
        ("G6",),
    ),
    ("combat/1/4", SUP, ("fact_context", COVER, SELECTION, "most_protective"), ()),
    ("combat/1/5", SUP, ("record", COVER), ()),
    ("combat/2/0", SUP, ("record", COVER), ()),
    ("combat/3/0", SUP, ("component_context", COVER, BENEFIT), ()),
    ("combat/4/0", SUP, ("component_context", COVER, PROVISION), ()),
    ("combat/5/0", SUB, ("fact", COVER, PROVISION, F_PROV, "half_provision"), ("G1",)),
    ("combat/6/0", SUB, ("fact", COVER, BENEFIT, F_BONUS, "half_benefit"), ("G2",)),
    (
        "combat/6/1",
        SUB,
        ("fact", COVER, PROVISION, F_PROV, "half_provision"),
        ("G4",),
    ),
    (
        "combat/7/0",
        SUB,
        ("fact", COVER, PROVISION, F_PROV, "three_quarters_provision"),
        (),
    ),
    (
        "combat/8/0",
        SUB,
        ("fact", COVER, BENEFIT, F_BONUS, "three_quarters_benefit"),
        ("G2",),
    ),
    (
        "combat/9/0",
        SUB,
        ("fact", COVER, PROVISION, F_PROV, "three_quarters_provision"),
        ("G4",),
    ),
    ("combat/10/0", SUB, ("fact", COVER, PROVISION, F_PROV, "total_provision"), ()),
    (
        "combat/11/0",
        SUB,
        ("fact", COVER, BENEFIT, F_PROHIB, "total_prohibition"),
        ("G3",),
    ),
    (
        "combat/11/1",
        SUB,
        ("fact", COVER, PROVISION, F_PROV, "total_provision"),
        ("G4",),
    ),
)

#: What each substantive obligation must *state*, in the words the review used.
#: Not machine-checked — a reviewer reads this beside the fact payload — but
#: keyed to the clause id so it cannot drift onto a different clause.
OBLIGATION_TEXT = {
    "glossary/1/1": (
        "the printed vocabulary is CLOSED AT THREE members, stated outright "
        "and about no single fact"
    ),
    "glossary/1/2": "Half Cover grants +2 to AC AND to Dexterity saving throws",
    "glossary/1/3": (
        "Three-Quarters Cover grants +5 to AC AND to Dexterity saving throws"
    ),
    "glossary/1/4": (
        "Total Cover's benefit is categorically different: not a bonus at all, "
        "but that the target can't be targeted DIRECTLY"
    ),
    "glossary/1/5": (
        "behind more than one degree, a target benefits only from the MOST "
        "PROTECTIVE degree"
    ),
    "combat/1/2": (
        "cover benefits a target ONLY when the attack or other effect "
        "originates on the OPPOSITE SIDE of the cover"
    ),
    "combat/1/3": (
        "the same selection rule, stated negatively: only the most protective "
        "degree applies and the degrees AREN'T ADDED TOGETHER"
    ),
    "combat/5/0": "the Half degree row: the table's key for this provision",
    "combat/6/0": (
        "the Cover table's Benefit column for Half, the same +2 to AC and "
        "Dexterity saving throws the glossary prints"
    ),
    "combat/6/1": (
        "Half Cover is offered by ANOTHER CREATURE OR AN OBJECT covering AT "
        "LEAST HALF of the target - the only clause admitting a creature"
    ),
    "combat/7/0": (
        "the Three-Quarters degree row, carried verbatim as the release "
        "extracts it ('ThreeQuarters')"
    ),
    "combat/8/0": (
        "the Cover table's Benefit column for Three-Quarters, the same +5 the "
        "glossary prints"
    ),
    "combat/9/0": (
        "Three-Quarters Cover is offered by AN OBJECT covering AT LEAST "
        "THREE-QUARTERS of the target"
    ),
    "combat/10/0": "the Total degree row: the table's key for this provision",
    "combat/11/0": (
        "the Cover table's Benefit column for Total, the same direct-targeting "
        "prohibition the glossary prints"
    ),
    "combat/11/1": (
        "Total Cover is offered by AN OBJECT covering THE WHOLE target - its "
        "own printed phrase, not 'at least the whole'"
    ),
}

# --- The obligation ledger, checked against the reviewed inventory ----------
EXPECTED = {row[0]: row for row in EXPECTED_OBLIGATIONS}
assert len(EXPECTED) == len(EXPECTED_OBLIGATIONS), "an obligation is listed twice"
#: Every printed clause is an obligation, and no obligation names a clause the
#: reviewed inventory does not print.
assert set(EXPECTED) == set(CLAUSE), sorted(set(EXPECTED) ^ set(CLAUSE))
_expected_dispositions: dict[str, int] = defaultdict(int)
for _row in EXPECTED_OBLIGATIONS:
    _expected_dispositions[_row[1]] += 1
assert dict(_expected_dispositions) == {SUP: 12, SUB: 16}, dict(_expected_dispositions)
assert sorted(OBLIGATION_TEXT) == sorted(
    cid for cid, disp, _, _ in EXPECTED_OBLIGATIONS if disp == SUB
), "every substantive obligation states what it owes"
#: The six gaps §4 found, each still witnessed by at least one clause.
GAPS_WITNESSED = sorted({g for _, _, _, gaps in EXPECTED_OBLIGATIONS for g in gaps})
assert GAPS_WITNESSED == ["G1", "G2", "G3", "G4", "G5", "G6"], GAPS_WITNESSED
#: And the independent cross-check: the reviewed table's own witness lists.
#: Transcribed from §4 and compared with what the obligation rows say, so a gap
#: that quietly moved witnesses fails here.
CHECKPOINT_GAP_WITNESSES = {
    "G1": ("glossary/1/2", "combat/5/0"),
    "G2": ("glossary/1/2", "glossary/1/3", "combat/6/0", "combat/8/0"),
    "G3": ("glossary/1/4", "combat/11/0"),
    "G4": ("combat/6/1", "combat/9/0", "combat/11/1"),
    "G5": ("combat/1/2",),
    "G6": ("glossary/1/5", "combat/1/3"),
}
_derived_witnesses: dict[str, list[str]] = defaultdict(list)
for _cid, _, _, _gaps in EXPECTED_OBLIGATIONS:
    for _g in _gaps:
        _derived_witnesses[_g].append(_cid)
#: `glossary/1/1` is the one addition and it is stated, not smuggled: §4's G1 row
#: names it in the "represented distinction" column as the clause that states the
#: three-member closure outright, while its "witnesses" column lists the two
#: clauses that need the new member. Both readings are kept.
assert {
    g: tuple(sorted(set(v) - {CLOSURE_CLAUSE})) for g, v in _derived_witnesses.items()
} == {g: tuple(sorted(v)) for g, v in CHECKPOINT_GAP_WITNESSES.items()}, dict(
    _derived_witnesses
)

# ---------------------------------------------------------------------------
# Emission
# ---------------------------------------------------------------------------

ORIGIN_LABEL = "issue-5d-batch-cover-1-generator.py"

DISPOSITION_OF = {
    SUB: SemanticDisposition.SUBSTANTIVE,
    SUP: SemanticDisposition.SUPPORTING_AUTHORITY,
}
RATIONALE = {
    "record": (
        "identifies, frames, or defines the mechanic; preserved as supporting "
        "authority owned by the record rather than discarded"
    ),
    "component": (
        "states something true of a whole column of rule and of no single fact "
        "in it, so it is claimed PRIMARY on the component; the schema's carrier "
        "for a substantive statement that is about no one fact"
    ),
    "component_context": (
        "bounds or defers to a whole component and states no rule of its own; "
        "supporting authority claimed CONTEXTUAL by that component, so the link "
        "a reviewer needs is in the provenance instead of in prose"
    ),
    "fact": (
        "states a mechanic the closed typed union carries exactly, with every "
        "qualifier that narrows or multiplies it carried by a structure of this "
        "schema rather than left implicit; where the source prints the same rule "
        "twice, both printings claim the one fact PRIMARY"
    ),
    "fact_context": (
        "bounds exactly one typed fact and states no rule of its own; supporting "
        "authority claimed CONTEXTUAL by that fact rather than by the record"
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
    proposed.append(
        ProposedSpan(span=span, origin=ORIGIN_LABEL, rationale=RATIONALE[kind])
    )

    if kind == "record":
        record_key = str(carrier[1])
        claim = ProvenanceClaim(
            ProvenanceTargetKind.RECORD, (record_key,), sid, ProvenanceRole.CONTEXTUAL
        )
        claimant = record_key
    elif kind in {"component", "component_context"}:
        record_key, component_key = str(carrier[1]), str(carrier[2])
        claim = ProvenanceClaim(
            ProvenanceTargetKind.COMPONENT,
            (record_key, component_key),
            sid,
            ProvenanceRole.PRIMARY
            if kind == "component"
            else ProvenanceRole.CONTEXTUAL,
        )
        claimant = f"{record_key}/{component_key}" + (
            "" if kind == "component" else " (bounds the component)"
        )
    else:
        record_key, component_key, label = (
            str(carrier[1]),
            str(carrier[2]),
            str(carrier[-1]),
        )
        fact = FACT_OF_LABEL[label]
        claim = ProvenanceClaim(
            ProvenanceTargetKind.FACT,
            fact_target_key(record_key, component_key, fact),
            sid,
            ProvenanceRole.PRIMARY if kind == "fact" else ProvenanceRole.CONTEXTUAL,
        )
        claimant = f"{record_key}/{component_key}/{fact_key(fact)}" + (
            "" if kind == "fact" else " (bounds the fact)"
        )
    provenance.append(claim)

    # Read the carrier back off the emitted claim rather than off the table it
    # is about to be compared with.
    if claim.target_kind is ProvenanceTargetKind.RECORD:
        derived: tuple[object, ...] = ("record", claim.target_key[0])
    elif claim.target_kind is ProvenanceTargetKind.COMPONENT:
        derived = (
            "component" if claim.role is ProvenanceRole.PRIMARY else "component_context",
            claim.target_key[0],
            claim.target_key[1],
        )
    else:
        emitted_label = LABEL_OF_FACT_KEY[str(claim.target_key[2])]
        emitted = FACT_OF_LABEL[emitted_label]
        derived = (
            (
                "fact",
                claim.target_key[0],
                claim.target_key[1],
                emitted.FAMILY.value,
                emitted_label,
            )
            if claim.role is ProvenanceRole.PRIMARY
            else (
                "fact_context",
                claim.target_key[0],
                claim.target_key[1],
                emitted_label,
            )
        )
    DERIVED[clause_id] = derived

    audit.append(
        {
            "clause": clause_id,
            "site": _site(clause_id),
            "record": COVER,
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
assert len(spans) == len(CLAUSE_ORDER) == 28, len(spans)
assert len({s.span_id for s in spans}) == 28, "a span id repeats"
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
assert (
    not _carrier_drift
), f"the emission does not carry what the review says: {_carrier_drift}"
_disposition_drift = {
    a["clause"]: a["disposition"]
    for a in audit
    if a["disposition"] != DISPOSITION_OF[EXPECTED[a["clause"]][1]].value
}
assert not _disposition_drift, _disposition_drift

#: **Shared provenance, proved from both directions.** Each doubly-printed rule
#: is one fact claimed PRIMARY by two spans, and those two spans are on leaves
#: from two *different* sites. A composition that quietly split one of them into
#: two facts, or that claimed both spans from one site, fails here.
_primary_by_target: dict[tuple[object, ...], list[str]] = defaultdict(list)
for _claim in provenance:
    if _claim.target_kind is ProvenanceTargetKind.FACT and (
        _claim.role is ProvenanceRole.PRIMARY
    ):
        _primary_by_target[tuple(_claim.target_key)].append(_claim.span_id)
_span_clause = {_span_id(c): c for c in CLAUSE_ORDER}
SHARED_PROVENANCE = {}
for _label, _clauses in COMPOSITION:
    _fact = FACT_OF_LABEL[_label]
    _key = fact_target_key(COVER, COMPONENT_OF_LABEL[_label], _fact)
    _claimed = sorted(_span_clause[s] for s in _primary_by_target[tuple(_key)])
    assert _claimed == sorted(_clauses), (_label, _claimed, _clauses)
    SHARED_PROVENANCE[_label] = {
        "component": COMPONENT_OF_LABEL[_label],
        "family": _fact.FAMILY.value,
        "fact_key": fact_key(_fact),
        "clauses": list(_clauses),
        "sites": sorted({_site(c) for c in _clauses}),
        "printed_twice": len(_clauses) == 2,
        "text": [_text(c) for c in _clauses],
    }
DOUBLY_PRINTED = sorted(
    label for label, row in SHARED_PROVENANCE.items() if len(row["sites"]) == 2
)
assert DOUBLY_PRINTED == [
    "half_benefit",
    "most_protective",
    "three_quarters_benefit",
    "total_prohibition",
], DOUBLY_PRINTED
for _label in DOUBLY_PRINTED:
    assert SHARED_PROVENANCE[_label]["sites"] == ["combat", "glossary"], _label

# --- The drafted representation --------------------------------------------
#
# Four components, all STRUCTURED. **Zero prose bindings**, and that is a
# positive claim: `ProseBindingDraft` requires one of the six closed reasons in
# `policy.IRREDUCIBILITY_REASONS`, and none is affirmatively true of any clause
# in this population. Binding one anyway would record a vocabulary gap as an
# irreducibility, which is the misfiling the closed catalog exists to prevent.
COMPONENTS = tuple(
    ComponentDraft(
        record_key=COVER,
        semantic_key=component_key,
        handling=ComponentHandling.STRUCTURED,
        facts=FACTS_BY_COMPONENT[component_key],
    )
    for component_key in COMPONENTS_IN_ORDER
)
for _c in COMPONENTS:
    assert _c.facts, _c
    for _f in _c.facts:
        assert not fact_invariant_violations(_f), (
            f"{_c.record_key}/{_c.semantic_key}",
            type(_f).__name__,
            fact_invariant_violations(_f),
        )
_component_by_key = {c.semantic_key: c for c in COMPONENTS}
for _claim in provenance:
    if _claim.target_kind is ProvenanceTargetKind.COMPONENT:
        assert tuple(_claim.target_key) == component_target_key(
            _component_by_key[str(_claim.target_key[1])]
        ), _claim

DRAFT = RepresentationDraft(
    records=tuple(
        RecordDraft(semantic_key=key, kind=RECORD_KIND[key]) for key in RECORDS_IN_ORDER
    ),
    components=COMPONENTS,
    prose_bindings=(),
    relationships=(),
    references=(),
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
    "records": (len(DRAFT.records), 1),
    "source_sites": (len(SITES), 2),
    "represented_leaves": (len(touched), 16),
    "policy_exclusions": (len(POLICY_EXCLUDED), 0),
    "container_leaves": (len(touched) + len(POLICY_EXCLUDED), 16),
    "clauses": (len(CLAUSE_ORDER), 28),
    "substantive_clauses": (
        sum(1 for s in spans if s.disposition is SemanticDisposition.SUBSTANTIVE),
        16,
    ),
    "components": (len(COMPONENTS), 4),
    "facts": (sum(len(c.facts) for c in COMPONENTS), 8),
    "boundary_leaves_excluded": (len(BOUNDARY_REDERIVED), 30),
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
        "site": _site(cid),
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

#: "All 28 discharged" is true and, alone, misleading: it counts a clause whose
#: text was handed to a supporting-authority span the same as one whose mechanic
#: entered the typed vocabulary. Classified by CARRIAGE — what the span
#: contributes — not by which element happens to own it.
OBLIGATION_ACCOUNTING: dict[str, object] = defaultdict(list)
for cid in CLAUSE_ORDER:
    bucket = {
        "fact": "typed",
        "component": "typed_component_scope",
        "record": "supporting_authority_record_owned",
        "component_context": "supporting_authority_bounding_a_component",
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
    len(OBLIGATION_ACCOUNTING["typed"])  # type: ignore[arg-type]
    + len(OBLIGATION_ACCOUNTING["typed_component_scope"])  # type: ignore[arg-type]
    == 16
), OBLIGATION_ACCOUNTING["tally"]

#: The closed irreducibility catalog, one line each, saying why *that* code is
#: false of this population rather than asserting a blanket "none of them fit".
#: Keys are checked against the live catalog, so a code added or renamed makes
#: this disclosure fail rather than quietly go stale.
REASON_DISPOSITION = {
    "contextual_applicability": (
        "false of all sixteen: each states its rule outright. The one printed "
        "condition - a benefit applies only against something originating on "
        "the opposite side - is a closed printed term carried by a field of the "
        "fact, not applicability prose the projection cannot enumerate."
    ),
    "subjective_judgment": (
        "false: nothing is left to anyone's assessment. 'at least half', 'at "
        "least three-quarters' and 'the whole' are exact printed thresholds, "
        "and 'most protective' is a printed selection rule."
    ),
    "open_ended_effect": (
        "false: every effect here is closed. 'Walls, trees, creatures, and "
        "other obstacles' is inline exemplification in a supporting-authority "
        "clause and is deliberately NOT read as an obstacle vocabulary."
    ),
    "gamemaster_latitude": (
        "false: the source delegates nothing here. Every degree, benefit, "
        "offeror and threshold is printed."
    ),
    "natural_language_exception": (
        "false: these are the rules, not exceptions carved out of one. The "
        "no-adding clause is the same rule stated negatively, carried by a "
        "required field beside the selection rather than as prose."
    ),
    "fiction_dependent_consequence": (
        "false: each consequence is mechanical and stated. Measuring how much "
        "of a target an obstacle covers, deciding which side an effect came "
        "from, and choosing a degree for a scene are adapter and adjudication "
        "work the record never claims to do."
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
NEW_FAMILIES = sorted(
    {str(r["name"]) for r in _INTRO_ROWS if r["kind"] == "fact_family"}
)
_VOCABULARIES = sorted(
    {tuple(r["vocabulary"]) for r in _INTRO_ROWS if r["kind"] == "vocabulary_member"}
)
assert {r["kind"] for r in _INTRO_ROWS} == {"fact_family", "vocabulary_member"}, sorted(
    {str(r["kind"]) for r in _INTRO_ROWS}
)
assert len(NEW_FAMILIES) == 5, NEW_FAMILIES
#: **One of those vocabularies is not new.** `CoverDegree` is schema 6's, carried
#: `THREE_QUARTERS` and `TOTAL`, and gains exactly one member here. Separated
#: rather than counted together, because widening an accepted vocabulary and
#: minting a new one are different acts with different review weight.
_COVER_DEGREE_VOCABULARY = tuple(m.value for m in CoverDegree)
assert _COVER_DEGREE_VOCABULARY in _VOCABULARIES, _VOCABULARIES
NEW_VOCABULARIES = [v for v in _VOCABULARIES if v != _COVER_DEGREE_VOCABULARY]
assert len(NEW_VOCABULARIES) == 8, NEW_VOCABULARIES
WIDENED_MEMBERS = sorted(
    str(r["name"])
    for r in _INTRO_ROWS
    if r["kind"] == "vocabulary_member"
    and tuple(r["vocabulary"]) == _COVER_DEGREE_VOCABULARY
)
assert WIDENED_MEMBERS == ["half"], WIDENED_MEMBERS
#: The families this batch actually uses are exactly the families the schema
#: introduced: an admitted-but-unused family would be speculation.
assert NEW_FAMILIES == sorted(
    {fact.FAMILY.value for fact in FACT_OF_LABEL.values()}
), NEW_FAMILIES

#: Decision 4 binds `invariant_manifest()` into schema identity. This schema
#: declares **no** intrinsic invariant row for its five families, and that is
#: read back rather than asserted from memory: every field of every new fact is
#: a single required closed member or a required int, so there is no
#: at-least-one, no-repeats or requires-a-stated-X rule to declare.
INTRINSIC_INVARIANTS = [
    dict(row)
    for row in invariant_manifest()
    if str(row["locus"]).removeprefix("fact:") in NEW_FAMILIES
]
assert INTRINSIC_INVARIANTS == [], INTRINSIC_INVARIANTS

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
        "CoverDegree": list(_COVER_DEGREE_VOCABULARY),
        "members_added_here": WIDENED_MEMBERS,
        "why": (
            "CoverDegree is schema 6's, minted from Hide (p183), and carried "
            "THREE_QUARTERS and TOTAL only - its own docstring said Half Cover "
            "'is outside this batch's cut and is admitted by the batch that "
            "states it'. This is that batch. representation_schema_payload "
            "emits vocabularies by their sorted admitted values, so this one "
            "member moves the schema hash by itself, independent of the five "
            "new families."
        ),
    },
    "intrinsic_invariants_declared": INTRINSIC_INVARIANTS,
    "accepted_families_changed": [],
    "registered_transitions_touched": ["5d-lift-schema-9-to-10"],
    "note": (
        "Five families over eight new closed vocabularies plus one member added "
        "to an accepted one, one family per gap in the discovery checkpoint's "
        "section 4 except that G1 is the widening rather than a family and G2 "
        "and G3 are two families because the two benefits are different kinds "
        "of thing: a bonus has a number and Total Cover's benefit is a "
        "prohibition. No field is added to, made required on, or made nullable "
        "on any accepted family and no ownership form changes, which is what "
        "makes the crossing a re-declaration rather than a rewrite."
    ),
    "no_runtime_geometry": (
        "Nothing here computes geometry. CoverageThreshold names the printed "
        "threshold - 'at least half', 'at least three-quarters', 'the whole "
        "target' - as closed members a hand-authored adapter interprets. "
        "Measuring how much of a target an obstacle covers, deciding which side "
        "an effect originated on, and choosing a degree for a scene are all "
        "runtime computation and are outside 5d. The excluded work is the "
        "computation, not the subject matter."
    ),
    "no_rank_over_the_degrees": (
        "'most protective' is the printed selection rule and no order over the "
        "three degrees is printed, recorded or implied. A rank field would be "
        "stating something the page does not."
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

#: Schema 10 appears in none of the five anchors. The prior is a schema-9
#: object through and through, which is what makes the crossing necessary
#: rather than cosmetic.
assert SCHEMA[0] not in set(REVIEW_PRIOR_ANCHORS.values()), REVIEW_PRIOR_ANCHORS

#: **One registered crossing.** The prior is anchored at schema 9; this batch
#: proposes under schema 10, which the sixteen substantive clauses required. The
#: step is looked up in the registry rather than named, and `verify_lift_path`
#: re-proves the accepted content element by element under the new contract
#: instead of asserting it. Accepted bytes are never restamped: the frozen prior
#: still declares schema 9 after this run, and is asserted unchanged below.
STEPS = lift_path((PRIOR.oracle.schema_version, PRIOR.oracle.schema_hash), SCHEMA)
LIFT_RECORDS = verify_lift_path(STEPS, PRIOR.oracle.representation)
assert [r.lift_id for r in LIFT_RECORDS] == ["5d-lift-schema-9-to-10"], LIFT_RECORDS

#: Reading a superseded prior as current is a *finding*, not a silent pass, and
#: the lift is what clears it.
_unlifted_findings = validate_schema_binding(candidate_from_accepted_inputs(PRIOR))
assert _unlifted_findings, "a superseded prior must not read as current"
LIFTED, _lift_records = lift_accepted_inputs(PRIOR, SCHEMA)
assert [r.lift_id for r in _lift_records] == ["5d-lift-schema-9-to-10"]
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
#: most — each batch's accepted-under hash is what keeps schema 10 from
#: restamping five batches as one.
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
        "a DIFFERENT object: the in-memory copy this run lifts to schema 10. "
        "Reported rather than pinned, because oracle_payload carries the "
        "representation binding and the lift re-declares exactly that, so this "
        "value moves with every destination-pin change."
    ),
    "payload_keys_that_moved": _moved_keys,
    "inherited_authority_unchanged": {
        "representation_object_is_the_same_object": True,
        "spans_obligations_batches_acceptances_anchors_cross_by_identity": True,
        "per_batch_schema_anchors": REVIEW_PRIOR_ANCHORS,
        "schema_10_appears_in_no_anchor": True,
        "why_anchors_matter": (
            "each accepted batch keeps the hash it was reviewed under. A lift "
            "that re-derived anchors would restamp five batches as one and "
            "erase the distinction succession depends on."
        ),
    },
    "unlifted_prior_read_as_current_is_a_finding": list(_unlifted_findings),
    "note": (
        "the accepted prior is anchored at 5d-representation-schema-9 and this "
        "batch proposes under 5d-representation-schema-10, which the "
        "population's sixteen substantive clauses required. Exactly one "
        "registered transition separates them and it is exercised here rather "
        "than described. The transition adds fact families and vocabularies and "
        "widens one accepted vocabulary by one member; it adds no field to an "
        "accepted family, no ownership form, no nullable field and no required "
        "field, so every accepted fact key, component key and provenance "
        "coordinate has the same canonical form under both contracts."
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
    # reports as unaccepted below is one of this batch's twenty-eight proposed
    # rows, and none of the prior's five hundred and thirty accepted ones.
    batches=tuple(LIFTED.batches),
    acceptances=tuple(LIFTED.acceptances),
)
merged_findings = list(validate_representation(MERGED, MERGED_LEDGER, CORPUS))

# --- Reference scope: standalone and combined, kept apart -------------------
#
# This batch emits no reference at all. What changes at the merge is that
# somebody else's citation acquires a target, and that is a property of the
# merged candidate rather than of accepted authority.
_batch_records = {rec.semantic_key for rec in DRAFT.records}
_prior_records = {r.semantic_key for r in PRIOR.oracle.representation.records}
_merged_records = {r.semantic_key for r in MERGED.records}
assert COVER not in _prior_records, "Cover is already in accepted authority"
assert COVER in _merged_records, "the merge does not define Cover"

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
assert _prior_missing == [
    "glossary.concentration",
    "glossary.cover",
    "glossary.speed",
], _prior_missing
assert _merged_missing == ["glossary.concentration", "glossary.speed"], _merged_missing
assert sorted(set(_prior_missing) - set(_merged_missing)) == [COVER], _prior_missing

#: The citing tuple, read out of the prior rather than described: who cites
#: Cover, from which component, in which scope, with which printed text.
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
        if ref.target_record_key == COVER
    ),
    key=lambda r: (str(r["from_record_key"]), str(r["source_text"])),
)
assert len(INBOUND_CITATIONS) == 1, INBOUND_CITATIONS
assert INBOUND_CITATIONS[0] == {
    "from_record_key": "glossary.area_of_effect",
    "from_component_key": "",
    "scope_key": "srd-5.2.1/rules-glossary",
    "source_text": "Cover",
    "target_record_key": COVER,
}, INBOUND_CITATIONS

REFERENCE_SCOPE = {
    "references_emitted": 0,
    "why_zero": (
        "the population prints exactly one citation - glossary/3/0, "
        "'\"Playing the Game\" (\"Combat\").' - and it names a CHAPTER, not a "
        "record. Every one of the prior's 53 references targets a record key "
        "and there is no record for a chapter. It is also this record's own "
        "second site, so a reference would be self-directed even if a target "
        "existed. The honest shape is record-owned supporting authority, which "
        "is what glossary/3/0 gets."
    ),
    "scope_key_decision": (
        "none arises. scope_key lives only on references and this batch emits "
        "none, so this batch proposes no second scope. Whether a future "
        "non-glossary batch needs one is left open and untouched."
    ),
    "outbound_citations": [],
    "inbound_citations": INBOUND_CITATIONS,
    "standalone": {
        "findings": len(standalone),
        "note": (
            "zero. The draft cites nothing, so there is no unresolved target "
            "for a standalone validation to report."
        ),
    },
    "combined": {
        "findings": len(merged_findings),
        "unresolved_targets_before": _prior_missing,
        "unresolved_targets_after": _merged_missing,
        "resolved_by_this_batch": [COVER],
        "resolving_citation": INBOUND_CITATIONS[0],
    },
    "resolution_scope": (
        "The Cover citation resolves in the MERGED CANDIDATE this run builds in "
        "memory - the lifted five-batch prior plus this proposal. It does NOT "
        "mean current accepted authority has changed: accepted authority is the "
        "frozen prior, it still carries three unresolved targets, nothing here "
        "is accepted, and the resolution becomes a property of accepted "
        "authority only at an acceptance that has not happened."
    ),
    "publishable_alone": False,
}

#: Both columns checked against a count DERIVED from the drafts rather than a
#: number chosen in advance: the validator reports one finding per unresolved
#: reference, not one per unresolved target.
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

#: **Standalone is clean, and the merged findings are asserted as exact tuples**,
#: so a third finding cannot hide behind the two inherited ones.
assert tuple(standalone) == (), standalone
assert UNRESOLVED_FINDINGS["standalone"]["distinct_targets"] == []
MERGED_FINDINGS_EXACT = (
    "reference srd-5.2.1/rules-glossary:'Concentration': unknown target record "
    "glossary.concentration",
    "reference srd-5.2.1/rules-glossary:'Speed': unknown target record "
    "glossary.speed",
)
assert len(merged_findings) == 2, merged_findings
assert all("unknown target record" in f for f in merged_findings), merged_findings
assert UNRESOLVED_FINDINGS["merged"]["distinct_targets"] == _merged_missing
assert not any(COVER in f for f in merged_findings), merged_findings
REFERENCE_SCOPE["validator_findings"] = UNRESOLVED_FINDINGS
REFERENCE_SCOPE["merged_findings_exact"] = sorted(merged_findings)

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
    "representation gate, merged with the lifted five-batch prior": len(
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
    "representation gate, merged with the lifted five-batch prior": (
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
# resulting objects rather than off this run's own dictionaries.
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
#: accepted. Filtering them away would be the dishonest move; asserting the
#: binding subset is empty is the check Task's "required authoritative seam"
#: names.
CANDIDATE_FINDINGS = list(validate_candidate(CANDIDATE, CORPUS))


#: The binding family is every prefix validate_candidate can emit before it
#: reaches the leaf partition, read off the validators themselves rather than
#: guessed: release agreement between binding, classification and corpus
#: snapshot (projection.validate_candidate), the semantic-policy binding
#: (accounting.validate_policy_binding) and the representation-schema binding
#: (projection.validate_schema_binding). Anything this does not recognise falls
#: to "other", which is asserted empty, so a binding disagreement worded some
#: other way still fails this run instead of being read as something milder.
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
        return "inherited_unresolved_reference"
    return "other"


CANDIDATE_FINDINGS_BY_CLASS: dict[str, list[str]] = defaultdict(list)
for _f in CANDIDATE_FINDINGS:
    CANDIDATE_FINDINGS_BY_CLASS[_finding_class(_f)].append(_f)
BINDING_CLASS_FINDINGS = CANDIDATE_FINDINGS_BY_CLASS["release_binding_disagreement"]
#: **The binding check is the one that must be clean**, and it is.
assert BINDING_CLASS_FINDINGS == [], BINDING_CLASS_FINDINGS
#: Nothing unexplained. Every other finding falls into exactly two classes, both
#: of which are the CORRECT result for a proposal of one record and neither of
#: which is filtered away: they are counted, classed, and one example of each is
#: carried so a reviewer can see what they say.
assert CANDIDATE_FINDINGS_BY_CLASS["other"] == [], CANDIDATE_FINDINGS_BY_CLASS[
    "other"
][:20]
assert sorted(k for k, v in CANDIDATE_FINDINGS_BY_CLASS.items() if v) == [
    "corpus_leaf_not_yet_classified",
    "inherited_unresolved_reference",
    "span_not_accepted",
], sorted(k for k, v in CANDIDATE_FINDINGS_BY_CLASS.items() if v)
#: And the tally is exhaustive: nothing was dropped by the classification.
assert sum(len(v) for v in CANDIDATE_FINDINGS_BY_CLASS.values()) == len(
    CANDIDATE_FINDINGS
), len(CANDIDATE_FINDINGS)
#: validate_candidate runs validate_representation too, so its reference
#: findings must be exactly the two the merged gate already reported - no more.
assert sorted(CANDIDATE_FINDINGS_BY_CLASS["inherited_unresolved_reference"]) == sorted(
    merged_findings
), CANDIDATE_FINDINGS_BY_CLASS["inherited_unresolved_reference"]
#: Derived, so the counts cannot drift: one per unclassified leaf of the bound
#: release, and one per span in the merged ledger.
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
    f.split()[1].rstrip(":")
    for f in CANDIDATE_FINDINGS_BY_CLASS["span_not_accepted"]
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
            f"reported honestly: the five accepted batches plus this proposal "
            f"cover {len(_classified_leaves)} leaves of the "
            f"{len(CORPUS.leaf_lengths)}-leaf release and the rest are "
            "undischarged. It is not a defect of this "
            "proposal and this proposal does not reduce it beyond its own "
            "sixteen leaves."
        ),
    },
    "inherited_unresolved_reference": {
        "count": len(CANDIDATE_FINDINGS_BY_CLASS["inherited_unresolved_reference"]),
        "example": CANDIDATE_FINDINGS_BY_CLASS["inherited_unresolved_reference"][0],
        "meaning": (
            "exactly the two the merged representation gate reports, inherited "
            "from the accepted prior: glossary.concentration and "
            "glossary.speed. Asserted equal to that list rather than merely "
            "counted, so a third could not hide here."
        ),
    },
    "span_not_accepted": {
        "count": len(CANDIDATE_FINDINGS_BY_CLASS["span_not_accepted"]),
        "example": CANDIDATE_FINDINGS_BY_CLASS["span_not_accepted"][0],
        "meaning": (
            "exactly this batch's twenty-eight proposed spans, by span id and "
            "not merely by count. The merged ledger carries the accepted "
            "prior's batches and acceptance records, so its 530 accepted spans "
            "clear this check and only the machine rows proposed here do not - "
            "which is the correct reading of a proposal: it is unaccepted "
            "because acceptance has not happened, and clearing it is the "
            "Owner's act, not this run's."
        ),
    },
}
SEAMS["binding agreement (validate_candidate, binding class)"] = len(
    BINDING_CLASS_FINDINGS
)
assert SEAMS["binding agreement (validate_candidate, binding class)"] == 0, SEAMS

_span_text = {a["span_id"]: a["text"] for a in audit}
BASE = _base_records(CANDIDATE)
assert COVER in BASE, sorted(BASE)


def _component_of(record_key: str, component_key: str) -> object:
    return next(
        c for c in BASE[record_key].components if c.semantic_key == component_key
    )


def _held(record_key: str, component_key: str, label: str) -> object:
    component = _component_of(record_key, component_key)
    assert component.handling is ComponentHandling.STRUCTURED, component
    assert component.irreducibility_reason_code is None, component
    assert len(component.governing_prose) == 0, component
    target = fact_key(FACT_OF_LABEL[label])
    return next(h for h in component.facts if fact_key(h.fact) == target)


CONSUMER_VIEW: dict[str, object] = {
    COVER: {
        "kind": BASE[COVER].kind.value,
        "component_keys": sorted(c.semantic_key for c in BASE[COVER].components),
        "record_scope_span_ids": len(BASE[COVER].span_ids),
        "clauses_carried_by_the_whole_record": len(spans),
        "assembled_from_sites": sorted({_site(c) for c in CLAUSE_ORDER}),
        "note": (
            "one record assembled from two printed sites in two chapters - "
            "#137 contract 3's composite case. Record membership is declared by "
            "accepted semantic assembly, not by a runtime heuristic over "
            "containers."
        ),
    }
}
assert CONSUMER_VIEW[COVER]["component_keys"] == sorted(COMPONENTS_IN_ORDER)
#: A base record carries the spans claimed at RECORD scope; the other twenty
#: hang off the components and facts that carry them, which is the point of
#: putting them there.
assert CONSUMER_VIEW[COVER]["record_scope_span_ids"] == len(RECORD_CONTEXT) == 8

#: **Three degrees, closed.** The vocabulary the closure clause states is read
#: back off the schema and off the facts, and the two agree.
_degrees_in_benefits = [_held(COVER, BENEFIT, lbl).fact.degree.value for lbl in
                        ("half_benefit", "three_quarters_benefit", "total_prohibition")]
_degrees_in_provisions = [_held(COVER, PROVISION, lbl).fact.degree.value for lbl in
                          ("half_provision", "three_quarters_provision", "total_provision")]
assert sorted(_degrees_in_benefits) == sorted(_COVER_DEGREE_VOCABULARY)
assert sorted(_degrees_in_provisions) == sorted(_COVER_DEGREE_VOCABULARY)
CONSUMER_VIEW["three_degrees"] = {
    "vocabulary": list(_COVER_DEGREE_VOCABULARY),
    "stated_by": CLOSURE_CLAUSE,
    "closure_text": _text(CLOSURE_CLAUSE),
    "carried_by": "a PRIMARY provenance claim on the whole degree_benefit component",
    "every_degree_has_a_benefit": _degrees_in_benefits,
    "every_degree_has_a_provision": _degrees_in_provisions,
    "no_rank_is_stated": True,
}

#: **Each degree's benefit, and the categorical difference at Total.** Half and
#: Three-Quarters are bonuses with a number; Total's is a prohibition with none.
_benefits = {
    "half": {
        "family": _held(COVER, BENEFIT, "half_benefit").fact.FAMILY.value,
        "bonus": _held(COVER, BENEFIT, "half_benefit").fact.bonus,
        "to_defense": _held(COVER, BENEFIT, "half_benefit").fact.to_defense.value,
        "to_saving_throw": _held(
            COVER, BENEFIT, "half_benefit"
        ).fact.to_saving_throw.value,
    },
    "three_quarters": {
        "family": _held(COVER, BENEFIT, "three_quarters_benefit").fact.FAMILY.value,
        "bonus": _held(COVER, BENEFIT, "three_quarters_benefit").fact.bonus,
        "to_defense": _held(
            COVER, BENEFIT, "three_quarters_benefit"
        ).fact.to_defense.value,
        "to_saving_throw": _held(
            COVER, BENEFIT, "three_quarters_benefit"
        ).fact.to_saving_throw.value,
    },
    "total": {
        "family": _held(COVER, BENEFIT, "total_prohibition").fact.FAMILY.value,
        "prohibits": _held(COVER, BENEFIT, "total_prohibition").fact.prohibits.value,
        "bonus": None,
    },
}
assert _benefits["half"]["bonus"] == 2 and _benefits["three_quarters"]["bonus"] == 5
assert _benefits["half"]["to_defense"] == "armor_class"
assert _benefits["half"]["to_saving_throw"] == "dexterity"
assert _benefits["total"]["family"] != _benefits["half"]["family"]
assert _benefits["total"]["prohibits"] == "direct_targeting"
CONSUMER_VIEW["degree_benefits"] = dict(_benefits) | {
    "note": (
        "one printed benefit that is TWO modifications at once - a bonus to AC "
        "AND to Dexterity saving throws - kept keyed to one degree, so neither "
        "half can be dropped. Total Cover has no bonus row at all: its benefit "
        "is a different kind of thing, and 'directly' is load-bearing and "
        "printed."
    )
}

#: **The printed offeror asymmetry.** Half admits a creature or an object; the
#: other two admit an object only. A shared offeror member would erase it.
_provisions = {
    _held(COVER, PROVISION, lbl).fact.degree.value: {
        "offered_by": _held(COVER, PROVISION, lbl).fact.offered_by.value,
        "coverage": _held(COVER, PROVISION, lbl).fact.coverage.value,
    }
    for lbl in ("half_provision", "three_quarters_provision", "total_provision")
}
assert _provisions["half"]["offered_by"] == "another_creature_or_an_object"
assert _provisions["three_quarters"]["offered_by"] == "an_object"
assert _provisions["total"]["offered_by"] == "an_object"
assert [_provisions[d]["coverage"] for d in ("half", "three_quarters", "total")] == [
    "at_least_half",
    "at_least_three_quarters",
    "whole_target",
], _provisions
CONSUMER_VIEW["degree_provision"] = dict(_provisions) | {
    "note": (
        "the asymmetry is the rule: only Half admits another creature as an "
        "offeror. The coverage members name the printed thresholds; nothing "
        "here measures anything, and 'the whole target' stays the phrase the "
        "page prints rather than becoming a number."
    )
}

#: **The opposite-side requirement**, printed at one site only and a
#: precondition on the benefit rather than a property of any degree.
_origin = _held(COVER, ORIGIN, "opposite_side").fact
assert _origin.interaction is CoveredInteraction.AN_ATTACK_OR_OTHER_EFFECT
assert _origin.requires_origin is BenefitOriginSide.OPPOSITE_SIDE_OF_THE_COVER
CONSUMER_VIEW["benefit_origin"] = {
    "interaction": _origin.interaction.value,
    "requires_origin": _origin.requires_origin.value,
    "printed_at": [_site("combat/1/2")],
    "text": _text("combat/1/2"),
    "note": (
        "printed only in Combat. A degree-only record would lose it entirely. "
        "Deciding which side an effect originated on is runtime geometry and is "
        "outside 5d."
    ),
}

#: **Most protective, and not added together** — one rule, claimed PRIMARY from
#: both printings, with the worked example kept as supporting authority.
_selection = _held(COVER, SELECTION, "most_protective")
assert _selection.fact.selects is CoverDegreeSelection.MOST_PROTECTIVE
assert _selection.fact.combination is CoverDegreeCombination.NOT_ADDED_TOGETHER
_selection_spans = sorted(_selection.span_ids)
_selection_primary = sorted(
    _primary_by_target[tuple(fact_target_key(COVER, SELECTION, _selection.fact))]
)
#: Three claiming spans: the two printings that state the rule, plus the worked
#: example that bounds it.
assert len(_selection_spans) == 3, _selection_spans
assert len(_selection_primary) == 2, _selection_primary
CONSUMER_VIEW["degree_selection"] = {
    "selects": _selection.fact.selects.value,
    "combination": _selection.fact.combination.value,
    "claimed_primary_by": [_span_text[s] for s in _selection_primary],
    "worked_example_is_supporting_authority": _text("combat/1/4"),
    "note": (
        "two clauses, one rule, both PRIMARY on their own spans: the glossary "
        "states it positively and Combat states the same rule negatively. No "
        "rank over the three degrees is printed, recorded or implied, and the "
        "worked example stays supporting authority rather than becoming a fact "
        "with a ranking in it."
    ),
}

#: **The shared provenance, read back off the projection.** Each doubly-printed
#: rule is one held fact with two claiming spans, one from each site.
def _primary_spans(label: str) -> list[str]:
    _component = COMPONENT_OF_LABEL[label]
    _key = tuple(fact_target_key(COVER, _component, FACT_OF_LABEL[label]))
    return sorted(_primary_by_target[_key])


CONSUMER_VIEW["shared_provenance"] = {
    label: {
        "component": SHARED_PROVENANCE[label]["component"],
        "span_ids_on_the_projection": len(
            _held(COVER, SHARED_PROVENANCE[label]["component"], label).span_ids
        ),
        "claiming_it_primary": len(_primary_spans(label)),
        "sites": SHARED_PROVENANCE[label]["sites"],
        "text": SHARED_PROVENANCE[label]["text"],
    }
    for label in DOUBLY_PRINTED
}
for _label, _row in CONSUMER_VIEW["shared_provenance"].items():  # type: ignore[union-attr]
    #: Two PRIMARY claims each, one per printed site. `most_protective`
    #: additionally carries the worked example as CONTEXTUAL, which is why the
    #: projection's span_ids are counted separately from the primary claims.
    assert _row["claiming_it_primary"] == 2, _row
    assert _row["sites"] == ["combat", "glossary"], _row
    assert _row["span_ids_on_the_projection"] == (
        3 if _label == "most_protective" else 2
    ), _row

#: **The closure claim**, read off the merged representation rather than off
#: this run's own list: exactly one component-level PRIMARY claim, on
#: `degree_benefit`, from the closure clause's span.
_closure_claims = [
    p
    for p in MERGED.provenance
    if p.target_kind is ProvenanceTargetKind.COMPONENT
    and p.role is ProvenanceRole.PRIMARY
    and p.span_id == _span_id(CLOSURE_CLAUSE)
]
assert len(_closure_claims) == 1, _closure_claims
assert tuple(_closure_claims[0].target_key) == (COVER, BENEFIT), _closure_claims
CONSUMER_VIEW["closure_claim"] = {
    "clause": CLOSURE_CLAUSE,
    "target": [COVER, BENEFIT],
    "role": "primary",
    "precedent_in_the_accepted_prior": sum(
        1
        for p in PRIOR.oracle.representation.provenance
        if p.target_kind is ProvenanceTargetKind.COMPONENT
        and p.role is ProvenanceRole.PRIMARY
    ),
    "note": (
        "a substantive statement about no single fact needs a component-scope "
        "carrier. The count above is the accepted precedent for that shape, "
        "read off the frozen prior rather than recalled."
    ),
}
assert CONSUMER_VIEW["closure_claim"]["precedent_in_the_accepted_prior"] == 19

#: The citing record, read off the same projection: `glossary.area_of_effect`'s
#: See-also citation of Cover now has a target in the merged candidate.
_aoe_targets = sorted(
    {
        r.target_record_key
        for r in MERGED.references
        if r.from_record_key == "glossary.area_of_effect"
    }
)
CONSUMER_VIEW["inbound_citation_resolution"] = {
    "citing_record": "glossary.area_of_effect",
    "its_targets": _aoe_targets,
    "assembled_by_the_projection": sorted(t for t in _aoe_targets if t in BASE),
    "not_assembled": sorted(t for t in _aoe_targets if t not in BASE),
    "scope": REFERENCE_SCOPE["resolution_scope"],
}
assert CONSUMER_VIEW["inbound_citation_resolution"]["not_assembled"] == []

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
        f"{ORIGIN_LABEL} (CRD Issue 5d batch cover-1, representation schema 10)"
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

counts: dict[str, int] = defaultdict(int)
for s in spans:
    counts[s.disposition.value] += 1

_provenance_shapes: dict[str, int] = defaultdict(int)
for _claim in provenance:
    _provenance_shapes[f"{_claim.target_kind.value}/{_claim.role.value}"] += 1

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
    "fact_families_used": len({f.FAMILY.value for f in FACT_OF_LABEL.values()}),
    "facts_printed_at_both_sites": len(DOUBLY_PRINTED),
    "prose_bindings": len(DRAFT.prose_bindings),
    "references": len(DRAFT.references),
    "relationships": len(DRAFT.relationships),
    "provenance_edges": len(provenance),
    "obligations": len(EXPECTED_OBLIGATIONS),
}
assert COUNTS["spans"] == len(audit) == len(proposed) == 28, COUNTS
assert COUNTS["provenance_edges"] == len(spans), COUNTS
assert (
    COUNTS["substantive"]
    + COUNTS["supporting_authority"]
    + COUNTS["non_mechanical"]
    + COUNTS["unresolved"]
    == COUNTS["spans"]
), COUNTS
assert COUNTS["substantive"] == 16 and COUNTS["supporting_authority"] == 12, COUNTS
assert COUNTS["references"] == COUNTS["relationships"] == 0, COUNTS
assert COUNTS["facts"] == 8 and COUNTS["components"] == 4, COUNTS
assert COUNTS["components_structured"] == 4, COUNTS
assert COUNTS["components_mixed"] == COUNTS["components_prose_bound"] == 0, COUNTS
assert COUNTS["prose_bindings"] == 0, COUNTS
assert COUNTS["unresolved"] == COUNTS["non_mechanical"] == 0, COUNTS
assert COUNTS["fact_families_used"] == 5, COUNTS
assert COUNTS["facts_printed_at_both_sites"] == 4, COUNTS
PROVENANCE_SHAPES = dict(sorted(_provenance_shapes.items()))
assert PROVENANCE_SHAPES == {
    "component/contextual": 3,
    "component/primary": 1,
    "fact/contextual": 1,
    "fact/primary": 15,
    "record/contextual": 8,
}, PROVENANCE_SHAPES

COUNT_DERIVATION = {
    "records": (
        "one. The two printed sites are one composite glossary.cover record, "
        "not two: accepted authority already cites glossary.cover by name, the "
        "three degrees are untagged table rows with no entry of their own, and "
        "CoverDegree is already consumed as a vocabulary by two accepted facts"
    ),
    "represented_leaves": (
        "distinct leaf ids the spans cover; all 16 of the two containers' 16 "
        "leaves, because this boundary has no policy exclusion"
    ),
    "clauses": (
        "the reviewed inventory's partition cells, read from the committed "
        "discovery manifest and re-proved gap-free against the bound leaves"
    ),
    "spans": "one per printed clause, at the clause's exact reviewed extent",
    "facts": (
        "8 over 16 substantive clauses: four rules are printed at both sites "
        "and are represented once each with PRIMARY provenance from both, and "
        "the three provision rows each take their degree label and their "
        "Offered By cell"
    ),
    "components": (
        "four, all STRUCTURED: one per column of the printed table "
        "(degree_benefit, degree_provision) and one per qualifying rule the "
        "prose adds (benefit_origin, degree_selection). Grouping the degrees is "
        "what gives the closure sentence a component to claim"
    ),
    "references": (
        "none. The population prints one citation and it names a chapter, not a "
        "record - and it points at this record's own second site. No scope_key "
        "decision arises"
    ),
    "prose_bindings": (
        "none. No clause in this population matches one of the six closed "
        "irreducibility reasons, so binding any of them would record a "
        "vocabulary gap as an irreducibility"
    ),
    "provenance_edges": (
        "one per clause: 8 record-scope CONTEXTUAL, 1 component-scope PRIMARY "
        "(the closure statement), 3 component-scope CONTEXTUAL, 15 fact-scope "
        "PRIMARY and 1 fact-scope CONTEXTUAL"
    ),
    "unresolved": (
        "none. Schema 10 carries all sixteen substantive clauses, so no span is "
        "emitted UNRESOLVED"
    ),
}

# ---------------------------------------------------------------------------
# Audit document
# ---------------------------------------------------------------------------

AUDIT_DOC: dict[str, object] = {
    "_": (
        "DISPOSABLE REVIEW MATERIAL for CRD Issue 5d batch cover-1. Emitted by "
        + ORIGIN_LABEL
        + ". This run accepts nothing, publishes nothing, activates nothing, "
        "retires nothing, writes no database and never executes the publication "
        "gate. It is material for semantic review."
    ),
    "proposal_identity": ident,
    "proposal_identity_scope": (
        "the identity of THIS PROPOSAL object. It is not the identity of "
        "accepted authority, which is unchanged, and it is not a claim that "
        "anything was accepted."
    ),
    "batch_selection": {
        "batch_id": "cover-1",
        "chosen_by": "complete source membership",
        "rule": (
            "there is no tag. Membership is the structural claim the run "
            "asserts: exactly two entry containers labeled 'Cover', one beneath "
            "'Rules Definitions' and one beneath 'Combat', and the first directs "
            "to the second through its own printed See-also citation. Printing "
            "the word 'Cover' is use, not definition, and pulls nothing in."
        ),
        "membership": {
            site: {
                "container_id": cid,
                "container_path": _path_of(cid),
                "page_index": sorted(
                    {LEAF_BY_ID[lid].page_index for lid in touched if LEAF_SITE[lid] == site}
                ),
                "leaves": sum(1 for lid in touched if LEAF_SITE[lid] == site),
            }
            for site, cid in SITES
        },
        "printed_join": DIRECTION,
        "record": COVER,
        "composite": (
            "#137 contract 3's composite case and ADR-005d Decision 3 read "
            "literally: a 5c ENTRY is structural evidence, not universal "
            "semantic authority, so two entries can state one mechanical "
            "entity. This is the first record in this build whose authority is "
            "drawn from two chapters."
        ),
        "what_this_is_not": (
            "the corpus #137 governs. This is ONE record of the Rules Glossary "
            "plus its governing section. The full-corpus obligation is "
            "untouched and undischarged, and no count in this artifact is "
            "evidence about it."
        ),
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
            "is the repository's own check that the binding, the classification "
            "ledger and the bound corpus snapshot all name one release - two of "
            "three agreeing is not agreement. Its binding-class findings are "
            "empty."
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
                "persisted_corpus_digest is a function of the persisted "
                "rp_sources rows and the read-back vector state. Recomputing it "
                "needs a session over that persisted state "
                "(persistence.recompute_persisted_digest); verifying a published "
                "release against declared values is "
                "operational.load_verified_operational_corpus, the narrower "
                "downstream seam. Neither requires a publish, and this run "
                "performs neither, so the value is carried from the 5c release "
                "record and disclosed."
            ),
        },
        "operational_database_evidence": {
            "performed_by_this_run": [],
            "note": (
                "NONE. This run opens no session, reads no rp_sources row, "
                "queries no vector store and persists nothing. The five "
                "re-derived values are source rederivation from the committed "
                "PDF; the sixth is a disclosed carry. No claim in this artifact "
                "rests on operational database evidence."
            ),
        },
    },
    "boundary": {
        "derived_from": (
            "the two entry containers the bound release labels 'Cover', one "
            "beneath 'Rules Definitions' and one beneath 'Combat'"
        ),
        "printed_pages": sorted({LEAF_BY_ID[lid].page_index + 1 for lid in touched}),
        "page_index_note": (
            "printed_page is page_index + 1: the glossary site is page index "
            "178 / printed p179, the Combat site page index 14 / printed p15"
        ),
        "policy_exclusions": POLICY_EXCLUDED,
        "excluded_leaves_that_print_the_word": {
            "count": len(BOUNDARY_REDERIVED),
            "by_section": BOUNDARY_BY_SECTION,
            "without_the_standalone_word": MANIFEST["boundary_without_standalone_word"],
            "lowercase_only_leaf_count": MANIFEST[
                "boundary_lowercase_only_leaf_count"
            ],
            "rederived_and_checked_against_the_manifest": True,
            "note": (
                "each of these uses Cover while stating some other rule, or "
                "restates a Cover rule from outside a Cover entry - leaf "
                "7322a0d0-afaf-5df9-97f6-a0e428c81097 (Spells > Casting Spells "
                "> Targets) states the spell-targeting rule that a caster needs "
                "a clear path, so the target cannot be behind Total Cover. "
                "Membership here is the reviewed structural rule - the container "
                "labelled Cover - so these leaves stay outside this reviewed "
                "population."
            ),
        },
        "canaries": {
            k: {"derived": v[0], "expected": v[1]} for k, v in CANARIES.items()
        },
        "extraction_artifacts_carried_verbatim": {
            "degree_label_as_extracted": _text("combat/7/0"),
            "degree_label_as_printed": "Three-Quarters",
            "table_caption_absorbed_into_the_prose_leaf": _text("combat/1/5"),
            "note": (
                "properties of the frozen 5c release, carried verbatim rather "
                "than repaired. The committed table inventory independently "
                "records the same fragmentation. No source-corpus change is "
                "proposed or made here."
            ),
        },
        "no_grid_language_in_the_source": (
            "the population prints no 'square', 'grid', 'battle map' or "
            "'token', so no grid semantic is represented. Recorded here as a "
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
            "from the PDF and holds byte-identical content; the reviewed clause "
            "extents partition each of the sixteen leaves end to end, starting "
            "at 0 and stopping at the leaf's length, and the concatenation "
            "reconstructs the leaf byte for byte. The manifest supplies the "
            "reviewed coordinates; the PDF supplies the content."
        ),
    },
    "counts": COUNTS,
    "count_derivation": COUNT_DERIVATION,
    "provenance_shapes": PROVENANCE_SHAPES,
    "record_shapes": {
        COVER: {
            "kind": RECORD_KIND[COVER].value,
            "components": [c.semantic_key for c in COMPONENTS],
            "facts": {
                c.semantic_key: [f.FAMILY.value for f in c.facts] for c in COMPONENTS
            },
            "prose_bindings": 0,
            "references": 0,
            "relationships": 0,
        }
    },
    "shared_provenance": SHARED_PROVENANCE,
    "shared_provenance_note": (
        "Four rules are printed at both sites and are represented ONCE each, "
        "with PRIMARY provenance from both sites' spans, because that is what "
        "the source did: it printed one rule twice. Provenance is per span, so "
        "several spans claiming one target is the ordinary shape. No validator "
        "forces this: validation.py:159 rejects two equal-keyed facts inside one "
        "component, and _validate_duplicated_fact_authority (validation.py:652) "
        "rejects sibling components holding an equivalent fact drawn from the "
        "SAME substantive span, so two components each holding a copy taken from "
        "the two distinct printings would pass both. One fact is chosen because "
        "both sites state one rule, and publishing two copies would be two "
        "claims where the source made one. Where the second printing "
        "DEFERS rather than states ('As detailed in the Cover table') it is "
        "supporting authority linked to what it defers to."
    ),
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
        "merged_findings": merged_findings,
        "candidate_findings_binding_class": BINDING_CLASS_FINDINGS,
        "candidate_findings_by_class": CANDIDATE_FINDING_CLASSES,
        "candidate_findings_note": (
            f"{len(CANDIDATE_FINDINGS)} findings, every one of them in one of "
            "three classes, all of them the "
            "correct result for a proposal of one record: leaves of the "
            "release no batch has classified yet, spans no acceptance has "
            "accepted, and the two unresolved reference targets inherited from "
            "the accepted prior. They are counted and classed rather than "
            "listed, with "
            "one example each, because a full dump would be tens of megabytes "
            "of the same two sentences. Nothing is filtered: the class tally "
            "sums to the total and the 'other' class is asserted empty."
        ),
        "what_zero_would_not_prove": (
            "these judge shape, not fidelity. Standalone this batch is clean, "
            "which proves only that it cites nothing it does not define; the "
            "two merged findings are inherited from the accepted prior and are "
            "named exactly."
        ),
    },
    "classification_partitions": {
        lid: {
            "record": COVER,
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
        "by schema 10, every one of them witnessed by at least one clause in "
        "this batch, and no span is emitted UNRESOLVED."
    ),
    "gaps_closed": GAPS_WITNESSED,
    "gap_witnesses": {g: sorted(v) for g, v in sorted(_derived_witnesses.items())},
    "irreducibility_catalog_disposition": dict(REASON_DISPOSITION)
    | {
        "conclusion": (
            "none of the six closed reasons is affirmatively true of any of the "
            "sixteen substantive clauses, so this batch emits ZERO prose "
            "bindings. That is a positive claim, not an omission: binding one "
            "anyway would record a vocabulary gap as an irreducibility, which "
            "is exactly the misfiling the closed catalog exists to prevent."
        )
    },
    "typed_prose_dispositions": {
        "typed": [
            {
                "record": COVER,
                "component": COMPONENT_OF_LABEL[label],
                "family": FACT_OF_LABEL[label].FAMILY.value,
                "fact": fact_key(FACT_OF_LABEL[label]),
                "clauses": list(clauses),
                "sites": sorted({_site(c) for c in clauses}),
                "text": [_text(c) for c in clauses],
                "states": OBLIGATION_TEXT[clauses[0]],
            }
            for label, clauses in COMPOSITION
        ],
        "typed_at_component_scope": [
            {
                "record": COVER,
                "component": BENEFIT,
                "clause": CLOSURE_CLAUSE,
                "text": _text(CLOSURE_CLAUSE),
                "states": OBLIGATION_TEXT[CLOSURE_CLAUSE],
            }
        ],
        "prose_bound": [],
        "supporting_authority": [
            {
                "record": COVER,
                "clause": a["clause"],
                "site": a["site"],
                "carried_by": a["claimant_kind"],
                "claimant": a["claimant"],
                "text": a["text"],
            }
            for a in audit
            if a["disposition"] == "supporting_authority"
        ],
        "unresolved": [],
    },
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
        "discovery checkpoint for the 5c disposition, section 4's gap table for "
        "the gap ids and its witness lists, section 4a for the shared-provenance "
        "disposition and section 4c for the one-record finding. It is not "
        "computed from anything this run emits, and the discovery manifest "
        "deliberately carries no disposition and no candidate record key, so "
        "the table is the independent statement of what the proposal owes the "
        "source. The emission is then checked against it three ways: every "
        "obligation discharged (omission), by exactly one span at exactly the "
        "reviewed extent (duplication), and carried by exactly the element the "
        "review names, down to WHICH fact of a multi-fact component (semantic "
        "loss)."
    ),
    "evidence_classes": [
        {
            "class": "source extraction and partition reconstruction",
            "executed_here": True,
            "strength": (
                "strong for coverage and span boundaries: the reviewed clause "
                "extents are re-proved gap-free against the sixteen leaves this "
                "run just extracted from the PDF, and the thirty-leaf exclusion "
                "is re-derived rather than transcribed. Says nothing about "
                "whether the meaning assigned to a span is right - that is what "
                "semantic review is for"
            ),
        },
        {
            "class": "obligation closure against the reviewed inventory",
            "executed_here": True,
            "strength": (
                "exposes omission, duplication and carrier drift against a "
                "table typed from the checkpoint rather than from the emission, "
                "including which fact of a multi-fact component carries a "
                "clause. It does not prove the checkpoint's judgment is right; "
                "it proves the proposal states that judgment and no other"
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
                "all six parts read through release_binding_payload and checked "
                "at validate_candidate, the seam that requires the binding, the "
                "classification ledger and the bound corpus snapshot to name "
                "one release. Five values are source rederivation from the "
                "committed PDF; the sixth is a disclosed carry and no "
                "operational database evidence was performed"
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
                "stated at two scopes. Standalone: zero findings, because this "
                "batch cites nothing. Combined with the lifted prior: two "
                "findings, glossary.concentration and glossary.speed, down from "
                "three because the prior's Cover citation acquires a target IN "
                "THE MERGED CANDIDATE. Accepted authority is unchanged"
            ),
        },
        {
            "class": "full-corpus completeness",
            "executed_here": False,
            "strength": (
                "NOT claimed. This is one record of the Rules Glossary and its "
                "governing section. The corpus #137 governs is untouched and "
                "undischarged"
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
            "glossary.concentration and glossary.speed remain unresolved from "
            "the accepted prior; they belong to a later glossary batch",
            "the prior's Cover citation resolves in the merged candidate only. "
            "Accepted authority still carries three unresolved targets and does "
            "so until an acceptance that has not happened",
            "the full-corpus obligation #137 governs is undischarged: this is "
            "one record",
        ],
        "requires_owner_authorization_before": [
            "any acceptance of this batch into committed authority",
            "any acceptance is also what would carry the accepted prior across "
            "5d-lift-schema-9-to-10; this run proves the crossing and performs "
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
RERUN = os.environ.get("COVER1_RERUN") == "1"
FINAL_SHA256 = {
    PROPOSAL_FILE: hashlib.sha256(_proposal_bytes).hexdigest(),
    AUDIT_FILE: hashlib.sha256(_audit_bytes).hexdigest(),
}
DETERMINISTIC: bool | None = None
if not RERUN:
    _child = subprocess.run(
        [sys.executable, str(Path(__file__).resolve())],
        env={**os.environ, "COVER1_RERUN": "1"},
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
print(f"batch          cover-1: one composite record {COVER}")
for _site_name, _cid in SITES:
    print(f"  {_site_name:10} {_path_of(_cid)}")
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
    print(
        f"  {c.record_key}/{c.semantic_key}: "
        + ", ".join(f.FAMILY.value for f in c.facts)
    )
print(f"facts          {COUNTS['facts']} over {COUNTS['substantive']} substantive clauses")
print(f"  printed twice {DOUBLY_PRINTED}")
print(f"prose bindings {COUNTS['prose_bindings']}  (none; no closed reason is true)")
print(f"references     {COUNTS['references']}  (the one printed citation names a chapter)")
print(f"provenance     {len(provenance)}  {json.dumps(PROVENANCE_SHAPES)}")
print("relationships  0")
print()
for name, found in (
    ("partition", partition),
    ("structural", STRUCTURAL),
    ("component rules", _component_rules),
    ("declared meaning", _declared_meaning),
    ("reason codes", reason_codes),
    ("representation (standalone)", standalone),
    ("representation (merged w/ lifted prior)", merged_findings),
    ("candidate findings, binding class", BINDING_CLASS_FINDINGS),
):
    print(f"{name:44} {len(found)}")
    for f in found:
        print("   -", f)
print(f"{'candidate findings, all classes':44} {len(CANDIDATE_FINDINGS)}")
for _cls, _row in sorted(CANDIDATE_FINDING_CLASSES.items()):
    print(f"   - {_cls:32} {_row['count']:>6}   e.g. {_row['example']}")
print()
print(f"wire trip      {WIRE_ROUND_TRIP}")
print(f"binding parts  {len(BINDING_PARTS)} via release_binding_payload; "
      f"rederived {len(BINDING_REDERIVED_HERE)}, disclosed {len(BINDING_DISCLOSED)}")
print("db evidence    none performed by this run")
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
    f"+{len(NEW_VOCABULARIES)} vocabularies, "
    f"+{len(WIDENED_MEMBERS)} member into CoverDegree, "
    f"{len(INTRINSIC_INVARIANTS)} declared invariant rows)"
)
print(
    f"succession     {REVIEW_PRIOR_SCHEMA_VERSION} -> {SCHEMA[0]} via "
    f"{SUCCESSION['steps']}, verified element by element"
)
print(f"prior identity (frozen file)   {PRIOR_IDENTITY}")
print(f"prior identity (lifted copy)   {LIFTED_IDENTITY}  (reported, not pinned)")
print(f"payload keys moved by the lift {_moved_keys}")
print(f"refs emitted   {COUNTS['references']}")
print(f"unresolved before  {_prior_missing}")
print(f"unresolved after   {_merged_missing}")
print(f"resolved by this   {[COVER]}  (in the MERGED CANDIDATE only)")
print(
    "publishable    False  (proposed only; not accepted, not activated, "
    "publication gate not executed)"
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
