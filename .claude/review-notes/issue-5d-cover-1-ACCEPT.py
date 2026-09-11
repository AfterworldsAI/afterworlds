"""Owner acceptance of CRD Issue 5d batch `cover-1` — the executable record.

The Owner accepted the reviewed proposal
`1d8a51164f9be0a1559aba93fb076ee0e8c262dda183791491bc339e3ebfec01` exactly as
represented, in these words:

    "I accept all 28 spans and the complete representation of proposal
    1d8a51164f9be0a1559aba93fb076ee0e8c262dda183791491bc339e3ebfec01 as batch
    cover-1, extending the preserved prior through the registered schema
    transitions."

**The decision is the Owner's; this script is only its execution.** Nothing here
reviews anything. It re-derives the exact object the Owner named, calls the one
native acceptance seam, and asserts that what landed on disk is what was
authorized and nothing else. The reviewer recorded in the artifact is therefore
the Owner, not the agent that ran this file.

It is an **acceptance** operation, not a regeneration and not a semantic
revision. It changes no proposal, no audit, no schema, no policy, and nothing
under `src/` except the one accepted-authority artifact it is authorized to
extend. In acceptance mode the reviewed `MechanicalProposal` is rebuilt by
executing the reviewed generator; in `--verify` it is reconstructed from the
committed proposal JSON and proved to be that proposal by round-tripping its
payload back to those exact bytes. Neither mode hand-converts the proposal JSON
into accepted authority: both hand the rebuilt object to the one native
`accept_proposal` seam and both assert its identity and payload hash before
doing so. It does not create a second oracle file; the resolver refuses two
artifacts claiming one release, so this batch *extends* the existing one. It
does not publish, activate, or retire anything, and it closes nothing.

Re-running it is refused once the acceptance exists, and refused early: in
acceptance mode the prior is the **live** artifact, pinned by content digest and
Git blob, so the moment accepted authority moves past this batch the run stops
before the generator executes and long before anything is written. Pass
`--verify` to rebuild the merge and re-check it against the committed artifact
without attempting the acceptance again; that mode reads the frozen five-batch
fixture as the prior, because after acceptance the live file *is* the merged
result and reading it as "the prior" would make every preservation comparison
compare the artifact to itself.

**What `--verify` reproduces, and from what.** It reconstructs the reviewed
proposal from the committed proposal JSON, derives the accepted scope *in its
recorded order* from the digest-pinned discovery manifest, calls the same
`accept_proposal` seam over the frozen prior, serializes the result in the one
committed form, and asserts the bytes equal the committed artifact's. Nothing in
that chain is read from the artifact being checked, and nothing is written: the
expected result is built in memory and compared, so a difference anywhere in the
merged file is refused, not only in the fields sampled further down. The scope
order matters because `resolved_scope` is retained verbatim while every other
collection is canonicalized — the generator emitted it in manifest clause order,
the proposal JSON sorts its spans canonically, and the accepted order is the
former. It is recovered from the manifest rather than re-read from the artifact,
so the check cannot pass by copying its own subject.

**What acceptance did make true, and in which direction.** This is the first
acceptance in the sequence that *shrinks* the unresolved-reference set rather
than leaving it alone or widening it. `areas-of-effect-1` carried the Area of
Effect umbrella's printed See-also citation of `Cover` as a real reference to
`glossary.cover` and could not resolve it, because no accepted batch defined
that record. This batch defines it, so that citation resolves. Nothing is
removed from the prior to achieve that and no reference is rewritten: the
resolution is a consequence of a record arriving, and the inbound citation is
asserted to still be the same single edge from `glossary.area_of_effect`, at the
same scope, with the same source text.

**What it did not make true.** `glossary.concentration` and `glossary.speed`
remain unresolved and remain publication blockers. They are asserted here by set
equality on target keys and asserted **non-empty**: a run reporting zero
findings would mean a target had been fabricated or a citation quietly dropped,
which is a worse outcome than the blockers it would appear to remove. The before
set, the resolved set and the added set (empty) are each stated, so neither
direction can drift silently. The corpus stays incomplete and the release stays
runtime-unpublished.

Schema 10 is likewise not a closure claim. It adds the five fact families this
entry needs over eight new closed vocabularies, widens the accepted
`CoverDegree` vocabulary by the single member `half` that `areas-of-effect-1`'s
schema-6 ancestor said the batch stating Half Cover would admit, and carries the
accepted schema-9 authority forward through the one registered lift
`5d-lift-schema-9-to-10`. It gives the repository no runtime geometry: nothing
here measures how much of a target an obstacle covers, decides which side an
effect originated on, or chooses a degree for a scene.

**There is no independent review-probe file for this batch** of the kind
`attitudes-1` had, and none is synthesized here. The retained review evidence is
the committed proposal, the committed audit
(`issue-5d-batch-cover-1-audit.json`) and the discovery checkpoint, all tracked
repository files. The audit is pinned by canonical-LF digest below and
cross-checked on exactly the fields it carries — identity, schema, prior
digests, reviewed counts and dispositions, the obligation tally, the reference
scope and the succession step. The accepted scope is derived from the proposal
and the digest-pinned discovery manifest, never from the audit and never from
the artifact under check. Every input either mode requires — the generator, the
proposal, the audit, the discovery manifest, the frozen prior and the committed
SRD PDF — is a tracked repository file, so `--verify` reproduces on any checkout
rather than only on the machine the review ran on.

The final independent review of record is `cover-1-final-owner-review.md` in the
Codex task folder. It is **not** a repository file and this script does not read
it; it is named here so the reader knows which review the authorization
followed, not cited as an input.
"""

from __future__ import annotations

import hashlib
import json
import os
import runpy
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
assert HERE.name == "review-notes" and HERE.parent.name == ".claude", HERE
sys.path.insert(0, str(REPO / "src"))

GENERATOR = HERE / "issue-5d-batch-cover-1-generator.py"
PROPOSAL_FILE = HERE / "issue-5d-batch-cover-1-PROPOSAL.json"
AUDIT_FILE = HERE / "issue-5d-batch-cover-1-audit.json"

#: The reviewed source inventory, and the only retained record of the order the
#: accepted scope was selected in. The generator walks its clause rows in file
#: order, which is what fixed `resolved_scope`; the proposal JSON sorts its spans
#: canonically and so cannot state that order. Pinned by the same canonical-LF
#: digest the generator pins, so verification cannot silently follow a different
#: inventory than the one that was reviewed.
MANIFEST_FILE = HERE / "issue-5d-cover-1-source-manifest.json"
MANIFEST_SHA256 = "f82163ee2fc6b6c1805974e6e7404eca45fd6b48452a64a91f9e6a4f0e0cdcad"  # noqa: E501  # pragma: allowlist secret

ACCEPTED_PATH = (
    REPO
    / "src/afterworlds/ingestion/mechanical/oracles"
    / "srd-5-2-1-corpus-36b786d8-fa2.json"
)

for _p in (GENERATOR, PROPOSAL_FILE, AUDIT_FILE, MANIFEST_FILE, ACCEPTED_PATH):
    assert _p.exists(), _p

# --- The pinned reviewed proposal ------------------------------------------
BATCH_ID = "cover-1"
REVIEWER = "Ravenlok (Owner)"

#: The content-derived identity of the reviewed **proposal** (`proposal.py:161`),
#: which is what the Owner's authorization names. It is expressly not a
#: projection identity: the accepted artifact's own identities are the three
#: `MERGED_*` pins further down.
PROPOSAL_IDENTITY = "1d8a51164f9be0a1559aba93fb076ee0e8c262dda183791491bc339e3ebfec01"  # noqa: E501  # pragma: allowlist secret
PROPOSAL_CONTENT_SHA256 = "132bbc9f47104cc5e768ef3a5ee48101ba3c6e8fcdbbaaec8029b3b36083d07e"  # noqa: E501  # pragma: allowlist secret
AUDIT_CONTENT_SHA256 = "927ca2d9985efce3fdcc2c851cff1f4a88d8c7021d15c2cd87f8f9d9abcd97ab"  # noqa: E501  # pragma: allowlist secret
SCHEMA_VERSION = "5d-representation-schema-10"
SCHEMA_HASH = "c39e3a35e197a1d1db5c2c2b3445ff0cbf03395c91e3426353a4bce589be4be0"  # noqa: E501  # pragma: allowlist secret
REVIEWED_HEAD = "717e6b10aa0cd355e3d2e354b4b0a9c38ed443b2"  # pragma: allowlist secret

#: The Owner's authorization, verbatim. Retained in the batch rule below so the
#: artifact carries the actual words the decision was made in, rather than a
#: paraphrase written by the process that executed it.
AUTHORIZATION = (
    "I accept all 28 spans and the complete representation of proposal "
    "1d8a51164f9be0a1559aba93fb076ee0e8c262dda183791491bc339e3ebfec01 as batch "
    "cover-1, extending the preserved prior through the registered schema "
    "transitions."
)

