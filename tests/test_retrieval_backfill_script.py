"""Tests for scripts/retrieval_backfill.py — CRD Issue 18 / ADR-018 D4/D7.

Codex review (PR #119): the manual recovery CLI must derive its
RetrievalMemoryConfig from the same environment the running application
reads, not dataclass defaults -- otherwise reindex/backfill/delete run
through this script can recreate the exact embedding-model mismatch they
were meant to fix.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from uuid import uuid4

import pytest

from afterworlds.pipeline.retrieval.client import build_isolated_test_chroma_client
from afterworlds.pipeline.retrieval.collections import get_story_memory_collection
from afterworlds.pipeline.retrieval.config import RetrievalMemoryConfig
from afterworlds.pipeline.retrieval.embedding import DeterministicFakeEmbeddingFunction
from afterworlds.pipeline.retrieval.write_service import RetrievalMemoryWriteService

_SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "retrieval_backfill.py"


def _load_script():  # type: ignore[no-untyped-def]
    """Import scripts/retrieval_backfill.py as a module (scripts/ is not a
    package). Cached in sys.modules so repeated calls don't re-exec it."""
    module_name = "retrieval_backfill_script_under_test"
    if module_name in sys.modules:
        return sys.modules[module_name]
    spec = importlib.util.spec_from_file_location(module_name, _SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


class TestBuildEffectiveConfig:
    def test_honors_env_embedding_model_id(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        script = _load_script()
        monkeypatch.setenv("AFTERWORLDS_RETRIEVAL_EMBEDDING_MODEL_ID", "env-model-x")

        config = script.build_effective_config(None)

        assert config.embedding_model_id == "env-model-x"

    def test_honors_env_chunk_ceiling(self, monkeypatch: pytest.MonkeyPatch) -> None:
        script = _load_script()
        monkeypatch.setenv("AFTERWORLDS_RETRIEVAL_CHUNK_CHAR_CEILING", "1234")

        config = script.build_effective_config(None)

        assert config.chunk_char_ceiling == 1234

    def test_chroma_path_overrides_only_persist_directory(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        script = _load_script()
        monkeypatch.setenv("AFTERWORLDS_RETRIEVAL_EMBEDDING_MODEL_ID", "env-model-y")
        monkeypatch.setenv("AFTERWORLDS_RETRIEVAL_CHUNK_CHAR_CEILING", "999")

        config = script.build_effective_config("/explicit/override/path")

        assert config.persist_directory == "/explicit/override/path"
        assert config.embedding_model_id == "env-model-y"
        assert config.chunk_char_ceiling == 999

    def test_none_chroma_path_uses_env_persist_directory(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        script = _load_script()
        monkeypatch.setenv(
            "AFTERWORLDS_RETRIEVAL_PERSIST_DIRECTORY", "/env/derived/path"
        )

        config = script.build_effective_config(None)

        assert config.persist_directory == "/env/derived/path"

    def test_parse_args_chroma_path_defaults_to_none(self) -> None:
        script = _load_script()
        old_argv = sys.argv
        try:
            sys.argv = ["retrieval_backfill.py", "--story-id", str(uuid4())]
            args = script.parse_args()
        finally:
            sys.argv = old_argv

        assert args.chroma_path is None


class TestEnvConfiguredReindexMatchesAppConfig:
    """Integration proof tying fix #1 (delete-only bypass) and fix #2
    (env-derived CLI config) together: after a recovery script reindex
    using env-derived config, the application's own env-derived config must
    see a compatible (not mismatched) collection."""

    def test_app_config_after_recovery_reindex_sees_compatible_collection(
        self, tmp_path, monkeypatch: pytest.MonkeyPatch  # type: ignore[no-untyped-def]
    ) -> None:
        monkeypatch.setenv(
            "AFTERWORLDS_RETRIEVAL_EMBEDDING_MODEL_ID", "shared-env-model"
        )
        monkeypatch.setenv("AFTERWORLDS_RETRIEVAL_PERSIST_DIRECTORY", str(tmp_path))

        # "Recovery script" side: builds config the same way the CLI does.
        recovery_config = RetrievalMemoryConfig.from_env()
        client = build_isolated_test_chroma_client(str(tmp_path))
        ef = DeterministicFakeEmbeddingFunction()
        recovery_write_service = RetrievalMemoryWriteService(
            client, recovery_config, ef
        )
        recovery_write_service.ingest_turn(
            uuid4(), uuid4(), None, "rpg", "Recovered prose.", "t1"
        )

        # "Application" side: builds its own config independently from the
        # same environment and must see a compatible collection, not a
        # RetrievalCollectionReindexRequiredError.
        app_config = RetrievalMemoryConfig.from_env()
        app_collection = get_story_memory_collection(client, app_config, ef)

        assert app_collection.metadata.get("embedding_model_id") == "shared-env-model"
