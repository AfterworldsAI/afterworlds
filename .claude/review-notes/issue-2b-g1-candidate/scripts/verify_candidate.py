"""Verify the CRD Issue 2b G1 candidate natively, in isolated store copies.

REVIEW MATERIAL; nothing is published or activated and no shared store is
touched. Checks, each asserted and recorded in ``reports/verify-candidate.json``:

1. Native findings: ``validate_candidate`` against the bound release. The
   candidate must have none. Under this build (schema 18) the schema-17 prior
   must be refused for its schema declaration and for nothing else.
2. Persist -> reconstruct -> re-identify for both, each in its own temp copy of
   the isolated release store, then the read-only publication gate: each
   projection against its own oracle passes; each against the other's oracle
   is refused (fail-closed control).
3. Preservation: the other 23 batches, their acceptance records, review-unit
   records and schema anchors, all 1,486 reference resolutions and their
   records, and every span and representation element outside the Equipment
   batch are byte-identical between the prior oracle and the candidate.
"""

import json
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, ".claude/review-notes/issue-2b-g1-candidate/scripts")
from build_candidate import CANDIDATE  # noqa: E402
from common import BATCH, HERE, PRIOR_PATH, PRIOR_SHA256, STORE, sha  # noqa: E402
from sqlalchemy import event  # noqa: E402

