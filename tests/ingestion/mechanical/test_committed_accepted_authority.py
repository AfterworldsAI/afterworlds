"""The committed accepted authority — CRD Issue 5d, batches 1 through 3.

Three Owner authorizations, one file. 2026-08-23 accepted ``conditions-1``
(proposal ``14587d5b…``, reviewed under representation schema 3); 2026-09-03
accepted ``hazards-1`` (proposal ``f7ce4491…``, reviewed under schema 5);
2026-09-09 accepted ``actions-1`` (proposal ``62202e9a…``, reviewed under
schema 7). The artifact that records all three actions is committed under the
oracle directory, and this module is what keeps it honest: the file is the
acceptance action of record, so a change to it that no one reviewed must fail
here.

Six properties, each of which could break independently:

* the release resolves to **this** artifact and only this one;
* each batch's proposal identity, reviewer, scope, and counts are exact, and the
  scopes are pairwise disjoint;
* the schema each batch was *reviewed* under is retained beside it, and the
  registered succession that carried the older ones forward is recorded;
* the committed bytes round-trip strictly and reproduce every derived identity;
* the refused candidates cannot be selected; and
* the corpus is still incomplete, so nothing here can publish.

The end-to-end publication refusal lives in ``test_production_release`` and
``test_runtime_production_release``, which carry the real SRD fixture. What is
asserted here is the reason it refuses: this artifact judges 15 conditions, the
glossary entry that defines them, 5 hazards and the glossary entry that defines
*those*, and 12 actions plus the glossary entry that defines *those* — 35
records, not the release.

``batches`` is keyed rather than ordered: ``load_accepted_inputs`` returns it in
canonical id order, so every assertion below looks a batch up by id. Acceptance
order is asserted where the artifact actually records it — ``schema_anchors``.

**The legacy form is no longer here.** Until ``hazards-1`` was accepted, this
file was also the repository's only specimen of a single-batch, schema-3,
unanchored artifact, and a dozen succession and subclass-refusal modules used it
as one. That shape is frozen at
``data/legacy_conditions_1_unanchored_schema3.json`` — byte-identical to what
this file was, Git blob ``42faeca2…`` — and those modules read it there. This
module is about the artifact the release actually resolves to.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
from dataclasses import replace

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
    REPRESENTATION_COLLECTIONS,
    REPRESENTATION_SCHEMA_VERSION,
    fact_qualifier_target_key,
    fact_target_key,
    prose_binding_target_key,
    reference_target_key,
    representation_schema_hash,
)
from afterworlds.ingestion.mechanical.schema_lift import (
    SCHEMA_3_HASH,
    SCHEMA_3_VERSION,
    SCHEMA_5_HASH,
    SCHEMA_5_VERSION,
    SCHEMA_7_HASH,
    SCHEMA_7_VERSION,
    lift_accepted_inputs,
)

PACKAGE_UUID = "4458fa10-4a66-5e0e-9ecc-ea37530ad2b4"
RELEASE_VERSION = "5.2.1-corpus.36b786d8-fa2"

ARTIFACT_NAME = "srd-5-2-1-corpus-36b786d8-fa2.json"
ARTIFACT_PATH = COMMITTED_ORACLE_DIR / ARTIFACT_NAME

REVIEWER = "Ravenlok (Owner)"

#: The legacy specimen: what this file was before ``hazards-1`` was accepted
#: into it. The succession tests below carry *that* content across the
#: registered lifts, because that is the content a lift exists to carry.
LEGACY_PATH = (
    pathlib.Path(__file__).resolve().parent
    / "data"
    / "legacy_conditions_1_unanchored_schema3.json"
)

BATCH_ID = "conditions-1"
PROPOSAL_IDENTITY = "14587d5b5d51ad282f3d16510e015cd7116adcbd3877964bf034eef96780b0eb"  # noqa: E501  # pragma: allowlist secret
HAZARDS_BATCH_ID = "hazards-1"
HAZARDS_PROPOSAL_IDENTITY = "f7ce449174102f1cdb7087a806d1f594add384282e54fb17181c4f5168c40417"  # noqa: E501  # pragma: allowlist secret
ACTIONS_BATCH_ID = "actions-1"
ACTIONS_PROPOSAL_IDENTITY = "62202e9a4b9e0cb539c770e1244b3aa322d8f988e82a544991998fd8fb363b5c"  # noqa: E501  # pragma: allowlist secret

ORACLE_IDENTITY = "8c41b01e92878c614fad5c039c006c66221a4cc55cfab68698ef9302865a6eee"  # noqa: E501  # pragma: allowlist secret

#: The whole committed file, by two identities the oracle identity does not
#: cover. ``oracle_identity`` is content-only **by design** — reviewer and
#: timestamp are evidence, not identity, so re-reviewing an unchanged
#: classification must not remint a projection (#137 acceptance criterion 11).
#: The consequence is that an unreviewed edit to the acceptance *evidence* —
#: reviewer, timestamp, batch rule, resolved scope, anchors, lifts — leaves the
#: oracle identity untouched. These two pin the file itself, so it does not.
#:
#: The content digest normalizes CRLF to LF, which is what ``.gitattributes``
#: declares this file is stored as; the blob id is Git's own content identity,
#: computed from those same bytes rather than read out of ``.git``.
ARTIFACT_CONTENT_SHA256 = "87864b6ac81e4f8baf57eddf9524dade1b2045a5fc804c79b3d57412c87f46fc"  # noqa: E501  # pragma: allowlist secret
ARTIFACT_BLOB = "a729a797594e1156b279fac76c3073c733707a2f"  # pragma: allowlist secret
PROJECTION_UUID = "9da8e85e-1d3d-55a6-ac9a-bb35e06d6322"
PROJECTION_PAYLOAD_HASH = "7c4c1bd4d636dcb5dc09ead85b2ed843f3e838b097952d164b85adad231222a7"  # noqa: E501  # pragma: allowlist secret

#: What each batch accepted, and what the file therefore holds. Kept per batch
#: rather than only as totals: a merged count that is right for the wrong reason
#: — one batch grown, another shrunk — would still add up.
CONDITIONS = {
    "spans": 185,
    "records": 16,
    "components": 54,
    "facts": 70,
    "prose_bindings": 15,
    "relationships": 0,
    "references": 15,
    "provenance": 185,
    "substantive": 87,
    "supporting": 98,
}
HAZARDS = {
    "spans": 96,
    "records": 6,
    "components": 15,
    "facts": 21,
    "prose_bindings": 5,
    "relationships": 0,
    "references": 7,
    "provenance": 96,
    "substantive": 65,
    "supporting": 31,
}
ACTIONS = {
    "spans": 182,
    "records": 13,
    "components": 37,
    "facts": 48,
    "prose_bindings": 27,
    "relationships": 0,
    "references": 17,
    "provenance": 199,
    "substantive": 84,
    "supporting": 98,
}
BATCH_COUNTS = {
    BATCH_ID: CONDITIONS,
    HAZARDS_BATCH_ID: HAZARDS,
    ACTIONS_BATCH_ID: ACTIONS,
}
MERGED = {k: sum(c[k] for c in BATCH_COUNTS.values()) for k in CONDITIONS}

SPANS = MERGED["spans"]
RECORDS = MERGED["records"]
COMPONENTS = MERGED["components"]
FACTS = MERGED["facts"]
PROSE_BINDINGS = MERGED["prose_bindings"]
RELATIONSHIPS = MERGED["relationships"]
REFERENCES = MERGED["references"]
PROVENANCE = MERGED["provenance"]
SUBSTANTIVE = MERGED["substantive"]
SUPPORTING = MERGED["supporting"]

#: Refused by semantic review. Named here so "not selectable" is a test rather
#: than a promise in a checkpoint document.
REFUSED = (
    "756922a3892f9420dc8bfb2fe6af8a5a4db491111d1786ab0de6c2ddbf7dbfa6",  # noqa: E501  # pragma: allowlist secret
    "b9ac21bf045a3f5d1e020f91fd43fdd6e5f3fb0b3d0a715de556a574d3ab14a6",  # noqa: E501  # pragma: allowlist secret
    "2f42f2bb82bcb4ed6ac489b47f774495d2ec5d985871a0d5b69f659fc83fb24b",  # noqa: E501  # pragma: allowlist secret
    # The schema-4 hazards proposal the semantic review rejected. It stays
    # historical evidence; the batch that was accepted is a different identity
    # against a different schema, and the assertion below is what keeps the two
    # from ever being confused.
    "6277ff735e0e47b3337f2c3736ca7922864b1cde9a3c286b3aee48ee461ba259",  # noqa: E501  # pragma: allowlist secret
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
    batches = {b.batch_id: b for b in inputs.batches}
    assert len(batches) == len(inputs.batches), "a batch id is recorded twice"
    assert sorted(batches) == sorted(BATCH_COUNTS)
    for batch_id, identity in (
        (BATCH_ID, PROPOSAL_IDENTITY),
        (HAZARDS_BATCH_ID, HAZARDS_PROPOSAL_IDENTITY),
        (ACTIONS_BATCH_ID, ACTIONS_PROPOSAL_IDENTITY),
    ):
        batch = batches[batch_id]
        counts = BATCH_COUNTS[batch_id]
        assert batch.proposal_identity == identity
        assert len(batch.resolved_scope) == counts["spans"]
        assert len(set(batch.resolved_scope)) == counts["spans"], "the scope repeats"
        assert len(batch.diff) == counts["spans"]
        assert batch.rule.strip()
    # Pairwise disjoint, which is what makes each later batch an extension
    # rather than a re-judgement of something already accepted.
    scopes = [set(b.resolved_scope) for b in inputs.batches]
    assert len(set().union(*scopes)) == sum(len(scope) for scope in scopes)


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
    assert set(accepted_ids) == {
        span_id for batch in inputs.batches for span_id in batch.resolved_scope
    }
    assert {a.batch_id for a in inputs.acceptances} == set(BATCH_COUNTS)
    assert {a.reviewer for a in inputs.acceptances} == {REVIEWER}
    # One acceptance action per batch, so one timestamp within each and three
    # across the file — a later acceptance must not restamp an earlier one.
    for batch_id, counts in BATCH_COUNTS.items():
        stamps = {a.accepted_at for a in inputs.acceptances if a.batch_id == batch_id}
        assert len(stamps) == 1, batch_id
        assert (
            len([a for a in inputs.acceptances if a.batch_id == batch_id])
            == counts["spans"]
        )
    assert len({a.accepted_at for a in inputs.acceptances}) == len(BATCH_COUNTS)


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


def test_each_batch_still_states_the_schema_it_was_reviewed_under() -> None:
    """The declaration follows the newest acceptance; the anchors do not move.

    An accepted artifact records the contract a human reviewed it under, and
    that record is per batch, not per file. ``conditions-1`` was reviewed under
    schema 3, ``hazards-1`` under schema 5, ``actions-1`` under schema 7, so
    those are the three anchors — and restamping any of them to match whatever
    the build currently implements is exactly the attack ``BatchSchemaAnchor``
    exists to refuse. Accepting ``actions-1`` moved the file's *declaration* to
    schema 7, because that is the schema the newest acceptance was reviewed
    under; it did not touch either earlier anchor, which is the whole reason
    they sit beside the batches rather than in the header.

    The anchors are also the only place the artifact records acceptance
    *order*: ``batches`` comes back in canonical id order, so ``actions-1``
    sorts first while having been accepted last.

    The retained succession is the one that has actually run: schema
    3 → 4 → 5 → 6 → 7, one row per crossing, never collapsed into a transition
    the registry has no row for.
    """
    inputs = load_accepted_inputs(ARTIFACT_PATH)
    assert inputs.oracle.schema_version == SCHEMA_7_VERSION
    assert inputs.oracle.schema_hash == SCHEMA_7_HASH

    assert [a.batch_id for a in inputs.schema_anchors] == [
        BATCH_ID,
        HAZARDS_BATCH_ID,
        ACTIONS_BATCH_ID,
    ]
    anchors = {a.batch_id: a for a in inputs.schema_anchors}
    for batch_id, version, schema_hash, identity in (
        (BATCH_ID, SCHEMA_3_VERSION, SCHEMA_3_HASH, PROPOSAL_IDENTITY),
        (HAZARDS_BATCH_ID, SCHEMA_5_VERSION, SCHEMA_5_HASH, HAZARDS_PROPOSAL_IDENTITY),
        (ACTIONS_BATCH_ID, SCHEMA_7_VERSION, SCHEMA_7_HASH, ACTIONS_PROPOSAL_IDENTITY),
    ):
        assert anchors[batch_id].schema_version == version, batch_id
        assert anchors[batch_id].schema_hash == schema_hash, batch_id
        assert anchors[batch_id].proposal_identity == identity, batch_id

    assert [lift.lift_id for lift in inputs.lifts] == [
        "5d-lift-schema-3-to-4",
        "5d-lift-schema-4-to-5",
        "5d-lift-schema-5-to-6",
        "5d-lift-schema-6-to-7",
    ]
    assert (inputs.lifts[0].from_version, inputs.lifts[0].from_hash) == (
        SCHEMA_3_VERSION,
        SCHEMA_3_HASH,
    )
    assert (inputs.lifts[-1].to_version, inputs.lifts[-1].to_hash) == (
        SCHEMA_7_VERSION,
        SCHEMA_7_HASH,
    )


def test_the_committed_artifact_is_buildable_and_the_legacy_form_is_not() -> None:
    """Both halves of the fail-closed rule, in one place.

    ``actions-1`` was reviewed under schema 7, which is the schema this build
    implements, so the committed artifact declares current authority and is
    admitted exactly as it sits. That is the half the rule *permits*, and it is
    asserted against ``REPRESENTATION_SCHEMA_VERSION`` rather than a literal, so
    the next succession moves this test rather than quietly passing it.

    The refusal has not gone anywhere — it belongs to whichever artifact still
    declares a superseded contract, which is now the frozen schema-3 specimen
    alone. That specimen is **not** current authority as it stands, and that is
    correct rather than a regression: a projection built under a wider union is
    a different projection (ADR-005d Decision 6), and the authorized way
    through is the registered lift.
    """
    inputs = load_accepted_inputs(ARTIFACT_PATH)
    assert inputs.oracle.schema_version == SCHEMA_7_VERSION
    assert inputs.oracle.schema_version == REPRESENTATION_SCHEMA_VERSION
    assert inputs.oracle.schema_hash == representation_schema_hash()
    assert validate_schema_binding(candidate_from_accepted_inputs(inputs)) == ()

    legacy = load_accepted_inputs(LEGACY_PATH)
    assert legacy.oracle.schema_version == SCHEMA_3_VERSION
    findings = validate_schema_binding(candidate_from_accepted_inputs(legacy))
    assert findings != ()
    assert any(REPRESENTATION_SCHEMA_VERSION in f for f in findings), findings

    lifted, _ = lift_accepted_inputs(
        legacy, (REPRESENTATION_SCHEMA_VERSION, representation_schema_hash())
    )
    assert validate_schema_binding(candidate_from_accepted_inputs(lifted)) == ()


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

    Asserted **under the schema the artifact declares**, which since
    ``actions-1`` is again the schema this build implements: the artifact is
    built as current authority, and the test above asserts that it is admitted
    rather than refused. The refusal that used to belong in this sentence is not
    gone — it applies to the frozen schema-3 specimen, and the test above
    asserts it there.

    Both pins moved when ``actions-1`` was accepted, and had to: the projection
    covers strictly more records under a schema whose declaration is itself
    identity-bearing (ADR-005d Decision 6). The property is not that they never
    move — it is that they move only when an Owner accepted something.
    """
    inputs = load_accepted_inputs(ARTIFACT_PATH)
    identified = identify_projection(candidate_from_accepted_inputs(inputs))
    assert identified.projection_uuid == PROJECTION_UUID
    assert identified.payload_hash == PROJECTION_PAYLOAD_HASH
    assert len(identified.record_ids) == RECORDS
    assert len(identified.component_ids) == COMPONENTS
    assert len(identified.fact_ids) == FACTS


