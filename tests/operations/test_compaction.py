"""CRD Issue 22 physical disposal: the rebuilt vector store keeps every
remaining Story-memory and Rules-corpus record exactly (ids, documents,
metadata, embeddings, the embedding-model guard), carries no deleted text in
any file, and an interrupted compaction is resumed -- never served."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

import pytest

from afterworlds.api.app import create_app
from afterworlds.api.config import ApiSettings
from afterworlds.operations import compaction
from afterworlds.operations.compaction import (
    compact_vector_store,
    compaction_unfinished,
)
from afterworlds.pipeline.retrieval.client import build_chroma_client
from afterworlds.pipeline.retrieval.collections import (
    get_existing_rules_corpus_collection,
    get_story_memory_collection,
)
from afterworlds.pipeline.retrieval.config import RetrievalMemoryConfig
from afterworlds.remote.storage import StoreRefused
from tests.operations._data import files_with

MARK = "COMPACTIONERASEMARK"
RULES = "rules_corpus__compaction_test"


def _vec(i: int) -> list[float]:
    return [float((i * 7 + k) % 11) / 10 for k in range(384)]


def _seed(vector_dir: Path, monkeypatch: pytest.MonkeyPatch) -> RetrievalMemoryConfig:
    monkeypatch.setenv("AFTERWORLDS_RETRIEVAL_PERSIST_DIRECTORY", str(vector_dir))
    config = RetrievalMemoryConfig.from_env()
    client = build_chroma_client(config)
    from afterworlds.pipeline.retrieval.collections import get_rules_corpus_collection

    story = get_story_memory_collection(client, config)
    story.add(
        ids=[f"gone-{i}" for i in range(40)] + ["kept-1", "kept-2"],
        documents=[f"{MARK} deleted prose {i}" for i in range(40)]
        + ["kept prose one", "kept prose two"],
        metadatas=[{"story_id": "gone"}] * 40 + [{"story_id": "kept"}] * 2,
        embeddings=[_vec(i) for i in range(42)],
    )
    rules = get_rules_corpus_collection(client, RULES, config)
    rules.add(
        ids=["r1", "r2"],
        documents=["Rule one.", "Rule two."],
        metadatas=[{"package": "p"}, {"package": "p"}],
        embeddings=[_vec(100), _vec(101)],
    )
    story.delete(where={"story_id": "gone"})
    return config


def _snapshot(config: RetrievalMemoryConfig) -> dict[str, Any]:
    client = build_chroma_client(config)
    story = get_story_memory_collection(client, config)
    rules = get_existing_rules_corpus_collection(client, RULES, config)
    assert rules is not None
    out = {}
    for name, col in (("story", story), ("rules", rules)):
        got = col.get(include=["documents", "metadatas", "embeddings"])
        out[name] = sorted(
            zip(
                got["ids"],
                got["documents"],
                [tuple(sorted(m.items())) for m in got["metadatas"]],
                [tuple(round(float(x), 6) for x in e) for e in got["embeddings"]],
                strict=True,
            )
        )
    return out


def _release() -> None:
    import gc

    from chromadb.api.shared_system_client import SharedSystemClient

    SharedSystemClient.clear_system_cache()
    gc.collect()


def test_rebuild_preserves_records_and_guards_and_removes_deleted_text(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    vector_dir = tmp_path / "chroma"
    config = _seed(vector_dir, monkeypatch)
    before = _snapshot(config)
    _release()
    evidence = compact_vector_store(vector_dir, lambda: build_chroma_client(config))
    _release()
    assert evidence["collections"] == {"story_memory": 2, RULES: 2}
    assert files_with(vector_dir, MARK) == []
    assert not compaction_unfinished(vector_dir)
    # The production read/write paths still accept the rebuilt store.
    assert _snapshot(config) == before
    client = build_chroma_client(config)
    get_story_memory_collection(client, config).add(
        ids=["new"],
        documents=["after"],
        metadatas=[{"story_id": "kept"}],
        embeddings=[_vec(5)],
    )
    assert get_story_memory_collection(client, config).count() == 3
    _release()


def test_interrupted_swap_is_refused_then_resumed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    vector_dir = tmp_path / "chroma"
    config = _seed(vector_dir, monkeypatch)
    before = _snapshot(config)
    _release()

    real_tree, real_copy = shutil.copytree, shutil.copy2
    calls = {"n": 0}

    def crash(*args: Any, **kwargs: Any) -> Any:
        calls["n"] += 1
        raise OSError("power loss")

    monkeypatch.setattr(compaction.shutil, "copytree", crash)
    monkeypatch.setattr(compaction.shutil, "copy2", crash)
    with pytest.raises(OSError):
        compact_vector_store(vector_dir, lambda: build_chroma_client(config))
    assert calls["n"] == 1
    # The live store is part-replaced: nothing may serve it.
    assert compaction_unfinished(vector_dir)
    settings = ApiSettings(
        database_url=f"sqlite:///{tmp_path / 'local.db'}",
        frontend_dist_dir=tmp_path / "no_frontend",
    )
    with pytest.raises(StoreRefused, match="compaction did not finish"):
        create_app(settings)
    monkeypatch.setattr(compaction.shutil, "copytree", real_tree)
    monkeypatch.setattr(compaction.shutil, "copy2", real_copy)
    compact_vector_store(vector_dir, lambda: build_chroma_client(config))
    _release()
    assert not compaction_unfinished(vector_dir)
    # Scan before this test process (which read the deleted text) reopens the
    # store: a process that held it must not write the store afterwards.
    assert files_with(vector_dir, MARK) == []
    assert _snapshot(config) == before
    _release()
