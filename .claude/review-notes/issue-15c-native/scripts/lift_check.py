"""18 -> 19 lift proof over the whole accepted G1 representation.

``verify_lift`` serializes every accepted collection under both contracts and
requires canonical byte equality, element by element. Also asserts the build's
schema-19 hash equals the registered destination pin, and that the G1
predecessor and prior oracle bytes are unchanged. Writes ../reports/lift.json.
"""

from __future__ import annotations

import json

import common as c

from afterworlds.ingestion.mechanical.oracle import load_accepted_inputs
from afterworlds.ingestion.mechanical.representation import (
    REPRESENTATION_SCHEMA_VERSION,
    representation_schema_hash,
)
from afterworlds.ingestion.mechanical.schema_lift import (
    SCHEMA_18_HASH,
    SCHEMA_18_VERSION,
    SCHEMA_19_HASH,
    SCHEMA_19_VERSION,
    lift_for,
    verify_lift,
)


def main() -> None:
    c.pinned(c.G1_PATH, c.G1_SHA256)
    c.pinned(c.PREDECESSOR_PATH, c.PREDECESSOR_SHA256)
    build = (REPRESENTATION_SCHEMA_VERSION, representation_schema_hash())
    assert build == (SCHEMA_19_VERSION, SCHEMA_19_HASH), (build, SCHEMA_19_HASH)
    g1 = load_accepted_inputs(c.G1_PATH)
    assert (g1.oracle.schema_version, g1.oracle.schema_hash) == (SCHEMA_18_VERSION,
                                                                 SCHEMA_18_HASH)
    lift = lift_for((SCHEMA_18_VERSION, SCHEMA_18_HASH), build)
    record = verify_lift(lift, g1.oracle.representation)
    report = {"lift_id": lift.lift_id, "from": [lift.from_version, lift.from_hash],
              "to": [lift.to_version, lift.to_hash],
              "verified_collections": list(record.verified_collections),
              "g1_sha256": c.G1_SHA256, "predecessor_sha256": c.PREDECESSOR_SHA256}
    (c.NATIVE / "reports" / "lift.json").write_text(json.dumps(report, indent=1) + "\n", "utf-8")
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
