"""Tests for scripts/ci_test_shards.py: the CI shards are the whole suite."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

_SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "ci_test_shards.py"


def _load() -> ModuleType:
    spec = importlib.util.spec_from_file_location("ci_test_shards", _SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def project(tmp_path: Path) -> Path:
    (tmp_path / "pytest.ini").write_text("[pytest]\n")
    (tmp_path / "test_prefixed.py").write_text("def test_one():\n    pass\n")
    (tmp_path / "suffixed_test.py").write_text("def test_two():\n    pass\n")
    (tmp_path / "helper.py").write_text("def test_not_collected():\n    pass\n")
    return tmp_path


def test_every_collected_file_is_in_exactly_one_shard(project: Path) -> None:
    shards = _load()
    selected = [shards.main(["2", str(index)], root=project) for index in (0, 1)]
    assert sorted(selected) == ["suffixed_test.py", "test_prefixed.py"]


def test_an_empty_shard_is_refused(project: Path) -> None:
    with pytest.raises(SystemExit, match="shard 2 of 3 is empty"):
        _load().main(["3", "2"], root=project)


def test_a_collection_failure_is_refused(project: Path) -> None:
    (project / "test_broken.py").write_text("def test_(:\n")
    with pytest.raises(SystemExit, match="pytest collection failed"):
        _load().main(["2", "0"], root=project)
