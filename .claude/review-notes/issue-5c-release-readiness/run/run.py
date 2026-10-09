"""Run a venv python command; log raw output, input pins and exit code durably.

usage: run.py NAME ARG... (ARGs go to the venv python, cwd = repo). Refuses to
overwrite an existing NAME.log. Copied from
issue-5c-release-order-candidate/scripts/run.py (sha 2f51f230).
"""

import datetime
import hashlib
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
name, args = sys.argv[1], sys.argv[2:]
LOG = HERE / f"{name}.log"
EXIT = HERE / f"{name}.exit"
assert not LOG.exists() and not EXIT.exists(), f"{name} already ran"
env = dict(
    os.environ, RTK_DISABLED="1", PYTHONUTF8="1", PYTHONUNBUFFERED="1", MYPYPATH="src"
)
with LOG.open("w", encoding="utf-8", newline="\n") as log:
    now = datetime.datetime.now(datetime.UTC).isoformat()
    log.write(f"start {now}\n$ RTK_DISABLED=1 PYTHONUTF8=1 MYPYPATH=src ")
    log.write(f"{Path(sys.executable).relative_to(REPO).as_posix()} {' '.join(args)}\n")
    for a in args:
        p = REPO / a
        if p.is_file():
            log.write(f"input {hashlib.sha256(p.read_bytes()).hexdigest()}  {a}\n")
    log.flush()
    code = subprocess.call(
        [sys.executable, *args], cwd=REPO, env=env, stdout=log, stderr=subprocess.STDOUT
    )
    log.write(f"end {datetime.datetime.now(datetime.UTC).isoformat()} exit {code}\n")
EXIT.write_text(f"{code}\n", encoding="utf-8", newline="\n")
