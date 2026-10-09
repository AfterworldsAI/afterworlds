"""Close the raw-tuple comparison limit with exact native canonical payloads."""
import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0,str(ROOT / "src"))
from sqlalchemy import event
from afterworlds.ingestion.mechanical.accounting import acceptance_evidence_payload
from afterworlds.ingestion.mechanical.oracle import candidate_from_accepted_inputs, load_accepted_inputs
from afterworlds.ingestion.mechanical.persistence import persist_draft, reconstruct_candidate, verify_reconstruction
from afterworlds.ingestion.mechanical.projection import identify_projection, projection_payload
from afterworlds.persistence.database import create_engine, create_session_factory
from afterworlds.persistence.orm.base import Base

report = {}
for tag,rel,path in [("old","rel-old",HERE / "pre-edit/accepted-oracle.json"),("new","rel-new",HERE / "candidate/srd-5-2-1-corpus-8781d4e0-a3b.json")]:
    source = HERE / rel / "afterworlds.db"
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    inputs = load_accepted_inputs(path)
    expected = identify_projection(candidate_from_accepted_inputs(inputs))
    with tempfile.TemporaryDirectory(prefix="codex-canonical-",dir=HERE) as name:
        work = Path(name).resolve()
        assert work.is_relative_to(HERE)
        db = work / "proof.db"
        shutil.copyfile(source,db)
        engine = create_engine(f"sqlite:///{db}")
        @event.listens_for(engine,"connect")
        def fk(connection,record):
            connection.execute("PRAGMA foreign_keys=ON")
        try:
            Base.metadata.create_all(engine)
            with create_session_factory(engine)() as session:
                persist_draft(session,expected,now="2026-10-06T00:00:00Z")
                session.commit()
                findings = verify_reconstruction(session,expected)
                rebuilt = reconstruct_candidate(session,expected.projection_uuid)
                actual = identify_projection(rebuilt)
                checks = {
                    "native_verification_zero_findings":findings == (),
                    "six_field_binding_exact":rebuilt.binding == inputs.oracle.binding,
                    "complete_native_projection_payload_exact":projection_payload(rebuilt) == projection_payload(expected.candidate),
                    "complete_native_acceptance_evidence_exact":acceptance_evidence_payload(rebuilt.classification) == acceptance_evidence_payload(expected.candidate.classification),
                    "projection_uuid_exact":actual.projection_uuid == expected.projection_uuid,
                    "payload_hash_exact":actual.payload_hash == expected.payload_hash,
                }
        finally:
            engine.dispose()
    checks["source_store_bytes_unchanged"] = hashlib.sha256(source.read_bytes()).hexdigest() == source_hash
    report[tag] = {"input_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),"source_store_sha256":source_hash,"projection_uuid":expected.projection_uuid,"payload_hash":expected.payload_hash,"checks":checks,"findings":list(findings)}
    print(tag,json.dumps(report[tag]),flush=True)
report["scope"] = "Draft persistence into disposable copies only; exact native canonical projection and acceptance evidence; no publication, activation or shared-store writes. Does not repeat reader tests."
(HERE / "codex-canonical-reconstruction.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
raise SystemExit(0 if all(all(report[k]["checks"].values()) for k in ["old","new"]) else 1)
