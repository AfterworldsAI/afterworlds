"""Independent stdlib JSON inspection; no application imports, stores, builder, tests."""
import collections, copy, hashlib, json, pathlib, subprocess
R=pathlib.Path.cwd(); W=R/'.claude/worktrees/agent-aa5b1ea6bf4ee4f39'; O=R/'.claude/review-notes/issue-15c-implementation/c8-native-review'
N=pathlib.Path('.claude/review-notes/issue-15c-c8-native'); I=pathlib.Path('.claude/review-notes/issue-15c-implementation/candidate-c8')
sha=lambda b:hashlib.sha256(b).hexdigest()
canon=lambda x:json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()
counter=lambda xs:collections.Counter(canon(x) for x in xs)
key=lambda c:(c['record_key'],c['semantic_key'])
keyraw=lambda c:(c['record_key'],c['component_key'])
inputs={}
def read(p,pin=None):
 b=p.read_bytes(); h=sha(b); inputs[str(p.relative_to(R)) if p.is_relative_to(R) else str(p)]=h
 if pin:assert h==pin,(p,h,pin)
 return json.loads(b)
def unique(xs,k):
 d={k(x):x for x in xs};assert len(d)==len(xs);return d
report=read(O/'original-c8-preview.json')
P=read(W/N/'preview/srd-5-2-1-corpus-8781d4e0-a3b-c8-PREVIEW.json',report['preview_sha256'])
G=read(R/'src/afterworlds/ingestion/mechanical/oracles/srd-5-2-1-corpus-8781d4e0-a3b-15c-c7.json','2853f30a832ca581c9d4169b82d0c360f3d6a2d78f0ad8980de9997eef51f373')
for rel,pin in report['pins'].items():
 p=pathlib.Path(rel) if pathlib.Path(rel).is_absolute() else R/rel
 b=p.read_bytes();assert sha(b)==pin,(p,sha(b));inputs[str(p)]=sha(b)
raw=read(R/I/'c8.json'); corr=unique(read(R/I/'correspondence.json'),keyraw)
facts=unique(raw['facts']+raw['source_type_choices'],keyraw);assert len(facts)==len(corr)==346
GC=unique(G['representation']['components'],key); PC=unique(P['representation']['components'],key);assert GC.keys()==PC.keys()
changed={k for k in GC if GC[k]!=PC[k]};assert changed==facts.keys()
handling=[]
for k,f in facts.items():
 a,b=GC[k],PC[k];assert b['facts']==a['facts']+[f['fact']],k
 restore=dict(b,facts=a['facts'],handling=a['handling']);assert restore==a,k
 if a['handling']!=b['handling']:
  assert a['handling']=='prose_bound' and b['handling']=='mixed' and not a['facts'] and not a['options'];handling.append('/'.join(k))
 else:assert a['handling']=='mixed'
assert len(handling)==10
for family in ['records','prose_bindings','relationships','references']:
 assert G['representation'][family]==P['representation'][family],family
GP=counter(G['representation']['provenance']); PP=counter(P['representation']['provenance']);assert not GP-PP
added_claims=[json.loads(x) for x,n in (PP-GP).items() for _ in range(n)]; assert len(added_claims)==346
claims=unique(added_claims,lambda c:tuple(c['target_key'][:2]))
spans=unique(P['spans'],lambda s:s['span_id'])
bound=collections.defaultdict(set); prior_claimed=collections.defaultdict(set)
for x in G['representation']['prose_bindings']:bound[(x['record_key'],x['component_key'])].add(x['span_id'])
for x in G['representation']['provenance']:
 if x['target_kind']=='fact':prior_claimed[tuple(x['target_key'][:2])].add(x['span_id'])
span_batch={x['span_id']:x['batch_id'] for x in G['acceptance']['records']}
units=unique(P['review_units'],lambda u:u['unit_id']); gunits=unique(G['review_units'],lambda u:u['unit_id']);assert units.keys()==gunits.keys()
added_rules=[]
for uid,a in gunits.items():
 b=units[uid];assert {k:v for k,v in a.items() if k!='expected_rules'}=={k:v for k,v in b.items() if k!='expected_rules'}
 ac,bc=counter(a['expected_rules']),counter(b['expected_rules']);assert not ac-bc
 added_rules.extend((uid,json.loads(x)) for x,n in (bc-ac).items() for _ in range(n))
