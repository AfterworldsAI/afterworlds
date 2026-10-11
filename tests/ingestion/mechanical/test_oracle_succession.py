"""Same-release oracle succession by artifact digest (CRD Issue 2b G1).

A successor for the same 5c release cannot be selected by release version, so
resolution skips a committed file whose exact bytes a recorded successor
supersedes. Exercised through the directory-parameterized resolver.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from afterworlds.ingestion.mechanical import oracle
from afterworlds.ingestion.mechanical.acceptance import accept_proposal
from afterworlds.ingestion.mechanical.oracle import (
    OracleLoadError,
    _resolve_committed_inputs,
    accepted_inputs_payload,
)
from tests.ingestion.mechanical.conftest import PACKAGE_UUID, RELEASE_VERSION
from tests.ingestion.mechanical.test_proposal_boundary import _proposal


def _accepted(tmp_path: Path, name: str, reviewer: str) -> Path:
    proposal = _proposal()
    inputs = accept_proposal(
        proposal,
        batch_id="batch-1",
        rule="every span of the bounded fixture",
        resolved_scope=tuple(p.span.span_id for p in proposal.proposed_spans),
        reviewer=reviewer,
        accepted_at="2026-10-10T00:00:00Z",
    )
    path = tmp_path / name
    path.write_text(json.dumps(accepted_inputs_payload(inputs)), encoding="utf-8")
    return path


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_two_claimants_for_one_release_are_refused(tmp_path: Path) -> None:
    _accepted(tmp_path, "a.json", "prior")
    _accepted(tmp_path, "b.json", "successor")
    with pytest.raises(OracleLoadError, match="2 committed oracles"):
        _resolve_committed_inputs(PACKAGE_UUID, RELEASE_VERSION, tmp_path)


def test_a_superseded_digest_leaves_the_successor_as_the_one_claimant(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    prior = _accepted(tmp_path, "a.json", "prior")
    _accepted(tmp_path, "b.json", "successor")
    before = prior.read_bytes()
    monkeypatch.setattr(oracle, "SUPERSEDED_ORACLE_SHA256", frozenset({_digest(prior)}))
    resolved = _resolve_committed_inputs(PACKAGE_UUID, RELEASE_VERSION, tmp_path)
    assert resolved is not None
    assert {a.reviewer for a in resolved.acceptances} == {"successor"}
    assert prior.read_bytes() == before  # kept byte for byte, only skipped


def test_superseding_the_only_claimant_resolves_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    prior = _accepted(tmp_path, "a.json", "prior")
    monkeypatch.setattr(oracle, "SUPERSEDED_ORACLE_SHA256", frozenset({_digest(prior)}))
    assert _resolve_committed_inputs(PACKAGE_UUID, RELEASE_VERSION, tmp_path) is None


def test_only_the_g1_predecessor_is_superseded_by_digest() -> None:
    prior = oracle.COMMITTED_ORACLE_DIR / "srd-5-2-1-corpus-8781d4e0-a3b.json"
    assert oracle.SUPERSEDED_ORACLE_SHA256 == {_digest(prior)}


def test_the_committed_release_resolves_to_the_recorded_g1_successor() -> None:
    inputs = oracle.committed_inputs_for(
        "1299484e-c72d-509b-bd8d-d0169ee1f8d2", "5.2.1-corpus.8781d4e0-a3b"
    )
    assert inputs is not None
    (equipment,) = [b for b in inputs.batches if b.batch_id == "equipment"]
    assert equipment.proposal_identity == (
        "8a8a737b0d1e47410de86bbeca44b66522b46511e078727d20760678943b5345"
    )
    assert oracle.oracle_identity(inputs.oracle) == (
        "3e7b27dbb291eb11ca7489719442308397b091d745beb3e48a517bf38685c05a"
    )