def test_the_lift_carries_the_artifact_without_touching_its_content() -> None:
    """The authorized succession, and exactly what it is allowed to change.

    One thing moves: the oracle's declared ``(schema_version, schema_hash)``.
    Every element is carried **by identity rather than by transformation**, and
    ``verify_lift`` has already proved their canonical payloads byte-identical
    under both contracts before this returns.

    The projection UUID does move, and that is correct rather than a leak: the
    schema declaration is identity-bearing (ADR-005d Decision 6), so a
    projection built under a wider contract is a different projection. What may
    not move — the semantic coordinates the Owner accepted — is asserted in
    ``test_every_accepted_semantic_coordinate_survives_the_lift``.
    """
    inputs = load_accepted_inputs(LEGACY_PATH)
    lifted, records = lift_accepted_inputs(
        inputs, (REPRESENTATION_SCHEMA_VERSION, representation_schema_hash())
    )
    # Every registered crossing between the schema this artifact was reviewed
    # under and the one this build implements, oldest first. The chain is not
    # collapsed: a single record would name a transition the registry has no row
    # for, and would assert the artifact never crossed the schemas in between.
    assert [r.lift_id for r in records] == [
        "5d-lift-schema-3-to-4",
        "5d-lift-schema-4-to-5",
        "5d-lift-schema-5-to-6",
        "5d-lift-schema-6-to-7",
    ]
    for record in records:
        assert set(record.verified_collections) == REPRESENTATION_COLLECTIONS
    # The extent the lift proved, asserted against the representation itself.
    # The record no longer repeats it back as element counts: once later batches
    # merge, nothing can re-derive the pre-lift extent to check them against
    # (#137 round 3).
    assert len(inputs.oracle.representation.components) == CONDITIONS["components"]
    assert len(inputs.oracle.representation.records) == CONDITIONS["records"]

    # Carried by identity, never transformed.
    assert lifted.oracle.representation is inputs.oracle.representation
    assert lifted.oracle.spans == inputs.oracle.spans
    assert lifted.oracle.obligations == inputs.oracle.obligations
    # Review evidence is not a review, so a succession may not edit it.
    assert lifted.batches == inputs.batches
    assert lifted.acceptances == inputs.acceptances
    assert lifted.batches[0].proposal_identity == PROPOSAL_IDENTITY

    # Only the declaration moved, and it now names current authority.
    assert lifted.oracle.schema_version == REPRESENTATION_SCHEMA_VERSION
    assert lifted.oracle.schema_hash == representation_schema_hash()
    candidate = candidate_from_accepted_inputs(lifted)
    assert validate_schema_binding(candidate) == ()

    identified = identify_projection(candidate)
    assert len(identified.record_ids) == CONDITIONS["records"]
    assert len(identified.component_ids) == CONDITIONS["components"]
    assert len(identified.fact_ids) == CONDITIONS["facts"]
    # A wider contract is a different projection, as Decision 6 requires, and
    # so is a wider *scope*: neither the pre-lift nor the post-lift identity of
    # the specimen is the identity the committed two-batch artifact derives.
    assert identified.projection_uuid != PROJECTION_UUID


