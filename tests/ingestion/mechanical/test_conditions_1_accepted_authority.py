"""The committed conditions-1 accepted authority — CRD Issue 5d, batch 1.

Owner authorization of 2026-08-23 accepted proposal identity
``14587d5b…`` and its exact resolved scope, and nothing else. The artifact that
records that action is committed under the oracle directory, and this module is
what keeps it honest: the file is the acceptance action of record, so a change
to it that no one reviewed must fail here.

Five properties, each of which could break independently:

* the release resolves to **this** artifact and only this one;
* the batch, proposal identity, reviewer, scope, and counts are exact;
* the committed bytes round-trip strictly and reproduce every derived identity;
* the refused candidates cannot be selected; and
* the corpus is still incomplete, so nothing here can publish.

The end-to-end publication refusal lives in ``test_production_release`` and
``test_runtime_production_release``, which carry the real SRD fixture. What is
asserted here is the reason it refuses: this artifact judges 15 conditions plus
the glossary entry that defines them, not the release.
"""

from __future__ import annotations

import json

from afterworlds.ingestion.mechanical.models import ReviewState, SemanticDisposition
from afterworlds.ingestion.mechanical.oracle import (
    ACCEPTED_ARTIFACT_KIND,
    COMMITTED_ORACLE_DIR,
    accepted_inputs_payload,
    candidate_from_accepted_inputs,
    committed_inputs_for,
    committed_oracle_for,
    load_accepted_inputs,
    load_oracle,
    oracle_identity,
)
from afterworlds.ingestion.mechanical.projection import (
    identify_projection,
    validate_schema_binding,
)
from afterworlds.ingestion.mechanical.representation import (
    REPRESENTATION_SCHEMA_VERSION,
    representation_schema_hash,
)

PACKAGE_UUID = "4458fa10-4a66-5e0e-9ecc-ea37530ad2b4"
RELEASE_VERSION = "5.2.1-corpus.36b786d8-fa2"

ARTIFACT_NAME = "srd-5-2-1-corpus-36b786d8-fa2.json"
ARTIFACT_PATH = COMMITTED_ORACLE_DIR / ARTIFACT_NAME

BATCH_ID = "conditions-1"
REVIEWER = "Ravenlok (Owner)"
PROPOSAL_IDENTITY = "14587d5b5d51ad282f3d16510e015cd7116adcbd3877964bf034eef96780b0eb"
ORACLE_IDENTITY = "a0f0bd2f6f6f05d3b0b46b63d1dfa9c5e4c3bf0741118b063a5d2b6adf401fda"
PROJECTION_UUID = "48a015cb-a9bd-56c5-b4a4-1e5901d5be7b"
PROJECTION_PAYLOAD_HASH = (
    "9af8b93da4ab54ba43ad57a9fc08a48e3196d9b173e4f1e0210167d0504bef66"
)

SPANS = 185
RECORDS = 16
COMPONENTS = 54
FACTS = 70
PROSE_BINDINGS = 15
RELATIONSHIPS = 0
REFERENCES = 15
PROVENANCE = 185
SUBSTANTIVE = 87
SUPPORTING = 98

#: Refused by semantic review. Named here so "not selectable" is a test rather
#: than a promise in a checkpoint document.
REFUSED = (
    "756922a3892f9420dc8bfb2fe6af8a5a4db491111d1786ab0de6c2ddbf7dbfa6",
    "b9ac21bf045a3f5d1e020f91fd43fdd6e5f3fb0b3d0a715de556a574d3ab14a6",
    "2f42f2bb82bcb4ed6ac489b47f774495d2ec5d985871a0d5b69f659fc83fb24b",
)


# ---------------------------------------------------------------------------
# 1. Exact release lookup, and only this artifact
# ---------------------------------------------------------------------------


def test_the_release_resolves_to_this_sole_committed_artifact() -> None:
    """One artifact per release, and this release resolves to it.

    The resolver refuses two artifacts claiming one release rather than picking
    one, so a later batch must *extend* this file. Asserting the exact filename
    is what makes a second file for this release fail here before it can fail
    there.
    """
    assert sorted(p.name for p in COMMITTED_ORACLE_DIR.glob("*.json")) == [
        ARTIFACT_NAME
    ]
    inputs = committed_inputs_for(PACKAGE_UUID, RELEASE_VERSION)
    assert inputs is not None
    assert inputs.oracle.binding.package_uuid == PACKAGE_UUID
    assert inputs.oracle.binding.release_version == RELEASE_VERSION
    assert oracle_identity(inputs.oracle) == ORACLE_IDENTITY


