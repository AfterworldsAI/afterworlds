"""Owner acceptance of CRD Issue 5d batch `speed-1` — the executable record.

The Owner accepted the reviewed proposal
`bd9d49427b7f2d996269e4e30a74abc26dacb7804e9176d8ca7f908b6c6a2bf8` exactly as
represented, in these words:

    "I accept all 36 spans and the complete representation of proposal
    bd9d49427b7f2d996269e4e30a74abc26dacb7804e9176d8ca7f908b6c6a2bf8 as batch
    speed-1, extending the preserved prior through the registered schema
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
without attempting the acceptance again; that mode reads the frozen six-batch
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

**What acceptance makes true, and in which direction.** The residue moves both
ways here, which is why all four sets are stated rather than a net figure. The
prior could not resolve `glossary.speed`: `action.dash` cites Speed and no
accepted batch defined that record. This batch defines it, so that one citation
resolves — the same way `cover-1` resolved the Area of Effect umbrella's Cover
citation, by a record arriving rather than by a citation being rewritten. In the
same act this batch emits **nine** outgoing references of its own, one for each
entry the Speed rule cites and none of which any accepted batch defines, so the
unresolved-target set goes from two to ten. That is not a regression and it is
not a reason to withhold the batch: the source prints those citations, and an
acceptance that dropped them to keep a count down would be recording something
the page does not say. `glossary.concentration` is untouched and remains the
inherited residue it was.

**The nine are references, not records.** This batch ingests `glossary.speed`
and nothing else. Climbing, Crawling, Flying, Jumping, Swimming, Burrow Speed,
Climb Speed, Fly Speed and Swim Speed are named as *targets* of citations the
Speed entry prints; no record, component, fact or span is created for any of
them, and no target was invented — each target key follows from the printed term
by the same rule the earlier batches used. They belong to later glossary
batches.

Schema 11 is likewise not a closure claim. It adds the seven fact families this
entry needs over eleven new closed vocabularies, widens the accepted
`MovementMode` vocabulary by the single member `jump`, and carries the accepted
schema-10 authority forward through the one registered lift
`5d-lift-schema-10-to-11`. The one field added to an accepted family —
`movement_allowance.window` — is optional and defaults to `None`, so every
accepted fact key, component key and provenance coordinate keeps the canonical
form it had under schema 10. It gives the repository no runtime movement and no
geometry: nothing here measures a distance, tracks a remaining allowance,
subtracts what a creature has already moved, or converts a Speed into squares.
`DistanceUnit.FOOT` reproduces the unit the page prints; it is not a grid.

**This script consumes no committed repository review probe** of the kind
`attitudes-1` had, and none is synthesized here. The retained review evidence is
the committed proposal, the committed audit
(`issue-5d-batch-speed-1-audit.json`) and the discovery checkpoint, all tracked
repository files. The audit is pinned by canonical-LF digest below and
cross-checked on exactly the fields it carries — identity, schema, prior
digests, reviewed counts and dispositions, the obligation tally, the reference
scope and the succession step. The accepted scope is derived from the proposal
and the digest-pinned discovery manifest, never from the audit and never from
the artifact under check. Every input either mode requires — the generator, the
proposal, the audit, the discovery manifest, the frozen prior and the committed
SRD PDF — is a tracked repository file, so `--verify` reproduces on any checkout
rather than only on the machine the review ran on.

The independent semantic review of record was performed by Codex against head
`7a38b1619e7725c5b531d7b52bd06a2789d84eb2` and returned no blocking finding. It
is **not** a repository file and this script does not read it; it is named here
so the reader knows which review the authorization followed, not cited as an
input.
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

GENERATOR = HERE / "issue-5d-batch-speed-1-generator.py"
PROPOSAL_FILE = HERE / "issue-5d-batch-speed-1-PROPOSAL.json"
AUDIT_FILE = HERE / "issue-5d-batch-speed-1-audit.json"

#: The reviewed source inventory, and the only retained record of the order the
#: accepted scope was selected in. The generator walks its clause rows in file
#: order, which is what fixed `resolved_scope`; the proposal JSON sorts its spans
#: canonically and so cannot state that order. Pinned by the same canonical-LF
#: digest the generator pins, so verification cannot silently follow a different
#: inventory than the one that was reviewed.
MANIFEST_FILE = HERE / "issue-5d-speed-1-source-manifest.json"
MANIFEST_SHA256 = "8c8ea8eed38feaeb28d74386690b5ee28e43872b1316517b922fb89afa016b20"  # noqa: E501  # pragma: allowlist secret

ACCEPTED_PATH = (
    REPO
    / "src/afterworlds/ingestion/mechanical/oracles"
    / "srd-5-2-1-corpus-36b786d8-fa2.json"
)

for _p in (GENERATOR, PROPOSAL_FILE, AUDIT_FILE, MANIFEST_FILE, ACCEPTED_PATH):
    assert _p.exists(), _p

# --- The pinned reviewed proposal ------------------------------------------
BATCH_ID = "speed-1"
REVIEWER = "Ravenlok (Owner)"

#: The content-derived identity of the reviewed **proposal** (`proposal.py:161`),
#: which is what the Owner's authorization names. It is expressly not a
#: projection identity: the accepted artifact's own identities are the three
#: `MERGED_*` pins further down.
PROPOSAL_IDENTITY = "bd9d49427b7f2d996269e4e30a74abc26dacb7804e9176d8ca7f908b6c6a2bf8"  # noqa: E501  # pragma: allowlist secret
PROPOSAL_CONTENT_SHA256 = "78e6dc72c208f11f1a1c234611751563ece50338d7c212bec81054e4f111188a"  # noqa: E501  # pragma: allowlist secret
AUDIT_CONTENT_SHA256 = "15c1cf300d7a656b1d42c705b7b63407b1669f976912e39b9a31d6c43abd679a"  # noqa: E501  # pragma: allowlist secret
SCHEMA_VERSION = "5d-representation-schema-11"
SCHEMA_HASH = "605e8b4cfdaf0cb6d4f0b65fcf0d23f3e45c4734404c9568f41dc4261eefd037"  # noqa: E501  # pragma: allowlist secret
REVIEWED_HEAD = "7a38b1619e7725c5b531d7b52bd06a2789d84eb2"  # pragma: allowlist secret

#: The Owner's authorization, verbatim. Retained in the batch rule below so the
#: artifact carries the actual words the decision was made in, rather than a
#: paraphrase written by the process that executed it.
AUTHORIZATION = (
    "I accept all 36 spans and the complete representation of proposal "
    "bd9d49427b7f2d996269e4e30a74abc26dacb7804e9176d8ca7f908b6c6a2bf8 as batch "
    "speed-1, extending the preserved prior through the registered schema "
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
    "cover-1",
    "hazards-1",
]
PRIOR_ANCHOR_ORDER = [
    "conditions-1",
    "hazards-1",
    "actions-1",
    "attitudes-1",
    "areas-of-effect-1",
    "cover-1",
]
PRIOR_CONTENT_SHA256 = "391c71b72d7fa9406890c74eed9a505278ea4f8f4536a01cd3db1edf403f6407"  # noqa: E501  # pragma: allowlist secret
PRIOR_BLOB = "b7c0149432072d4a3b151d0f9b2c458252e584da"  # pragma: allowlist secret
PRIOR_ORACLE_IDENTITY = "86cd11c2be330f5962982d8d87dfc1847815710868223257529f30bef8cdb500"  # noqa: E501  # pragma: allowlist secret
PRIOR_SCHEMA_VERSION = "5d-representation-schema-10"
PRIOR_SCHEMA_HASH = "c39e3a35e197a1d1db5c2c2b3445ff0cbf03395c91e3426353a4bce589be4be0"  # noqa: E501  # pragma: allowlist secret
PRIOR_ANCHOR_SCHEMAS = [
    "5d-representation-schema-3",
    "5d-representation-schema-5",
    "5d-representation-schema-7",
    "5d-representation-schema-8",
    "5d-representation-schema-9",
    "5d-representation-schema-10",
]
PRIOR_LIFT_IDS = [
    "5d-lift-schema-3-to-4",
    "5d-lift-schema-4-to-5",
    "5d-lift-schema-5-to-6",
    "5d-lift-schema-6-to-7",
    "5d-lift-schema-7-to-8",
    "5d-lift-schema-8-to-9",
    "5d-lift-schema-9-to-10",
]

#: The frozen prior. Byte-identical to the live artifact as it stood before this
#: acceptance, and the file `--verify` compares the merged artifact against. It
#: is never written by this script and is not superseded by this acceptance: it
#: remains the frozen six-batch prior it was created to be, and this script
#: asserts its two identities unchanged in both modes.
FROZEN_PRIOR_PATH = (
    REPO
    / "tests/ingestion/mechanical/data"
    / (
        "accepted_prior_conditions_1_hazards_1_actions_1"
        "_attitudes_1_areas_of_effect_1_cover_1.json"
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
MERGED_CONTENT_SHA256 = "eed7df0476445fc6e5d1d9cd6bdd67977f72372bc67b01808eaa240b69a7e619"  # noqa: E501  # pragma: allowlist secret
MERGED_BLOB = "4fcfab6f667923acbaa98345b56a405061287643"  # pragma: allowlist secret
MERGED_ORACLE_IDENTITY = "d395e4ed79045d0b3ef015240d61fd91445a4b38a77a5f75b0e537ca74eaa29f"  # noqa: E501  # pragma: allowlist secret

#: The **observed execution time** of the acceptance, truncated to the second.
#: Fixed rather than `now()`, because pinning it is what makes the merged
#: artifact reproducible: a wall-clock timestamp would give the same accepted
#: content a different file digest on every run, so the three pins above could
#: never be asserted. It is not invented and it is not a synthetic midnight; its
#: basis is recorded beside it rather than left to be taken on trust.
ACCEPTED_AT = "2026-09-12T18:26:58Z"

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
    "session that ran it, whose local date is 2026-09-12 and whose local time "
    "at the clock read was 11:26:58 - the workstation runs seven hours behind "
    "UTC, and both readings are stated rather than one being reported as the "
    "other."
)

assert ACCEPTED_AT.endswith("Z") and len(ACCEPTED_AT) == 20, ACCEPTED_AT

# --- Expected merged shape, stated before it is computed --------------------
PRIOR_COUNTS = {
    "spans": 558,
    "acceptances": 558,
    "records": 47,
    "components": 136,
    "prose_bindings": 49,
    "relationships": 0,
    "references": 53,
    "provenance": 575,
}
BATCH_COUNTS = {
    "spans": 36,
    "acceptances": 36,
    "records": 1,
    "components": 9,
    "prose_bindings": 0,
    "relationships": 0,
    "references": 9,
    "provenance": 52,
}
MERGED_COUNTS = {k: PRIOR_COUNTS[k] + BATCH_COUNTS[k] for k in PRIOR_COUNTS}
LEAVES = 16

#: Facts are counted **recursively**, over every object in the representation
#: carrying a `family` discriminator, because a fact may be nested inside another
#: fact. A top-level `sum(len(c.facts))` is a different and smaller number in
#: general; for this batch the two agree, which is asserted rather than assumed.
PRIOR_FACTS = 173
BATCH_FACTS = 17
MERGED_FACTS = PRIOR_FACTS + BATCH_FACTS

SPEED_RECORDS = ("glossary.speed",)

#: The nine components this batch adds, by their `(record_key, semantic_key)`
#: pairs, and how many facts each carries. Pinned as a mapping rather than as a
#: total, because "nine components, seventeen facts" is also true of a merge that
#: put the seventeen facts in the wrong nine places.
SPEED_COMPONENT_FACTS = {
    ("glossary.speed", "speed_definition"): 1,
    ("glossary.speed", "movement_allowance"): 1,
    ("glossary.speed", "movement_composition"): 2,
    ("glossary.speed", "movement_depletion"): 1,
    ("glossary.speed", "movement_modes"): 4,
    ("glossary.speed", "special_speeds"): 4,
    ("glossary.speed", "speed_selection"): 2,
    ("glossary.speed", "speed_switch_limit"): 1,
    ("glossary.speed", "speed_change_propagation"): 1,
}

#: The prior's two unresolved citations, what this batch resolves, what it adds,
#: and what survives. Every one of the four sets is stated, because a description
#: would hide which direction the blocker set moved — and here it moves in both
#: directions at once: one target leaves and nine join.
PRIOR_MISSING_REFERENCE_TARGETS = frozenset(
    {"glossary.concentration", "glossary.speed"}
)
RESOLVED_BY_THIS_BATCH = frozenset({"glossary.speed"})
ADDED_BY_THIS_BATCH = frozenset(
    {
        "glossary.burrow_speed",
        "glossary.climb_speed",
        "glossary.climbing",
        "glossary.crawling",
        "glossary.fly_speed",
        "glossary.flying",
        "glossary.jumping",
        "glossary.swim_speed",
        "glossary.swimming",
    }
)
MISSING_REFERENCE_TARGETS = frozenset(
    {
        "glossary.burrow_speed",
        "glossary.climb_speed",
        "glossary.climbing",
        "glossary.concentration",
        "glossary.crawling",
        "glossary.fly_speed",
        "glossary.flying",
        "glossary.jumping",
        "glossary.swim_speed",
        "glossary.swimming",
    }
)
assert (
    PRIOR_MISSING_REFERENCE_TARGETS - RESOLVED_BY_THIS_BATCH
) | ADDED_BY_THIS_BATCH == MISSING_REFERENCE_TARGETS
#: The inherited residue, named separately: `glossary.concentration` is the one
#: target that is neither resolved nor added here. It survives untouched from the
#: prior, and saying so is what keeps "ten unresolved" from reading as ten things
#: this batch did.
INHERITED_RESIDUE = frozenset({"glossary.concentration"})
assert (
    PRIOR_MISSING_REFERENCE_TARGETS - RESOLVED_BY_THIS_BATCH == INHERITED_RESIDUE
)

#: The single inbound citation this acceptance resolves, stated in full. It is
#: the prior's edge, not one this batch emits. Pinned as a 4-tuple so a merge
#: that resolved the target by rewriting the citation instead of by defining the
#: record fails here.
RESOLVING_CITATION = (
    "action.dash",
    "",
    "srd-5.2.1/rules-glossary",
    "Speed",
)

#: The nine citations this batch emits, in full. All record-owned - the empty
#: component key is `RECORD_OWNED_REFERENCE` - and all at the glossary scope, so
#: a merge that attached one to a component or invented a scope fails here rather
#: than passing a count of nine.
EMITTED_CITATIONS = (
    ("glossary.speed", "", "srd-5.2.1/rules-glossary", "Burrow Speed",
     "glossary.burrow_speed"),
    ("glossary.speed", "", "srd-5.2.1/rules-glossary", "Climb Speed",
     "glossary.climb_speed"),
    ("glossary.speed", "", "srd-5.2.1/rules-glossary", "Climbing",
     "glossary.climbing"),
    ("glossary.speed", "", "srd-5.2.1/rules-glossary", "Crawling",
     "glossary.crawling"),
    ("glossary.speed", "", "srd-5.2.1/rules-glossary", "Fly Speed",
     "glossary.fly_speed"),
    ("glossary.speed", "", "srd-5.2.1/rules-glossary", "Flying",
     "glossary.flying"),
    ("glossary.speed", "", "srd-5.2.1/rules-glossary", "Jumping",
     "glossary.jumping"),
    ("glossary.speed", "", "srd-5.2.1/rules-glossary", "Swim Speed",
     "glossary.swim_speed"),
    ("glossary.speed", "", "srd-5.2.1/rules-glossary", "Swimming",
     "glossary.swimming"),
)
assert {c[4] for c in EMITTED_CITATIONS} == ADDED_BY_THIS_BATCH
assert len(EMITTED_CITATIONS) == BATCH_COUNTS["references"]

#: The one reference the source prints across **two** clauses. `Fly Speed` is
#: cited by a sentence that runs over three glossary leaves, and the printed term
#: falls on the seam, so the single reference carries two provenance claims. It
#: is one edge with two witnesses, not two edges: `_validate_provenance` rejects
#: exact duplicate edges only, which is what makes the shape admissible.
SPLIT_REFERENCE = ("Fly Speed", "glossary.fly_speed", ("glossary/5/0", "glossary/6/0"))

#: The registered crossing that carries the schema-10 prior to the schema-11
#: proposal. A table lookup, never a version comparison.
EXPECTED_LIFT_IDS = ["5d-lift-schema-10-to-11"]

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
    ComponentHandling,
    DistanceUnit,
    MovementAllowanceBasis,
    MovementComposition,
    MovementDepletionResolution,
    MovementDepletionTerminator,
    MovementMode,
    MovementWindow,
    SpecialSpeedListing,
    SpeedPropagationDuration,
    SpeedPropagationMagnitude,
    SpeedPropagationScope,
    SpeedSelection,
    SpeedSwitchAccounting,
    SpeedSwitchOutcome,
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

# It holds the six previously accepted batches, and only those.
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

#: The prior's two unresolved citations, stated **before** the merge, so what
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
#: than after the fact: exactly one edge targets `glossary.speed`, it comes from
#: `action.dash`, and the prior defines no such record. Asserting it here is what
#: makes "the Dash citation of Speed resolves" a statement about a specific
#: pre-existing edge rather than about a count that happened to move.
PRIOR_SPEED_CITATIONS = [
    (
        ref.from_record_key,
        ref.from_component_key,
        ref.scope_key,
        ref.source_text,
    )
    for ref in PRIOR.oracle.representation.references
    if ref.target_record_key == "glossary.speed"
]
assert PRIOR_SPEED_CITATIONS == [RESOLVING_CITATION], PRIOR_SPEED_CITATIONS
assert "glossary.speed" not in _prior_record_keys

#: And the prior names none of the nine entries this batch cites. Asserted so
#: "nine targets joined the blocker set" is a statement about nine genuinely new
#: keys rather than about records the prior already had under another name.
assert not (ADDED_BY_THIS_BATCH & _prior_record_keys), sorted(
    ADDED_BY_THIS_BATCH & _prior_record_keys
)
assert not (
    ADDED_BY_THIS_BATCH & set(PRIOR_UNRESOLVED_REFERENCES)
), sorted(ADDED_BY_THIS_BATCH & set(PRIOR_UNRESOLVED_REFERENCES))

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
# frozen six-batch fixture as its review prior and the live oracle only as a
# sentinel it asserts unmodified, so executing it here changes no authority —
# including after this acceptance, which is why `--verify` does not need it.

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
    os.environ["SPEED1_RERUN"] = "1"
    _generated = runpy.run_path(str(GENERATOR), run_name="__speed1_accept__")
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
#: Glossary `Speed` entry and the Combat chapter's movement section — which is
#: what the cross-site provenance shape rests on. Recovered from the manifest,
#: which records each clause's site, rather than from the audit.
MANIFEST_SITES = sorted({str(row["site"]) for row in MANIFEST["clauses"]})
assert MANIFEST_SITES == ["combat", "glossary"], MANIFEST_SITES

#: What the retained review evidence recorded, checked against what this script
#: derived on its own. No committed repository review probe exists for this
#: batch, so the cross-check subject is the committed audit — a tracked
#: repository file, pinned by digest above. It carries no accepted scope and is
#: never used to build one; it is compared on identity, schema, prior digests,
#: counts, dispositions, the obligation tally, the reference scope and the
#: succession step. Reported as a dict so a mismatch names the field rather than
#: only failing.
_audit = json.loads(AUDIT_FILE.read_text(encoding="utf-8"))
_audit_counts = _audit["counts"]
_audit_prior = _audit["accepted_prior"]
_audit_refs = _audit["reference_scope"]
_audit_tally = _audit["obligation_accounting"]
MATCHES_RETAINED_AUDIT = {
    "proposal_identity": _audit["proposal_identity"] == PROPOSAL_IDENTITY,
    "schema": _audit["representation_schema"]
    == {
        "version": SCHEMA_VERSION,
        "hash": SCHEMA_HASH,
    },
    "prior_sha256": _audit_prior["content_sha256_before"] == PRIOR_CONTENT_SHA256,
    "prior_blob": _audit_prior["blob"] == PRIOR_BLOB,
    "prior_identity": _audit_prior["identity"] == PRIOR_ORACLE_IDENTITY,
    "prior_batch_ids": _audit_prior["batches"] == PRIOR_BATCH_IDS,
    "prior_spans": _audit_prior["spans"] == PRIOR_COUNTS["spans"],
    "prior_obligations": _audit_prior["obligations"] == PRIOR_COUNTS["records"],
    "prior_unchanged_by_the_review_run": _audit_prior["unchanged"] is True,
    "spans": _audit_counts["spans"] == BATCH_COUNTS["spans"],
    "clauses": _audit_counts["clauses"] == BATCH_COUNTS["spans"],
    "records": _audit_counts["records"] == BATCH_COUNTS["records"],
    "components": _audit_counts["components"] == BATCH_COUNTS["components"],
    "facts": _audit_counts["facts"] == BATCH_FACTS,
    "prose_bindings": (
        _audit_counts["prose_bindings"] == BATCH_COUNTS["prose_bindings"]
    ),
    "references": _audit_counts["references"] == BATCH_COUNTS["references"],
    "relationships": _audit_counts["relationships"] == BATCH_COUNTS["relationships"],
    "provenance": _audit_counts["provenance"] == BATCH_COUNTS["provenance"],
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
        and _audit_tally["typed"] == 11
        and _audit_tally["typed_at_component_scope"] == 5
        and _audit_tally["supporting_authority_record_owned"] == 10
        and _audit_tally["supporting_authority_reference_owned"] == 5
        and _audit_tally["supporting_authority_bounding_a_fact"] == 5
    ),
    "unresolved_before": (
        sorted(_audit_refs["unresolved_targets_before_this_batch"])
        == sorted(PRIOR_MISSING_REFERENCE_TARGETS)
    ),
    "unresolved_after": (
        sorted(_audit_refs["unresolved_targets_after_the_merge"])
        == sorted(MISSING_REFERENCE_TARGETS)
    ),
    "resolved_by_this_batch": (
        sorted(_audit_refs["resolved_by_this_batch"])
        == sorted(RESOLVED_BY_THIS_BATCH)
    ),
    "resolving_citation": (
        _audit_refs["resolving_citation"]
        == {
            "from_record_key": RESOLVING_CITATION[0],
            "from_component_key": RESOLVING_CITATION[1],
            "scope_key": RESOLVING_CITATION[2],
            "source_text": RESOLVING_CITATION[3],
            "target_record_key": "glossary.speed",
        }
    ),
    "emits_nine_record_owned_references": (
        _audit_refs["references_emitted"] == BATCH_COUNTS["references"]
        and _audit_refs["record_owned"] == BATCH_COUNTS["references"]
        and _audit_refs["targets_defined_by_this_batch"] == []
    ),
    "the_split_reference": (
        _audit_refs["split_across_two_clauses"]
        == [
            {
                "source_text": SPLIT_REFERENCE[0],
                "target_record_key": SPLIT_REFERENCE[1],
                "clauses": list(SPLIT_REFERENCE[2]),
            }
        ]
    ),
    "not_publishable_alone": (
        _audit_refs["publishable_alone"] is False
        and _audit_refs["cross_batch_citations_all_resolve_into_the_accepted_prior"]
        is False
    ),
    "succession_step": _audit["schema_succession"]["steps"] == EXPECTED_LIFT_IDS,
    "no_open_schema_stop": _audit["review_disposition"]["open_schema_stops"] == [],
}
assert all(MATCHES_RETAINED_AUDIT.values()), {
    k: v for k, v in MATCHES_RETAINED_AUDIT.items() if not v
}


# ---------------------------------------------------------------------------
# 3. The acceptance action
# ---------------------------------------------------------------------------

#: Every figure the rule states is re-derived from the retained evidence rather
#: than typed, because the rule is baked into the accepted bytes: a wrong number
#: here cannot be corrected without reverting the acceptance. The assertions run
#: before `accept_proposal` is called.
assert DISPOSITIONS["substantive"] == 16, DISPOSITIONS
assert DISPOSITIONS["supporting_authority"] == 20, DISPOSITIONS
assert _audit_counts["source_sites"] == 2, _audit_counts
assert _audit_counts["cross_leaf_sentences"] == 3, _audit_counts
assert _audit["schema_extension"]["new_fact_families"] == [
    "movement_composition",
    "movement_depletion",
    "special_speed",
    "speed_change_propagation",
    "speed_definition",
    "speed_selection",
    "speed_switch_limit",
], _audit["schema_extension"]["new_fact_families"]
assert _audit["schema_extension"]["new_vocabularies"]["count"] == 11
assert (
    len(_audit["schema_extension"]["new_vocabularies"]["members"]) == 11
), _audit["schema_extension"]["new_vocabularies"]

#: The one member admitted into an already-accepted vocabulary, and the one
#: clause that witnesses it. Pinned as a pair, because "one member added" is also
#: true of a widening justified by a clause that does not print the term.
assert _audit["schema_extension"]["accepted_vocabulary_widened"][
    "members_added_here"
] == ["jump"]
assert _audit["schema_extension"]["accepted_vocabulary_widened"][
    "witness_clauses"
] == ["combat/3/0"]
assert sorted(
    _audit["schema_extension"]["accepted_vocabulary_widened"]["MovementMode"]
) == sorted(m.value for m in MovementMode)

#: No accepted family changed shape in a way any accepted fact can observe. The
#: one field schema 11 adds to an accepted family — `movement_allowance.window` —
#: is optional and defaults to `None`, and the audit records which accepted
#: instances that touches. Asserted here rather than asserted in prose only,
#: because "the prior is carried unchanged" is the whole claim of the lift.
assert _audit["schema_extension"]["accepted_families_changed"] == []
assert sorted(
    _audit["schema_extension"]["accepted_families_reused_unchanged"]
) == ["movement_allowance", "movement_permission"]

#: The two intrinsic invariants this schema declares, both on the new
#: `movement_depletion` family. Named by id, so a schema that declared a
#: different pair — or one — fails here rather than passing a count of two.
assert [
    inv["id"] for inv in _audit["schema_extension"]["intrinsic_invariants_declared"]
] == [
    "movement_depletion.until.at-least-one",
    "movement_depletion.until.no-repeats",
], _audit["schema_extension"]["intrinsic_invariants_declared"]
assert all(
    inv["locus"] == "fact:movement_depletion"
    for inv in _audit["schema_extension"]["intrinsic_invariants_declared"]
)

#: The rule below names the six gaps by the checkpoint's own labels. `gaps_closed`
#: is the set closed; `schema_stops` is the set of stops still *open*, and it is
#: empty, which is why the rule says closed rather than found.
assert _audit["gaps_closed"] == ["G1", "G2", "G3", "G4", "G5", "G6"], _audit[
    "gaps_closed"
]
assert sorted(_audit["gap_witnesses"]) == _audit["gaps_closed"]
assert all(_audit["gap_witnesses"][g] for g in _audit["gaps_closed"])
assert _audit["schema_stops"] == [], _audit["schema_stops"]

#: The rule states the obligation split in prose; the audit's accounting is the
#: source of those five numbers, and unlike earlier batches the five keys *are*
#: the tally — there is no nested sub-key and no prose-bound or unresolved list,
#: because this batch has neither.
assert _audit_tally == {
    "typed": 11,
    "typed_at_component_scope": 5,
    "supporting_authority_record_owned": 10,
    "supporting_authority_reference_owned": 5,
    "supporting_authority_bounding_a_fact": 5,
}, _audit_tally
assert sum(_audit_tally.values()) == BATCH_COUNTS["spans"], _audit_tally
assert BATCH_COUNTS["prose_bindings"] == 0

RULE = (
    f"Owner authorization recorded at {ACCEPTED_AT}, verbatim: {AUTHORIZATION!r} "
    f"Applied to CRD Issue 5d batch {BATCH_ID}, proposal identity "
    f"{PROPOSAL_IDENTITY} under representation schema {SCHEMA_VERSION} over 5c "
    f"release {PRIOR.oracle.binding.package_uuid}/"
    f"{PRIOR.oracle.binding.release_version}. The scope is the complete "
    "proposed span set and nothing outside it: 36 spans over 16 represented 5c "
    "leaves and 1 record - the Speed glossary rule, stated at both of the two "
    "sites that print it, the Rules Glossary entry and the Combat chapter's "
    "movement section - with 16 substantive and 20 supporting-authority "
    "dispositions, and zero unresolved and zero non-mechanical. All 36 source "
    "obligations are discharged by carriage rather than by assertion: 11 typed, "
    "5 typed at component scope, 0 prose-bound and 20 supporting-authority-only "
    "(10 record-owned, 5 reference-owned and 5 bounding a fact). The six "
    "representation gaps the discovery checkpoint found - G1 what a Speed is, "
    "G2 the per-turn movement allowance, G3 depletion, G4 multi-speed selection "
    "and mid-move switching, G5 propagation of a Speed change to every special "
    "speed, and G6 special speed as a named category with the printed mode "
    "list, each witnessed by at least one clause in this batch - were all "
    "closed at representation schema 11 before review, by adding seven fact "
    "families over eleven new closed vocabularies and admitting the single "
    "member 'jump' into the accepted MovementMode vocabulary, whose witness is "
    "combat/3/0. One optional field, movement_allowance.window, is added to an "
    "accepted family; it defaults to None, no accepted fact carries it, and "
    "every accepted fact key, component key and provenance coordinate keeps the "
    "canonical form it had under schema 10. No field is made required or "
    "nullable on any accepted family and no ownership form changes. The schema "
    "declares two intrinsic invariants, both on movement_depletion.until: at "
    "least one terminator, and no terminator twice. The prior accepted "
    "schema-10 authority is carried forward by the single registered lift "
    "5d-lift-schema-10-to-11. The residue moves in both directions here and "
    "both directions are recorded. This acceptance resolves one citation the "
    "prior could not: Dash's printed Speed citation now has the record it "
    "names. It emits nine outgoing citations of its own - Burrow Speed, Climb "
    "Speed, Climbing, Crawling, Fly Speed, Flying, Jumping, Swim Speed and "
    "Swimming - each a record-owned reference to a glossary entry no accepted "
    "batch defines, so the unresolved-target set goes from two to ten. Those "
    "nine are cited, not ingested: no record, component, fact or span is "
    "created for any of them, and no target was invented. "
    "glossary.concentration is untouched and remains the inherited residue it "
    "was. All ten remain publication blockers until the batches that define "
    "them are accepted. The one record carries nine components and seventeen "
    "facts, all structured and none prose-bound; one reference, Fly Speed, is "
    "printed across two clauses and so carries two provenance claims as a "
    "single edge. Schema 11 names Speed; it supplies no runtime movement and no "
    "geometry - nothing here measures a distance, tracks a remaining allowance, "
    "subtracts what a creature has already moved, or converts a Speed into "
    "squares, and DistanceUnit.FOOT reproduces the printed unit rather than a "
    "grid. Recorded by an agent executing this authorization; the decision is "
    "the Owner's and the execution is not a review."
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
#: the reviewed proposal proposed — so the diff records what review changed
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
# beside them, never in place of them: 558 acceptance records with a rewritten
# reviewer is still 558.
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
    #: Unlike `cover-1`, the reference collection is **not** unchanged here: this
    #: batch emits nine citations of its own. So the claim is preservation, not
    #: identity — every one of the prior's 53 references survives element for
    #: element, and the merged collection is exactly those 53 plus this batch's
    #: nine. Asserting equality here would be false; asserting only the count
    #: would let a rewritten prior edge pass.
    "prior_references_preserved": all(
        ref in _merged_representation_payload["references"]
        for ref in PRIOR_PAYLOAD["representation"]["references"]
    ),
    "merged_references_are_prior_plus_this_batch": (
        len(_merged_representation_payload["references"])
        == PRIOR_COUNTS["references"] + BATCH_COUNTS["references"]
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
assert PRESERVATION["prior_references_preserved"], "a prior reference moved"
assert PRESERVATION["merged_references_are_prior_plus_this_batch"]

#: The frozen six-batch prior is not superseded by this acceptance and is not
#: written by it. Asserted in both modes, because a script that quietly refreshed
#: the fixture it verifies against would verify nothing.
_frozen_raw, _frozen_content, _frozen_blob = _identifiers(FROZEN_PRIOR_PATH)
FROZEN_PRIOR_UNTOUCHED = (
    _frozen_content == PRIOR_CONTENT_SHA256 and _frozen_blob == PRIOR_BLOB
)
assert FROZEN_PRIOR_UNTOUCHED, (_frozen_content, _frozen_blob)

# --- Schema anchors and the registered 10 -> 11 succession ------------------
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
assert [a["schema_version"] for a in ANCHORS[:6]] == PRIOR_ANCHOR_SCHEMAS, ANCHORS
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
#: The prior's own 3 -> 4 -> 5 -> 6 -> 7 -> 8 -> 9 -> 10 records are retained and
#: the new crossing is appended, so the artifact carries the whole succession
#: rather than only the last hop.
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
assert set(SPEED_RECORDS) <= _keys, sorted(set(SPEED_RECORDS) - _keys)
assert _keys == _prior_record_keys | set(SPEED_RECORDS), sorted(_keys)
assert {o.record_key for o in RESULT.oracle.obligations} == _keys

#: The batch's typed representation arrived, not merely its spans. Every one of
#: the seventeen facts is probed **by value** below rather than by count: a merge
#: that carried the right number of the wrong facts would pass a count and fail
#: here. The nine components are keyed by `(record_key, semantic_key)`, so a fact
#: landing in the wrong component fails too.
_components = {
    (c.record_key, c.semantic_key): c for c in RESULT.oracle.representation.components
}
_bound = {
    (b.record_key, b.component_key) for b in RESULT.oracle.representation.prose_bindings
}


def _facts_of(semantic_key: str) -> list[object]:
    return list(_components[("glossary.speed", semantic_key)].facts)


#: G1 — what a Speed *is*: a distance in the printed unit, coverable in the
#: creature's own turn. The unit is asserted by value because reproducing the
#: printed unit is exactly the boundary this batch does not cross: no quantity,
#: no conversion and no grid.
_definition = _facts_of("speed_definition")
assert [type(f).__name__ for f in _definition] == ["SpeedDefinitionFact"], _definition
assert _definition[0].unit is DistanceUnit.FOOT
assert _definition[0].window is MovementWindow.OWN_TURN

#: G2 — the per-turn allowance. The accepted `movement_allowance` family is
#: reused rather than duplicated, and this is the first instance to carry the
#: optional `window` field schema 11 adds: the base allowance exists every turn,
#: where Dash's and Ready's instances are grants from another rule and carry no
#: window at all. Both halves are asserted.
_allowance = _facts_of("movement_allowance")
assert [type(f).__name__ for f in _allowance] == ["MovementAllowanceFact"], _allowance
assert _allowance[0].basis is MovementAllowanceBasis.OWN_SPEED
assert _allowance[0].window is MovementWindow.OWN_TURN
assert all(
    f.get("window") is None
    for c in _merged_representation_payload["components"]
    if c["record_key"] != "glossary.speed"
    for f in c["facts"]
    if f.get("family") == "movement_allowance"
), "an accepted movement_allowance fact acquired a window"

#: G3 — depletion. Both printed terminators, in printed order, resolved at
#: whichever comes first. The tuple is compared in order rather than as a set,
#: because the schema's own invariant preserves printed order instead of sorting.
_depletion = _facts_of("movement_depletion")
assert [type(f).__name__ for f in _depletion] == ["MovementDepletionFact"], _depletion
assert _depletion[0].depletes is MovementAllowanceBasis.OWN_SPEED
assert _depletion[0].until == (
    MovementDepletionTerminator.ALLOWANCE_USED_UP,
    MovementDepletionTerminator.DONE_MOVING,
), _depletion[0].until
assert _depletion[0].resolution is MovementDepletionResolution.WHICHEVER_COMES_FIRST

#: G4 — selection and mid-move switching, carried as three separate claims: the
#: two permissions, the switching cost, and the printed floor. The floor is a
#: *prohibition*, not a clamp to zero, which is why `when_nonpositive` names an
#: outcome rather than a number.
_selection = _facts_of("speed_selection")
assert [type(f).__name__ for f in _selection] == ["SpeedSelectionFact"] * 2, _selection
assert {f.permits for f in _selection} == {
    SpeedSelection.CHOOSE_BEFORE_MOVING,
    SpeedSelection.SWITCH_DURING_MOVE,
}, _selection
_switch = _facts_of("speed_switch_limit")
assert [type(f).__name__ for f in _switch] == ["SpeedSwitchLimitFact"], _switch
assert _switch[0].accounting is SpeedSwitchAccounting.SUBTRACT_DISTANCE_ALREADY_MOVED
assert _switch[0].when_nonpositive is SpeedSwitchOutcome.FORBIDS_USING_THE_NEW_SPEED

#: G5 — propagation. All three coordinates are asserted: a change to Speed
#: reaches *every* special speed, by an *equal* amount, for the *same* duration.
#: Dropping any one of them would state a weaker rule than the page prints.
_propagation = _facts_of("speed_change_propagation")
assert [type(f).__name__ for f in _propagation] == [
    "SpeedChangePropagationFact"
], _propagation
assert _propagation[0].to is SpeedPropagationScope.EVERY_SPECIAL_SPEED
assert _propagation[0].magnitude is SpeedPropagationMagnitude.EQUAL_AMOUNT
assert _propagation[0].duration is SpeedPropagationDuration.SAME_DURATION

#: G6, both halves. The four named special speeds carry the open-boundary listing
#: the source prints ("such as"), so the category is named without being closed;
#: and the four movement modes the Combat section prints compose with the regular
#: move or constitute the whole of it. `jump` is the member schema 11 admits into
#: the accepted `MovementMode` vocabulary, asserted present by value here.
_special = _facts_of("special_speeds")
assert [type(f).__name__ for f in _special] == ["SpecialSpeedFact"] * 4, _special
assert {f.mode for f in _special} == {
    MovementMode.BURROW,
    MovementMode.CLIMB,
    MovementMode.FLY,
    MovementMode.SWIM,
}, _special
assert {f.listing for f in _special} == {
    SpecialSpeedListing.NAMED_IN_A_NON_EXHAUSTIVE_LIST
}
_modes = _facts_of("movement_modes")
assert [type(f).__name__ for f in _modes] == ["MovementPermissionFact"] * 4, _modes
assert {f.mode for f in _modes} == {
    MovementMode.CLIMB,
    MovementMode.CRAWL,
    MovementMode.JUMP,
    MovementMode.SWIM,
}, _modes
assert MovementMode.JUMP in {f.mode for f in _modes}
_composition = _facts_of("movement_composition")
assert [type(f).__name__ for f in _composition] == [
    "MovementCompositionFact"
] * 2, _composition
assert {f.composes for f in _composition} == {
    MovementComposition.COMBINED_WITH_REGULAR_MOVEMENT,
    MovementComposition.ENTIRE_MOVE,
}, _composition

SPEED_COMPONENTS = {
    f"{record}/{key}": {
        "handling": _components[(record, key)].handling.value,
        "facts": sorted(type(f).__name__ for f in _components[(record, key)].facts),
        "fact_count": len(_components[(record, key)].facts),
        "prose_bound": (record, key) in _bound,
    }
    for record, key in SPEED_COMPONENT_FACTS
}

#: Whole-batch shape: every component structured, none prose-bound, and the
#: fact-per-component distribution is the pinned mapping rather than a total.
_batch_components = [
    c for c in RESULT.oracle.representation.components if c.record_key in SPEED_RECORDS
]
assert len(_batch_components) == BATCH_COUNTS["components"], len(_batch_components)
assert {c.handling for c in _batch_components} == {ComponentHandling.STRUCTURED}
assert not [c for c in _batch_components if (c.record_key, c.semantic_key) in _bound]
assert {
    (c.record_key, c.semantic_key): len(c.facts) for c in _batch_components
} == SPEED_COMPONENT_FACTS
assert sum(len(c.facts) for c in _batch_components) == BATCH_FACTS
#: Top-level and recursive fact counts agree for this batch, so the seventeen
#: facts carry no nested facts. Asserted rather than assumed, because
#: `_count_facts` is recursive and the two numbers differ in general.
assert (
    _count_facts(
        [
            _merged_representation_payload["components"][i]
            for i, c in enumerate(RESULT.oracle.representation.components)
            if c.record_key in SPEED_RECORDS
        ]
    )
    == BATCH_FACTS
)

#: The provenance shape, measured from the merged artifact rather than read from
#: the audit. Two distinct discharge forms are in play and both are asserted.
#: Seven facts are claimed PRIMARY by the spans that print them — five by one
#: span each and two by three each, which is the eleven typed obligations. The
#: remaining ten facts are not individually claimed: their spans claim the
#: *component* that holds them, which is the five obligations discharged at
#: component scope over three components. A batch that had moved a fact from one
#: form to the other would pass every count above and fail here.
_batch_span_ids = set(RESOLVED_SCOPE)
_primary_spans_per_fact: dict[tuple[str, ...], set[str]] = {}
_primary_spans_per_component: dict[tuple[str, ...], set[str]] = {}
for _edge in RESULT.oracle.representation.provenance:
    if _edge.span_id not in _batch_span_ids or _edge.role.value != "primary":
        continue
    if _edge.target_kind.value == "fact":
        _primary_spans_per_fact.setdefault(tuple(_edge.target_key), set()).add(
            _edge.span_id
        )
    elif _edge.target_kind.value == "component":
        _primary_spans_per_component.setdefault(tuple(_edge.target_key), set()).add(
            _edge.span_id
        )
SHARED_PROVENANCE = sorted(len(spans_) for spans_ in _primary_spans_per_fact.values())
assert SHARED_PROVENANCE == [1, 1, 1, 1, 1, 3, 3], SHARED_PROVENANCE
assert sum(SHARED_PROVENANCE) == _audit_tally["typed"], SHARED_PROVENANCE
COMPONENT_SCOPED_PROVENANCE = {
    "/".join(key): sorted(spans_) for key, spans_ in _primary_spans_per_component.items()
}
assert sorted(_primary_spans_per_component) == [
    ("glossary.speed", "movement_composition"),
    ("glossary.speed", "movement_modes"),
    ("glossary.speed", "special_speeds"),
], sorted(_primary_spans_per_component)
assert (
    sum(len(v) for v in _primary_spans_per_component.values())
    == _audit_tally["typed_at_component_scope"]
), COMPONENT_SCOPED_PROVENANCE
#: Every fact is reachable as PRIMARY exactly once: either on its own or through
#: the component that holds it. Seven plus ten is seventeen, with no overlap.
_component_scoped_facts = sum(
    SPEED_COMPONENT_FACTS[key] for key in _primary_spans_per_component
)
assert len(_primary_spans_per_fact) + _component_scoped_facts == BATCH_FACTS, (
    len(_primary_spans_per_fact),
    _component_scoped_facts,
)
assert not {
    key[:2] for key in _primary_spans_per_fact
} & set(_primary_spans_per_component), "a fact is claimed at both scopes"
assert all(key[0] == "glossary.speed" for key in _primary_spans_per_fact), sorted(
    _primary_spans_per_fact
)

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

# --- Ten source-authored citations still have no target --------------------
#
# Asserted by **set equality on target keys**, not by count, and in both
# directions, because the blocker set moves both ways here: exactly
# `glossary.speed` left it and exactly the nine entries this batch cites joined
# it. A run that showed the set shrinking to one would mean the nine printed
# citations had been dropped; a run that showed `glossary.concentration` gone
# would mean a prior citation had been rewritten.
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
assert (
    set(UNRESOLVED_REFERENCES) & set(PRIOR_UNRESOLVED_REFERENCES) == INHERITED_RESIDUE
), UNRESOLVED_REFERENCES
assert len(REPRESENTATION_FINDINGS) == len(
    MISSING_REFERENCE_TARGETS
), REPRESENTATION_FINDINGS
assert all(
    any(target in finding for target in MISSING_REFERENCE_TARGETS)
    for finding in REPRESENTATION_FINDINGS
), REPRESENTATION_FINDINGS
assert not any(
    "unknown target record glossary.speed" in finding
    for finding in REPRESENTATION_FINDINGS
), REPRESENTATION_FINDINGS

#: **The resolution, stated as a property of the surviving edge.** The prior's
#: single citation of `glossary.speed` is still there, unchanged in every field,
#: and now points at a record the artifact defines. It is the same shape
#: `cover-1` had: a record arrived, no citation was rewritten.
RESOLVED_CITATIONS = [
    (
        ref.from_record_key,
        ref.from_component_key,
        ref.scope_key,
        ref.source_text,
    )
    for ref in RESULT.oracle.representation.references
    if ref.target_record_key == "glossary.speed"
]
assert RESOLVED_CITATIONS == [RESOLVING_CITATION], RESOLVED_CITATIONS
assert "glossary.speed" in _keys

#: **The nine outgoing citations, in full.** Compared as sorted 5-tuples rather
#: than by count, so a merge that kept nine references but changed a target key,
#: a scope or an owner fails here. All nine are record-owned — the empty
#: component key — which is what makes them citations the Speed record makes
#: rather than claims some component of it makes.
BATCH_CITATIONS = sorted(
    (
        ref.from_record_key,
        ref.from_component_key,
        ref.scope_key,
        ref.source_text,
        ref.target_record_key,
    )
    for ref in RESULT.oracle.representation.references
    if ref.from_record_key in set(SPEED_RECORDS)
)
assert BATCH_CITATIONS == sorted(EMITTED_CITATIONS), BATCH_CITATIONS
assert {c[1] for c in BATCH_CITATIONS} == {""}, BATCH_CITATIONS
assert len(RESULT.oracle.representation.references) == (
    PRIOR_COUNTS["references"] + BATCH_COUNTS["references"]
)

#: **The split citation.** `Fly Speed` falls on the seam of a sentence that runs
#: across three glossary leaves, so the one reference carries two provenance
#: claims, at the two clauses the printed term spans. Asserted by clause id — the
#: manifest's own coordinates, translated to span ids the same way the scope was
#: — rather than by a count of two, which a pair of unrelated witnesses would
#: also satisfy.
_clause_to_span = {
    str(row["clause_id"]): derive_span_id(
        str(row["leaf_id"]), int(row["char_start"]), int(row["char_end"])
    )
    for row in MANIFEST["clauses"]
}
_split_target = SPLIT_REFERENCE[1]
_split_spans = sorted(
    _edge.span_id
    for _edge in RESULT.oracle.representation.provenance
    if _edge.target_kind.value == "reference"
    and _edge.target_key[-1] == _split_target
    and _edge.span_id in _batch_span_ids
)
assert _split_spans == sorted(
    _clause_to_span[c] for c in SPLIT_REFERENCE[2]
), _split_spans
SPLIT_REFERENCE_WITNESSES = list(SPLIT_REFERENCE[2])
#: And it is one edge, not two: `_validate_provenance` rejects exact duplicate
#: edges only, which is what makes two witnesses for one reference admissible.
assert (
    len(
        [
            ref
            for ref in RESULT.oracle.representation.references
            if ref.target_record_key == _split_target
        ]
    )
    == 1
), _split_target

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
        "an independent Codex semantic review of the reviewed head, which "
        "returned no blocking finding - not a repository file, not read by this "
        "script, and named rather than cited"
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
    "schema_extension": {
        "new_fact_families": _audit["schema_extension"]["new_fact_families"],
        "new_vocabularies": _audit["schema_extension"]["new_vocabularies"]["count"],
        "accepted_vocabulary_widened": {
            "MovementMode": ["jump"],
            "witness_clauses": ["combat/3/0"],
        },
        "optional_field_added_to_an_accepted_family": "movement_allowance.window",
        "accepted_families_changed": _audit["schema_extension"][
            "accepted_families_changed"
        ],
        "intrinsic_invariants_declared": [
            inv["id"]
            for inv in _audit["schema_extension"]["intrinsic_invariants_declared"]
        ],
    },
    "scope": {
        "spans": len(RESOLVED_SCOPE),
        "leaves": LEAVES,
        "records": len(SPEED_RECORDS),
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
    "frozen_six_batch_prior_untouched": FROZEN_PRIOR_UNTOUCHED,
    "speed_components": SPEED_COMPONENTS,
    "primary_spans_per_fact": SHARED_PROVENANCE,
    "component_scoped_primary_spans": COMPONENT_SCOPED_PROVENANCE,
    "obligation_accounting": _audit_tally,
    "round_trip": ROUND_TRIP,
    "validate_acceptance": ACCEPTANCE_FINDINGS,
    "validate_representation": REPRESENTATION_FINDINGS,
    "publication_blockers": {
        "unresolved_before": PRIOR_UNRESOLVED_REFERENCES,
        "resolved_by_this_batch": sorted(RESOLVED_BY_THIS_BATCH),
        "added_by_this_batch": sorted(ADDED_BY_THIS_BATCH),
        "inherited_residue": sorted(INHERITED_RESIDUE),
        "unresolved_reference_targets": UNRESOLVED_REFERENCES,
        "still_blocked": bool(UNRESOLVED_REFERENCES),
        "resolving_citation": list(RESOLVING_CITATION),
        "note": (
            "accepted, not publishable, and the residue moved in both "
            "directions. This batch resolved the prior's Dash-to-Speed citation "
            "by defining the record, and emitted nine citations of its own to "
            "glossary entries no accepted batch defines, so the unresolved set "
            "went from two to ten. The nine are cited, not ingested: no record, "
            "component, fact or span was created for any of them and no target "
            "was invented. glossary.concentration is untouched and remains the "
            "inherited residue it was."
        ),
    },
    "batch_references": BATCH_CITATIONS,
    "split_reference_witnesses": SPLIT_REFERENCE_WITNESSES,
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
        "a seven-batch frozen prior fixture",
        "the nine cited glossary entries, and any further movement batch",
        "runtime movement or geometry of any kind",
        "full-corpus completion is not claimed",
        "#137 remains in progress",
    ],
}

print(json.dumps(REPORT, indent=1))
