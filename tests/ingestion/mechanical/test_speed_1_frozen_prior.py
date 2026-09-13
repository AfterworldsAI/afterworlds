"""The frozen six-batch prior ``speed-1`` is reviewed against — CRD Issue 5d.

``data/accepted_prior_conditions_1_hazards_1_actions_1_attitudes_1``
``_areas_of_effect_1_cover_1.json`` is a byte-for-byte copy of accepted
authority as it stood after the Owner accepted ``cover-1`` on 2026-09-11:
``conditions-1``, ``hazards-1``, ``actions-1``, ``attitudes-1``,
``areas-of-effect-1`` and ``cover-1``, anchored at representation schema 10.
``speed-1`` derives its evidence against *this* file rather than against the
live committed artifact, so a later acceptance cannot silently re-date the
evidence — a batch reviewed against a prior that has since moved was reviewed
against something the reviewer never saw.

**The copy is the preservation proof.** The fixture is
``git cat-file blob b7c0149432072d4a3b151d0f9b2c458252e584da``, which was the
live accepted artifact's blob when the freeze was taken. The Owner's acceptance
of ``speed-1`` on 2026-09-12 extended the live file, so the copy no longer
matches it byte for byte; what it now proves is that the extension *carried*
this prior — every batch here is still present in the live artifact and
identical. That is the replacement the previous form of this module's last test
named in advance, made rather than deleted. Both fixture identities stay pinned
— blob sha1 and LF sha256 — and every other pin below is derived by loading the
file rather than transcribed.

**Exactly one registered crossing separates this prior from this build.** The
freeze was taken *at* schema 10, level with the checkout, and this module's
crossing test named in advance what would have to change if ``speed-1`` needed
a schema 11. It did: the two defining Speed sites print meanings schema 10
cannot state, this build mints schema 11, and ``5d-lift-schema-10-to-11`` is
the single registered step between the frozen prior and the checkout. The
frozen bytes do not move; a crossing to a *later* union is a property of the
pair, not a field the file gains.

**What this module does not do.** It proves nothing about representation, and
nothing about the live artifact beyond the equality claim. Every pin describes
the *frozen* file: the six batches it holds, its 47 records, and the two
reference targets it cannot resolve — the honest starting position ``speed-1``
was measured from, not a list to be worked through. ``speed-1`` resolved one of
those two, ``glossary.speed``, by defining the record, and emitted nine outgoing
citations of its own; ``glossary.concentration`` was outside its cut and remains
open. Where the live artifact now stands is pinned in
``test_committed_accepted_authority``, not here.
"""

from __future__ import annotations

import hashlib
import json
import pathlib

from afterworlds.ingestion.mechanical.oracle import (
    COMMITTED_ORACLE_DIR,
    accepted_inputs_payload,
    candidate_from_accepted_inputs,
    load_accepted_inputs,
    oracle_identity,
    oracle_payload,
)
from afterworlds.ingestion.mechanical.projection import validate_schema_binding
from afterworlds.ingestion.mechanical.representation import (
    REPRESENTATION_SCHEMA_VERSION,
    representation_schema_hash,
)
from afterworlds.ingestion.mechanical.schema_lift import (
    SCHEMA_3_HASH,
    SCHEMA_5_HASH,
    SCHEMA_7_HASH,
    SCHEMA_8_HASH,
    SCHEMA_9_HASH,
    SCHEMA_10_HASH,
    SCHEMA_10_VERSION,
    SCHEMA_11_HASH,
    SCHEMA_11_VERSION,
    UnknownSchemaLiftError,
    lift_accepted_inputs,
    lift_path,
)

DATA = pathlib.Path(__file__).resolve().parent / "data"
FROZEN_PRIOR = DATA / (
    "accepted_prior_conditions_1_hazards_1_actions_1"
    "_attitudes_1_areas_of_effect_1_cover_1.json"
)
COMMITTED = COMMITTED_ORACLE_DIR / "srd-5-2-1-corpus-36b786d8-fa2.json"

#: Two independent identities of the frozen copy, so an edit cannot pass as a
#: reformat. LF-normalized, which is what ``.gitattributes`` declares.
FROZEN_CONTENT_SHA256 = "391c71b72d7fa9406890c74eed9a505278ea4f8f4536a01cd3db1edf403f6407"  # noqa: E501  # pragma: allowlist secret
FROZEN_BLOB = "b7c0149432072d4a3b151d0f9b2c458252e584da"  # pragma: allowlist secret

