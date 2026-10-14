"""Native review-only preview: G1 with the eleven affected batches replaced.

Chain (each step validated by native ``accept_proposal`` over the merged
result, every other batch present):

    for each affected batch, in G1's accepted-anchor order:
        excise it (claim-based, ``excise.py``) from the current state, then
        accept its replacement proposal with SIMULATED evidence.

The first acceptance records the registered 18 -> 19 lift. The resolved
scope and review units are the accepted batch's own.

Sequential control (Codex closure note): the same chain over the *unchanged*
replayed proposals, re-declared at the prior's schema, must reproduce G1's
oracle identity and every oracle payload key -- the sequential path, not only
each singleton, is reversible.

Writes ``../preview/srd-5-2-1-corpus-8781d4e0-a3b-15c-PREVIEW.json`` (never
in the committed oracle directory) and ``../reports/candidate-build.json``.
"""

from __future__ import annotations

import dataclasses
import json
from collections.abc import Callable

import build_proposals
import common as c
from excise import excise

from afterworlds.ingestion.mechanical.acceptance import accept_proposal
from afterworlds.ingestion.mechanical.oracle import (
    AcceptedInputs,
    candidate_from_accepted_inputs,
    load_accepted_inputs,
    oracle_identity,
    oracle_payload,
    serialize_accepted_inputs,
)
from afterworlds.ingestion.mechanical.projection import identify_projection
from afterworlds.ingestion.mechanical.proposal import MechanicalProposal, proposal_identity

PREVIEW = c.NATIVE / "preview" / "srd-5-2-1-corpus-8781d4e0-a3b-15c-PREVIEW.json"


def order(base: AcceptedInputs) -> list[str]:
    return [a.batch_id for a in base.schema_anchors if a.batch_id in c.AFFECTED]


def chain(base: AcceptedInputs, proposals: dict[str, MechanicalProposal],
          evidence: Callable[[str], dict[str, object]]) -> tuple[AcceptedInputs, dict[str, object]]:
    state, steps = base, {}
    for batch in order(base):
        (old,) = [b for b in state.batches if b.batch_id == batch]
        excised, report = excise(state, {batch: c.replayed(batch).proposed_representation})
        p = proposals[batch]
        state = accept_proposal(
            p, batch_id=batch, resolved_scope=old.resolved_scope,
            resolved_review_units=tuple(u.unit_id for u in p.proposed_review_units),
            prior=excised, **evidence(batch))  # type: ignore[arg-type]
        steps[batch] = {"excision": report, "proposal_identity": proposal_identity(p)}
    return state, steps


def recorded(base: AcceptedInputs) -> Callable[[str], dict[str, object]]:
    def ev(batch: str) -> dict[str, object]:
        (b,) = [x for x in base.batches if x.batch_id == batch]
        (who,) = {a.reviewer for a in base.acceptances if a.batch_id == batch}
        (when,) = {a.accepted_at for a in base.acceptances if a.batch_id == batch}
        return {"rule": b.rule, "reviewer": who, "accepted_at": when}
    return ev


def simulated(_: str) -> dict[str, object]:
    return {"rule": c.SIMULATED_RULE, "reviewer": c.SIMULATED_REVIEWER,
            "accepted_at": c.SIMULATED_AT}


def main() -> None:
    c.pinned(c.G1_PATH, c.G1_SHA256)
    base = load_accepted_inputs(c.G1_PATH)
    pair = (base.oracle.schema_version, base.oracle.schema_hash)

    # Sequential control: unchanged proposals, recorded evidence.
    unchanged = {b: dataclasses.replace(c.replayed(b), schema_version=pair[0],
                                        schema_hash=pair[1]) for b in c.AFFECTED}
    control, _ = chain(base, unchanged, recorded(base))
    a, b = oracle_payload(control.oracle), oracle_payload(base.oracle)
    control_report = {
        "oracle_identity_equal": oracle_identity(control.oracle) == oracle_identity(base.oracle),
        "payload_keys_differing": sorted(k for k in a.keys() | b.keys() if a.get(k) != b.get(k)),
    }
    print("sequential control", control_report)
    assert control_report["oracle_identity_equal"] and not control_report["payload_keys_differing"]

    proposals, proposal_report = build_proposals.build()
    preview, steps = chain(base, proposals, simulated)
    data = serialize_accepted_inputs(preview)
    PREVIEW.parent.mkdir(parents=True, exist_ok=True)
    PREVIEW.write_bytes(data)
    back = load_accepted_inputs(PREVIEW)
    round_trip = serialize_accepted_inputs(back) == data
    assert round_trip
    identified = identify_projection(candidate_from_accepted_inputs(back))
    report = {
        "label": "SIMULATION - review-only native preview; not an Owner acceptance",
        "preview_path": str(PREVIEW.relative_to(c.REPO)).replace("\\", "/"),
        "preview_sha256": c.hashlib.sha256(data).hexdigest(),
        "oracle_identity": oracle_identity(back.oracle),
        "projection_uuid": str(identified.projection_uuid),
        "payload_hash": identified.payload_hash,
        "schema": [back.oracle.schema_version, back.oracle.schema_hash],
        "lifts": [lf.lift_id for lf in back.lifts],
        "round_trip_bytes_equal": round_trip,
        "sequential_control": control_report,
        "steps": steps,
        "g1_oracle_identity": oracle_identity(base.oracle),
    }
    (c.NATIVE / "reports" / "candidate-build.json").write_text(
        json.dumps(report, indent=1, sort_keys=True) + "\n", "utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "steps"}, indent=1))


if __name__ == "__main__":
    main()
