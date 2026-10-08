"""Native persisted reconstruction of the recorded oracle on a disposable store.

Adapted from issue-5c-release-order-codex-evidence/codex_canonical_reconstruction.py
(sha 72a1a1e8): recorded file only, store = isolated rel-new, fresh report path.
"""

import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "src"))
from sqlalchemy import event  # noqa: E402

from afterworlds.ingestion.mechanical.accounting import (  # noqa: E402
    acceptance_evidence_payload,
)
from afterworlds.ingestion.mechanical.oracle import (  # noqa: E402
    candidate_from_accepted_inputs,
    load_accepted_inputs,
)
from afterworlds.ingestion.mechanical.persistence import (  # noqa: E402
    persist_draft,
    reconstruct_candidate,
    verify_reconstruction,
)
from afterworlds.ingestion.mechanical.projection import (  # noqa: E402
    identify_projection,
    projection_payload,
)
from afterworlds.persistence.database import (  # noqa: E402
    create_engine,
    create_session_factory,
)
from afterworlds.persistence.orm.base import Base  # noqa: E402

RECORDED = ROOT / "src/afterworlds/ingestion/mechanical/oracles"
RECORDED /= "srd-5-2-1-corpus-8781d4e0-a3b.json"
SOURCE = ROOT / ".claude/_sp/release-order-candidate/rel-new/afterworlds.db"
OUT = HERE / "reports/recorded-canonical-reconstruction.json"
assert not OUT.exists()

source_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
inputs = load_accepted_inputs(RECORDED)
expected = identify_projection(candidate_from_accepted_inputs(inputs))
with tempfile.TemporaryDirectory(prefix="release-order-recorded-") as name:
    db = Path(name) / "proof.db"
    shutil.copyfile(SOURCE, db)
    engine = create_engine(f"sqlite:///{db}")

    @event.listens_for(engine, "connect")
    def fk(connection, record):  # type: ignore[no-untyped-def]
        connection.execute("PRAGMA foreign_keys=ON")

    try:
        Base.metadata.create_all(engine)
        with create_session_factory(engine)() as session:
            persist_draft(session, expected, now="2026-10-07T05:39:49Z")
            session.commit()
            findings = verify_reconstruction(session, expected)
            rebuilt = reconstruct_candidate(session, expected.projection_uuid)
            actual = identify_projection(rebuilt)
            checks = {
                "native_verification_zero_findings": findings == (),
                "six_field_binding_exact": rebuilt.binding == inputs.oracle.binding,
                "complete_native_projection_payload_exact": projection_payload(rebuilt)
                == projection_payload(expected.candidate),
                "complete_native_acceptance_evidence_exact": (
                    acceptance_evidence_payload(rebuilt.classification)
                    == acceptance_evidence_payload(expected.candidate.classification)
                ),
                "projection_uuid_exact": actual.projection_uuid
                == expected.projection_uuid,
                "payload_hash_exact": actual.payload_hash == expected.payload_hash,
            }
    finally:
        engine.dispose()
checks["source_store_bytes_unchanged"] = (
    hashlib.sha256(SOURCE.read_bytes()).hexdigest() == source_hash
)
report = {
    "input_sha256": hashlib.sha256(RECORDED.read_bytes()).hexdigest(),
    "source_store_sha256": source_hash,
    "projection_uuid": expected.projection_uuid,
    "payload_hash": expected.payload_hash,
    "checks": checks,
    "findings": list(findings),
    "scope": "Draft persistence into a disposable copy only; no publication, "
    "activation or shared-store write.",
}
print(json.dumps(report, indent=1), flush=True)
OUT.parent.mkdir(exist_ok=True)
OUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
raise SystemExit(0 if all(checks.values()) else 1)
