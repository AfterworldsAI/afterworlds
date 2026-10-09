"""Independent exact semantic comparison with explicit release-only differences."""
import collections
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
old_path = HERE / "pre-edit/accepted-oracle.json"
new_path = Path(sys.argv[1])
old = json.loads(old_path.read_text(encoding="utf-8"))
new = json.loads(new_path.read_text(encoding="utf-8"))
checks = {}
checks["root_keys_equal"] = old.keys() == new.keys()
for key in old.keys() - {"release_binding", "representation", "reference_resolutions", "acceptance"}:
    checks[f"exact_root_{key}"] = old[key] == new[key]
checks["binding_keys_equal"] = old["release_binding"].keys() == new["release_binding"].keys()
checks["official_source_hash_preserved"] = old["release_binding"]["authoritative_source_hash"] == new["release_binding"]["authoritative_source_hash"]
checks["new_package_and_version"] = all(old["release_binding"][k] != new["release_binding"][k] for k in ["package_uuid", "release_version"])
checks["representation_keys_equal"] = old["representation"].keys() == new["representation"].keys()
for key in old["representation"].keys() - {"prose_bindings"}:
    checks[f"exact_representation_{key}"] = old["representation"][key] == new["representation"][key]

def keyed_prose(rows):
    result = {}
    for row in rows:
        stripped = {k:v for k,v in row.items() if k != "chunk_id"}
        key = json.dumps(stripped, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        if key in result:
            raise ValueError("Duplicate prose binding after removing only chunk identity")
        result[key] = row["chunk_id"]
    return result

op = keyed_prose(old["representation"]["prose_bindings"])
np = keyed_prose(new["representation"]["prose_bindings"])
checks["prose_binding_content_and_extents_exact"] = op.keys() == np.keys()
# Reordering the canonical list may be a consequence of changed opaque chunk IDs.
# Verify the actual old/new chunk identity algorithm, not a guessed correspondence.
sys.path.insert(0, str(ROOT / "src"))
from afterworlds.ingestion.corpus.hashing import content_id, canonical_bytes
from afterworlds.ingestion.mechanical.canonical import canonical_order
span_leaf = {row["span_id"]:row["leaf_id"] for row in old["spans"]}
chunk_errors = []
for label, data in [("old", old), ("new", new)]:
    for row in data["representation"]["prose_bindings"]:
        leaf_id = span_leaf.get(row["span_id"])
        expected = content_id("chunk", data["release_binding"]["package_uuid"], leaf_id)
        if leaf_id is None or row["chunk_id"] != expected:
            chunk_errors.append({"side":label,"span_id":row["span_id"],"actual":row["chunk_id"],"expected":expected})
checks["all_chunk_ids_native_release_scoped"] = not chunk_errors
new_identity = json.loads((HERE / "rel-new/identity.json").read_text(encoding="utf-8"))
checks["six_field_binding_equals_actual_release"] = all(new["release_binding"][k] == new_identity[k] for k in new["release_binding"])
old_leaves = json.loads((HERE / "rel-old/leaves.json").read_text(encoding="utf-8"))
new_leaves = json.loads((HERE / "rel-new/leaves.json").read_text(encoding="utf-8"))
old_chunks = {r["leaf_id"]:r["chunk"]["chunk_id"] for r in old_leaves}
new_chunks = {r["leaf_id"]:r["chunk"]["chunk_id"] for r in new_leaves}
chunk_map = {new_chunks[k]:v for k,v in old_chunks.items()}
def normalize_chunks(x):
    if isinstance(x, dict):
        return {k:normalize_chunks(v) for k,v in x.items()}
    if isinstance(x, list):
        return [normalize_chunks(v) for v in x]
    return chunk_map.get(x,x) if isinstance(x,str) else x
checks["exact_representation_provenance"] = collections.Counter(map(canonical_bytes,old["representation"]["provenance"])) == collections.Counter(map(canonical_bytes,normalize_chunks(new["representation"]["provenance"])))
for field in ["prose_bindings", "provenance"]:
    checks[f"native_canonical_representation_{field}"] = all(data["representation"][field] == canonical_order(data["representation"][field]) for data in [old,new])
serialized_new = new_path.read_text(encoding="utf-8")
checks["no_old_chunk_residue"] = all(value not in serialized_new for value in old_chunks.values())
checks["no_old_binding_residue"] = all(value not in serialized_new for k,value in old["release_binding"].items() if k != "authoritative_source_hash")

def references(data):
    return [{k:v for k,v in row.items() if k != "release_binding"} for row in data["reference_resolutions"]]

checks["reference_resolutions_exact_except_binding_in_order"] = references(old) == references(new)
checks["every_reference_uses_new_full_binding"] = all(row["release_binding"] == new["release_binding"] for row in new["reference_resolutions"])
oa,na = old["acceptance"],new["acceptance"]
checks["batch_ids_in_original_order"] = [r["batch_id"] for r in oa["batches"]] == [r["batch_id"] for r in na["batches"]]
checks["batch_scope_and_diff_exact"] = [{k:r[k] for k in ["batch_id", "diff", "resolved_scope", "semantic_diff_hash"]} for r in oa["batches"]] == [{k:r[k] for k in ["batch_id", "diff", "resolved_scope", "semantic_diff_hash"]} for r in na["batches"]]
for field,identity in [("records","span_id"),("review_unit_records","unit_id"),("reference_resolution_records","resolution_id")]:
    checks[f"acceptance_{field}_identity_order_exact"] = [r[identity] for r in oa[field]] == [r[identity] for r in na[field]]
    if field != "reference_resolution_records":
        # These collections sort by complete evidence payload. Simulated dates
        # change canonical order; compare exact identity/batch multisets instead.
        del checks[f"acceptance_{field}_identity_order_exact"]
        checks[f"acceptance_{field}_batch_scope_exact"] = collections.Counter((r[identity],r["batch_id"]) for r in oa[field]) == collections.Counter((r[identity],r["batch_id"]) for r in na[field])
        checks[f"native_canonical_acceptance_{field}"] = all(data[field] == canonical_order(data[field]) for data in [oa,na])
approver_values = collections.Counter()
for field in ["records","review_unit_records","reference_resolution_records"]:
    for row in na[field]:
        for key in ["reviewer","authorized_by"]:
            if key in row:
                approver_values[(key,str(row[key]))] += 1
checks["no_new_approval_attributed_to_owner"] = all(value == "SIMULATION - not an Owner approval" for key,value in approver_values)
checks["acceptance_keys_exact"] = oa.keys() == na.keys()
checks["schema_lifts_exact"] = oa["lifts"] == na["lifts"]
checks["schema_anchor_history_exact_except_proposal_identity"] = [{k:v for k,v in r.items() if k != "proposal_identity"} for r in oa["schema_anchors"]] == [{k:v for k,v in r.items() if k != "proposal_identity"} for r in na["schema_anchors"]]
checks["every_batch_and_anchor_has_new_proposal_identity"] = all(a["proposal_identity"] != b["proposal_identity"] for f in ["batches","schema_anchors"] for a,b in zip(oa[f],na[f]))
checks["batch_rule_simulated"] = all(r["rule"].startswith("SIMULATION ONLY: release-order replacement candidate") and r["rule"].endswith("not an Owner acceptance") for r in na["batches"])
checks["authorization_reference_simulated"] = all(r["authorization_reference"].startswith("SIMULATION ONLY: release-order replacement candidate") and r["authorization_reference"].endswith("not an Owner authorization") for r in na["reference_resolution_records"])
checks["simulated_dates_exact"] = all(r[key] == "2026-10-06T00:00:00Z" for f,key in [("records","accepted_at"),("review_unit_records","accepted_at"),("reference_resolution_records","resolved_at")] for r in na[f])
result = {"old_sha256":hashlib.sha256(old_path.read_bytes()).hexdigest(),"candidate_path":str(new_path),"candidate_sha256":hashlib.sha256(new_path.read_bytes()).hexdigest(),"old_binding":old["release_binding"],"new_binding":new["release_binding"],"checks":checks,"approval_attribution_counts":[{"field":k,"value":v,"count":n} for (k,v),n in approver_values.items()],"chunk_errors":chunk_errors[:5],"acceptance_fields_requiring_independent_review":["batch proposal identities and rule", "schema anchors and lifts", "simulated approval timestamps and authorization references"],"limits":"This compares payloads and native chunk ID derivation only; release construction/locators/validation/persistence/readers and schema-anchor histories require separate evidence."}
(HERE / "codex-payload-review.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(result,ensure_ascii=False,indent=2))
raise SystemExit(0 if all(checks.values()) else 1)
