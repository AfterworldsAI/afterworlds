import pathlib,json,hashlib,collections,subprocess,sys,datetime
R=pathlib.Path.cwd();O=R/'.claude/review-notes/issue-15c-implementation/c8-native-review/recording';N=R/'.claude/review-notes/issue-15c-c8-recording';W=R/'.claude/worktrees/agent-aa5b1ea6bf4ee4f39';VN=W/'.claude/review-notes/issue-15c-c8-native';BN=R/'.claude/review-notes/issue-15c-c8-native';OBS=R/'.claude/review-notes/issue-15c-preparation/c8-recording-exit-observer';pins={}
sha=lambda b:hashlib.sha256(b).hexdigest()
canon=lambda x:json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()
def raw(p,pin=None):
 b=p.read_bytes();h=sha(b);assert not pin or h==pin,(p,h,pin);pins[str(p)]=h;return b
def read(p,pin=None):return json.loads(raw(p,pin))
def unique(xs,k):
 out={k(x):x for x in xs};assert len(out)==len(xs);return out
follow=read(N/'recorded-followup.json','c43748bd9366cc5f1a99bc26b54d2ff4c61721f5d163f38d56b3eb6acb752338');recbytes=raw(R/follow['successor'],'ead7fa9d4fde484098f71221ca5ef82dfb2c82229d8fca80ab5feeb4e4d62d0d');rec=json.loads(recbytes);prev=read(VN/'preview/srd-5-2-1-corpus-8781d4e0-a3b-c8-PREVIEW.json','a2d96264dd18605680358393270e1f9f4fc27da144fda09da06e31cbd5250016')
receipt=read(N/'owner-acceptance.json');assert receipt['owner']=='Ravenlok (Owner)' and receipt['exact_user_message']=='Accept exact C8' and receipt['species_input_message']=='Approve bounded species input'
receipttext=raw(R/receipt['receipt'],receipt['receipt_sha256']).decode('utf8');assert 'call_e440e8a1d917462d92745745f84e671b' in receipttext
for path,field in [(receipt['decision_packet'],'decision_packet_sha256'),(receipt['owner_packet'],'owner_packet_sha256'),('.claude/review-notes/issue-15c-c8-native/PLANNING-ADDENDUM-target-domain.md','planning_addendum_sha256'),('.claude/review-notes/issue-15c-implementation/codex-c8-native-final-review.md','independent_final_review_sha256'),('.claude/review-notes/issue-15c-c8-native/reports/c8-revalidation.json','corrected_revalidation_report_sha256')]:raw(R/path,receipt[field])
raw(R/'.claude/review-notes/issue-15c-implementation/owner-whole-pr-review-2026-10-13.md')
raw(N/'record_successor.py','5a319a198f5f869da4967f4abb7743f69dd90bd8b800f3ce743fc3791f6454d4')
original=read(R/'.claude/review-notes/issue-15c-implementation/c8-native-review/original-c8-preview.json')
for path,h in original['pins'].items():raw(pathlib.Path(path) if pathlib.Path(path).is_absolute() else R/path,h)
for batch,(path,h) in original['accepted_inputs_located'].items():raw(R/path,h)
OR=R/'src/afterworlds/ingestion/mechanical/oracles';predecessors={'srd-5-2-1-corpus-8781d4e0-a3b-15c.json':'23e5d8e0fac60e3f5417b3a41e40e6f475366dd385856f38c42104f4dd264f69','srd-5-2-1-corpus-8781d4e0-a3b-15c-c7.json':'2853f30a832ca581c9d4169b82d0c360f3d6a2d78f0ad8980de9997eef51f373','srd-5-2-1-corpus-8781d4e0-a3b-g1.json':'2ccbaeba6de75d9787fbdd407e42dc2425fa20d4d26bcc298b681b550bd11258','srd-5-2-1-corpus-8781d4e0-a3b.json':'def7caa1625458a40c1f635db153268082cf52d5e25c28f57fd29518e44de58c'}
for f,h in predecessors.items():raw(OR/f,h)
T=set(follow['proposal_identities']);assert T==set(original['touched_batches'])
assert rec.keys()==prev.keys();assert all(rec[k]==prev[k] for k in rec if k!='acceptance'); assert b'SIMULATION' not in recbytes
assert rec['acceptance'].keys()==prev['acceptance'].keys();evidence={};untouched={}
at=follow['recorded_at'];assert at=='2026-10-13T17:50:52Z' and at>receipt['receipt_recorded_at_utc']
expectedrule=(f"Owner exact acceptance, Ravenlok (Owner): 'Accept exact C8' CRD Issue 15c C8 successor (includes disclosed interpretations I1 and I2). Decision packet {receipt['decision_packet']} sha256 {receipt['decision_packet_sha256']}; receipt {receipt['receipt']} sha256 {receipt['receipt_sha256']}; Owner packet sha256 {receipt['owner_packet_sha256']}; independent final review sha256 {receipt['independent_final_review_sha256']}; corrected revalidation sha256 {receipt['corrected_revalidation_report_sha256']}; reviewed preview sha256 {receipt['reviewed_preview_sha256']}; schema {receipt['schema'][0]} {receipt['schema'][1]}; oracle identity {receipt['oracle_identity']}; projection {receipt['projection']}; recorded {at}")
for col in rec['acceptance']:
 if col not in ['batches','records','review_unit_records']:
  assert rec['acceptance'][col]==prev['acceptance'][col];continue
 idkey='batch_id' if col=='batches' else 'span_id' if col=='records' else 'unit_id'
 a=unique(prev['acceptance'][col],lambda x:(x['batch_id'],x[idkey]));b=unique(rec['acceptance'][col],lambda x:(x['batch_id'],x[idkey]));assert a.keys()==b.keys();delta=collections.Counter()
 for k,x in a.items():
  y=b[k];assert x.keys()==y.keys();changed={f for f in x if x[f]!=y[f]}
  if x['batch_id'] in T:
   assert changed==({'rule'} if col=='batches' else {'reviewer','accepted_at'}),(col,k,changed)
   if col=='batches':assert y['rule']==expectedrule
   else:assert y['reviewer']==receipt['owner'] and y['accepted_at']==at
  else:assert not changed
  delta.update(changed)
 untouched[col]=len([x for x in a.values() if x['batch_id'] not in T]);assert [x for x in prev['acceptance'][col] if x['batch_id'] not in T]==[x for x in rec['acceptance'][col] if x['batch_id'] not in T]
 evidence[col]=dict(delta)
