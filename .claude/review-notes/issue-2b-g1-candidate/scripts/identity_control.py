"""Gate 2: excising the accepted Equipment batch and re-accepting the
identity-matched regenerated proposal natively (re-declared at the prior's
schema 17, because native acceptance has no reverse lift) reproduces every
semantic collection of the accepted oracle byte for byte."""

import dataclasses
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
    generator,
    sha,
)
from excise import excise  # noqa: E402

from afterworlds.ingestion.mechanical.acceptance import accept_proposal  # noqa: E402
from afterworlds.ingestion.mechanical.oracle import (  # noqa: E402
    load_accepted_inputs,
    oracle_identity,
    oracle_payload,
    serialize_accepted_inputs,
)
from afterworlds.ingestion.mechanical.proposal import proposal_identity  # noqa: E402
from afterworlds.ingestion.mechanical.schema_lift import (  # noqa: E402
    SCHEMA_17_HASH,
    SCHEMA_17_VERSION,
)

raw = PRIOR_PATH.read_bytes()
assert sha(raw) == PRIOR_SHA256
prior = load_accepted_inputs(PRIOR_PATH)
old = class_eligibility_edited(generator().batch())
built16 = build_proposal(old)
(batch,) = [b for b in prior.batches if b.batch_id == BATCH]
assert proposal_identity(built16.proposal) == batch.proposal_identity
excised, report = excise(prior, BATCH, built16.proposal.proposed_representation)
print("excision", json.dumps(report))

built17 = build_proposal(
    dataclasses.replace(old, schema=(SCHEMA_17_VERSION, SCHEMA_17_HASH))
)
p = built17.proposal
(who,) = {a.reviewer for a in prior.acceptances if a.batch_id == BATCH}
(when,) = {a.accepted_at for a in prior.acceptances if a.batch_id == BATCH}
assert tuple(sorted(batch.resolved_scope)) == tuple(
    sorted(x.span.span_id for x in p.proposed_spans)
)
units = tuple(
    a.unit_id for a in prior.review_unit_acceptances if a.batch_id == BATCH
)
again = accept_proposal(
    p,
    batch_id=BATCH,
    rule=batch.rule,
    resolved_scope=batch.resolved_scope,
    resolved_review_units=units,
    reviewer=who,
    accepted_at=when,
    prior=excised,
)
same_identity = oracle_identity(again.oracle) == oracle_identity(prior.oracle)
a, b = oracle_payload(again.oracle), oracle_payload(prior.oracle)
diff_keys = sorted(k for k in a.keys() | b.keys() if a.get(k) != b.get(k))
print("oracle_identity equal:", same_identity)
print("oracle payload keys differing:", diff_keys)
out = serialize_accepted_inputs(again)
new = json.loads(out)
old_doc = json.loads(raw)
top = sorted(k for k in new if new[k] != old_doc[k])
print("serialized top-level keys differing:", top)
for k in ("acceptance",):
    if new[k] != old_doc[k]:
        print(" acceptance subkeys differing:",
              sorted(s for s in new[k] if new[k][s] != old_doc[k][s]))
eq_anchor = [x for x in new["acceptance"]["schema_anchors"] if x["batch_id"] == BATCH]
print(" equipment anchor now:", eq_anchor)
print(" anchor order (old/new last):",
      old_doc["acceptance"]["schema_anchors"][-1]["batch_id"],
      new["acceptance"]["schema_anchors"][-1]["batch_id"])
print("schema-17 proposal identity:", proposal_identity(p))
(HERE / "reports").mkdir(exist_ok=True)
(HERE / "reports/identity-control.json").write_text(json.dumps({
    "prior_sha256": PRIOR_SHA256,
    "recorded_equipment_proposal_identity": batch.proposal_identity,
    "regenerated_schema16_identity": proposal_identity(built16.proposal),
    "redeclared_schema17_identity": proposal_identity(p),
    "excision": report,
    "oracle_identity_equal": same_identity,
    "oracle_payload_keys_differing": diff_keys,
    "serialized_top_level_keys_differing": top,
}, indent=1), encoding="utf-8")
raise SystemExit(0 if same_identity and not diff_keys else 1)
