"""Owner acceptance of CRD Issue 5d batch `attitudes-1` — the executable record.

On 2026-09-10 the Owner accepted the reviewed proposal
`c571dfd6b829852e58ca066f8735b6d5944cb51c0f4b42c82052d876392bff22` exactly as
represented, in these words:

    "I accept all 24 spans and the complete representation of proposal
    c571dfd6b829852e58ca066f8735b6d5944cb51c0f4b42c82052d876392bff22 as batch
    attitudes-1, extending the preserved prior through the registered schema
    transitions."

**The decision is the Owner's; this script is only its execution.** Nothing here
reviews anything. It re-derives the exact object the Owner named, calls the one
native acceptance seam, and asserts that what landed on disk is what was
authorized and nothing else. The reviewer recorded in the artifact is therefore
the Owner, not the agent that ran this file.

It is an **acceptance** operation, not a regeneration and not a semantic
revision. It changes no proposal, no audit, no schema, no policy, and nothing
under `src/` except the one accepted-authority artifact it is authorized to
extend. It does not hand-convert the proposal JSON into accepted authority — the
reviewed `MechanicalProposal` is rebuilt by executing the reviewed generator and
its identity and payload hash are asserted before acceptance. It does not create
a second oracle file; the resolver refuses two artifacts claiming one release, so
this batch *extends* the existing one. It does not publish, activate, or retire
anything, and it closes nothing.

Re-running it is refused once the acceptance exists, and refused early: in
acceptance mode the prior is the **live** artifact, pinned by content digest and
Git blob, so the moment accepted authority moves past this batch the run stops
before the generator executes and long before anything is written. Pass
`--verify` to re-check the post-acceptance assertions against the committed
artifact without attempting the acceptance again; that mode reads the frozen
three-batch fixture as the prior, because after acceptance the live file *is* the
merged result and reading it as "the prior" would make every preservation
comparison compare the artifact to itself.

**What acceptance did not make true.** `actions-1` cited five records no accepted
batch defined. This batch defines three of them — `attitude.friendly`,
`attitude.hostile`, `attitude.indifferent` — and defines neither of the other
two. `glossary.concentration` and `glossary.speed` remain unresolved and remain
publication blockers, asserted below by set equality on target keys and asserted
non-empty: a run reporting zero findings would mean a target had been fabricated.
The prior carried five unresolved citations before this merge and carries exactly
two after it; both sets are asserted, so neither can drift silently.

**There is no review-scope manifest for this batch** of the kind `actions-1` had.
The retained independent-review evidence is a probe document
(`attitudes-1-final-independent-probe.json`) recording the proposal identity, the
proposal, audit and prior digests, the reviewed head and the batch counts — but
no span list. It is cross-checked here on exactly the fields it carries, and the
accepted scope is derived from the proposal itself, never from the probe.
"""

from __future__ import annotations

import hashlib
import json
import os
import runpy
import sys
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
assert HERE.name == "review-notes" and HERE.parent.name == ".claude", HERE
sys.path.insert(0, str(REPO / "src"))

GENERATOR = HERE / "issue-5d-batch-attitudes-1-generator.py"
PROPOSAL_FILE = HERE / "issue-5d-batch-attitudes-1-PROPOSAL.json"
AUDIT_FILE = HERE / "issue-5d-batch-attitudes-1-audit.json"
ACCEPTED_PATH = (
    REPO
    / "src/afterworlds/ingestion/mechanical/oracles"
    / "srd-5-2-1-corpus-36b786d8-fa2.json"
)

#: Historical review evidence, produced during the independent review and **not**
#: the authorization. The Owner's statement quoted in the module docstring is the
#: authorization; this file is part of what the Owner was looking at. It is read
#: here only to cross-check identities this script derives independently, on the
#: fields it actually carries. It holds no span list, so it cannot define — and
#: is never used to build — the accepted scope.
REVIEW_PROBE = Path(
    "C:/Users/raven/.codex/visualizations/2026/09/05"
    "/01a07071-8e0c-7502-b149-77574cc34096/attitudes-1-final-independent-probe.json"
)

for _p in (GENERATOR, PROPOSAL_FILE, AUDIT_FILE, ACCEPTED_PATH):
    assert _p.exists(), _p

