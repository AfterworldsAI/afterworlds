"""Extending accepted authority across a schema succession — CRD Issue 5d.

``accept_proposal`` refuses a proposal whose representation schema differs from
the prior accepted artifact's, and that refusal is correct: a proposal built
under a union that means something else is not extending the reviewed authority,
it is replacing it.

The committed ``conditions-1`` artifact declares schema 3. A later content batch
needs schema 4. This module is the seam where those two meet, and what it has to
prove is that the meeting costs the earlier reviewer nothing:

* the prior batch, its exact ``proposal_identity``, its reviewer, timestamp,
  rule, scope and diff all survive untouched;
* every inherited element is proved byte-identical **before** anything is
  re-declared; and
* an unknown, reversed, skipped, or hash-mismatched transition is refused, since
  "a later version" is never evidence that it can carry earlier content.

The prior artifact used here is the **real committed one**, not a fixture. A
synthetic prior could be built to suit the test; the file a reviewer actually
accepted cannot.
"""

from __future__ import annotations

import pathlib
from dataclasses import replace

import pytest

from afterworlds.ingestion.mechanical.acceptance import AcceptanceError, accept_proposal
from afterworlds.ingestion.mechanical.accounting import derive_span_id
from afterworlds.ingestion.mechanical.models import (
    ComponentHandling,
    ReviewState,
    SemanticDisposition,
    SemanticSpan,
)
from afterworlds.ingestion.mechanical.oracle import (
    load_accepted_inputs,
)
from afterworlds.ingestion.mechanical.proposal import MechanicalProposal, ProposedSpan
from afterworlds.ingestion.mechanical.representation import (
    REPRESENTATION_COLLECTIONS,
    REPRESENTATION_SCHEMA_VERSION,
    ComponentDraft,
    ConditionKind,
    ConditionLevelFact,
    LevelDirection,
    ProvenanceClaim,
    ProvenanceRole,
    ProvenanceTargetKind,
    RecordDraft,
    RecordKind,
    RepresentationDraft,
    fact_target_key,
    representation_schema_hash,
)
from afterworlds.ingestion.mechanical.schema_lift import (
    SCHEMA_3_HASH,
    SCHEMA_3_VERSION,
    SCHEMA_4_HASH,
    SCHEMA_4_VERSION,
    BatchSchemaAnchor,
    lift_chain_violations,
)

#: The **legacy specimen**: the committed accepted artifact exactly as it stood
#: before hazards-1 was accepted into it — one batch, reviewed under schema 3,
#: with no schema anchors and no lift evidence. That is the shape this module's
#: scenarios are about, and the Owner's acceptance of hazards-1 legitimately
#: ended it in production, so the specimen is frozen under ``data/`` rather than
#: read out of the oracle directory. Byte-identical to the file this repository
#: committed (Git blob ``42faeca2…``), so every identity pinned below is
#: unchanged.
#:
#: Deliberately **not** in :data:`COMMITTED_ORACLE_DIR`: a second file there
#: claiming one release is exactly what the resolver refuses, and
#: ``test_exactly_one_accepted_artifact_is_committed_for_the_release`` asserts
#: it stays the only one.
LEGACY_PATH = (
    pathlib.Path(__file__).resolve().parent
    / "data"
    / "legacy_conditions_1_unanchored_schema3.json"
)
PRIOR_PROPOSAL_IDENTITY = "14587d5b5d51ad282f3d16510e015cd7116adcbd3877964bf034eef96780b0eb"  # noqa: E501  # pragma: allowlist secret
PRIOR_SPANS = 185

#: A leaf the accepted artifact does not touch, so the new scope is disjoint.
NEW_LEAF = "leaf-succession-probe"
NEW_SPAN_ID = derive_span_id(NEW_LEAF, 0, 28)
NEW_RECORD = "hazard.succession-probe"
NEW_COMPONENT = "accrual"
GAIN = ConditionLevelFact(
    condition=ConditionKind.EXHAUSTION, direction=LevelDirection.GAIN, amount=1
)


