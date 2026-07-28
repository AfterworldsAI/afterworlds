"""Tests for scripts/reset_corpus_baseline.py — CRD Issue 5c (#132), PR #134 R19.

Codex review: the destructive reset's operator-facing configuration contract must
name the variable the code actually reads. ``RetrievalMemoryConfig.from_env()``
reads ``AFTERWORLDS_RETRIEVAL_PERSIST_DIRECTORY``; the script's documented short
name ``AFTERWORLDS_RETRIEVAL_PERSIST_DIR`` was never read, so an operator who
followed the documented command would have exported an ignored variable and reset
the *default* store instead of the intended one. The mistaken spelling is
corrected, not aliased — these tests pin both halves of that contract.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

import afterworlds.persistence.orm.character_sheet  # noqa: F401
import afterworlds.persistence.orm.corpus  # noqa: F401
import afterworlds.persistence.orm.node  # noqa: F401
import afterworlds.persistence.orm.retrieval  # noqa: F401
import afterworlds.persistence.orm.rules_package  # noqa: F401
import afterworlds.persistence.orm.session_state  # noqa: F401
import afterworlds.persistence.orm.state  # noqa: F401
import afterworlds.persistence.orm.story  # noqa: F401
import afterworlds.persistence.orm.story_bible  # noqa: F401
from afterworlds.persistence.database import create_engine
from afterworlds.persistence.orm.base import Base
from afterworlds.pipeline.retrieval.config import DEFAULT_PERSIST_DIRECTORY

CANONICAL_ENV = "AFTERWORLDS_RETRIEVAL_PERSIST_DIRECTORY"
MISTAKEN_ENV = "AFTERWORLDS_RETRIEVAL_PERSIST_DIR"

_SCRIPT_PATH = (
    Path(__file__).resolve().parents[1] / "scripts" / "reset_corpus_baseline.py"
)


def _load_script():  # type: ignore[no-untyped-def]
    """Import scripts/reset_corpus_baseline.py as a module (scripts/ is not a
    package). Cached in sys.modules so repeated calls don't re-exec it."""
    module_name = "reset_corpus_baseline_script_under_test"
    if module_name in sys.modules:
        return sys.modules[module_name]
    spec = importlib.util.spec_from_file_location(module_name, _SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _empty_db_url(tmp_path) -> str:  # type: ignore[no-untyped-def]
    """A real, schema-created SQLite DB with no published release, so main()
    reaches its idempotent 'store reset only' tail without a rebuild."""
    db_path = tmp_path / "baseline.db"
    url = f"sqlite:///{db_path}"
    engine = create_engine(url)
    Base.metadata.create_all(engine)
    engine.dispose()
    return url


class _Client:
    """Stand-in for the constructed Chroma client (identity is what matters)."""


def _run_main(  # type: ignore[no-untyped-def]
    script, monkeypatch, tmp_path, stub_resolver=True
):
    """Run main() with the *destructive* steps (client construction + store reset)
    recorded instead of performed. The resolver is real unless stubbed, so a test
    can prove the configured target genuinely validates."""
    seen: dict[str, object] = {}

    def fake_resolve(persist_directory):  # type: ignore[no-untyped-def]
        seen["resolved_from"] = persist_directory
        return Path(persist_directory)

    def fake_build_client(config):  # type: ignore[no-untyped-def]
        seen["client_config"] = config
        return _Client()

    def fake_reset(client):  # type: ignore[no-untyped-def]
        seen["reset_client"] = client
        return []

    if stub_resolver:
        monkeypatch.setattr(script, "resolve_reset_target", fake_resolve)
    monkeypatch.setattr(script, "build_chroma_client", fake_build_client)
    monkeypatch.setattr(script, "reset_chroma_store", fake_reset)
    monkeypatch.setattr(
        sys,
        "argv",
        ["reset_corpus_baseline.py", "--db-url", _empty_db_url(tmp_path)],
    )

    assert script.main() == 0
    return seen


def test_canonical_env_var_selects_the_validated_and_reset_target(
    tmp_path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The variable the script documents is the variable that steers the reset:
    the exact configured directory is what the REAL guard validates AND what the
    client the reset runs against is built from — one target, no divergence."""
    script = _load_script()
    target = tmp_path / "isolated_chroma"
    monkeypatch.setenv(CANONICAL_ENV, str(target))

    seen = _run_main(script, monkeypatch, tmp_path, stub_resolver=False)

    # The real resolve_reset_target accepted exactly this target (it would have
    # raised ResetTargetError otherwise) and reports it before anything destructive.
    assert f"Chroma target validated: {target.resolve()}" in capsys.readouterr().out
    assert seen["client_config"].persist_directory == str(target)  # type: ignore[union-attr]
    assert seen["reset_client"] is not None


def test_mistaken_short_name_is_not_an_alias(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The erroneous spelling is corrected, not supported: exporting it alone must
    not redirect the destructive reset (it is simply ignored, as it always was)."""
    script = _load_script()
    monkeypatch.delenv(CANONICAL_ENV, raising=False)
    monkeypatch.setenv(MISTAKEN_ENV, str(tmp_path / "decoy_store"))

    seen = _run_main(script, monkeypatch, tmp_path)

    # Positive, not merely "not the decoy": with the canonical variable unset the
    # script falls through to the documented default, exactly as it always did.
    assert seen["resolved_from"] == DEFAULT_PERSIST_DIRECTORY
    assert seen["client_config"].persist_directory == DEFAULT_PERSIST_DIRECTORY  # type: ignore[union-attr]


def test_usage_documents_only_the_canonical_variable(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """--help must show operators the variable that is actually read. Every
    occurrence of the short name must be a prefix of the canonical one, so the
    counts matching proves the short name never appears on its own."""
    script = _load_script()
    # Pin the width so argparse's textwrap can't split the 40-char name.
    monkeypatch.setenv("COLUMNS", "200")
    monkeypatch.setattr(sys, "argv", ["reset_corpus_baseline.py", "--help"])

    with pytest.raises(SystemExit):
        script.main()

    out = capsys.readouterr().out
    assert CANONICAL_ENV in out
    assert out.count(MISTAKEN_ENV) == out.count(CANONICAL_ENV)