# --- The pinned reviewed proposal ------------------------------------------
BATCH_ID = "attitudes-1"
REVIEWER = "Ravenlok (Owner)"
PROPOSAL_IDENTITY = "c571dfd6b829852e58ca066f8735b6d5944cb51c0f4b42c82052d876392bff22"  # noqa: E501  # pragma: allowlist secret
PROPOSAL_CONTENT_SHA256 = "b310565f60374e8d169ceb992fb73e6c9f82768ee7664673c48bd56180d80763"  # noqa: E501  # pragma: allowlist secret
AUDIT_CONTENT_SHA256 = "d59ced7472fb21491ecf5e32233dd5121bbf83d4815c8b7841ed8b58dfd80a8c"  # noqa: E501  # pragma: allowlist secret
SCHEMA_VERSION = "5d-representation-schema-8"
SCHEMA_HASH = "8a125f6c4c9929109879ad98a8f14a4ec1d0c7f5fe56fe4f894dafbdf707afff"  # noqa: E501  # pragma: allowlist secret
REVIEWED_HEAD = "1e6ecc95d0c830f4357de4c55502a51a606ffb7c"  # pragma: allowlist secret

#: The Owner's authorization, verbatim. Retained in the batch rule below so the
#: artifact carries the actual words the decision was made in, rather than a
#: paraphrase written by the process that executed it.
AUTHORIZATION = (
    "I accept all 24 spans and the complete representation of proposal "
    "c571dfd6b829852e58ca066f8735b6d5944cb51c0f4b42c82052d876392bff22 as batch "
    "attitudes-1, extending the preserved prior through the registered schema "
    "transitions."
)

# --- The prior accepted authority, by the identities that survive a checkout -
#: Canonical order, which is the order the loaded artifact holds the batches in.
#: Not acceptance order — that is `PRIOR_ANCHOR_ORDER`, and the two differ here
#: for the first time, because `actions-1` was accepted last but sorts first.
PRIOR_BATCH_IDS = ["actions-1", "conditions-1", "hazards-1"]
PRIOR_ANCHOR_ORDER = ["conditions-1", "hazards-1", "actions-1"]
PRIOR_CONTENT_SHA256 = "87864b6ac81e4f8baf57eddf9524dade1b2045a5fc804c79b3d57412c87f46fc"  # noqa: E501  # pragma: allowlist secret
PRIOR_BLOB = "a729a797594e1156b279fac76c3073c733707a2f"  # pragma: allowlist secret
PRIOR_ORACLE_IDENTITY = "8c41b01e92878c614fad5c039c006c66221a4cc55cfab68698ef9302865a6eee"  # noqa: E501  # pragma: allowlist secret
PRIOR_SCHEMA_VERSION = "5d-representation-schema-7"
PRIOR_SCHEMA_HASH = "80e853ef9433ba2e7232c384a7192235692463c9954f5ff766be1fafade6f43d"  # noqa: E501  # pragma: allowlist secret
PRIOR_ANCHOR_SCHEMAS = [
    "5d-representation-schema-3",
    "5d-representation-schema-5",
    "5d-representation-schema-7",
]
PRIOR_LIFT_IDS = [
    "5d-lift-schema-3-to-4",
    "5d-lift-schema-4-to-5",
    "5d-lift-schema-5-to-6",
    "5d-lift-schema-6-to-7",
]

#: The frozen prior. Byte-identical to the live artifact as it stood before this
#: acceptance, and the file `--verify` compares the merged artifact against. It
#: is never written by this script and is not superseded by this acceptance: it
#: remains the frozen three-batch prior it was created to be, and this script
#: asserts its two identities unchanged in both modes.
FROZEN_PRIOR_PATH = (
    REPO
    / "tests/ingestion/mechanical/data"
    / "accepted_prior_conditions_1_hazards_1_actions_1.json"
)

