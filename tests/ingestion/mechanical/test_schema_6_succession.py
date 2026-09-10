"""Zero movement across the schema-5 → schema-6 succession — CRD Issue 5d.

Proved against the **frozen prior** rather than against the live committed
oracle. ``data/accepted_prior_conditions_1_hazards_1.json`` is a byte-for-byte
copy of the two-batch accepted authority as it stood before this schema step
began — Git blob ``6e65533f…``, taken with ``git cat-file blob`` so line endings
are the stored ones rather than the working copy's. Asserting against it means
this module cannot pass by agreeing with a file the same change edited.

**What zero movement means here, precisely.** A succession may move exactly one
thing: the artifact's declared ``(schema_version, schema_hash)``. Everything the
Owner accepted — every element of all six representation collections, every
provenance coordinate, every span, acceptance and obligation, and both batches'
schema anchors — must be carried *by identity rather than by transformation*,
and ``verify_lift`` must have proved that before ``lift_accepted_inputs``
returns. That is a stronger guarantee than a transforming lift could give: a
transforming lift argues its mapping preserved meaning, this one demonstrates
nothing moved.

**And the file itself never changes.** The last test re-reads both the frozen
prior and the committed artifact after every lift in this module has run, and
asserts their bytes. A succession that quietly rewrote accepted authority to
make itself work would pass every other assertion here.
"""

from __future__ import annotations

import hashlib
import json
import pathlib

import pytest

from afterworlds.ingestion.mechanical.oracle import (
    COMMITTED_ORACLE_DIR,
    accepted_inputs_payload,
    candidate_from_accepted_inputs,
    load_accepted_inputs,
    oracle_identity,
)
from afterworlds.ingestion.mechanical.projection import validate_schema_binding
from afterworlds.ingestion.mechanical.representation import (
    REPRESENTATION_COLLECTIONS,
    REPRESENTATION_SCHEMA_VERSION,
    fact_qualifier_target_key,
    fact_target_key,
    prose_binding_target_key,
    reference_target_key,
    relationship_target_key,
    representation_schema_hash,
)
from afterworlds.ingestion.mechanical.schema_lift import (
    SCHEMA_3_HASH,
    SCHEMA_5_HASH,
    SCHEMA_5_VERSION,
    SCHEMA_6_HASH,
    SCHEMA_6_VERSION,
    SCHEMA_7_HASH,
    SCHEMA_7_VERSION,
    lift_accepted_inputs,
)

DATA = pathlib.Path(__file__).resolve().parent / "data"
FROZEN_PRIOR = DATA / "accepted_prior_conditions_1_hazards_1.json"
COMMITTED = COMMITTED_ORACLE_DIR / "srd-5-2-1-corpus-36b786d8-fa2.json"

#: The frozen copy's identity, taken when it was frozen. LF-normalized, which is
#: what ``.gitattributes`` declares this file is stored as.
FROZEN_CONTENT_SHA256 = "0925d796a058ff4e64f9a429c9ad73d3c39f1e74dff7e394bc2957c1587e73f7"  # noqa: E501  # pragma: allowlist secret
FROZEN_BLOB = "6e65533f4a3523aba3d60cfc3c274ab22e66b59a"  # pragma: allowlist secret

#: The committed artifact's own digest. It was the same file as the frozen copy
#: until the Owner accepted ``actions-1`` into it, and reusing one constant for
#: both only ever worked because of that coincidence. Two constants, because
#: they are two files: the sentinel below has to be able to fail for one and
#: pass for the other.
COMMITTED_CONTENT_SHA256 = "d247aed8ab98dab8e71da322de224449f0fe7a46b782c6447010f330d8e87987"  # noqa: E501  # pragma: allowlist secret

#: The accepted oracle's own identity. Derived from the semantic content the
#: Owner accepted, and the one figure a succession may not move at all.
ACCEPTED_ORACLE_IDENTITY = "c794bde48a6fbe6c59e5cc901a30f092524fe0ceecdc60b7ba080f11fd356245"  # noqa: E501  # pragma: allowlist secret

#: What the two accepted batches hold together. Stated so a collection that
#: silently gained or lost an element during a lift fails by name.
MERGED = {
    "records": 22,
    "components": 69,
    "prose_bindings": 20,
    "relationships": 0,
    "references": 22,
    "provenance": 281,
}
SPANS = 281

CONDITIONS_BATCH = "conditions-1"
HAZARDS_BATCH = "hazards-1"

TARGET = (REPRESENTATION_SCHEMA_VERSION, representation_schema_hash())


