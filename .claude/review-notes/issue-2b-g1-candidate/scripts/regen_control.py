"""Gate 1: the recorded generator plus the accepted class-eligibility edit,
built natively against the isolated release, reproduces the accepted
Equipment batch's recorded proposal identity."""

import json
import sys

sys.path.insert(0, ".claude/review-notes/issue-2b-g1-candidate/scripts")
from common import (  # noqa: E402
    BATCH,
    PRIOR_PATH,
    PRIOR_SHA256,
    build_proposal,
    class_eligibility_edited,
    generator,
    sha,
)

from afterworlds.ingestion.mechanical.proposal import proposal_identity  # noqa: E402

assert sha(PRIOR_PATH.read_bytes()) == PRIOR_SHA256
prior = json.loads(PRIOR_PATH.read_text("utf-8"))
(recorded,) = [
    b["proposal_identity"]
    for b in prior["acceptance"]["batches"]
    if b["batch_id"] == BATCH
]
built = build_proposal(class_eligibility_edited(generator().batch()))
got = proposal_identity(built.proposal)
print("recorded", recorded)
print("rebuilt ", got)
print("MATCH" if got == recorded else "MISMATCH")
raise SystemExit(0 if got == recorded else 1)
