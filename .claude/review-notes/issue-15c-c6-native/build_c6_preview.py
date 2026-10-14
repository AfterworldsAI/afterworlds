"""CRD Issue 15c — native SIMULATED preview of raw candidate C6-r2.

REVIEW MATERIAL ONLY: not an Owner acceptance, recording, publication or
activation. Run from the repository root with the clone's venv.

Construction (the reviewed C5 method, one batch):

* prior: the recorded native C5 successor ``srd-5-2-1-corpus-8781d4e0-a3b-15c.json``
  (``23e5d8e0…``), whose real receipts are preserved;
* the ``character-origins-feats`` batch's accepted proposal (the exact C5
  packet proposal, identity-matched to the successor's anchor) gains the four
  C6-r2 ``feat_prerequisite`` facts on their prose-bound ``category``
  components (handling ``mixed``; prose kept), a provenance claim per fact on
  the bound span holding its quote, and an ExpectedRule per review unit;
* the batch is excised claim-based (``issue-15c-native/scripts/excise.py``) and
  the new proposal accepted natively with SIMULATED evidence.

Proofs, each asserted and written to ``reports/c6-preview.json``:

* pins: successor, C6-r2, C6, the accepted proposal file and the source;
* the new proposal adds exactly the four C6-r2 payloads at their addresses and
  changes nothing else of the proposal;
* the 23 other batches' ordered acceptance/review-unit/anchor/batch rows,
  every resolution, span and the binding/policy are byte-identical to the
  successor; the representation changed by exactly the proposal delta;
* native ``validate_candidate`` has no findings; persist -> reconstruct ->
  re-identify; the read-only gate passes against the preview oracle and
  refuses the successor's projection against it (and vice versa), in private
  copies of the isolated release store;
* two runs are byte-identical (``--twice``).
"""

from __future__ import annotations

import collections
import dataclasses
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

REPO = Path.cwd()
NOTES = REPO / ".claude/review-notes"
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(NOTES / "issue-15c-native/scripts"))

import common as c  # noqa: E402
from excise import excise  # noqa: E402

from afterworlds.ingestion.mechanical.acceptance import accept_proposal  # noqa: E402
from afterworlds.ingestion.mechanical.authoring import render  # noqa: E402
from afterworlds.ingestion.mechanical.bound_corpus import load_bound_corpus  # noqa: E402
from afterworlds.ingestion.mechanical.gate import run_publication_gate  # noqa: E402
from afterworlds.ingestion.mechanical.models import ExpectedRule  # noqa: E402
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
from afterworlds.ingestion.mechanical.representation import (  # noqa: E402
    ComponentHandling,
    ProvenanceClaim,
    ProvenanceRole,
    ProvenanceTargetKind,
    fact_from_payload,
    fact_key,
    fact_payload,
    fact_target_key,
)
from afterworlds.persistence.database import create_engine, create_session_factory  # noqa: E402
from afterworlds.persistence.orm.base import Base  # noqa: E402

HERE = NOTES / "issue-15c-c6-native"
BATCH = "character-origins-feats"
SUCCESSOR = COMMITTED_ORACLE_DIR / "srd-5-2-1-corpus-8781d4e0-a3b-15c.json"
C6R2 = NOTES / "issue-15c-implementation/candidate-c6-r2/c6r2.json"
C6 = NOTES / "issue-15c-implementation/candidate-c6/c6.json"
PROPOSAL = NOTES / "issue-15c-native/preview/proposals/character-origins-feats-PROPOSAL.json"
FEATS = REPO / "docs/sources/community/dnd-5e-srd-markdown/feats.md"
PINS = {
    SUCCESSOR: "23e5d8e0fac60e3f5417b3a41e40e6f475366dd385856f38c42104f4dd264f69",
    C6R2: "699718ff9bac8298c08fc6da706309819b864b604685c88f462669d68e8923f4",
    C6: "eb014b30e685543c435930913d00fe8762963c95b0fdcc9ce470c019bbfb554a",
    PROPOSAL: "a8928f18d65538d21993e7f94090272bdc7e279c412134ebb8ffc996ada48b89",
    FEATS: "3894f4a147df40adb8b090825b4c2e3e5ee2c67851aca42305b11f2477bcfbf7",
}
ACCEPTED_IDENTITY = "20716b7dcadd5e1216ff3594c5aa654cb41c2961fe49048b0c853c1eed381838"
PREVIEW = HERE / "preview/srd-5-2-1-corpus-8781d4e0-a3b-c6-PREVIEW.json"
RENDERED = HERE / "preview/character-origins-feats-C6-PROPOSAL.json"
ORIGIN = ("CRD Issue 15c C6-r2 native preview (review only): the accepted "
          "character-origins-feats proposal {identity} with the four C6-r2 Origin "
          "feat-category facts on their category components")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def norm(text: str) -> str:
    return " ".join(text.replace("&emsp;", " ").split())