#: The merged artifact of record. Pinned by three identities that fail for three
#: different reasons: the oracle identity covers accepted *content*, while the
#: canonical content digest and the Git blob additionally cover the acceptance
#: **evidence** - reviewer, timestamp, batch rule, resolved scope, anchors and
#: lifts - which the oracle identity deliberately excludes, because re-reviewing
#: an unchanged classification must not remint a projection.
#:
#: These three could not be stated before the acceptance ran, because they are
#: properties of an output that did not exist yet. They were pinned from the
#: first run's report, and every run of either mode asserts them from here on:
#: `--verify` is what proves they still hold of the committed artifact.
MERGED_CONTENT_SHA256 = "fd390d95dde74498142035d9dde00ccf7effadb372fc13f9662154841bb787ab"  # noqa: E501  # pragma: allowlist secret
MERGED_BLOB = "2346404005618b0389b4e4f66d2e96c5c35b200f"  # pragma: allowlist secret
MERGED_ORACLE_IDENTITY = "c3b4d4b759441b05418fcbe1d90811e0d7c2535319aa005e64201ce29b5c74fa"  # noqa: E501  # pragma: allowlist secret

#: The **observed execution time** of the acceptance, truncated to the second.
#: Fixed rather than `now()`, because pinning it is what makes the merged
#: artifact reproducible: a wall-clock timestamp would give the same accepted
#: content a different file digest on every run, so the three pins above could
#: never be asserted. It is not invented and it is not a synthetic midnight; its
#: basis is recorded beside it rather than left to be taken on trust.
ACCEPTED_AT = "2026-09-10T18:53:49Z"

#: How that time is known.
ACCEPTED_AT_BASIS = (
    "A UTC clock read taken in the same shell invocation that ran this script, "
    "immediately before the run, truncated - not rounded - to the second, and "
    "written into the constant above before the interpreter started. It is not "
    "a wall clock read at replay, and it is not a synthetic date. The write it "
    "authorizes was observed afterwards: the accepted artifact carries "
    "LastWriteTimeUtc 2026-09-10T18:54:19.5767892Z, thirty seconds later, which "
    "is the time the reviewed generator took to re-derive the proposal and the "
    "acceptance seam took to merge and serialize it. The pinned value is "
    "therefore the moment the acceptance was initiated rather than the moment "
    "the bytes landed, and both are recorded here rather than one being passed "
    "off as the other. The Owner's authorization is of the same UTC day, "
    f"{ACCEPTED_AT[:10]}."
)

assert ACCEPTED_AT.endswith("Z") and len(ACCEPTED_AT) == 20, ACCEPTED_AT

# --- Expected merged shape, stated before it is computed --------------------
PRIOR_COUNTS = {
    "spans": 463,
    "acceptances": 463,
    "records": 35,
    "components": 106,
    "prose_bindings": 47,
    "relationships": 0,
    "references": 39,
    "provenance": 480,
}
BATCH_COUNTS = {
    "spans": 24,
    "acceptances": 24,
    "records": 4,
    "components": 3,
    "prose_bindings": 2,
    "relationships": 0,
    "references": 7,
    "provenance": 24,
}
MERGED_COUNTS = {k: PRIOR_COUNTS[k] + BATCH_COUNTS[k] for k in PRIOR_COUNTS}
LEAVES = 16

#: Facts are counted **recursively**, over every object in the representation
#: carrying a `family` discriminator, because a fact may be nested inside another
#: fact. A top-level `sum(len(c.facts))` is a different and smaller number, and
#: is not the metric the batch checkpoints state.
PRIOR_FACTS = 139
BATCH_FACTS = 3
MERGED_FACTS = PRIOR_FACTS + BATCH_FACTS

ATTITUDE_RECORDS = (
    "attitude.friendly",
    "attitude.hostile",
    "attitude.indifferent",
    "glossary.attitude",
)

#: The five source-authored citations the prior could not resolve, and the two
#: that survive this acceptance. Both sets are stated, so "three were resolved"
#: is measured against a known start rather than asserted, and so a run that
#: resolved anything beyond the three records this batch defines would fail.
PRIOR_MISSING_REFERENCE_TARGETS = frozenset(
    {
        "attitude.friendly",
        "attitude.hostile",
        "attitude.indifferent",
        "glossary.concentration",
        "glossary.speed",
    }
)
MISSING_REFERENCE_TARGETS = frozenset({"glossary.concentration", "glossary.speed"})
RESOLVED_BY_THIS_BATCH = frozenset(
    {"attitude.friendly", "attitude.hostile", "attitude.indifferent"}
)
assert (
    PRIOR_MISSING_REFERENCE_TARGETS - RESOLVED_BY_THIS_BATCH
    == MISSING_REFERENCE_TARGETS
)

