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
``git cat-file blob b7c0149432072d4a3b151d0f9b2c458252e584da``, which is the
live accepted artifact's blob as this freeze is taken. At this moment the two
files are the same content, and that is asserted rather than assumed. Accepting
``speed-1`` would extend the live file and end that equality; when it does, this
module's last test is the one that must change, and it names in advance what
should replace it — the live artifact is this prior plus exactly one batch, and
every batch the freeze holds is still present and identical.

**No crossing separates this prior from the checkout.** ``cover-1``'s freeze was
taken at schema 9 and the build that reviewed it declared schema 10, so exactly
one registered lift stood between them. This freeze is taken *at* schema 10,
which is the checkout's own binding, so the honest assertion is the opposite
one: reading this prior as current is not a finding, no lift path exists, and a
generator that reached for one would raise. Whether ``speed-1`` needs a schema
11 is a question for its discovery checkpoint and is not prejudged here.

**What this module does not do.** It proves nothing about representation, and
nothing about the live artifact beyond the equality claim. Every pin describes
the *frozen* file: the six batches it holds, its 47 records, and the two
reference targets it cannot resolve — the honest starting position ``speed-1``
is measured from, not a list to be worked through. One of those two,
``glossary.speed``, is the citation this batch exists to consider; the other
remains open and out of its cut.
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
    UnknownSchemaLiftError,
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
    and records the seven crossings that carried it there, and it will still say
    schema 10 after any schema 11. A crossing to a *later* union is a property of
    the pair, not a field this file gains.
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


def test_no_crossing_separates_this_prior_from_the_checkout() -> None:
    """The position at the freeze, stated rather than assumed.

    ``cover-1``'s freeze was taken one registered step behind its own build and
    said so. This one is taken level with the checkout, so the assertions invert:
    the prior's binding *is* the current binding, reading it as current is not a
    finding, and no lift path exists between them. A generator that reached for
    a self-lift raises rather than silently no-opping, which is what keeps
    "level" from being indistinguishable from "not checked".

    Whether ``speed-1`` needs a schema 11 is not decided here. If one is minted,
    this test is where the crossing becomes visible: ``prior != current`` and a
    one-step path appears, exactly as ``cover-1``'s equivalent recorded.
    """
    inputs = load_accepted_inputs(FROZEN_PRIOR)
    current = (REPRESENTATION_SCHEMA_VERSION, representation_schema_hash())
    prior = (inputs.oracle.schema_version, inputs.oracle.schema_hash)
    assert prior == (SCHEMA_10_VERSION, SCHEMA_10_HASH)
    assert prior == current

    assert validate_schema_binding(candidate_from_accepted_inputs(inputs)) == ()
    assert oracle_identity(inputs.oracle) == ACCEPTED_ORACLE_IDENTITY

    try:
        lift_path(prior, current)
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


def test_the_committed_artifact_is_still_this_copy_byte_for_byte() -> None:
    """The copy, attached to what it was copied from.

    Taking the freeze changes nothing about accepted authority, so until the
    Owner accepts another batch the live artifact and this copy are the same
    content. That equality is asserted rather than assumed, because a freeze
    that had silently copied something else would otherwise pass every test
    above.

    **What replaces this test.** An acceptance of ``speed-1`` extends the live
    file and ends the equality. The replacement is the shape ``cover-1``'s
    freeze ended at: assert the live digest *differs*, assert the live batch set
    is this one plus exactly the newly accepted batch, and assert every batch the
    freeze holds is still present and identical — which is the part that would
    catch a merge rewriting history. Naming it here means the edit is a
    recorded succession rather than a deletion.
    """
    assert _lf_digest(FROZEN_PRIOR) == FROZEN_CONTENT_SHA256
    assert _blob_id(FROZEN_PRIOR) == FROZEN_BLOB
    assert _lf_digest(COMMITTED) == FROZEN_CONTENT_SHA256

    frozen = {b.batch_id: b for b in load_accepted_inputs(FROZEN_PRIOR).batches}
    committed = {b.batch_id: b for b in load_accepted_inputs(COMMITTED).batches}
    assert set(committed) == set(frozen) == set(BATCH_IDS)
    assert {k: committed[k] for k in frozen} == frozen
