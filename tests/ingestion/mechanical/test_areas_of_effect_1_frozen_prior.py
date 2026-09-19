"""The frozen four-batch prior ``areas-of-effect-1`` is reviewed against — CRD Issue 5d.

``data/accepted_prior_conditions_1_hazards_1_actions_1_attitudes_1.json`` is a
byte-for-byte copy of accepted authority as it stood after the Owner accepted
``attitudes-1`` on 2026-09-10: ``conditions-1``, ``hazards-1``, ``actions-1``
and ``attitudes-1``, anchored at representation schema 8. ``areas-of-effect-1``
derives its merge evidence against *this* file rather than against the live
committed artifact, so a later acceptance cannot silently re-date the evidence
— a proposal reviewed against a prior that has since moved was reviewed against
something the reviewer never saw.

**No longer the same bytes.** This copy was taken while the committed
artifact was still the four-batch union, and the final test below asserted that
the two files *were* the same bytes — the assertion this module said would fail
first the moment a fifth batch was accepted. The Owner's acceptance of
``areas-of-effect-1`` is that moment, so it has been replaced — as its
predecessor in ``test_attitudes_1_frozen_prior`` was — by the stronger claim
that the live artifact extends this prior by exactly one batch. Deleting it
instead would have left the copy unattached to the thing it was copied from.

**No longer the same schema.** When this module was written the prior declared
schema 8 and schema 8 was current, so no registered crossing separated them and
none was asserted. The discovery checkpoint answered the open question the other
way: the Area of Effect class prints twenty-four substantive clauses schema 8
cannot state, so this build mints schema 9 and exactly one registered crossing
now separates the prior from it. That is the visible edit this module promised
to make rather than drift into.

**What this module does not do.** It proves nothing about the live artifact
beyond the final extension assertion. Every pin below describes the *frozen*
file: the four batches it holds, the 39 records, and the two reference targets
it cannot resolve — the honest starting position ``areas-of-effect-1`` was
measured from, not a list to be worked through. The committed artifact's own
pins live in ``test_committed_accepted_authority``.
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
    SCHEMA_8_VERSION,
    UnknownSchemaLiftError,
    lift_accepted_inputs,
    lift_path,
)
from tests.ingestion.mechanical._schema_pins import crossings_from

DATA = pathlib.Path(__file__).resolve().parent / "data"
FROZEN_PRIOR = DATA / "accepted_prior_conditions_1_hazards_1_actions_1_attitudes_1.json"
COMMITTED = COMMITTED_ORACLE_DIR / "srd-5-2-1-corpus-36b786d8-fa2.json"

#: Two independent identities of the frozen copy, so an edit cannot pass as a
#: reformat. LF-normalized, which is what ``.gitattributes`` declares.
FROZEN_CONTENT_SHA256 = "fd390d95dde74498142035d9dde00ccf7effadb372fc13f9662154841bb787ab"  # noqa: E501  # pragma: allowlist secret
FROZEN_BLOB = "2346404005618b0389b4e4f66d2e96c5c35b200f"  # pragma: allowlist secret

#: Derived from the semantic content the Owner accepted, and the figure
#: ``areas-of-effect-1``'s merge evidence names as the prior it was built
#: against.
ACCEPTED_ORACLE_IDENTITY = "c3b4d4b759441b05418fcbe1d90811e0d7c2535319aa005e64201ce29b5c74fa"  # noqa: E501  # pragma: allowlist secret

BATCH_IDS = ["actions-1", "attitudes-1", "conditions-1", "hazards-1"]

#: What the four accepted batches hold together, so a collection that silently
#: gained or lost an element fails by name rather than by total.
MERGED = {
    "records": 39,
    "components": 109,
    "prose_bindings": 49,
    "relationships": 0,
    "references": 46,
    "provenance": 504,
}
SPANS = 487
OBLIGATIONS = 39

#: Reference targets accepted authority cites and does not define, and the two
#: standing publication blockers as of this freeze. Pinned as a set, not a
#: count: this is the exact residue ``areas-of-effect-1``'s merge evidence was
#: measured against, and a batch that resolved a different target than it said
#: it would must fail here. ``areas-of-effect-1`` resolved neither and added
#: ``glossary.cover``; the post-merge residue is pinned in
#: ``test_committed_accepted_authority``, not here, because this file describes
#: the prior rather than the union.
UNRESOLVED_TARGETS = {
    "glossary.concentration",
    "glossary.speed",
}


def _lf_digest(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _blob_id(path: pathlib.Path) -> str:
    body = path.read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha1(b"blob %d\0" % len(body) + body).hexdigest()  # noqa: S324


def test_the_frozen_prior_is_the_four_batch_authority_it_claims_to_be() -> None:
    assert _lf_digest(FROZEN_PRIOR) == FROZEN_CONTENT_SHA256
    assert _blob_id(FROZEN_PRIOR) == FROZEN_BLOB

    inputs = load_accepted_inputs(FROZEN_PRIOR)
    assert oracle_identity(inputs.oracle) == ACCEPTED_ORACLE_IDENTITY
    assert inputs.oracle.schema_version == SCHEMA_8_VERSION
    assert inputs.oracle.schema_hash == SCHEMA_8_HASH
    assert sorted(b.batch_id for b in inputs.batches) == BATCH_IDS
    # One acceptance per span, not per batch: every accepted span names the
    # batch it was accepted in, and all four batches are represented.
    assert sorted({a.batch_id for a in inputs.acceptances}) == BATCH_IDS
    assert len(inputs.acceptances) == SPANS

    draft = inputs.oracle.representation
    assert {name: len(getattr(draft, name)) for name in MERGED} == MERGED
    assert len(inputs.oracle.spans) == SPANS
    assert len(inputs.oracle.obligations) == OBLIGATIONS


def test_each_batch_still_names_the_schema_it_was_reviewed_under() -> None:
    """Four batches, four different anchors, none restamped by the merge.

    Only ``attitudes-1`` was reviewed under schema 8. The artifact declaring
    schema 8 as a whole is what it was *lifted* to; what each batch was
    *accepted* under is the acceptance record, and ``areas-of-effect-1`` may not
    collapse the four into one.
    """
    anchors = {a.batch_id: a for a in load_accepted_inputs(FROZEN_PRIOR).schema_anchors}
    assert sorted(anchors) == BATCH_IDS
    assert anchors["conditions-1"].schema_hash == SCHEMA_3_HASH
    assert anchors["hazards-1"].schema_hash == SCHEMA_5_HASH
    assert anchors["actions-1"].schema_hash == SCHEMA_7_HASH
    assert anchors["attitudes-1"].schema_hash == SCHEMA_8_HASH


def test_the_prior_declares_schema_8_and_records_the_five_lifts_that_got_it_there() -> (
    None
):
    """What the file itself carries, which no successor schema restamps.

    Accepted bytes are never re-declared in place: the artifact says schema 8
    and records the five crossings that carried it there, and it will still say
    schema 8 after schema 9. A crossing to a *later* union is a property of the
    pair, not a field this file gains.
    """
    inputs = load_accepted_inputs(FROZEN_PRIOR)
    assert (inputs.oracle.schema_version, inputs.oracle.schema_hash) == (
        SCHEMA_8_VERSION,
        SCHEMA_8_HASH,
    )
    assert [lift.lift_id for lift in inputs.lifts] == [
        "5d-lift-schema-3-to-4",
        "5d-lift-schema-4-to-5",
        "5d-lift-schema-5-to-6",
        "5d-lift-schema-6-to-7",
        "5d-lift-schema-7-to-8",
    ]


def test_the_registered_crossings_separate_the_prior_from_this_build() -> None:
    """The position after the checkpoint, stated rather than assumed.

    This is the edit the previous form of this test said would be needed if
    ``areas-of-effect-1`` turned out to want a schema step. It does: schema 9
    admits seven families the prior's contract cannot state, so the prior is no
    longer current and reading it as current is a *finding* rather than a silent
    pass. It was exactly one registered step until ``cover-1`` minted schema 10,
    ``speed-1`` schema 11 and the practical-reliability amendment schema 12;
    the path is read from the registry rather than counted, so a succession
    lengthens the list here instead of breaking the claim.

    **Two identities, two scopes.** The frozen authority is untouched on disk and
    keeps the identity the Owner accepted. Its lifted copy is a *different*
    object with a *different* identity, because ``oracle_payload`` carries the
    representation binding and the lift re-declares exactly that. The content is
    what survives, and identically rather than equally: the lifted copy holds
    the same representation object, and the only top-level payload key that
    moves is ``representation_schema``. Reporting the lifted identity as the
    accepted one would claim the binding is not part of identity, which is the
    opposite of what this succession relies on.

    A self-lift stays unregistered, so a generator that reached for one here
    would raise rather than silently no-op.
    """
    inputs = load_accepted_inputs(FROZEN_PRIOR)
    current = (REPRESENTATION_SCHEMA_VERSION, representation_schema_hash())
    prior = (inputs.oracle.schema_version, inputs.oracle.schema_hash)
    assert prior == (SCHEMA_8_VERSION, SCHEMA_8_HASH)
    assert prior != current

    findings = validate_schema_binding(candidate_from_accepted_inputs(inputs))
    assert findings, "reading a superseded prior as current must be visible"
    assert any(REPRESENTATION_SCHEMA_VERSION in f for f in findings), findings

    expected = crossings_from(SCHEMA_8_VERSION)
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

    # Everything the prior carries besides the binding crosses untouched, and
    # by identity rather than equality -- the lift rebinds, it does not rebuild.
    # ``schema_anchors`` matters most: each batch's accepted-under hash is the
    # record that keeps schema 9 from restamping four batches as one, so a lift
    # that re-derived anchors would erase exactly the distinction the test above
    # exists to hold.
    for field in ("batches", "acceptances", "schema_anchors"):
        assert getattr(lifted, field) is getattr(inputs, field), field
    assert lifted.oracle.spans is inputs.oracle.spans
    assert lifted.oracle.obligations is inputs.oracle.obligations

    try:
        lift_path(current, current)
    except UnknownSchemaLiftError:
        pass
    else:  # pragma: no cover - would mean a self-lift got registered
        raise AssertionError("a self-lift is registered")


def test_the_unresolved_reference_targets_are_exactly_the_recorded_residue() -> None:
    """What accepted authority cites and cannot yet resolve.

    ``areas-of-effect-1`` recorded how many of these its merge closes: none, and
    it added one of its own. Pinning the set here is what makes that claim
    checkable, and these two were the standing publication blockers no accepted
    batch had defined when the freeze was taken.
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
    """The copy, attached to what it was copied from.

    Taking the freeze changed nothing about accepted authority, and until the
    Owner accepted ``areas-of-effect-1`` the live artifact and this copy were
    the same content. The previous form of this test named that acceptance as
    the thing that would end it and named what should replace it, so this is
    that replacement rather than a deletion: the live artifact is this prior
    plus exactly the batches accepted since, and every batch the freeze holds
    is still present and identical. ``cover-1`` and ``speed-1`` make
    that three, so the claim is generalized rather than re-pinned to a single
    batch name, following ``test_attitudes_1_frozen_prior``.
    """
    assert _lf_digest(FROZEN_PRIOR) == FROZEN_CONTENT_SHA256
    assert _lf_digest(COMMITTED) != FROZEN_CONTENT_SHA256

    frozen = {b.batch_id: b for b in load_accepted_inputs(FROZEN_PRIOR).batches}
    committed = {b.batch_id: b for b in load_accepted_inputs(COMMITTED).batches}
    assert set(committed) - set(frozen) == {
        "areas-of-effect-1",
        "cover-1",
        "speed-1",
    }
    assert {k: committed[k] for k in frozen} == frozen