#: The registered crossing that carries the schema-7 prior to the schema-8
#: proposal. A table lookup, never a version comparison.
EXPECTED_LIFT_IDS = ["5d-lift-schema-7-to-8"]

from afterworlds.ingestion.corpus.hashing import hash_obj  # noqa: E402
from afterworlds.ingestion.corpus.pipeline import build_candidate  # noqa: E402
from afterworlds.ingestion.corpus.policy import exclusion_reason_for  # noqa: E402
from afterworlds.ingestion.corpus.reconcile import _full_coverage_edges  # noqa: E402
from afterworlds.ingestion.mechanical.acceptance import accept_proposal  # noqa: E402
from afterworlds.ingestion.mechanical.accounting import (  # noqa: E402
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
    accepted_inputs_payload,
    load_accepted_inputs,
    oracle_identity,
)
from afterworlds.ingestion.mechanical.projection import (  # noqa: E402
    representation_payload,
)
from afterworlds.ingestion.mechanical.proposal import (  # noqa: E402
    proposal_identity,
    proposal_payload,
)
from afterworlds.ingestion.mechanical.representation import (  # noqa: E402
    REPRESENTATION_COLLECTIONS,
    AdvantageState,
    Attitude,
    ComponentHandling,
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


@dataclass(frozen=True)
class _Reviewed:
    """One reviewed span, as the committed proposal states it."""

    span_id: str
    leaf_id: str
    disposition: SemanticDisposition


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

# It holds the three previously accepted batches, and only those.
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

#: The prior's five unresolved citations, stated **before** the merge. Unlike
#: every prior a batch has been accepted over before, this one does not resolve
#: everything it cites: `actions-1` cited records no accepted batch defines.
#: Asserted by set equality, so what this acceptance resolves is measured
#: against a known start rather than described.
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
# frozen three-batch fixture as its review prior and the live oracle only as a
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
    hash_obj(json.loads(PROPOSAL_FILE.read_text(encoding="utf-8")))
    == PROPOSAL_IDENTITY
), "the committed proposal JSON is not the proposal the Owner named"

if not VERIFY_ONLY:
    os.environ["ATTITUDES1_RERUN"] = "1"
    _generated = runpy.run_path(str(GENERATOR), run_name="__attitudes1_accept__")
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

    # --- The scope: every proposed span, in the proposal's own order --------
    RESOLVED_SCOPE = tuple(p.span.span_id for p in PROPOSAL.proposed_spans)
    _spans_reviewed = [p.span for p in PROPOSAL.proposed_spans]
else:
    _committed_proposal = json.loads(PROPOSAL_FILE.read_text(encoding="utf-8"))
    PROPOSAL_PAYLOAD_HASH = hash_obj(_committed_proposal)
    assert PROPOSAL_PAYLOAD_HASH == PROPOSAL_IDENTITY, PROPOSAL_PAYLOAD_HASH
    _proposal_raw_after, _proposal_content_after, _proposal_blob_after = (
        _proposal_raw_before,
        _proposal_content_before,
        _proposal_blob_before,
    )
    _spans_reviewed = [
        _Reviewed(
            span_id=p["span_id"],
            leaf_id=p["leaf_id"],
            disposition=SemanticDisposition(p["disposition"]),
        )
        for p in _committed_proposal["proposed_spans"]
    ]
    RESOLVED_SCOPE = tuple(p.span_id for p in _spans_reviewed)

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