def test_an_unrelated_release_still_resolves_to_nothing() -> None:
    """Resolution is by binding, not by "there is a file in the directory"."""
    assert committed_oracle_for(PACKAGE_UUID, "5.2.1-corpus.not-a-release") is None
    assert committed_inputs_for("no-such-package", RELEASE_VERSION) is None


# ---------------------------------------------------------------------------
# 2. The acceptance action, exactly as authorized
# ---------------------------------------------------------------------------


def test_the_batch_records_the_authorized_acceptance_exactly() -> None:
    """Batch id, proposal identity, reviewer, and scope size — all four.

    The proposal identity is what ties this accepted representation to a thing a
    human actually read. A batch that named a different proposal would be
    accepted authority over content nobody reviewed.
    """
    inputs = load_accepted_inputs(ARTIFACT_PATH)
    (batch,) = inputs.batches
    assert batch.batch_id == BATCH_ID
    assert batch.proposal_identity == PROPOSAL_IDENTITY
    assert len(batch.resolved_scope) == SPANS
    assert len(set(batch.resolved_scope)) == SPANS, "the scope repeats a span"
    assert len(batch.diff) == SPANS
    assert batch.rule.strip()


def test_every_span_has_exactly_one_acceptance_record() -> None:
    """No missing, duplicate, or out-of-scope acceptance.

    All three failures are silent in different ways — a missing record leaves a
    span unaccepted while the file looks complete, a duplicate inflates the
    evidence, and an out-of-scope record accepts something the reviewer never
    saw — so each is asserted separately.
    """
    inputs = load_accepted_inputs(ARTIFACT_PATH)
    accepted_ids = [a.span_id for a in inputs.acceptances]
    span_ids = {s.span_id for s in inputs.oracle.spans}

    assert len(accepted_ids) == SPANS
    assert len(set(accepted_ids)) == SPANS, "an acceptance record is duplicated"
    assert set(accepted_ids) == span_ids, "acceptance and span sets differ"
    assert set(accepted_ids) == set(inputs.batches[0].resolved_scope)
    assert {a.batch_id for a in inputs.acceptances} == {BATCH_ID}
    assert {a.reviewer for a in inputs.acceptances} == {REVIEWER}
    # One acceptance action, so one timestamp across the whole batch.
    assert len({a.accepted_at for a in inputs.acceptances}) == 1


def test_the_accepted_scope_and_counts_are_exact() -> None:
    """The scope the Owner authorized, measured rather than described."""
    oracle = load_oracle(ARTIFACT_PATH)
    rep = oracle.representation

    assert len(oracle.spans) == SPANS
    assert len(rep.records) == RECORDS
    assert len(rep.components) == COMPONENTS
    assert len(rep.prose_bindings) == PROSE_BINDINGS
    assert len(rep.relationships) == RELATIONSHIPS
    assert len(rep.references) == REFERENCES
    assert len(rep.provenance) == PROVENANCE

    facts = sum(
        len(c.facts) + sum(len(o.facts) for o in c.options) for c in rep.components
    )
    assert facts == FACTS

    by_disposition = {d: 0 for d in SemanticDisposition}
    for span in oracle.spans:
        by_disposition[span.disposition] += 1
    assert by_disposition[SemanticDisposition.SUBSTANTIVE] == SUBSTANTIVE
    assert by_disposition[SemanticDisposition.SUPPORTING_AUTHORITY] == SUPPORTING
    assert by_disposition[SemanticDisposition.UNRESOLVED] == 0
    assert by_disposition[SemanticDisposition.NON_MECHANICAL] == 0


def test_the_artifact_is_accepted_authority_not_a_proposal() -> None:
    """Structurally accepted, and carrying no proposal-only shape.

    ``artifact_kind`` is the legible check; the key set is the one that cannot
    be defeated by editing a field. Review state is absent from the payload
    entirely — it is evidence, not identity — so the in-memory spans are what
    carry ``ACCEPTED``.
    """
    raw = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))
    assert raw["artifact_kind"] == ACCEPTED_ARTIFACT_KIND
    for proposal_only in (
        "proposed_spans",
        "proposed_representation",
        "proposal_origin",
    ):
        assert proposal_only not in raw
    assert "acceptance" in raw and "obligations" in raw
    assert all("review_state" not in s for s in raw["spans"])

    inputs = load_accepted_inputs(ARTIFACT_PATH)
    assert all(s.review_state is ReviewState.ACCEPTED for s in inputs.oracle.spans)


def test_the_declared_schema_is_the_one_this_build_implements() -> None:
    oracle = load_oracle(ARTIFACT_PATH)
    assert oracle.schema_version == REPRESENTATION_SCHEMA_VERSION
    assert oracle.schema_version == "5d-representation-schema-3"
    assert oracle.schema_hash == representation_schema_hash()


# ---------------------------------------------------------------------------
# 3. Strict round-trip, and every derived identity
# ---------------------------------------------------------------------------