assert len(added_rules)==346
rule_by_key=unique(added_rules,lambda pair:keyraw(pair[1]))
for k,f in facts.items():
 c=corr[k];s=f['source'];assert (c['file'],c['line'],c['quote'])==(s['file'],s['line'],s['quote'])
 assert s['quote'] in (R/'docs/sources/community/dnd-5e-srd-markdown'/s['file']).read_text(encoding='utf8').splitlines()[s['line']-1]
 assert {span_batch[x] for x in prior_claimed[k] or bound[k]}=={c['batch']}
 assert set(c['claim_spans'])==(prior_claimed[k] or bound[k]),k
 claim=claims[k]; sid=claim['span_id'];assert sid in bound[k] and sid in c['claim_spans']
 assert claim=={'role':'contextual','span_id':sid,'target_kind':'fact','target_key':[*k,sha(canon(f['fact']))[:16]]}
 assert report['batches'][c['batch']]['claimed_span']['/'.join(k)]==sid
 uid,rule=rule_by_key[k];assert rule=={'record_key':k[0],'component_key':k[1],'fact_family':f['fact']['family'],'source_span_ids':[sid]}
 assert spans[sid]['leaf_id'] in units[uid]['leaf_ids']
# Exact obligation addition only, including unchanged retained-prose component sets.
go=unique(G['obligations'],lambda o:o['record_key']);po=unique(P['obligations'],lambda o:o['record_key']);assert go.keys()==po.keys()
byrecord=collections.defaultdict(set)
for k,f in facts.items():byrecord[k[0]].add(f['fact']['family'])
for k,a in go.items():
 b=copy.deepcopy(a);b['structured_fact_families']=sorted(set(a['structured_fact_families'])|byrecord[k]);assert b==po[k],k
T=set(report['touched_batches']); unchanged_counts={}
for name in ['batches','records','review_unit_records','schema_anchors']:
 a=[x for x in G['acceptance'][name] if x['batch_id'] not in T];b=[x for x in P['acceptance'][name] if x['batch_id'] not in T]
 assert a==b,name;unchanged_counts[name]=len(a)
ga=[x['batch_id'] for x in G['acceptance']['schema_anchors']];pa=[x['batch_id'] for x in P['acceptance']['schema_anchors']]
assert pa==[b for b in ga if b not in T]+[b for b in ga if b in T]
assert len(pa)==len(set(pa))==24
for k in G.keys()-{'acceptance','representation','representation_schema','obligations','review_units'}:assert G[k]==P[k],k
assert P['acceptance']['lifts'][:-1]==G['acceptance']['lifts'];assert P['acceptance']['lifts'][-1]['lift_id']=='5d-lift-schema-20-to-21'
assert P['acceptance']['reference_resolution_records']==G['acceptance']['reference_resolution_records']
# All proposal bytes/identities; exact proposal delta and equality with snapshot additions.
proposal_results={}; anchor=unique(P['acceptance']['schema_anchors'],lambda x:x['batch_id']);oldanchors=unique(G['acceptance']['schema_anchors'],lambda x:x['batch_id'])
for batch,meta in report['batches'].items():
 oldpath,oldpin=report['accepted_inputs_located'][batch];a=read(R/oldpath,oldpin);b=read(W/N/'preview'/f'{batch}-C8-PROPOSAL.json',meta['rendered_proposal_sha256'])
 assert sha(canon(a))==meta['accepted_proposal_identity']==oldanchors[batch]['proposal_identity']
 assert sha(canon(b))==meta['proposal_identity']==anchor[batch]['proposal_identity']
 assert b['representation_schema']==P['representation_schema']=={'version':report['schema'][0],'hash':report['schema'][1]}
 assert {k:v for k,v in a.items() if k not in ['proposal_origin','representation_schema','proposed_representation','proposed_review_units']}=={k:v for k,v in b.items() if k not in ['proposal_origin','representation_schema','proposed_representation','proposed_review_units']}
 ac=unique(a['proposed_representation']['components'],key);bc=unique(b['proposed_representation']['components'],key);assert ac.keys()==bc.keys()
 modified={k for k in ac if ac[k]!=bc[k]};assert modified=={k for k in facts if corr[k]['batch']==batch}
 for k in modified:assert ac[k]==GC[k] and bc[k]==PC[k]
 for k in ac.keys()-modified:assert ac[k]==bc[k]
 for col in ['records','prose_bindings','relationships','references']:assert a['proposed_representation'][col]==b['proposed_representation'][col]
 x,y=counter(a['proposed_representation']['provenance']),counter(b['proposed_representation']['provenance']);assert not x-y
 assert y-x==counter([claims[k] for k in modified])
 au=unique(a['proposed_review_units'],lambda u:u['unit_id']);bu=unique(b['proposed_review_units'],lambda u:u['unit_id']);assert au.keys()==bu.keys()
 for uid in au:assert au[uid]==gunits[uid] and bu[uid]==units[uid]
 proposal_results[batch]={'rendered_sha256':meta['rendered_proposal_sha256'],'proposal_identity':meta['proposal_identity'],'added_facts':len(modified)}