# --- The prior accepted authority, by the identities that survive a checkout -
#: Canonical order, which is the order the loaded artifact holds the batches in.
#: Not acceptance order — that is `PRIOR_ANCHOR_ORDER`, and the two differ.
PRIOR_BATCH_IDS = [
    "actions-1",
    "areas-of-effect-1",
    "attitudes-1",
    "conditions-1",
    "hazards-1",
]
PRIOR_ANCHOR_ORDER = [
    "conditions-1",
    "hazards-1",
    "actions-1",
    "attitudes-1",
    "areas-of-effect-1",
]
PRIOR_CONTENT_SHA256 = "9f3802514298f519120680db4a9a20805f5dcb8a4b00dd8686ed6faddec1e738"  # noqa: E501  # pragma: allowlist secret
PRIOR_BLOB = "467fcc62c8fb64e54cf74e73a6f55c384129eef7"  # pragma: allowlist secret
PRIOR_ORACLE_IDENTITY = "8e08ac48f2a57a4498557990a07270f9abd855b246c1039da68cc9ec82d44b40"  # noqa: E501  # pragma: allowlist secret
PRIOR_SCHEMA_VERSION = "5d-representation-schema-9"
PRIOR_SCHEMA_HASH = "f5a5e30817e64f019e31aa7f4692d72611215e4294e7da36242e492bca6b336e"  # noqa: E501  # pragma: allowlist secret
PRIOR_ANCHOR_SCHEMAS = [
    "5d-representation-schema-3",
    "5d-representation-schema-5",
    "5d-representation-schema-7",
    "5d-representation-schema-8",
    "5d-representation-schema-9",
]
PRIOR_LIFT_IDS = [
    "5d-lift-schema-3-to-4",
    "5d-lift-schema-4-to-5",
    "5d-lift-schema-5-to-6",
    "5d-lift-schema-6-to-7",
    "5d-lift-schema-7-to-8",
    "5d-lift-schema-8-to-9",
]

#: The frozen prior. Byte-identical to the live artifact as it stood before this
#: acceptance, and the file `--verify` compares the merged artifact against. It
#: is never written by this script and is not superseded by this acceptance: it
#: remains the frozen five-batch prior it was created to be, and this script
#: asserts its two identities unchanged in both modes.
FROZEN_PRIOR_PATH = (
    REPO
    / "tests/ingestion/mechanical/data"
    / (
        "accepted_prior_conditions_1_hazards_1_actions_1"
        "_attitudes_1_areas_of_effect_1.json"
    )
)

#: The merged artifact of record. Pinned by three identities that fail for three
#: different reasons: the oracle identity covers accepted *content*, while the
#: canonical content digest and the Git blob additionally cover the acceptance
#: **evidence** - reviewer, timestamp, batch rule, resolved scope, anchors and
#: lifts - which the oracle identity deliberately excludes, because re-reviewing
#: an unchanged classification must not remint a projection.
#:
#: These three are properties of an output that did not exist when this script
#: was written. They were obtained before the acceptance ran, by an untracked
#: probe that built the same merge in memory from the same retained inputs and
#: wrote nothing, so the acceptance run itself asserted them strictly rather
#: than being allowed to mint them. `--verify` is what proves they still hold of
#: the committed artifact.
MERGED_CONTENT_SHA256 = "391c71b72d7fa9406890c74eed9a505278ea4f8f4536a01cd3db1edf403f6407"  # noqa: E501  # pragma: allowlist secret
MERGED_BLOB = "b7c0149432072d4a3b151d0f9b2c458252e584da"  # pragma: allowlist secret
MERGED_ORACLE_IDENTITY = "86cd11c2be330f5962982d8d87dfc1847815710868223257529f30bef8cdb500"  # noqa: E501  # pragma: allowlist secret

#: The **observed execution time** of the acceptance, truncated to the second.
#: Fixed rather than `now()`, because pinning it is what makes the merged
#: artifact reproducible: a wall-clock timestamp would give the same accepted
#: content a different file digest on every run, so the three pins above could
#: never be asserted. It is not invented and it is not a synthetic midnight; its
#: basis is recorded beside it rather than left to be taken on trust.
ACCEPTED_AT = "2026-09-11T17:14:44Z"

#: How that time is known.
ACCEPTED_AT_BASIS = (
    "A UTC clock read taken in the same shell session that ran this script, "
    "before the run, truncated - not rounded - to the second, and written into "
    "the constant above before the interpreter started. It is not a wall clock "
    "read at replay, and it is not a synthetic date. It is the moment the "
    "acceptance was initiated rather than the moment the bytes landed; the "
    "observed write time of the accepted artifact is recorded in the "
    "acceptance checkpoint beside this script rather than passed off as this "
    "value. The session in which the Owner authorized the acceptance is the "
    "session that ran it, whose local date is 2026-09-11 and whose local time "
    "at the clock read was 10:14:44 - the workstation runs seven hours behind "
    "UTC, and both readings are stated rather than one being reported as the "
    "other."
)

assert ACCEPTED_AT.endswith("Z") and len(ACCEPTED_AT) == 20, ACCEPTED_AT

# --- Expected merged shape, stated before it is computed --------------------
PRIOR_COUNTS = {
    "spans": 530,
    "acceptances": 530,
    "records": 46,
    "components": 132,
    "prose_bindings": 49,
    "relationships": 0,
    "references": 53,
    "provenance": 547,
}
BATCH_COUNTS = {
    "spans": 28,
    "acceptances": 28,
    "records": 1,
    "components": 4,
    "prose_bindings": 0,
    "relationships": 0,
    "references": 0,
    "provenance": 28,
}
MERGED_COUNTS = {k: PRIOR_COUNTS[k] + BATCH_COUNTS[k] for k in PRIOR_COUNTS}
LEAVES = 16

#: Facts are counted **recursively**, over every object in the representation
#: carrying a `family` discriminator, because a fact may be nested inside another
#: fact. A top-level `sum(len(c.facts))` is a different and smaller number in
#: general; for this batch the two agree, which is asserted rather than assumed.
PRIOR_FACTS = 165
BATCH_FACTS = 8
MERGED_FACTS = PRIOR_FACTS + BATCH_FACTS

COVER_RECORDS = ("glossary.cover",)

#: The four components this batch adds, by their `(record_key, semantic_key)`
#: pairs, and how many facts each carries. Pinned as a mapping rather than as a
#: total, because "four components, eight facts" is also true of a merge that put
#: the eight facts in the wrong four places.
COVER_COMPONENT_FACTS = {
    ("glossary.cover", "degree_benefit"): 3,
    ("glossary.cover", "degree_provision"): 3,
    ("glossary.cover", "degree_selection"): 1,
    ("glossary.cover", "benefit_origin"): 1,
}

#: The prior's three unresolved citations, what this batch resolves, what it adds
#: (nothing), and what survives. Every one of the four sets is stated, because
#: this is the first acceptance in the sequence that moves the blocker set
#: **down** and a description would hide which direction it moved.
PRIOR_MISSING_REFERENCE_TARGETS = frozenset(
    {"glossary.concentration", "glossary.cover", "glossary.speed"}
)
RESOLVED_BY_THIS_BATCH = frozenset({"glossary.cover"})
ADDED_BY_THIS_BATCH: frozenset[str] = frozenset()
MISSING_REFERENCE_TARGETS = frozenset({"glossary.concentration", "glossary.speed"})
assert (
    PRIOR_MISSING_REFERENCE_TARGETS - RESOLVED_BY_THIS_BATCH
) | ADDED_BY_THIS_BATCH == MISSING_REFERENCE_TARGETS

#: The single inbound citation this acceptance resolves, stated in full. It is
#: the prior's edge, not one this batch emits: this batch emits **no** reference
#: at all. Pinned as a 4-tuple so a merge that resolved the target by rewriting
#: the citation instead of by defining the record fails here.
RESOLVING_CITATION = (
    "glossary.area_of_effect",
    "",
    "srd-5.2.1/rules-glossary",
    "Cover",
)

#: The registered crossing that carries the schema-9 prior to the schema-10
#: proposal. A table lookup, never a version comparison.
EXPECTED_LIFT_IDS = ["5d-lift-schema-9-to-10"]

from afterworlds.ingestion.corpus.hashing import hash_obj  # noqa: E402
from afterworlds.ingestion.corpus.pipeline import build_candidate  # noqa: E402
from afterworlds.ingestion.corpus.policy import exclusion_reason_for  # noqa: E402
from afterworlds.ingestion.corpus.reconcile import _full_coverage_edges  # noqa: E402
from afterworlds.ingestion.mechanical.acceptance import accept_proposal  # noqa: E402
from afterworlds.ingestion.mechanical.accounting import (  # noqa: E402
    derive_span_id,
    validate_acceptance,
)
from afterworlds.ingestion.mechanical.bound_corpus import (  # noqa: E402
    BoundCorpusSnapshot,
    ChunkCoverage,
)
from afterworlds.ingestion.mechanical.models import (  # noqa: E402
    ReviewState,
    SemanticDisposition,
)
from afterworlds.ingestion.mechanical.oracle import (  # noqa: E402
    ACCEPTED_ARTIFACT_KIND,
    _representation,
    _span,
    accepted_inputs_payload,
    load_accepted_inputs,
    oracle_identity,
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
    REPRESENTATION_COLLECTIONS,
    BenefitOriginSide,
    ComponentHandling,
    CoverageThreshold,
    CoverDefense,
    CoverDegree,
    CoverDegreeCombination,
    CoverDegreeSelection,
    CoveredInteraction,
    CoverOfferor,
    TargetingProhibition,
)
from afterworlds.ingestion.mechanical.schema_lift import (  # noqa: E402
    schema_binding_violations,
)
from afterworlds.ingestion.mechanical.validation import (  # noqa: E402
    validate_representation,
)
from afterworlds.pipeline.retrieval.config import RetrievalMemoryConfig  # noqa: E402


