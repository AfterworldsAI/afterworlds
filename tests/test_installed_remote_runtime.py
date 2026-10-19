"""#205 review 5575759407: the remote runtime works from an installed
distribution, not only from a source checkout.

A wheel and an sdist are built from a staged copy of the project, installed
with ``pip --target`` and exercised in a ``python -S`` subprocess from a neutral
directory (the editable-install finder never registers, so the checkout cannot
be imported -- the probe asserts ``afterworlds.__file__`` is the install).

Both artifacts: both Alembic chains resolve from the install, the exact control
head is discovered, and a remote app starts twice on disposable stores with an
external built-assets directory. The wheel additionally provisions shared Rules
from operator-supplied qualified inputs (a copy of the official PDF and pinned
snapshot outside the checkout) against the packaged accepted oracle, reuses it
on a second run, and refuses missing or tampered inputs.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import sysconfig
from pathlib import Path

import pytest

from afterworlds.ingestion.corpus.pdf_source import PDF_REPO_PATH
from afterworlds.ingestion.corpus.source_ledger import CORPUS_FILES, PIN_DIR

_REPO_ROOT = Path(__file__).resolve().parent.parent

_STARTUP_PROBE = r"""
import gc, json, os, sqlite3, sys, tempfile
from pathlib import Path

import hashlib

import afterworlds
from afterworlds import prompt_contracts
from afterworlds.api import db_bootstrap
from afterworlds.remote import control_store

work = Path(tempfile.mkdtemp(prefix="aw-installed-"))
dist = work / "dist"
dist.mkdir()
(dist / "index.html").write_text("<p>installed assets</p>", encoding="utf-8")
os.environ["AFTERWORLDS_FAKE_PROVIDER"] = "1"
os.environ["AFTERWORLDS_RETRIEVAL_PERSIST_DIRECTORY"] = str(work / "chroma")

from chromadb.api.shared_system_client import SharedSystemClient
from fastapi.testclient import TestClient

from afterworlds.api.app import create_app
from afterworlds.api.config import ApiSettings

settings = ApiSettings(
    database_url=f"sqlite:///{work / 'content.db'}",
    frontend_dist_dir=dist,
    deployment="remote",
    control_database_url=f"sqlite:///{work / 'control.db'}",
    notice_outbox_dir=work / "outbox",
)


def start_and_stop() -> str:
    app = create_app(settings)
    with TestClient(app, base_url="https://testserver") as client:
        page = client.get("/").text
    app.state.session_factory.kw["bind"].dispose()
    app.state.control_factory.kw["bind"].dispose()
    app.state.orchestrator = app.state.rpg_actions = None
    SharedSystemClient.clear_system_cache()
    gc.collect()
    for name in ("control_lock", "vector_lock", "store_lock"):
        handle = getattr(app.state, name, None)
        if handle is not None:
            handle.close()
    return page


first, second = start_and_stop(), start_and_stop()
control_store.connect_control_store(settings.control_database_url).kw["bind"].dispose()


def revisions(db: Path) -> list[str]:
    conn = sqlite3.connect(db)
    try:
        return [r[0] for r in conn.execute("SELECT version_num FROM alembic_version")]
    finally:
        conn.close()


print(json.dumps({
    "module_file": afterworlds.__file__,
    "content_migrations": str(db_bootstrap.CONTENT_MIGRATIONS),
    "control_migrations": str(control_store.CONTROL_MIGRATIONS),
    "control_head": control_store.control_head(),
    "control_revisions": revisions(work / "control.db"),
    "content_revisions": revisions(work / "content.db"),
    "first": first,
    "second": second,
    "prompt_dir": str(prompt_contracts.PROMPT_DIR),
    "prompts": {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(prompt_contracts.PROMPT_DIR.glob("*.md"))
    },
}))
"""

_PROVISION_PROBE = r"""
import gc, json, os, sys, tempfile
from pathlib import Path

import afterworlds
from chromadb.api.shared_system_client import SharedSystemClient

from afterworlds.api.app import create_app
from afterworlds.api.config import ApiSettings
from afterworlds.pipeline.retrieval.embedding import DeterministicFakeEmbeddingFunction
from afterworlds.remote import rules_provisioning

qualified, tampered = Path(sys.argv[1]), Path(sys.argv[2])
work = Path(tempfile.mkdtemp(prefix="aw-installed-rules-"))
env = {
    "AFTERWORLDS_DEPLOYMENT": "remote",
    "AFTERWORLDS_DATABASE_URL": f"sqlite:///{work / 'content.db'}",
    "AFTERWORLDS_CONTROL_DATABASE_URL": f"sqlite:///{work / 'control.db'}",
    "AFTERWORLDS_NOTICE_OUTBOX_DIR": str(work / "outbox"),
    "AFTERWORLDS_FRONTEND_DIST": str(work / "no_frontend"),
    "AFTERWORLDS_RETRIEVAL_PERSIST_DIRECTORY": str(work / "chroma"),
    "AFTERWORLDS_FAKE_PROVIDER": "1",
}
os.environ.update(env)
settings = ApiSettings(
    database_url=env["AFTERWORLDS_DATABASE_URL"],
    frontend_dist_dir=work / "no_frontend",
    deployment="remote",
    control_database_url=env["AFTERWORLDS_CONTROL_DATABASE_URL"],
    notice_outbox_dir=work / "outbox",
)
app = create_app(settings)  # a fresh deployment, then stopped
app.state.session_factory.kw["bind"].dispose()
app.state.control_factory.kw["bind"].dispose()
app.state.orchestrator = app.state.rpg_actions = None
SharedSystemClient.clear_system_cache()
gc.collect()
for name in ("control_lock", "vector_lock", "store_lock"):
    handle = getattr(app.state, name, None)
    if handle is not None:
        handle.close()

