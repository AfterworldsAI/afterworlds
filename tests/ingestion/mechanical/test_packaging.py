"""Packaging smoke test for committed accepted oracles — CRD Issue 5d, PR #141 R2.

``oracle.committed_oracle_for`` resolves accepted authority from a fixed
directory inside the installed package. If that directory's JSON is missing from
the distribution metadata, a source checkout publishes and an installed
application silently returns ``ABSENT`` for every projection — publication
failing for a reason that has nothing to do with the oracle.

The real SRD artifact would make a resolution hit ambiguous — it might succeed
because packaging works, or because some other release happened to match. So
this builds a **copy** of the source tree carrying one valid *sentinel* oracle
bound to a release that exists nowhere else, produces a wheel and an sdist from
it, installs each, and drives the genuine production resolution and publication
entry point against the installed copy. Archive listings are checked
too, but they are not the proof: the defect is runtime resource resolution, so
the assertion that matters is that ``publish_from_committed_oracle`` reaches the
packaged oracle instead of reporting ``ABSENT``.

Follows the CRD Issue 5c pattern in ``tests/ingestion/corpus/test_packaging.py``.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import sysconfig
import tarfile
import zipfile
from pathlib import Path

import pytest

from afterworlds.ingestion.mechanical.representation import (
    REPRESENTATION_SCHEMA_VERSION,
    representation_schema_hash,
)

_REPO_ROOT = Path(__file__).resolve().parents[3]
_ORACLES_REL = "afterworlds/ingestion/mechanical/oracles"
_PRODUCTION_ORACLES = _REPO_ROOT / "src" / _ORACLES_REL

#: Distinct from every real release so a resolution hit cannot be a coincidence.
SENTINEL_PACKAGE = "pkg-sentinel-packaging"
SENTINEL_RELEASE = "rel-sentinel-packaging"
SENTINEL_FILENAME = "sentinel_packaging_oracle.json"

#: The smallest payload ``load_accepted_inputs`` accepts: no spans, no
#: representation, and therefore no obligations — the derived obligation
#: relation over an empty record set is empty, so the closed-relation check
#: passes — plus an empty acceptance block, which is complete evidence for an
#: empty span set. It exists to be *found*, not to pass a gate.
SENTINEL_ORACLE: dict[str, object] = {
    "artifact_kind": "accepted_authority",
    "acceptance": {"batches": [], "records": []},
    "release_binding": {
        "package_uuid": SENTINEL_PACKAGE,
        "release_version": SENTINEL_RELEASE,
        "authoritative_source_hash": "a" * 64,
        "transform_config_hash": "b" * 64,
        "bundle_root_hash": "c" * 64,
        "persisted_corpus_digest": "d" * 64,
    },
    "semantic_policy_version": "sentinel",
    "semantic_policy_hash": "e" * 64,
    # The one field that may not be a sentinel. A committed artifact is refused
    # at load unless its exact (version, hash) pair names a contract this build
    # accepts authority under (#137 round 4), and the resolver loads every file
    # in the packaged directory before filtering by release — so a fake schema
    # here would make the sentinel unloadable rather than merely unpublishable.
    # Taken live rather than pinned: this test is about packaging, and a literal
    # would rot at the next succession.
    "representation_schema": {
        "version": REPRESENTATION_SCHEMA_VERSION,
        "hash": representation_schema_hash(),
    },
    "spans": [],
    "representation": {
        "records": [],
        "components": [],
        "prose_bindings": [],
        "relationships": [],
        "references": [],
        "provenance": [],
    },
    "obligations": [],
}

#: Runs inside the installed distribution, with the repository unimportable. It
#: exercises the real production path: resolve the committed oracle for the
#: sentinel release, then call the production publication entry against a header
#: bound to that release. Without the packaged JSON, ``committed_oracle_for``
#: returns ``None`` and the entry reports ``ABSENT``; with it, the gate runs and
#: refuses for a real reason. "Not ABSENT" is therefore the discriminator.
_PROBE = f"""
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from afterworlds.persistence.orm.base import Base
from afterworlds.persistence.orm.corpus import CorpusReleaseORM
from afterworlds.persistence.orm.mechanical import MechanicalProjectionORM
from afterworlds.ingestion.mechanical import oracle as oracle_module
from afterworlds.ingestion.mechanical.oracle import committed_oracle_for
from afterworlds.ingestion.mechanical.publication import publish_from_committed_oracle

PKG = {SENTINEL_PACKAGE!r}
REL = {SENTINEL_RELEASE!r}
NOW = "2026-08-01T00:00:00Z"

resolved = committed_oracle_for(PKG, REL)

