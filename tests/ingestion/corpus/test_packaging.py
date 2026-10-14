"""Packaging smoke test for the shipped rules authority — CRD Issue 5c/5d.

Builds the real project's wheel **and** sdist and proves three things about what
they carry:

* the current accepted authority, ``srd-5-2-1-corpus-8781d4e0-a3b-15b-c9.json``, ships
  byte-identically and resolves through ``committed_inputs_for`` from an
  *installed* distribution (not the source checkout or the CWD);
* the products retired under Step 5 of the Recorded Owner Decision of
  21 September 2026 -- the original accepted authority
  ``srd-5-2-1-corpus-36b786d8-fa2.json`` and the corpus table inventory
  ``srd_table_inventory.json`` -- ship in neither archive, and the installed
  resolver still refuses the retired release as quarantined rather than
  reporting it absent;
* the superseded intermediate releases, which only tests and replay evidence
  read, are not shipped either.
"""

from __future__ import annotations

import hashlib
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
_ORACLES_REL = "afterworlds/ingestion/mechanical/oracles"
#: The CRD Issue 15b C9 successor; the release's original artifact, its CRD
#: Issue 2b G1 successor, the native C5 successor and the C7 and C8 successors
#: are superseded by digest.
_CURRENT = "srd-5-2-1-corpus-8781d4e0-a3b-15b-c9.json"
_CURRENT_SHA256 = "01729b532a0ff46047608d9e46d539851ba2c9a32aaa9e0468ae0babb902ec7b"  # noqa: E501  # pragma: allowlist secret
_CURRENT_PKG = "1299484e-c72d-509b-bd8d-d0169ee1f8d2"
_CURRENT_REL = "5.2.1-corpus.8781d4e0-a3b"
_RETIRED_PKG = "4458fa10-4a66-5e0e-9ecc-ea37530ad2b4"
_RETIRED_REL = "5.2.1-corpus.36b786d8-fa2"
_NOT_SHIPPED = (
    "srd_table_inventory.json",
    "srd-5-2-1-corpus-36b786d8-fa2.json",
    "srd-5-2-1-corpus-3fe24ff6-4e3.json",
    "srd-5-2-1-corpus-574662e9-0ef.json",
    "srd-5-2-1-corpus-8781d4e0-a3b.json",
    "srd-5-2-1-corpus-8781d4e0-a3b-g1.json",
    "srd-5-2-1-corpus-8781d4e0-a3b-15c.json",
    "srd-5-2-1-corpus-8781d4e0-a3b-15c-c7.json",
    "srd-5-2-1-corpus-8781d4e0-a3b-15c-c8.json",
)

_PROBE = f"""
import json
from afterworlds.ingestion.mechanical import oracle
from afterworlds.quarantine import QuarantinedAuthorityError

inputs = oracle.committed_inputs_for({_CURRENT_PKG!r}, {_CURRENT_REL!r})
try:
    oracle.committed_inputs_for({_RETIRED_PKG!r}, {_RETIRED_REL!r})
    retired = "resolved"
except QuarantinedAuthorityError:
    retired = "quarantined"
print(json.dumps({{
    "module_file": oracle.__file__,
    "files": sorted(p.name for p in oracle.COMMITTED_ORACLE_DIR.glob("*.json")),
    "resolved_release": inputs.oracle.binding.release_version if inputs else None,
    "batches": len(inputs.batches) if inputs else None,
    "retired": retired,
}}))
"""


def _build_dists(out_dir: Path) -> tuple[Path, Path]:
    """Build wheel + sdist into *out_dir* (no build isolation → uses the dev env).

    ``--no-isolation`` requires the declared build backend (``setuptools>=83.0.0``,
    ``wheel`` — see ``[build-system].requires``) to be importable in the current
    environment; the dev extra installs them explicitly. On any build failure the
    captured stdout+stderr are surfaced.
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


def _install(artifact: Path, target: Path) -> None:
    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--no-deps",
            "--no-build-isolation",
            "--target",
            str(target),
            str(artifact),
        ],
        check=True,
        capture_output=True,
        text=True,
    )


def _probe_installed(target: Path, cwd: Path) -> dict[str, object]:
    """Resolve authority from the install in *target*, never the source tree.

    ``-S`` skips ``site.py`` so the editable-install finder never registers and
    cannot shadow the target; dependencies resolve from the dev env and ``cwd``
    is a neutral tmp dir.
    """
    purelib = sysconfig.get_paths()["purelib"]
    env = {**os.environ, "PYTHONPATH": os.pathsep.join([str(target), purelib])}
    proc = subprocess.run(
        [sys.executable, "-S", "-c", _PROBE],
        cwd=str(cwd),
        env=env,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    result: dict[str, object] = json.loads(proc.stdout.strip().splitlines()[-1])
    assert str(target) in str(result["module_file"])
    assert str(_REPO_ROOT / "src") not in str(result["module_file"])
    return result


def test_wheel_and_sdist_ship_current_authority_and_omit_retired_products(
    tmp_path: Path,
) -> None:
    dist = tmp_path / "dist"
    dist.mkdir()
    wheel, sdist = _build_dists(dist)

    with zipfile.ZipFile(wheel) as zf:
        wheel_names = zf.namelist()
        current = [n for n in wheel_names if n.endswith(f"{_ORACLES_REL}/{_CURRENT}")]
        assert len(current) == 1, [n for n in wheel_names if n.endswith(".json")]
        assert hashlib.sha256(zf.read(current[0])).hexdigest() == _CURRENT_SHA256
    with tarfile.open(sdist) as tf:
        sdist_names = tf.getnames()
        member = tf.extractfile(
            next(n for n in sdist_names if n.endswith(f"src/{_ORACLES_REL}/{_CURRENT}"))
        )
        assert member is not None
        assert hashlib.sha256(member.read()).hexdigest() == _CURRENT_SHA256
    for name in _NOT_SHIPPED:
        assert not [n for n in wheel_names if n.endswith("/" + name)], name
        assert not [n for n in sdist_names if n.endswith("/" + name)], name

    for label, artifact in (("wheel", wheel), ("sdist", sdist)):
        target = tmp_path / f"site-{label}"
        _install(artifact, target)
        result = _probe_installed(target, tmp_path)
        assert result["files"] == [_CURRENT], f"{label}: {result}"
        assert result["resolved_release"] == _CURRENT_REL, f"{label}: {result}"
        assert result["batches"] == 24, f"{label}: {result}"
        assert result["retired"] == "quarantined", f"{label}: {result}"
