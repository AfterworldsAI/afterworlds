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


def test_only_the_release_predecessor_g1_c5_and_c7_are_superseded_by_digest() -> None:
    """The original artifact, its CRD Issue 2b G1 successor and the CRD Issue
    15c native C5 and C7 successors, each kept byte for byte; the CRD Issue
    15c C8 successor is the one claimant."""
    directory = oracle.COMMITTED_ORACLE_DIR
    prior = directory / "srd-5-2-1-corpus-8781d4e0-a3b.json"
    g1 = directory / "srd-5-2-1-corpus-8781d4e0-a3b-g1.json"
    c5 = directory / "srd-5-2-1-corpus-8781d4e0-a3b-15c.json"
    c7 = directory / "srd-5-2-1-corpus-8781d4e0-a3b-15c-c7.json"
    assert {
        _digest(prior),
        _digest(g1),
        _digest(c5),
        _digest(c7),
    } == oracle.SUPERSEDED_ORACLE_SHA256
    assert _digest(g1) == (
        "2ccbaeba6de75d9787fbdd407e42dc2425fa20d4d26bcc298b681b550bd11258"  # noqa: E501  # pragma: allowlist secret
    )
    assert _digest(c5) == (
        "23e5d8e0fac60e3f5417b3a41e40e6f475366dd385856f38c42104f4dd264f69"  # noqa: E501  # pragma: allowlist secret
    )
    assert _digest(c7) == (
        "2853f30a832ca581c9d4169b82d0c360f3d6a2d78f0ad8980de9997eef51f373"  # noqa: E501  # pragma: allowlist secret
    )
    assert _digest(directory / "srd-5-2-1-corpus-8781d4e0-a3b-15c-c8.json") == (
        "ead7fa9d4fde484098f71221ca5ef82dfb2c82229d8fca80ab5feeb4e4d62d0d"  # noqa: E501  # pragma: allowlist secret
    )


#: The eleven proposals the Owner accepted with the exact native C5 packet
#: (``.claude/review-notes/issue-15c-native/OWNER-ACCEPTANCE-PACKET.md``).
_ACCEPTED_15C_PROPOSALS = {
    "animals": "efa248a979c21d293701253cda86b561b876bec332667437769abebbb06221c9",  # noqa: E501  # pragma: allowlist secret
    "character-origins-feats": (
        "20716b7dcadd5e1216ff3594c5aa654cb41c2961fe49048b0c853c1eed381838"  # noqa: E501  # pragma: allowlist secret
    ),
    "checks-actions-rests": (
        "f459a65ded7f0f5eab59c6e57a357e8015efff973976aa17a89fb42c9422096d"  # noqa: E501  # pragma: allowlist secret
    ),
    "classes": "536c569f4226be24496edd8c1c1f27e59a6f873c7fcd53188aad9abc3a821e83",  # noqa: E501  # pragma: allowlist secret
    "combat-damage-breaking": (
        "75ce69ce7e2e5da48743dcb24c066540b90bdf9a116ba84e78959759be5cea7d"  # noqa: E501  # pragma: allowlist secret
    ),
    "core-play-completion": (
        "a9330308d5905b1ab6c296d34b149c2bf95332b91e5a7c75e94c6c50a33becb6"  # noqa: E501  # pragma: allowlist secret
    ),
    "equipment": "b01f54b917653f83b7dbeebd6ad54757bdf183f71235d76e9198815f21789c4b",  # noqa: E501  # pragma: allowlist secret
    "magic-items": "bc4979d74a841065af99502e0cf20d157ab4bedd1fd7a9724a2130ffa092e712",  # noqa: E501  # pragma: allowlist secret
    "monsters": "ff24d9daf6dd81a760778865a011a5da236b56514a32753c2a8034f5f3eec617",  # noqa: E501  # pragma: allowlist secret
    "spell-descriptions": (
        "dce22fbd6f89a61cbd7ab5efa0be75f81eec87840ae91731e8162c8fabfbbdc9"  # noqa: E501  # pragma: allowlist secret
    ),
    "spellcasting": "1033979c0b9308aed91f413826477c0318c054ae6af074b0a17b1fd3fe05363f",  # noqa: E501  # pragma: allowlist secret
}


#: The two proposals the Owner accepted with the exact consolidated C7
#: packet (``.claude/review-notes/issue-15c-c7-native/OWNER-PACKET.md``).
_ACCEPTED_C7_PROPOSALS = {
    "character-origins-feats": (
        "1e7b63d3800154eee539297b0ae5d4f9efbfe21c1776986db133e3cc046bfd28"  # noqa: E501  # pragma: allowlist secret
    ),
    "equipment": "b8c65454cae97f82cdb96c857aad84c70ba8c78e96fa24f1e95e89360e144a76",  # noqa: E501  # pragma: allowlist secret
}


#: The five proposals the Owner accepted with exact C8
#: (``.claude/review-notes/issue-15c-c8-native/owner-acceptance-2026-10-13.md``).
_ACCEPTED_C8_PROPOSALS = {
    "animals": "db3f0d2dd9c997f4f2edc1f8fd361244becf7720ab80834c7e2828d971e92014",  # noqa: E501  # pragma: allowlist secret
    "character-origins-feats": (
        "301572d46bc655125bc45ad8d08b53d044c0d28014c2ea0340bedd08d2a20f5f"  # noqa: E501  # pragma: allowlist secret
    ),
    "magic-items": "d88713097ad106b5e645b35cf1e0f1bffaa6408a8cd7af2faa4da68331f6996b",  # noqa: E501  # pragma: allowlist secret
    "monsters": "bec1bedc4097a7b42c6acbf64c6131688caa2c86cc85616006b2de1a85c886be",  # noqa: E501  # pragma: allowlist secret
    "spell-descriptions": (
        "1c01d1e4f603acebf8baa14b909b7b07406e0e3f0c27330a305363f923d527c7"  # noqa: E501  # pragma: allowlist secret
    ),
}


def test_the_committed_release_resolves_to_the_recorded_c8_successor() -> None:
    """The C8 successor: C5's eleven accepted proposals, two replaced by C7's
    and five (one of them C7's) by C8's, at the accepted oracle identity."""
    inputs = oracle.committed_inputs_for(
        "1299484e-c72d-509b-bd8d-d0169ee1f8d2", "5.2.1-corpus.8781d4e0-a3b"
    )
    assert inputs is not None
    identities = {b.batch_id: b.proposal_identity for b in inputs.batches}
    expected = {
        **_ACCEPTED_15C_PROPOSALS,
        **_ACCEPTED_C7_PROPOSALS,
        **_ACCEPTED_C8_PROPOSALS,
    }
    assert {k: identities[k] for k in expected} == expected
    assert oracle.oracle_identity(inputs.oracle) == (
        "70646cd987dcf75adc7b57b6271e38c6ca8cc9b508584dac89c5acefafa3e8d9"  # noqa: E501  # pragma: allowlist secret
    )