engine = create_engine("sqlite://")
Base.metadata.create_all(engine)
with Session(engine) as session:
    session.add(
        CorpusReleaseORM(
            package_uuid=PKG,
            release_version=REL,
            authoritative_source_hash="a" * 64,
            transform_config_hash="b" * 64,
            bundle_root_hash="c" * 64,
            persisted_corpus_digest="d" * 64,
            ledger_hash="1" * 64,
            policy_hash="2" * 64,
            reconciliation_hash="3" * 64,
            transform_config={{}},
            publication_status="published",
            created_at=NOW,
        )
    )
    session.flush()
    session.add(
        MechanicalProjectionORM(
            projection_uuid="sentinel-projection",
            package_uuid=PKG,
            release_version=REL,
            authoritative_source_hash="a" * 64,
            transform_config_hash="b" * 64,
            bundle_root_hash="c" * 64,
            persisted_corpus_digest="d" * 64,
            semantic_policy_version="sentinel",
            semantic_policy_hash="e" * 64,
            representation_schema_version="sentinel",
            representation_schema_hash="f" * 64,
            payload_hash="f" * 64,
            publication_status="draft",
            created_at=NOW,
        )
    )
    session.flush()
    outcome = publish_from_committed_oracle(
        session, "sentinel-projection", now=NOW
    ).outcome

print(json.dumps({{
    "module_file": oracle_module.__file__,
    "oracle_dir": str(oracle_module.COMMITTED_ORACLE_DIR),
    "resolved": resolved is not None,
    "resolved_release": None if resolved is None else resolved.binding.release_version,
    "outcome": outcome.value,
}}))
"""


def _staged_source_tree(tmp_path: Path) -> Path:
    """A build-able copy of the project carrying one sentinel oracle.

    A copy rather than the checkout: the sentinel must be present at build time
    to prove the distribution metadata picks it up, and it must never be written
    into the real oracle directory, which holds reviewed content only.
    """
    staged = tmp_path / "src-tree"
    staged.mkdir()
    for name in ("pyproject.toml", "MANIFEST.in"):
        shutil.copyfile(_REPO_ROOT / name, staged / name)
    shutil.copytree(
        _REPO_ROOT / "src",
        staged / "src",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )
    (staged / "src" / _ORACLES_REL / SENTINEL_FILENAME).write_text(
        json.dumps(SENTINEL_ORACLE, indent=2), encoding="utf-8"
    )
    return staged


def _build_dists(source: Path, out_dir: Path) -> tuple[Path, Path]:
    """Build wheel + sdist from *source* using the dev env's build backend."""
    pytest.importorskip("build")
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "build",
            "--no-isolation",
            "--outdir",
            str(out_dir),
            str(source),
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
    """Run the production path against the install in *target*.

    ``-S`` skips ``site.py`` so the editable-install finder never registers and
    cannot shadow the target; the target leads ``PYTHONPATH`` and dependencies
    resolve from the dev env. ``cwd`` is a neutral tmp dir, so the repository is
    never importable.
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
    # Proof it imported the installed copy, not the source tree.
    assert str(target) in str(result["module_file"])
    assert str(_REPO_ROOT / "src") not in str(result["module_file"])
    return result


def test_the_production_oracle_directory_ships_only_reviewed_content() -> None:
    """The real directory holds the accepted SRD artifact and nothing else.

    Guards the sentinel from leaking into the checkout — its release is chosen
    to collide with nothing, so its presence here would mean a test wrote into
    the source tree.
    """
    assert _PRODUCTION_ORACLES.is_dir()
    assert sorted(p.name for p in _PRODUCTION_ORACLES.glob("*.json")) == [
        "srd-5-2-1-corpus-36b786d8-fa2.json"
    ]
    assert not list(_PRODUCTION_ORACLES.glob(f"*{SENTINEL_PACKAGE}*"))


def test_a_packaged_oracle_resolves_and_publishes_from_wheel_and_sdist(
    tmp_path: Path,
) -> None:
    """The production entry reaches a packaged oracle from an installed dist.

    Both artifact types, because they carry package data through different
    metadata: the wheel through ``[tool.setuptools.package-data]`` and the sdist
    through ``MANIFEST.in``. A rule missing from either one is a real
    distribution defect for the accepted-content PR that follows this one.
    """
    staged = _staged_source_tree(tmp_path)
    dist = tmp_path / "dist"
    dist.mkdir()
    wheel, sdist = _build_dists(staged, dist)

    # Runtime resolution first, deliberately: it is the property under test, so
    # it should also be the failure a regression reports. The archive listings
    # below are a diagnostic that says *where* a runtime failure came from.
    for label, artifact in (("wheel", wheel), ("sdist", sdist)):
        target = tmp_path / f"site-{label}"
        _install(artifact, target)
        result = _probe_installed(target, tmp_path)

        assert result["resolved"] is True, f"{label}: {result}"
        assert result["resolved_release"] == SENTINEL_RELEASE, f"{label}: {result}"
        assert str(target) in str(result["oracle_dir"]), f"{label}: {result}"
        # The gate refuses this sentinel — it describes no real projection — but
        # it refuses *having judged it*. ABSENT would mean the installed
        # application could not see the accepted authority at all, which is the
        # defect under test.
        assert result["outcome"] != "absent", f"{label}: {result}"

    sentinel_rel = f"{_ORACLES_REL}/{SENTINEL_FILENAME}"
    with zipfile.ZipFile(wheel) as zf:
        assert any(n.endswith(sentinel_rel) for n in zf.namelist()), zf.namelist()
    with tarfile.open(sdist) as tf:
        assert any(m.name.endswith(f"src/{sentinel_rel}") for m in tf.getmembers()), [
            m.name for m in tf.getmembers() if m.name.endswith(".json")
        ]
