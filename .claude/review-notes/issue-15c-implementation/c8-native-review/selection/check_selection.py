import pathlib,subprocess,hashlib,json,ast,tomllib,fnmatch,datetime
R=pathlib.Path.cwd();O=R/'.claude/review-notes/issue-15c-implementation/c8-native-review/selection';V='183a664e8645ecadd97c55517e8ba1120e9c5b19';P=V+'^';pins={}
sha=lambda b:hashlib.sha256(b).hexdigest()
def blob(path,rev=V):
 b=subprocess.check_output(['git','show',rev+':'+path]);pins[rev+':'+path]=sha(b);return b
def consts(b):
 out={}
 for n in ast.parse(b).body:
  if isinstance(n,(ast.Assign,ast.AnnAssign)):
   name=n.targets[0].id if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) else n.target.id if isinstance(n,ast.AnnAssign) and isinstance(n.target,ast.Name) else None
   if name:
    v=n.value
    try:out[name]=ast.literal_eval(v.args[0]) if isinstance(v,ast.Call) and isinstance(v.func,ast.Name) and v.func.id=='frozenset' else ast.literal_eval(v)
    except (ValueError,TypeError):pass
 return out
files=['MANIFEST.in','pyproject.toml','src/afterworlds/ingestion/mechanical/oracle.py','tests/ingestion/corpus/test_packaging.py','tests/ingestion/mechanical/test_accepted_inputs.py','tests/ingestion/mechanical/test_accepted_release_publication.py','tests/ingestion/mechanical/test_committed_accepted_authority.py','tests/ingestion/mechanical/test_oracle.py','tests/ingestion/mechanical/test_oracle_succession.py','tests/ingestion/mechanical/test_packaging.py','scripts/run_focused_tests.py']
bs={f:blob(f) for f in files};old=consts(blob(files[2],P));new=consts(bs[files[2]])
c7='2853f30a832ca581c9d4169b82d0c360f3d6a2d78f0ad8980de9997eef51f373';c8='ead7fa9d4fde484098f71221ca5ef82dfb2c82229d8fca80ab5feeb4e4d62d0d'
assert new['SUPERSEDED_ORACLE_SHA256']==old['SUPERSEDED_ORACLE_SHA256']|{c7};assert new['SUPERSEDED_RELEASE_VERSIONS']==old['SUPERSEDED_RELEASE_VERSIONS']
# The resolver functions themselves are exact AST matches, including quarantine and ambiguity guards.
functions=['committed_oracle_for','committed_inputs_for','_resolve_committed_inputs','_resolve_committed_oracle']
asts=[]
for src in [blob(files[2],P),bs[files[2]]]:asts.append({n.name:ast.dump(n,include_attributes=False) for n in ast.parse(src).body if isinstance(n,ast.FunctionDef) and n.name in functions})
assert asts[0]==asts[1] and set(asts[1])==set(functions)
pp=tomllib.loads(bs['pyproject.toml'].decode());oldpp=tomllib.loads(blob('pyproject.toml',P).decode())
newex=pp['tool']['setuptools']['exclude-package-data']['afterworlds'];oldex=oldpp['tool']['setuptools']['exclude-package-data']['afterworlds'];assert newex==oldex+['ingestion/mechanical/oracles/srd-5-2-1-corpus-8781d4e0-a3b-15c-c7.json']
assert pp['tool']['setuptools']['package-data']==oldpp['tool']['setuptools']['package-data']
newmanifest=[x for x in bs['MANIFEST.in'].decode().splitlines() if x.strip() and not x.lstrip().startswith('#')];oldmanifest=[x for x in blob('MANIFEST.in',P).decode().splitlines() if x.strip() and not x.lstrip().startswith('#')];assert newmanifest==oldmanifest+['exclude src/afterworlds/ingestion/mechanical/oracles/srd-5-2-1-corpus-8781d4e0-a3b-15c-c7.json']
OR='src/afterworlds/ingestion/mechanical/oracles/';tree=subprocess.check_output(['git','ls-tree','-r','--name-only',V,'--',OR],text=True).splitlines();oracles=[x for x in tree if x.endswith('.json')];records={};selected=[]
for path in oracles:
 b=blob(path);doc=json.loads(b);h=sha(b);records[path]={'sha256':h,'binding':doc['release_binding'],'schema':doc['representation_schema']}
 if h not in new['SUPERSEDED_ORACLE_SHA256'] and doc['release_binding']['release_version']=='5.2.1-corpus.8781d4e0-a3b' and doc['release_binding']['package_uuid']=='1299484e-c72d-509b-bd8d-d0169ee1f8d2': selected.append(path)
