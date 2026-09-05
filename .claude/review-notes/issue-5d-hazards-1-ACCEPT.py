"""Owner acceptance of CRD Issue 5d batch `hazards-1` — the executable record.

Ravenlok (Owner) accepted the reviewed proposal
`f7ce449174102f1cdb7087a806d1f594add384282e54fb17181c4f5168c40417` exactly as
represented. This script is what performed that acceptance, and it is retained
so every material claim in the checkpoint can be re-executed rather than read.

It is an **acceptance** operation, not a regeneration and not a semantic
revision. It changes no proposal, no audit, no schema, no policy, and nothing
under `src/` except the one accepted-authority artifact it is authorized to
extend.

Three things it deliberately does not do:

* it does not hand-convert the proposal JSON, rename it as accepted authority,
  or reproduce its contents. The reviewed `MechanicalProposal` is rebuilt by
  executing the reviewed generator, and its identity and payload hash are
  asserted before acceptance;
* it does not create a second oracle file. The resolver refuses two artifacts
  claiming one release, so a later batch *extends* the existing one;
* it does not publish, activate, or retire anything.

Re-running it is refused once the acceptance exists: `accept_proposal` rejects a
batch id the prior already records, which is the correct behaviour for a
one-time action. Pass `--verify` to re-check the post-acceptance assertions
against the committed artifact without attempting the acceptance again. Every
comparison it reports is real in that mode, against the frozen prior; the one
claim it cannot make is the in-memory prior-first prefix, because verification
performs no new merge, and it says so in place rather than emitting a value that
reads as success.

`--verify` does **not** re-run the reviewed generator, and that is a separation
of concerns rather than an inability. The two proofs answer different questions
and neither substitutes for the other:

* **this script's `--verify`** checks the *committed acceptance* - that the
  artifact on disk is the one the Owner accepted, that every `conditions-1`
  element survived the merge, and that the pinned identities still hold;
* **the regeneration generator** reproduces the *proposal and audit* from the
  immutable reviewed prior, `tests/ingestion/mechanical/data/
  legacy_conditions_1_unanchored_schema3.json`. It reads that frozen prior and
  never the live oracle, so it executes from the final committed tree and keeps
  executing after later batches are accepted; it reads the live oracle only as a
  mutation sentinel.

Running the generator from here would therefore prove nothing this script needs
and would conflate the two. The bound corpus required for the representation
gate is built here, from the same committed PDF, rather than borrowed from it.
"""

from __future__ import annotations

import hashlib
import json
import os
import runpy
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
assert HERE.name == "review-notes" and HERE.parent.name == ".claude", HERE
sys.path.insert(0, str(REPO / "src"))

GENERATOR = HERE / "issue-5d-hazards-1-schema5-REGEN-generator.py"
PROPOSAL_FILE = HERE / "issue-5d-hazards-1-schema5-REGEN-PROPOSAL.json"
ACCEPTED_PATH = (
    REPO
    / "src/afterworlds/ingestion/mechanical/oracles"
    / "srd-5-2-1-corpus-36b786d8-fa2.json"
)
for _p in (GENERATOR, PROPOSAL_FILE, ACCEPTED_PATH):
    assert _p.exists(), _p

# --- The pinned reviewed proposal ------------------------------------------
BATCH_ID = "hazards-1"
REVIEWER = "Ravenlok (Owner)"
PROPOSAL_IDENTITY = "f7ce449174102f1cdb7087a806d1f594add384282e54fb17181c4f5168c40417"  # noqa: E501  # pragma: allowlist secret
PROPOSAL_CONTENT_SHA256 = "6d0e0566eaa7241f0d7bb519040b874815fe5a9df79ba278427a926b7d25753f"  # noqa: E501  # pragma: allowlist secret
PROPOSAL_BLOB = "3018bce5f774e40f78ab0f1ab373fe8b5543ee3b"  # pragma: allowlist secret
SCHEMA_VERSION = "5d-representation-schema-5"
SCHEMA_HASH = "2803840899363988cc2f67e0d9f310d9baffe394d52ca0919d11388bcd7f4c40"  # noqa: E501  # pragma: allowlist secret