def _bound_corpus() -> BoundCorpusSnapshot:
    """The bound 5c corpus, built here from the committed PDF.

    Built in this script rather than taken from the generator, so verification
    of the committed artifact does not depend on re-running a pre-acceptance
    proof that is no longer true of the artifact it was proved against.
    """
    candidate = build_candidate(
        REPO / "docs/sources/DnD5_5e_SRD_CC_v5_2_1.pdf",
        retrieval_config=RetrievalMemoryConfig(),
    )
    labels = {c.container_id: c.label for c in candidate.ledger.containers}
    leaf_by_id = {leaf.leaf_id: leaf for leaf in candidate.ledger.leaves}
    represented = {
        leaf.leaf_id
        for leaf in candidate.ledger.leaves
        if exclusion_reason_for(leaf, labels) is None
    }
    edges = _full_coverage_edges(candidate.members.chunks, leaf_by_id)
    return BoundCorpusSnapshot(
        package_uuid=candidate.package_uuid,
        release_version=candidate.release_version,
        leaf_lengths={lid: len(leaf_by_id[lid].content) for lid in represented},
        chunk_coverage=tuple(
            ChunkCoverage(
                chunk_id=e.chunk_id,
                leaf_id=e.leaf_id,
                cover_start=e.cover_start,
                cover_end=e.cover_end,
                role=e.role,
                projection_id=e.projection_id,
            )
            for e in edges
        ),
    )


def _count_facts(payload: object) -> int:
    """Every fact in a representation payload, including nested ones.

    A fact is an object carrying a `family` discriminator. Counting the
    top-level `facts` lists alone undercounts, because a fact may carry facts.
    """
    if isinstance(payload, dict):
        here = 1 if "family" in payload else 0
        return here + sum(_count_facts(v) for v in payload.values())
    if isinstance(payload, list):
        return sum(_count_facts(v) for v in payload)
    return 0


def _reconstruct_proposal(document: dict[str, object]) -> MechanicalProposal:
    """The reviewed `MechanicalProposal`, rebuilt from the committed proposal JSON.

    Used by `--verify`, which must not run the generator: the generator writes
    the proposal and audit files, and a verification that writes is not a
    verification. Deserialization goes through the loader's own field parsers
    (`_span`, `_representation`) rather than a second hand-written reader, so a
    field this script forgot to carry cannot be quietly dropped instead of
    rejected.

    Fidelity is not taken on trust from those parsers either. The caller
    round-trips the result back through `proposal_payload` and asserts equality
    with the committed bytes, which is what makes "reconstructed from the
    retained proposal" a checked claim rather than an assertion about this
    function.

    `_span` stamps `ReviewState.ACCEPTED` because an oracle span is accepted by
    construction. That is immaterial here: review state is not part of any
    payload, and `accept_proposal` restamps every in-scope span regardless.
    """
    spans = []
    for index, raw in enumerate(document["proposed_spans"]):  # type: ignore[attr-defined]
        assert isinstance(raw, dict), raw
        spans.append(
            ProposedSpan(
                span=_span(
                    {
                        k: v
                        for k, v in raw.items()
                        if k not in ("proposal_origin", "rationale")
                    },
                    index,
                ),
                origin=str(raw["proposal_origin"]),
                rationale=str(raw["rationale"]),
            )
        )
    schema = document["representation_schema"]
    assert isinstance(schema, dict), schema
    binding = document["release_binding"]
    assert isinstance(binding, dict), binding
    return MechanicalProposal(
        binding=ReleaseBinding(**binding),
        policy_version=str(document["semantic_policy_version"]),
        policy_hash=str(document["semantic_policy_hash"]),
        schema_version=str(schema["version"]),
        schema_hash=str(schema["hash"]),
        proposed_spans=tuple(spans),
        proposed_representation=_representation(document["proposed_representation"]),
        proposal_origin=str(document["proposal_origin"]),
    )


def _identifiers(path: Path) -> tuple[str, str, str]:
    """Raw digest, canonical-LF digest, and Git blob id of one file.

    The canonical digest and the blob id are properties of the *content*; the
    raw digest is a property of a checkout, because `.gitattributes` declares
    `eol=lf` and a working copy predating that attribute can hold CRLF.
    """
    raw = path.read_bytes()
    canonical = raw.replace(b"\r\n", b"\n")
    blob = hashlib.sha1(  # noqa: S324 - Git's object id, not a security digest
        b"blob " + str(len(canonical)).encode() + b"\x00" + canonical
    ).hexdigest()
    return (
        hashlib.sha256(raw).hexdigest(),
        hashlib.sha256(canonical).hexdigest(),
        blob,
    )


def _write_artifact(path: Path, payload: dict[str, object]) -> bytes:
    """Write accepted authority as UTF-8 with LF newlines, exactly as committed.

    `indent=2, sort_keys=True` plus a trailing newline is the form the existing
    artifact is committed in — verified against it below — so extending the file
    does not reformat the batches it already holds.
    """
    text = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    path.write_text(text, encoding="utf-8", newline="\n")
    written = path.read_bytes()
    assert b"\r" not in written, "the accepted artifact was written with CR bytes"
    return written


# ---------------------------------------------------------------------------
# 1. The prior accepted authority, asserted before anything is computed from it
# ---------------------------------------------------------------------------

VERIFY_ONLY = "--verify" in sys.argv

#: Where the prior comes from, and it is a different file in each mode. During
#: the acceptance the prior is the live artifact being extended — never a frozen
#: copy, so this script can only ever extend the authority that actually exists
#: and refuses the moment that authority has moved on. Afterwards the live file
#: *is* the merged result, so verification reads the frozen fixture instead,
#: which is byte-identical to the pre-acceptance artifact and is never written.
PRIOR_PATH = ACCEPTED_PATH if not VERIFY_ONLY else FROZEN_PRIOR_PATH
_prior_raw_sha, _prior_content_sha, _prior_blob = _identifiers(PRIOR_PATH)

#: Asserted in **both** modes against the same two pinned values, because the
#: frozen fixture is byte-identical to the pre-acceptance artifact. There is one
#: prior identity, not two. In acceptance mode this is also the guard that stops
#: a stale re-run: it fails against current authority before a single byte is
#: generated or written.
assert _prior_content_sha == PRIOR_CONTENT_SHA256, (PRIOR_PATH, _prior_content_sha)
assert _prior_blob == PRIOR_BLOB, (PRIOR_PATH, _prior_blob)

PRIOR = load_accepted_inputs(PRIOR_PATH)
PRIOR_PAYLOAD = accepted_inputs_payload(PRIOR)

# It holds the five previously accepted batches, and only those.
assert [b.batch_id for b in PRIOR.batches] == PRIOR_BATCH_IDS, PRIOR.batches
assert {a.batch_id for a in PRIOR.acceptances} == set(PRIOR_BATCH_IDS)
assert PRIOR.oracle.schema_version == PRIOR_SCHEMA_VERSION
assert PRIOR.oracle.schema_hash == PRIOR_SCHEMA_HASH
assert oracle_identity(PRIOR.oracle) == PRIOR_ORACLE_IDENTITY
assert [a.batch_id for a in PRIOR.schema_anchors] == PRIOR_ANCHOR_ORDER
assert [a.schema_version for a in PRIOR.schema_anchors] == PRIOR_ANCHOR_SCHEMAS
assert [lr.lift_id for lr in PRIOR.lifts] == PRIOR_LIFT_IDS
assert len(PRIOR.oracle.spans) == PRIOR_COUNTS["spans"]
assert len(PRIOR.acceptances) == PRIOR_COUNTS["acceptances"]
for _coll in REPRESENTATION_COLLECTIONS:
    assert (
        len(getattr(PRIOR.oracle.representation, _coll)) == PRIOR_COUNTS[_coll]
    ), _coll
assert _count_facts(PRIOR_PAYLOAD["representation"]) == PRIOR_FACTS

#: The prior's three unresolved citations, stated **before** the merge, so what
#: this acceptance does to the blocker set is measured against a known start.
_prior_record_keys = {r.semantic_key for r in PRIOR.oracle.representation.records}
PRIOR_UNRESOLVED_REFERENCES = sorted(
    {
        ref.target_record_key
        for ref in PRIOR.oracle.representation.references
        if ref.target_record_key not in _prior_record_keys
    }
)
assert (
    set(PRIOR_UNRESOLVED_REFERENCES) == PRIOR_MISSING_REFERENCE_TARGETS
), PRIOR_UNRESOLVED_REFERENCES

#: The citation this acceptance will resolve, identified in the **prior** rather
#: than after the fact: exactly one edge targets `glossary.cover`, it comes from
#: `glossary.area_of_effect`, and the prior defines no such record. Asserting it
#: here is what makes "the previous Cover citation resolves" a statement about a
#: specific pre-existing edge rather than about a count that happened to drop.
PRIOR_COVER_CITATIONS = [
    (
        ref.from_record_key,
        ref.from_component_key,
        ref.scope_key,
        ref.source_text,
    )
    for ref in PRIOR.oracle.representation.references
    if ref.target_record_key == "glossary.cover"
]
assert PRIOR_COVER_CITATIONS == [RESOLVING_CITATION], PRIOR_COVER_CITATIONS
assert "glossary.cover" not in _prior_record_keys