def _prior():
    return load_accepted_inputs(LEGACY_PATH)


def _schema_4_proposal(prior, *, version: str, schema_hash: str) -> MechanicalProposal:
    """A minimal well-formed proposal over a span the prior artifact never saw."""
    span = SemanticSpan(
        span_id=NEW_SPAN_ID,
        leaf_id=NEW_LEAF,
        char_start=0,
        char_end=28,
        disposition=SemanticDisposition.SUBSTANTIVE,
        review_state=ReviewState.PROPOSED,
    )
    component = ComponentDraft(
        record_key=NEW_RECORD,
        semantic_key=NEW_COMPONENT,
        handling=ComponentHandling.STRUCTURED,
        facts=(GAIN,),
    )
    representation = RepresentationDraft(
        records=(RecordDraft(semantic_key=NEW_RECORD, kind=RecordKind.GLOSSARY_RULE),),
        components=(component,),
        prose_bindings=(),
        relationships=(),
        references=(),
        provenance=(
            ProvenanceClaim(
                ProvenanceTargetKind.FACT,
                fact_target_key(NEW_RECORD, NEW_COMPONENT, GAIN),
                NEW_SPAN_ID,
                ProvenanceRole.PRIMARY,
            ),
        ),
    )
    return MechanicalProposal(
        binding=prior.oracle.binding,
        policy_version=prior.oracle.policy_version,
        policy_hash=prior.oracle.policy_hash,
        schema_version=version,
        schema_hash=schema_hash,
        proposed_spans=(
            ProposedSpan(span=span, origin="succession-probe", rationale="probe"),
        ),
        proposed_representation=representation,
        proposal_origin="test_accept_across_schema_succession",
    )


def _accept(prior, proposal):
    return accept_proposal(
        proposal,
        batch_id="succession-probe-1",
        rule="the probe span",
        resolved_scope=(NEW_SPAN_ID,),
        reviewer="Test",
        accepted_at="2026-08-24T00:00:00Z",
        prior=prior,
    )


# ---------------------------------------------------------------------------
# The authorized succession
# ---------------------------------------------------------------------------


def test_a_schema_4_proposal_extends_schema_3_accepted_authority() -> None:
    """The seam this whole mechanism exists for, on real accepted content.

    Schema 5 made the crossing a *path*: the content was reviewed under schema 3
    and the build now implements schema 5, so it crosses two registered
    successions rather than one. The seam is unchanged — what it proves is that
    the destination this build declares is reached only through rows the registry
    holds.

    The prior here is the **frozen historical fixture**, not the live committed
    artifact. It was the live artifact until the Owner accepted ``hazards-1``
    into the same file; the fixture is that state byte for byte, and it is what
    a schema-3-to-later crossing has to be demonstrated against now that the
    committed artifact declares schema 5 and needs no crossing at all.
    """
    prior = _prior()
    assert prior.oracle.schema_version == SCHEMA_3_VERSION
    assert prior.lifts == ()

    result = _accept(
        prior,
        _schema_4_proposal(
            prior,
            version=REPRESENTATION_SCHEMA_VERSION,
            schema_hash=representation_schema_hash(),
        ),
    )

    # The merged artifact declares the destination contract.
    assert result.oracle.schema_version == REPRESENTATION_SCHEMA_VERSION
    assert result.oracle.schema_hash == representation_schema_hash()
    # Both batches, and the union of both scopes.
    assert [b.batch_id for b in result.batches] == [
        "conditions-1",
        "succession-probe-1",
    ]
    assert len(result.oracle.spans) == PRIOR_SPANS + 1


def test_the_prior_batch_and_its_proposal_identity_are_untouched() -> None:
    """A succession is not a review, so it may not edit what a human reviewed."""
    prior = _prior()
    result = _accept(
        prior,
        _schema_4_proposal(
            prior,
            version=REPRESENTATION_SCHEMA_VERSION,
            schema_hash=representation_schema_hash(),
        ),
    )
    assert result.batches[0] == prior.batches[0]
    assert result.batches[0].proposal_identity == PRIOR_PROPOSAL_IDENTITY
    # Every acceptance record the earlier reviewer produced, unchanged.
    assert result.acceptances[:PRIOR_SPANS] == prior.acceptances


