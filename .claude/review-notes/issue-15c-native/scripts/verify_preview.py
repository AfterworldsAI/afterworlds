"""Verify the CRD Issue 15c native preview, in private copies of the isolated
release store (adapted from ``issue-2b-g1-candidate/scripts/verify_candidate.py``).

REVIEW MATERIAL; nothing is published or activated and no shared store is
touched. Checks, each asserted and recorded in ``../reports/verify-preview.json``:

1. Native findings: ``validate_candidate`` against the bound release. The
   preview must have none; under this build (schema 19) G1 must be refused for
   its schema-18 declaration and nothing else.
2. Persist -> reconstruct -> re-identify for both, each in its own private
   store copy; the read-only publication gate passes each projection against
   its own oracle (G1: schema only) and refuses it against the other's.
3. Preservation against G1: the 13 untouched batches' ordered batch,
   acceptance, review-unit and schema-anchor rows are byte-identical; the
   eleven affected keep their batch id and resolved scope and carry only the
   SIMULATED reviewer, rule and time; lifts are G1's plus 18 -> 19;
   resolutions and their records, spans, release binding and policy are
   byte-identical; review units outside the eleven are byte-identical; and the
   representation changed by exactly the replayed -> new proposal delta.
4. Pinned inputs unchanged.
"""

from __future__ import annotations

import collections
import json
import shutil
import tempfile
from pathlib import Path
from typing import Any

import build_candidate
import common as c
from sqlalchemy import event

from afterworlds.ingestion.mechanical.bound_corpus import load_bound_corpus
from afterworlds.ingestion.mechanical.gate import GateFailureCategory, run_publication_gate
from afterworlds.ingestion.mechanical.oracle import (
    candidate_from_accepted_inputs,
    load_accepted_inputs,
)
from afterworlds.ingestion.mechanical.persistence import (
    persist_draft,
    reconstruct_candidate,
    record_persisted_state_digest,
    verify_reconstruction,
)
from afterworlds.ingestion.mechanical.projection import (
    identify_projection,
    projection_payload,
    validate_candidate,
)
from afterworlds.ingestion.mechanical.proposal import load_proposal, proposal_identity
from afterworlds.persistence.database import create_engine, create_session_factory
from afterworlds.persistence.orm.base import Base

NOW = "2026-10-12T00:00:00Z"  # SIMULATED persistence time, review only
report: dict[str, Any] = {"label": "FOCUSED DIAGNOSTICS ONLY - SIMULATION, not acceptance"}
checks: list[tuple[str, bool]] = []


def check(name: str, ok: bool) -> None:
    checks.append((name, ok))
    print(("PASS " if ok else "FAIL ") + name)


def store_copy(tmp: Path, name: str) -> Path:
    p = tmp / name
    shutil.copyfile(c.STORE, p)
    engine = create_engine(f"sqlite:///{p}")
    Base.metadata.create_all(engine)
    engine.dispose()
    return p


def session_for(db: Path, engines: list[Any]) -> Any:
    engine = create_engine(f"sqlite:///{db}")

    @event.listens_for(engine, "connect")
    def _fk(dbapi, _rec):  # type: ignore[no-untyped-def]
        dbapi.execute("PRAGMA foreign_keys=ON")

    engines.append(engine)
    return create_session_factory(engine)()


def pins() -> bool:
    try:
        c.pinned(c.G1_PATH, c.G1_SHA256)
        c.pinned(c.PREDECESSOR_PATH, c.PREDECESSOR_SHA256)
        c.pinned(c.OLD_RELEASE_PATH, c.OLD_RELEASE_SHA256)
        for name, digest in c.C5_SHA256.items():
            c.pinned(c.C5 / name, digest)
        return c.sha(c.STORE) == c.STORE_SHA256
    except AssertionError:
        return False


check("pinned inputs (G1, predecessor, old release, C5, store) unchanged before", pins())
g1 = load_accepted_inputs(c.G1_PATH)
preview = load_accepted_inputs(build_candidate.PREVIEW)
report["preview_sha256"] = c.sha(build_candidate.PREVIEW)

