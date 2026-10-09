"""Scoped, additive secrets-baseline coverage for the release-order recording.

Scans only this recording's files, the new oracle, the affected live pins and
the restart opening (Codex's own ``codex*`` review files are left to Codex).
Every hit must be a public content hash, 64-hex or the 16-hex ``fact_key``
form the prior oracle's entries already cover; it is added as
``is_secret: false`` unless its (type, hash) is already listed for that file.
Existing entries and all settings are preserved; only in-scope entries'
line numbers are refreshed. Runs the hook twice, keeping exits distinct:
against a private copy (content check) and against the real relative path
(fails while the baseline is unstaged; nothing is staged to cure it).
"""

import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

from detect_secrets.core.secrets_collection import SecretsCollection
from detect_secrets.settings import transient_settings

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RUN = HERE / "run"
BASELINE = ROOT / ".secrets.baseline"
EXPECTED_BEFORE = sys.argv[1]
OUT = HERE / "recorded-secrets-validation.json"
PRIVATE = ROOT / ".claude/_sp/release-order-recording/recorded-private.baseline"

CHANGED = [
    "docs/architecture/issue-5c-5d-clean-restart.md",
    "src/afterworlds/ingestion/mechanical/oracles/README.md",
    "src/afterworlds/ingestion/mechanical/oracles/srd-5-2-1-corpus-8781d4e0-a3b.json",
    "tests/ingestion/mechanical/test_accepted_inputs.py",
    "tests/ingestion/mechanical/test_committed_accepted_authority.py",
    "tests/ingestion/mechanical/test_oracle.py",
    "tests/ingestion/mechanical/test_packaging.py",
    "tests/ingestion/mechanical/test_source_release_readiness.py",
]
HEX = re.compile(r"[0-9a-fA-F]{64}|[0-9a-fA-F]{16}")


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> None:
    for p in (OUT, PRIVATE):
        assert not p.exists(), f"refusing to overwrite {p}"
    before_bytes = BASELINE.read_bytes()
    assert hashlib.sha256(before_bytes).hexdigest() == EXPECTED_BEFORE
    before = json.loads(before_bytes)
    own = sorted(
        p.relative_to(ROOT).as_posix()
        for p in HERE.rglob("*")
        if p.is_file()
        and p != OUT
        and "__pycache__" not in p.parts
        and not any(part.startswith("codex") for part in p.relative_to(HERE).parts)
    )
    files = sorted(set(own) | set(CHANGED))
    assert all((ROOT / f).is_file() for f in files)

    with transient_settings(before):
        found = SecretsCollection()
        for f in files:
            found.scan_file(f)
    for f, s in found:
        assert s.type == "Hex High Entropy String" and HEX.fullmatch(
            s.secret_value or ""
        ), ("non-public-hash hit needs review", f, s.type, s.line_number)

    after = json.loads(before_bytes)
    added = refreshed = 0
    for f, rows in found.json().items():
        existing = after["results"].setdefault(f, [])
        index = {(r["type"], r["hashed_secret"]): r for r in existing}
        for row in rows:
            key = (row["type"], row["hashed_secret"])
            if key in index:
                if index[key]["line_number"] != row["line_number"]:
                    index[key]["line_number"] = row["line_number"]
                    refreshed += 1
            else:
                row["is_secret"] = False
                existing.append(row)
                index[key] = row
                added += 1

    # Settings and every out-of-scope entry exact; in-scope entries keep
    # their identity and order, only line numbers may move.
    assert all(after[k] == before[k] for k in before if k != "results")
    for f, rows in before["results"].items():
        new = after["results"][f]
        if f.replace("\\", "/") not in files:
            assert new == rows, f
        else:
            strip = [{k: v for k, v in r.items() if k != "line_number"} for r in rows]
            assert [
                {k: v for k, v in r.items() if k != "line_number"}
                for r in new[: len(rows)]
            ] == strip, f
    assert BASELINE.read_bytes() == before_bytes, "concurrent baseline edit"
    BASELINE.write_text(
        json.dumps(after, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    sealed = sha(BASELINE)
    shutil.copyfile(BASELINE, PRIVATE)

    def hook(baseline: str, label: str) -> int:
        for ext in (".log", ".exit"):
            assert not (RUN / f"{label}{ext}").exists(), label
        r = subprocess.run(
            [
                str(ROOT / "venv/Scripts/detect-secrets-hook.exe"),
                "--baseline",
                baseline,
                *files,
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        (RUN / f"{label}.log").write_text(r.stdout + r.stderr, encoding="utf-8")
        (RUN / f"{label}.exit").write_text(f"{r.returncode}\n", encoding="utf-8")
        return r.returncode

    private_exit = hook(str(PRIVATE), "secrets-private-copy")
    private_after = sha(PRIVATE)
    real_exit = hook(".secrets.baseline", "secrets-real-hook")
    assert sha(BASELINE) == sealed, "real hook changed the baseline"
    receipt = {
        "scope": "recording folder, new oracle, affected live pins, restart opening",
        "files_checked": len(files),
        "baseline_before_sha256": EXPECTED_BEFORE,
        "baseline_after_sha256": sealed,
        "entries_added_public_sha256": added,
        "in_scope_line_numbers_refreshed": refreshed,
        "all_hits_public_sha256": True,
        "settings_and_out_of_scope_entries_exact": True,
        "private_copy_hook_exit": private_exit,
        "private_copy_unchanged_by_hook": private_after == sealed,
        "real_relative_path_hook_exit": real_exit,
        "real_hook_is_green": real_exit == 0,
        "staged": False,
    }
    OUT.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
