"""Bounded runner checks; the coverage comparison uses a tiny isolated project."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts import run_focused_tests as runner


@pytest.fixture
def workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    (tmp_path / "changed.py").write_text("value = 1\n", encoding="utf-8")
    (tmp_path / "test_sample.py").write_text(
        "def test_ok():\n    assert True\n", encoding="utf-8"
    )
    monkeypatch.setattr(runner, "ROOT", tmp_path)
    return tmp_path


@pytest.mark.parametrize("black_exit,pytest_exit", [(0, 0), (0, 1), (0, 5), (1, 0)])
def test_order_exit_and_diagnostic_label(
    workspace: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    black_exit: int,
    pytest_exit: int,
) -> None:
    calls: list[list[str]] = []

    def run(command: list[str], *, cwd: Path, check: bool) -> SimpleNamespace:
        assert cwd == workspace
        assert check is False
        calls.append(command)
        return SimpleNamespace(
            returncode=black_exit if len(calls) == 1 else pytest_exit
        )

    monkeypatch.setattr(subprocess, "run", run)
    code = runner.main(["--check", "changed.py", "test_sample.py::test_ok"])
    assert calls[0] == [
        sys.executable,
        "-m",
        "black",
        "--check",
        "changed.py",
        "test_sample.py",
    ]
    output = capsys.readouterr().out
    assert runner.LABEL in output
    if black_exit:
        assert len(calls) == 1
        assert code == black_exit
        assert "pytest was not started" in output
    else:
        assert calls[1] == [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "--no-cov",
            "test_sample.py::test_ok",
        ]
        assert code == pytest_exit
        assert ("diagnostics PASSED" in output) == (pytest_exit == 0)


@pytest.mark.parametrize("target", [".", "missing.py", "../outside.py"])
def test_invalid_or_broad_selection_never_launches_tools(
    workspace: Path, monkeypatch: pytest.MonkeyPatch, target: str
) -> None:
    def unexpected(*args: object, **kwargs: object) -> None:
        pytest.fail("invalid selection launched a tool")

    monkeypatch.setattr(subprocess, "run", unexpected)
    with pytest.raises(SystemExit) as error:
        runner.main(["--check", "changed.py", target])
    assert error.value.code == 2


def test_focused_selection_does_not_remove_default_coverage_gate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    project = Path(__file__).resolve().parents[1]
    (tmp_path / "pyproject.toml").write_bytes((project / "pyproject.toml").read_bytes())
    source = tmp_path / "src" / "afterworlds"
    source.mkdir(parents=True)
    (source / "sample.py").write_text(
        "def unused():\n    a = 1\n    b = 2\n    c = 3\n    return a + b + c\n",
        encoding="utf-8",
    )
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "test_sample.py").write_text(
        "import runpy\n\n\ndef test_import():\n"
        '    runpy.run_path("src/afterworlds/sample.py")\n',
        encoding="utf-8",
    )
    monkeypatch.delenv("PYTEST_ADDOPTS", raising=False)
    monkeypatch.setattr(runner, "ROOT", tmp_path)
    assert (
        runner.main(["--check", "src/afterworlds/sample.py", "tests/test_sample.py"])
        == 0
    )
    assert runner.LABEL in capsys.readouterr().out
    assert not (tmp_path / ".coverage").exists()

    full = subprocess.run(
        [sys.executable, "-m", "pytest", "-q"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=os.environ.copy(),
        check=False,
    )
    assert full.returncode == 1, full.stdout + full.stderr
    assert "1 passed" in full.stdout
    assert "Required test coverage of 80% not reached" in full.stdout
    assert (tmp_path / ".coverage").exists()