def test_every_accepted_semantic_coordinate_survives_the_lift() -> None:
    """Zero movement, stated over the coordinates the Owner accepted.

    Owner Decision 2026-08-24: a previously accepted fact key or provenance
    coordinate may not move. This is that invariant as an exact assertion over
    the committed bytes rather than a count — every stored fact, qualifier,
    prose-binding and reference coordinate must re-derive exactly from the
    lifted representation.
    """
    inputs = load_accepted_inputs(LEGACY_PATH)
    lifted, _ = lift_accepted_inputs(
        inputs, (REPRESENTATION_SCHEMA_VERSION, representation_schema_hash())
    )
    stored = {
        tuple(claim["target_key"])
        for claim in json.loads(LEGACY_PATH.read_text(encoding="utf-8"))[
            "representation"
        ]["provenance"]
    }

    derived: set[tuple[str, ...]] = set()
    for component in lifted.oracle.representation.components:
        key = (component.record_key, component.semantic_key)
        derived.add(key)
        for fact in component.facts:
            derived.add(fact_target_key(*key, fact))
        for option in component.options:
            for fact in option.facts:
                derived.add(fact_target_key(*key, fact, option.semantic_key))
        for qualifier in component.fact_qualifiers:
            derived.add(
                fact_qualifier_target_key(
                    *key, qualifier.fact_key, qualifier.option_key
                )
            )
    for binding in lifted.oracle.representation.prose_bindings:
        derived.add(prose_binding_target_key(binding))
    for reference in lifted.oracle.representation.references:
        derived.add(reference_target_key(reference))
    for record in lifted.oracle.representation.records:
        derived.add((record.semantic_key,))

    assert not stored - derived, sorted(stored - derived)


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
    assert named == {
        PROPOSAL_IDENTITY,
        HAZARDS_PROPOSAL_IDENTITY,
        ACTIONS_PROPOSAL_IDENTITY,
    }
    for refused in REFUSED:
        assert refused not in named
    assert PROPOSAL_IDENTITY not in REFUSED
    # The rejected schema-4 hazards proposal is in REFUSED, and the accepted
    # hazards batch is a different identity against a different schema.
    assert HAZARDS_PROPOSAL_IDENTITY not in REFUSED
    assert ACTIONS_PROPOSAL_IDENTITY not in REFUSED


