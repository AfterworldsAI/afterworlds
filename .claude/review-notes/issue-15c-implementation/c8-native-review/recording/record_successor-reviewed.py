"""Record the Owner-accepted CRD Issue 15c C8 successor.

Run from the repository root with the clone's venv:

    PYTHONIOENCODING=utf-8 venv/Scripts/python.exe         .claude/review-notes/issue-15c-c8-recording/record_successor.py

The construction is the reviewed one (``issue-15c-c8-native/build_c8_preview``,
corrected code ``bf3fb2d``): on the recorded C7 successor (``2853f30a...``,
never modified), each of the five touched batches is excised (claim-based)
and its C8 proposal -- byte-identical to the accepted preview's rendered
proposal -- is accepted natively in its place, recording the registered
20 -> 21 lift. Only the acceptance evidence differs from the reviewed
simulated preview: the real Owner as reviewer, the recording time, and a rule
quoting the Owner's statement and the pinned hashes. The preview and packet
are preserved unchanged.

Write-once, as the C5 and C7 recordings: if the successor does not exist it
is recorded; if it exists it is rebuilt from the evidence it carries and must
match byte for byte. Either way the proofs below run and
``recorded-followup.json`` is written:

* pins: C7 successor, G1, predecessor, raw C8 inputs, receipt, decision
  packet, Owner packet, addendum, reviews, the preserved preview and its five
  proposals;
* each rebuilt proposal renders byte-identical to the accepted preview's;
* oracle identity and projection (UUID and payload hash) equal the accepted;
* the recording differs from the preview only in ``reviewer``,
  ``accepted_at`` and ``rule``, and only on the five batches' rows;
* no SIMULATION residue; the C7 successor, G1 and predecessor bytes untouched;
* native ``validate_candidate`` has no findings; persist -> reconstruct ->
  re-identify; the read-only publication gate passes against the recording
  in a private copy of the isolated release store. Nothing is published.
"""

from __future__ import annotations

import datetime
import json
import sys
import tempfile
from pathlib import Path
from typing import Any

REPO = Path.cwd()
NOTES = REPO / ".claude/review-notes"
sys.path.insert(0, str(NOTES / "issue-15c-c8-native"))

import build_c8_preview as b  # noqa: E402  (pins inputs, asserts schema 21)

c = b.c
HERE = NOTES / "issue-15c-c8-recording"
NATIVE = NOTES / "issue-15c-c8-native"
IMPL = NOTES / "issue-15c-implementation"
PREVIEW_DIR = REPO / ".claude/worktrees/agent-aa5b1ea6bf4ee4f39" / (
    ".claude/review-notes/issue-15c-c8-native/preview"
)
PREVIEW = PREVIEW_DIR / "srd-5-2-1-corpus-8781d4e0-a3b-c8-PREVIEW.json"
RECEIPT = NATIVE / "owner-acceptance-2026-10-13.md"
DECISION = IMPL / "codex-c8-owner-decision-packet.md"
RECEIPT_JSON = HERE / "owner-acceptance.json"
PACKET = NATIVE / "OWNER-PACKET.md"
ADDENDUM = NATIVE / "PLANNING-ADDENDUM-target-domain.md"
REVIEW = IMPL / "codex-c8-native-final-review.md"
REVALIDATION = NATIVE / "reports/c8-revalidation.json"
TARGET = b.COMMITTED_ORACLE_DIR / "srd-5-2-1-corpus-8781d4e0-a3b-15c-c8.json"
FOLLOWUP = HERE / "recorded-followup.json"

