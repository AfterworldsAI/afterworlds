"""Run selected regression diagnostics after formatting checks, without coverage.

This command never establishes acceptance or full-gate success. Use ordinary
pytest and the other required gates for final-head acceptance evidence.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LABEL = "FOCUSED DIAGNOSTICS ONLY - not acceptance or full-gate evidence"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="append",
        required=True,
        metavar="PYTHON_FILE",
        help="changed Python file to check with Black; repeat for each file",
    )
    parser.add_argument("targets", nargs="+", help="test files or pytest node IDs")
    args = parser.parse_args(argv)
    test_files = [target.split("::", 1)[0] for target in args.targets]
    files = list(dict.fromkeys([*args.check, *test_files]))
    for name in files:
        path = (ROOT / name).resolve()
        if not path.is_relative_to(ROOT) or not path.is_file() or path.suffix != ".py":
            parser.error(f"expected a Python file within the repository: {name}")

    print(LABEL, flush=True)
    formatted = subprocess.run(
        [sys.executable, "-m", "black", "--check", *files], cwd=ROOT, check=False
    )
    if formatted.returncode:
        print("Formatting check failed; pytest was not started.", flush=True)
        return formatted.returncode

    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "--no-cov", *args.targets],
        cwd=ROOT,
        check=False,
    )
    status = "PASSED" if result.returncode == 0 else "FAILED"
    print(
        f"Focused diagnostics {status} (exit {result.returncode}). {LABEL}", flush=True
    )
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