def build(base: AcceptedInputs) -> tuple[MechanicalProposal, dict[str, Any]]:
    p = load_proposal(PROPOSAL)
    assert proposal_identity(p) == ACCEPTED_IDENTITY
    (anchor,) = [a for a in base.schema_anchors if a.batch_id == BATCH]
    assert anchor.proposal_identity == ACCEPTED_IDENTITY, "successor anchor"
    facts = json.loads(C6R2.read_text("utf-8"))["facts"]
    leaves = c.leaf_texts()
    rep = p.proposed_representation
    spans = {x.span.span_id: x.span for x in p.proposed_spans}
    bound: dict[tuple[str, str], list[str]] = collections.defaultdict(list)
    for b in rep.prose_bindings:
        bound[(b.record_key, b.component_key)].append(b.span_id)
    unit_of_leaf = {leaf: u.unit_id for u in p.proposed_review_units for leaf in u.leaf_ids}
    added: dict[tuple[str, str], Any] = {}
    claims, rules = [], collections.defaultdict(list)
    for f in facts:
        key = (f["record_key"], f["component_key"])
        fact = fact_from_payload(f["fact"])
        assert fact_payload(fact) == f["fact"], key
        quote = norm(f["source"]["quote"])
        chosen = sorted(
            s for s in bound[key]
            if quote in norm(leaves[spans[s].leaf_id][spans[s].char_start:spans[s].char_end])
        )
        assert chosen, ("quote on no bound span", key)
        added[key] = fact
        for sid in chosen:
            claims.append(ProvenanceClaim(ProvenanceTargetKind.FACT,
                                          fact_target_key(*key, fact, ""), sid,
                                          ProvenanceRole.CONTEXTUAL))
        per_unit: dict[str, list[str]] = collections.defaultdict(list)
        for sid in chosen:
            per_unit[unit_of_leaf[spans[sid].leaf_id]].append(sid)
        for unit, sids in per_unit.items():
            rules[unit].append(ExpectedRule(record_key=key[0], component_key=key[1],
                                            fact_family=fact.FAMILY.value,
                                            source_span_ids=tuple(sids)))
    components = []
    for comp in rep.components:
        key = (comp.record_key, comp.semantic_key)
        if key in added:
            assert comp.handling is ComponentHandling.PROSE_BOUND and not comp.facts, key
            comp = dataclasses.replace(comp, handling=ComponentHandling.MIXED,
                                       facts=(added[key],))
        components.append(comp)
    assert sum(1 for a, b in zip(rep.components, components, strict=True) if a != b) == 4
    units = tuple(dataclasses.replace(u, expected_rules=(*u.expected_rules,
                                                          *rules.get(u.unit_id, ())))
                  for u in p.proposed_review_units)
    new = dataclasses.replace(
        p,
        proposed_representation=dataclasses.replace(
            rep, components=tuple(components), provenance=(*rep.provenance, *claims)),
        proposed_review_units=units,
        proposal_origin=ORIGIN.format(identity=ACCEPTED_IDENTITY))
    return new, {"facts_added": len(added), "claims_added": len(claims),
                 "expected_rules_added": sum(len(v) for v in rules.values()),
                 "fact_keys": sorted(f"{k[0]}/{k[1]}:{fact_key(v)}" for k, v in added.items())}


def chain(base: AcceptedInputs, proposal: MechanicalProposal) -> AcceptedInputs:
    (old,) = [b for b in base.batches if b.batch_id == BATCH]
    excised, _ = excise(base, {BATCH: load_proposal(PROPOSAL).proposed_representation})
    return accept_proposal(
        proposal, batch_id=BATCH, resolved_scope=old.resolved_scope,
        resolved_review_units=tuple(u.unit_id for u in proposal.proposed_review_units),
        prior=excised, rule=c.SIMULATED_RULE, reviewer=c.SIMULATED_REVIEWER,
        accepted_at=c.SIMULATED_AT)