def test_the_lift_is_recorded_as_evidence_with_its_verified_extent() -> None:
    """ "It verified" is not evidence; what it verified is.

    The record carries the exact source and destination pair and the collections
    proved byte-identical, so an audit can see the proof's extent instead of
    taking the lift's word for it. Names only: see :class:`SchemaLiftRecord` for
    why the element counts a lift produces in process are not carried into
    evidence a loader would have no way to check.
    """
    prior = _prior()
    result = _accept(
        prior,
        _schema_4_proposal(
            prior,
            version=REPRESENTATION_SCHEMA_VERSION,
            schema_hash=representation_schema_hash(),
        ),
    )
    # Every crossing, oldest first, each with its own proved extent. A single
    # collapsed record would assert a transition the registry does not contain.
    first, last = result.lifts[0], result.lifts[-1]
    assert [x.lift_id for x in result.lifts] == [
        "5d-lift-schema-3-to-4",
        "5d-lift-schema-4-to-5",
    ]
    assert (first.from_version, first.from_hash) == (SCHEMA_3_VERSION, SCHEMA_3_HASH)
    assert (last.to_version, last.to_hash) == (
        REPRESENTATION_SCHEMA_VERSION,
        representation_schema_hash(),
    )
    # Continuous: each record's destination is the next record's source.
    assert (first.to_version, first.to_hash) == (
        result.lifts[1].from_version,
        result.lifts[1].from_hash,
    )
    for lift in result.lifts:
        assert set(lift.verified_collections) == REPRESENTATION_COLLECTIONS
    # What the lift actually proved, asserted against the representation rather
    # than against a number the record repeats back to the reader.
    assert len(prior.oracle.representation.components) == 54
    assert len(prior.oracle.representation.records) == 16
    assert len(prior.oracle.representation.provenance) == 185


def test_growth_after_the_crossing_leaves_no_recoverable_pre_lift_extent() -> None:
    """Why the record states collections and not element counts (#137 round 3).

    The lift proves the *prior* artifact, and the very acceptance that carries it
    across then merges a new batch into the same collections. One committed file
    supersedes its predecessor and no record anchors the crossing to a point in
    the batch sequence, so the artifact that survives cannot tell an auditor how
    much was inherited. A count in the evidence would have been a number nothing
    could check — which is exactly how a fabricated one passed.
    """
    prior = _prior()
    result = _accept(
        prior,
        _schema_4_proposal(
            prior,
            version=REPRESENTATION_SCHEMA_VERSION,
            schema_hash=representation_schema_hash(),
        ),
    )
    # Same collections, strictly more in them than any lift ever saw.
    for lift in result.lifts:
        assert set(lift.verified_collections) == REPRESENTATION_COLLECTIONS
    for collection in ("records", "components", "provenance"):
        proved = len(getattr(prior.oracle.representation, collection))
        assert len(getattr(result.oracle.representation, collection)) > proved

    # The evidence still validates, because it claims only what remains true.
    assert (
        lift_chain_violations(
            result.lifts, (result.oracle.schema_version, result.oracle.schema_hash)
        )
        == []
    )


def test_an_identical_schema_still_needs_no_lift() -> None:
    """The direct path is unchanged: same contract, no succession recorded."""
    prior = _prior()
    same = _schema_4_proposal(
        prior, version=SCHEMA_3_VERSION, schema_hash=SCHEMA_3_HASH
    )
    result = _accept(prior, same)
    assert result.oracle.schema_version == SCHEMA_3_VERSION
    assert result.lifts == ()