# The prior's committed serialization is the form this script writes back.
assert (
    json.dumps(PRIOR_PAYLOAD, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
).encode("utf-8") == PRIOR_PATH.read_bytes().replace(b"\r\n", b"\n")


# ---------------------------------------------------------------------------
# 2. The reviewed proposal, rebuilt through the reviewed generator
# ---------------------------------------------------------------------------
# Not read from the JSON and not reconstructed by hand: the object accepted here
# is the one the generator builds, and its identity is asserted against the
# pinned value. Run with the rerun flag so it does not spawn its own child; its
# artifacts are deterministic, and both digests are asserted unchanged across the
# run so this script cannot be a covert regeneration. The generator reads the
# frozen five-batch fixture as its review prior and the live oracle only as a
# sentinel it asserts unmodified, so executing it here changes no authority.

(
    _proposal_raw_before,
    _proposal_content_before,
    _proposal_blob_before,
) = _identifiers(PROPOSAL_FILE)
assert _proposal_content_before == PROPOSAL_CONTENT_SHA256, _proposal_content_before
_audit_content_before = _identifiers(AUDIT_FILE)[1]
assert _audit_content_before == AUDIT_CONTENT_SHA256, _audit_content_before

#: The proposal identity, computed from the committed JSON before anything runs.
#: The Owner's authorization names this hash explicitly, so it is checked against
#: the bytes on disk first and against the rebuilt object second.
assert (
    hash_obj(json.loads(PROPOSAL_FILE.read_text(encoding="utf-8"))) == PROPOSAL_IDENTITY
), "the committed proposal JSON is not the proposal the Owner named"

# --- The recorded selection order, recovered from the reviewed inventory ----
#
# `resolved_scope` is the one field acceptance retains *verbatim*: spans, diffs
# and every representation collection are canonicalized on serialization, so the
# only order that survives into the artifact is the order the scope was handed
# over in. The generator handed over manifest clause order, which the canonically
# sorted proposal JSON does not preserve.
#
# So the order is recovered here from the manifest itself, whose digest is pinned
# to the value the generator asserts. Span ids are re-derived from each clause's
# leaf and half-open extent through the same `derive_span_id` the generator uses,
# never read back from the artifact under check — an expected value copied from
# its own subject would make the comparison below vacuous.
_manifest_raw, MANIFEST_DIGEST, _manifest_blob = _identifiers(MANIFEST_FILE)
assert MANIFEST_DIGEST == MANIFEST_SHA256, MANIFEST_DIGEST
MANIFEST = json.loads(MANIFEST_FILE.read_text(encoding="utf-8"))
MANIFEST_SCOPE = tuple(
    derive_span_id(str(row["leaf_id"]), int(row["char_start"]), int(row["char_end"]))
    for row in MANIFEST["clauses"]
)
assert len(MANIFEST_SCOPE) == BATCH_COUNTS["spans"], len(MANIFEST_SCOPE)
assert len(set(MANIFEST_SCOPE)) == len(MANIFEST_SCOPE), "a clause id repeats"

if not VERIFY_ONLY:
    os.environ["COVER1_RERUN"] = "1"
    _generated = runpy.run_path(str(GENERATOR), run_name="__cover1_accept__")
    PROPOSAL = _generated["PROPOSAL"]

    (
        _proposal_raw_after,
        _proposal_content_after,
        _proposal_blob_after,
    ) = _identifiers(PROPOSAL_FILE)
    assert _proposal_content_after == PROPOSAL_CONTENT_SHA256, _proposal_content_after
    assert _identifiers(AUDIT_FILE)[1] == AUDIT_CONTENT_SHA256, "the audit changed"
    assert _generated["LIVE_ORACLE_UNCHANGED"], "the generator touched live authority"

    assert proposal_identity(PROPOSAL) == PROPOSAL_IDENTITY, proposal_identity(PROPOSAL)
    PROPOSAL_PAYLOAD_HASH = hash_obj(proposal_payload(PROPOSAL))
    assert PROPOSAL_PAYLOAD_HASH == PROPOSAL_IDENTITY, PROPOSAL_PAYLOAD_HASH
    assert PROPOSAL.schema_version == SCHEMA_VERSION
    assert PROPOSAL.schema_hash == SCHEMA_HASH
    assert not schema_binding_violations(
        PROPOSAL.proposed_representation, (SCHEMA_VERSION, SCHEMA_HASH)
    )

    # The committed proposal JSON says the same thing the rebuilt object does.
    _committed_proposal = json.loads(PROPOSAL_FILE.read_text(encoding="utf-8"))
    assert (
        proposal_payload(PROPOSAL) == _committed_proposal
    ), "the rebuilt proposal differs from the committed proposal JSON"

    # --- The scope: every proposed span, in the generator's emission order --
    RESOLVED_SCOPE = tuple(p.span.span_id for p in PROPOSAL.proposed_spans)
    #: The generator emitted in manifest clause order, and the manifest is what
    #: `--verify` recovers that order from. Asserted here so the two derivations
    #: are known to agree on the run that actually creates the authority, rather
    #: than only claimed to by the mode that checks it afterwards.
    assert RESOLVED_SCOPE == MANIFEST_SCOPE, "the emission order left the manifest"
    SCOPE_SOURCE = "the reviewed generator's emission order (manifest clause order)"
else:
    # The generator is deliberately *not* run here: it writes the proposal and
    # the audit, and a verification that writes has verified nothing about the
    # bytes that were already there. The reviewed object is reconstructed from
    # the committed proposal JSON instead, and then proved to be that proposal
    # by round-tripping it back to those exact bytes.
    _committed_proposal = json.loads(PROPOSAL_FILE.read_text(encoding="utf-8"))
    PROPOSAL = _reconstruct_proposal(_committed_proposal)

    #: Two independent checks on the reconstruction, in this order. Payload
    #: equality is the strong one: every field of every span, component, fact,
    #: binding and provenance claim has to come back identical, so a field this
    #: script failed to carry fails here rather than passing as a subset. The
    #: identity check then ties the reconstruction to the hash the Owner's
    #: authorization names by its own words.
    assert (
        proposal_payload(PROPOSAL) == _committed_proposal
    ), "the reconstructed proposal does not round-trip to the committed JSON"
    assert proposal_identity(PROPOSAL) == PROPOSAL_IDENTITY, proposal_identity(PROPOSAL)
    PROPOSAL_PAYLOAD_HASH = hash_obj(proposal_payload(PROPOSAL))
    assert PROPOSAL_PAYLOAD_HASH == PROPOSAL_IDENTITY, PROPOSAL_PAYLOAD_HASH
    assert PROPOSAL.schema_version == SCHEMA_VERSION
    assert PROPOSAL.schema_hash == SCHEMA_HASH
    assert not schema_binding_violations(
        PROPOSAL.proposed_representation, (SCHEMA_VERSION, SCHEMA_HASH)
    )

    #: Nothing was written, so the pre-run identifiers are still the file's.
    #: Re-read rather than aliased, so a mode that somehow did write would be
    #: caught by the assertions rather than reported with stale values.
    (
        _proposal_raw_after,
        _proposal_content_after,
        _proposal_blob_after,
    ) = _identifiers(PROPOSAL_FILE)
    assert _proposal_content_after == PROPOSAL_CONTENT_SHA256, _proposal_content_after
    assert _identifiers(AUDIT_FILE)[1] == AUDIT_CONTENT_SHA256, "the audit changed"

    RESOLVED_SCOPE = MANIFEST_SCOPE
    SCOPE_SOURCE = "manifest clause order, re-derived from the pinned inventory"
    #: The reconstructed proposal proposed exactly the spans the manifest names.
    #: Set equality, because the proposal's own order is canonical and is not the
    #: recorded one; the order claim is the manifest's and is asserted by the
    #: full byte comparison in section 3 rather than by a second reading here.
    assert set(RESOLVED_SCOPE) == {
        p.span.span_id for p in PROPOSAL.proposed_spans
    }, "the manifest and the committed proposal name different spans"

_spans_reviewed = [p.span for p in PROPOSAL.proposed_spans]

assert _committed_proposal["representation_schema"] == {
    "version": SCHEMA_VERSION,
    "hash": SCHEMA_HASH,
}
assert len(RESOLVED_SCOPE) == BATCH_COUNTS["spans"], len(RESOLVED_SCOPE)
assert len(set(RESOLVED_SCOPE)) == len(RESOLVED_SCOPE), "the scope repeats a span"
assert len({p.leaf_id for p in _spans_reviewed}) == LEAVES
_by_disposition = {d: 0 for d in SemanticDisposition}
for _p in _spans_reviewed:
    _by_disposition[_p.disposition] += 1
assert _by_disposition[SemanticDisposition.UNRESOLVED] == 0, _by_disposition
assert _by_disposition[SemanticDisposition.NON_MECHANICAL] == 0, _by_disposition
DISPOSITIONS = {d.value: n for d, n in _by_disposition.items()}

#: The reviewed population is drawn from **two** printed sites — the Rules
#: Glossary `Cover` entry and the Combat chapter's `Cover` section — which is the
#: fact the whole shared-provenance shape rests on. Recovered from the manifest,
#: which records each clause's site, rather than from the audit.
MANIFEST_SITES = sorted({str(row["site"]) for row in MANIFEST["clauses"]})
assert MANIFEST_SITES == ["combat", "glossary"], MANIFEST_SITES

#: What the retained review evidence recorded, checked against what this script
#: derived on its own. There is no independent probe file for this batch, so the
#: cross-check subject is the committed audit — a tracked repository file, pinned
#: by digest above. It carries no accepted scope and is never used to build one;
#: it is compared on identity, schema, prior digests, counts, dispositions, the
#: obligation tally, the reference scope and the succession step. Reported as a
#: dict so a mismatch names the field rather than only failing.
_audit = json.loads(AUDIT_FILE.read_text(encoding="utf-8"))
_audit_counts = _audit["counts"]
_audit_prior = _audit["accepted_prior"]
_audit_refs = _audit["reference_scope"]
_audit_tally = _audit["obligation_accounting"]["tally"]
MATCHES_RETAINED_AUDIT = {
    "proposal_identity": _audit["proposal_identity"] == PROPOSAL_IDENTITY,
    "schema": _audit["representation_schema"]
    == {
        "version": SCHEMA_VERSION,
        "hash": SCHEMA_HASH,
    },
    "prior_sha256": _audit_prior["content_sha256"] == PRIOR_CONTENT_SHA256,
    "prior_blob": _audit_prior["blob"] == PRIOR_BLOB,
    "prior_identity": _audit_prior["identity"] == PRIOR_ORACLE_IDENTITY,
    "prior_batch_ids": _audit_prior["batch_ids"] == PRIOR_BATCH_IDS,
    "prior_spans": _audit_prior["spans"] == PRIOR_COUNTS["spans"],
    "prior_collections": (
        _audit_prior["collections"]
        == {coll: PRIOR_COUNTS[coll] for coll in REPRESENTATION_COLLECTIONS}
    ),
    "spans": _audit_counts["spans"] == BATCH_COUNTS["spans"],
    "records": _audit_counts["records"] == BATCH_COUNTS["records"],
    "components": _audit_counts["components"] == BATCH_COUNTS["components"],
    "facts": _audit_counts["facts"] == BATCH_FACTS,
    "prose_bindings": (
        _audit_counts["prose_bindings"] == BATCH_COUNTS["prose_bindings"]
    ),
    "references": _audit_counts["references"] == BATCH_COUNTS["references"],
    "relationships": _audit_counts["relationships"] == BATCH_COUNTS["relationships"],
    "provenance": _audit_counts["provenance_edges"] == BATCH_COUNTS["provenance"],
    "leaves": _audit_counts["represented_leaves"] == LEAVES,
    "source_sites": _audit_counts["source_sites"] == len(MANIFEST_SITES),
    "dispositions": (
        _audit_counts["substantive"] == DISPOSITIONS["substantive"]
        and _audit_counts["supporting_authority"]
        == DISPOSITIONS["supporting_authority"]
        and _audit_counts["unresolved"] == 0
        and _audit_counts["non_mechanical"] == 0
    ),
    "obligation_tally": (
        sum(_audit_tally.values()) == BATCH_COUNTS["spans"]
        and _audit_tally["typed"] == 15
        and _audit_tally["typed_component_scope"] == 1
        and _audit_tally["supporting_authority_record_owned"] == 8
        and _audit_tally["supporting_authority_bounding_a_component"] == 3
        and _audit_tally["supporting_authority_bounding_a_fact"] == 1
        and _audit["obligation_accounting"]["prose_bound"] == []
        and _audit["obligation_accounting"]["unresolved"] == []
    ),
    "unresolved_before": (
        sorted(_audit_refs["combined"]["unresolved_targets_before"])
        == sorted(PRIOR_MISSING_REFERENCE_TARGETS)
    ),
    "unresolved_after": (
        sorted(_audit_refs["combined"]["unresolved_targets_after"])
        == sorted(MISSING_REFERENCE_TARGETS)
    ),
    "resolved_by_this_batch": (
        sorted(_audit_refs["combined"]["resolved_by_this_batch"])
        == sorted(RESOLVED_BY_THIS_BATCH)
    ),
    "resolving_citation": (
        _audit_refs["combined"]["resolving_citation"]
        == {
            "from_record_key": RESOLVING_CITATION[0],
            "from_component_key": RESOLVING_CITATION[1],
            "scope_key": RESOLVING_CITATION[2],
            "source_text": RESOLVING_CITATION[3],
            "target_record_key": "glossary.cover",
        }
    ),
    "emits_no_reference": (
        _audit_refs["references_emitted"] == 0
        and _audit_refs["outbound_citations"] == []
    ),
    "succession_step": _audit["schema_succession"]["steps"] == EXPECTED_LIFT_IDS,
    "no_open_schema_stop": _audit["review_disposition"]["open_schema_stops"] == [],
}
assert all(MATCHES_RETAINED_AUDIT.values()), MATCHES_RETAINED_AUDIT

# ---------------------------------------------------------------------------
# 3. The acceptance action
# ---------------------------------------------------------------------------

#: Every figure the rule states is re-derived from the retained evidence rather
#: than typed, because the rule is baked into the accepted bytes: a wrong number
#: here cannot be corrected without reverting the acceptance. The assertions run
#: before `accept_proposal` is called.
assert DISPOSITIONS["substantive"] == 16, DISPOSITIONS
assert DISPOSITIONS["supporting_authority"] == 12, DISPOSITIONS
assert _audit_counts["fact_families_used"] == 5, _audit_counts
assert _audit_counts["facts_printed_at_both_sites"] == 4, _audit_counts
assert len(_audit["schema_extension"]["new_fact_families"]) == 5
assert _audit["schema_extension"]["new_vocabularies"]["count"] == 8
assert _audit["schema_extension"]["accepted_vocabulary_widened"][
    "members_added_here"
] == ["half"]
assert _audit["schema_extension"]["accepted_families_changed"] == []
#: The rule below names the six gaps by the checkpoint's own labels and gloss.
#: `schema_stops` is the set of stops still *open*; it is empty, which is why the
#: rule says closed rather than found.
assert _audit["gaps_closed"] == ["G1", "G2", "G3", "G4", "G5", "G6"], _audit[
    "gaps_closed"
]
assert sorted(_audit["gap_witnesses"]) == _audit["gaps_closed"]
assert all(_audit["gap_witnesses"][g] for g in _audit["gaps_closed"])
assert _audit["schema_stops"] == [], _audit["schema_stops"]
#: The rule states the obligation split in prose; the audit's tally is the
#: source of those five numbers.
assert _audit["obligation_accounting"]["tally"] == {
    "typed": 15,
    "typed_component_scope": 1,
    "supporting_authority_record_owned": 8,
    "supporting_authority_bounding_a_component": 3,
    "supporting_authority_bounding_a_fact": 1,
}, _audit["obligation_accounting"]["tally"]
assert _audit["obligation_accounting"]["prose_bound"] == []
assert _audit["obligation_accounting"]["unresolved"] == []

RULE = (
    f"Owner authorization recorded at {ACCEPTED_AT}, verbatim: {AUTHORIZATION!r} "
    f"Applied to CRD Issue 5d batch {BATCH_ID}, proposal identity "
    f"{PROPOSAL_IDENTITY} under representation schema {SCHEMA_VERSION} over 5c "
    f"release {PRIOR.oracle.binding.package_uuid}/"
    f"{PRIOR.oracle.binding.release_version}. The scope is the complete "
    "proposed span set and nothing outside it: 28 spans over 16 represented 5c "
    "leaves and 1 record — the Cover glossary rule, stated at both of the two "
    "sites that print it, the Rules Glossary entry and the Combat chapter's "
    "Cover section — with 16 substantive and 12 supporting-authority "
    "dispositions, and zero unresolved and zero non-mechanical. All 28 source "
    "obligations are discharged by carriage rather than by assertion: 15 typed, "
    "1 typed at component scope, 0 prose-bound and 12 supporting-authority-only "
    "(8 record-owned, 3 bounding a component and 1 bounding a fact). The six "
    "representation gaps the discovery checkpoint found — G1 the three-degree "
    "closure, G2 the defensive bonus, G3 the direct-targeting prohibition, G4 "
    "the provision polarity, G5 the opposite-side requirement and G6 "
    "most-protective selection, each witnessed by at least one clause in this "
    "batch — were all closed at representation schema 10 before review, by "
    "adding five fact families over "
    "eight new closed vocabularies and admitting the single member 'half' into "
    "the accepted CoverDegree vocabulary; no field is added to, made required "
    "on, or made nullable on any accepted family and no ownership form changes. "
    "The prior accepted schema-9 authority is carried forward by the single "
    "registered lift 5d-lift-schema-9-to-10. This acceptance emits no reference "
    "of its own and resolves one the prior could not: the Area of Effect "
    "umbrella's printed See-also citation of glossary.cover now has the record "
    "it names. glossary.concentration and glossary.speed remain unresolved from "
    "the prior; both remain publication blockers until the batches that define "
    "them are accepted, and no target was invented for either. The four "
    "components carry eight facts, seven of which are printed twice and four of "
    "those at both sites; each is one fact claimed as PRIMARY by every span "
    "that prints it, because the source stated one rule. Schema 10 names Cover; "
    "it supplies no runtime geometry, measures no coverage, decides no side and "
    "chooses no degree for a scene. Recorded by an agent executing this "
    "authorization; the decision is the Owner's and the execution is not a "
    "review."
)

#: **The merge itself, computed in both modes.** Acceptance and verification run
#: the same native seam over the same prior with the same scope, rule, reviewer
#: and timestamp — every one of which is a pinned constant or derived from a
#: pinned input above. Only the *writing* is conditional: verification produces
#: the expected artifact in memory and compares it, which is the whole point of
#: the mode. Nothing is reaccepted on disk and no second authority is created.
ACCEPTED = accept_proposal(
    PROPOSAL,
    batch_id=BATCH_ID,
    rule=RULE,
    resolved_scope=RESOLVED_SCOPE,
    reviewer=REVIEWER,
    accepted_at=ACCEPTED_AT,
    prior=PRIOR,
)
EXPECTED_BYTES = (
    json.dumps(
        accepted_inputs_payload(ACCEPTED), indent=2, sort_keys=True, ensure_ascii=False
    )
    + "\n"
).encode("utf-8")

if not VERIFY_ONLY:
    WRITTEN = _write_artifact(ACCEPTED_PATH, accepted_inputs_payload(ACCEPTED))
    assert WRITTEN == EXPECTED_BYTES, "the written bytes are not the computed merge"

# --- The complete comparison, before any sampled property is looked at ------
#
# This is the claim the reproduction rests on, and it is deliberately total: the
# expected artifact is rebuilt from retained inputs and compared **byte for
# byte** against the committed one. It subsumes every pin, count, set and tally
# below — those stay because they name *what* differs when something does, but
# none of them is what makes the reproduction sound. A field nobody thought to
# sample still fails here.
#
# It is stated before the three identity pins rather than after, so it cannot be
# read as a consequence of them: an artifact that satisfied all three pins and
# still differed somewhere the oracle identity excludes would be refused on this
# line.
_committed_bytes = ACCEPTED_PATH.read_bytes().replace(b"\r\n", b"\n")
REBUILT_ARTIFACT_IS_BYTE_IDENTICAL = _committed_bytes == EXPECTED_BYTES
if not REBUILT_ARTIFACT_IS_BYTE_IDENTICAL:
    _expected_doc = json.loads(EXPECTED_BYTES.decode("utf-8"))
    _committed_doc = json.loads(_committed_bytes.decode("utf-8"))
    _differing = sorted(
        key
        for key in sorted(set(_expected_doc) | set(_committed_doc))
        if _expected_doc.get(key) != _committed_doc.get(key)
    )
    raise AssertionError(
        "the merge rebuilt from the retained proposal, the pinned manifest and "
        "the frozen prior is not the committed artifact; top-level keys that "
        f"differ: {_differing or ['(none - byte-level difference only)']}"
    )

# From here the committed file is the subject: every assertion below reads what
# was actually written, not the in-memory result that produced it.
RESULT = load_accepted_inputs(ACCEPTED_PATH)
RESULT_PAYLOAD = accepted_inputs_payload(RESULT)
_accepted_raw_sha, _accepted_content_sha, _accepted_blob = _identifiers(ACCEPTED_PATH)
ORACLE_IDENTITY = oracle_identity(RESULT.oracle)

assert _accepted_content_sha == MERGED_CONTENT_SHA256, _accepted_content_sha
assert _accepted_blob == MERGED_BLOB, _accepted_blob
assert ORACLE_IDENTITY == MERGED_ORACLE_IDENTITY, ORACLE_IDENTITY

# ---------------------------------------------------------------------------
# 4. Post-acceptance assertions
# ---------------------------------------------------------------------------

# --- Batches, scope and evidence -------------------------------------------
#: The loaded artifact orders batches canonically rather than by acceptance
#: order, so a batch is identified here by its id and never by its position.
#: Acceptance order is not lost: `schema_anchors` below records it, and is
#: asserted there against `PRIOR_ANCHOR_ORDER`.
_by_batch = {b.batch_id: b for b in RESULT.batches}
assert sorted(_by_batch) == sorted([*PRIOR_BATCH_IDS, BATCH_ID]), sorted(_by_batch)
assert len(_by_batch) == len(RESULT.batches), "a batch id is recorded twice"
_batch = _by_batch[BATCH_ID]
_prior_batches = [_by_batch[bid] for bid in PRIOR_BATCH_IDS]
assert _batch.proposal_identity == PROPOSAL_IDENTITY
assert len(_batch.resolved_scope) == BATCH_COUNTS["spans"]
assert set(_batch.resolved_scope) == set(RESOLVED_SCOPE)
assert len(_batch.diff) == BATCH_COUNTS["spans"]
assert _batch.rule == RULE
assert AUTHORIZATION in _batch.rule, "the Owner's words did not survive into the batch"
_new_records = [a for a in RESULT.acceptances if a.batch_id == BATCH_ID]
assert len(_new_records) == BATCH_COUNTS["acceptances"]
assert {a.reviewer for a in _new_records} == {REVIEWER}
assert {a.accepted_at for a in _new_records} == {ACCEPTED_AT}

#: The semantic diff, retained in full rather than as a digest. Every entry must
#: name a span this batch accepted, and the accepted disposition must be the one
#: the reviewed proposal proposed - so the diff records what review changed
#: rather than restating the outcome.
_proposed_disposition = {p.span_id: p.disposition for p in _spans_reviewed}
DIFF_TALLY: dict[str, int] = {}
for _entry in _batch.diff:
    assert _entry.span_id in set(RESOLVED_SCOPE), _entry
    assert _entry.accepted_disposition == _proposed_disposition[_entry.span_id], _entry
    _was = (
        "none" if _entry.prior_disposition is None else _entry.prior_disposition.value
    )
    _k = f"{_was} -> {_entry.accepted_disposition.value}"
    DIFF_TALLY[_k] = DIFF_TALLY.get(_k, 0) + 1
assert sum(DIFF_TALLY.values()) == BATCH_COUNTS["spans"], DIFF_TALLY

# --- Merged counts, measured -----------------------------------------------
MEASURED = {
    "spans": len(RESULT.oracle.spans),
    "acceptances": len(RESULT.acceptances),
    **{
        coll: len(getattr(RESULT.oracle.representation, coll))
        for coll in sorted(REPRESENTATION_COLLECTIONS)
    },
}
assert MEASURED == MERGED_COUNTS, (MEASURED, MERGED_COUNTS)
MEASURED_FACTS = _count_facts(RESULT_PAYLOAD["representation"])
assert MEASURED_FACTS == MERGED_FACTS, (MEASURED_FACTS, MERGED_FACTS)
assert {s.review_state for s in RESULT.oracle.spans} == {ReviewState.ACCEPTED}
assert {a.span_id for a in RESULT.acceptances} == {
    s.span_id for s in RESULT.oracle.spans
}

# --- Every prior element and every piece of prior evidence, unchanged -------
#
# `PRIOR` is the genuine pre-acceptance content in both modes: the live artifact
# during the acceptance, and the byte-identical frozen fixture under `--verify`.
# So the exact comparisons below run in full in both modes. Counts are reported
# beside them, never in place of them: 530 acceptance records with a rewritten
# reviewer is still 530.
_prior_scope = {s for b in _prior_batches for s in b.resolved_scope}
_prior_kept_records = [a for a in RESULT.acceptances if a.batch_id in PRIOR_BATCH_IDS]
_prior_kept_spans = [s_ for s_ in RESULT.oracle.spans if s_.span_id in _prior_scope]
_merged_representation_payload = representation_payload(RESULT.oracle.representation)
PRESERVATION = {
    "prior_batch_records_identical": _prior_batches == list(PRIOR.batches),
    "prior_acceptance_records_identical": _prior_kept_records
    == list(PRIOR.acceptances),
    "prior_spans_identical": _prior_kept_spans == list(PRIOR.oracle.spans),
    "prior_payload_elements_present": {
        coll: all(
            element in _merged_representation_payload[coll]
            for element in PRIOR_PAYLOAD["representation"][coll]
        )
        for coll in sorted(REPRESENTATION_COLLECTIONS)
    },
    "prior_obligations_preserved": all(
        obligation in RESULT_PAYLOAD["obligations"]
        for obligation in PRIOR_PAYLOAD["obligations"]
    ),
    "prior_schema_anchors_identical": [
        (a.batch_id, a.proposal_identity, a.schema_version, a.schema_hash)
        for a in RESULT.schema_anchors
        if a.batch_id in PRIOR_BATCH_IDS
    ]
    == [
        (a.batch_id, a.proposal_identity, a.schema_version, a.schema_hash)
        for a in PRIOR.schema_anchors
    ],
    "prior_facts_still_present": MEASURED_FACTS - BATCH_FACTS == PRIOR_FACTS,
    "prior_references_identical": (
        _merged_representation_payload["references"]
        == PRIOR_PAYLOAD["representation"]["references"]
    ),
}
#: Every element of the prior the merged artifact does not carry, per collection.
#: Reported rather than only asserted, so a failure names what is missing.
MISSING_PRIOR_ELEMENTS = {
    coll: [
        element
        for element in PRIOR_PAYLOAD["representation"][coll]
        if element not in _merged_representation_payload[coll]
    ]
    for coll in sorted(REPRESENTATION_COLLECTIONS)
}
for _coll in REPRESENTATION_COLLECTIONS:
    # The acceptance seam keeps prior items first, so the in-memory result
    # carries them as an element-identical prefix — a property of the merge that
    # serialization then hides, because the committed order is canonical rather
    # than prior-first. Checked in **both** modes: verification computes the same
    # in-memory merge, so this is no longer an acceptance-only claim.
    _prior_elements = getattr(PRIOR.oracle.representation, _coll)
    _in_memory = getattr(ACCEPTED.oracle.representation, _coll)
    assert _in_memory[: len(_prior_elements)] == _prior_elements, _coll
    assert not MISSING_PRIOR_ELEMENTS[_coll], (
        _coll,
        len(MISSING_PRIOR_ELEMENTS[_coll]),
    )
    assert len(RESULT_PAYLOAD["representation"][_coll]) == MERGED_COUNTS[_coll], _coll
assert PRESERVATION["prior_batch_records_identical"], "a prior batch record moved"
assert PRESERVATION["prior_acceptance_records_identical"]
assert PRESERVATION["prior_spans_identical"]
assert all(PRESERVATION["prior_payload_elements_present"].values())
assert len(PRESERVATION["prior_payload_elements_present"]) == len(
    REPRESENTATION_COLLECTIONS
), "a collection was not compared at all"
assert PRESERVATION["prior_obligations_preserved"]
assert PRESERVATION["prior_schema_anchors_identical"], "a prior schema anchor moved"
assert PRESERVATION["prior_facts_still_present"]
#: The reference collection is *unchanged*, not merely preserved: this batch
#: emits none, so the merged references are exactly the prior's 53. That is what
#: makes "the Cover citation resolves because a record arrived" checkable —
#: nothing about the citation itself moved.
assert PRESERVATION["prior_references_identical"], "a prior reference moved"

#: The frozen five-batch prior is not superseded by this acceptance and is not
#: written by it. Asserted in both modes, because a script that quietly refreshed
#: the fixture it verifies against would verify nothing.
_frozen_raw, _frozen_content, _frozen_blob = _identifiers(FROZEN_PRIOR_PATH)
FROZEN_PRIOR_UNTOUCHED = (
    _frozen_content == PRIOR_CONTENT_SHA256 and _frozen_blob == PRIOR_BLOB
)
assert FROZEN_PRIOR_UNTOUCHED, (_frozen_content, _frozen_blob)

# --- Schema anchors and the registered 9 -> 10 succession -------------------
ANCHORS = [
    {
        "batch_id": a.batch_id,
        "proposal_identity": a.proposal_identity,
        "schema_version": a.schema_version,
        "schema_hash": a.schema_hash,
    }
    for a in RESULT.schema_anchors
]
assert [a["batch_id"] for a in ANCHORS] == [*PRIOR_ANCHOR_ORDER, BATCH_ID], ANCHORS
assert [a["schema_version"] for a in ANCHORS[:5]] == PRIOR_ANCHOR_SCHEMAS, ANCHORS
assert ANCHORS[-1]["schema_version"] == SCHEMA_VERSION, ANCHORS
assert ANCHORS[-1]["schema_hash"] == SCHEMA_HASH, ANCHORS
assert ANCHORS[-1]["proposal_identity"] == PROPOSAL_IDENTITY, ANCHORS
LIFTS = [
    {
        "lift_id": lift_record.lift_id,
        "from": [lift_record.from_version, lift_record.from_hash],
        "to": [lift_record.to_version, lift_record.to_hash],
        "verified_collections": list(lift_record.verified_collections),
    }
    for lift_record in RESULT.lifts
]
#: The prior's own 3 -> 4 -> 5 -> 6 -> 7 -> 8 -> 9 records are retained and the
#: new crossing is appended, so the artifact carries the whole succession rather
#: than only the last hop.
assert [lift_record["lift_id"] for lift_record in LIFTS] == [
    *PRIOR_LIFT_IDS,
    *EXPECTED_LIFT_IDS,
], LIFTS
assert LIFTS[-1]["from"] == [PRIOR_SCHEMA_VERSION, PRIOR_SCHEMA_HASH], LIFTS
assert LIFTS[-1]["to"] == [SCHEMA_VERSION, SCHEMA_HASH], LIFTS
for lift_record in LIFTS:
    assert sorted(lift_record["verified_collections"]) == sorted(
        REPRESENTATION_COLLECTIONS
    ), lift_record
assert RESULT.oracle.schema_version == SCHEMA_VERSION
assert RESULT.oracle.schema_hash == SCHEMA_HASH

# --- The one record arrived, and the representation with it -----------------
_keys = {r.semantic_key for r in RESULT.oracle.representation.records}
assert set(COVER_RECORDS) <= _keys, sorted(set(COVER_RECORDS) - _keys)
assert _keys == _prior_record_keys | set(COVER_RECORDS), sorted(_keys)
assert {o.record_key for o in RESULT.oracle.obligations} == _keys

#: The batch's typed representation arrived, not merely its spans. Schema 10
#: exists for five families, and every one of the eight facts is probed **by
#: value** below rather than by count: a merge that carried the right number of
#: the wrong facts would pass a count and fail here. The four components are
#: keyed by `(record_key, semantic_key)`, so a fact landing in the wrong
#: component fails too.
_components = {
    (c.record_key, c.semantic_key): c for c in RESULT.oracle.representation.components
}
_bound = {
    (b.record_key, b.component_key) for b in RESULT.oracle.representation.prose_bindings
}
_benefit = _components[("glossary.cover", "degree_benefit")]
_provision = _components[("glossary.cover", "degree_provision")]
_selection = _components[("glossary.cover", "degree_selection")]
_origin = _components[("glossary.cover", "benefit_origin")]

#: Half Cover is the member schema 10 admits into the accepted `CoverDegree`
#: vocabulary, and it is asserted present by value: the widening is the whole
#: reason this crossing moves the schema hash independently of the five new
#: families.
_benefit_bonuses = {
    f.degree: (f.bonus, f.to_defense, f.to_saving_throw)
    for f in _benefit.facts
    if type(f).__name__ == "CoverDefensiveBonusFact"
}
assert _benefit_bonuses[CoverDegree.HALF][0] == 2, _benefit_bonuses
assert _benefit_bonuses[CoverDegree.THREE_QUARTERS][0] == 5, _benefit_bonuses
assert {v[1] for v in _benefit_bonuses.values()} == {CoverDefense.ARMOR_CLASS}
assert len(_benefit_bonuses) == 2, _benefit_bonuses
_prohibitions = [
    f for f in _benefit.facts if type(f).__name__ == "CoverTargetingProhibitionFact"
]
assert len(_prohibitions) == 1, _prohibitions
assert _prohibitions[0].degree is CoverDegree.TOTAL, _prohibitions
assert _prohibitions[0].prohibits is TargetingProhibition.DIRECT_TARGETING

#: What each degree requires of an obstacle, and who may offer it. Half Cover is
#: the only degree the source lets a *creature* provide, which is a stated
#: mechanic a summary would drop.
_provisions = {
    f.degree: (f.offered_by, f.coverage)
    for f in _provision.facts
    if type(f).__name__ == "CoverProvisionFact"
}
assert _provisions == {
    CoverDegree.HALF: (
        CoverOfferor.ANOTHER_CREATURE_OR_AN_OBJECT,
        CoverageThreshold.AT_LEAST_HALF,
    ),
    CoverDegree.THREE_QUARTERS: (
        CoverOfferor.AN_OBJECT,
        CoverageThreshold.AT_LEAST_THREE_QUARTERS,
    ),
    CoverDegree.TOTAL: (CoverOfferor.AN_OBJECT, CoverageThreshold.WHOLE_TARGET),
}, _provisions

#: The selection rule is carried with **both** halves of what the source prints:
#: the most protective degree applies, and the degrees are not added together.
#: A bare "most protective" would read the same in a report and drop a mechanic.
assert [type(f).__name__ for f in _selection.facts] == ["CoverDegreeSelectionFact"]
assert _selection.facts[0].selects is CoverDegreeSelection.MOST_PROTECTIVE
assert _selection.facts[0].combination is CoverDegreeCombination.NOT_ADDED_TOGETHER

assert [type(f).__name__ for f in _origin.facts] == ["CoverBenefitOriginFact"]
assert _origin.facts[0].interaction is CoveredInteraction.AN_ATTACK_OR_OTHER_EFFECT
assert _origin.facts[0].requires_origin is BenefitOriginSide.OPPOSITE_SIDE_OF_THE_COVER

COVER_COMPONENTS = {
    f"{record}/{key}": {
        "handling": _components[(record, key)].handling.value,
        "facts": sorted(type(f).__name__ for f in _components[(record, key)].facts),
        "fact_count": len(_components[(record, key)].facts),
        "prose_bound": (record, key) in _bound,
    }
    for record, key in COVER_COMPONENT_FACTS
}

#: Whole-batch shape: every component structured, none prose-bound, and the
#: fact-per-component distribution is the pinned mapping rather than a total.
_batch_components = [
    c for c in RESULT.oracle.representation.components if c.record_key in COVER_RECORDS
]
assert len(_batch_components) == BATCH_COUNTS["components"], len(_batch_components)
assert {c.handling for c in _batch_components} == {ComponentHandling.STRUCTURED}
assert not [c for c in _batch_components if (c.record_key, c.semantic_key) in _bound]
assert {
    (c.record_key, c.semantic_key): len(c.facts) for c in _batch_components
} == COVER_COMPONENT_FACTS
assert sum(len(c.facts) for c in _batch_components) == BATCH_FACTS
#: Top-level and recursive fact counts agree for this batch, so the eight facts
#: carry no nested facts. Asserted rather than assumed, because `_count_facts`
#: is recursive and the two numbers differ in general.
assert (
    _count_facts(
        [
            _merged_representation_payload["components"][i]
            for i, c in enumerate(RESULT.oracle.representation.components)
            if c.record_key in COVER_RECORDS
        ]
    )
    == BATCH_FACTS
)

#: The shared-provenance shape, measured from the merged artifact rather than
#: read from the audit. One fact per printed rule, claimed PRIMARY by every span
#: that prints it: seven of the eight facts are printed twice and one once, so
#: the batch's fifteen PRIMARY fact edges are 7x2 + 1. Four of the seven are
#: printed at *both* sites — the Rules Glossary entry and the Combat section —
#: and three are printed twice within the Combat section alone.
_batch_span_ids = set(RESOLVED_SCOPE)
_primary_spans_per_fact: dict[tuple[str, ...], set[str]] = {}
for _edge in RESULT.oracle.representation.provenance:
    if _edge.target_kind.value != "fact" or _edge.role.value != "primary":
        continue
    if _edge.span_id not in _batch_span_ids:
        continue
    _primary_spans_per_fact.setdefault(tuple(_edge.target_key), set()).add(
        _edge.span_id
    )
assert len(_primary_spans_per_fact) == BATCH_FACTS, len(_primary_spans_per_fact)
SHARED_PROVENANCE = sorted(
    len(spans_) for spans_ in _primary_spans_per_fact.values()
)
assert SHARED_PROVENANCE == [1, 2, 2, 2, 2, 2, 2, 2], SHARED_PROVENANCE
assert sum(SHARED_PROVENANCE) == 15, SHARED_PROVENANCE
assert all(
    key[0] == "glossary.cover" for key in _primary_spans_per_fact
), sorted(_primary_spans_per_fact)

# --- Round trip, and the two validators ------------------------------------
ROUND_TRIP = json.loads(ACCEPTED_PATH.read_text(encoding="utf-8")) == RESULT_PAYLOAD
assert ROUND_TRIP, "the written artifact does not round-trip"
assert RESULT_PAYLOAD["artifact_kind"] == ACCEPTED_ARTIFACT_KIND
ACCEPTANCE_FINDINGS = list(validate_acceptance(RESULT.classification()))
assert not ACCEPTANCE_FINDINGS, ACCEPTANCE_FINDINGS
assert not schema_binding_violations(
    RESULT.oracle.representation, (SCHEMA_VERSION, SCHEMA_HASH)
)

CORPUS = _bound_corpus()
assert CORPUS.package_uuid == RESULT.oracle.binding.package_uuid
assert CORPUS.release_version == RESULT.oracle.binding.release_version
REPRESENTATION_FINDINGS = list(
    validate_representation(
        RESULT.oracle.representation, RESULT.classification(), CORPUS
    )
)

# --- Two source-authored citations still have no target --------------------
#
# Asserted by **set equality on target keys**, not by count, and asserted to be
# non-empty. The movement is asserted in both directions: exactly
# `glossary.cover` left the blocker set, and nothing joined it. A run that showed
# this batch adding a target would mean a citation had been minted; a run that
# showed it emptying the set would mean `glossary.concentration` or
# `glossary.speed` had been fabricated or their citations quietly dropped.
UNRESOLVED_REFERENCES = sorted(
    {
        ref.target_record_key
        for ref in RESULT.oracle.representation.references
        if ref.target_record_key not in _keys
    }
)
assert set(UNRESOLVED_REFERENCES) == MISSING_REFERENCE_TARGETS, UNRESOLVED_REFERENCES
assert UNRESOLVED_REFERENCES, "a blocker set that emptied here would be fabricated"
assert (
    set(PRIOR_UNRESOLVED_REFERENCES) - set(UNRESOLVED_REFERENCES)
    == RESOLVED_BY_THIS_BATCH
), (PRIOR_UNRESOLVED_REFERENCES, UNRESOLVED_REFERENCES)
assert (
    set(UNRESOLVED_REFERENCES) - set(PRIOR_UNRESOLVED_REFERENCES) == ADDED_BY_THIS_BATCH
), (PRIOR_UNRESOLVED_REFERENCES, UNRESOLVED_REFERENCES)
assert len(REPRESENTATION_FINDINGS) == len(
    MISSING_REFERENCE_TARGETS
), REPRESENTATION_FINDINGS
assert all(
    any(target in finding for target in MISSING_REFERENCE_TARGETS)
    for finding in REPRESENTATION_FINDINGS
), REPRESENTATION_FINDINGS
assert not any(
    "glossary.cover" in finding for finding in REPRESENTATION_FINDINGS
), REPRESENTATION_FINDINGS

#: **The resolution, stated as a property of the surviving edge.** The prior's
#: single citation of `glossary.cover` is still there, unchanged in every field,
#: and now points at a record the artifact defines. This batch emitted no
#: reference of its own, which is asserted rather than described: the merged
#: reference collection is the prior's, element for element.
RESOLVED_CITATIONS = [
    (
        ref.from_record_key,
        ref.from_component_key,
        ref.scope_key,
        ref.source_text,
    )
    for ref in RESULT.oracle.representation.references
    if ref.target_record_key == "glossary.cover"
]
assert RESOLVED_CITATIONS == [RESOLVING_CITATION], RESOLVED_CITATIONS
assert "glossary.cover" in _keys
_batch_references = [
    (ref.from_record_key, ref.target_record_key)
    for ref in RESULT.oracle.representation.references
    if ref.from_record_key in set(COVER_RECORDS)
]
assert _batch_references == [], _batch_references
assert len(RESULT.oracle.representation.references) == PRIOR_COUNTS["references"]

# ---------------------------------------------------------------------------
# 5. Report
# ---------------------------------------------------------------------------

REPORT = {
    "batch": BATCH_ID,
    "reviewer": REVIEWER,
    "reviewer_is_the_decision_maker": (
        "the Owner accepted; this script executed the recorded action and "
        "reviewed nothing"
    ),
    "accepted_at": ACCEPTED_AT,
    "accepted_at_basis": ACCEPTED_AT_BASIS,
    "authorization": AUTHORIZATION,
    "reviewed_head": REVIEWED_HEAD,
    "final_independent_review": (
        "cover-1-final-owner-review.md in the Codex task folder - not a "
        "repository file, not read by this script, and named rather than cited"
    ),
    "proposal_identity": PROPOSAL_IDENTITY,
    "proposal_identity_scope": (
        "the content-derived identity of this proposal (proposal.py:161). Not a "
        "projection identity and not the identity of accepted authority: those "
        "are the accepted_* fields below."
    ),
    "proposal_payload_hash": PROPOSAL_PAYLOAD_HASH,
    "proposal_content_sha256": _proposal_content_after,
    "proposal_blob": _proposal_blob_after,
    "proposal_raw_sha256_diagnostic": _proposal_raw_after,
    "schema": [SCHEMA_VERSION, SCHEMA_HASH],
    "scope": {
        "spans": len(RESOLVED_SCOPE),
        "leaves": LEAVES,
        "records": len(COVER_RECORDS),
        "source_sites": MANIFEST_SITES,
        "dispositions": DISPOSITIONS,
        "order_source": SCOPE_SOURCE,
    },
    "source_manifest_sha256": MANIFEST_DIGEST,
    #: The whole reproduction claim, in one boolean. The expected artifact is
    #: rebuilt from the retained proposal, the pinned manifest and the frozen
    #: prior through `accept_proposal`, and compared byte for byte. Independent
    #: of the three identity pins below and asserted before them: every other
    #: field in this report samples the result, and this one compares all of it.
    "reconstructed_artifact_byte_identical_to_committed": (
        REBUILT_ARTIFACT_IS_BYTE_IDENTICAL
    ),
    "matches_retained_audit": MATCHES_RETAINED_AUDIT,
    "semantic_diff_tally": DIFF_TALLY,
    "merged_counts": MEASURED,
    "merged_facts_recursive": MEASURED_FACTS,
    "batches": [b.batch_id for b in RESULT.batches],
    "schema_anchors": ANCHORS,
    "lifts": LIFTS,
    "preservation": PRESERVATION,
    "frozen_five_batch_prior_untouched": FROZEN_PRIOR_UNTOUCHED,
    "cover_components": COVER_COMPONENTS,
    "primary_spans_per_fact": SHARED_PROVENANCE,
    "round_trip": ROUND_TRIP,
    "validate_acceptance": ACCEPTANCE_FINDINGS,
    "validate_representation": REPRESENTATION_FINDINGS,
    "publication_blockers": {
        "unresolved_before": PRIOR_UNRESOLVED_REFERENCES,
        "resolved_by_this_batch": sorted(RESOLVED_BY_THIS_BATCH),
        "added_by_this_batch": sorted(ADDED_BY_THIS_BATCH),
        "unresolved_reference_targets": UNRESOLVED_REFERENCES,
        "still_blocked": bool(UNRESOLVED_REFERENCES),
        "resolving_citation": list(RESOLVING_CITATION),
        "note": (
            "accepted, not publishable. This batch is the first to shrink the "
            "blocker set: it resolved the prior's Cover citation by defining "
            "the record and added none of its own. Concentration and Speed "
            "remain explicit unresolved targets and no target was invented for "
            "either."
        ),
    },
    "batch_references": _batch_references,
    "accepted_oracle_identity": ORACLE_IDENTITY,
    "accepted_artifact_content_sha256": _accepted_content_sha,
    "accepted_artifact_blob": _accepted_blob,
    "accepted_artifact_raw_sha256_diagnostic": _accepted_raw_sha,
    "accepted_artifact_matches_pinned_merged_identity": (
        _accepted_content_sha == MERGED_CONTENT_SHA256
        and _accepted_blob == MERGED_BLOB
        and ORACLE_IDENTITY == MERGED_ORACLE_IDENTITY
    ),
    "prior_artifact_source": str(PRIOR_PATH.relative_to(REPO).as_posix()),
    "prior_artifact_content_sha256": _prior_content_sha,
    "prior_artifact_blob": _prior_blob,
    "prior_artifact_raw_sha256_diagnostic": _prior_raw_sha,
    "prior_oracle_identity": PRIOR_ORACLE_IDENTITY,
    "missing_prior_elements": {
        coll: len(missing) for coll, missing in MISSING_PRIOR_ELEMENTS.items()
    },
    "not_done": [
        "publication",
        "activation",
        "retirement",
        "merge",
        "a six-batch frozen prior fixture",
        "any further batch or runtime geometry",
        "full-corpus completion is not claimed",
        "#137 remains in progress",
    ],
}

print(json.dumps(REPORT, indent=1))