rules_provisioning._embedding_function = DeterministicFakeEmbeddingFunction
codes = {
    "default_root": str(rules_provisioning.default_source_root()),
    "no_inputs": rules_provisioning.main([]),
    "tampered": rules_provisioning.main(["--source-root", str(tampered)]),
    "qualified": rules_provisioning.main(["--source-root", str(qualified)]),
    "qualified_again": rules_provisioning.main(["--source-root", str(qualified)]),
}
print(json.dumps({"module_file": afterworlds.__file__, **codes}))
"""


def _stage(tmp_path: Path) -> Path:
    staged = tmp_path / "src-tree"
    staged.mkdir()
    for name in ("pyproject.toml", "MANIFEST.in", "setup.py"):
        shutil.copyfile(_REPO_ROOT / name, staged / name)
    shutil.copytree(_REPO_ROOT / "docs" / "prompts", staged / "docs" / "prompts")
    shutil.copytree(
        _REPO_ROOT / "src",
        staged / "src",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )
    return staged


def _build(source: Path, out_dir: Path) -> tuple[Path, Path]:
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
    assert proc.returncode == 0, proc.stdout + proc.stderr
    [wheel] = list(out_dir.glob("*.whl"))
    [sdist] = list(out_dir.glob("*.tar.gz"))
    return wheel, sdist


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


def _probe(target: Path, cwd: Path, script: str, *args: str) -> dict[str, object]:
    purelib = sysconfig.get_paths()["purelib"]
    env = {**os.environ, "PYTHONPATH": os.pathsep.join([str(target), purelib])}
    for name in list(env):
        if name.startswith("AFTERWORLDS_"):
            del env[name]
    proc = subprocess.run(
        [sys.executable, "-S", "-c", script, *args],
        cwd=str(cwd),
        env=env,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr[-4000:]
    result: dict[str, object] = json.loads(proc.stdout.strip().splitlines()[-1])
    assert str(target) in str(result["module_file"])
    assert str(_REPO_ROOT / "src") not in str(result["module_file"])
    return result


def _qualified_inputs(root: Path) -> Path:
    """A copy of only the qualified Rules inputs, outside the checkout."""
    root.mkdir()
    (root / PDF_REPO_PATH).parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(_REPO_ROOT / PDF_REPO_PATH, root / PDF_REPO_PATH)
    shutil.copytree(_REPO_ROOT / PIN_DIR, root / PIN_DIR)
    return root


@pytest.fixture(scope="module")
def installed(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Path]:
    """Wheel and sdist built once from a staged copy, each installed apart."""
    root = tmp_path_factory.mktemp("installed")
    dist = root / "dist"
    dist.mkdir()
    wheel, sdist = _build(_stage(root), dist)
    targets = {"neutral": root / "neutral"}
    targets["neutral"].mkdir()
    for label, artifact in (("wheel", wheel), ("sdist", sdist)):
        targets[label] = root / f"site-{label}"
        _install(artifact, targets[label])
    return targets


@pytest.mark.parametrize("artifact", ["wheel", "sdist"])
def test_the_remote_runtime_starts_from_an_installed_artifact(
    installed: dict[str, Path], artifact: str
) -> None:
    import hashlib

    target = installed[artifact]
    result = _probe(target, installed["neutral"], _STARTUP_PROBE)
    for key in ("content_migrations", "control_migrations", "prompt_dir"):
        assert str(target) in str(result[key]), result
    assert result["control_revisions"] == [result["control_head"]]
    assert len(result["content_revisions"]) == 1  # type: ignore[arg-type]
    assert "installed assets" in str(result["first"])
    assert "installed assets" in str(result["second"])
    # The shipped prompt contracts are byte-identical to docs/prompts.
    assert result["prompts"] == {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted((_REPO_ROOT / "docs" / "prompts").glob("*.md"))
    }


def test_installed_rules_provisioning_takes_qualified_explicit_inputs(
    installed: dict[str, Path], tmp_path: Path
) -> None:
    qualified = _qualified_inputs(tmp_path / "rules-inputs")
    tampered = _qualified_inputs(tmp_path / "tampered-inputs")
    pinned = tampered / PIN_DIR / CORPUS_FILES[0]  # a file the build reads
    pinned.write_bytes(pinned.read_bytes() + b"\nnot the qualified snapshot\n")
    codes = _probe(
        installed["wheel"],
        installed["neutral"],
        _PROVISION_PROBE,
        str(qualified),
        str(tampered),
    )
    assert codes["default_root"] == "None"  # an installation has no inputs
    assert codes["no_inputs"] == 1
    assert codes["tampered"] == 1
    assert codes["qualified"] == 0
    assert codes["qualified_again"] == 0  # verified reuse / already published
