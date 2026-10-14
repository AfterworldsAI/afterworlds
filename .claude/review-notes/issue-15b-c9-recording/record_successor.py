"""Record the Owner-accepted CRD Issue 15b C9 successor.

Run from the repository root with the venv and this checkout's ``src`` first
on ``PYTHONPATH``:

    PYTHONIOENCODING=utf-8 PYTHONPATH=src venv/Scripts/python.exe \
        .claude/review-notes/issue-15b-c9-recording/record_successor.py \
        --inputs PRIVATE_DIR

The Owner accepted PR #194 and the native review packet
(``owner-acceptance-2026-10-14.md``). Nothing is rebuilt: the four accepted C9
proposals are the reviewed preview's rendered files (``issue-15b-c9-native/
preview/``, git-ignored, pinned by rendered SHA-256 and proposal identity). On
the recorded C8 successor (``ead7fa9d...``, never modified), in its anchor
order, each touched batch is excised (claim-based, the packet's unchanged
``scripts/excise.py`` against the C8 proposal it was accepted from, read from
the pinned private copy) and its C9 proposal accepted natively with
``accept_proposal`` in its place, recording the registered 21 -> 22 lift. The
only difference from the reviewed SIMULATED preview is the acceptance
evidence: the real Owner as reviewer, the recording time and a rule quoting
the Owner's statement and the pinned identities. The preview, its proposals
and the packet are preserved unchanged.

Write-once, as the C5, C7 and C8 recordings: if the successor does not exist
it is recorded; if it exists it is rebuilt from the recording time it carries
and must match byte for byte. Either way the proofs below run and
``recorded-followup.json`` is written:

* pins: C8 successor, G1, predecessor, raw C9 r2, receipt, packet report, the
  packet builder (equal to the report's ``builder_sha256``), the preserved
  preview and its four proposals, the four C8 proposals and the store copy;
* oracle identity and projection (UUID and payload hash) equal the accepted;
* matched by row identity, the recording differs from the preview only in
  ``reviewer``, ``accepted_at`` and ``rule``, and only on the four batches;
  lifts, anchors and every other acceptance collection are equal;
* the 20 untouched batches' rows equal the C8 successor's, in order;
* no SIMULATION residue; the C8 successor, G1 and predecessor bytes untouched;
* native ``validate_candidate`` has no findings; persist -> reconstruct ->
  re-identify; the read-only publication gate passes against the recording
  in a private copy of the isolated release store. Nothing is published.

Carried, not rerun (the representation and projection payload equal the
accepted packet's, so they do not depend on the acceptance evidence): the
five malformed-input refusals, the cross-oracle refusals, the preservation
proof and the sequencing proof in ``issue-15b-c9-native/reports/
c9-packet.json``.
"""

from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
import tempfile
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
NOTES = HERE.parent
REPO = NOTES.parent.parent
NATIVE = NOTES / "issue-15b-c9-native"
sys.path.insert(0, str(NATIVE))

import build_c9_preview as b  # noqa: E402  (asserts schema 22 and its src)

c = b.c
sha = b.sha
PREVIEW_DIR = NATIVE / "preview"
PREVIEW = b.PREVIEW
PACKET = NATIVE / "reports/c9-packet.json"
BUILDER = NATIVE / "build_c9_preview.py"
RECEIPT = HERE / "owner-acceptance-2026-10-14.md"
RECEIPT_JSON = HERE / "owner-acceptance.json"
TARGET = b.COMMITTED_ORACLE_DIR / "srd-5-2-1-corpus-8781d4e0-a3b-15b-c9.json"
FOLLOWUP = HERE / "recorded-followup.json"