# --- The prior accepted authority, by the identities that survive a checkout -
PRIOR_BATCH_ID = "conditions-1"
PRIOR_PROPOSAL_IDENTITY = "14587d5b5d51ad282f3d16510e015cd7116adcbd3877964bf034eef96780b0eb"  # noqa: E501  # pragma: allowlist secret
PRIOR_BLOB = "42faeca2486117cd1ea518f8b679d036d6fcde87"  # pragma: allowlist secret
PRIOR_CONTENT_SHA256 = "ead1458e9b54cb33831908d6c6b0faf4c1038daa474bd3acc76599b5008d81ce"  # noqa: E501  # pragma: allowlist secret
PRIOR_SCHEMA_VERSION = "5d-representation-schema-3"

#: The frozen prior. Accepting hazards-1 into the one accepted-authority file
#: ended the repository's only instance of the pre-acceptance state, so
#: verification cannot read the prior out of production any more - the file
#: there *is* the merged result. This fixture is that prior, byte-identical,
#: and it is what ``--verify`` compares the merged artifact against.
LEGACY_PRIOR_PATH = (
    REPO
    / "tests/ingestion/mechanical/data"
    / "legacy_conditions_1_unanchored_schema3.json"
)

#: The merged artifact of record: the result of the one acceptance that
#: happened. Pinned so that an unreviewed edit to *any* part of it fails here -
#: acceptance evidence included, which the oracle identity deliberately does not
#: cover, because reviewer and timestamp are evidence rather than identity.
MERGED_CONTENT_SHA256 = "0925d796a058ff4e64f9a429c9ad73d3c39f1e74dff7e394bc2957c1587e73f7"  # noqa: E501  # pragma: allowlist secret
MERGED_BLOB = "6e65533f4a3523aba3d60cfc3c274ab22e66b59a"  # pragma: allowlist secret
MERGED_ORACLE_IDENTITY = "c794bde48a6fbe6c59e5cc901a30f092524fe0ceecdc60b7ba080f11fd356245"  # noqa: E501  # pragma: allowlist secret

# --- Expected merged shape, stated before it is computed --------------------
PRIOR_COUNTS = {
    "spans": 185,
    "acceptances": 185,
    "records": 16,
    "components": 54,
    "prose_bindings": 15,
    "relationships": 0,
    "references": 15,
    "provenance": 185,
}
BATCH_COUNTS = {
    "spans": 96,
    "acceptances": 96,
    "records": 6,
    "components": 15,
    "prose_bindings": 5,
    "relationships": 0,
    "references": 7,
    "provenance": 96,
}
MERGED_COUNTS = {k: PRIOR_COUNTS[k] + BATCH_COUNTS[k] for k in PRIOR_COUNTS}
LEAVES = 43
HAZARD_RECORDS = (
    "glossary.hazard",
    "hazard.burning",
    "hazard.dehydration",
    "hazard.falling",
    "hazard.malnutrition",
    "hazard.suffocation",
)
EXHAUSTION_REFERENCES = (
    ("hazard.dehydration", "condition.exhaustion"),
    ("hazard.malnutrition", "condition.exhaustion"),
)

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
    ChunkCoverage,  # noqa: E402
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
    does not reformat the batch it already holds. `newline="\\n"` is explicit:
    left to the default, Python writes CRLF on Windows and LF on Linux.
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
#: file is the merged result, so verification reads the frozen prior instead.
#: Reading the merged file and calling it "the prior" is exactly the mistake
#: this correction closes - it makes every preservation comparison compare the
#: artifact to itself.
PRIOR_PATH = ACCEPTED_PATH if not VERIFY_ONLY else LEGACY_PRIOR_PATH
_prior_raw_sha, _prior_content_sha, _prior_blob = _identifiers(PRIOR_PATH)

#: Asserted in **both** modes, against the same two pinned values. The frozen
#: fixture is byte-identical to the artifact as it stood before the acceptance,
#: so there is one prior identity, not two.
assert _prior_content_sha == PRIOR_CONTENT_SHA256, (PRIOR_PATH, _prior_content_sha)
assert _prior_blob == PRIOR_BLOB, (PRIOR_PATH, _prior_blob)

PRIOR = load_accepted_inputs(PRIOR_PATH)
PRIOR_PAYLOAD = accepted_inputs_payload(PRIOR)