OWNER = "Ravenlok (Owner)"
STATEMENT = "Accept exact C8"
PROPOSAL_FILES = {
    "spell-descriptions": (
        "68c7526213cf976963e9408b0063140c70af38ef7a671c23c4144e00dfcc4377",
        "1c01d1e4f603acebf8baa14b909b7b07406e0e3f0c27330a305363f923d527c7",
    ),
    "magic-items": (
        "f6a8b41281de0023a493803c934bf906ed8ee5909a544a9800743f0e9c63a2cd",
        "d88713097ad106b5e645b35cf1e0f1bffaa6408a8cd7af2faa4da68331f6996b",
    ),
    "monsters": (
        "c12dad2846359cd35823c48c36e7dbca6fc6553a37c65ac5764a571173289984",
        "bec1bedc4097a7b42c6acbf64c6131688caa2c86cc85616006b2de1a85c886be",
    ),
    "animals": (
        "6c2cd65751bdbefbb48ac042c0a201af087f8aca0cd9229a0e53bf48d95b8bbf",
        "db3f0d2dd9c997f4f2edc1f8fd361244becf7720ab80834c7e2828d971e92014",
    ),
    "character-origins-feats": (
        "9705cf1d223db4395311f23215bd12e451a1115a65b1ee6b3aa8bcd88674f1fe",
        "301572d46bc655125bc45ad8d08b53d044c0d28014c2ea0340bedd08d2a20f5f",
    ),
}
PINS = {
    b.SUCCESSOR: "2853f30a832ca581c9d4169b82d0c360f3d6a2d78f0ad8980de9997eef51f373",
    c.G1_PATH: c.G1_SHA256,
    c.PREDECESSOR_PATH: c.PREDECESSOR_SHA256,
    b.C8: "7e7d5b43ccd7bd877e0764643e57df1270419dd758a6ae5fcf52422081e42628",
    b.CORRESPONDENCE: (
        "43589153ee7befe4e46052f0e7fe7db053b5a9a22c3ff8a6b4468e41c9e0ce24"
    ),
    RECEIPT: "0fffe6c014f6e98b4559320477c921c2732d376e4811b8d4d070ad65c11bdee2",
    DECISION: "7a29c7cd27d3e0434da090fa59f30bf0df94c9c4fd04a604846d22ad013bcdc6",
    PACKET: "b9c6cbec31f386d8962d44edb5c8615e59596e5c5c32f73b83ff4ce65d8c59a7",
    ADDENDUM: "cb76230c7b98344ccf60bebacddaf1408d779ae0e8eb7ae5cbb1240af9a4fa8a",
    REVIEW: "bedbcfabff0471e4b82e3a3324ba88f1224510af67661f66e00d82bcdb2beb85",
    REVALIDATION: "77b22fd668c8b773aa1d25c322cbbb40b369cf54c68966872e0ba373e228f584",
    PREVIEW: "a2d96264dd18605680358393270e1f9f4fc27da144fda09da06e31cbd5250016",
    **{
        PREVIEW_DIR / f"{batch}-C8-PROPOSAL.json": rendered
        for batch, (rendered, _) in PROPOSAL_FILES.items()
    },
}
SCHEMA = (b.SCHEMA_21_VERSION, b.SCHEMA_21_HASH)
assert SCHEMA == (
    "5d-representation-schema-21",
    "4499b3964aac338e10c7b6d1f67a5eb37570878600e0c5f04bd4464d58f1df55",
)
ORACLE_IDENTITY = "70646cd987dcf75adc7b57b6271e38c6ca8cc9b508584dac89c5acefafa3e8d9"
PROJECTION = "e4f8f4fb-de6c-53c9-98f1-fa7a0159fe42"
PAYLOAD_HASH = "e615d0106996466b8ab72dacd481934b7982e4c421a661eb2cc0e3fcdfad5d87"
EVIDENCE = frozenset({"reviewer", "accepted_at", "rule"})
TOUCHED = frozenset(PROPOSAL_FILES)
sha = b.sha


def rule(at: str) -> str:
    return (
        f"Owner exact acceptance, {OWNER}: {STATEMENT!r} CRD Issue 15c C8 "
        f"successor (includes disclosed interpretations I1 and I2). Decision "
        f"packet {DECISION.relative_to(REPO).as_posix()} sha256 {PINS[DECISION]}; "
        f"receipt {RECEIPT.relative_to(REPO).as_posix()} sha256 {PINS[RECEIPT]}; "
        f"Owner packet sha256 {PINS[PACKET]}; independent final review sha256 "
        f"{PINS[REVIEW]}; corrected revalidation sha256 {PINS[REVALIDATION]}; "
        f"reviewed preview sha256 {PINS[PREVIEW]}; schema {SCHEMA[0]} "
        f"{SCHEMA[1]}; oracle identity {ORACLE_IDENTITY}; projection "
        f"{PROJECTION}; recorded {at}"
    )