OWNER = "Ravenlok (Owner)"
#: (rendered SHA-256, proposal identity) of each accepted C9 proposal.
PROPOSAL_FILES = {
    "spell-descriptions": (
        "48f1ba1291c2cba7aacc99e80a5552e49249467f9c6bf85c65cf2f64d4650848",  # pragma: allowlist secret  # noqa: E501
        "2f296a37e843fc408a0b8cdab542d651364345c04d74cf36154a3e2479d3897b",  # pragma: allowlist secret  # noqa: E501
    ),
    "magic-items": (
        "5255c82699780573c27905898720666d930abaf7d98f41e3524ea011a0e44168",  # pragma: allowlist secret  # noqa: E501
        "b5412d4bde82e7153f119783da126ac1251fcaa106cbe094f2416bd3400f9bc6",  # pragma: allowlist secret  # noqa: E501
    ),
    "monsters": (
        "5b726871e6aa5b64120a1c01d33cd20764b6937e4ecce99102bac7a6456000a0",  # pragma: allowlist secret  # noqa: E501
        "6445a5b1433ec73f9972c78f7d4f9edfd1bf204debc588ce55272effae3824ab",  # pragma: allowlist secret  # noqa: E501
    ),
    "animals": (
        "c3dbcc7184f9167b356ec39bee9afbdb0c8bf22822f54d7951878f311275bc37",  # pragma: allowlist secret  # noqa: E501
        "3c6fa54203a5412d1d93b524d52ddb4fe80eb8627152c7761e14ac211c7305f3",  # pragma: allowlist secret  # noqa: E501
    ),
}
PINS = {
    b.SUCCESSOR: "ead7fa9d4fde484098f71221ca5ef82dfb2c82229d8fca80ab5feeb4e4d62d0d",  # pragma: allowlist secret  # noqa: E501
    c.G1_PATH: c.G1_SHA256,
    c.PREDECESSOR_PATH: c.PREDECESSOR_SHA256,
    b.C9: "a3d40545d1a0ea1b4a1e24a1e3831b12b972f50ea26981b0edf1b578fd0648db",  # pragma: allowlist secret  # noqa: E501
    RECEIPT: "30b50a3ed2a07d4eb179159b95f00e460d1988c09065b2014386f4ab3fa31b80",  # pragma: allowlist secret  # noqa: E501
    PACKET: "d61ed1b435e539da7127373d387d2124167581b9df9b5fcc9afb146049e096d4",  # pragma: allowlist secret  # noqa: E501
    BUILDER: "3cc7f94f2f8fe194fa5570aed67a3fd01baf48895bdc29023020489927446547",  # pragma: allowlist secret  # noqa: E501
    PREVIEW: "3ad7bdcb7aa926e38eca6c4019f7c77119427076a1639b2aa1f81cbfd25f59a3",  # pragma: allowlist secret  # noqa: E501
    **{
        PREVIEW_DIR / f"{batch}-C9-PROPOSAL.json": rendered
        for batch, (rendered, _) in PROPOSAL_FILES.items()
    },
}
SCHEMA = (b.SCHEMA_22_VERSION, b.SCHEMA_22_HASH)
assert SCHEMA == (
    "5d-representation-schema-22",
    "b073cd4f429631826efd628ed164a5ad680050c7e957e74680777922affb414f",  # pragma: allowlist secret  # noqa: E501
)
ORACLE_IDENTITY = "924321dff5ab1821de3a4cdf464e3db1aa28859238458ddd6a58663ddf15ab0c"  # pragma: allowlist secret  # noqa: E501
PROJECTION = "3703faf5-8b51-5c3f-b28c-b378b005f7bf"
PAYLOAD_HASH = "c7a52d551823917a8def153396262a816eb51c60a5c6b5a58cdb8d009902b82f"  # pragma: allowlist secret  # noqa: E501
BUNDLE_SHA256 = "acbee2ed44b3795614f2b0d5e08982b8cf9cac57bffa5d50cc5b306d5ca1c22d"  # pragma: allowlist secret  # noqa: E501
S1_SHA256 = "c232a7863d3a31144ebb7fcdd2f7af6591b68b4f3cb096bf65ad6e6d3372c64a"  # pragma: allowlist secret  # noqa: E501
PR_HEAD = "5d05f4732c41a527dddd5e40dbd0ac045aaceb75"
EVIDENCE = frozenset({"reviewer", "accepted_at", "rule"})
TOUCHED = frozenset(PROPOSAL_FILES)
ROWS = ("batches", "records", "review_unit_records", "schema_anchors")


def statement() -> str:
    """The Owner's message, read from the pinned receipt's quotation."""
    (line,) = re.findall(r"^> (.+)$", RECEIPT.read_text("utf-8"), re.M)
    return line


def rule(at: str) -> str:
    return (
        f"Owner exact acceptance, {OWNER}: {statement()!r} CRD Issue 15b C9 "
        f"successor (PR #194 at {PR_HEAD} and the native review packet; S1 "
        f"{S1_SHA256} stays a release-bound authored override, not recorded "
        f"here). Receipt {RECEIPT.relative_to(REPO).as_posix()} sha256 "
        f"{PINS[RECEIPT]}; native packet report sha256 {PINS[PACKET]}; bundle "
        f"C9-NATIVE-OWNER-REVIEW.zip sha256 {BUNDLE_SHA256}; raw C9 r2 sha256 "
        f"{PINS[b.C9]}; reviewed preview sha256 {PINS[PREVIEW]}; schema "
        f"{SCHEMA[0]} {SCHEMA[1]}; oracle identity {ORACLE_IDENTITY}; "
        f"projection {PROJECTION}; recorded {at}"
    )