# ---------------------------------------------------------------------------
# 5. The corpus is incomplete, so nothing publishes
# ---------------------------------------------------------------------------


def test_the_accepted_authority_covers_the_three_accepted_batches_only() -> None:
    """Why the release still cannot publish, stated at the artifact level.

    Every accepted record belongs to one of the three accepted batches. The
    publication gate compares accepted authority against the *whole* persisted
    projection, so a projection over the full SRD still carries records this
    artifact does not accept — the end-to-end refusal is asserted in
    ``test_production_release`` and ``test_runtime_production_release``.
    """
    oracle = load_oracle(ARTIFACT_PATH)
    keys = sorted(r.semantic_key for r in oracle.representation.records)
    assert len(keys) == RECORDS

    # Fifteen conditions, five hazards, twelve actions, and the glossary entry
    # that defines each of the three lists. Nothing from any other CRD Issue 5d
    # batch is in here.
    conditions = [k for k in keys if k.startswith("condition.")]
    hazards = [k for k in keys if k.startswith("hazard.")]
    actions = [k for k in keys if k.startswith("action.")]
    assert len(conditions) == 15, conditions
    assert hazards == [
        "hazard.burning",
        "hazard.dehydration",
        "hazard.falling",
        "hazard.malnutrition",
        "hazard.suffocation",
    ], hazards
    assert actions == [
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
    ], actions
    assert sorted(set(keys) - set(conditions) - set(hazards) - set(actions)) == [
        "glossary.action",
        "glossary.condition",
        "glossary.hazard",
    ], keys

    # One obligation per accepted record, and no obligation over a record this
    # artifact does not accept.
    assert {o.record_key for o in oracle.obligations} == set(keys)


