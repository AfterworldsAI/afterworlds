"""Independent delta against the pre-edit snapshot; never writes accepted files."""
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
BASE = json.loads((HERE / "pre-edit/snapshot.json").read_text(encoding="utf-8"))


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git(*args):
    return subprocess.check_output(["rtk", "proxy", "git", *args], cwd=ROOT).decode("utf-8").strip()


changed = []
for name, old in BASE["file_hashes"].items():
    path = ROOT / name
    current = sha(path) if path.is_file() else None
    if current != old["sha256"]:
        changed.append({"path": name, "before": old["sha256"], "after": current})
external_changed = []
for name, old in BASE["external_hashes"].items():
    path = Path(name)
    current = sha(path) if path.is_file() else None
    if current != old:
        external_changed.append({"path": name, "before": old, "after": current})
oracle = ROOT / "src/afterworlds/ingestion/mechanical/oracles/srd-5-2-1-corpus-3fe24ff6-4e3.json"
checks = {
    "head_unchanged": git("rev-parse", "HEAD") == BASE["head"],
    "branch_unchanged": git("branch", "--show-current") == BASE["branch"],
    "index_unchanged": sha(ROOT / ".git/index") == BASE["index_sha256"],
    "stashes_unchanged": git("stash", "list", "--format=%H %gd %s") == BASE["stashes"].strip(),
    "live_oracle_unchanged": sha(oracle) == BASE["oracle_sha256"],
    "external_settings_guidance_launcher_unchanged": not external_changed,
}
result = {"checks": checks, "changed_existing_files": changed, "external_changed": external_changed}
(HERE / "claude-preservation.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, indent=2))
raise SystemExit(0 if all(checks.values()) else 1)