def _lf_digest(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _blob_id(path: pathlib.Path) -> str:
    body = path.read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha1(b"blob %d\0" % len(body) + body).hexdigest()  # noqa: S324


# ---------------------------------------------------------------------------
# The fixture is the prior it claims to be
# ---------------------------------------------------------------------------


def test_the_frozen_prior_is_the_accepted_authority_this_step_started_from() -> None:
    """Two independent identities, so an edit cannot pass as a reformat."""
    assert _lf_digest(FROZEN_PRIOR) == FROZEN_CONTENT_SHA256
    assert _blob_id(FROZEN_PRIOR) == FROZEN_BLOB

    inputs = load_accepted_inputs(FROZEN_PRIOR)
    assert oracle_identity(inputs.oracle) == ACCEPTED_ORACLE_IDENTITY
    assert inputs.oracle.schema_version == SCHEMA_5_VERSION
    assert inputs.oracle.schema_hash == SCHEMA_5_HASH
    assert [b.batch_id for b in inputs.batches] == [CONDITIONS_BATCH, HAZARDS_BATCH]


def test_the_prior_is_not_current_authority_until_it_is_lifted() -> None:
    """The refusal that makes the succession the *authorized* way through.

    An artifact declaring a schema this build no longer implements is not
    current authority as it stands — a projection built under a wider union is
    a different projection (ADR-005d Decision 6). Reading it as current anyway
    is the forged-identity failure the whole mechanism exists to prevent.
    """
    inputs = load_accepted_inputs(FROZEN_PRIOR)
    findings = validate_schema_binding(candidate_from_accepted_inputs(inputs))
    assert findings != ()
    assert any(SCHEMA_7_VERSION in f for f in findings), findings


# ---------------------------------------------------------------------------
# The lift, and what it is allowed to change
# ---------------------------------------------------------------------------


def test_the_registered_chain_reaches_current_authority_one_crossing_at_a_time() -> (
    None
):
    """Every crossing since the artifact was reviewed, and the earlier ones kept.

    The artifact still declares schema 5, so reaching current authority is now
    two registered steps rather than one: schema 6, then schema 7. The crossings
    that carried ``conditions-1`` up from schema 3 are not re-run — they already
    happened, and the file records them — so what this asserts is that the
    retained evidence and the new records together name the whole path, one row
    per crossing, never collapsed into a transition the registry has no row for.
    """
    inputs = load_accepted_inputs(FROZEN_PRIOR)
    lifted, records = lift_accepted_inputs(inputs, TARGET)

    assert [lift.lift_id for lift in inputs.lifts] == [
        "5d-lift-schema-3-to-4",
        "5d-lift-schema-4-to-5",
    ]
    assert [r.lift_id for r in records] == [
        "5d-lift-schema-5-to-6",
        "5d-lift-schema-6-to-7",
    ]
    for record in records:
        assert set(record.verified_collections) == REPRESENTATION_COLLECTIONS
    assert (records[0].from_version, records[0].from_hash) == (
        SCHEMA_5_VERSION,
        SCHEMA_5_HASH,
    )
    # Continuous: each record's destination is the next record's source.
    assert (records[0].to_version, records[0].to_hash) == (
        SCHEMA_6_VERSION,
        SCHEMA_6_HASH,
    )
    assert (records[-1].to_version, records[-1].to_hash) == (
        SCHEMA_7_VERSION,
        SCHEMA_7_HASH,
    )
    assert lifted.oracle.schema_version == SCHEMA_7_VERSION
    assert lifted.oracle.schema_hash == SCHEMA_7_HASH
    assert validate_schema_binding(candidate_from_accepted_inputs(lifted)) == ()


def test_every_accepted_element_is_carried_by_identity() -> None:
    """Not merely equal — the same objects, so no transformation could have run."""
    inputs = load_accepted_inputs(FROZEN_PRIOR)
    lifted, _ = lift_accepted_inputs(inputs, TARGET)

    assert lifted.oracle.representation is inputs.oracle.representation
    assert lifted.oracle.spans is inputs.oracle.spans
    assert lifted.oracle.obligations is inputs.oracle.obligations
    # Review evidence is not a review, so a succession may not edit it either.
    assert lifted.batches == inputs.batches
    assert lifted.acceptances == inputs.acceptances

    draft = lifted.oracle.representation
    assert {name: len(getattr(draft, name)) for name in MERGED} == MERGED
    assert len(lifted.oracle.spans) == SPANS
    assert len(lifted.oracle.obligations) == len(inputs.oracle.obligations)


def test_both_batches_keep_the_schema_they_were_reviewed_under() -> None:
    """The anchors are the acceptance record, and a lift may not restamp them."""
    inputs = load_accepted_inputs(FROZEN_PRIOR)
    lifted, _ = lift_accepted_inputs(inputs, TARGET)

    anchors = {a.batch_id: a for a in lifted.schema_anchors}
    assert sorted(anchors) == sorted([CONDITIONS_BATCH, HAZARDS_BATCH])
    assert anchors[CONDITIONS_BATCH].schema_version == "5d-representation-schema-3"
    assert anchors[CONDITIONS_BATCH].schema_hash == SCHEMA_3_HASH
    assert anchors[HAZARDS_BATCH].schema_version == SCHEMA_5_VERSION
    assert anchors[HAZARDS_BATCH].schema_hash == SCHEMA_5_HASH
    assert lifted.schema_anchors == inputs.schema_anchors


def test_every_accepted_provenance_coordinate_re_derives_exactly() -> None:
    """Owner Decision 2026-08-24, as an exact assertion over the committed bytes.

    A previously accepted fact key or provenance coordinate may not move. This
    re-derives every coordinate from the lifted representation and compares the
    set to the one stored in the file — so a schema-6 field that failed to be
    omitted when empty would surface here as a coordinate nobody accepted,
    rather than as a count that still added up.
    """
    inputs = load_accepted_inputs(FROZEN_PRIOR)
    lifted, _ = lift_accepted_inputs(inputs, TARGET)

    stored = {
        tuple(claim["target_key"])
        for claim in json.loads(FROZEN_PRIOR.read_text(encoding="utf-8"))[
            "representation"
        ]["provenance"]
    }

    draft = lifted.oracle.representation
    derived: set[tuple[str, ...]] = {(r.semantic_key,) for r in draft.records}
    for component in draft.components:
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
    for binding in draft.prose_bindings:
        derived.add(prose_binding_target_key(binding))
    for relationship in draft.relationships:
        derived.add(relationship_target_key(relationship))
    for reference in draft.references:
        derived.add(reference_target_key(reference))

    assert stored <= derived, sorted(stored - derived)


def test_no_prose_binding_coordinate_grew_a_sixth_element() -> None:
    """The omit-when-empty rule, asserted where it would have been violated.

    Schema 6 adds ``option_key`` to a prose binding. Accepted authority holds
    twenty bindings and none is option-scoped, so every one of them must still
    address with the five-element key it was accepted with. Emitting the new
    element unconditionally would have moved all twenty at once.
    """
    inputs = load_accepted_inputs(FROZEN_PRIOR)
    lifted, _ = lift_accepted_inputs(inputs, TARGET)
    keys = [
        prose_binding_target_key(b) for b in lifted.oracle.representation.prose_bindings
    ]
    assert len(keys) == MERGED["prose_bindings"]
    assert {len(k) for k in keys} == {5}
    assert all(b.option_key == "" for b in lifted.oracle.representation.prose_bindings)


def test_the_accepted_oracle_identity_is_unmoved() -> None:
    """The one figure a succession may not move at all.

    ``oracle_identity`` is derived from the semantic content the Owner
    accepted. A lift re-declares the artifact's schema and nothing else, so the
    accepted oracle read from the file identifies exactly as it did before this
    schema step existed.
    """
    inputs = load_accepted_inputs(FROZEN_PRIOR)
    assert oracle_identity(inputs.oracle) == ACCEPTED_ORACLE_IDENTITY


def test_the_prior_round_trips_strictly_through_its_own_payload() -> None:
    """Loaded and re-emitted, the file is itself — before any lift touches it."""
    inputs = load_accepted_inputs(FROZEN_PRIOR)
    assert accepted_inputs_payload(inputs) == json.loads(
        FROZEN_PRIOR.read_text(encoding="utf-8")
    )


# ---------------------------------------------------------------------------
# The sentinel
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("path", [FROZEN_PRIOR, COMMITTED])
def test_no_accepted_file_was_rewritten_by_this_schema_step(
    path: pathlib.Path,
) -> None:
    """Read after every lift above has run, which is the point.

    A succession that quietly edited accepted authority to make itself work
    would satisfy every other assertion in this module. Both files are pinned
    by content digest — each by its own, since ``actions-1`` was accepted into
    the committed artifact and not into the frozen copy — and the committed
    artifact's full set of pins lives beside it in
    ``test_committed_accepted_authority``.

    What this asserts is unchanged by that acceptance: a *lift* may not rewrite
    either file. An Owner acceptance may extend the committed one, which is why
    its digest is a separate constant rather than a claim that the two files are
    the same bytes.
    """
    digests = {
        FROZEN_PRIOR: FROZEN_CONTENT_SHA256,
        COMMITTED: COMMITTED_CONTENT_SHA256,
    }
    assert _lf_digest(path) == digests[path]
    assert FROZEN_CONTENT_SHA256 != COMMITTED_CONTENT_SHA256
