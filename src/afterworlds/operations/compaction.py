"""Offline physical disposal of deleted content -- CRD Issue 22 matrix
("live-store proof must cover ... WAL/journals and reusable pages, vector
persistence").

A logical delete leaves prose behind: SQLite free pages and WAL frames, and
in embedded Chroma its SQLite free pages, its operation log and HNSW segment
files. Worse, Chroma's HNSW writer can persist bytes from freed process
memory into a freshly built segment, so a rebuild inside a process that ever
read the deleted text can write it back (observed on the pinned chromadb
1.5.9). With the app stopped (the store locks held), :func:`compact_stores`
therefore:

1. checkpoints (TRUNCATE) and VACUUMs the content SQLite;
2. exports every remaining record of every collection (ids, documents,
   metadatas and stored embeddings -- nothing is re-embedded, no Story or
   Rules chunk is lost) from the live vector store;
3. imports it, in a **fresh subprocess** whose memory never held deleted
   text, into a new store beside the live one, which records completion;
4. replaces the live store's contents with the rebuilt ones (keeping its
   deployment marker and serve lock) and removes the export and staging.

Staging (claim, export and rebuilt store) lives inside the live vector
directory, claimed for this store's deployment identity and one operation
before any effect; any other occupant is refused untouched. Steps 3-4 are
crash-safe: this claim's completed rebuild is resumed (its contents are
copied again over whatever an interrupted swap left), its incomplete one is
discarded and rebuilt. Evidence is counts, never content.

Remotely the live control store is checkpointed and VACUUMed too.
"""

from __future__ import annotations

import gc
import json
import os
import shutil
import sqlite3
import stat
import subprocess
import sys
from collections.abc import Callable
from contextlib import closing
from pathlib import Path
from typing import Any
from uuid import uuid4

from chromadb.api import ClientAPI
from chromadb.api.shared_system_client import SharedSystemClient

from afterworlds.remote.storage import (
    VECTOR_LOCK,
    VECTOR_MARKER,
    StoreRefused,
    read_vector_marker,
)

_PAGE = 500
_COMPLETE = ".compaction-complete.json"


def vacuum_sqlite(path: Path) -> dict[str, int]:
    with closing(sqlite3.connect(path)) as conn:
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        conn.execute("VACUUM")
        busy, _log, _ckpt = conn.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()
    if busy:
        # A reader kept old frames in the WAL: nothing is reported disposed.
        raise RuntimeError(f"{path.name}: WAL checkpoint was blocked")
    wal = path.with_name(path.name + "-wal")
    return {
        "checkpoint_busy": int(busy),
        "wal_bytes": wal.stat().st_size if wal.exists() else 0,
    }


#: Staging lives inside the live vector directory -- covered by its serve
#: lock and deployment marker, so no other store's path can be adopted or
#: deleted (review P1-6) -- and is claimed before any effect.
STAGING = ".afterworlds-compaction"
_CLAIM = "claim.json"


def _staging(vector_dir: Path) -> Path:
    return vector_dir / STAGING


def export_vectors(client: ClientAPI, path: Path) -> dict[str, int]:
    """Every remaining record of every collection, written owner-only."""
    collections = []
    counts: dict[str, int] = {}
    for listed in client.list_collections():
        name = listed if isinstance(listed, str) else listed.name
        collection = client.get_collection(name)
        records: dict[str, list[Any]] = {
            "ids": [],
            "documents": [],
            "metadatas": [],
            "embeddings": [],
        }
        offset = 0
        while True:
            page = collection.get(
                include=["documents", "metadatas", "embeddings"],
                limit=_PAGE,
                offset=offset,
            )
            ids = page.get("ids") or []
            if not ids:
                break
            records["ids"] += ids
            blank: list[Any] = [None] * len(ids)
            records["documents"] += list(page.get("documents") or blank)
            records["metadatas"] += list(page.get("metadatas") or blank)
            embeddings: Any = page.get("embeddings")
            records["embeddings"] += [[float(x) for x in e] for e in embeddings]
            offset += len(ids)
        configuration = collection.configuration_json or {}
        collections.append(
            {
                "name": name,
                "metadata": collection.metadata,
                "hnsw": configuration.get("hnsw"),
                "records": records,
            }
        )
        counts[name] = len(records["ids"])
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump(collections, handle)
    return counts


def import_vectors(export: Path, target: Path, operation_id: str) -> dict[str, int]:
    """Build a fresh store from an export. Run only in a fresh process
    (``python -m afterworlds.operations.compaction``)."""
    import chromadb

    from afterworlds.pipeline.retrieval.embedding import (
        resolve_default_embedding_function,
    )

    collections = json.loads(export.read_text(encoding="utf-8"))
    client = chromadb.PersistentClient(path=str(target))
    counts: dict[str, int] = {}
    for item in collections:
        configuration: Any = {"hnsw": item["hnsw"]} if item.get("hnsw") else None
        collection = client.create_collection(
            item["name"],
            metadata=item["metadata"],
            configuration=configuration,
            embedding_function=resolve_default_embedding_function(),  # type: ignore[arg-type]
        )
        records = item["records"]
        for start in range(0, len(records["ids"]), _PAGE):
            end = start + _PAGE
            collection.add(
                ids=records["ids"][start:end],
                documents=records["documents"][start:end],
                metadatas=records["metadatas"][start:end],
                embeddings=records["embeddings"][start:end],
            )
        if collection.count() != len(records["ids"]):
            raise RuntimeError(f"import of {item['name']} is incomplete")
        counts[item["name"]] = collection.count()
    (target / _COMPLETE).write_text(
        json.dumps({"operation_id": operation_id, "counts": counts}), encoding="utf-8"
    )
    return counts


