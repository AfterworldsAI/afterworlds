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
    COMMITTED_ORACLE_DIR,
    load_accepted_inputs,
)
from afterworlds.ingestion.mechanical.proposal import MechanicalProposal, ProposedSpan
from afterworlds.ingestion.mechanical.representation import (
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
    SCHEMA_4_VERSION,
)

ARTIFACT_PATH = COMMITTED_ORACLE_DIR / "srd-5-2-1-corpus-36b786d8-fa2.json"
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
    return load_accepted_inputs(ARTIFACT_PATH)


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
    """The seam this whole mechanism exists for, on the real committed artifact."""
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
    assert result.oracle.schema_version == SCHEMA_4_VERSION
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

    The record carries the exact source and destination pair and the element
    counts proved byte-identical, so an audit can see the proof's extent instead
    of taking the lift's word for it.
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
    (lift,) = result.lifts
    assert lift.lift_id == "5d-lift-schema-3-to-4"
    assert (lift.from_version, lift.from_hash) == (SCHEMA_3_VERSION, SCHEMA_3_HASH)
    assert (lift.to_version, lift.to_hash) == (
        SCHEMA_4_VERSION,
        representation_schema_hash(),
    )
    counts = dict(lift.verified_counts)
    assert counts["components"] == 54
    assert counts["records"] == 16
    assert counts["provenance"] == 185


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
    """Only the exact registered pair is admitted; nothing is inferred from it."""
    prior = _prior()
    with pytest.raises(AcceptanceError) as caught:
        _accept(
            prior, _schema_4_proposal(prior, version=version, schema_hash=schema_hash)
        )
    assert "no verified lift authorizes the difference" in str(caught.value), why


def test_the_reverse_transition_is_refused() -> None:
    """Schema 4 back to schema 3 is not a lift, and is not inferable from one.

    The registry is keyed by source; a lift from 3 to 4 says nothing whatever
    about 4 to 3, and a build that reasoned otherwise would treat every
    succession as reversible.
    """
    prior = _prior()
    lifted = replace(
        prior,
        oracle=replace(
            prior.oracle,
            schema_version=SCHEMA_4_VERSION,
            schema_hash=representation_schema_hash(),
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
    assert "content only a later schema can state" in str(caught.value)
