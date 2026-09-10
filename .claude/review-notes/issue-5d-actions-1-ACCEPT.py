"""Owner acceptance of CRD Issue 5d batch `actions-1` — the executable record.

On 2026-09-09 the Owner accepted the reviewed proposal
`62202e9a4b9e0cb539c770e1244b3aa322d8f988e82a544991998fd8fb363b5c` exactly as
represented, in these words:

    "I accept all 182 spans and the complete representation of this exact
    proposal as batch actions-1, extending the preserved prior through the
    registered schema transitions."

**The decision is the Owner's; this script is only its execution.** Nothing here
reviews anything. It re-derives the exact object the Owner named, calls the one
native acceptance seam, and asserts that what landed on disk is what was
authorized and nothing else. The reviewer recorded in the artifact is therefore
the Owner, not the agent that ran this file.

It is an **acceptance** operation, not a regeneration and not a semantic
revision. It changes no proposal, no audit, no schema, no policy, and nothing
under `src/` except the one accepted-authority artifact it is authorized to
extend. Three things it deliberately does not do:

* it does not hand-convert the proposal JSON, rename it as accepted authority,
  or reproduce its contents. The reviewed `MechanicalProposal` is rebuilt by
  executing the reviewed generator, and its identity and payload hash are
  asserted before acceptance. Accepted meaning is never regenerated from a
  builder's output;
* it does not create a second oracle file. The resolver refuses two artifacts
  claiming one release, so this batch *extends* the existing one;
* it does not publish, activate, or retire anything, and it closes nothing.

Re-running it is refused once the acceptance exists: `accept_proposal` rejects a
batch id the prior already records, which is the correct behaviour for a
one-time action. Pass `--verify` to re-check the post-acceptance assertions
against the committed artifact without attempting the acceptance again.

**What acceptance did not make true.** `actions-1` cites five records no
accepted batch defines — `glossary.speed`, `glossary.concentration`,
`attitude.friendly`, `attitude.hostile`, `attitude.indifferent`. Accepting the
batch did not resolve them and did not invent them. They are asserted here, by
set equality on target keys, to be exactly the five `validate_representation`
reports against the merged artifact, and they remain explicit publication
blockers. This script asserts that the merged authority still refuses to
publish; a run that reported zero findings would mean a target had been
fabricated.

`--verify` does **not** re-run the reviewed generator, and that is a separation
of concerns rather than an inability. The two proofs answer different questions:
this script's `--verify` checks the *committed acceptance*, while the reviewed
generator reproduces the *proposal and audit* from the immutable bound corpus.
The prior it compares against is the frozen fixture
`tests/ingestion/mechanical/data/accepted_prior_conditions_1_hazards_1.json`,
byte-identical to the live artifact as it stood before this acceptance — because
after it, the live file *is* the merged result, and reading that and calling it
"the prior" would make every preservation comparison compare the artifact to
itself.
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

GENERATOR = HERE / "issue-5d-actions-1-schema7-PROPOSAL-generator.py"
PROPOSAL_FILE = HERE / "issue-5d-actions-1-schema7-PROPOSAL.json"
AUDIT_FILE = HERE / "issue-5d-actions-1-schema7-audit.json"
ACCEPTED_PATH = (
    REPO
    / "src/afterworlds/ingestion/mechanical/oracles"
    / "srd-5-2-1-corpus-36b786d8-fa2.json"
)

#: Historical review evidence, produced during the semantic review and **not**
#: the authorization. The Owner's statement quoted in the module docstring is
#: the authorization; this file is what the Owner was looking at. It is read
#: here only to cross-check the scope this script derives from the proposal
#: itself, so a manifest that drifted cannot quietly redefine what was accepted.
REVIEW_SCOPE_MANIFEST = Path(
    "C:/Users/raven/.codex/visualizations/2026/09/05"
    "/01a07071-8e0c-7502-b149-77574cc34096/actions-1-schema7-review-scope.json"
)

for _p in (GENERATOR, PROPOSAL_FILE, AUDIT_FILE, ACCEPTED_PATH):
    assert _p.exists(), _p

# --- The pinned reviewed proposal ------------------------------------------
BATCH_ID = "actions-1"
REVIEWER = "Ravenlok (Owner)"
PROPOSAL_IDENTITY = "62202e9a4b9e0cb539c770e1244b3aa322d8f988e82a544991998fd8fb363b5c"  # noqa: E501  # pragma: allowlist secret
PROPOSAL_CONTENT_SHA256 = "e08759e7202793a3fa61b6589f21eb68f1b0fdbb3e39743129918837b2633c03"  # noqa: E501  # pragma: allowlist secret
AUDIT_CONTENT_SHA256 = "a087c17e90271a4a94582cce117b4a3fe521c04559485d6ad85aa6a8e1bbeb72"  # noqa: E501  # pragma: allowlist secret
SCHEMA_VERSION = "5d-representation-schema-7"
SCHEMA_HASH = "80e853ef9433ba2e7232c384a7192235692463c9954f5ff766be1fafade6f43d"  # noqa: E501  # pragma: allowlist secret

#: The Owner's authorization, verbatim. Retained in the batch rule below so the
#: artifact carries the actual words the decision was made in, rather than a
#: paraphrase written by the process that executed it.
AUTHORIZATION = (
    "I accept all 182 spans and the complete representation of this exact "
    "proposal as batch actions-1, extending the preserved prior through the "
    "registered schema transitions."
)

# --- The prior accepted authority, by the identities that survive a checkout -
PRIOR_BATCH_IDS = ["conditions-1", "hazards-1"]
PRIOR_CONTENT_SHA256 = "0925d796a058ff4e64f9a429c9ad73d3c39f1e74dff7e394bc2957c1587e73f7"  # noqa: E501  # pragma: allowlist secret
PRIOR_BLOB = "6e65533f4a3523aba3d60cfc3c274ab22e66b59a"  # pragma: allowlist secret
PRIOR_ORACLE_IDENTITY = "c794bde48a6fbe6c59e5cc901a30f092524fe0ceecdc60b7ba080f11fd356245"  # noqa: E501  # pragma: allowlist secret
PRIOR_SCHEMA_VERSION = "5d-representation-schema-5"
PRIOR_SCHEMA_HASH = "2803840899363988cc2f67e0d9f310d9baffe394d52ca0919d11388bcd7f4c40"  # noqa: E501  # pragma: allowlist secret
PRIOR_ANCHOR_SCHEMAS = ["5d-representation-schema-3", "5d-representation-schema-5"]
PRIOR_LIFT_IDS = ["5d-lift-schema-3-to-4", "5d-lift-schema-4-to-5"]

#: The frozen prior. Byte-identical to the live artifact as it stood before this
#: acceptance, and the file `--verify` compares the merged artifact against.
FROZEN_PRIOR_PATH = (
    REPO
    / "tests/ingestion/mechanical/data"
    / "accepted_prior_conditions_1_hazards_1.json"
)

#: The merged artifact of record. Pinned by three identities that fail for three
#: different reasons: the oracle identity covers accepted *content*, while the
#: canonical content digest and the Git blob additionally cover the acceptance
#: **evidence** - reviewer, timestamp, batch rule, resolved scope, anchors and
#: lifts - which the oracle identity deliberately excludes, because re-reviewing
#: an unchanged classification must not remint a projection.
MERGED_CONTENT_SHA256 = "d247aed8ab98dab8e71da322de224449f0fe7a46b782c6447010f330d8e87987"  # noqa: E501  # pragma: allowlist secret
MERGED_BLOB = "b0bb88a3d1f245141f5c2d60cacb68869ab9440c"  # pragma: allowlist secret
MERGED_ORACLE_IDENTITY = "8c41b01e92878c614fad5c039c006c66221a4cc55cfab68698ef9302865a6eee"  # noqa: E501  # pragma: allowlist secret

#: Fixed, not `now()`. The Owner's decision has a date, and pinning it is what
#: makes the merged artifact reproducible: a wall-clock timestamp would give the
#: same accepted content a different file digest on every run, so the three pins
#: above could never be asserted.
ACCEPTED_AT = "2026-09-09T00:00:00Z"

# --- Expected merged shape, stated before it is computed --------------------
PRIOR_COUNTS = {
    "spans": 281,
    "acceptances": 281,
    "records": 22,
    "components": 69,
    "prose_bindings": 20,
    "relationships": 0,
    "references": 22,
    "provenance": 281,
}
BATCH_COUNTS = {
    "spans": 182,
    "acceptances": 182,
    "records": 13,
    "components": 37,
    "prose_bindings": 27,
    "relationships": 0,
    "references": 17,
    "provenance": 199,
}
MERGED_COUNTS = {k: PRIOR_COUNTS[k] + BATCH_COUNTS[k] for k in PRIOR_COUNTS}
LEAVES = 92
ACTION_RECORDS = (
    "action.attack",
    "action.dash",
    "action.disengage",
    "action.dodge",
    "action.help",
    "action.hide",
    "action.influence",
    "action.magic",
    "action.ready",
    "action.search",
    "action.study",
    "action.utilize",
    "glossary.action",
)

#: The five source-authored citations no accepted batch defines. Acceptance did
#: not resolve them, and nothing here may invent a target for one.
MISSING_REFERENCE_TARGETS = frozenset(
    {
        "attitude.friendly",
        "attitude.hostile",
        "attitude.indifferent",
        "glossary.concentration",
        "glossary.speed",
    }
)

#: The registered crossings that carry the schema-5 prior to the schema-7
#: proposal. A table lookup, never a version comparison.
EXPECTED_LIFT_IDS = ["5d-lift-schema-5-to-6", "5d-lift-schema-6-to-7"]

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
#: the acceptance the prior is the live artifact being extended; afterwards that
#: file is the merged result, so verification reads the frozen fixture instead.
PRIOR_PATH = ACCEPTED_PATH if not VERIFY_ONLY else FROZEN_PRIOR_PATH
_prior_raw_sha, _prior_content_sha, _prior_blob = _identifiers(PRIOR_PATH)

#: Asserted in **both** modes against the same two pinned values, because the
#: frozen fixture is byte-identical to the pre-acceptance artifact. There is one
#: prior identity, not two.
assert _prior_content_sha == PRIOR_CONTENT_SHA256, (PRIOR_PATH, _prior_content_sha)
assert _prior_blob == PRIOR_BLOB, (PRIOR_PATH, _prior_blob)

PRIOR = load_accepted_inputs(PRIOR_PATH)
PRIOR_PAYLOAD = accepted_inputs_payload(PRIOR)

# It holds the two previously accepted batches, and only those.
assert [b.batch_id for b in PRIOR.batches] == PRIOR_BATCH_IDS, PRIOR.batches
assert {a.batch_id for a in PRIOR.acceptances} == set(PRIOR_BATCH_IDS)
assert PRIOR.oracle.schema_version == PRIOR_SCHEMA_VERSION
assert PRIOR.oracle.schema_hash == PRIOR_SCHEMA_HASH
assert oracle_identity(PRIOR.oracle) == PRIOR_ORACLE_IDENTITY
assert [a.schema_version for a in PRIOR.schema_anchors] == PRIOR_ANCHOR_SCHEMAS
assert [lr.lift_id for lr in PRIOR.lifts] == PRIOR_LIFT_IDS
assert len(PRIOR.oracle.spans) == PRIOR_COUNTS["spans"]
assert len(PRIOR.acceptances) == PRIOR_COUNTS["acceptances"]
for _coll in REPRESENTATION_COLLECTIONS:
    assert (
        len(getattr(PRIOR.oracle.representation, _coll)) == PRIOR_COUNTS[_coll]
    ), _coll

#: Every prior reference already resolves inside accepted authority. Stated
#: before the merge so the five that do not resolve afterwards are known to have
#: arrived with `actions-1` rather than to have been there all along.
_prior_record_keys = {r.semantic_key for r in PRIOR.oracle.representation.records}
assert not [
    ref
    for ref in PRIOR.oracle.representation.references
    if ref.target_record_key not in _prior_record_keys
], "the prior already carried an unresolved reference"

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
# run so this script cannot be a covert regeneration.

(
    _proposal_raw_before,
    _proposal_content_before,
    _proposal_blob_before,
) = _identifiers(PROPOSAL_FILE)
assert _proposal_content_before == PROPOSAL_CONTENT_SHA256, _proposal_content_before
_audit_content_before = _identifiers(AUDIT_FILE)[1]
assert _audit_content_before == AUDIT_CONTENT_SHA256, _audit_content_before

if not VERIFY_ONLY:
    os.environ["ACTIONS7_RERUN"] = "1"
    _generated = runpy.run_path(str(GENERATOR), run_name="__actions7_accept__")
    PROPOSAL = _generated["PROPOSAL"]

    (
        _proposal_raw_after,
        _proposal_content_after,
        _proposal_blob_after,
    ) = _identifiers(PROPOSAL_FILE)
    assert _proposal_content_after == PROPOSAL_CONTENT_SHA256, _proposal_content_after
    assert _identifiers(AUDIT_FILE)[1] == AUDIT_CONTENT_SHA256, "the audit changed"

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

assert len(RESOLVED_SCOPE) == BATCH_COUNTS["spans"], len(RESOLVED_SCOPE)
assert len(set(RESOLVED_SCOPE)) == len(RESOLVED_SCOPE), "the scope repeats a span"
assert len({p.leaf_id for p in _spans_reviewed}) == LEAVES
_by_disposition = {d: 0 for d in SemanticDisposition}
for _p in _spans_reviewed:
    _by_disposition[_p.disposition] += 1
assert _by_disposition[SemanticDisposition.UNRESOLVED] == 0, _by_disposition
assert _by_disposition[SemanticDisposition.NON_MECHANICAL] == 0, _by_disposition
DISPOSITIONS = {d.value: n for d, n in _by_disposition.items()}

#: The scope this script derived from the proposal is the scope the review
#: manifest recorded. The manifest is evidence, not authorization: it is checked
#: *against* the derived scope, and never used to build one.
_manifest = json.loads(REVIEW_SCOPE_MANIFEST.read_text(encoding="utf-8"))
SCOPE_MATCHES_REVIEW_MANIFEST = {
    "proposal_identity": _manifest["proposal_identity"] == PROPOSAL_IDENTITY,
    "proposal_sha256": _manifest["proposal_sha256"] == PROPOSAL_CONTENT_SHA256,
    "span_ids": set(_manifest["resolved_scope"]) == set(RESOLVED_SCOPE),
    "span_count": _manifest["span_count"] == len(RESOLVED_SCOPE),
    "record_keys": sorted(_manifest["record_keys"]) == sorted(ACTION_RECORDS),
    "prior_sha256": _manifest["prior_sha256"] == PRIOR_CONTENT_SHA256,
    "schema": _manifest["representation_schema"]
    == {"version": SCHEMA_VERSION, "hash": SCHEMA_HASH},
    "missing_reference_targets": set(_manifest["missing_reference_targets"])
    == MISSING_REFERENCE_TARGETS,
}
assert all(SCOPE_MATCHES_REVIEW_MANIFEST.values()), SCOPE_MATCHES_REVIEW_MANIFEST

# ---------------------------------------------------------------------------
# 3. The acceptance action
# ---------------------------------------------------------------------------

RULE = (
    f"Owner authorization of {ACCEPTED_AT[:10]}, verbatim: {AUTHORIZATION!r} "
    f"Applied to CRD Issue 5d batch {BATCH_ID}, proposal identity "
    f"{PROPOSAL_IDENTITY} under representation schema {SCHEMA_VERSION} over 5c "
    f"release {PRIOR.oracle.binding.package_uuid}/"
    f"{PRIOR.oracle.binding.release_version}. The scope is the complete "
    "proposed span set and nothing outside it: 182 spans over 92 represented 5c "
    "leaves and 13 records — the Action umbrella glossary rule and the twelve "
    "action entries Attack, Dash, Disengage, Dodge, Help, Hide, Influence, "
    "Magic, Ready, Search, Study and Utilize — with 84 substantive and 98 "
    "supporting-authority dispositions, and zero unresolved and zero "
    "non-mechanical. Schema stop S-1 (Magic's long-casting gate) was closed at "
    "representation schema 7 before review; the prior accepted schema-5 "
    "authority is carried forward by the registered lifts "
    "5d-lift-schema-5-to-6 and 5d-lift-schema-6-to-7. Disclosed and still open "
    "at acceptance: representation limit L-1 (Attack's equipment options), "
    "residue R-help-reason, and general casting-time eligibility, which remains "
    "a deferred Known Unknown. Five source-authored citations — glossary.speed, "
    "glossary.concentration, attitude.friendly, attitude.hostile and "
    "attitude.indifferent — have no accepted target and were not resolved by "
    "this acceptance; they remain publication blockers until the batches that "
    "define them are accepted. Recorded by an agent executing this "
    "authorization; the decision is the Owner's and the execution is not a "
    "review."
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
#: order - `actions-1` sorts ahead of the two batches accepted before it - so a
#: batch is identified here by its id and never by its position. Acceptance
#: order is not lost: `schema_anchors` below records it, and is asserted there.
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
    assert (
        _entry.accepted_disposition == _proposed_disposition[_entry.span_id]
    ), _entry
    _was = (
        "none"
        if _entry.prior_disposition is None
        else _entry.prior_disposition.value
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
assert {s.review_state for s in RESULT.oracle.spans} == {ReviewState.ACCEPTED}
assert {a.span_id for a in RESULT.acceptances} == {
    s.span_id for s in RESULT.oracle.spans
}

# --- Every prior element and every piece of prior evidence, unchanged -------
#
# `PRIOR` is the genuine pre-acceptance content in both modes: the live artifact
# during the acceptance, and the byte-identical frozen fixture under `--verify`.
# So the exact comparisons below run in full in both modes. Counts are reported
# beside them, never in place of them: 281 acceptance records with a rewritten
# reviewer is still 281.
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

# --- Schema anchors and the registered 5 -> 6 -> 7 succession ---------------
ANCHORS = [
    {
        "batch_id": a.batch_id,
        "proposal_identity": a.proposal_identity,
        "schema_version": a.schema_version,
        "schema_hash": a.schema_hash,
    }
    for a in RESULT.schema_anchors
]
assert [a["batch_id"] for a in ANCHORS] == [*PRIOR_BATCH_IDS, BATCH_ID], ANCHORS
assert [a["schema_version"] for a in ANCHORS[:2]] == PRIOR_ANCHOR_SCHEMAS, ANCHORS
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
#: The prior's own 3 -> 4 -> 5 records are retained and the new crossings are
#: appended, so the artifact carries the whole succession rather than only the
#: last hop.
assert [lift_record["lift_id"] for lift_record in LIFTS] == [
    *PRIOR_LIFT_IDS,
    *EXPECTED_LIFT_IDS,
], LIFTS
assert LIFTS[-2]["from"] == [PRIOR_SCHEMA_VERSION, PRIOR_SCHEMA_HASH], LIFTS
assert LIFTS[-1]["to"] == [SCHEMA_VERSION, SCHEMA_HASH], LIFTS
for lift_record in LIFTS:
    assert sorted(lift_record["verified_collections"]) == sorted(
        REPRESENTATION_COLLECTIONS
    ), lift_record
assert RESULT.oracle.schema_version == SCHEMA_VERSION
assert RESULT.oracle.schema_hash == SCHEMA_HASH

# --- The action records actually arrived, and the representation with them --
_keys = {r.semantic_key for r in RESULT.oracle.representation.records}
assert set(ACTION_RECORDS) <= _keys, sorted(set(ACTION_RECORDS) - _keys)
assert _keys == _prior_record_keys | set(ACTION_RECORDS), sorted(_keys)
assert {o.record_key for o in RESULT.oracle.obligations} == _keys

#: The batch's typed representation arrived, not merely its spans: the
#: schema-7 long-casting gate is the reason schema 7 exists, so its absence
#: would mean the accepted authority is a schema-7 declaration over schema-5
#: content.
_components = {
    (c.record_key, c.semantic_key): c
    for c in RESULT.oracle.representation.components
}
GATED_COMPONENTS = {
    f"{rk}/{ck}": {
        "applies_when": _components[(rk, ck)].applies_when is not None,
        "facts": len(_components[(rk, ck)].facts),
    }
    for rk, ck in (
        ("action.magic", "magic_long_casting"),
        ("action.magic", "magic_concentration_break"),
    )
}
assert all(g["applies_when"] for g in GATED_COMPONENTS.values()), GATED_COMPONENTS

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

# --- The five cross-batch citations still have no target -------------------
#
# Asserted by **set equality on target keys**, not by count, and asserted to be
# non-empty. A run reporting zero here would mean a target was fabricated, which
# is a worse outcome than the blocker it would appear to remove.
UNRESOLVED_REFERENCES = sorted(
    {
        ref.target_record_key
        for ref in RESULT.oracle.representation.references
        if ref.target_record_key not in _keys
    }
)
assert set(UNRESOLVED_REFERENCES) == MISSING_REFERENCE_TARGETS, UNRESOLVED_REFERENCES
assert len(REPRESENTATION_FINDINGS) == len(MISSING_REFERENCE_TARGETS), (
    REPRESENTATION_FINDINGS
)
assert all(
    any(target in finding for target in MISSING_REFERENCE_TARGETS)
    for finding in REPRESENTATION_FINDINGS
), REPRESENTATION_FINDINGS

#: Every reference the merge *did* resolve, including both directions across the
#: batch boundary. Reported so the five blockers are not the only thing said
#: about references.
_cross_batch_resolved = sorted(
    (ref.from_record_key, ref.target_record_key)
    for ref in RESULT.oracle.representation.references
    if ref.target_record_key in _keys
    and (ref.from_record_key in set(ACTION_RECORDS))
    != (ref.target_record_key in set(ACTION_RECORDS))
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
        "records": len(ACTION_RECORDS),
        "dispositions": DISPOSITIONS,
    },
    "scope_matches_review_manifest": SCOPE_MATCHES_REVIEW_MANIFEST,
    "semantic_diff_tally": DIFF_TALLY,
    "merged_counts": MEASURED,
    "batches": [b.batch_id for b in RESULT.batches],
    "schema_anchors": ANCHORS,
    "lifts": LIFTS,
    "preservation": PRESERVATION,
    "gated_components": GATED_COMPONENTS,
    "round_trip": ROUND_TRIP,
    "validate_acceptance": ACCEPTANCE_FINDINGS,
    "validate_representation": REPRESENTATION_FINDINGS,
    "publication_blockers": {
        "unresolved_reference_targets": UNRESOLVED_REFERENCES,
        "still_blocked": bool(UNRESOLVED_REFERENCES),
        "note": (
            "accepted, not publishable. These five were not resolved by this "
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
    ],
}

print(json.dumps(REPORT, indent=1))
