"""Record the Owner-accepted CRD Issue 2b G1 successor natively.

Run from the repository root with the clone's venv:

    ./venv/Scripts/python .claude/review-notes/issue-2b-g1-recording/record_successor.py

The construction is the reviewed one (``issue-2b-g1-candidate/scripts``): the
accepted Equipment batch is excised from the prior accepted oracle and the
Owner-accepted G1 proposal is accepted natively in its place. Only the
acceptance evidence differs from the reviewed preview: the real Owner as
reviewer, the recording time, and a rule that quotes the Owner's statement and
the pinned hashes. Nothing synthetic is carried.

Write-once. If the successor does not exist it is recorded; if it exists it is
rebuilt from the evidence it carries and must match byte for byte. Either way
the proofs below run and ``recorded-followup.json`` is written:

* pins: prior oracle, receipt, packet, reviews, preview, rendered proposal;
* proposal identity, oracle identity and projection equal the reviewed ones;
* the recording differs from the preview only in ``reviewer``, ``accepted_at``
  and ``rule``, and only on the Equipment batch's rows;
* no SIMULATION residue; the prior oracle bytes are untouched;
* native ``validate_candidate`` has no findings; persist -> reconstruct ->
  re-identify; the read-only publication gate passes against the recording, in
  a private copy of the isolated release store. Nothing is published.
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
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / ".claude/review-notes/issue-2b-g1-candidate/scripts"))

from common import (  # noqa: E402
    BATCH,
    PRIOR_PATH,
    PRIOR_SHA256,
    STORE,
    build_proposal,
    class_eligibility_edited,
    g1_generator,
    generator,
)
from excise import excise  # noqa: E402

from afterworlds.ingestion.mechanical.acceptance import accept_proposal  # noqa: E402
from afterworlds.ingestion.mechanical.authoring import render  # noqa: E402
from afterworlds.ingestion.mechanical.bound_corpus import (  # noqa: E402
    load_bound_corpus,
)
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
from afterworlds.ingestion.mechanical.proposal import proposal_identity  # noqa: E402
from afterworlds.persistence.database import (  # noqa: E402
    create_engine,
    create_session_factory,
)
from afterworlds.persistence.orm.base import Base  # noqa: E402

NOTES = REPO / ".claude/review-notes"
HERE = NOTES / "issue-2b-g1-recording"
CANDIDATE_DIR = NOTES / "issue-2b-g1-candidate/candidate"
PREVIEW = CANDIDATE_DIR / "srd-5-2-1-corpus-8781d4e0-a3b-g1-candidate.json"
PROPOSAL_FILE = CANDIDATE_DIR / "issue-2b-g1-equipment-PROPOSAL.json"
RECEIPT = HERE / "owner-acceptance.md"
RECEIPT_JSON = HERE / "owner-acceptance.json"
TARGET = COMMITTED_ORACLE_DIR / "srd-5-2-1-corpus-8781d4e0-a3b-g1.json"
FOLLOWUP = HERE / "recorded-followup.json"

OWNER = "Ravenlok (Owner)"
STATEMENT = (
    "I accept the G1 semantic proposal in that packet. Continue CRD Issue 2b "
    "implementation and prepare its independently reviewed PR, preserving all "
    "existing checkout protections and stop boundaries."
)
PINS = {
    PRIOR_PATH: PRIOR_SHA256,
    RECEIPT: "14fe1da93856a2ae50debed46be84475a86c6573bda289a5405ecc4d3a9df780",
    PREVIEW: "bfd0d371fc7ee3cecee45bb607b5b709050347ddf9766b4a442783a966076082",
    PROPOSAL_FILE: "d1385de0f02af5f63bd218c1fb2f6acc58857e1e7e6bb3e04a4fa28815ab4508",
}
EXTERNAL_PINS = {
    "owner_packet_sha256": "9a3c94149823f20626da92c0b0060ca14d1cef16e47b076687a73b022bd1c4eb",
    "independent_review_sha256": (
        "9baa01c02a2e1c3189b997adf3f6d37280127dde5299e204ac11babedeba8ac2"
    ),
    "final_checkpoint_review_sha256": (
        "45e7db001a3a0c3b425bde573930215c69a6deef7216c441df4857df82ef5bd8"
    ),
    "recording_permission_authorization_sha256": (
        "3a9e3687d081a22ad4b095859564e9830e4fe6a3becb32726aaf9feb7c25e00c"
    ),
}
PROPOSAL_IDENTITY = "8a8a737b0d1e47410de86bbeca44b66522b46511e078727d20760678943b5345"
ORACLE_IDENTITY = "3e7b27dbb291eb11ca7489719442308397b091d745beb3e48a517bf38685c05a"
PROJECTION = "efab27a9-5d44-52ba-ad74-47940d5fd717"
EVIDENCE = frozenset({"reviewer", "accepted_at", "rule"})


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def rule(at: str) -> str:
    return (
        f"Owner exact acceptance, {OWNER}: {STATEMENT!r} Accepted proposal "
        f"{PROPOSAL_IDENTITY} (rendered sha256 {PINS[PROPOSAL_FILE]}); receipt "
        f"{RECEIPT.relative_to(REPO).as_posix()} sha256 {PINS[RECEIPT]}; Owner "
        f"packet sha256 {EXTERNAL_PINS['owner_packet_sha256']}; independent "
        f"review sha256 {EXTERNAL_PINS['independent_review_sha256']}; final "
        "checkpoint review sha256 "
        f"{EXTERNAL_PINS['final_checkpoint_review_sha256']}; reviewed preview "
        f"sha256 {PINS[PREVIEW]}; recording permission sha256 "
        f"{EXTERNAL_PINS['recording_permission_authorization_sha256']}; "
        f"recorded {at}"
    )


def construct(at: str) -> AcceptedInputs:
    """The reviewed construction with the real Owner evidence."""
    prior = load_accepted_inputs(PRIOR_PATH)
    (batch,) = [b for b in prior.batches if b.batch_id == BATCH]
    recorded = build_proposal(class_eligibility_edited(generator().batch())).proposal
    assert proposal_identity(recorded) == batch.proposal_identity, "regeneration"
    excised, _ = excise(prior, BATCH, recorded.proposed_representation)
    g1 = build_proposal(class_eligibility_edited(g1_generator().batch())).proposal
    assert proposal_identity(g1) == PROPOSAL_IDENTITY, proposal_identity(g1)
    assert sha(render(g1).encode("utf-8")) == PINS[PROPOSAL_FILE], "proposal bytes"
    return accept_proposal(
        g1,
        batch_id=BATCH,
        rule=rule(at),
        resolved_scope=tuple(p.span.span_id for p in g1.proposed_spans),
        resolved_review_units=tuple(u.unit_id for u in g1.proposed_review_units),
        reviewer=OWNER,
        accepted_at=at,
        prior=excised,
    )


def _blank(x: Any) -> Any:
    if isinstance(x, dict):
        return {k: ("<evidence>" if k in EVIDENCE else _blank(v)) for k, v in x.items()}
    if isinstance(x, list):
        return [_blank(v) for v in x]
    return x


def compare(preview: bytes, recorded: bytes) -> dict[str, Any]:
    """Recorded vs preview: only the three evidence fields, only on Equipment."""
    a, b = json.loads(preview), json.loads(recorded)
    outside = sorted(k for k in a.keys() | b.keys() if k != "acceptance" and a.get(k) != b.get(k))
    blanked_equal = _blank(a["acceptance"]) == _blank(b["acceptance"])
    changed: dict[str, int] = {}
    foreign: list[str] = []
    for coll in ("batches", "records", "review_unit_records"):
        for x, y in zip(a["acceptance"][coll], b["acceptance"][coll], strict=True):
            for k in EVIDENCE & x.keys():
                if x[k] != y[k]:
                    changed[f"{coll}.{k}"] = changed.get(f"{coll}.{k}", 0) + 1
                    if x.get("batch_id") != BATCH:
                        foreign.append(f"{coll}:{x.get('batch_id')}")
    return {
        "outside_acceptance_differences": outside,
        "acceptance_equal_after_blanking_evidence": blanked_equal,
        "evidence_changed": changed,
        "evidence_changed_outside_equipment": sorted(set(foreign)),
    }


def native_checks(inputs: AcceptedInputs) -> dict[str, Any]:
    tmp = Path(tempfile.mkdtemp(prefix="g1-record-"))
    engine = None
    try:
        db = tmp / "release.db"
        shutil.copyfile(STORE, db)
        engine = create_engine(f"sqlite:///{db}")
        Base.metadata.create_all(engine)
        with create_session_factory(engine)() as s:
            b = inputs.oracle.binding
            corpus = load_bound_corpus(s, b.package_uuid, b.release_version)
            findings = list(
                validate_candidate(candidate_from_accepted_inputs(inputs), corpus)
            )
            identified = identify_projection(candidate_from_accepted_inputs(inputs))
            persist_draft(s, identified, now="2026-10-11T00:00:00Z")
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
                "reidentified_projection": identify_projection(rebuilt).projection_uuid,
                "projection": identified.projection_uuid,
                "gate_passed": gate.passed,
                "gate_failures": [f.detail for f in gate.failures][:10],
            }
    finally:
        if engine is not None:
            engine.dispose()
        shutil.rmtree(tmp, ignore_errors=True)


def main() -> None:
    for path, want in PINS.items():
        got = sha(path.read_bytes())
        print(f"pin {got == want} {path.relative_to(REPO).as_posix()}")
        assert got == want, path
    receipt = json.loads(RECEIPT_JSON.read_text("utf-8"))
    assert receipt["exact_user_message"] == STATEMENT and receipt["owner"] == OWNER
    assert receipt["receipt_sha256"] == PINS[RECEIPT]
    for key, value in EXTERNAL_PINS.items():
        assert receipt[key] == value, key

    if TARGET.exists():
        existing = load_accepted_inputs(TARGET)
        (at,) = {a.accepted_at for a in existing.acceptances if a.batch_id == BATCH}
        mode = "verify"
    else:
        at = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        assert at > receipt["receipt_recorded_at_utc"], at
        mode = "record"
    print("mode", mode, "recording time", at)

    inputs = construct(at)
    data = serialize_accepted_inputs(inputs)
    assert b"SIMULATION" not in data, "simulated evidence in the recording"
    report = compare(PREVIEW.read_bytes(), data)
    print(json.dumps(report, indent=1))
    assert not report["outside_acceptance_differences"]
    assert report["acceptance_equal_after_blanking_evidence"]
    assert not report["evidence_changed_outside_equipment"]
    assert oracle_identity(inputs.oracle) == ORACLE_IDENTITY, "oracle identity"
    assert load_accepted_inputs_bytes_roundtrip(data)

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
    assert native["gate_passed"] and not native["gate_failures"]
    assert sha(PRIOR_PATH.read_bytes()) == PRIOR_SHA256, "prior oracle changed"

    followup = {
        "mode": mode,
        "recorded_at": at,
        "successor": TARGET.relative_to(REPO).as_posix(),
        "successor_sha256": sha(on_disk),
        "successor_bytes": len(on_disk),
        "proposal_identity": PROPOSAL_IDENTITY,
        "oracle_identity": ORACLE_IDENTITY,
        "projection": PROJECTION,
        "prior_oracle_sha256_after": sha(PRIOR_PATH.read_bytes()),
        "comparison_with_reviewed_preview": report,
        "native": native,
    }
    FOLLOWUP.write_text(json.dumps(followup, indent=1) + "\n", encoding="utf-8")
    print("successor sha256", followup["successor_sha256"])


def load_accepted_inputs_bytes_roundtrip(data: bytes) -> bool:
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "roundtrip.json"
        p.write_bytes(data)
        return serialize_accepted_inputs(load_accepted_inputs(p)) == data


if __name__ == "__main__":
    main()
