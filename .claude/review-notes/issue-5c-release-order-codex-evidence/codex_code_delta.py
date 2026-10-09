"""Reconstruct the two pre-edit files without touching the Git index/worktree."""
import difflib
import hashlib
import json
import re
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
snapshot = json.loads((HERE / "pre-edit/snapshot.json").read_text(encoding="utf-8"))
patch = (HERE / "pre-edit/tracked.patch").read_text(encoding="utf-8")
report = {}
for name in ["src/afterworlds/ingestion/corpus/source_units.py", "tests/ingestion/corpus/test_source_units.py"]:
    head = subprocess.check_output(["rtk", "proxy", "git", "show", f"HEAD:{name}"], cwd=ROOT).decode("utf-8").replace("\r\n", "\n").splitlines(keepends=True)
    marker = f"diff --git a/{name} b/{name}\n"
    section = patch.split(marker,1)[1].split("diff --git ",1)[0] if marker in patch else ""
    output = []
    pos = 0
    in_hunk = False
    for line in section.splitlines(keepends=True):
        match = re.match(r"@@ -(\d+)(?:,\d+)? \+\d+(?:,\d+)? @@", line)
        if match:
            start = int(match.group(1)) - 1
            output.extend(head[pos:start])
            pos = start
            in_hunk = True
        elif in_hunk and line[0] in " +-":
            if line[0] in " -":
                assert head[pos] == line[1:], (name, pos, head[pos], line)
                pos += 1
            if line[0] in " +":
                output.append(line[1:])
        elif in_hunk and line.startswith("\\ No newline"):
            raise ValueError("No-newline patch needs explicit handling")
    output.extend(head[pos:])
    before = "".join(output)
    expected = snapshot["file_hashes"][name]["sha256"]
    assert expected in [hashlib.sha256(before.encode()).hexdigest(), hashlib.sha256(before.replace("\n", "\r\n").encode()).hexdigest()], (name,"baseline reconstruction mismatch")
    if name.endswith("/source_units.py"):
        exact_before = before.encode() if hashlib.sha256(before.encode()).hexdigest() == expected else before.replace("\n","\r\n").encode()
        (HERE / "source_units-before-order.py").write_bytes(exact_before)
    after = (ROOT / name).read_text(encoding="utf-8")
    delta = "".join(difflib.unified_diff(before.splitlines(keepends=True), after.splitlines(keepends=True), fromfile="pre-edit/"+name,tofile="current/"+name))
    target = HERE / ("codex-" + Path(name).stem + "-delta.patch")
    target.write_text(delta,encoding="utf-8")
    report[name] = {"verified_pre_edit_sha256":expected,"current_sha256":hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),"delta_path":str(target.relative_to(ROOT)),"delta_sha256":hashlib.sha256(target.read_bytes()).hexdigest(),"delta":delta}
(HERE / "codex-code-delta.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
print(json.dumps(report,indent=2))