current=OR+'srd-5-2-1-corpus-8781d4e0-a3b-15c-c8.json';assert selected==[current];assert records[current]['sha256']==c8
rec=json.loads(blob(current));expected_review=json.loads((R/'.claude/review-notes/issue-15c-implementation/c8-native-review/recording/results.json').read_bytes());assert records[current]['sha256']==expected_review['recorded_sha256']
for name,h in expected_review['predecessor_pins'].items():assert records[OR+name]['sha256']==h and sha(blob(OR+name,P))==h
pkg=consts(bs['tests/ingestion/corpus/test_packaging.py']);assert pkg['_CURRENT']==pathlib.PurePosixPath(current).name and pkg['_CURRENT_SHA256']==c8
pkgdata=pp['tool']['setuptools']['package-data']['afterworlds'];wheel=[x for x in oracles if any(fnmatch.fnmatchcase(x.removeprefix('src/afterworlds/'),pat) for pat in pkgdata) and not any(fnmatch.fnmatchcase(x.removeprefix('src/afterworlds/'),pat) for pat in newex)];assert wheel==[current]
excluded=[x.split(' ',1)[1] for x in newmanifest if x.startswith('exclude ')];sdist=[x for x in oracles if x not in excluded];assert sdist==[current]
assert set(pkg['_NOT_SHIPPED'])>=set(pathlib.PurePosixPath(x).name for x in oracles if x!=current)
succ=consts(bs['tests/ingestion/mechanical/test_oracle_succession.py']);assert succ['_ACCEPTED_C8_PROPOSALS']==expected_review['proposal_identities'];expect={**succ['_ACCEPTED_15C_PROPOSALS'],**succ['_ACCEPTED_C7_PROPOSALS'],**succ['_ACCEPTED_C8_PROPOSALS']};actual={x['batch_id']:x['proposal_identity'] for x in rec['acceptance']['schema_anchors']};assert all(actual[k]==v for k,v in expect.items())
pub=consts(bs['tests/ingestion/mechanical/test_accepted_release_publication.py']);assert pub['PROJECTION']==expected_review['pure_native']['projection'] and pub['ORACLE_SHA256']==c8
F='.claude/review-notes/issue-15c-c8-recording/runs/';run=json.loads(blob(F+'recording-focused.result.json'));stdout=blob(F+'recording-focused.out.txt').decode();stderr=blob(F+'recording-focused.err.txt').decode();assert run['exit']==0 and '168 passed in 1889.68s' in stdout and 'Focused diagnostics PASSED (exit 0)' in stdout
assert 'tests/ingestion/corpus/test_packaging.py' not in run['args'];assert '--no-cov' in bs['scripts/run_focused_tests.py'].decode()
working={}
for path in files+[current]:working[path]={'sha256':sha((R/path).read_bytes()),'matches_reviewed_commit':sha((R/path).read_bytes())==pins[V+':'+path]}
head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
result={'reviewed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reviewed_revision':V,'head_observed':head,'only_added_superseded_digest':c7,'prior_supersession_and_resolver_guards_preserved':True,'sole_current_release_candidate':selected,'static_wheel_inclusion':wheel,'static_sdist_inclusion':sdist,'test_constants_match_actual_recording':True,'focused_diagnostics':run,'focused_output_summary':'168 passed in 1889.68s; six mechanical targets; no coverage; real distribution install smoke test excluded','artifact_pins':records,'reviewed_blob_sha256':pins,'working_file_boundary':working,'limits':['Static manifest selection is not an actual distribution build/install','No builder/store/re-record/test run performed','Baseline and independent gameplay changes outside this review','Full configured-coverage pytest, installed packaging smoke test and exact-head CI remain whole-PR gates']}
(O/'results.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8');print(json.dumps({k:v for k,v in result.items() if k not in ['artifact_pins','reviewed_blob_sha256','working_file_boundary']},indent=2));print('working_selected_all_match',all(x['matches_reviewed_commit'] for x in working.values()))