def test_a_later_batch_extended_this_artifact_rather_than_adding_one() -> None:
    """The extension contract, now demonstrated twice rather than anticipated.

    ``accept_proposal`` takes prior accepted inputs and merges, and the resolver
    refuses two artifacts for one release. Together those made "extend the file"
    the only representable way to add a batch. ``hazards-1`` did exactly that,
    and ``actions-1`` did it again: three batches, one file, one release.

    Acceptance order is asserted through ``schema_anchors`` rather than through
    ``batches``, which is canonically keyed — ``actions-1`` sorts first and was
    accepted last, so reading order out of ``batches`` would assert the
    opposite of the truth.
    """
    inputs = load_accepted_inputs(ARTIFACT_PATH)
    assert sorted(b.batch_id for b in inputs.batches) == sorted(BATCH_COUNTS)
    assert [a.batch_id for a in inputs.schema_anchors] == [
        BATCH_ID,
        HAZARDS_BATCH_ID,
        ACTIONS_BATCH_ID,
    ]
    same_release = [
        p
        for p in COMMITTED_ORACLE_DIR.glob("*.json")
        if load_accepted_inputs(p).oracle.binding.release_version == RELEASE_VERSION
    ]
    assert same_release == [ARTIFACT_PATH]
    # The frozen specimen is a test fixture, not committed authority: it must
    # never appear in the oracle directory, because two artifacts claiming one
    # release is precisely what the resolver refuses.
    assert LEGACY_PATH.parent.name == "data"
    assert LEGACY_PATH not in set(COMMITTED_ORACLE_DIR.glob("*.json"))