def native(inputs: AcceptedInputs, other: AcceptedInputs) -> dict[str, Any]:
    out: dict[str, Any] = {}
    with c.private_store() as db:
        engine = create_engine(f"sqlite:///{db}")
        try:
            Base.metadata.create_all(engine)
            with create_session_factory(engine)() as s:
                b = inputs.oracle.binding
                corpus = load_bound_corpus(s, b.package_uuid, b.release_version)
                findings = list(validate_candidate(candidate_from_accepted_inputs(inputs), corpus))
                ids = {}
                for tag, x in (("preview", inputs), ("successor", other)):
                    identified = identify_projection(candidate_from_accepted_inputs(x))
                    persist_draft(s, identified, now=c.SIMULATED_AT)
                    s.commit()
                    rebuilt = reconstruct_candidate(s, identified.projection_uuid)
                    out[f"{tag}_reconstruction_clean"] = (
                        verify_reconstruction(s, identified) == ()
                        and projection_payload(rebuilt) == projection_payload(identified.candidate)
                        and identify_projection(rebuilt).projection_uuid == identified.projection_uuid)
                    record_persisted_state_digest(s, identified.projection_uuid)
                    s.commit()
                    ids[tag] = identified
                own = run_publication_gate(s, ids["preview"].projection_uuid, inputs.oracle)
                cross = run_publication_gate(s, ids["successor"].projection_uuid, inputs.oracle)
                back = run_publication_gate(s, ids["preview"].projection_uuid, other.oracle)
                out.update(
                    validate_candidate_findings=findings[:10],
                    projection=str(ids["preview"].projection_uuid),
                    payload_hash=ids["preview"].payload_hash,
                    own_gate_passed=own.passed and not own.failures,
                    successor_refused_against_preview=not cross.passed,
                    preview_refused_against_successor=not back.passed,
                )
        finally:
            engine.dispose()
    return out


def preserved(base: AcceptedInputs, data: bytes, old_rep: Any, new_rep: Any,
              preview: AcceptedInputs) -> dict[str, bool]:
    G, P = json.loads(serialize_accepted_inputs(base)), json.loads(data)
    keep = lambda rows: [r for r in rows if r["batch_id"] != BATCH]  # noqa: E731
    out = {f"acceptance.{f}": keep(G["acceptance"][f]) == keep(P["acceptance"][f])
           for f in ("batches", "records", "review_unit_records", "schema_anchors")}
    out["lifts"] = G["acceptance"]["lifts"] == P["acceptance"]["lifts"]
    for k in ("reference_resolutions", "spans", "release_binding", "semantic_policy_hash",
              "semantic_policy_version", "artifact_kind", "representation_schema"):
        out[k] = G[k] == P[k]
    out["resolution_records"] = (G["acceptance"]["reference_resolution_records"]
                                 == P["acceptance"]["reference_resolution_records"])
    gr, pr = base.oracle.representation, preview.oracle.representation
    for f in ("records", "components", "prose_bindings", "relationships", "references",
              "provenance"):
        before, after = set(getattr(gr, f)), set(getattr(pr, f))
        old, new = set(getattr(old_rep, f)), set(getattr(new_rep, f))
        out[f"representation.{f}"] = (before - after == old - new) and (after - before == new - old)
    return out


def main() -> None:
    for path, digest in PINS.items():
        assert sha(path.read_bytes()) == digest, path
    base = load_accepted_inputs(SUCCESSOR)
    proposal, delta = build(base)
    preview = chain(base, proposal)
    data = serialize_accepted_inputs(preview)
    if "--twice" in sys.argv:
        assert serialize_accepted_inputs(chain(base, build(base)[0])) == data, "determinism"
    PREVIEW.parent.mkdir(parents=True, exist_ok=True)
    PREVIEW.write_bytes(data)
    rendered = render(proposal).encode("utf-8")
    RENDERED.write_bytes(rendered)
    back = load_accepted_inputs(PREVIEW)
    assert serialize_accepted_inputs(back) == data
    pres = preserved(base, data, load_proposal(PROPOSAL).proposed_representation,
                     proposal.proposed_representation, back)
    nat = native(back, base)
    report = {
        "label": "SIMULATION - review-only native preview; not an Owner acceptance",
        "candidate": {"c6r2_sha256": PINS[C6R2], "c6_sha256_preserved": PINS[C6]},
        "prior_successor_sha256": PINS[SUCCESSOR],
        "accepted_proposal_identity": ACCEPTED_IDENTITY,
        "proposal_identity": proposal_identity(proposal),
        "rendered_proposal_sha256": sha(rendered),
        "delta": delta,
        "preview_sha256": sha(data),
        "oracle_identity": oracle_identity(back.oracle),
        "schema": [back.oracle.schema_version, back.oracle.schema_hash],
        "preservation": pres,
        "native": nat,
        "deterministic_twice": "--twice" in sys.argv,
        "pins_after": all(sha(p.read_bytes()) == d for p, d in PINS.items()),
    }
    (HERE / "reports").mkdir(exist_ok=True)
    (HERE / "reports/c6-preview.json").write_text(
        json.dumps(report, indent=1, sort_keys=True) + "\n", "utf-8", newline="\n")
    print(json.dumps({k: v for k, v in report.items() if k != "preservation"}, indent=1))
    assert all(pres.values()), pres
    assert not nat["validate_candidate_findings"]
    assert nat["own_gate_passed"] and nat["successor_refused_against_preview"]
    assert nat["preview_refused_against_successor"]
    assert nat["preview_reconstruction_clean"] and nat["successor_reconstruction_clean"]
    assert report["pins_after"] and delta["facts_added"] == 4


if __name__ == "__main__":
    main()