#: What the retained independent-review evidence recorded, checked against what
#: this script derived on its own. The probe carries no span list, so it is
#: cross-checked on identity, digests, reviewed head and counts only. Reported as
#: a dict so a mismatch names the field rather than only failing.
_probe = json.loads(REVIEW_PROBE.read_text(encoding="utf-8"))
_probe_hashes = {Path(k).name: v for k, v in _probe["unchanged_hashes"].items()}
MATCHES_REVIEW_PROBE = {
    "proposal_identity": _probe["proposal_identity"] == PROPOSAL_IDENTITY,
    "proposal_sha256": _probe_hashes[PROPOSAL_FILE.name] == PROPOSAL_CONTENT_SHA256,
    "audit_sha256": _probe_hashes[AUDIT_FILE.name] == AUDIT_CONTENT_SHA256,
    "prior_sha256": _probe_hashes[ACCEPTED_PATH.name] == PRIOR_CONTENT_SHA256,
    "reviewed_head": _probe["head"] == REVIEWED_HEAD,
    "spans": _probe["counts"]["spans"] == BATCH_COUNTS["spans"],
    "records": _probe["counts"]["records"] == BATCH_COUNTS["records"],
    "components": _probe["counts"]["components"] == BATCH_COUNTS["components"],
    "facts": _probe["counts"]["facts"] == BATCH_FACTS,
    "prose_bindings": (
        _probe["counts"]["prose_bindings"] == BATCH_COUNTS["prose_bindings"]
    ),
    "references": _probe["counts"]["references"] == BATCH_COUNTS["references"],
    "provenance": _probe["counts"]["provenance_edges"] == BATCH_COUNTS["provenance"],
    "leaves": _probe["counts"]["represented_leaves"] == LEAVES,
    "dispositions": (
        _probe["counts"]["substantive"] == DISPOSITIONS["substantive"]
        and _probe["counts"]["supporting_authority"]
        == DISPOSITIONS["supporting_authority"]
        and _probe["counts"]["unresolved"] == 0
        and _probe["counts"]["non_mechanical"] == 0
    ),
}
assert all(MATCHES_REVIEW_PROBE.values()), MATCHES_REVIEW_PROBE

# ---------------------------------------------------------------------------
# 3. The acceptance action
# ---------------------------------------------------------------------------

RULE = (
    f"Owner authorization of {ACCEPTED_AT[:10]}, verbatim: {AUTHORIZATION!r} "
    f"Applied to CRD Issue 5d batch {BATCH_ID}, proposal identity "
    f"{PROPOSAL_IDENTITY} under representation schema {SCHEMA_VERSION} over 5c "
    f"release {PRIOR.oracle.binding.package_uuid}/"
    f"{PRIOR.oracle.binding.release_version}. The scope is the complete "
    "proposed span set and nothing outside it: 24 spans over 16 represented 5c "
    "leaves and 4 records — the Attitude umbrella glossary rule and the three "
    "attitude entries Friendly, Hostile and Indifferent — with 5 substantive "
    "and 19 supporting-authority dispositions, and zero unresolved and zero "
    "non-mechanical. Schema stop S-2, the default attitude of a monster, which "
    "no schema-7 family could carry, was closed at representation schema 8 "
    "before review by adding the DefaultAttitudeFact family and the closed "
    "Attitude vocabulary friendly/hostile/indifferent; the prior accepted "
    "schema-7 authority is carried forward by the registered lift "
    "5d-lift-schema-7-to-8. Fifteen source obligations are discharged by "
    "carriage rather than by assertion: 3 typed, 2 prose-bound and 10 "
    "supporting-authority-only. This acceptance resolves three of the five "
    "citations the prior could not resolve — attitude.friendly, "
    "attitude.hostile and attitude.indifferent — which is a consequence of "
    "accepting a complete source class and not the reason for accepting it. "
    "glossary.concentration and glossary.speed are untagged entries in other "
    "source groups, were not resolved by this acceptance, and remain "
    "publication blockers until the batches that define them are accepted. "
    "Disclosed and still deferred: [Area of Effect], the remaining complete "
    "tagged class, on the spatial-geometry family it would require. Recorded "
    "by an agent executing this authorization; the decision is the Owner's and "
    "the execution is not a review."
)

if not VERIFY_ONLY:
    ACCEPTED = accept_proposal(
        PROPOSAL,
        batch_id=BATCH_ID,
        rule=RULE,
        resolved_scope=RESOLVED_SCOPE,
        reviewer=REVIEWER,
        accepted_at=ACCEPTED_AT,
        prior=PRIOR,
    )
    WRITTEN = _write_artifact(ACCEPTED_PATH, accepted_inputs_payload(ACCEPTED))

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
        for coll in REPRESENTATION_COLLECTIONS
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
# beside them, never in place of them: 463 acceptance records with a rewritten
# reviewer is still 463.
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
        for coll in REPRESENTATION_COLLECTIONS
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
}
#: Every element of the prior the merged artifact does not carry, per collection.
#: Reported rather than only asserted, so a failure names what is missing.
MISSING_PRIOR_ELEMENTS = {
    coll: [
        element
        for element in PRIOR_PAYLOAD["representation"][coll]
        if element not in _merged_representation_payload[coll]
    ]
    for coll in REPRESENTATION_COLLECTIONS
}
for _coll in REPRESENTATION_COLLECTIONS:
    if not VERIFY_ONLY:
        # The acceptance seam keeps prior items first, so the in-memory result
        # carries them as a byte-identical prefix. There is no in-memory result
        # under --verify, and the serialized order is canonical rather than
        # prior-first, so this is the one claim that is acceptance-only.
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