# ---------------------------------------------------------------------------
# 6. The complete acceptance record, not merely the accepted content
# ---------------------------------------------------------------------------


def _content_identities(path: pathlib.Path) -> tuple[str, str]:
    """SHA-256 of the canonical LF content, and Git's blob id for it.

    Both are properties of the *content*. The raw on-disk digest is not: a
    working copy predating ``.gitattributes``' ``eol=lf`` can hold CRLF and
    hash differently while holding the same committed file.
    """
    canonical = path.read_bytes().replace(b"\r\n", b"\n")
    blob = hashlib.sha1(  # noqa: S324 - Git's object id, not a security digest
        b"blob " + str(len(canonical)).encode() + b"\x00" + canonical
    ).hexdigest()
    return hashlib.sha256(canonical).hexdigest(), blob


def test_the_whole_acceptance_record_is_pinned_not_only_the_oracle() -> None:
    """An unreviewed edit anywhere in this file fails here.

    The oracle identity is deliberately blind to acceptance evidence, so pinning
    it alone would let someone rewrite a reviewer, a timestamp, a batch rule, a
    resolved scope, an anchor or a lift and still pass every other test in this
    module. The file's own content digest and Git blob close that, and they are
    asserted beside the evidence they protect so a reader can see what would
    have slipped through.
    """
    content_sha, blob = _content_identities(ARTIFACT_PATH)
    assert content_sha == ARTIFACT_CONTENT_SHA256
    assert blob == ARTIFACT_BLOB

    inputs = load_accepted_inputs(ARTIFACT_PATH)
    assert oracle_identity(inputs.oracle) == ORACLE_IDENTITY

    # The evidence the two file-level pins are what actually protect.
    assert {b.batch_id: b.proposal_identity for b in inputs.batches} == {
        BATCH_ID: PROPOSAL_IDENTITY,
        HAZARDS_BATCH_ID: HAZARDS_PROPOSAL_IDENTITY,
        ACTIONS_BATCH_ID: ACTIONS_PROPOSAL_IDENTITY,
    }
    assert {a.reviewer for a in inputs.acceptances} == {REVIEWER}
    assert {a.accepted_at for a in inputs.acceptances} == {
        "2026-08-23T09:53:55Z",
        "2026-09-03T10:58:59Z",
        "2026-09-09T20:45:32Z",
    }
    assert [a.schema_version for a in inputs.schema_anchors] == [
        SCHEMA_3_VERSION,
        SCHEMA_5_VERSION,
        SCHEMA_7_VERSION,
    ]
    assert [lift.lift_id for lift in inputs.lifts] == [
        "5d-lift-schema-3-to-4",
        "5d-lift-schema-4-to-5",
        "5d-lift-schema-5-to-6",
        "5d-lift-schema-6-to-7",
    ]
    assert all(b.rule.strip() for b in inputs.batches)