tmp = Path(tempfile.mkdtemp(prefix="15c-native-verify-"))
engines: list[Any] = []
try:
    assert c.sha(c.STORE) == c.STORE_SHA256
    s = session_for(store_copy(tmp, "findings.db"), engines)
    b = preview.oracle.binding
    corpus = load_bound_corpus(s, b.package_uuid, b.release_version)
    for tag, inputs in (("g1", g1), ("preview", preview)):
        found = list(validate_candidate(candidate_from_accepted_inputs(inputs), corpus))
        report[f"{tag}_findings"] = {"count": len(found), "first": found[:10]}
        if tag == "preview":
            check("preview: validate_candidate reports no findings", not found)
        else:
            check("g1: under schema 19 refused for its schema-18 declaration only",
                  bool(found) and all("declares representation schema" in f for f in found))
    s.close()

    ids, sessions = {}, {}
    for tag, inputs in (("g1", g1), ("preview", preview)):
        s = session_for(store_copy(tmp, f"{tag}.db"), engines)
        sessions[tag] = s
        identified = identify_projection(candidate_from_accepted_inputs(inputs))
        persist_draft(s, identified, now=NOW)
        s.commit()
        check(f"{tag}: verify_reconstruction is empty",
              verify_reconstruction(s, identified) == ())
        rebuilt = reconstruct_candidate(s, identified.projection_uuid)
        check(f"{tag}: reconstructed canonical payload is identical",
              projection_payload(rebuilt) == projection_payload(identified.candidate))
        again = identify_projection(rebuilt)
        check(f"{tag}: reconstruction re-identifies (uuid and payload hash)",
              again.projection_uuid == identified.projection_uuid
              and again.payload_hash == identified.payload_hash)
        ids[tag] = identified.projection_uuid
        report[f"{tag}_projection"] = {"uuid": str(identified.projection_uuid),
                                       "payload_hash": identified.payload_hash}
        report[f"{tag}_persisted_state_digest"] = str(
            record_persisted_state_digest(s, identified.projection_uuid))
        s.commit()
        gate = run_publication_gate(s, identified.projection_uuid, inputs.oracle)
        report[f"{tag}_own_gate_categories"] = sorted(x.value for x in gate.categories())
        if tag == "preview":
            check("preview: publication gate passes against its own (preview) oracle",
                  gate.passed and not gate.failures)
        else:
            report["g1_own_gate_failures"] = [f.detail for f in gate.failures]
            check("g1: under schema 19 its own gate refuses on schema only",
                  not gate.passed
                  and gate.categories() <= {GateFailureCategory.SCHEMA_MISMATCH,
                                            GateFailureCategory.SEMANTIC_VALIDATION}
                  and all("schema" in f.detail for f in gate.failures))
    for tag, other in (("g1", preview), ("preview", g1)):
        gate = run_publication_gate(sessions[tag], ids[tag], other.oracle)
        check(f"{tag} projection is refused against the other oracle",
              not gate.passed and bool(gate.failures))
        report[f"{tag}_cross_gate_categories"] = sorted(x.value for x in gate.categories())
    for s in sessions.values():
        s.close()
finally:
    for e in engines:
        e.dispose()
    shutil.rmtree(tmp, ignore_errors=True)
check("isolated store unchanged after the private copies", c.sha(c.STORE) == c.STORE_SHA256)

# 3. Preservation, on the serialized payloads.
G = c.g1()
P = json.loads(build_candidate.PREVIEW.read_text("utf-8"))
ga, pa = G["acceptance"], P["acceptance"]
affected = set(c.AFFECTED)


def rows(field: str, keep: bool, src: dict[str, Any]) -> list[Any]:
    return [r for r in src[field] if (r["batch_id"] not in affected) == keep]


for field in ("batches", "records", "review_unit_records", "schema_anchors"):
    check(f"acceptance.{field}: the 13 untouched batches' rows, in order, byte-identical",
          rows(field, True, ga) == rows(field, True, pa))