#: The frozen three-batch prior is not superseded by this acceptance and is not
#: written by it. Asserted in both modes, because a script that quietly refreshed
#: the fixture it verifies against would verify nothing.
_frozen_raw, _frozen_content, _frozen_blob = _identifiers(FROZEN_PRIOR_PATH)
FROZEN_PRIOR_UNTOUCHED = (
    _frozen_content == PRIOR_CONTENT_SHA256 and _frozen_blob == PRIOR_BLOB
)
assert FROZEN_PRIOR_UNTOUCHED, (_frozen_content, _frozen_blob)

# --- Schema anchors and the registered 7 -> 8 succession --------------------
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
assert [a["schema_version"] for a in ANCHORS[:3]] == PRIOR_ANCHOR_SCHEMAS, ANCHORS
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
#: The prior's own 3 -> 4 -> 5 -> 6 -> 7 records are retained and the new
#: crossing is appended, so the artifact carries the whole succession rather than
#: only the last hop.
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

# --- The attitude records arrived, and the representation with them ---------
_keys = {r.semantic_key for r in RESULT.oracle.representation.records}
assert set(ATTITUDE_RECORDS) <= _keys, sorted(set(ATTITUDE_RECORDS) - _keys)
assert _keys == _prior_record_keys | set(ATTITUDE_RECORDS), sorted(_keys)
assert {o.record_key for o in RESULT.oracle.obligations} == _keys

#: The batch's typed representation arrived, not merely its spans. Schema 8
#: exists for exactly one clause — the default attitude of a monster — so the
#: `DefaultAttitudeFact` carrying `indifferent` is what distinguishes accepted
#: schema-8 *content* from a schema-8 declaration over schema-7 content. The two
#: influence components are checked beside it because they are the boundary the
#: extension did **not** cross: ordinary `AdvantageFact`s over one shared roll,
#: mixed rather than structured, and they are the two that carry prose bindings
#: while the structured default attitude carries none.
_components = {
    (c.record_key, c.semantic_key): c for c in RESULT.oracle.representation.components
}
_bound = {
    (b.record_key, b.component_key)
    for b in RESULT.oracle.representation.prose_bindings
}
_default = _components[("attitude.indifferent", "default_attitude")]
_friendly = _components[("attitude.friendly", "influence_advantage")]
_hostile = _components[("attitude.hostile", "influence_disadvantage")]
SCHEMA_8_COMPONENTS = {
    "attitude.indifferent/default_attitude": {
        "handling": _default.handling.value,
        "facts": [type(f).__name__ for f in _default.facts],
        "attitude": _default.facts[0].attitude.value,
        "prose_bound": ("attitude.indifferent", "default_attitude") in _bound,
    },
    "attitude.friendly/influence_advantage": {
        "handling": _friendly.handling.value,
        "facts": [type(f).__name__ for f in _friendly.facts],
        "state": _friendly.facts[0].state.value,
        "prose_bound": ("attitude.friendly", "influence_advantage") in _bound,
    },
    "attitude.hostile/influence_disadvantage": {
        "handling": _hostile.handling.value,
        "facts": [type(f).__name__ for f in _hostile.facts],
        "state": _hostile.facts[0].state.value,
        "prose_bound": ("attitude.hostile", "influence_disadvantage") in _bound,
    },
}
assert _default.handling is ComponentHandling.STRUCTURED, _default
assert [type(f).__name__ for f in _default.facts] == ["DefaultAttitudeFact"], _default
assert _default.facts[0].attitude is Attitude.INDIFFERENT, _default
assert ("attitude.indifferent", "default_attitude") not in _bound
assert _friendly.handling is ComponentHandling.MIXED
assert _hostile.handling is ComponentHandling.MIXED
assert _friendly.facts[0].state is AdvantageState.ADVANTAGE, _friendly
assert _hostile.facts[0].state is AdvantageState.DISADVANTAGE, _hostile
assert _friendly.facts[0].roll == _hostile.facts[0].roll, "the influence roll differs"
assert ("attitude.friendly", "influence_advantage") in _bound
assert ("attitude.hostile", "influence_disadvantage") in _bound

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
# non-empty. A run reporting zero here would mean a target was fabricated, which
# is a worse outcome than the blocker it would appear to remove. The difference
# against the prior's five is asserted too, so this acceptance is shown to have
# resolved exactly the three records it defines and nothing else.
UNRESOLVED_REFERENCES = sorted(
    {
        ref.target_record_key
        for ref in RESULT.oracle.representation.references
        if ref.target_record_key not in _keys
    }
)
assert set(UNRESOLVED_REFERENCES) == MISSING_REFERENCE_TARGETS, UNRESOLVED_REFERENCES
assert (
    set(PRIOR_UNRESOLVED_REFERENCES) - set(UNRESOLVED_REFERENCES)
    == RESOLVED_BY_THIS_BATCH
), (PRIOR_UNRESOLVED_REFERENCES, UNRESOLVED_REFERENCES)
assert len(REPRESENTATION_FINDINGS) == len(MISSING_REFERENCE_TARGETS), (
    REPRESENTATION_FINDINGS
)
assert all(
    any(target in finding for target in MISSING_REFERENCE_TARGETS)
    for finding in REPRESENTATION_FINDINGS
), REPRESENTATION_FINDINGS

