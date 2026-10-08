"""Read-only SQLite check of every exported leaf/chunk and release binding."""
import hashlib
import json
import sqlite3
from pathlib import Path

HERE = Path(__file__).resolve().parent
results = []
for name in ["rel-old", "rel-new"]:
    root = HERE / name
    identity = json.loads((root / "identity.json").read_text())
    leaves = json.loads((root / "leaves.json").read_text())
    db = root / "afterworlds.db"
    con = sqlite3.connect(db.resolve().as_uri() + "?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    errors = []
    release = con.execute("SELECT * FROM rp_corpus_releases WHERE package_uuid=?", (identity["package_uuid"],)).fetchone()
    for field in ["package_uuid","release_version","authoritative_source_hash","transform_config_hash","ledger_hash","bundle_root_hash","persisted_corpus_digest"]:
        if release is None or release[field] != identity[field]:
            errors.append("release:" + field)
    stored = {r["leaf_id"]:r for r in con.execute("SELECT * FROM rp_ledger_leaves WHERE package_uuid=?",(identity["package_uuid"],))}
    chunks = {r["chunk_id"]:r for r in con.execute("SELECT * FROM rp_chunks")}
    if len(stored) != len(leaves):
        errors.append("leaf count")
    if len(chunks) != identity["chunks"]:
        errors.append("chunk count")
    for row in leaves:
        actual = stored.get(row["leaf_id"])
        if actual is None:
            errors.append("missing leaf:" + row["leaf_id"])
            continue
        for field in row.keys() - {"chunk", "content_sha256", "container_path"}:
            if actual[field] != row[field]:
                errors.append("leaf:"+row["leaf_id"]+":"+field)
        if json.loads(actual["container_path"]) != row["container_path"]:
            errors.append("leaf container path:" + row["leaf_id"])
        if hashlib.sha256(actual["content"].encode()).hexdigest() != row["content_sha256"]:
            errors.append("leaf content:" + row["leaf_id"])
        expected = row["chunk"]
        if expected is not None:
            chunk = chunks.get(expected["chunk_id"])
            if chunk is None:
                errors.append("missing chunk:"+expected["chunk_id"])
                continue
            if hashlib.sha256(chunk["content"].encode()).hexdigest() != expected["content_sha256"]:
                errors.append("chunk content:"+expected["chunk_id"])
            if [chunk[f] for f in ["source_document","source_locator_type","source_locator_value"]] != expected["locator"]:
                errors.append("chunk locator:"+expected["chunk_id"])
            if chunk["source_section_label"] != expected["section_label"]:
                errors.append("chunk section:"+expected["chunk_id"])
    con.close()
    results.append({"source_store":name,"checked_leaves":len(leaves),"checked_chunks":len(chunks),"release_binding_matches_export":not any(e.startswith("release:") for e in errors),"all_exported_values_match_actual_sqlite":not errors,"errors":errors[:12],"read_only_connection":True})
result = {"results":results,"all_pass":all(r["all_exported_values_match_actual_sqlite"] for r in results)}
(HERE / "codex-sqlite-source-review.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
print(json.dumps(result,indent=2))
raise SystemExit(0 if result["all_pass"] else 1)