# Exact replacement receipts preserve scopes/diffs/membership; only documented evidence changes.
receipt_deltas={}
allowed={'batches':{'rule','proposal_identity'},'records':{'accepted_at','reviewer'},'review_unit_records':{'accepted_at','reviewer'},'schema_anchors':{'schema_hash','schema_version','proposal_identity'}}
for col,allowed_fields in allowed.items():
 idkey='batch_id' if col in ['batches','schema_anchors'] else 'span_id' if col=='records' else 'unit_id'
 a=unique([x for x in G['acceptance'][col] if x['batch_id'] in T],lambda x:x[idkey]);b=unique([x for x in P['acceptance'][col] if x['batch_id'] in T],lambda x:x[idkey]);assert a.keys()==b.keys()
 deltas=collections.Counter()
 for k in a:
  fields={f for f in a[k].keys()|b[k].keys() if a[k].get(f)!=b[k].get(f)};assert fields==allowed_fields,(col,k,fields)
  deltas.update(fields)
  if col in ['records','review_unit_records']:assert b[k]['reviewer']=='SIMULATION - not an Owner approval' and b[k]['accepted_at']=='2026-10-12T00:00:00Z'
 receipt_deltas[col]={'rows':len(a),'fields_changed':dict(deltas)}
# Original tracked proof bytes have independent commit provenance and agree with report pins.
blob_pins={}
for rel in ['build_c8_preview.py','reports/c8-preview.json','reports/c8-build.log.out','reports/c8-build.log.err','README.md','OWNER-PACKET.md']:
 b=subprocess.check_output(['git','show','277a2357ec3df1805b81f2158722b16f9bcd1b2d:'+str(N/rel).replace('\\','/')]);blob_pins[rel]=sha(b)
assert blob_pins['build_c8_preview.py']==report['builder_sha256']
for name in ['common.py','excise.py']:
 b=subprocess.check_output(['git','show','277a2357ec3df1805b81f2158722b16f9bcd1b2d:.claude/review-notes/issue-15c-native/scripts/'+name]);blob_pins[name]=sha(b);assert sha(b)==report['scripts_sha256'][name]
# Actual 11 form components directly supply unqualified size and fixed Beast authority.
familiar=PC[('spells.find_familiar','effect')]['facts'][-1]; forms=[]
for f in familiar['forms']:
 k=keyraw(f); c=PC[k];size=[x for x in c['facts'] if x['family']=='creature_size'];typ=[x for x in c['facts'] if x['family']=='creature_type']
 assert len(size)==len(typ)==1 and typ[0]['type']=='beast' and typ[0]['type_choice']==[]
 assert c['applies_when'] is None and c['options']==[] and c['fact_qualifiers']==[]
 forms.append('/'.join(k))
# Re-check observed byte inputs at end; no application imports or artifact generation.
for p,h in inputs.items():assert sha(pathlib.Path(p).read_bytes())==h,('changed while reviewing',p)
result={'status':'passed','tracked_original_blob_sha256':blob_pins,'touched_receipt_deltas':receipt_deltas,'artifact_commit':'277a2357ec3df1805b81f2158722b16f9bcd1b2d','original_code':'056d3d4fdf0617a0b4539778bbcdf7fbdcb637a8','input_sha256':inputs,'snapshot_sha256':report['preview_sha256'],'component_count':len(PC),'changed_components':len(changed),'unchanged_mixed_profile_fields':336,'handling_changes':sorted(handling),'claims_added':len(added_claims),'rules_added':len(added_rules),'obligation_records_changed':sum(go[k]!=po[k] for k in go),'ordered_untouched_rows':unchanged_counts,'original_anchor_order':ga,'preview_anchor_order':pa,'proposals':proposal_results,'direct_unqualified_familiar_forms':forms,'limits':['Source interpretation/census reused from RAW review; leaf quote substring proof not rerun against store','No native validation, persistence, full replay, builder or tests executed','Corrected-code revalidation and packet correction remain coordinator-owned']}
(O/'results.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
print(json.dumps({k:v for k,v in result.items() if k!='input_sha256'},indent=2))