def construct(at: str, accepted: dict[str, Path]) -> tuple[Any, dict[str, str]]:
    base = b.load_accepted_inputs(b.SUCCESSOR)
    anchors = {a.batch_id: a.proposal_identity for a in base.schema_anchors}
    identities = {}
    state = base
    for batch in [a.batch_id for a in base.schema_anchors if a.batch_id in TOUCHED]:
        old_proposal = b.load_proposal(accepted[batch])
        assert b.proposal_identity(old_proposal) == anchors[batch], batch
        new = b.load_proposal(PREVIEW_DIR / f"{batch}-C9-PROPOSAL.json")
        assert b.proposal_identity(new) == PROPOSAL_FILES[batch][1], batch
        assert (new.schema_version, new.schema_hash) == SCHEMA, batch
        identities[batch] = PROPOSAL_FILES[batch][1]
        (old,) = [x for x in state.batches if x.batch_id == batch]
        excised, _ = b.excise(state, {batch: old_proposal.proposed_representation})
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
    assert set(identities) == TOUCHED, sorted(identities)
    return state, identities


def _blank(x: Any) -> Any:
    if isinstance(x, dict):
        return {k: ("<evidence>" if k in EVIDENCE else _blank(v)) for k, v in x.items()}
    if isinstance(x, list):
        return [_blank(v) for v in x]
    return x


def _row_key(coll: str, row: dict[str, Any]) -> tuple[str, ...]:
    if coll in ("batches", "schema_anchors"):
        return (row["batch_id"],)
    unit = row.get("span_id") or row.get("unit_id")
    return (row["batch_id"], str(unit))