from afterworlds.ingestion.mechanical.bound_corpus import (  # noqa: E402
    load_bound_corpus,
)
from afterworlds.ingestion.mechanical.gate import (  # noqa: E402
    GateFailureCategory,
    run_publication_gate,
)
from afterworlds.ingestion.mechanical.oracle import (  # noqa: E402
    candidate_from_accepted_inputs,
    load_accepted_inputs,
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
from afterworlds.persistence.database import (  # noqa: E402
    create_engine,
    create_session_factory,
)
from afterworlds.persistence.orm.base import Base  # noqa: E402

NOW = "2026-10-10T00:00:00Z"
report: dict[str, object] = {}
checks: list[tuple[str, bool]] = []


def check(name: str, ok: bool) -> None:
    checks.append((name, ok))
    print(("PASS " if ok else "FAIL ") + name)


def store_copy(tmp: Path, name: str) -> Path:
    p = tmp / name
    shutil.copyfile(STORE, p)
    engine = create_engine(f"sqlite:///{p}")
    Base.metadata.create_all(engine)
    engine.dispose()
    return p


def session_for(db: Path, engines: list) -> object:
    engine = create_engine(f"sqlite:///{db}")

    @event.listens_for(engine, "connect")
    def _fk(dbapi, _rec):  # type: ignore[no-untyped-def]
        dbapi.execute("PRAGMA foreign_keys=ON")

    engines.append(engine)
    return create_session_factory(engine)()


assert sha(PRIOR_PATH.read_bytes()) == PRIOR_SHA256
prior = load_accepted_inputs(PRIOR_PATH)
cand = load_accepted_inputs(CANDIDATE)
report["candidate_sha256"] = sha(CANDIDATE.read_bytes())

tmp = Path(tempfile.mkdtemp(prefix="g1-verify-"))
engines: list = []
try:
    # 1. Native findings.
    s = session_for(store_copy(tmp, "findings.db"), engines)
    b = cand.oracle.binding
    corpus = load_bound_corpus(s, b.package_uuid, b.release_version)
    for tag, inputs in (("prior", prior), ("candidate", cand)):
        found = list(validate_candidate(candidate_from_accepted_inputs(inputs), corpus))
        refs = [f for f in found if f.startswith("reference ")]
        leaves = [f for f in found if f.startswith("leaf ")]
        report[f"{tag}_findings"] = {
            "reference": len(refs),
            "uncovered_leaf": len(leaves),
            "other": len(found) - len(refs) - len(leaves),
            "first": found[:10],
        }
        if tag == "candidate":
            check("candidate: validate_candidate reports no findings", not found)
        else:
            check(
                "prior: under schema 18 refused for its schema-17 declaration only",
                len(found) == 2
                and all("declares representation schema" in f for f in found),
            )
    s.close()

    # 2. Persist, reconstruct, gate.
    ids = {}
    sessions = {}
    for tag, inputs in (("prior", prior), ("candidate", cand)):
        s = session_for(store_copy(tmp, f"{tag}.db"), engines)
        sessions[tag] = s
        identified = identify_projection(candidate_from_accepted_inputs(inputs))
        persist_draft(s, identified, now=NOW)
        s.commit()
        check(f"{tag}: verify_reconstruction is empty",
              verify_reconstruction(s, identified) == ())
        rebuilt = reconstruct_candidate(s, identified.projection_uuid)
        check(f"{tag}: reconstructed candidate's canonical payload is identical",
              projection_payload(rebuilt) == projection_payload(identified.candidate))
        check(f"{tag}: reconstruction re-identifies to the persisted projection",
              identify_projection(rebuilt).projection_uuid == identified.projection_uuid)
        ids[tag] = identified.projection_uuid
        record_persisted_state_digest(s, identified.projection_uuid)
        s.commit()
        gate = run_publication_gate(s, identified.projection_uuid, inputs.oracle)
        report[f"{tag}_own_gate_categories"] = sorted(
            c.value for c in gate.categories()
        )
        if tag == "candidate":
            check("candidate: publication gate passes against its own oracle",
                  gate.passed and not gate.failures)
        else:
            report["prior_own_gate_failures"] = [f.detail for f in gate.failures]
            check("prior: under schema 18 its own gate refuses on schema only",
                  not gate.passed
                  and gate.categories()
                  <= {GateFailureCategory.SCHEMA_MISMATCH,
                      GateFailureCategory.SEMANTIC_VALIDATION}
                  and all("schema" in f.detail for f in gate.failures))
    for tag, other in (("prior", cand), ("candidate", prior)):
        gate = run_publication_gate(sessions[tag], ids[tag], other.oracle)
        check(f"{tag} projection is refused against the other oracle",
              not gate.passed and bool(gate.failures))
        report[f"{tag}_cross_gate_categories"] = sorted(
            c.value for c in gate.categories()
        )
    report["projection_ids"] = ids
    for s in sessions.values():
        s.close()
finally:
    for e in engines:
        e.dispose()
    shutil.rmtree(tmp, ignore_errors=True)

# 3. Preservation, on the serialized payloads.
P = json.loads(PRIOR_PATH.read_text("utf-8"))
C = json.loads(CANDIDATE.read_text("utf-8"))
pa, ca = P["acceptance"], C["acceptance"]


def by_batch(rows: list, keep: bool) -> list:
    return [r for r in rows if (r["batch_id"] != BATCH) == keep]


for field in ("batches", "records", "review_unit_records", "schema_anchors"):
    check(f"acceptance.{field}: the other 23 batches' rows are byte-identical",
          by_batch(pa[field], True) == by_batch(ca[field], True))
check("acceptance.lifts: prior lifts kept, 17->18 appended",
      ca["lifts"][: len(pa["lifts"])] == pa["lifts"]
      and [x["lift_id"] for x in ca["lifts"][len(pa["lifts"]):]]
      == ["5d-lift-schema-17-to-18"])
check("reference_resolutions: all 1,486 byte-identical",
      P["reference_resolutions"] == C["reference_resolutions"]
      and len(C["reference_resolutions"]) == 1486)
check("acceptance.reference_resolution_records: byte-identical",
      pa["reference_resolution_records"] == ca["reference_resolution_records"])
for k in ("release_binding", "semantic_policy_hash", "semantic_policy_version",
          "artifact_kind"):
    check(f"{k}: unchanged", P[k] == C[k])
(eq,) = [b for b in pa["batches"] if b["batch_id"] == BATCH]
scope = set(eq["resolved_scope"])
(neq,) = [b for b in ca["batches"] if b["batch_id"] == BATCH]
nscope = set(neq["resolved_scope"])
check("spans outside the Equipment scope are byte-identical",
      [x for x in P["spans"] if x["span_id"] not in scope]
      == [x for x in C["spans"] if x["span_id"] not in nscope])
units_old = {r["unit_id"] for r in by_batch(pa["review_unit_records"], False)}
units_new = {r["unit_id"] for r in by_batch(ca["review_unit_records"], False)}
check("review units outside Equipment are byte-identical",
      [u for u in P["review_units"] if u["unit_id"] not in units_old]
      == [u for u in C["review_units"] if u["unit_id"] not in units_new])
delta: dict[str, dict[str, int]] = {}
for field, rows in P["representation"].items():
    old = {json.dumps(x, sort_keys=True) for x in rows}
    new = {json.dumps(x, sort_keys=True) for x in C["representation"][field]}
    gone = [json.loads(x) for x in old - new]
    added = [json.loads(x) for x in new - old]
    outside = [x for x in gone if "equipment." not in json.dumps(x)]
    delta[field] = {"removed": len(gone), "added": len(added),
                    "removed_outside_equipment": len(outside)}
    check(f"representation.{field}: nothing outside Equipment removed or changed",
          not outside)
report["representation_delta"] = delta
check("accepted oracle SHA-256 unchanged after verification",
      sha(PRIOR_PATH.read_bytes()) == PRIOR_SHA256)
report["checks"] = [{"check": n, "ok": ok} for n, ok in checks]
(HERE / "reports/verify-candidate.json").write_text(
    json.dumps(report, indent=1) + "\n", encoding="utf-8")
print(json.dumps({k: v for k, v in report.items() if k != "checks"}, indent=1))
raise SystemExit(0 if all(ok for _, ok in checks) else 1)