#: Every reference the merge *did* resolve across the batch boundary, in both
#: directions: this batch's entries and umbrella cite `action.influence` from
#: `actions-1`, and `actions-1` cites the three attitude records back. Reported
#: so the two remaining blockers are not the only thing said about references.
_cross_batch_resolved = sorted(
    (ref.from_record_key, ref.target_record_key)
    for ref in RESULT.oracle.representation.references
    if ref.target_record_key in _keys
    and (ref.from_record_key in set(ATTITUDE_RECORDS))
    != (ref.target_record_key in set(ATTITUDE_RECORDS))
)

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
    "proposal_identity": PROPOSAL_IDENTITY,
    "proposal_payload_hash": PROPOSAL_PAYLOAD_HASH,
    "proposal_content_sha256": _proposal_content_after,
    "proposal_blob": _proposal_blob_after,
    "proposal_raw_sha256_diagnostic": _proposal_raw_after,
    "schema": [SCHEMA_VERSION, SCHEMA_HASH],
    "scope": {
        "spans": len(RESOLVED_SCOPE),
        "leaves": LEAVES,
        "records": len(ATTITUDE_RECORDS),
        "dispositions": DISPOSITIONS,
    },
    "matches_review_probe": MATCHES_REVIEW_PROBE,
    "semantic_diff_tally": DIFF_TALLY,
    "merged_counts": MEASURED,
    "merged_facts_recursive": MEASURED_FACTS,
    "batches": [b.batch_id for b in RESULT.batches],
    "schema_anchors": ANCHORS,
    "lifts": LIFTS,
    "preservation": PRESERVATION,
    "frozen_three_batch_prior_untouched": FROZEN_PRIOR_UNTOUCHED,
    "schema_8_components": SCHEMA_8_COMPONENTS,
    "round_trip": ROUND_TRIP,
    "validate_acceptance": ACCEPTANCE_FINDINGS,
    "validate_representation": REPRESENTATION_FINDINGS,
    "publication_blockers": {
        "unresolved_before": PRIOR_UNRESOLVED_REFERENCES,
        "resolved_by_this_batch": sorted(RESOLVED_BY_THIS_BATCH),
        "unresolved_reference_targets": UNRESOLVED_REFERENCES,
        "still_blocked": bool(UNRESOLVED_REFERENCES),
        "note": (
            "accepted, not publishable. These two were not resolved by this "
            "acceptance and no target was invented for them."
        ),
    },
    "cross_batch_references_resolved": _cross_batch_resolved,
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
        "push",
        "merge",
        "closing #137",
        "a four-batch frozen prior fixture",
    ],
}

print(json.dumps(REPORT, indent=1))
