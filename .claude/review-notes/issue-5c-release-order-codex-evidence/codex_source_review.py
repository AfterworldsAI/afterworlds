"""Compare actual persisted old/new build evidence with a narrow allowlist."""
import collections
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
old_dir = HERE / "rel-old"
new_dir = Path(sys.argv[1])

def read(root, name):
    return json.loads((root / name).read_text(encoding="utf-8"))

oi,ni = read(old_dir,"identity.json"),read(new_dir,"identity.json")
expected = read(HERE.parent / "release-order-review","structure-order-probe.json")["proposed_order"]
expected_order = [r["file"] for r in expected]
checks = {"official_fourteen_file_order":ni["corpus_files"] == expected_order,
          "same_file_membership":len(oi["corpus_files"]) == len(ni["corpus_files"]) == len(set(ni["corpus_files"])) == 14 and set(oi["corpus_files"]) == set(ni["corpus_files"])}
for field in ["authoritative_source_hash","units","containers","chunks","citation_report"]:
    checks[f"exact_{field}"] = oi[field] == ni[field]
for field in ["package_uuid","release_version","transform_config_hash","ledger_hash","bundle_root_hash","persisted_corpus_digest"]:
    checks[f"changed_{field}"] = oi[field] != ni[field]
old_leaves,new_leaves = read(old_dir,"leaves.json"),read(new_dir,"leaves.json")
old = {r["leaf_id"]:r for r in old_leaves}
new = {r["leaf_id"]:r for r in new_leaves}
checks["leaf_ids_unique_and_exact"] = len(old) == len(old_leaves) == len(new) == len(new_leaves) and old.keys() == new.keys()
changes = collections.Counter()
violations = []
for key in old.keys() & new.keys():
    a,b = old[key],new[key]
    if a.keys() != b.keys():
        violations.append({"leaf":key,"field":"keys"})
        continue
    for field in a:
        if field == "chunk":
            ca,cb = a[field],b[field]
            if (ca is None) != (cb is None):
                violations.append({"leaf":key,"field":"chunk presence"})
            elif ca is not None:
                if ca.keys() != cb.keys():
                    violations.append({"leaf":key,"field":"chunk keys"})
                for cfield in ca:
                    if ca[cfield] != cb.get(cfield):
                        changes["chunk."+cfield] += 1
                        if cfield != "chunk_id":
                            violations.append({"leaf":key,"field":"chunk."+cfield,"before":ca[cfield],"after":cb.get(cfield)})
        elif a[field] != b[field]:
            changes[field] += 1
            if field not in {"page_index","occurrence_index"}:
                violations.append({"leaf":key,"field":field,"before":a[field],"after":b[field]})
checks["only_reading_coordinates_and_chunk_id_change"] = not violations
checks["new_global_order_consecutive"] = [r["occurrence_index"] for r in new_leaves] == list(range(len(new_leaves)))
checks["within_file_leaf_order_preserved"] = all([r["leaf_id"] for r in old_leaves if r["page_index"] == i] == [r["leaf_id"] for r in new_leaves if r["page_index"] == ni["corpus_files"].index(name)] for i,name in enumerate(oi["corpus_files"]))
oc,nc = read(old_dir,"containers.json"),read(new_dir,"containers.json")
checks["container_ids_and_every_field_exact"] = len(oc) == len(nc) and {r["container_id"]:r for r in oc} == {r["container_id"]:r for r in nc}
result = {"old_build":str(old_dir),"new_build":str(new_dir),"checks":checks,"actual_changed_fields":dict(changes),"unexpected_differences":violations[:20],"old_binding":{k:oi[k] for k in ["package_uuid","release_version","authoritative_source_hash","transform_config_hash","bundle_root_hash","persisted_corpus_digest"]},"new_binding":{k:ni[k] for k in ["package_uuid","release_version","authoritative_source_hash","transform_config_hash","bundle_root_hash","persisted_corpus_digest"]},"limits":"Compares exported native-build evidence; raw build/persistence exits and SQLite reconstruction/reader checks must also be reviewed."}
(HERE / "codex-source-review.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(result,ensure_ascii=False,indent=2))
raise SystemExit(0 if all(checks.values()) else 1)
