"""One-time pre-release Chroma baseline reset — CRD Issue 5c (#132), R18.

Owner decision (Issue 5c Rev7 / Issue 18 Rev6): Afterworlds is pre-release, so the
configured development ChromaDB store is reset **in full, once** before the
corrected rules corpus is indexed — no selective per-collection legacy cleanup, no
legacy-UUID handoff, no prefix-based deletion.

This is an **explicit one-time remediation step** (see
``scripts/reset_corpus_baseline.py``), never automatic startup behavior — resetting
on ordinary startup could later erase valid user data.

Safety: the reset only ever deletes **Chroma collections through the configured
client** (never the filesystem, never ``rmtree``, never a name prefix), so it
cannot escape the configured store. Before any destructive action the configured
target is resolved and validated by :func:`resolve_reset_target`, which refuses an
empty/unresolved path, a filesystem root, the home directory, or the current
working directory / an ancestor of it (which would include a repository checkout).
"""

from __future__ import annotations

from pathlib import Path

from chromadb.api import ClientAPI

from afterworlds.pipeline.retrieval.collections import (
    delete_collection_ignoring_absence,
)


class ResetTargetError(RuntimeError):
    """Raised when the configured Chroma target is unsafe to reset — fail closed."""


def resolve_reset_target(persist_directory: str) -> Path:
    """Resolve *persist_directory* to an absolute path and validate it is safe.

    Refuses (rather than proceeds on) a suspicious target: empty/whitespace, a
    filesystem root, the home directory, or the current working directory or any
    ancestor of it (a repository checkout resolves under the CWD in development).
    Returns the resolved absolute path on success.
    """
    if not persist_directory or not persist_directory.strip():
        raise ResetTargetError("empty/blank Chroma persist_directory")

    target = Path(persist_directory).expanduser().resolve()

    if target == Path(target.anchor):
        raise ResetTargetError(f"refusing a filesystem-root Chroma target: {target}")

    home = Path.home().resolve()
    cwd = Path.cwd().resolve()
    if target in (home, cwd):
        raise ResetTargetError(
            f"refusing to reset a store at the home/current directory: {target}"
        )
    # An ancestor of the CWD (e.g. a repo root when run from a subdirectory) is far
    # too broad a target to reset.
    if target in cwd.parents:
        raise ResetTargetError(
            f"refusing to reset a store at an ancestor of the CWD: {target}"
        )
    return target


def reset_chroma_store(client: ClientAPI) -> list[str]:
    """Delete **every** collection in *client* — a full store reset.

    Enumerates ``list_collections()`` and deletes each through the client (no
    filesystem access, no name-prefix filter). Returns the deleted collection names
    (empty on an already-empty store, so re-running is idempotent).
    """
    names = [c.name for c in client.list_collections()]
    for name in names:
        delete_collection_ignoring_absence(client, name)
    return names