assert evidence=={'batches':{'rule':5},'records':{'accepted_at':7536,'reviewer':7536},'review_unit_records':{'accepted_at':1154,'reviewer':1154}}
anchors=unique(rec['acceptance']['schema_anchors'],lambda x:x['batch_id']);assert len(anchors)==24
for batch,identity in follow['proposal_identities'].items():
 p=read(VN/'preview'/f'{batch}-C8-PROPOSAL.json',original['batches'][batch]['rendered_proposal_sha256']);assert sha(canon(p))==identity==anchors[batch]['proposal_identity']==original['batches'][batch]['proposal_identity']
assert rec['representation_schema']=={'version':receipt['schema'][0],'hash':receipt['schema'][1]}
ob=read(OBS/'result.json');launch=read(OBS/'launch.json');assert ob['actual_python_exit']==0;assert launch['python_pid']==30320 and launch['record_script_sha256']==pins[str(N/'record_successor.py')];assert raw(OBS/'exit.txt')==b'0'
assert ob['recorded_report_sha256']==pins[str(N/'recorded-followup.json')];assert raw(N/'record.err.txt',ob['stderr_sha256'])==b''
stdout=raw(N/'record.out.txt',ob['stdout_sha256']).decode('utf8');assert stdout.rstrip().endswith('successor sha256 '+follow['successor_sha256'])
raw(R/'.claude/review-notes/issue-15c-preparation/watch-c8-recording-exit.ps1')
nat=follow['native'];assert nat['validate_candidate_finding_count']==0 and nat['validate_candidate_findings']==[] and nat['verify_reconstruction']==[] and nat['reconstructed_payload_identical'] and nat['gate_passed'] and nat['gate_failures']==[]
# Pure native identity under the exact reviewed preview code, not mutable selection/gameplay code.
assert subprocess.check_output(['git','-C',str(W),'rev-parse','HEAD'],text=True).strip()=='bf3fb2d17279114b0981da13ee76fd9f1ddc88bc'
for f in ['oracle.py','projection.py','representation.py','validation.py','schema_lift.py']:
 rel='src/afterworlds/ingestion/mechanical/'+f;b=raw(W/rel);assert b==subprocess.check_output(['git','show','bf3fb2d17279114b0981da13ee76fd9f1ddc88bc:'+rel])
sys.dont_write_bytecode=True;sys.path.insert(0,str(W/'src'))
import afterworlds
assert pathlib.Path(afterworlds.__file__).resolve().is_relative_to((W/'src').resolve())
from afterworlds.ingestion.mechanical.oracle import load_accepted_inputs,serialize_accepted_inputs,oracle_identity,candidate_from_accepted_inputs
from afterworlds.ingestion.mechanical.projection import identify_projection
native=load_accepted_inputs(R/follow['successor']);assert serialize_accepted_inputs(native)==recbytes
ident=identify_projection(candidate_from_accepted_inputs(native));assert oracle_identity(native.oracle)==follow['oracle_identity']==receipt['oracle_identity'];assert str(ident.projection_uuid)==follow['projection']==receipt['projection']==nat['reidentified_projection'];assert ident.payload_hash==follow['payload_hash']==receipt['projection_payload_hash']
for p,h in pins.items():assert sha(pathlib.Path(p).read_bytes())==h,('changed input',p)
out={'reviewed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'recording_slice_clear','recorded_sha256':follow['successor_sha256'],'recorded_bytes':len(recbytes),'recorded_at':at,'outside_acceptance_identical':True,'acceptance_other_collections_identical':True,'changed_evidence':evidence,'untouched_ordered_rows':untouched,'unchanged_schema_anchors':24,'real_owner_receipts_exact':True,'simulation_residue':False,'proposal_identities':follow['proposal_identities'],'pure_native':{'afterworlds_file':afterworlds.__file__,'code_revision':'bf3fb2d17279114b0981da13ee76fd9f1ddc88bc','serialization_identical':True,'oracle_identity':oracle_identity(native.oracle),'projection':str(ident.projection_uuid),'payload_hash':ident.payload_hash},'observer':ob,'predecessor_pins':predecessors,'input_sha256':pins,'limitations':['Native private-store/gate result inspected and reused, not rerun','Current main selection/packaging changes not yet reviewed at a coherent final commit','Whole PR implementation and required full/CI gates remain separate']}
(O/'results.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8');print(json.dumps({k:v for k,v in out.items() if k!='input_sha256'},indent=2))