#: Derived from the semantic content the Owner accepted, and the figure
#: ``speed-1``'s evidence names as the prior it was built against.
ACCEPTED_ORACLE_IDENTITY = "86cd11c2be330f5962982d8d87dfc1847815710868223257529f30bef8cdb500"  # noqa: E501  # pragma: allowlist secret

BATCH_IDS = [
    "actions-1",
    "areas-of-effect-1",
    "attitudes-1",
    "conditions-1",
    "cover-1",
    "hazards-1",
]

#: What the six accepted batches hold together, so a collection that silently
#: gained or lost an element fails by name rather than by total.
MERGED = {
    "records": 47,
    "components": 136,
    "prose_bindings": 49,
    "relationships": 0,
    "references": 53,
    "provenance": 575,
}
SPANS = 558
OBLIGATIONS = 47

#: Reference targets accepted authority cites and does not define, and the two
#: standing publication blockers as of this freeze. Pinned as a set, not a
#: count: this is the exact residue ``speed-1``'s evidence is measured against,
#: and a batch that resolved a different target than it said it would must fail
#: here. ``glossary.speed`` is the one ``speed-1`` exists to consider;
#: ``glossary.concentration`` remains outside its cut.
UNRESOLVED_TARGETS = {
    "glossary.concentration",
    "glossary.speed",
}