def construct(at: str) -> tuple[Any, dict[str, str]]:
    base = b.load_accepted_inputs(b.SUCCESSOR)
    built = b.build(base)
    assert set(built) == TOUCHED, sorted(built)
    identities = {}
    for batch, (_, new, _) in built.items():
        rendered, identity = PROPOSAL_FILES[batch]
        text = b.render(new).encode("utf-8")
        assert sha(text) == rendered, ("rendered proposal", batch)
        assert b.proposal_identity(new) == identity, ("proposal identity", batch)
        assert (new.schema_version, new.schema_hash) == SCHEMA, batch
        identities[batch] = identity
    state = base
    for batch in [a.batch_id for a in base.schema_anchors if a.batch_id in built]:
        accepted, new, _ = built[batch]
        (old,) = [x for x in state.batches if x.batch_id == batch]
        excised, _ = b.excise(state, {batch: accepted.proposed_representation})
        state = b.accept_proposal(
            new,
            batch_id=batch,
            resolved_scope=old.resolved_scope,
            resolved_review_units=tuple(u.unit_id for u in new.proposed_review_units),
            prior=excised,
            rule=rule(at),
            reviewer=OWNER,
            accepted_at=at,
        )
    return state, identities


def _blank(x: Any) -> Any:
    if isinstance(x, dict):
        return {k: ("<evidence>" if k in EVIDENCE else _blank(v)) for k, v in x.items()}
    if isinstance(x, list):
        return [_blank(v) for v in x]
    return x


def _row_key(coll: str, row: dict[str, Any]) -> tuple[str, ...]:
    if coll == "batches":
        return (row["batch_id"],)
    unit = row.get("span_id") or row.get("unit_id")
    return (row["batch_id"], str(unit))


def compare(preview: bytes, recorded: bytes) -> dict[str, Any]:
    """Recorded vs preview: only the three evidence fields, only on the five.

    Evidence rows are serialized in canonical order (``canonical_order``),
    which reads the row content -- ``accepted_at`` included -- so a real
    recording time can move the touched batches' rows relative to the
    preview's simulated time. Rows are therefore matched by identity; the
    untouched rows' own order is checked separately.
    """
    a, r = json.loads(preview), json.loads(recorded)
    outside = sorted(
        k for k in a.keys() | r.keys() if k != "acceptance" and a.get(k) != r.get(k)
    )
    changed: dict[str, int] = {}
    foreign: list[str] = []
    non_evidence: list[str] = []
    untouched_order: dict[str, bool] = {}
    for coll in ("batches", "records", "review_unit_records"):
        rows_a = {_row_key(coll, x): x for x in a["acceptance"][coll]}
        rows_r = {_row_key(coll, y): y for y in r["acceptance"][coll]}
        assert len(rows_a) == len(a["acceptance"][coll]), coll
        assert rows_a.keys() == rows_r.keys(), coll
        for key, x in rows_a.items():
            y = rows_r[key]
            if _blank(x) != _blank(y):
                non_evidence.append(f"{coll}:{key}")
            for k in EVIDENCE & x.keys():
                if x[k] != y[k]:
                    changed[f"{coll}.{k}"] = changed.get(f"{coll}.{k}", 0) + 1
                    if x.get("batch_id") not in TOUCHED:
                        foreign.append(f"{coll}:{x.get('batch_id')}")
        untouched_order[coll] = [
            _row_key(coll, x)
            for x in a["acceptance"][coll]
            if x["batch_id"] not in TOUCHED
        ] == [
            _row_key(coll, y)
            for y in r["acceptance"][coll]
            if y["batch_id"] not in TOUCHED
        ]
    others = {k: v for k, v in a["acceptance"].items() if k not in untouched_order}
    return {
        "outside_acceptance_differences": outside,
        "acceptance_equal_after_blanking_evidence": not non_evidence
        and others == {k: r["acceptance"][k] for k in others}
        and a["acceptance"].keys() == r["acceptance"].keys(),
        "non_evidence_differences": non_evidence[:10],
        "untouched_rows_in_same_order": untouched_order,
        "evidence_changed": changed,
        "evidence_changed_outside_touched": sorted(set(foreign)),
    }


