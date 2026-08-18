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
    ProposedSpan,
    proposal_identity,
    proposal_payload,
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
    from afterworlds.ingestion.mechanical.acceptance import accept_proposal

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