gb = {b["batch_id"]: b for b in rows("batches", False, ga)}
pb = {b["batch_id"]: b for b in rows("batches", False, pa)}
check("affected batches: same ids and resolved scopes; rule SIMULATED",
      gb.keys() == pb.keys() == affected
      and all(gb[k]["resolved_scope"] == pb[k]["resolved_scope"] for k in affected)
      and all(pb[k]["rule"] == c.SIMULATED_RULE for k in affected))
sim = rows("records", False, pa)
check("affected acceptance records: SIMULATED reviewer and time only",
      bool(sim) and all(r["reviewer"] == c.SIMULATED_REVIEWER
                        and r["accepted_at"] == c.SIMULATED_AT for r in sim))
report["anchor_order"] = {"g1": [a["batch_id"] for a in ga["schema_anchors"]],
                          "preview": [a["batch_id"] for a in pa["schema_anchors"]]}
check("acceptance.lifts: G1 lifts kept, 18->19 appended",
      pa["lifts"][: len(ga["lifts"])] == ga["lifts"]
      and [x["lift_id"] for x in pa["lifts"][len(ga["lifts"]):]] == ["5d-lift-schema-18-to-19"])
check("reference_resolutions and their records byte-identical",
      G["reference_resolutions"] == P["reference_resolutions"]
      and ga["reference_resolution_records"] == pa["reference_resolution_records"])
for k in ("release_binding", "semantic_policy_hash", "semantic_policy_version",
          "artifact_kind", "spans"):
    check(f"{k}: byte-identical", G[k] == P[k])
units = {r["unit_id"] for r in rows("review_unit_records", False, ga)}
check("review units outside the eleven batches byte-identical",
      [u for u in G["review_units"] if u["unit_id"] not in units]
      == [u for u in P["review_units"] if u["unit_id"] not in units])

# The representation changed by exactly the proposal delta (old = replayed,
# new = the rendered preview proposals, identity-checked against the build).
proposals_dir = c.NATIVE / "preview" / "proposals"
built = json.loads((c.NATIVE / "reports" / "proposals.json").read_text("utf-8"))["batches"]
old_el: dict[str, collections.Counter[Any]] = collections.defaultdict(collections.Counter)
new_el: dict[str, collections.Counter[Any]] = collections.defaultdict(collections.Counter)
identities_ok = True
for batch in c.AFFECTED:
    new = load_proposal(proposals_dir / f"{batch}-PROPOSAL.json")
    identities_ok &= proposal_identity(new) == built[batch]["proposal_identity"]
    for tag, prop, acc in (("old", c.replayed(batch), old_el), ("new", new, new_el)):
        rep = prop.proposed_representation
        for field in ("records", "components", "prose_bindings", "relationships",
                      "references", "provenance"):
            acc[field].update(getattr(rep, field))
check("rendered preview proposals re-identify to the built identities", identities_ok)
gr, pr = g1.oracle.representation, preview.oracle.representation
delta = {}
for field in ("records", "components", "prose_bindings", "relationships", "references",
              "provenance"):
    before, after = set(getattr(gr, field)), set(getattr(pr, field))
    removed, gained = before - after, after - before
    want_removed = set(old_el[field]) - set(new_el[field])
    want_gained = set(new_el[field]) - set(old_el[field])
    delta[field] = {"removed": len(removed), "added": len(gained)}
    check(f"representation.{field}: changed by exactly the replayed->new proposal delta",
          removed == want_removed and gained == want_gained)
report["representation_delta"] = delta
check("pinned inputs unchanged after", pins())
report["checks"] = [{"check": n, "ok": ok} for n, ok in checks]
(c.NATIVE / "reports" / "verify-preview.json").write_text(
    json.dumps(report, indent=1, sort_keys=True) + "\n", "utf-8")
print(json.dumps({k: v for k, v in report.items() if k not in ("checks", "anchor_order")},
                 indent=1))
raise SystemExit(0 if all(ok for _, ok in checks) else 1)