# ---------------------------------------------------------------------------
# Everything that must be refused
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("version", "schema_hash", "why"),
    [
        ("5d-representation-schema-9", "9" * 64, "unregistered destination"),
        (SCHEMA_4_VERSION, "0" * 64, "destination hash mismatch"),
        (SCHEMA_3_VERSION, "3" * 64, "same version, different hash"),
    ],
)
def test_an_unauthorized_transition_is_refused(
    version: str, schema_hash: str, why: str
) -> None:
    """Only the exact registered pair is admitted; nothing is inferred from it.

    Refused by the recognition half of the binding invariant, which runs before
    the lift lookup: none of these pairs names a contract this build accepts
    authority under, so there is no transition to look up. The authorization
    half — two recognized pairs with no lift between them — is
    ``test_the_reverse_transition_is_refused``.
    """
    prior = _prior()
    with pytest.raises(AcceptanceError) as caught:
        _accept(
            prior, _schema_4_proposal(prior, version=version, schema_hash=schema_hash)
        )
    assert "is not a contract this build accepts authority under" in str(
        caught.value
    ), why


def test_the_reverse_transition_is_refused() -> None:
    """Schema 4 back to schema 3 is not a lift, and is not inferable from one.

    The registry is keyed by source; a lift from 3 to 4 says nothing whatever
    about 4 to 3, and a build that reasoned otherwise would treat every
    succession as reversible.
    """
    prior = _prior()
    # A schema-4 prior whose batches were *reviewed* under schema 4, not one
    # whose declaration was overwritten. Re-declaring alone would be the restamp
    # ``carried_anchors`` now refuses, and this test would then pass for the
    # wrong reason — it is about the registry having no 4-to-3 row (#137 round 8).
    # The schema-4 pair is named literally rather than read from the live build:
    # this build implements schema 5, so ``representation_schema_hash()`` would
    # pair schema 4's version with schema 5's hash and be refused for the
    # unrelated reason that it names no contract at all.
    lifted = replace(
        prior,
        oracle=replace(
            prior.oracle,
            schema_version=SCHEMA_4_VERSION,
            schema_hash=SCHEMA_4_HASH,
        ),
        schema_anchors=tuple(
            BatchSchemaAnchor(
                b.batch_id, b.proposal_identity, SCHEMA_4_VERSION, SCHEMA_4_HASH
            )
            for b in prior.batches
        ),
    )
    with pytest.raises(AcceptanceError) as caught:
        _accept(
            lifted,
            _schema_4_proposal(
                lifted, version=SCHEMA_3_VERSION, schema_hash=SCHEMA_3_HASH
            ),
        )
    assert "no verified lift authorizes the difference" in str(caught.value)


def test_a_restamped_prior_is_refused_rather_than_lifted() -> None:
    """Prior content carrying schema-4 meaning under a schema-3 declaration.

    That artifact's declaration and content disagree — it was not accepted under
    the schema it names — so it is refused as a restamp rather than reported as
    a payload difference or quietly normalized.
    """
    from afterworlds.ingestion.mechanical.representation import Skill

    prior = _prior()
    components = list(prior.oracle.representation.components)
    for index, component in enumerate(components):
        facts = list(component.facts)
        moved = False
        for position, fact in enumerate(facts):
            roll = getattr(fact, "roll", None)
            if roll is not None:
                facts[position] = replace(fact, roll=replace(roll, skill=Skill.STEALTH))
                moved = True
                break
        if moved:
            components[index] = replace(component, facts=tuple(facts))
            break
    tampered = replace(
        prior,
        oracle=replace(
            prior.oracle,
            representation=replace(
                prior.oracle.representation, components=tuple(components)
            ),
        ),
    )
    with pytest.raises(AcceptanceError) as caught:
        _accept(
            tampered,
            _schema_4_proposal(
                tampered,
                version=REPRESENTATION_SCHEMA_VERSION,
                schema_hash=representation_schema_hash(),
            ),
        )
    message = str(caught.value)
    assert "not admissible under it" in message
    assert "stealth" in message and SCHEMA_4_VERSION in message
