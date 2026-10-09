"""Independent full native validation and persistence of the recorded input."""
import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
DEST=ROOT/'.claude/review-notes/issue-5c-release-order-recording'
sys.path.insert(0,str(ROOT/'src'))
from afterworlds.ingestion.mechanical.accounting import acceptance_evidence_payload
from afterworlds.ingestion.mechanical.bound_corpus import load_bound_corpus, published_release_binding
from afterworlds.ingestion.mechanical.oracle import candidate_from_accepted_inputs, load_accepted_inputs
from afterworlds.ingestion.mechanical.persistence import persist_draft, reconstruct_candidate, verify_reconstruction
from afterworlds.ingestion.mechanical.projection import identify_projection, projection_payload, validate_candidate
from afterworlds.persistence.database import create_engine, create_session_factory
from afterworlds.persistence.orm.base import Base

path=ROOT/'src/afterworlds/ingestion/mechanical/oracles/srd-5-2-1-corpus-8781d4e0-a3b.json'
source=ROOT/'.claude/_sp/release-order-candidate/rel-new/afterworlds.db'
source_sha=hashlib.sha256(source.read_bytes()).hexdigest()
inputs=load_accepted_inputs(path)
expected=identify_projection(candidate_from_accepted_inputs(inputs))
accepted_proof=json.loads((ROOT/'.claude/review-notes/issue-5c-release-order-codex-evidence/codex-canonical-reconstruction.json').read_text())['new']
with tempfile.TemporaryDirectory(prefix='codex-recording-',dir=HERE) as name:
    work=Path(name).resolve()
    assert work.is_relative_to(HERE)
    db=work/'proof.db'
    shutil.copyfile(source,db)
    engine=create_engine(f'sqlite:///{db}')
    try:
        Base.metadata.create_all(engine)
        with create_session_factory(engine)() as session:
            binding=published_release_binding(session)
            corpus=load_bound_corpus(session,binding.package_uuid,binding.release_version)
            native_findings=validate_candidate(expected.candidate,corpus)
            assert not native_findings, native_findings[:10]
            assert binding==inputs.oracle.binding
            assert session.connection().exec_driver_sql('PRAGMA foreign_keys').scalar()==1
            persist_draft(session,expected,now=inputs.reference_resolution_acceptances[0].resolved_at)
            session.commit()
            findings=verify_reconstruction(session,expected)
            rebuilt=reconstruct_candidate(session,expected.projection_uuid)
            actual=identify_projection(rebuilt)
            checks={
                'native_validation_zero_findings':not native_findings,
                'native_reconstruction_zero_findings':findings==(),
                'six_field_binding_exact':rebuilt.binding==inputs.oracle.binding,
                'complete_native_projection_payload_exact':projection_payload(rebuilt)==projection_payload(expected.candidate),
                'complete_native_acceptance_evidence_exact':acceptance_evidence_payload(rebuilt.classification)==acceptance_evidence_payload(expected.candidate.classification),
                'projection_uuid_exact':actual.projection_uuid==expected.projection_uuid,
                'payload_hash_exact':actual.payload_hash==expected.payload_hash,
                'semantic_projection_uuid_same_as_accepted_candidate':expected.projection_uuid==accepted_proof['projection_uuid'],
                'semantic_payload_hash_same_as_accepted_candidate':expected.payload_hash==accepted_proof['payload_hash'],
            }
    finally:
        engine.dispose()
checks['source_store_bytes_unchanged']=hashlib.sha256(source.read_bytes()).hexdigest()==source_sha
report={'input_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'source_store_sha256':source_sha,'projection_uuid':expected.projection_uuid,'payload_hash':expected.payload_hash,'checks':checks,'native_findings':list(native_findings),'reconstruction_findings':list(findings),'scope':'Draft persistence into disposable source-store copy only; no publication, activation or shared-store writes.'}
(DEST/'codex-native-persistence.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,indent=2))
raise SystemExit(0 if all(checks.values()) else 1)
