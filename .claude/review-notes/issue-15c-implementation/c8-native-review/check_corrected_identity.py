import pathlib,sys,json,hashlib,subprocess
R=pathlib.Path.cwd();W=(R/'.claude/worktrees/agent-aa5b1ea6bf4ee4f39').resolve();O=R/'.claude/review-notes/issue-15c-implementation/c8-native-review';N=W/'.claude/review-notes/issue-15c-c8-native'
sys.dont_write_bytecode=True;sys.path.insert(0,str(W/'src'))
sha=lambda b:hashlib.sha256(b).hexdigest()
rev='bf3fb2d17279114b0981da13ee76fd9f1ddc88bc';assert subprocess.check_output(['git','-C',str(W),'rev-parse','HEAD'],text=True).strip()==rev
pins={}
for f in ['oracle.py','projection.py','representation.py','validation.py','schema_lift.py']:
 rel='src/afterworlds/ingestion/mechanical/'+f;b=(W/rel).read_bytes();gitb=subprocess.check_output(['git','show',rev+':'+rel]);assert b==gitb;pins[rel]=sha(b)
for f in ['OWNER-PACKET.md','PLANNING-ADDENDUM-target-domain.md','revalidate_c8_preview.py']:
 b=(N/f).read_bytes();pins[str((N/f).relative_to(W))]=sha(b);(O/('corrected-'+f)).write_bytes(b)
preview=N/'preview/srd-5-2-1-corpus-8781d4e0-a3b-c8-PREVIEW.json';data=preview.read_bytes();assert sha(data)=='a2d96264dd18605680358393270e1f9f4fc27da144fda09da06e31cbd5250016'
import afterworlds
assert pathlib.Path(afterworlds.__file__).resolve().is_relative_to(W/'src')
from afterworlds.ingestion.mechanical.oracle import load_accepted_inputs,serialize_accepted_inputs,oracle_identity,candidate_from_accepted_inputs
from afterworlds.ingestion.mechanical.projection import identify_projection
from afterworlds.ingestion.mechanical.representation import representation_schema_hash
inputs=load_accepted_inputs(preview);assert serialize_accepted_inputs(inputs)==data
identified=identify_projection(candidate_from_accepted_inputs(inputs))
result={'preview_code_revision':rev,'afterworlds_file':afterworlds.__file__,'preview_sha256':sha(data),'serialization_byte_identical':True,'oracle_identity':oracle_identity(inputs.oracle),'projection':str(identified.projection_uuid),'payload_hash':identified.payload_hash,'schema_hash':representation_schema_hash(),'reviewed_file_sha256':pins}
expected=json.loads((O/'original-c8-preview.json').read_bytes());assert result['oracle_identity']==expected['oracle_identity'];assert result['projection']==expected['native']['projection'];assert result['payload_hash']==expected['native']['payload_hash'];assert result['schema_hash']==expected['schema'][1]
for rel,h in pins.items():assert sha((W/rel).read_bytes())==h
assert preview.read_bytes()==data
(O/'corrected-identity.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8');print(json.dumps(result,indent=2))
