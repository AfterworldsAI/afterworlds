"""Pre-release Chroma baseline-reset tests — CRD Issue 5c (#132), R18.

The one-time reset validates the exact configured target, then deletes **every**
collection through the configured client (never the filesystem, never a name
prefix, no legacy-UUID/collection-name knowledge). These cover the safety guard,
the full reset, and idempotency.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from afterworlds.pipeline.retrieval.baseline_reset import (
    ResetTargetError,
    reset_chroma_store,
    resolve_reset_target,
)
from afterworlds.pipeline.retrieval.client import build_isolated_test_chroma_client


def test_resolve_reset_target_accepts_a_configured_store_dir(tmp_path):
    target = resolve_reset_target(str(tmp_path / "chroma"))
    assert target.is_absolute()
    assert target == (tmp_path / "chroma").resolve()


def test_resolve_reset_target_refuses_empty():
    with pytest.raises(ResetTargetError):
        resolve_reset_target("")
    with pytest.raises(ResetTargetError):
        resolve_reset_target("   ")


def test_resolve_reset_target_refuses_filesystem_root():
    root = Path(Path.cwd().anchor)  # e.g. "C:\\" or "/"
    with pytest.raises(ResetTargetError):
        resolve_reset_target(str(root))


def test_resolve_reset_target_refuses_home_and_cwd():
    with pytest.raises(ResetTargetError):
        resolve_reset_target(str(Path.home()))
    with pytest.raises(ResetTargetError):
        resolve_reset_target(str(Path.cwd()))
    # An ancestor of the CWD (e.g. a repo root when run from a subdir) is refused.
    with pytest.raises(ResetTargetError):
        resolve_reset_target(str(Path.cwd().parent))


def test_reset_wipes_every_collection_regardless_of_name(tmp_path):
    """Regression 3/4: arbitrary pre-baseline collections (any names) are wiped in
    full — no legacy-UUID or collection-name knowledge is used to select them."""
    client = build_isolated_test_chroma_client(str(tmp_path / "chroma"))
    names = [
        "rules_corpus_deadbeef",
        "arbitrary-interim",
        "story_memory_x",
        "misc123",
    ]
    for name in names:
        client.create_collection(name)
    assert len(client.list_collections()) == 4

    deleted = reset_chroma_store(client)

    assert sorted(deleted) == sorted(names)
    assert client.list_collections() == []


def test_reset_is_idempotent_on_empty_store(tmp_path):
    """Regression 5: resetting an empty (fresh) store is a no-op, and re-running is
    safe."""
    client = build_isolated_test_chroma_client(str(tmp_path / "chroma"))
    assert reset_chroma_store(client) == []
    client.create_collection("only-one")
    assert reset_chroma_store(client) == ["only-one"]
    assert reset_chroma_store(client) == []  # re-run: still a no-op
