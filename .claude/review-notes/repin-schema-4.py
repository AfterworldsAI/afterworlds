"""Re-pin every derived schema-4 value after a type-surface change.

Development helper for PR A, not production code. The representation schema hash
moves every time an addition lands, and several sites state it literally: the
schema-lift registry's destination pin, the bounded test-oracle fixture, and
three canaries whose whole job is to notice the move. Re-pinning them by hand
after each addition is how one of them silently keeps a stale value.

Two things this deliberately never touches:

* **The committed production oracle.** It declares schema 3 and must keep
  declaring it. Carrying it forward is ``verify_lift``'s job, and re-stamping its
  declaration is exactly what the lift exists to refuse.
* **``schema_lift.SCHEMA_3_HASH``.** That is the lift's *source* pin — it names
  the contract the committed artifact was accepted under. The first version of
  this helper did a blanket replace of the previous hash and rewrote the source
  pin, silently re-authorizing a transition nobody reviewed. The destination pin
  is now rewritten by its own name, and the source pin is asserted unmoved.

Usage: ``python repin-schema-4.py [previous-hash]``
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from afterworlds.ingestion.mechanical.representation import (  # noqa: E402
    REPRESENTATION_SCHEMA_VERSION,
    representation_schema_hash,
)

#: The contract the committed conditions-1 artifact was accepted under. Constant
#: for all time; asserted rather than rewritten.
SCHEMA_3_HASH = "43ed330d3b3630d37ed92122fd87cc2c170863bab4465e53c727f1b8c6b86e05"  # noqa: E501  # pragma: allowlist secret

VERSION = REPRESENTATION_SCHEMA_VERSION
HASH = representation_schema_hash()
assert VERSION == "5d-representation-schema-4", VERSION
assert HASH != SCHEMA_3_HASH, "schema 4 must not hash to schema 3's contract"

PRODUCTION_ORACLE = REPO / "src/afterworlds/ingestion/mechanical/oracles"
LIFT = REPO / "src/afterworlds/ingestion/mechanical/schema_lift.py"

#: Literal pins that follow the current contract. Each is a canary, updated
#: deliberately here rather than edited by hand.
PINS = (
    REPO / "tests/ingestion/mechanical/test_representation_schema_identity.py",
    REPO / "tests/ingestion/mechanical/test_review_round_7_draft_exact_types.py",
    REPO
    / "tests/services/rules_authority/test_review_round_5_component_patch_schema2.py",
)
assert not any(
    p.is_relative_to(PRODUCTION_ORACLE) for p in (*PINS, LIFT)
), "the committed production oracle is never re-pinned"

previous = sys.argv[1] if len(sys.argv) > 1 else None
changed: list[str] = []

# 1. The bounded test fixture. Schema-3 content that is also valid schema-4
#    content, so only its declaration and its own anchors move.
fixture = REPO / "tests/ingestion/mechanical/data/bounded_oracle.json"
payload = json.loads(fixture.read_text(encoding="utf-8"))
payload["representation_schema"] = {"version": VERSION, "hash": HASH}
# Its schema anchors move with its declaration, and that is honest for exactly
# this file: it is a synthetic bounded fixture whose batches have no review
# history outside the build that generates them, so "reviewed under what this
# file declares" is true of it. A *committed* artifact may never be re-anchored
# this way — that is the restamp ``succession_evidence_violations`` refuses, and
# the reason this helper has never been allowed near the production oracle.
payload["acceptance"]["schema_anchors"] = [
    {
        "batch_id": batch["batch_id"],
        "proposal_identity": batch["proposal_identity"],
        "schema_version": VERSION,
        "schema_hash": HASH,
    }
    for batch in payload["acceptance"]["batches"]
]
fixture.write_text(
    json.dumps(payload, indent=1, sort_keys=True, ensure_ascii=False) + "\n",
    encoding="utf-8",
    newline="\n",
)
changed.append(fixture.name)

# 2. The literal canaries.
for path in PINS:
    text = path.read_text(encoding="utf-8")
    if previous and previous in text:
        path.write_text(text.replace(previous, HASH), encoding="utf-8", newline="\n")
        changed.append(path.name)

# 3. The lift's destination pin only, rewritten by name.
text = LIFT.read_text(encoding="utf-8")
# The trailing ``# pragma: allowlist secret`` is preserved: it is part of the
# line's meaning to the secret scanner, and a rewrite that dropped it would
# reintroduce a gate failure every time the pin moved.
text = re.sub(
    r'SCHEMA_4_HASH = "[0-9a-f]{64}"',
    f'SCHEMA_4_HASH = "{HASH}"',
    text,
)
assert (
    f'SCHEMA_3_HASH = "{SCHEMA_3_HASH}"' in text
), "the lift's source pin moved; it names the contract the artifact was accepted under"
LIFT.write_text(text, encoding="utf-8", newline="\n")
changed.append(f"{LIFT.name} (destination pin only)")

print(f"version {VERSION}")
print(f"hash    {HASH}")
print(f"repinned {changed}")
if not previous:
    print("note: pass the previous hash as argv[1] to rewrite the literal canaries")
