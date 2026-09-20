"""Versioned semantic policy and its authorized succession — CRD Issue 5d.

The Owner Decision of 2026-09-16 (ADR-005d, #137 contract 2) adds one closed
catalog: prose retained because *no identified code-owned use* needs it
structured, as distinct from prose retained because judgement is required.
Adding a catalog changes the policy payload, so it changes the policy hash, so
it is a **version transition** — which is the whole reason this module exists.

What has to stay true across that transition, and is asserted here rather than
assumed anywhere else:

* the seven accepted batches were accepted under ``5d-semantic-policy-1`` and
  remain readable with their original meanings — policy 1's payload is
  reproduced key for key, and its recorded hash still verifies;
* both carried catalogs cross element for element, which is what makes
  ``5d-policy-1-to-2`` a strict superset rather than a redescription;
* an artifact crosses only through a registered transition, recorded as
  evidence that never touches identity; and
* the committed artifact is not rewritten by any of this. It is byte-identical
  after a policy-2 acceptance is built over it in memory.

The prior used for the crossing is the **real seven-batch accepted artifact**,
not a synthesized one: the file a reviewer actually accepted is the only prior
that can prove the crossing costs that reviewer nothing. It was the live file
until the Owner accepted the two Proficiency batches across this very
transition; it is now the frozen copy of that state, retained as a committed
fixture for exactly this purpose, and the live file's own side of the crossing -
that it declares policy 2 and records the one registered transition - is
asserted at the end of this module.
"""

from __future__ import annotations

import pathlib

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
    accepted_inputs_payload,
    load_accepted_inputs,
    oracle_identity,
)
from afterworlds.ingestion.mechanical.policy import (
    IRREDUCIBILITY_REASONS,
    NON_MECHANICAL_REASONS,
    POLICY_1_HASH,
    POLICY_1_VERSION,
    POLICY_2_HASH,
    POLICY_2_VERSION,
    PROSE_RETENTION_REASONS,
    SEMANTIC_POLICY_VERSION,
    UnknownPolicyTransitionError,
    accepted_policy_contracts,
    irreducibility_reason_for,
    policy_transition_for,
    prose_retention_reason_for,
    semantic_policy_hash,
    semantic_policy_payload,
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
from tests.ingestion.mechanical.test_committed_accepted_authority import ARTIFACT_PATH

#: The seven-batch accepted state, accepted under policy 1. The specimen for
#: every claim in this module about what policy-1 authority looks like and what a
#: crossing built over it may not touch.
POLICY_1_ARTIFACT = (
    pathlib.Path(__file__).resolve().parent
    / "data"
    / "accepted_prior_conditions_1_hazards_1_actions_1"
    "_attitudes_1_areas_of_effect_1_cover_1_speed_1.json"
)

#: A leaf the committed artifact does not touch, so the new scope is disjoint.
NEW_LEAF = "leaf-policy-crossing-probe"
NEW_SPAN_ID = derive_span_id(NEW_LEAF, 0, 31)
NEW_RECORD = "hazard.policy-crossing-probe"
NEW_COMPONENT = "accrual"
GAIN = ConditionLevelFact(
    condition=ConditionKind.EXHAUSTION, direction=LevelDirection.GAIN, amount=1
)


# ---------------------------------------------------------------------------
# The committed policies themselves
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("version", "pinned"),
    [(POLICY_1_VERSION, POLICY_1_HASH), (POLICY_2_VERSION, POLICY_2_HASH)],
)
def test_every_recognized_policy_still_hashes_to_its_pinned_contract(
    version: str, pinned: str
) -> None:
    """The registry's pins are facts about committed policies, not restatements.

    Without this, editing one description silently mints a third contract: the
    constant would still say ``da63b894…`` while ``semantic_policy_hash`` said
    something else, and every artifact declaring the pinned pair would stop
    loading with no test naming the cause.
    """
    assert semantic_policy_hash(version) == pinned


def test_policy_1_is_reproduced_with_exactly_the_keys_it_was_hashed_under() -> None:
    """The retention catalog is absent from policy 1, not emitted empty.

    An added key changes the hash. A superseded policy whose recorded hash no
    longer verifies is not superseded, it is lost — and the seven batches
    accepted under it become unreadable rather than historical.
    """
    assert set(semantic_policy_payload(POLICY_1_VERSION)) == {
        "semantic_policy_version",
        "normalization_version",
        "non_mechanical_reasons",
        "irreducibility_reasons",
    }
    assert "prose_retention_reasons" in semantic_policy_payload(POLICY_2_VERSION)


def test_both_carried_catalogs_cross_element_for_element() -> None:
    """What makes 1 → 2 a strict superset, asserted rather than asserted *of*.

    Every disposition and handling reason recorded under policy 1 has to mean
    exactly what it meant when it was accepted. That is a claim about these two
    lists being identical across the versions, so it is checked against the two
    payloads directly.
    """
    one = semantic_policy_payload(POLICY_1_VERSION)
    two = semantic_policy_payload(POLICY_2_VERSION)
    assert one["non_mechanical_reasons"] == two["non_mechanical_reasons"]
    assert one["irreducibility_reasons"] == two["irreducibility_reasons"]
    assert len(NON_MECHANICAL_REASONS) == 5
    assert len(IRREDUCIBILITY_REASONS) == 6


