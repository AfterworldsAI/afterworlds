"""Capture the live oracle's native action chain from its existing replay.

Read-only for repository state. Wraps ``accept_proposal`` and
``resolve_references`` (pass-through, results unchanged) before the reviewed
scripts load, runs the final-ten recording's own historical replay
(``prior()`` then ``recorded(.., OWNER, RECORDED_AT)``), asserts the result is
the live oracle byte for byte, then backtracks from it through each call's
prior to None. Writes the ordered calls (inputs only, no AcceptedInputs) to
OUT as a pickle plus a JSON summary.
"""

import hashlib
import importlib.util
import json
import pickle
import sys
from pathlib import Path

REPO = Path.cwd()
sys.path.insert(0, str(REPO / "src"))
from afterworlds.ingestion.mechanical import acceptance  # noqa: E402
from afterworlds.ingestion.mechanical.oracle import (  # noqa: E402
    COMMITTED_ORACLE_DIR,
    serialize_accepted_inputs,
)
from afterworlds.ingestion.mechanical.proposal import proposal_identity  # noqa: E402

LIVE = COMMITTED_ORACLE_DIR / "srd-5-2-1-corpus-3fe24ff6-4e3.json"
LIVE_SHA = "e6f5f36aa3af13807bbff721797d971dcf0d8e588a97483c7d769cf88cbd1308"
OUT = Path(sys.argv[1])
assert not OUT.exists()
assert hashlib.sha256(LIVE.read_bytes()).hexdigest() == LIVE_SHA

calls: list[dict] = []
_real = {n: getattr(acceptance, n) for n in ("accept_proposal", "resolve_references")}


def _wrap(name):
    real = _real[name]

    def wrapper(*args, **kwargs):
        result = real(*args, **kwargs)
        prior = kwargs.get("prior") if name == "accept_proposal" else (
            args[0] if args else kwargs["prior"]
        )
        calls.append({"fn": name, "args": args, "kwargs": kwargs, "prior": prior, "result": result})
        return result

    return wrapper


for n in _real:
    setattr(acceptance, n, _wrap(n))

path = REPO / ".claude/review-notes/issue-5d-final-ten-references-ACCEPT.py"
spec = importlib.util.spec_from_file_location("final_ten_accept", path)
FT = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = FT
spec.loader.exec_module(FT)
out = FT.recorded(FT.prior(), FT.OWNER, FT.RECORDED_AT)
assert serialize_accepted_inputs(out) == LIVE.read_bytes(), "replay is not the live oracle"
print("replay == live oracle bytes; wrapped calls", len(calls))

by_result = {id(c["result"]): c for c in calls}
chain, cur = [], out
while cur is not None:
    c = by_result[id(cur)]
    chain.append(c)
    cur = c["prior"]
chain.reverse()
steps, summary = [], []
for c in chain:
    kw = {k: v for k, v in c["kwargs"].items() if k != "prior"}
    if c["fn"] == "accept_proposal":
        (proposal,) = c["args"]
        steps.append(("accept_proposal", proposal, kw))
        summary.append({"fn": "accept_proposal", "batch_id": kw["batch_id"],
                        "proposal_identity": proposal_identity(proposal),
                        "schema_version": proposal.schema_version,
                        "scope": len(kw["resolved_scope"]),
                        "review_units": len(kw.get("resolved_review_units", ())),
                        "reviewer": kw["reviewer"], "accepted_at": kw["accepted_at"]})
    else:
        steps.append(("resolve_references", None, kw))
        summary.append({"fn": "resolve_references", "resolutions": len(kw["resolutions"]),
                        "lift_to": kw.get("lift_to"), "reviewer": kw["reviewer"],
                        "resolved_at": kw["resolved_at"]})
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_bytes(pickle.dumps(steps))
OUT.with_suffix(".json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
print("chain steps", len(steps), "accept", sum(s[0] == "accept_proposal" for s in steps),
      "resolve", sum(s[0] == "resolve_references" for s in steps))
print("pickle sha256", hashlib.sha256(OUT.read_bytes()).hexdigest())
