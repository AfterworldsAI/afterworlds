"""Record the Owner-accepted CRD Issue 15c C7 successor.

Run from the repository root with the clone's venv:

    PYTHONIOENCODING=utf-8 venv/Scripts/python.exe \
        .claude/review-notes/issue-15c-c7-recording/record_successor.py

The construction is the reviewed one (``issue-15c-c7-native/build_c7_preview``):
on the recorded C5 successor (``23e5d8e0...``, never modified), each of the two
touched batches is excised (claim-based) and its C7 proposal -- byte-identical
to the accepted packet's rendered proposal -- is accepted natively in its
place, recording the registered 19 -> 20 lift. Only the acceptance evidence
differs from the reviewed simulated preview: the real Owner as reviewer, the
recording time, and a rule quoting the Owner's statement and the pinned
hashes. The preview and packet are preserved unchanged.

Write-once, as the C5 recording: if the successor does not exist it is
recorded; if it exists it is rebuilt from the evidence it carries and must
match byte for byte. Either way the proofs below run and
``recorded-followup.json`` is written:

* pins: C5 successor, G1, predecessor, raw C7, packet, receipts, reviews,
  the preserved preview and its two proposals;
* each rebuilt proposal renders byte-identical to the accepted preview's;
* oracle identity and projection (UUID and payload hash) equal the accepted;
* the recording differs from the preview only in ``reviewer``,
  ``accepted_at`` and ``rule``, and only on the two batches' rows;
* no SIMULATION residue; the C5 successor, G1 and predecessor bytes untouched;
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
sys.path.insert(0, str(NOTES / "issue-15c-c7-native"))

import build_c7_preview as b  # noqa: E402  (pins inputs, asserts schema 20)

c = b.c
HERE = NOTES / "issue-15c-c7-recording"
NATIVE = NOTES / "issue-15c-c7-native"
IMPL = NOTES / "issue-15c-implementation"
PREVIEW_DIR = REPO / ".claude/worktrees/agent-afb6123d0b7851456" / (
    ".claude/review-notes/issue-15c-c7-native/preview"
)
PREVIEW = PREVIEW_DIR / "srd-5-2-1-corpus-8781d4e0-a3b-c7-PREVIEW.json"
RECEIPT = NATIVE / "owner-acceptance-2026-10-13.md"
INTEGRATION = IMPL / "owner-c7-integration-2026-10-13.md"
RECEIPT_JSON = HERE / "owner-acceptance.json"
PACKET = NATIVE / "OWNER-PACKET.md"
REVIEW = IMPL / "codex-c7-native-review.md"
CORRECTION = IMPL / "codex-c7-native-correction-review.md"
TARGET = b.COMMITTED_ORACLE_DIR / "srd-5-2-1-corpus-8781d4e0-a3b-15c-c7.json"
FOLLOWUP = HERE / "recorded-followup.json"

OWNER = "Ravenlok (Owner)"
STATEMENT = (
    'Do these: "existing logs show 9 malformed-input regressions" need revision? '
    "If not, I accept the exact C7 packet. If so, let's do those first."
)
PROPOSAL_FILES = {
    "character-origins-feats": (
        "587068868bbcbc05cb881f3ae4b2e68cb2c47c257192671470bdf792c17f178e",
        "1e7b63d3800154eee539297b0ae5d4f9efbfe21c1776986db133e3cc046bfd28",
    ),
    "equipment": (
        "5eb398b632b8dc226c22136df14e0b140408f27c5754ffbb115b7ccfba52c2ab",
        "b8c65454cae97f82cdb96c857aad84c70ba8c78e96fa24f1e95e89360e144a76",
    ),
}
PINS = {
    b.SUCCESSOR: "23e5d8e0fac60e3f5417b3a41e40e6f475366dd385856f38c42104f4dd264f69",
    c.G1_PATH: c.G1_SHA256,
    c.PREDECESSOR_PATH: c.PREDECESSOR_SHA256,
    b.C7: "bf2a269c6f5446a63d5ce2353c27d5dc75224935cd16960ce79da7e766aefa77",
    PACKET: "4912928fcfe58d0612ea908d21ad59988d6649b1e5b31be35b776d178948eb2c",
    RECEIPT: "116922a0cab21f3efa49ac9480e332ee81150681955ff0e93bdd494973da064f",
    INTEGRATION: "0ade8f3d68191feb1ff79b6ee45c36860ec1e3378f92b9b81ec81e2689f34a4a",
    REVIEW: "570cf7e6e039c8889551aec22bedc45eb65e72baa984602d3d75f0246e82a8a0",
    CORRECTION: "47eeae2262d0987dc3b9e05f237fec280bd104d44e3479dad835ae9a97df090d",
    PREVIEW: "d661cc3be22aa6aca996a4e67cac4f8ebbd2dfa1908dd29a0c7ae2e38177ef6d",
    **{
        PREVIEW_DIR / f"{batch}-C7-PROPOSAL.json": rendered
        for batch, (rendered, _) in PROPOSAL_FILES.items()
    },
}
SCHEMA = (b.SCHEMA_20_VERSION, b.SCHEMA_20_HASH)
assert SCHEMA == (
    "5d-representation-schema-20",
    "759dcc1f9de2cac9254be108ca8a83433ca30854061276a9c349a370e1c6e77a",
)
ORACLE_IDENTITY = "cb04163ba0374e95ce0fcdaae939b00793e71f84ed3222593c4babfc9065ef6e"
PROJECTION = "8446ab6b-be75-5999-8a9b-74fa133c030a"
PAYLOAD_HASH = "cffcdbfa70a6e64351b852ff9b932aa32df81abdd45700ef6c0034aefdaeb65a"
EVIDENCE = frozenset({"reviewer", "accepted_at", "rule"})
TOUCHED = frozenset(PROPOSAL_FILES)
sha = b.sha


def rule(at: str) -> str:
    return (
        f"Owner exact acceptance, {OWNER}: {STATEMENT!r} CRD Issue 15c consolidated "
        f"native C7 successor (includes disclosed inference I2). Owner packet "
        f"{PACKET.relative_to(REPO).as_posix()} sha256 {PINS[PACKET]}; receipt "
        f"{RECEIPT.relative_to(REPO).as_posix()} sha256 {PINS[RECEIPT]}; "
        f"integration authorization sha256 {PINS[INTEGRATION]}; independent "
        f"review sha256 {PINS[REVIEW]}, correction review sha256 "
        f"{PINS[CORRECTION]}; reviewed preview sha256 {PINS[PREVIEW]}; schema "
        f"{SCHEMA[0]} {SCHEMA[1]}; oracle identity {ORACLE_IDENTITY}; projection "
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
    """Recorded vs preview: only the three evidence fields, only on the two.

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