def compare(preview: bytes, recorded: bytes) -> dict[str, Any]:
    """Recorded vs preview: only the three evidence fields, only on the four.

    Evidence rows are serialized in canonical order, which reads the row
    content -- ``accepted_at`` included -- so a real recording time can move
    the touched batches' rows relative to the preview's simulated time. Rows
    are therefore matched by identity; the untouched rows' own order is
    checked separately. Every other acceptance collection (lifts, schema
    anchors, ...) must be equal as is.
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
        "other_acceptance_collections_equal": sorted(others),
        "non_evidence_differences": non_evidence[:10],
        "untouched_rows_in_same_order": untouched_order,
        "evidence_changed": changed,
        "evidence_changed_outside_touched": sorted(set(foreign)),
    }


def untouched_equal_c8(prior: bytes, recorded: bytes) -> dict[str, Any]:
    """The 20 untouched batches' acceptance rows equal the C8 successor's, in
    order: their receipts are preserved directly, not via the preview."""
    g, r = json.loads(prior), json.loads(recorded)

    def keep(coll: str, x: dict[str, Any]) -> list[Any]:
        return [row for row in x["acceptance"][coll] if row["batch_id"] not in TOUCHED]

    batches = {row["batch_id"] for row in g["acceptance"]["batches"]}
    return {
        "untouched_batches": len(batches - TOUCHED),
        **{coll: keep(coll, g) == keep(coll, r) for coll in ROWS},
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
                    b.validate_candidate(
                        b.candidate_from_accepted_inputs(inputs), corpus
                    )
                )
                identified = b.identify_projection(
                    b.candidate_from_accepted_inputs(inputs)
                )
                b.persist_draft(s, identified, now=at)
                s.commit()
                reconstruction = b.verify_reconstruction(s, identified)
                rebuilt = b.reconstruct_candidate(s, identified.projection_uuid)
                b.record_persisted_state_digest(s, identified.projection_uuid)
                s.commit()
                gate = b.run_publication_gate(
                    s, identified.projection_uuid, inputs.oracle
                )
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
    parser = argparse.ArgumentParser()
    parser.add_argument("--inputs", type=Path, required=True)
    args = parser.parse_args()
    # Points common at the private store copy and pins the C8 proposals.
    accepted = b.private_inputs(args.inputs)
    for path, want in PINS.items():
        got = sha(path.read_bytes())
        print(f"pin {got == want} {path.relative_to(REPO).as_posix()}")
        assert got == want, path
    packet = json.loads(PACKET.read_bytes())
    assert packet["builder_sha256"] == PINS[BUILDER], "packet builder"
    assert packet["preview_sha256"] == PINS[PREVIEW]
    assert packet["oracle_identity"] == ORACLE_IDENTITY
    for batch, (rendered, identity) in PROPOSAL_FILES.items():
        assert packet["batches"][batch]["proposal_identity"] == identity, batch
        assert packet["batches"][batch]["rendered_proposal_sha256"] == rendered
    receipt_text = RECEIPT.read_text("utf-8")
    for needle in (
        PR_HEAD,
        S1_SHA256,
        PINS[b.C9],
        BUNDLE_SHA256,
        PINS[PREVIEW],
        ORACLE_IDENTITY,
        PROJECTION,
        PAYLOAD_HASH,
        PINS[PACKET],
    ):
        assert needle in receipt_text, needle
    receipt = json.loads(RECEIPT_JSON.read_text("utf-8"))
    assert receipt["owner"] == OWNER
    assert receipt["exact_user_message"] == statement()
    assert receipt["receipt_sha256"] == PINS[RECEIPT]

    if TARGET.exists():
        existing = b.load_accepted_inputs(TARGET)
        (at,) = {a.accepted_at for a in existing.acceptances if a.batch_id in TOUCHED}
        mode = "verify"
    else:
        at = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        assert at > receipt["accepted_on"], at
        mode = "record"
    print("mode", mode, "recording time", at, flush=True)

    inputs, identities = construct(at, accepted)
    data = b.serialize_accepted_inputs(inputs)
    assert b"SIMULATION" not in data, "simulated evidence in the recording"
    report = compare(PREVIEW.read_bytes(), data)
    print(json.dumps(report, indent=1))
    assert not report["outside_acceptance_differences"]
    assert report["acceptance_equal_after_blanking_evidence"]
    assert not report["evidence_changed_outside_touched"]
    assert all(report["untouched_rows_in_same_order"].values())
    untouched = untouched_equal_c8(b.SUCCESSOR.read_bytes(), data)
    print(json.dumps(untouched, indent=1))
    assert untouched["untouched_batches"] == 20
    assert all(untouched[coll] for coll in ROWS), untouched
    assert b.oracle_identity(inputs.oracle) == ORACLE_IDENTITY, "oracle identity"
    assert (inputs.oracle.schema_version, inputs.oracle.schema_hash) == SCHEMA
    assert [lf.lift_id for lf in inputs.lifts][-1] == "5d-lift-schema-21-to-22"
    assert roundtrip(data)

    if mode == "record":
        with TARGET.open("xb") as f:
            f.write(data)
        print("wrote", TARGET.relative_to(REPO).as_posix(), flush=True)
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
    for path in (b.SUCCESSOR, c.G1_PATH, c.PREDECESSOR_PATH, PREVIEW):
        assert sha(path.read_bytes()) == PINS[path], f"{path} changed"

    followup = {
        "mode": mode,
        "recorded_at": at,
        "successor": TARGET.relative_to(REPO).as_posix(),
        "successor_sha256": sha(on_disk),
        "successor_bytes": len(on_disk),
        "prior_successor_sha256_after": sha(b.SUCCESSOR.read_bytes()),
        "reviewed_preview_sha256": PINS[PREVIEW],
        "packet_report_sha256": PINS[PACKET],
        "proposal_identities": identities,
        "schema": list(SCHEMA),
        "lifts": [lf.lift_id for lf in inputs.lifts],
        "oracle_identity": ORACLE_IDENTITY,
        "projection": PROJECTION,
        "payload_hash": PAYLOAD_HASH,
        "g1_sha256_after": sha(c.G1_PATH.read_bytes()),
        "predecessor_sha256_after": sha(c.PREDECESSOR_PATH.read_bytes()),
        "comparison_with_reviewed_preview": report,
        "untouched_rows_equal_c8_successor": untouched,
        "native": native,
        "carried_from_packet": [
            "malformed_variants_refused",
            "successor_refused_against_preview",
            "preview_refused_against_successor",
            "preservation",
            "sequencing",
        ],
    }
    FOLLOWUP.write_text(
        json.dumps(followup, indent=1) + "\n", encoding="utf-8", newline="\n"
    )
    print("successor sha256", followup["successor_sha256"])


if __name__ == "__main__":
    main()