def test_the_oracle_identity_alone_would_not_have_caught_an_evidence_edit() -> None:
    """Why the file-level pins above exist, demonstrated rather than asserted.

    Done entirely in memory: the committed artifact is never mutated. Rewriting
    a reviewer produces different accepted *inputs* — a different file, which
    the pins above would refuse — while leaving the accepted *oracle* and its
    identity untouched, which is exactly the gap the pins close.
    """
    inputs = load_accepted_inputs(ARTIFACT_PATH)
    forged = replace(
        inputs,
        acceptances=tuple(
            replace(a, reviewer="Somebody Else") for a in inputs.acceptances
        ),
    )

    assert oracle_identity(forged.oracle) == oracle_identity(inputs.oracle)
    assert accepted_inputs_payload(forged) != accepted_inputs_payload(inputs)
    # And the file on disk is untouched by any of this.
    assert _content_identities(ARTIFACT_PATH) == (
        ARTIFACT_CONTENT_SHA256,
        ARTIFACT_BLOB,
    )


def test_the_pinned_identities_survive_a_crlf_checkout_and_the_raw_digest_does_not(
    tmp_path: pathlib.Path,
) -> None:
    """The two pins are content identities; the raw on-disk digest is not.

    ``.gitattributes`` declares ``eol=lf``, but a working copy predating that
    attribute — or a checkout made with ``core.autocrlf=true`` — holds the same
    committed JSON with CRLF line endings. Verification must fail on an edited
    *artifact*, never on a checkout's line endings, so every pinned comparison
    canonicalizes first. This is the regression for that: it asserts the raw
    digest genuinely moves, so the test would still fail if canonicalization
    were dropped and the two digests happened to coincide.

    The committed file is never touched. The CRLF form is built in ``tmp_path``
    and is not committed anywhere — a CRLF copy in the tree would be a second
    artifact claiming one release, which the resolver refuses outright.
    """
    committed = ARTIFACT_PATH.read_bytes()
    assert b"\r\n" not in committed, "the committed artifact must be LF"

    crlf_copy = tmp_path / ARTIFACT_NAME
    crlf_copy.write_bytes(committed.replace(b"\n", b"\r\n"))

    # The raw digests differ, which is exactly why a raw digest cannot decide.
    assert (
        hashlib.sha256(crlf_copy.read_bytes()).hexdigest()
        != hashlib.sha256(committed).hexdigest()
    )

    # The identities that are pinned do not move.
    assert _content_identities(crlf_copy) == (ARTIFACT_CONTENT_SHA256, ARTIFACT_BLOB)

    # And the JSON content is the same content, not merely the same hash.
    reloaded = load_accepted_inputs(crlf_copy)
    committed_inputs = load_accepted_inputs(ARTIFACT_PATH)
    assert accepted_inputs_payload(reloaded) == accepted_inputs_payload(
        committed_inputs
    )
    assert oracle_identity(reloaded.oracle) == ORACLE_IDENTITY