def _lf_digest(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _blob_id(path: pathlib.Path) -> str:
    body = path.read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha1(b"blob %d\0" % len(body) + body).hexdigest()  # noqa: S324


def test_the_frozen_prior_is_the_six_batch_authority_it_claims_to_be() -> None:
    assert _lf_digest(FROZEN_PRIOR) == FROZEN_CONTENT_SHA256
    assert _blob_id(FROZEN_PRIOR) == FROZEN_BLOB

    inputs = load_accepted_inputs(FROZEN_PRIOR)
    assert oracle_identity(inputs.oracle) == ACCEPTED_ORACLE_IDENTITY
    assert inputs.oracle.schema_version == SCHEMA_10_VERSION
    assert inputs.oracle.schema_hash == SCHEMA_10_HASH
    assert sorted(b.batch_id for b in inputs.batches) == BATCH_IDS
    # One acceptance per span, not per batch: every accepted span names the
    # batch it was accepted in, and all six batches are represented.
    assert sorted({a.batch_id for a in inputs.acceptances}) == BATCH_IDS
    assert len(inputs.acceptances) == SPANS

    draft = inputs.oracle.representation
    assert {name: len(getattr(draft, name)) for name in MERGED} == MERGED
    assert len(inputs.oracle.spans) == SPANS
    assert len(inputs.oracle.obligations) == OBLIGATIONS


def test_each_batch_still_names_the_schema_it_was_reviewed_under() -> None:
    """Six batches, six different anchors, none restamped by the merge.

    Only ``cover-1`` was reviewed under schema 10. The artifact declaring schema
    10 as a whole is what its predecessors were *lifted* to; what each batch was
    *accepted* under is the acceptance record, and ``speed-1`` may not collapse
    the six into one.
    """
    anchors = {a.batch_id: a for a in load_accepted_inputs(FROZEN_PRIOR).schema_anchors}
    assert sorted(anchors) == BATCH_IDS
    assert anchors["conditions-1"].schema_hash == SCHEMA_3_HASH
    assert anchors["hazards-1"].schema_hash == SCHEMA_5_HASH
    assert anchors["actions-1"].schema_hash == SCHEMA_7_HASH
    assert anchors["attitudes-1"].schema_hash == SCHEMA_8_HASH
    assert anchors["areas-of-effect-1"].schema_hash == SCHEMA_9_HASH
    assert anchors["cover-1"].schema_hash == SCHEMA_10_HASH


def test_the_prior_declares_schema_10_and_records_the_seven_lifts_that_got_it_there() -> (  # noqa: E501
    None
):
    """What the file itself carries, which no successor schema restamps.

    Accepted bytes are never re-declared in place: the artifact says schema 10
    and records the seven crossings that carried it there, and it still says
    schema 10 now that this build declares schema 11. A crossing to a *later*
    union is a property of the pair, not a field this file gains.
    """
    inputs = load_accepted_inputs(FROZEN_PRIOR)
    assert (inputs.oracle.schema_version, inputs.oracle.schema_hash) == (
        SCHEMA_10_VERSION,
        SCHEMA_10_HASH,
    )
    assert [lift.lift_id for lift in inputs.lifts] == [
        "5d-lift-schema-3-to-4",
        "5d-lift-schema-4-to-5",
        "5d-lift-schema-5-to-6",
        "5d-lift-schema-6-to-7",
        "5d-lift-schema-7-to-8",
        "5d-lift-schema-8-to-9",
        "5d-lift-schema-9-to-10",
    ]


def test_exactly_one_registered_crossing_separates_the_prior_from_this_build() -> None:
    """The position after the mint, stated rather than assumed.

    This is the edit the previous form of this test named in advance. The freeze
    was taken level with the checkout; the checkpoint's question was whether
    ``speed-1`` needs a schema 11, and the answer was yes, so the assertions
    invert: the prior's binding is no longer the current binding, reading it as
    current is a *finding* rather than a silent pass, and exactly one registered
    step closes the gap.

    **Two identities, two scopes.** The frozen authority is untouched on disk and
    keeps the identity the Owner accepted. Its lifted copy is a *different*
    object with a *different* identity, because ``oracle_payload`` carries the
    representation binding and the lift re-declares exactly that. The content is
    what survives, and identically rather than equally: the lifted copy holds the
    same representation object, and the only top-level payload key that moves is
    ``representation_schema``.

    **The six schema anchors cross untouched.** That is the assertion schema 11
    most needs to make, because like schema 10 it widens a vocabulary accepted
    authority already uses: ``MovementMode`` gains ``jump``, and four accepted
    batches state members of that vocabulary. A lift that re-derived anchors
    would erase the record of what each batch was accepted under, which is the
    distinction the whole mechanism protects.

    A self-lift stays unregistered, so a generator that reached for one here
    would raise rather than silently no-op.
    """
    inputs = load_accepted_inputs(FROZEN_PRIOR)
    current = (REPRESENTATION_SCHEMA_VERSION, representation_schema_hash())
    prior = (inputs.oracle.schema_version, inputs.oracle.schema_hash)
    assert prior == (SCHEMA_10_VERSION, SCHEMA_10_HASH)
    assert current == (SCHEMA_11_VERSION, SCHEMA_11_HASH)
    assert prior != current

    findings = validate_schema_binding(candidate_from_accepted_inputs(inputs))
    assert findings, "reading a superseded prior as current must be visible"
    assert any(REPRESENTATION_SCHEMA_VERSION in f for f in findings), findings

    expected = ["5d-lift-schema-10-to-11"]
    assert [step.lift_id for step in lift_path(prior, current)] == expected
    lifted, records = lift_accepted_inputs(inputs, current)
    assert [record.lift_id for record in records] == expected
    assert validate_schema_binding(candidate_from_accepted_inputs(lifted)) == ()
    assert lifted.oracle.representation is inputs.oracle.representation
    assert oracle_identity(inputs.oracle) == ACCEPTED_ORACLE_IDENTITY

    # The lifted copy is newly bound, so it is newly identified. Asserted
    # structurally rather than against a literal: the value moves every time the
    # destination pin moves, and what is being proved is *why* it moves.
    assert oracle_identity(lifted.oracle) != ACCEPTED_ORACLE_IDENTITY
    before = oracle_payload(inputs.oracle)
    after = oracle_payload(lifted.oracle)
    moved = {k for k in set(before) | set(after) if before.get(k) != after.get(k)}
    assert moved == {"representation_schema"}, sorted(moved)

    # Everything the prior carries besides the binding crosses untouched, and by
    # identity rather than equality -- the lift rebinds, it does not rebuild.
    for field in ("batches", "acceptances", "schema_anchors"):
        assert getattr(lifted, field) is getattr(inputs, field), field
    assert lifted.oracle.spans is inputs.oracle.spans
    assert lifted.oracle.obligations is inputs.oracle.obligations
    # Named per batch as well as by identity, because this is the assertion the
    # vocabulary widening would break first if a lift ever re-derived them.
    crossed = {a.batch_id: a.schema_hash for a in lifted.schema_anchors}
    assert crossed == {
        "conditions-1": SCHEMA_3_HASH,
        "hazards-1": SCHEMA_5_HASH,
        "actions-1": SCHEMA_7_HASH,
        "attitudes-1": SCHEMA_8_HASH,
        "areas-of-effect-1": SCHEMA_9_HASH,
        "cover-1": SCHEMA_10_HASH,
    }

    try:
        lift_path(current, current)
    except UnknownSchemaLiftError:
        pass
    else:  # pragma: no cover - would mean a self-lift got registered
        raise AssertionError("a self-lift is registered")


def test_the_unresolved_reference_targets_are_exactly_the_recorded_residue() -> None:
    """What accepted authority cites and cannot yet resolve.

    ``cover-1`` closed ``glossary.cover`` and added none. Pinning the set here is
    what makes ``speed-1``'s own reference-scope claim checkable against the
    position it started from rather than against a remembered one.
    """
    draft = load_accepted_inputs(FROZEN_PRIOR).oracle.representation
    defined = {record.semantic_key for record in draft.records}
    dangling = {
        reference.target_record_key
        for reference in draft.references
        if reference.target_record_key not in defined
    }
    assert dangling == UNRESOLVED_TARGETS


def test_the_one_accepted_citation_of_speed_is_the_reference_this_batch_inherits() -> (
    None
):
    """The whole of what accepted authority currently says about ``Speed``.

    One reference, from ``action.dash``, scoped to the Rules Glossary, with the
    printed ``Speed`` as its source text — and no record, no component and no
    span anywhere in the prior that defines the target. That asymmetry is the
    reason ``speed-1`` exists, and stating it here keeps the discovery
    checkpoint's reference-scope section measured against the file rather than
    against prose.

    It also bounds the claim in the other direction. ``Dash`` prints *"such as a
    Fly Speed or Swim Speed"* in its own body and emitted **no** reference for
    either, so accepted authority already treats a named example inside
    substantive prose as part of the rule rather than as a citation. That is the
    precedent ``speed-1``'s outbound-reference judgment is measured against.
    """
    draft = load_accepted_inputs(FROZEN_PRIOR).oracle.representation
    citing = [
        reference
        for reference in draft.references
        if reference.target_record_key == "glossary.speed"
    ]
    assert [
        (
            reference.from_record_key,
            reference.from_component_key,
            reference.scope_key,
            reference.source_text,
        )
        for reference in citing
    ] == [("action.dash", "", "srd-5.2.1/rules-glossary", "Speed")]
    assert "glossary.speed" not in {record.semantic_key for record in draft.records}
    # No reference anywhere targets a special speed, under any spelling.
    assert not [
        reference
        for reference in draft.references
        if "speed" in reference.target_record_key
        and reference.target_record_key != "glossary.speed"
    ]


def test_the_prior_round_trips_strictly_through_its_own_payload() -> None:
    """Loaded and re-emitted, the file is itself."""
    inputs = load_accepted_inputs(FROZEN_PRIOR)
    assert accepted_inputs_payload(inputs) == json.loads(
        FROZEN_PRIOR.read_text(encoding="utf-8")
    )


def test_the_committed_artifact_extends_this_copy_by_exactly_one_batch() -> None:
    """The copy, attached to what it was copied from.

    Taking the freeze changed nothing about accepted authority, and until the
    Owner accepted ``speed-1`` the live artifact and this copy were the same
    content. The previous form of this test named that acceptance as the thing
    that would end it and named what should replace it, so this is that
    replacement rather than a deletion: the live artifact is this prior plus
    exactly one batch, and every batch the freeze holds is still present and
    identical, which is the part that would catch a merge rewriting history.

    The fixture's own two pins are asserted above and are unchanged by the
    acceptance; what moved is the live file, so its digest is asserted to
    *differ* rather than transcribed here. The committed artifact's own pins
    live in ``test_committed_accepted_authority``.
    """
    assert _lf_digest(FROZEN_PRIOR) == FROZEN_CONTENT_SHA256
    assert _blob_id(FROZEN_PRIOR) == FROZEN_BLOB
    assert _lf_digest(COMMITTED) != FROZEN_CONTENT_SHA256

    frozen = {b.batch_id: b for b in load_accepted_inputs(FROZEN_PRIOR).batches}
    committed = {b.batch_id: b for b in load_accepted_inputs(COMMITTED).batches}
    assert set(committed) - set(frozen) == {"speed-1"}
    assert {k: committed[k] for k in frozen} == frozen
