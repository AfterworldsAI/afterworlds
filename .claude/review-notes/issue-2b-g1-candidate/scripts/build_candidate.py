"""Build the CRD Issue 2b G1 successor candidate.

REVIEW MATERIAL. The accepted Equipment batch is excised from the accepted
oracle (``excise.py``, after the identity control) and the G1 Equipment
proposal is accepted natively in its place under clearly SIMULATED evidence.
Nothing is written under ``oracles/``; the accepted oracle is read only and
its SHA-256 is checked before and after.

Writes ``candidate/`` (the candidate artifact and the rendered proposal) and
``reports/candidate-build.json``.
"""

import json
import sys

sys.path.insert(0, ".claude/review-notes/issue-2b-g1-candidate/scripts")
from common import (  # noqa: E402
    BATCH,
    HERE,
    PRIOR_PATH,
    PRIOR_SHA256,
    build_proposal,
    class_eligibility_edited,
    g1_generator,
    generator,
    sha,
)
from excise import excise  # noqa: E402

from afterworlds.ingestion.mechanical.acceptance import accept_proposal  # noqa: E402
from afterworlds.ingestion.mechanical.authoring import render  # noqa: E402
from afterworlds.ingestion.mechanical.oracle import (  # noqa: E402
    candidate_from_accepted_inputs,
    load_accepted_inputs,
    oracle_identity,
    serialize_accepted_inputs,
)
from afterworlds.ingestion.mechanical.projection import (  # noqa: E402
    identify_projection,
)
from afterworlds.ingestion.mechanical.proposal import proposal_identity  # noqa: E402

SIMULATED_REVIEWER = "SIMULATION - not an Owner approval"
SIMULATED_RULE = (
    "SIMULATION ONLY - CRD Issue 2b G1 candidate; not an Owner acceptance or "
    "authorization"
)
SIMULATED_AT = "2026-10-10T00:00:00Z"
CANDIDATE = HERE / "candidate/srd-5-2-1-corpus-8781d4e0-a3b-g1-candidate.json"
PROPOSAL = HERE / "candidate/issue-2b-g1-equipment-PROPOSAL.json"


def main() -> None:
    raw = PRIOR_PATH.read_bytes()
    assert sha(raw) == PRIOR_SHA256, "accepted oracle changed"
    prior = load_accepted_inputs(PRIOR_PATH)
    (batch,) = [b for b in prior.batches if b.batch_id == BATCH]

    recorded = build_proposal(class_eligibility_edited(generator().batch())).proposal
    assert proposal_identity(recorded) == batch.proposal_identity, "gate 1 failed"
    excised, report = excise(prior, BATCH, recorded.proposed_representation)

    g1 = build_proposal(class_eligibility_edited(g1_generator().batch())).proposal
    candidate = accept_proposal(
        g1,
        batch_id=BATCH,
        rule=SIMULATED_RULE,
        resolved_scope=tuple(p.span.span_id for p in g1.proposed_spans),
        resolved_review_units=tuple(u.unit_id for u in g1.proposed_review_units),
        reviewer=SIMULATED_REVIEWER,
        accepted_at=SIMULATED_AT,
        prior=excised,
    )
    data = serialize_accepted_inputs(candidate)
    CANDIDATE.parent.mkdir(exist_ok=True)
    CANDIDATE.write_bytes(data)
    PROPOSAL.write_bytes(render(g1).encode("utf-8"))
    back = load_accepted_inputs(CANDIDATE)
    assert serialize_accepted_inputs(back) == data, "round trip is not byte-equal"
    assert sha(PRIOR_PATH.read_bytes()) == PRIOR_SHA256, "accepted oracle changed"

    o = candidate.oracle
    out = {
        "candidate": CANDIDATE.relative_to(HERE).as_posix(),
        "candidate_sha256": sha(data),
        "candidate_bytes": len(data),
        "proposal": PROPOSAL.relative_to(HERE).as_posix(),
        "proposal_sha256": sha(PROPOSAL.read_bytes()),
        "g1_proposal_identity": proposal_identity(g1),
        "replaced_proposal_identity": batch.proposal_identity,
        "prior_oracle_identity": oracle_identity(prior.oracle),
        "candidate_oracle_identity": oracle_identity(o),
        "prior_projection_id": identify_projection(
            candidate_from_accepted_inputs(prior)
        ).projection_uuid,
        "candidate_projection_id": identify_projection(
            candidate_from_accepted_inputs(candidate)
        ).projection_uuid,
        "schema": [o.schema_version, o.schema_hash],
        "lifts": [x.lift_id for x in candidate.lifts],
        "excision": report,
        "counts": {
            "batches": len(candidate.batches),
            "records": len(o.representation.records),
            "components": len(o.representation.components),
            "spans": len(o.spans),
            "review_units": len(o.review_units),
            "reference_resolutions": len(o.reference_resolutions),
            "references": len(o.representation.references),
        },
        "prior_sha256_after": sha(PRIOR_PATH.read_bytes()),
    }
    (HERE / "reports").mkdir(exist_ok=True)
    (HERE / "reports/candidate-build.json").write_text(
        json.dumps(out, indent=1) + "\n", encoding="utf-8"
    )
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