def compaction_unfinished(vector_dir: Path) -> bool:
    """A compaction started and did not finish: its claimed staging (plain
    copies of every remaining record) is still inside the live vector store,
    which may be partly replaced. Nothing may serve or maintain the stores
    until ``compact`` is run again."""
    return os.path.lexists(_staging(vector_dir))


def _clear(directory: Path, keep: set[str]) -> None:
    for entry in directory.iterdir():
        if entry.name in keep:
            continue
        if entry.is_dir() and not entry.is_symlink():
            shutil.rmtree(entry)
        else:
            entry.unlink()


def _read_json(path: Path) -> Any:
    """A regular file's JSON (never through a link), or None."""
    try:
        info = path.lstat()
    except FileNotFoundError:
        return None
    if not stat.S_ISREG(info.st_mode):
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _claim(vector_dir: Path, store_id: str) -> str:
    """This store's claimed staging and its operation ID: an existing claim
    of this store is resumed; anything else at the staging path (no claim, a
    foreign or unreadable one, a link or a file) is refused untouched."""
    staging = _staging(vector_dir)
    if os.path.lexists(staging):
        info = staging.lstat()
        claim = _read_json(staging / _CLAIM) if stat.S_ISDIR(info.st_mode) else None
        if (
            not isinstance(claim, dict)
            or claim.get("store_id") != store_id
            or not isinstance(claim.get("operation_id"), str)
        ):
            raise StoreRefused(
                f"{staging} is not this store's compaction; left untouched"
            )
        return str(claim["operation_id"])
    operation_id = str(uuid4())
    # The claim is written in full under a private name and published by one
    # atomic rename, so the staging path never exists without its proof of
    # ownership (review round 2, F4). An interrupted claim leaves only this
    # content-free directory, which the next swap clears with the rest of
    # the live store's old contents.
    pending = vector_dir / f"{STAGING}-{operation_id}.claiming"
    pending.mkdir()
    fd = os.open(pending / _CLAIM, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump({"store_id": store_id, "operation_id": operation_id}, handle)
    os.rename(pending, staging)
    return operation_id


def _teardown(staging: Path, operation_id: str) -> None:
    """Remove a finished compaction's staging, its claim last: until every
    dependent copy is gone the claim still identifies it for a retry, which
    rebuilds from the (already replaced) live store."""
    rebuilt = staging / "store"
    (rebuilt / _COMPLETE).unlink(missing_ok=True)  # a partial copy is never resumed
    if rebuilt.exists():
        shutil.rmtree(rebuilt)
    (staging / "export.json").unlink(missing_ok=True)
    # Only the claim is left: move it off the staging path in one step.
    finished = staging.with_name(f"{STAGING}-{operation_id}.finished")
    os.rename(staging, finished)
    shutil.rmtree(finished)


def compact_vector_store(
    vector_dir: Path, client_factory: Callable[[], ClientAPI]
) -> dict[str, Any]:
    store_id = read_vector_marker(vector_dir)
    if store_id is None:
        raise StoreRefused("the vector store is not bound to a deployment")
    operation_id = _claim(vector_dir, store_id)
    staging = _staging(vector_dir)
    export, rebuilt = staging / "export.json", staging / "store"
    done = _read_json(rebuilt / _COMPLETE)
    if not (isinstance(done, dict) and done.get("operation_id") == operation_id):
        # This claim's own incomplete work: discard and rebuild.
        if rebuilt.exists():
            shutil.rmtree(rebuilt)
        export.unlink(missing_ok=True)
        exported = export_vectors(client_factory(), export)
        SharedSystemClient.clear_system_cache()
        gc.collect()
        subprocess.run(
            [
                sys.executable,
                "-m",
                "afterworlds.operations.compaction",
                str(export),
                str(rebuilt),
                operation_id,
            ],
            check=True,
            stdout=subprocess.DEVNULL,
        )
        done = _read_json(rebuilt / _COMPLETE)
        if not isinstance(done, dict) or done.get("counts") != exported:
            raise RuntimeError("rebuilt vector store does not match the export")
    SharedSystemClient.clear_system_cache()
    gc.collect()
    _clear(vector_dir, {VECTOR_LOCK, VECTOR_MARKER, STAGING})
    for entry in rebuilt.iterdir():
        if entry.name in (_COMPLETE, VECTOR_MARKER, VECTOR_LOCK, STAGING):
            continue
        if entry.is_dir():
            shutil.copytree(entry, vector_dir / entry.name)
        else:
            shutil.copy2(entry, vector_dir / entry.name)
    _teardown(staging, operation_id)
    return {"collections": done["counts"]}


def compact_stores(
    database_path: Path,
    vector_dir: Path,
    client_factory: Callable[[], ClientAPI],
    control_path: Path | None = None,
) -> dict[str, Any]:
    """Physically dispose of logically deleted content in the live stores
    (app stopped): the content store, the vector store and -- remotely -- the
    control store, whose erased principal, contact, session and verifier rows
    would otherwise survive in free pages or the WAL (review round 2, F5).
    Raises on any failure; evidence otherwise."""
    evidence: dict[str, Any] = {"content": vacuum_sqlite(database_path)}
    if control_path is not None:
        evidence["control"] = vacuum_sqlite(control_path)
    if (vector_dir / "chroma.sqlite3").is_file() or compaction_unfinished(vector_dir):
        evidence["vector"] = compact_vector_store(vector_dir, client_factory)
    return evidence


if __name__ == "__main__":
    import_vectors(Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3])
