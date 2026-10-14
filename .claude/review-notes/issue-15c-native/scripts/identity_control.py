"""Identity control: excising each affected group from the accepted G1 inputs
and re-accepting its unchanged, identity-matched proposal natively (re-declared
at the prior's schema, because native acceptance has no reverse lift)
reproduces the accepted oracle identity and every oracle payload key.

Each batch is replaced singly, the others present, in accepted-anchor order.
Writes ../reports/identity-control.json. Read-only over every input.
"""

from __future__ import annotations

import dataclasses
import json

import common as c
from excise import excise

from afterworlds.ingestion.mechanical.acceptance import accept_proposal
from afterworlds.ingestion.mechanical.oracle import (
    AcceptedInputs,
    load_accepted_inputs,
    oracle_identity,
    oracle_payload,
)
from afterworlds.ingestion.mechanical.proposal import MechanicalProposal

GROUPS: tuple[tuple[str, ...], ...] = (
    ("combat-damage-breaking",), ("checks-actions-rests",), ("core-play-completion",),
    ("character-origins-feats",), ("spellcasting",), ("classes",), ("spell-descriptions",),
    ("magic-items",), ("monsters",), ("animals",), ("equipment",),
)
assert sorted(b for g in GROUPS for b in g) == sorted(c.AFFECTED)


def reaccept(prior: AcceptedInputs, base: AcceptedInputs,
             proposals: dict[str, MechanicalProposal]) -> AcceptedInputs:
    """Re-accept each group proposal over *prior* with *base*'s recorded
    evidence, in *base*'s anchor order."""
    order = [a.batch_id for a in base.schema_anchors if a.batch_id in proposals]
    state = prior
    for batch_id in order:
        (batch,) = [b for b in base.batches if b.batch_id == batch_id]
        (who,) = {a.reviewer for a in base.acceptances if a.batch_id == batch_id}
        (when,) = {a.accepted_at for a in base.acceptances if a.batch_id == batch_id}
        units = tuple(a.unit_id for a in base.review_unit_acceptances
                      if a.batch_id == batch_id)
        state = accept_proposal(
            proposals[batch_id], batch_id=batch_id, rule=batch.rule,
            resolved_scope=batch.resolved_scope, resolved_review_units=units,
            reviewer=who, accepted_at=when, prior=state)
    return state


def main() -> None:
    c.pinned(c.G1_PATH, c.G1_SHA256)
    base = load_accepted_inputs(c.G1_PATH)
    pair = (base.oracle.schema_version, base.oracle.schema_hash)
    want = oracle_identity(base.oracle)
    rows = []
    for group in GROUPS:
        replayed = {b: c.replayed(b) for b in group}
        excised, report = excise(base, {b: p.proposed_representation
                                        for b, p in replayed.items()})
        redeclared = {b: dataclasses.replace(p, schema_version=pair[0], schema_hash=pair[1])
                      for b, p in replayed.items()}
        again = reaccept(excised, base, redeclared)
        a, b = oracle_payload(again.oracle), oracle_payload(base.oracle)
        diff = sorted(k for k in a.keys() | b.keys() if a.get(k) != b.get(k))
        same = oracle_identity(again.oracle) == want
        rows.append({"group": list(group), "excision": report,
                     "oracle_identity_equal": same, "payload_keys_differing": diff})
        print(group, same, diff)
    out = c.NATIVE / "reports" / "identity-control.json"
    out.write_text(json.dumps({"g1_sha256": c.G1_SHA256, "oracle_identity": want,
                               "groups": rows}, indent=1) + "\n", "utf-8")
    assert all(r["oracle_identity_equal"] and not r["payload_keys_differing"] for r in rows)


if __name__ == "__main__":
    main()
