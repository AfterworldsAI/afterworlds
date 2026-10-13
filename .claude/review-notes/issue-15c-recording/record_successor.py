"""Record the Owner-accepted CRD Issue 15c native successor.

Run from the repository root with the clone's venv:

    PYTHONIOENCODING=utf-8 venv/Scripts/python.exe \
        .claude/review-notes/issue-15c-recording/record_successor.py

The construction is the reviewed one (``issue-15c-native/scripts/build_candidate``):
in G1's accepted-anchor order each of the eleven affected batches is excised
(claim-based) and its exact accepted proposal -- the rendered file the packet
pins -- is accepted natively in its place. Only the acceptance evidence differs
from the reviewed simulated preview: the real Owner as reviewer, the recording
time, and a rule quoting the Owner's statement and the pinned hashes. The
preview and packet are preserved unchanged; nothing simulated is carried.

Write-once, as G1's recording: if the successor does not exist it is recorded;
if it exists it is rebuilt from the evidence it carries and must match byte for
byte. Either way the proofs below run and ``recorded-followup.json`` is written:

* pins: G1, predecessor, C5, receipt, packet, review, preview, 11 proposals;
* every proposal identity and rendered hash appears in the accepted packet;
* oracle identity and projection (UUID and payload hash) equal the accepted;
* the recording differs from the preview only in ``reviewer``,
  ``accepted_at`` and ``rule``, and only on the eleven batches' rows;
* no SIMULATION residue; G1 and the predecessor bytes are untouched;
* native ``validate_candidate`` has no findings; persist -> reconstruct ->
  re-identify; the read-only publication gate passes against the recording,
  in a private copy of the isolated release store. Nothing is published.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

REPO = Path.cwd()
NOTES = REPO / ".claude/review-notes"
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(NOTES / "issue-15c-native/scripts"))

import common as c  # noqa: E402
from build_candidate import PREVIEW, chain  # noqa: E402

from afterworlds.ingestion.mechanical.bound_corpus import load_bound_corpus  # noqa: E402
from afterworlds.ingestion.mechanical.gate import run_publication_gate  # noqa: E402
from afterworlds.ingestion.mechanical.oracle import (  # noqa: E402
    COMMITTED_ORACLE_DIR,
    AcceptedInputs,
    candidate_from_accepted_inputs,
    load_accepted_inputs,
    oracle_identity,
    serialize_accepted_inputs,
)
from afterworlds.ingestion.mechanical.persistence import (  # noqa: E402
    persist_draft,
    reconstruct_candidate,
    record_persisted_state_digest,
    verify_reconstruction,
)
from afterworlds.ingestion.mechanical.projection import (  # noqa: E402
    identify_projection,
    projection_payload,
    validate_candidate,
)
from afterworlds.ingestion.mechanical.proposal import (  # noqa: E402
    MechanicalProposal,
    load_proposal,
    proposal_identity,
)
from afterworlds.persistence.database import (  # noqa: E402
    create_engine,
    create_session_factory,
)
from afterworlds.persistence.orm.base import Base  # noqa: E402

HERE = NOTES / "issue-15c-recording"
NATIVE = NOTES / "issue-15c-native"
RECEIPT = NATIVE / "owner-acceptance-2026-10-12.md"
RECEIPT_JSON = HERE / "owner-acceptance.json"
PACKET = NATIVE / "OWNER-ACCEPTANCE-PACKET.md"
REVIEW = NOTES / "issue-15c-implementation/codex-native-final-review.md"
PROPOSALS = NATIVE / "preview/proposals"
TARGET = COMMITTED_ORACLE_DIR / "srd-5-2-1-corpus-8781d4e0-a3b-15c.json"
FOLLOWUP = HERE / "recorded-followup.json"

OWNER = "Ravenlok (Owner)"
STATEMENT = (
    "I accept the exact native C5 packet so Claude can record the local successor "
    "and continue implementation."
)
PINS = {
    c.G1_PATH: c.G1_SHA256,
    c.PREDECESSOR_PATH: c.PREDECESSOR_SHA256,
    RECEIPT: "e2a5dd0edab09cdfbd7ecbbb9cca6132542a5d298b72a18ba7e5ec5cbf2478c7",
    PACKET: "525b4f9cb6645d1c83fe0b34b7cb2d080847970db37f47a200fb8219f8579e91",
    REVIEW: "462e25ddca73dac2f80191e67e44fed876c62fc032d203a89b2eb7e36cc5aac3",
    PREVIEW: "cd9d1d27428a1525955f83091125489e96bbc7bd0977bb9f3ce83933883a20d3",
    **{c.C5 / name: digest for name, digest in c.C5_SHA256.items()},
}
SCHEMA = ("5d-representation-schema-19",
          "3734ccf7d6be7f25e0a0d7c0395121c5525afcb87144f5cf9d6895e03c1cd18f")
ORACLE_IDENTITY = "000c4c108daf609c26eb9ae9f1197a26eef6fb80a3cb5c788f9e89ba20ad6e76"
PROJECTION = "44f212d5-32dd-5469-8f05-f0d236492347"
PAYLOAD_HASH = "ed8e21dc89ce519d6301e2bbf486405576069fe4348f0c8948bed4dbcb3e5188"
EVIDENCE = frozenset({"reviewer", "accepted_at", "rule"})


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def rule(at: str) -> str:
    return (
        f"Owner exact acceptance, {OWNER}: {STATEMENT!r} CRD Issue 15c native C5 "
        f"successor. Owner packet {PACKET.relative_to(REPO).as_posix()} sha256 "
        f"{PINS[PACKET]}; receipt {RECEIPT.relative_to(REPO).as_posix()} sha256 "
        f"{PINS[RECEIPT]}; independent review sha256 {PINS[REVIEW]}; reviewed "
        f"preview sha256 {PINS[PREVIEW]}; schema {SCHEMA[0]} {SCHEMA[1]}; oracle "
        f"identity {ORACLE_IDENTITY}; projection {PROJECTION}; recorded {at}"
    )


def accepted_proposals() -> dict[str, MechanicalProposal]:
    """The eleven exact accepted proposals, each pinned by the packet."""
    packet = PACKET.read_text("utf-8")
    out = {}
    for batch in c.AFFECTED:
        path = PROPOSALS / f"{batch}-PROPOSAL.json"
        digest = sha(path.read_bytes())
        p = load_proposal(path)
        ident = proposal_identity(p)
        assert digest in packet and ident in packet, (batch, digest, ident)
        assert (p.schema_version, p.schema_hash) == SCHEMA, batch
        out[batch] = p
    return out


def construct(at: str) -> tuple[AcceptedInputs, dict[str, str]]:
    base = load_accepted_inputs(c.G1_PATH)
    proposals = accepted_proposals()
    inputs, _ = chain(base, proposals, lambda _: {
        "rule": rule(at), "reviewer": OWNER, "accepted_at": at})
    return inputs, {b: proposal_identity(p) for b, p in proposals.items()}


def _blank(x: Any) -> Any:
    if isinstance(x, dict):
        return {k: ("<evidence>" if k in EVIDENCE else _blank(v)) for k, v in x.items()}
    if isinstance(x, list):
        return [_blank(v) for v in x]
    return x


def compare(preview: bytes, recorded: bytes) -> dict[str, Any]:
    """Recorded vs preview: only the three evidence fields, only on the eleven."""
    a, b = json.loads(preview), json.loads(recorded)
    outside = sorted(k for k in a.keys() | b.keys() if k != "acceptance" and a.get(k) != b.get(k))
    changed: dict[str, int] = {}
    foreign: list[str] = []
    for coll in ("batches", "records", "review_unit_records"):
        for x, y in zip(a["acceptance"][coll], b["acceptance"][coll], strict=True):
            for k in EVIDENCE & x.keys():
                if x[k] != y[k]:
                    changed[f"{coll}.{k}"] = changed.get(f"{coll}.{k}", 0) + 1
                    if x.get("batch_id") not in c.AFFECTED:
                        foreign.append(f"{coll}:{x.get('batch_id')}")
    return {
        "outside_acceptance_differences": outside,
        "acceptance_equal_after_blanking_evidence": _blank(a["acceptance"])
        == _blank(b["acceptance"]),
        "evidence_changed": changed,
        "evidence_changed_outside_affected": sorted(set(foreign)),
    }


def native_checks(inputs: AcceptedInputs) -> dict[str, Any]:
    with c.private_store() as db:
        engine = create_engine(f"sqlite:///{db}")
        try:
            Base.metadata.create_all(engine)
            with create_session_factory(engine)() as s:
                b = inputs.oracle.binding
                corpus = load_bound_corpus(s, b.package_uuid, b.release_version)
                findings = list(
                    validate_candidate(candidate_from_accepted_inputs(inputs), corpus)
                )
                identified = identify_projection(candidate_from_accepted_inputs(inputs))
                persist_draft(s, identified, now="2026-10-12T00:00:00Z")
                s.commit()
                reconstruction = verify_reconstruction(s, identified)
                rebuilt = reconstruct_candidate(s, identified.projection_uuid)
                record_persisted_state_digest(s, identified.projection_uuid)
                s.commit()
                gate = run_publication_gate(s, identified.projection_uuid, inputs.oracle)
                return {
                    "validate_candidate_findings": findings[:10],
                    "validate_candidate_finding_count": len(findings),
                    "verify_reconstruction": list(reconstruction),
                    "reconstructed_payload_identical": projection_payload(rebuilt)
                    == projection_payload(identified.candidate),
                    "reidentified_projection": str(
                        identify_projection(rebuilt).projection_uuid),
                    "projection": str(identified.projection_uuid),
                    "payload_hash": identified.payload_hash,
                    "gate_passed": gate.passed,
                    "gate_failures": [f.detail for f in gate.failures][:10],
                }
        finally:
            engine.dispose()


def roundtrip(data: bytes) -> bool:
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "roundtrip.json"
        p.write_bytes(data)
        return serialize_accepted_inputs(load_accepted_inputs(p)) == data


def main() -> None:
    for path, want in PINS.items():
        got = sha(path.read_bytes())
        print(f"pin {got == want} {path.relative_to(REPO).as_posix()}")
        assert got == want, path
    receipt = json.loads(RECEIPT_JSON.read_text("utf-8"))
    assert receipt["exact_user_message"] == STATEMENT and receipt["owner"] == OWNER
    assert receipt["receipt_sha256"] == PINS[RECEIPT]
    assert receipt["owner_packet_sha256"] == PINS[PACKET]
    assert receipt["independent_review_sha256"] == PINS[REVIEW]
    assert STATEMENT in RECEIPT.read_text("utf-8")

    if TARGET.exists():
        existing = load_accepted_inputs(TARGET)
        (at,) = {a.accepted_at for a in existing.acceptances if a.batch_id in c.AFFECTED}
        mode = "verify"
    else:
        at = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        assert at > receipt["receipt_recorded_at_utc"], at
        mode = "record"
    print("mode", mode, "recording time", at)

    inputs, identities = construct(at)
    data = serialize_accepted_inputs(inputs)
    assert b"SIMULATION" not in data, "simulated evidence in the recording"
    report = compare(PREVIEW.read_bytes(), data)
    print(json.dumps(report, indent=1))
    assert not report["outside_acceptance_differences"]
    assert report["acceptance_equal_after_blanking_evidence"]
    assert not report["evidence_changed_outside_affected"]
    assert oracle_identity(inputs.oracle) == ORACLE_IDENTITY, "oracle identity"
    assert (inputs.oracle.schema_version, inputs.oracle.schema_hash) == SCHEMA
    assert roundtrip(data)

    if mode == "record":
        with TARGET.open("xb") as f:
            f.write(data)
        print("wrote", TARGET.relative_to(REPO).as_posix())
    on_disk = TARGET.read_bytes()
    assert on_disk == data, "on-disk successor differs from the reconstruction"

    native = native_checks(load_accepted_inputs(TARGET))
    print(json.dumps(native, indent=1))
    assert native["validate_candidate_finding_count"] == 0
    assert native["verify_reconstruction"] == []
    assert native["reconstructed_payload_identical"]
    assert native["projection"] == native["reidentified_projection"] == PROJECTION
    assert native["payload_hash"] == PAYLOAD_HASH
    assert native["gate_passed"] and not native["gate_failures"]
    assert sha(c.G1_PATH.read_bytes()) == c.G1_SHA256, "G1 changed"
    assert sha(c.PREDECESSOR_PATH.read_bytes()) == c.PREDECESSOR_SHA256

    followup = {
        "mode": mode,
        "recorded_at": at,
        "successor": TARGET.relative_to(REPO).as_posix(),
        "successor_sha256": sha(on_disk),
        "successor_bytes": len(on_disk),
        "reviewed_preview_sha256": PINS[PREVIEW],
        "proposal_identities": identities,
        "schema": list(SCHEMA),
        "oracle_identity": ORACLE_IDENTITY,
        "projection": PROJECTION,
        "payload_hash": PAYLOAD_HASH,
        "g1_sha256_after": sha(c.G1_PATH.read_bytes()),
        "predecessor_sha256_after": sha(c.PREDECESSOR_PATH.read_bytes()),
        "comparison_with_reviewed_preview": report,
        "native": native,
    }
    FOLLOWUP.write_text(json.dumps(followup, indent=1) + "\n", encoding="utf-8")
    print("successor sha256", followup["successor_sha256"])


if __name__ == "__main__":
    main()
