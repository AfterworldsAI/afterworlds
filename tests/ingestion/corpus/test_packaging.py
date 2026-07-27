"""Packaging smoke test for the committed table oracle — Issue 5c, PR #134 R16 F3.

``srd_table_inventory.json`` is read at runtime by ``table_inventory.py`` and
candidate construction/finalization fail without it. This proves the exact
committed oracle ships in **both** the wheel and the sdist and loads from an
*installed* distribution (not the source checkout / CWD), reproducing the
committed inventory hash across 683 entries.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import sysconfig
import tarfile
import zipfile
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_INVENTORY_REL = "afterworlds/ingestion/corpus/srd_table_inventory.json"
_COMMITTED = _REPO_ROOT / "src" / _INVENTORY_REL


def _build_dists(out_dir: Path) -> tuple[Path, Path]:
    """Build wheel + sdist into *out_dir* (no build isolation → uses the dev env).

    ``--no-isolation`` requires the declared build backend (``setuptools>=68``,
    ``wheel`` — see ``[build-system].requires``) to be importable in the current
    environment; the dev extra installs them explicitly. On any build failure the
    captured stdout+stderr are surfaced (they were swallowed before, hiding the CI
    root cause — R17).
    """
    pytest.importorskip("build")
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "build",
            "--no-isolation",
            "--outdir",
            str(out_dir),
            str(_REPO_ROOT),
        ],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, (
        f"`python -m build --no-isolation` failed (exit {proc.returncode}).\n"
        f"--- stdout ---\n{proc.stdout}\n--- stderr ---\n{proc.stderr}"
    )
    wheels = list(out_dir.glob("*.whl"))
    sdists = list(out_dir.glob("*.tar.gz"))
    assert len(wheels) == 1, wheels
    assert len(sdists) == 1, sdists
    return wheels[0], sdists[0]


def test_wheel_and_sdist_include_inventory_and_load_from_install(tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    wheel, sdist = _build_dists(dist)

    # Both archives must contain the exact committed JSON.
    with zipfile.ZipFile(wheel) as zf:
        assert any(n.endswith(_INVENTORY_REL) for n in zf.namelist()), zf.namelist()
    with tarfile.open(sdist) as tf:
        assert any(
            m.name.endswith("src/" + _INVENTORY_REL) or m.name.endswith(_INVENTORY_REL)
            for m in tf.getmembers()
        ), [m.name for m in tf.getmembers() if m.name.endswith(".json")]

    # Install the wheel into an isolated target dir (not the editable checkout).
    target = tmp_path / "site"
    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--no-deps",
            "--target",
            str(target),
            str(wheel),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    # Import from the installed target — NOT the source tree. ``-S`` skips site.py
    # (so the editable-install finder never registers and cannot shadow); the
    # target is first on the path and dependencies resolve from the dev env's
    # site-packages. CWD is a neutral tmp dir, so the repo is never importable.
    purelib = sysconfig.get_paths()["purelib"]
    code = (
        "import afterworlds.ingestion.corpus.table_inventory as m;"
        "inv=m.load_committed_inventory();"
        "print(len(inv));print(m.committed_inventory_hash());print(m.__file__)"
    )
    env = {**os.environ, "PYTHONPATH": os.pathsep.join([str(target), purelib])}
    proc = subprocess.run(
        [sys.executable, "-S", "-c", code],
        cwd=str(tmp_path),
        env=env,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    n_str, hash_str, mod_file = proc.stdout.strip().splitlines()[:3]

    committed = json.loads(_COMMITTED.read_text(encoding="utf-8"))
    assert int(n_str) == committed["table_count"] == 683
    assert hash_str == committed["inventory_hash"]
    # Proof it imported the installed copy, not the source tree.
    assert str(target) in mod_file
    assert str(_REPO_ROOT / "src") not in mod_file