def test_the_committed_bytes_round_trip_strictly() -> None:
    """Re-serializing what was loaded reproduces the committed payload.

    Not "loads without error": the loader rejects a missing key, an extra key,
    and an undeclared enum value, so a strict round-trip is what proves the file
    is written in exactly the canonical form the loader expects.
    """
    inputs = load_accepted_inputs(ARTIFACT_PATH)
    raw = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))
    assert accepted_inputs_payload(inputs) == raw


def test_the_accepted_candidate_reproduces_every_derived_identity() -> None:
    """The committed artifact derives the projection the Owner authorized.

    This is the direction that matters: committed bytes a reviewer accepted
    become the candidate that gets persisted. If the artifact derived a
    different projection than the one reviewed, acceptance would name one thing
    and the build would produce another.
    """
    inputs = load_accepted_inputs(ARTIFACT_PATH)
    candidate = candidate_from_accepted_inputs(inputs)
    assert validate_schema_binding(candidate) == ()

    identified = identify_projection(candidate)
    assert identified.projection_uuid == PROJECTION_UUID
    assert identified.payload_hash == PROJECTION_PAYLOAD_HASH
    assert len(identified.record_ids) == RECORDS
    assert len(identified.component_ids) == COMPONENTS
    assert len(identified.fact_ids) == FACTS


def test_review_evidence_is_not_identity_bearing() -> None:
    """Reviewer and timestamp must not reach the oracle identity.

    Re-reviewing an unchanged classification must not remint a projection
    (#137 acceptance criterion 11), which is why the oracle half excludes
    evidence. Asserted by rebuilding the oracle identity from the file and
    comparing it to the pinned value while the evidence is right there beside
    it.
    """
    inputs = load_accepted_inputs(ARTIFACT_PATH)
    assert oracle_identity(inputs.oracle) == ORACLE_IDENTITY
    assert load_oracle(ARTIFACT_PATH) == inputs.oracle
    assert inputs.acceptances, "the evidence half must still be present"
    assert inputs.batches


# ---------------------------------------------------------------------------
# 4. The refused candidates
# ---------------------------------------------------------------------------


def test_no_refused_candidate_is_selectable() -> None:
    """Three identities were refused by review; none may reach the build.

    Selection is by what a committed artifact *names*, so the check is that no
    committed batch names any of them — there is no other route by which a
    refused proposal could become authority.
    """
    named = {
        b.proposal_identity
        for p in COMMITTED_ORACLE_DIR.glob("*.json")
        for b in load_accepted_inputs(p).batches
    }
    assert named == {PROPOSAL_IDENTITY}
    for refused in REFUSED:
        assert refused not in named
    assert PROPOSAL_IDENTITY not in REFUSED


# ---------------------------------------------------------------------------
# 5. The corpus is incomplete, so nothing publishes
# ---------------------------------------------------------------------------


def test_the_accepted_authority_covers_conditions_only() -> None:
    """Why the release still cannot publish, stated at the artifact level.

    Every accepted record is a condition. The publication gate compares accepted
    authority against the *whole* persisted projection, so a projection over the
    full SRD carries records this artifact does not accept — the end-to-end
    refusal is asserted in ``test_production_release`` and
    ``test_runtime_production_release``.
    """
    oracle = load_oracle(ARTIFACT_PATH)
    keys = sorted(r.semantic_key for r in oracle.representation.records)
    assert len(keys) == RECORDS
    # Fifteen conditions plus the glossary entry that defines the list. Nothing
    # from any other CRD Issue 5d batch is in here.
    conditions = [k for k in keys if k.startswith("condition.")]
    assert len(conditions) == 15, conditions
    assert [k for k in keys if not k.startswith("condition.")] == [
        "glossary.condition"
    ], keys
    # One obligation per accepted record, and no obligation over a record this
    # artifact does not accept.
    assert {o.record_key for o in oracle.obligations} == set(keys)


def test_a_later_batch_extends_this_artifact_rather_than_adding_one() -> None:
    """The extension contract, asserted where it can actually be checked.

    ``accept_proposal`` takes prior accepted inputs and merges, and the resolver
    refuses two artifacts for one release. Together those make "extend the file"
    the only representable way to add a batch — so this asserts the file is
    currently a single-batch artifact whose scope a later batch must stay
    disjoint from.
    """
    inputs = load_accepted_inputs(ARTIFACT_PATH)
    assert [b.batch_id for b in inputs.batches] == [BATCH_ID]
    same_release = [
        p
        for p in COMMITTED_ORACLE_DIR.glob("*.json")
        if load_accepted_inputs(p).oracle.binding.release_version == RELEASE_VERSION
    ]
    assert same_release == [ARTIFACT_PATH]
