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
STORE_ID = "11111111-2222-3333-4444-555555555555"
RULES = "rules_corpus__compaction_test"


def _vec(i: int) -> list[float]:
    return [float((i * 7 + k) % 11) / 10 for k in range(384)]


def _seed(vector_dir: Path, monkeypatch: pytest.MonkeyPatch) -> RetrievalMemoryConfig:
    monkeypatch.setenv("AFTERWORLDS_RETRIEVAL_PERSIST_DIRECTORY", str(vector_dir))
    config = RetrievalMemoryConfig.from_env()
    client = build_chroma_client(config)
    from afterworlds.pipeline.retrieval.collections import get_rules_corpus_collection
    from afterworlds.remote.storage import bind_vector_store

    bind_vector_store(vector_dir, STORE_ID)

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


def test_local_deployment_refuses_store_maintenance(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    from afterworlds.operations import maintenance

    monkeypatch.setenv("AFTERWORLDS_DEPLOYMENT", "local")
    monkeypatch.setenv("AFTERWORLDS_DATABASE_URL", f"sqlite:///{tmp_path / 'l.db'}")
    monkeypatch.setenv("AFTERWORLDS_FRONTEND_DIST", str(tmp_path))
    monkeypatch.setenv("AFTERWORLDS_RETRIEVAL_PERSIST_DIRECTORY", str(tmp_path / "c"))
    for command in ("compact", "enforce-restore", "finalize"):
        assert maintenance.main([command]) == 1
        assert "remote deployment" in capsys.readouterr().err
    assert not (tmp_path / "l.db").exists()


@pytest.mark.parametrize("occupant", ["unclaimed", "foreign", "file"])
def test_unproven_staging_is_refused_untouched(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, occupant: str
) -> None:
    """Review P1-6: only this store's own claimed staging is resumed or
    removed; anything else at the staging path stays exactly as it was."""
    import json

    from afterworlds.operations.compaction import STAGING

    vector_dir = tmp_path / "chroma"
    config = _seed(vector_dir, monkeypatch)
    before = _snapshot(config)
    _release()
    staging = vector_dir / STAGING
    if occupant == "file":
        staging.write_text("someone else's file", encoding="utf-8")
    else:
        (staging / "store").mkdir(parents=True)
        (staging / "store" / "precious.bin").write_bytes(b"other data")
        if occupant == "foreign":
            (staging / "claim.json").write_text(
                json.dumps({"store_id": "another-store", "operation_id": "x"}),
                encoding="utf-8",
            )
    snapshot = sorted(str(p.relative_to(tmp_path)) for p in tmp_path.rglob("*"))
    with pytest.raises(StoreRefused, match="not this store's compaction"):
        compact_vector_store(vector_dir, lambda: build_chroma_client(config))
    assert sorted(str(p.relative_to(tmp_path)) for p in tmp_path.rglob("*")) == snapshot
    if occupant != "file":
        assert (staging / "store" / "precious.bin").read_bytes() == b"other data"
    _release()
    assert _snapshot(config) == before
    _release()


def test_unbound_vector_store_is_refused(tmp_path: Path) -> None:
    (tmp_path / "plain").mkdir()
    with pytest.raises(StoreRefused, match="not bound"):
        compact_vector_store(tmp_path / "plain", lambda: None)  # type: ignore[arg-type,return-value]


def _leftovers(vector_dir: Path) -> list[str]:
    from afterworlds.operations.compaction import STAGING

    return sorted(p.name for p in vector_dir.iterdir() if p.name.startswith(STAGING))


@pytest.mark.parametrize("crash_at", ["claim_write", "claim_publish"])
def test_interrupted_claim_never_strands_recovery(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, crash_at: str
) -> None:
    """Review round 2, F4: the staging path is published only with its full
    claim; an interrupted claim blocks nothing and the retry completes."""
    vector_dir = tmp_path / "chroma"
    config = _seed(vector_dir, monkeypatch)
    before = _snapshot(config)
    _release()
    target = compaction.json if crash_at == "claim_write" else compaction.os
    name = "dump" if crash_at == "claim_write" else "rename"
    real = getattr(target, name)

    def crash(*args: Any, **kwargs: Any) -> Any:
        if crash_at == "claim_write":
            args[1].write('{"store_id": ')  # a torn claim
        raise OSError("power loss")

    monkeypatch.setattr(target, name, crash)
    with pytest.raises(OSError):
        compact_vector_store(vector_dir, lambda: build_chroma_client(config))
    monkeypatch.setattr(target, name, real)
    assert not compaction_unfinished(vector_dir)  # nothing was published
    compact_vector_store(vector_dir, lambda: build_chroma_client(config))
    _release()
    assert _leftovers(vector_dir) == []
    assert files_with(vector_dir, MARK) == []
    assert _snapshot(config) == before
    _release()


@pytest.mark.parametrize("crash_at", ["rebuilt_copy", "claim_removal"])
def test_interrupted_teardown_keeps_its_claim_and_resumes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, crash_at: str
) -> None:
    """Review round 2, F4: teardown removes the claim last, so a crash while
    removing the dependent copies or the claim still leaves this store's
    claimed staging, refused service and resumed by the next ``compact``."""
    vector_dir = tmp_path / "chroma"
    config = _seed(vector_dir, monkeypatch)
    before = _snapshot(config)
    _release()
    real_rmtree, real_rename = compaction.shutil.rmtree, compaction.os.rename

    def rmtree(path: Any, *args: Any, **kwargs: Any) -> Any:
        tree = Path(path)
        # Teardown: the completion record is already gone, the claim is not.
        if (
            crash_at == "rebuilt_copy"
            and tree.name == "store"
            and (tree.parent / "claim.json").exists()
            and not (tree / ".compaction-complete.json").exists()
        ):
            raise OSError("power loss")
        return real_rmtree(path, *args, **kwargs)

    def rename(src: Any, dst: Any) -> Any:
        if crash_at == "claim_removal" and str(dst).endswith(".finished"):
            raise OSError("power loss")
        return real_rename(src, dst)

    monkeypatch.setattr(compaction.shutil, "rmtree", rmtree)
    monkeypatch.setattr(compaction.os, "rename", rename)
    with pytest.raises(OSError):
        compact_vector_store(vector_dir, lambda: build_chroma_client(config))
    monkeypatch.setattr(compaction.shutil, "rmtree", real_rmtree)
    monkeypatch.setattr(compaction.os, "rename", real_rename)
    assert compaction_unfinished(vector_dir)
    settings = ApiSettings(
        database_url=f"sqlite:///{tmp_path / 'local.db'}",
        frontend_dist_dir=tmp_path / "no_frontend",
    )
    with pytest.raises(StoreRefused, match="compaction did not finish"):
        create_app(settings)
    compact_vector_store(vector_dir, lambda: build_chroma_client(config))
    _release()
    assert _leftovers(vector_dir) == []
    assert files_with(vector_dir, MARK) == []
    assert _snapshot(config) == before
    _release()