def test_the_two_prose_catalogs_are_disjoint() -> None:
    """A single recorded code says which of the two claims is being made.

    Never relabel reducible meaning with an irreducibility code (#137 contract
    2). If a code were in both catalogs, one component's recorded reason would
    no longer distinguish "cannot be reduced" from "nothing needs it reduced".
    """
    retention = {r.code for r in PROSE_RETENTION_REASONS}
    irreducible = {r.code for r in IRREDUCIBILITY_REASONS}
    assert retention == {"no_identified_structured_use"}
    assert not retention & irreducible
    for code in retention:
        assert irreducibility_reason_for(code) is None
    for code in irreducible:
        assert prose_retention_reason_for(code) is None


def test_the_build_applies_policy_2_and_accepts_both_contracts() -> None:
    assert SEMANTIC_POLICY_VERSION == POLICY_2_VERSION
    assert accepted_policy_contracts() == {
        (POLICY_1_VERSION, POLICY_1_HASH),
        (POLICY_2_VERSION, POLICY_2_HASH),
    }


# ---------------------------------------------------------------------------
# The registry is a table, not a comparison
# ---------------------------------------------------------------------------


def test_the_registered_transition_resolves_by_exact_pair() -> None:
    crossing = policy_transition_for(
        (POLICY_1_VERSION, POLICY_1_HASH), (POLICY_2_VERSION, POLICY_2_HASH)
    )
    assert crossing.transition_id == "5d-policy-1-to-2"


@pytest.mark.parametrize(
    ("source", "target"),
    [
        # Reversed: a newer policy's acceptances are not carried backwards.
        ((POLICY_2_VERSION, POLICY_2_HASH), (POLICY_1_VERSION, POLICY_1_HASH)),
        # A recognized version paired with the other one's hash names no policy.
        ((POLICY_1_VERSION, POLICY_2_HASH), (POLICY_2_VERSION, POLICY_2_HASH)),
        ((POLICY_1_VERSION, POLICY_1_HASH), (POLICY_2_VERSION, POLICY_1_HASH)),
        # An invented version, and an invented destination.
        (("5d-semantic-policy-0", POLICY_1_HASH), (POLICY_2_VERSION, POLICY_2_HASH)),
        ((POLICY_1_VERSION, POLICY_1_HASH), ("5d-semantic-policy-3", POLICY_2_HASH)),
    ],
)
def test_an_unregistered_succession_is_refused(
    source: tuple[str, str], target: tuple[str, str]
) -> None:
    """ "A later version" is never evidence that accepted authority may cross."""
    with pytest.raises(UnknownPolicyTransitionError):
        policy_transition_for(source, target)


def test_an_unrecognized_policy_payload_cannot_be_reproduced() -> None:
    with pytest.raises(ValueError, match="unrecognized semantic policy version"):
        semantic_policy_payload("5d-semantic-policy-0")


# ---------------------------------------------------------------------------
# Crossing the committed artifact
# ---------------------------------------------------------------------------


def _prior():
    return load_accepted_inputs(POLICY_1_ARTIFACT)


def _proposal(prior, *, version: str, policy_hash: str) -> MechanicalProposal:
    """A minimal well-formed proposal over a span the prior artifact never saw."""
    span = SemanticSpan(
        span_id=NEW_SPAN_ID,
        leaf_id=NEW_LEAF,
        char_start=0,
        char_end=31,
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
        policy_version=version,
        policy_hash=policy_hash,
        schema_version=REPRESENTATION_SCHEMA_VERSION,
        schema_hash=representation_schema_hash(),
        proposed_spans=(
            ProposedSpan(span=span, origin="policy-crossing-probe", rationale="probe"),
        ),
        proposed_representation=representation,
        proposal_origin="test_policy_versioning",
    )


def _accept(prior, proposal):
    return accept_proposal(
        proposal,
        batch_id="policy-crossing-probe-1",
        rule="the probe span",
        resolved_scope=(NEW_SPAN_ID,),
        reviewer="Test",
        accepted_at="2026-09-16T00:00:00Z",
        prior=prior,
    )


def test_the_seven_batch_artifact_was_accepted_under_policy_1() -> None:
    prior = _prior()
    assert prior.oracle.policy_version == POLICY_1_VERSION
    assert prior.oracle.policy_hash == POLICY_1_HASH
    assert prior.policy_transitions == ()
    assert len(prior.batches) == 7


