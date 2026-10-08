"""A machine proposal is not authority — CRD Issue 5d, #137 contract 2.

"Silence is not acceptance" is only enforceable if an unaccepted proposal
physically cannot be loaded as accepted authority. Convention cannot carry that:
a folder is a mistake away from being wrong, and a single ``accepted: false``
field is one edit away from a lie.

So the boundary is structural, and these tests attack it the way a mistake
would — by renaming the file, by moving it into the committed directory, and by
editing the discriminator to say what the loader wants to hear.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from afterworlds.ingestion.mechanical.acceptance import accept_proposal
from afterworlds.ingestion.mechanical.bound_corpus import BoundCorpusSnapshot
from afterworlds.ingestion.mechanical.models import (
    ReviewState,
    SemanticDisposition,
)
from afterworlds.ingestion.mechanical.oracle import (
    ACCEPTED_ARTIFACT_KIND,
    OracleLoadError,
    _resolve_committed_inputs,
    accepted_inputs_payload,
    load_accepted_inputs,
    load_oracle,
)
from afterworlds.ingestion.mechanical.policy import (
    SEMANTIC_POLICY_VERSION,
    semantic_policy_hash,
)
from afterworlds.ingestion.mechanical.proposal import (
    PROPOSAL_ARTIFACT_KIND,
    MechanicalProposal,
    ProposalLoadError,
    ProposedSpan,
    load_proposal,
    locate_span,
    proposal_identity,
    proposal_payload,
    seed_proposal,
)
from tests.ingestion.mechanical.conftest import (
    PACKAGE_UUID,
    RELEASE_BINDING,
    RELEASE_VERSION,
    SCHEMA_HASH,
    SCHEMA_VERSION,
    build_ledger,
    build_representation,
)


def _proposal() -> MechanicalProposal:
    """A proposal whose *content* is exactly the bounded accepted authority.

    Deliberately identical in substance to the accepted fixture: if the boundary
    depended on the proposal being somehow deficient, this would slip through.
    It must be refused for its shape alone.
    """
    return MechanicalProposal(
        binding=RELEASE_BINDING,
        policy_version=SEMANTIC_POLICY_VERSION,
        policy_hash=semantic_policy_hash(),
        schema_version=SCHEMA_VERSION,
        schema_hash=SCHEMA_HASH,
        proposed_spans=tuple(
            ProposedSpan(
                span=span,
                origin="tool:span-classifier@0",
                rationale="lexical mechanical signal in the leaf's canonical text",
            )
            for span in build_ledger().spans
        ),
        proposed_representation=build_representation(),
        proposal_origin="tool:mechanical-proposer@0",
    )


def _written(tmp_path: Path, payload: dict[str, object], name: str) -> Path:
    path = tmp_path / name
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


# -- the shapes are not interchangeable --------------------------------------


def test_a_proposal_declares_its_own_artifact_kind() -> None:
    payload = proposal_payload(_proposal())
    assert payload["artifact_kind"] == PROPOSAL_ARTIFACT_KIND
    assert payload["artifact_kind"] != ACCEPTED_ARTIFACT_KIND


def test_a_proposal_carries_no_acceptance_or_obligations() -> None:
    """Not empty ones — none at all.

    An empty ``acceptance`` block would be the proposal claiming a shape it has
    not earned, and an empty ``obligations`` list would let it satisfy the
    accepted loader's key set.
    """
    payload = proposal_payload(_proposal())
    assert "acceptance" not in payload
    assert "obligations" not in payload
    assert "spans" not in payload
    assert "representation" not in payload


def test_every_proposed_span_carries_a_reviewable_rationale() -> None:
    """The reviewer is accepting claims, and a claim needs a stated basis."""
    payload = proposal_payload(_proposal())
    spans = payload["proposed_spans"]
    assert isinstance(spans, list) and spans
    for span in spans:
        assert span["rationale"]
        assert span["proposal_origin"]


# -- and the accepted loader refuses every route in ---------------------------


def test_a_proposal_file_does_not_load_as_accepted_authority(tmp_path: Path) -> None:
    path = _written(tmp_path, proposal_payload(_proposal()), "proposal.json")
    with pytest.raises(OracleLoadError, match="not accepted authority"):
        load_accepted_inputs(path)


def test_renaming_a_proposal_does_not_make_it_accepted(tmp_path: Path) -> None:
    path = _written(
        tmp_path,
        proposal_payload(_proposal()),
        f"{PACKAGE_UUID}_{RELEASE_VERSION}.json",
    )
    with pytest.raises(OracleLoadError):
        load_oracle(path)


def test_forging_the_discriminator_still_fails_on_shape(tmp_path: Path) -> None:
    """The ``artifact_kind`` check is legibility, not the protection.

    With it edited to lie, the file is still missing every key accepted
    authority requires and still carrying four the accepted loader does not
    declare. There is no edit short of rewriting it into the accepted shape —
    which is what acceptance *is*.
    """
    payload = proposal_payload(_proposal())
    payload["artifact_kind"] = ACCEPTED_ARTIFACT_KIND
    path = _written(tmp_path, payload, "forged.json")
    with pytest.raises(OracleLoadError) as exc:
        load_accepted_inputs(path)
    message = str(exc.value)
    assert "missing" in message
    for required in ("spans", "acceptance", "representation", "obligations"):
        assert required in message


def test_a_proposal_in_the_committed_directory_is_refused(tmp_path: Path) -> None:
    """Directory placement never confers authority.

    A proposal dropped into the committed directory makes resolution *fail*
    rather than silently supplying unaccepted authority to the gate.
    """
    _written(tmp_path, proposal_payload(_proposal()), "dropped-in.json")
    with pytest.raises(OracleLoadError):
        _resolve_committed_inputs(PACKAGE_UUID, RELEASE_VERSION, tmp_path)


def test_an_accepted_artifact_still_loads_from_the_same_directory(
    tmp_path: Path,
) -> None:
    """The negative controls above are not just "nothing loads here"."""
    proposal = _proposal()
    inputs = accept_proposal(
        proposal,
        batch_id="batch-1",
        rule="every span of the bounded fixture, reviewed together",
        resolved_scope=tuple(p.span.span_id for p in proposal.proposed_spans),
        reviewer="owner",
        accepted_at="2026-08-09T00:00:00Z",
    )
    _written(tmp_path, accepted_inputs_payload(inputs), "accepted.json")
    resolved = _resolve_committed_inputs(PACKAGE_UUID, RELEASE_VERSION, tmp_path)
    assert resolved is not None
    assert resolved.oracle.binding == RELEASE_BINDING


# -- and the proposal loader refuses the route out ----------------------------
#
# The same boundary read the other way. ``load_proposal`` exists so a retained
# proposal can be reconstructed and its recorded identity re-derived; it must not
# become a way to read accepted authority back into an unaccepted shape.


def test_an_accepted_artifact_does_not_load_as_a_proposal(tmp_path: Path) -> None:
    proposal = _proposal()
    inputs = accept_proposal(
        proposal,
        batch_id="batch-1",
        rule="every span of the bounded fixture, reviewed together",
        resolved_scope=tuple(p.span.span_id for p in proposal.proposed_spans),
        reviewer="owner",
        accepted_at="2026-08-09T00:00:00Z",
    )
    path = _written(tmp_path, accepted_inputs_payload(inputs), "accepted.json")
    with pytest.raises(ProposalLoadError, match="not a machine proposal"):
        load_proposal(path)


def test_forging_an_accepted_artifact_into_a_proposal_fails_on_shape(
    tmp_path: Path,
) -> None:
    """Symmetric to ``test_forging_the_discriminator_still_fails_on_shape``.

    An accepted artifact with its discriminator edited to claim it is a proposal
    still declares no ``proposal_schema_version`` — it was never authored under
    one — so it is refused before anything tries to read spans out of it.
    """
    proposal = _proposal()
    payload = accepted_inputs_payload(
        accept_proposal(
            proposal,
            batch_id="batch-1",
            rule="every span of the bounded fixture, reviewed together",
            resolved_scope=tuple(p.span.span_id for p in proposal.proposed_spans),
            reviewer="owner",
            accepted_at="2026-08-09T00:00:00Z",
        )
    )
    payload["artifact_kind"] = PROPOSAL_ARTIFACT_KIND
    path = _written(tmp_path, payload, "forged-proposal.json")
    with pytest.raises(ProposalLoadError, match="proposal_schema_version"):
        load_proposal(path)


# -- proposals leave no trace in accepted authority ---------------------------


def test_proposal_identity_is_content_derived_and_not_a_projection_identity() -> None:
    first, second = proposal_identity(_proposal()), proposal_identity(_proposal())
    assert first == second

    noisier = MechanicalProposal(
        binding=_proposal().binding,
        policy_version=_proposal().policy_version,
        policy_hash=_proposal().policy_hash,
        schema_version=_proposal().schema_version,
        schema_hash=_proposal().schema_hash,
        proposed_spans=tuple(
            ProposedSpan(p.span, p.origin, "a different stated reason")
            for p in _proposal().proposed_spans
        ),
        proposed_representation=_proposal().proposed_representation,
        proposal_origin=_proposal().proposal_origin,
    )
    # The rationale is part of what a reviewer reads, so it identifies the
    # proposal — and none of it reaches any accepted artifact.
    assert proposal_identity(noisier) != first


# ---------------------------------------------------------------------------
# Seeding a proposal from bound source
# ---------------------------------------------------------------------------


def _snapshot(**leaf_lengths: int) -> BoundCorpusSnapshot:
    return BoundCorpusSnapshot(
        package_uuid=RELEASE_BINDING.package_uuid,
        release_version=RELEASE_BINDING.release_version,
        leaf_lengths=dict(leaf_lengths),
        chunk_coverage=(),
    )


def test_a_seed_is_inventory_not_interpretation() -> None:
    """Whole-leaf spans, UNRESOLVED, no representation and no review units.

    A seed states which source a proposal is about. Every judgement it could
    make instead -- a disposition, a structured record, a coherent unit and what
    it must contain -- is a human's reading, and code guessing one would put
    unauthored content inside the identity an acceptance records.
    """
    proposal = seed_proposal(
        _snapshot(alpha=10, beta=4),
        ("beta", "alpha"),
        binding=RELEASE_BINDING,
        origin="test-seed",
        rationale="seeded by a test",
    )
    assert [p.span.leaf_id for p in proposal.proposed_spans] == ["alpha", "beta"]
    assert [(p.span.char_start, p.span.char_end) for p in proposal.proposed_spans] == [
        (0, 10),
        (0, 4),
    ]
    assert {p.span.disposition for p in proposal.proposed_spans} == {
        SemanticDisposition.UNRESOLVED
    }
    assert {p.span.review_state for p in proposal.proposed_spans} == {
        ReviewState.PROPOSED
    }
    assert proposal.proposed_review_units == ()
    assert proposal.proposed_representation.records == ()


def test_a_repeated_leaf_seeds_one_span() -> None:
    """Two spans over one leaf would be an overlapping partition.

    Deduplicated at the seed, where the message can say so, rather than at
    acceptance, where it would surface as a repeated span id.
    """
    proposal = seed_proposal(
        _snapshot(alpha=10),
        ("alpha", "alpha"),
        binding=RELEASE_BINDING,
        origin="test-seed",
        rationale="seeded by a test",
    )
    assert len(proposal.proposed_spans) == 1


def test_a_seed_needs_source_to_be_about() -> None:
    """An empty seed is a caller mistake, not an empty proposal."""
    with pytest.raises(ValueError, match="at least one leaf"):
        seed_proposal(
            _snapshot(alpha=10),
            (),
            binding=RELEASE_BINDING,
            origin="test-seed",
            rationale="seeded by a test",
        )


def test_a_clause_is_located_by_its_unique_printed_text() -> None:
    leaves = {"leaf-a": "You can't see. You fall.", "leaf-b": "<td>Prone</td> Prone"}
    span = locate_span(leaves, "You fall.", SemanticDisposition.SUBSTANTIVE)
    assert (span.leaf_id, span.char_start, span.char_end) == ("leaf-a", 15, 24)
    assert span.review_state is ReviewState.PROPOSED
    # An anchored cell name is located inside its anchor, not in running prose.
    cell = locate_span(
        leaves,
        "Prone",
        SemanticDisposition.SUPPORTING_AUTHORITY,
        anchor="<td>Prone</td>",
    )
    assert (cell.leaf_id, cell.char_start, cell.char_end) == ("leaf-b", 4, 9)


@pytest.mark.parametrize(
    ("text", "anchor", "message"),
    [
        ("You fly.", None, "occurs 0 times"),
        ("Prone", None, "occurs 2 times"),
        ("Prone", "<td>Grappled</td>", "does not contain"),
    ],
)
def test_a_clause_that_is_absent_or_ambiguous_is_refused(
    text: str, anchor: str | None, message: str
) -> None:
    leaves = {"leaf-a": "You can't see. You fall.", "leaf-b": "<td>Prone</td> Prone"}
    with pytest.raises(ValueError, match=message):
        locate_span(leaves, text, SemanticDisposition.SUBSTANTIVE, anchor=anchor)