# It holds the previously accepted conditions-1 batch, and only that - in both
# modes, because in both modes it is the same content.
assert [b.batch_id for b in PRIOR.batches] == [PRIOR_BATCH_ID], PRIOR.batches
assert PRIOR.batches[0].proposal_identity == PRIOR_PROPOSAL_IDENTITY
assert {a.batch_id for a in PRIOR.acceptances} == {PRIOR_BATCH_ID}
assert PRIOR.oracle.schema_version == PRIOR_SCHEMA_VERSION
assert len(PRIOR.oracle.spans) == PRIOR_COUNTS["spans"]
assert len(PRIOR.acceptances) == PRIOR_COUNTS["acceptances"]
for _coll in REPRESENTATION_COLLECTIONS:
    assert (
        len(getattr(PRIOR.oracle.representation, _coll)) == PRIOR_COUNTS[_coll]
    ), _coll

# The prior's committed serialization is the form this script writes back, and
# it is checked against whichever file the prior was loaded from - the live
# artifact during the acceptance, the frozen fixture afterwards.
assert (
    json.dumps(PRIOR_PAYLOAD, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
).encode("utf-8") == PRIOR_PATH.read_bytes().replace(b"\r\n", b"\n")


# ---------------------------------------------------------------------------
# 2. The reviewed proposal, rebuilt through the reviewed generator
# ---------------------------------------------------------------------------
# Not read from the JSON and not reconstructed by hand: the object accepted here
# is the one the generator builds, and its identity is asserted against the
# pinned value. Run with the rerun flag so it does not spawn its own child; its
# artifacts are deterministic, and their digests are asserted unchanged across
# the run so this script cannot be a covert regeneration.

#: Canonical content digest and Git blob decide; the raw on-disk digest is
#: diagnostic only. A checkout holding CRLF has a different raw digest for
#: byte-identical JSON, so asserting the raw one against a canonical pin
#: would fail verification for the checkout rather than for the content.
(
    _proposal_raw_before,
    _proposal_content_before,
    _proposal_blob_before,
) = _identifiers(PROPOSAL_FILE)
assert _proposal_content_before == PROPOSAL_CONTENT_SHA256, _proposal_content_before
assert _proposal_blob_before == PROPOSAL_BLOB, _proposal_blob_before

if not VERIFY_ONLY:
    os.environ["HAZARDS5_RERUN"] = "1"
    _generated = runpy.run_path(str(GENERATOR), run_name="__hazards5_accept__")
    PROPOSAL = _generated["PROPOSAL"]

    (
        _proposal_raw_after,
        _proposal_content_after,
        _proposal_blob_after,
    ) = _identifiers(PROPOSAL_FILE)
    assert _proposal_content_after == PROPOSAL_CONTENT_SHA256, _proposal_content_after
    assert _proposal_blob_after == PROPOSAL_BLOB, _proposal_blob_after

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
    # Verification reads what the committed proposal states, which is the same
    # span set the acceptance recorded - checked against the batch scope below.
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

# ---------------------------------------------------------------------------
# 3. The acceptance action
# ---------------------------------------------------------------------------

RULE = (
    f"Every span of CRD Issue 5d batch {BATCH_ID}, as proposed by proposal "
    f"identity {PROPOSAL_IDENTITY} against representation schema "
    f"{SCHEMA_VERSION} over 5c release "
    f"{PRIOR.oracle.binding.package_uuid}/{PRIOR.oracle.binding.release_version}, "
    "was "
    "semantically reviewed and accepted as represented. The scope is the "
    "complete proposed span set and nothing outside it: 96 spans over 43 "
    "represented 5c leaves and 6 records — the Hazard umbrella glossary rule "
    "and the five [Hazard] entries Burning, Dehydration, Falling, Malnutrition "
    "and Suffocation — with zero unresolved and zero non-mechanical "
    "dispositions. Three questions the review raised are closed: D-3, Falling's "
    "timing, by the Owner's ruling that a normal fall finishes during the turn "
    "in which it begins, so its damage and landing resolve immediately and "
    "completion is delayed only where a specific rule provides a falling rate "
    "or duration; D-4, Burning's required rolling performance, and Z-1, the "
    "sustained zero-food rule, as correctly represented. No disclosed "
    "representation limit and no open semantic question remains for this batch."
)

ACCEPTED_AT = os.environ.get("HAZARDS1_ACCEPTED_AT") or datetime.now(UTC).strftime(
    "%Y-%m-%dT%H:%M:%SZ"
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

#: The merged artifact of record, pinned by three identities that fail for three
#: different reasons. The oracle identity covers the accepted *content*; the
#: canonical content digest and the Git blob additionally cover the acceptance
#: **evidence** -
#: reviewer, timestamp, batch rule, resolved scope, anchors and lifts - which
#: the oracle identity deliberately excludes, because re-reviewing an unchanged
#: classification must not remint a projection. Without the file-level pins an
#: unreviewed edit to the evidence would pass every other check here.
#: Both pins are checkout-independent, and that is deliberate: the raw digest
#: below is reported as diagnostic evidence and decides nothing, because
#: `.gitattributes` declares `eol=lf` and a working copy predating that
#: attribute holds the same JSON with different bytes.
assert _accepted_content_sha == MERGED_CONTENT_SHA256, _accepted_content_sha
assert _accepted_blob == MERGED_BLOB, _accepted_blob
assert ORACLE_IDENTITY == MERGED_ORACLE_IDENTITY, ORACLE_IDENTITY

# ---------------------------------------------------------------------------
# 4. Post-acceptance assertions
# ---------------------------------------------------------------------------

# --- Batches, scope and evidence -------------------------------------------
assert [b.batch_id for b in RESULT.batches] == [PRIOR_BATCH_ID, BATCH_ID]
_prior_batch, _batch = RESULT.batches
assert _batch.proposal_identity == PROPOSAL_IDENTITY
assert len(_batch.resolved_scope) == BATCH_COUNTS["spans"]
assert set(_batch.resolved_scope) == set(RESOLVED_SCOPE)
assert len(_batch.diff) == BATCH_COUNTS["spans"]
assert _batch.rule == RULE
_new_records = [a for a in RESULT.acceptances if a.batch_id == BATCH_ID]
assert len(_new_records) == BATCH_COUNTS["acceptances"]
assert {a.reviewer for a in _new_records} == {REVIEWER}
ACCEPTED_AT_RECORDED = {a.accepted_at for a in _new_records}
assert len(ACCEPTED_AT_RECORDED) == 1, ACCEPTED_AT_RECORDED
(ACCEPTED_AT_VALUE,) = ACCEPTED_AT_RECORDED
assert datetime.strptime(ACCEPTED_AT_VALUE, "%Y-%m-%dT%H:%M:%SZ")

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
# One statement, and it is the strong one in both modes. `PRIOR` is the genuine
# pre-acceptance content either way: the live artifact during the acceptance,
# and the byte-identical frozen fixture under `--verify`. So the exact
# comparisons below - the conditions-1 batch record, all 185 acceptance records,
# all 185 spans, every prior element of each of the six representation
# collections, and every prior obligation - run in full in both modes. Counts
# and measurements are reported beside them, never in place of them.
#
# Exactly one claim is acceptance-only, and it is not a weaker version of any of
# those: the in-memory prior-first *prefix*. `_merged_collection` retains prior
# items ahead of new ones, so the object `accept_proposal` returns carries them
# as a byte-identical prefix - but verification performs no new in-memory merge,
# so there is no such object for it to inspect.
#
# The *serialized* artifact never carries the prefix property in either mode:
# `representation_payload` orders every collection canonically, so once written
# and loaded back the prior elements interleave with the new ones. On disk the
# requirement is therefore preservation, not prefix order - every prior element
# survives unchanged and nothing was dropped or coalesced - which is what the
# per-collection comparisons below assert.
_conditions_1_records = [a for a in RESULT.acceptances if a.batch_id == PRIOR_BATCH_ID]
_conditions_1_spans = [
    s_ for s_ in RESULT.oracle.spans if s_.span_id in set(_prior_batch.resolved_scope)
]
# **One statement, real in both modes.** Every entry below is an element
# comparison against the prior loaded above - never a count, and never a
# non-empty explanatory string standing in for a comparison that did not happen.
# A count is not preservation: 185 acceptance records with a rewritten reviewer
# is still 185. A truthy note is not preservation either, and `all()` over a
# dict holding one is `True` for no reason at all.
_merged_representation_payload = representation_payload(RESULT.oracle.representation)
PRESERVATION = {
    "conditions_1_batch_record_identical": _prior_batch == PRIOR.batches[0],
    "conditions_1_acceptance_records_identical": _conditions_1_records
    == list(PRIOR.acceptances),
    "conditions_1_spans_identical": _conditions_1_spans == list(PRIOR.oracle.spans),
    "conditions_1_payload_elements_present": {
        coll: all(
            element in _merged_representation_payload[coll]
            for element in PRIOR_PAYLOAD["representation"][coll]
        )
        for coll in REPRESENTATION_COLLECTIONS
    },
    "conditions_1_obligations_preserved": all(
        obligation in RESULT_PAYLOAD["obligations"]
        for obligation in PRIOR_PAYLOAD["obligations"]
    ),
}
#: Every element of the prior that the merged artifact does not carry, per
#: collection. Reported rather than only asserted, so a failure names what is
#: missing instead of only that something is.
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
        # to check under --verify, and the serialized order is canonical rather
        # than prior-first, so this is the one claim that is acceptance-only.
        _prior_elements = getattr(PRIOR.oracle.representation, _coll)
        _in_memory = getattr(ACCEPTED.oracle.representation, _coll)
        assert _in_memory[: len(_prior_elements)] == _prior_elements, _coll
    assert not MISSING_PRIOR_ELEMENTS[_coll], (
        _coll,
        len(MISSING_PRIOR_ELEMENTS[_coll]),
    )
    assert len(RESULT_PAYLOAD["representation"][_coll]) == MERGED_COUNTS[_coll], _coll
assert PRESERVATION["conditions_1_batch_record_identical"], "the prior batch moved"
assert PRESERVATION["conditions_1_acceptance_records_identical"]
assert PRESERVATION["conditions_1_spans_identical"]
assert all(PRESERVATION["conditions_1_payload_elements_present"].values())
assert len(PRESERVATION["conditions_1_payload_elements_present"]) == len(
    REPRESENTATION_COLLECTIONS
), "a collection was not compared at all"
assert PRESERVATION["conditions_1_obligations_preserved"]

# --- Schema anchors and the registered 3 -> 4 -> 5 succession ---------------
ANCHORS = [
    {
        "batch_id": a.batch_id,
        "proposal_identity": a.proposal_identity,
        "schema_version": a.schema_version,
        "schema_hash": a.schema_hash,
    }
    for a in RESULT.schema_anchors
]
assert [a["batch_id"] for a in ANCHORS] == [PRIOR_BATCH_ID, BATCH_ID], ANCHORS
assert ANCHORS[0]["schema_version"] == PRIOR_SCHEMA_VERSION, ANCHORS
assert ANCHORS[0]["proposal_identity"] == PRIOR_PROPOSAL_IDENTITY, ANCHORS
assert ANCHORS[1]["schema_version"] == SCHEMA_VERSION, ANCHORS
assert ANCHORS[1]["schema_hash"] == SCHEMA_HASH, ANCHORS
assert ANCHORS[1]["proposal_identity"] == PROPOSAL_IDENTITY, ANCHORS
LIFTS = [
    {
        "lift_id": lift_record.lift_id,
        "from": [lift_record.from_version, lift_record.from_hash],
        "to": [lift_record.to_version, lift_record.to_hash],
        "verified_collections": list(lift_record.verified_collections),
    }
    for lift_record in RESULT.lifts
]
assert [lift_record["lift_id"] for lift_record in LIFTS] == [
    "5d-lift-schema-3-to-4",
    "5d-lift-schema-4-to-5",
], LIFTS
assert LIFTS[0]["from"][0] == PRIOR_SCHEMA_VERSION, LIFTS
assert LIFTS[-1]["to"] == [SCHEMA_VERSION, SCHEMA_HASH], LIFTS
for lift_record in LIFTS:
    assert sorted(lift_record["verified_collections"]) == sorted(
        REPRESENTATION_COLLECTIONS
    ), lift_record
assert RESULT.oracle.schema_version == SCHEMA_VERSION
assert RESULT.oracle.schema_hash == SCHEMA_HASH

# --- The hazards records actually arrived ----------------------------------
_keys = {r.semantic_key for r in RESULT.oracle.representation.records}
assert set(HAZARD_RECORDS) <= _keys, sorted(HAZARD_RECORDS)
assert {o.record_key for o in RESULT.oracle.obligations} == _keys

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
assert not REPRESENTATION_FINDINGS, REPRESENTATION_FINDINGS

# --- The two Exhaustion references now resolve -----------------------------
_record_keys = {r.semantic_key for r in RESULT.oracle.representation.records}
RESOLVED_REFERENCES = [
    {
        "from": ref.from_record_key,
        "to": ref.target_record_key,
        "source_text": ref.source_text,
        "target_is_accepted_authority": ref.target_record_key in _record_keys,
    }
    for ref in RESULT.oracle.representation.references
    if (ref.from_record_key, ref.target_record_key) in EXHAUSTION_REFERENCES
]
assert len(RESOLVED_REFERENCES) == len(EXHAUSTION_REFERENCES), RESOLVED_REFERENCES
assert all(r["target_is_accepted_authority"] for r in RESOLVED_REFERENCES)
assert not [
    ref
    for ref in RESULT.oracle.representation.references
    if ref.target_record_key not in _record_keys
], "an accepted reference points outside accepted authority"

# ---------------------------------------------------------------------------
# 5. Report
# ---------------------------------------------------------------------------

REPORT = {
    "batch": BATCH_ID,
    "reviewer": REVIEWER,
    "accepted_at": ACCEPTED_AT_VALUE,
    "proposal_identity": PROPOSAL_IDENTITY,
    "proposal_payload_hash": PROPOSAL_PAYLOAD_HASH,
    "proposal_content_sha256": _proposal_content_after,
    "proposal_blob": _proposal_blob_after,
    "proposal_raw_sha256_diagnostic": _proposal_raw_after,
    "schema": [SCHEMA_VERSION, SCHEMA_HASH],
    "scope": {
        "spans": len(RESOLVED_SCOPE),
        "leaves": LEAVES,
        "records": len(HAZARD_RECORDS),
        "dispositions": DISPOSITIONS,
    },
    "merged_counts": MEASURED,
    "batches": [b.batch_id for b in RESULT.batches],
    "schema_anchors": ANCHORS,
    "lifts": LIFTS,
    # Reported as computed, never collapsed. `all()` over a dict is what turned
    # a single explanatory string into a passing preservation claim; the six
    # per-collection Booleans are the evidence, so the report shows six.
    "preservation": PRESERVATION,
    "round_trip": ROUND_TRIP,
    "validate_acceptance": ACCEPTANCE_FINDINGS,
    "validate_representation": REPRESENTATION_FINDINGS,
    "resolved_exhaustion_references": RESOLVED_REFERENCES,
    "accepted_oracle_identity": ORACLE_IDENTITY,
    "accepted_artifact_content_sha256": _accepted_content_sha,
    "accepted_artifact_blob": _accepted_blob,
    "accepted_artifact_raw_sha256_diagnostic": _accepted_raw_sha,
    # Canonical content, Git blob and oracle identity. The raw digest is not
    # a term here: it varies with the checkout, so letting it decide would
    # report a CRLF working copy as an unreviewed edit.
    "accepted_artifact_matches_pinned_merged_identity": (
        _accepted_content_sha == MERGED_CONTENT_SHA256
        and _accepted_blob == MERGED_BLOB
        and ORACLE_IDENTITY == MERGED_ORACLE_IDENTITY
    ),
    "prior_artifact_source": str(PRIOR_PATH.relative_to(REPO).as_posix()),
    "prior_artifact_content_sha256": _prior_content_sha,
    "prior_artifact_blob": _prior_blob,
    "prior_artifact_raw_sha256_diagnostic": _prior_raw_sha,
    "missing_prior_elements": {
        coll: len(missing) for coll, missing in MISSING_PRIOR_ELEMENTS.items()
    },
}

print(json.dumps(REPORT, indent=1))