def native_checks(inputs: Any, at: str) -> dict[str, Any]:
    with c.private_store() as db:
        engine = b.create_engine(f"sqlite:///{db}")
        try:
            b.Base.metadata.create_all(engine)
            with b.create_session_factory(engine)() as s:
                binding = inputs.oracle.binding
                corpus = b.load_bound_corpus(
                    s, binding.package_uuid, binding.release_version
                )
                findings = list(
                    b.validate_candidate(b.candidate_from_accepted_inputs(inputs), corpus)
                )
                identified = b.identify_projection(b.candidate_from_accepted_inputs(inputs))
                b.persist_draft(s, identified, now=at)
                s.commit()
                reconstruction = b.verify_reconstruction(s, identified)
                rebuilt = b.reconstruct_candidate(s, identified.projection_uuid)
                b.record_persisted_state_digest(s, identified.projection_uuid)
                s.commit()
                gate = b.run_publication_gate(s, identified.projection_uuid, inputs.oracle)
                return {
                    "validate_candidate_findings": findings[:10],
                    "validate_candidate_finding_count": len(findings),
                    "verify_reconstruction": list(reconstruction),
                    "reconstructed_payload_identical": b.projection_payload(rebuilt)
                    == b.projection_payload(identified.candidate),
                    "reidentified_projection": str(
                        b.identify_projection(rebuilt).projection_uuid
                    ),
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
        return b.serialize_accepted_inputs(b.load_accepted_inputs(p)) == data


def main() -> None:
    for path, want in PINS.items():
        got = sha(path.read_bytes())
        print(f"pin {got == want} {path.relative_to(REPO).as_posix()}")
        assert got == want, path
    receipt = json.loads(RECEIPT_JSON.read_text("utf-8"))
    assert receipt["exact_user_message"] == STATEMENT and receipt["owner"] == OWNER
    assert receipt["receipt_sha256"] == PINS[RECEIPT]
    assert receipt["owner_packet_sha256"] == PINS[PACKET]
    assert receipt["decision_packet_sha256"] == PINS[DECISION]
    assert STATEMENT in RECEIPT.read_text("utf-8")
    packet = PACKET.read_text("utf-8")
    for _, identity in PROPOSAL_FILES.values():
        assert identity in packet, identity

    if TARGET.exists():
        existing = b.load_accepted_inputs(TARGET)
        (at,) = {a.accepted_at for a in existing.acceptances if a.batch_id in TOUCHED}
        mode = "verify"
    else:
        at = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        assert at > receipt["receipt_recorded_at_utc"], at
        mode = "record"
    print("mode", mode, "recording time", at)

    inputs, identities = construct(at)
    data = b.serialize_accepted_inputs(inputs)
    assert b"SIMULATION" not in data, "simulated evidence in the recording"
    report = compare(PREVIEW.read_bytes(), data)
    print(json.dumps(report, indent=1))
    assert not report["outside_acceptance_differences"]
    assert report["acceptance_equal_after_blanking_evidence"]
    assert not report["evidence_changed_outside_touched"]
    assert all(report["untouched_rows_in_same_order"].values())
    assert b.oracle_identity(inputs.oracle) == ORACLE_IDENTITY, "oracle identity"
    assert (inputs.oracle.schema_version, inputs.oracle.schema_hash) == SCHEMA
    assert roundtrip(data)

    if mode == "record":
        with TARGET.open("xb") as f:
            f.write(data)
        print("wrote", TARGET.relative_to(REPO).as_posix())
    on_disk = TARGET.read_bytes()
    assert on_disk == data, "on-disk successor differs from the reconstruction"

    native = native_checks(b.load_accepted_inputs(TARGET), at)
    print(json.dumps(native, indent=1))
    assert native["validate_candidate_finding_count"] == 0
    assert native["verify_reconstruction"] == []
    assert native["reconstructed_payload_identical"]
    assert native["projection"] == native["reidentified_projection"] == PROJECTION
    assert native["payload_hash"] == PAYLOAD_HASH
    assert native["gate_passed"] and not native["gate_failures"]
    for path in (b.SUCCESSOR, c.G1_PATH, c.PREDECESSOR_PATH):
        assert sha(path.read_bytes()) == PINS[path], f"{path} changed"

    followup = {
        "mode": mode,
        "recorded_at": at,
        "successor": TARGET.relative_to(REPO).as_posix(),
        "successor_sha256": sha(on_disk),
        "successor_bytes": len(on_disk),
        "prior_successor_sha256_after": sha(b.SUCCESSOR.read_bytes()),
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
