"""The frozen three-batch prior successor batches are reviewed against — CRD Issue 5d.

``data/accepted_prior_conditions_1_hazards_1_actions_1.json`` is a byte-for-byte
copy of accepted authority as it stood after the Owner accepted ``actions-1``:
``conditions-1``, ``hazards-1`` and ``actions-1``, anchored at representation
schema 7. Successor batches derive their merge evidence against *this* file
rather than against the live committed artifact, so a later acceptance cannot
silently re-date a proposal's evidence — a proposal reviewed against a prior
that has since moved was reviewed against something the reviewer never saw.

**Why a second frozen copy exists.** ``accepted_prior_conditions_1_hazards_1``
froze the two-batch authority a *schema step* would otherwise have rewritten
under it. This copy was taken while ``attitudes-1`` still looked like a
same-schema batch, and the schema-8 succession it eventually needed is exactly
the case the freeze was for: the bytes are untouched, so the prior a reviewer
reads is the prior the proposal was built against, and the one registered
crossing between it and the current union is *stated* here rather than assumed.
It was the same bytes as the committed artifact until the Owner accepted
``attitudes-1``; the committed artifact has since been extended again by
``areas-of-effect-1`` and this copy has not moved, which is the whole point of
taking it.

**What this module does not do.** It proves nothing about the live artifact
beyond the one extension assertion at the end. Every pin below describes the
*frozen* file: the three batches it holds, the 35 records, and the five
reference targets it cannot resolve — the honest starting position
``attitudes-1`` was measured from, not a list to be worked through. The
committed artifact's own pins live in ``test_committed_accepted_authority``.
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
    SCHEMA_7_VERSION,
    UnknownSchemaLiftError,
    lift_accepted_inputs,
    lift_path,
)

DATA = pathlib.Path(__file__).resolve().parent / "data"
FROZEN_PRIOR = DATA / "accepted_prior_conditions_1_hazards_1_actions_1.json"
COMMITTED = COMMITTED_ORACLE_DIR / "srd-5-2-1-corpus-36b786d8-fa2.json"

#: Two independent identities of the frozen copy, so an edit cannot pass as a
#: reformat. LF-normalized, which is what ``.gitattributes`` declares.
FROZEN_CONTENT_SHA256 = "87864b6ac81e4f8baf57eddf9524dade1b2045a5fc804c79b3d57412c87f46fc"  # noqa: E501  # pragma: allowlist secret
FROZEN_BLOB = "a729a797594e1156b279fac76c3073c733707a2f"  # pragma: allowlist secret

#: Derived from the semantic content the Owner accepted, and the figure any
#: successor batch's merge evidence names as the prior it was built against.
ACCEPTED_ORACLE_IDENTITY = "8c41b01e92878c614fad5c039c006c66221a4cc55cfab68698ef9302865a6eee"  # noqa: E501  # pragma: allowlist secret

BATCH_IDS = ["actions-1", "conditions-1", "hazards-1"]

#: What the three accepted batches hold together, so a collection that silently
#: gained or lost an element fails by name rather than by total.
MERGED = {
    "records": 35,
    "components": 106,
    "prose_bindings": 47,
    "relationships": 0,
    "references": 39,
    "provenance": 480,
}
SPANS = 463
OBLIGATIONS = 35

#: Reference targets accepted authority cites and does not define. Pinned as a
#: set, not a count: this is the exact residue a successor batch's merge
#: evidence claims to move, and a batch that resolved a different target than
#: it said it would must fail here.
UNRESOLVED_TARGETS = {
    "attitude.friendly",
    "attitude.hostile",
    "attitude.indifferent",
    "glossary.concentration",
    "glossary.speed",
}


def _lf_digest(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _blob_id(path: pathlib.Path) -> str:
    body = path.read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha1(b"blob %d\0" % len(body) + body).hexdigest()  # noqa: S324


def test_the_frozen_prior_is_the_three_batch_authority_it_claims_to_be() -> None:
    assert _lf_digest(FROZEN_PRIOR) == FROZEN_CONTENT_SHA256
    assert _blob_id(FROZEN_PRIOR) == FROZEN_BLOB

    inputs = load_accepted_inputs(FROZEN_PRIOR)
    assert oracle_identity(inputs.oracle) == ACCEPTED_ORACLE_IDENTITY
    assert inputs.oracle.schema_version == SCHEMA_7_VERSION
    assert inputs.oracle.schema_hash == SCHEMA_7_HASH
    assert sorted(b.batch_id for b in inputs.batches) == BATCH_IDS
    # One acceptance per span, not per batch: every accepted span names the
    # batch it was accepted in, and all three batches are represented.
    assert sorted({a.batch_id for a in inputs.acceptances}) == BATCH_IDS
    assert len(inputs.acceptances) == SPANS

    draft = inputs.oracle.representation
    assert {name: len(getattr(draft, name)) for name in MERGED} == MERGED
    assert len(inputs.oracle.spans) == SPANS
    assert len(inputs.oracle.obligations) == OBLIGATIONS


def test_each_batch_still_names_the_schema_it_was_reviewed_under() -> None:
    """Three batches, three different anchors, none restamped by the merge.

    ``actions-1`` was reviewed under schema 7 and the two earlier batches were
    not. The artifact declaring schema 7 as a whole is what it was *lifted* to;
    what each batch was *accepted* under is the acceptance record, and no
    successor batch may collapse the three into one.
    """
    anchors = {a.batch_id: a for a in load_accepted_inputs(FROZEN_PRIOR).schema_anchors}
    assert sorted(anchors) == BATCH_IDS
    assert anchors["conditions-1"].schema_hash == SCHEMA_3_HASH
    assert anchors["hazards-1"].schema_hash == SCHEMA_5_HASH
    assert anchors["actions-1"].schema_hash == SCHEMA_7_HASH


def test_the_prior_declares_schema_7_and_records_the_four_lifts_that_got_it_there() -> (
    None
):
    """What the file itself carries, which no successor schema restamps.

    Accepted bytes are never re-declared in place: the artifact says schema 7
    and records the four crossings that carried it there, and it will still say
    schema 7 after schema 9. The crossing to the *current* union is a property
    of the pair, proved in the next test, not a field this file gains.
    """
    inputs = load_accepted_inputs(FROZEN_PRIOR)
    assert (inputs.oracle.schema_version, inputs.oracle.schema_hash) == (
        SCHEMA_7_VERSION,
        SCHEMA_7_HASH,
    )
    assert [lift.lift_id for lift in inputs.lifts] == [
        "5d-lift-schema-3-to-4",
        "5d-lift-schema-4-to-5",
        "5d-lift-schema-5-to-6",
        "5d-lift-schema-6-to-7",
    ]


def test_the_registered_crossings_separate_the_prior_from_this_build() -> None:
    """The succession ``attitudes-1``'s prior takes, named rather than counted.

    Schema 8 admitted one family this prior's contract cannot state, and schema
    9 admitted seven more for ``areas-of-effect-1``. The prior is therefore no
    longer current and reading it as current is a *finding* rather than a silent
    pass. The registered steps that close the gap are named here in order, and
    the identity the Owner accepted survives them — ``lift`` re-declares the
    binding and proves the content unmoved, it does not rewrite content.

    The list, not its length, is the claim: a step appearing here that nobody
    registered, or a registered step missing from it, both fail.

    A self-lift stays unregistered, so a generator that reached for one would
    raise rather than silently no-op.
    """
    inputs = load_accepted_inputs(FROZEN_PRIOR)
    current = (REPRESENTATION_SCHEMA_VERSION, representation_schema_hash())
    prior = (inputs.oracle.schema_version, inputs.oracle.schema_hash)
    assert prior != current

    findings = validate_schema_binding(candidate_from_accepted_inputs(inputs))
    assert findings, "reading a superseded prior as current must be visible"
    assert any(REPRESENTATION_SCHEMA_VERSION in f for f in findings), findings

    expected = ["5d-lift-schema-7-to-8", "5d-lift-schema-8-to-9"]
    assert [step.lift_id for step in lift_path(prior, current)] == expected
    lifted, records = lift_accepted_inputs(inputs, current)
    assert [record.lift_id for record in records] == expected
    assert validate_schema_binding(candidate_from_accepted_inputs(lifted)) == ()
    assert lifted.oracle.representation is inputs.oracle.representation
    assert oracle_identity(inputs.oracle) == ACCEPTED_ORACLE_IDENTITY

    try:
        lift_path(current, current)
    except UnknownSchemaLiftError:
        pass
    else:  # pragma: no cover - would mean a self-lift got registered
        raise AssertionError("a self-lift is registered")


def test_the_unresolved_reference_targets_are_exactly_the_recorded_residue() -> None:
    """What accepted authority cites and cannot yet resolve.

    Successor batches record how many of these their merge closes. Pinning the
    set here is what makes that claim checkable: a batch that reported closing
    three of five is only telling the truth if these are the five.
    """
    draft = load_accepted_inputs(FROZEN_PRIOR).oracle.representation
    defined = {record.semantic_key for record in draft.records}
    dangling = {
        reference.target_record_key
        for reference in draft.references
        if reference.target_record_key not in defined
    }
    assert dangling == UNRESOLVED_TARGETS


def test_the_prior_round_trips_strictly_through_its_own_payload() -> None:
    """Loaded and re-emitted, the file is itself."""
    inputs = load_accepted_inputs(FROZEN_PRIOR)
    assert accepted_inputs_payload(inputs) == json.loads(
        FROZEN_PRIOR.read_text(encoding="utf-8")
    )


def test_the_committed_artifact_extends_this_copy_by_the_batches_since() -> None:
    """The successor relationship, now two acceptances deep.

    The first revision asserted the two files were the same bytes; the Owner's
    acceptance of ``attitudes-1`` ended that and this became the
    extends-by-exactly-one claim. ``areas-of-effect-1`` makes it two, so the
    claim is generalized rather than re-pinned to a single batch name: whatever
    has been accepted since the freeze is named exactly, and every batch the
    freeze holds must still be present and identical, which is the part that
    would catch a merge rewriting history. Narrowing it back to one batch, or
    deleting it, would leave the copy unattached to what it was copied from.
    """
    assert _lf_digest(FROZEN_PRIOR) == FROZEN_CONTENT_SHA256
    assert _lf_digest(COMMITTED) != FROZEN_CONTENT_SHA256

    frozen = {b.batch_id: b for b in load_accepted_inputs(FROZEN_PRIOR).batches}
    committed = {b.batch_id: b for b in load_accepted_inputs(COMMITTED).batches}
    assert set(committed) - set(frozen) == {"attitudes-1", "areas-of-effect-1"}
    assert {k: committed[k] for k in frozen} == frozen