def test_a_policy_2_proposal_extends_policy_1_accepted_authority() -> None:
    """The seam. Seven batches of reviewed meaning cross, and nothing is restated.

    Every retained batch keeps its own reviewer, timestamp, rule, scope, diff
    and ``proposal_identity``. The reason codes those batches recorded are
    still policy-1 codes, and they still mean what policy 1 said, which is
    exactly what the registered transition asserts and what
    ``test_both_carried_catalogs_cross_element_for_element`` proves.
    """
    prior = _prior()
    result = _accept(
        prior, _proposal(prior, version=POLICY_2_VERSION, policy_hash=POLICY_2_HASH)
    )

    assert result.oracle.policy_version == POLICY_2_VERSION
    assert result.oracle.policy_hash == POLICY_2_HASH
    assert [b.batch_id for b in result.batches] == [
        *(b.batch_id for b in prior.batches),
        "policy-crossing-probe-1",
    ]
    assert result.batches[: len(prior.batches)] == prior.batches
    assert result.acceptances[: len(prior.acceptances)] == prior.acceptances
    # Spans are canonically ordered, so the prior's survive as a subset rather
    # than as a prefix — unchanged element for element, including disposition
    # and every policy-1 reason code they carry.
    assert set(prior.oracle.spans) <= set(result.oracle.spans)
    assert len(result.oracle.spans) == len(prior.oracle.spans) + 1

    # The crossing is recorded once, oldest first, beside the schema lifts.
    assert [s.transition_id for s in result.policy_transitions] == ["5d-policy-1-to-2"]
    step = result.policy_transitions[0]
    assert (step.from_version, step.from_hash) == (POLICY_1_VERSION, POLICY_1_HASH)
    assert (step.to_version, step.to_hash) == (POLICY_2_VERSION, POLICY_2_HASH)


def test_the_policy_1_file_is_untouched_by_a_crossing_built_over_it() -> None:
    """Acceptance is a pure function over loaded bytes. Nothing is written back.

    The strongest available statement that this phase changed no accepted
    meaning: the policy-1 artifact's bytes, its payload, and its oracle identity
    are all what they were before the crossing was constructed. The real
    crossing, when the Owner authorized one, wrote a *new* nine-batch artifact
    and left this file exactly as it is.
    """
    before = POLICY_1_ARTIFACT.read_bytes()
    prior = _prior()
    identity_before = oracle_identity(prior.oracle)
    payload_before = accepted_inputs_payload(prior)

    _accept(
        prior, _proposal(prior, version=POLICY_2_VERSION, policy_hash=POLICY_2_HASH)
    )

    assert POLICY_1_ARTIFACT.read_bytes() == before
    reloaded = _prior()
    assert oracle_identity(reloaded.oracle) == identity_before
    assert accepted_inputs_payload(reloaded) == payload_before
    # Policy transitions are omitted when empty, exactly as lifts are, which is
    # why the committed file needs no reissue to be readable under policy 2.
    assert "policy_transitions" not in payload_before["acceptance"]


def test_a_same_policy_acceptance_records_no_crossing() -> None:
    """No transition is invented for a proposal that crosses nothing."""
    prior = _prior()
    result = _accept(
        prior, _proposal(prior, version=POLICY_1_VERSION, policy_hash=POLICY_1_HASH)
    )
    assert result.oracle.policy_version == POLICY_1_VERSION
    assert result.policy_transitions == ()


def test_an_unrecognized_policy_declaration_is_refused_before_anything_else() -> None:
    """A proposal under a policy this build cannot state the meaning of.

    Its reason codes cannot be checked against any closed catalog, so accepting
    it would mint authority under a policy that does not exist.
    """
    prior = _prior()
    with pytest.raises(AcceptanceError, match="not a contract this build accepts"):
        _accept(
            prior,
            _proposal(prior, version="5d-semantic-policy-0", policy_hash=POLICY_1_HASH),
        )


def test_a_recognized_version_with_the_wrong_hash_is_refused() -> None:
    """Both halves are matched together; a crossed pair names no policy at all."""
    prior = _prior()
    with pytest.raises(AcceptanceError, match="not a contract this build accepts"):
        _accept(
            prior,
            _proposal(prior, version=POLICY_2_VERSION, policy_hash=POLICY_1_HASH),
        )


def test_the_committed_artifact_crossed_once_and_records_it() -> None:
    """The live file's side of the seam, after a real Owner acceptance used it.

    Everything above builds the crossing in memory from the policy-1 artifact.
    This reads the artifact the Owner's acceptance of the two Proficiency batches
    actually wrote: it declares policy 2, it records ``5d-policy-1-to-2`` exactly
    once, and the two batches accepted across it are the only ones that could
    have carried it. A second transition record, or a policy-2 declaration with
    no transition behind it, is what this refuses.
    """
    committed = load_accepted_inputs(ARTIFACT_PATH)
    assert committed.oracle.policy_version == POLICY_2_VERSION
    assert committed.oracle.policy_hash == POLICY_2_HASH
    assert [s.transition_id for s in committed.policy_transitions] == [
        "5d-policy-1-to-2"
    ]
    step = committed.policy_transitions[0]
    assert (step.from_version, step.from_hash) == (POLICY_1_VERSION, POLICY_1_HASH)
    assert (step.to_version, step.to_hash) == (POLICY_2_VERSION, POLICY_2_HASH)

    prior = _prior()
    assert prior.oracle.policy_version == POLICY_1_VERSION
    assert prior.policy_transitions == ()
    assert {b.batch_id for b in committed.batches} - {
        b.batch_id for b in prior.batches
    } == {"proficiency-destinations-1", "proficiency-1"}
