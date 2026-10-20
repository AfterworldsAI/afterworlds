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

Steps 3-4 are crash-safe: a completed staging store is resumed (its contents
are copied again over whatever an interrupted swap left), an incomplete one
is discarded and rebuilt. Evidence is counts, never content.
"""

from __future__ import annotations

import gc
import json
import os
import shutil
import sqlite3
import subprocess
import sys
from collections.abc import Callable
from contextlib import closing
from pathlib import Path
from typing import Any

from chromadb.api import ClientAPI
from chromadb.api.shared_system_client import SharedSystemClient

from afterworlds.remote.storage import VECTOR_LOCK, VECTOR_MARKER

_PAGE = 500
_COMPLETE = ".compaction-complete.json"


def vacuum_sqlite(path: Path) -> dict[str, int]:
    with closing(sqlite3.connect(path)) as conn:
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        conn.execute("VACUUM")
        busy, _log, _ckpt = conn.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()
    wal = path.with_name(path.name + "-wal")
    return {
        "checkpoint_busy": int(busy),
        "wal_bytes": wal.stat().st_size if wal.exists() else 0,
    }


def _staging(vector_dir: Path) -> tuple[Path, Path]:
    return (
        vector_dir.with_name(f".{vector_dir.name}.compact-new"),
        vector_dir.with_name(f".{vector_dir.name}.compact-export.json"),
    )


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
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump(collections, handle)
    return counts


def import_vectors(export: Path, target: Path) -> dict[str, int]:
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
    (target / _COMPLETE).write_text(json.dumps(counts), encoding="utf-8")
    return counts


def compaction_unfinished(vector_dir: Path) -> bool:
    """A compaction started and did not finish: its staging store or export
    (plain copies of every remaining record) still exist beside the live
    vector store, which may be partly replaced. Nothing may serve or maintain
    the stores until ``compact`` is run again."""
    staging, export = _staging(vector_dir)
    return staging.exists() or export.exists()


def _clear(directory: Path, keep: set[str]) -> None:
    for entry in directory.iterdir():
        if entry.name in keep:
            continue
        if entry.is_dir() and not entry.is_symlink():
            shutil.rmtree(entry)
        else:
            entry.unlink()


def compact_vector_store(
    vector_dir: Path, client_factory: Callable[[], ClientAPI]
) -> dict[str, Any]:
    staging, export = _staging(vector_dir)
    if not (staging / _COMPLETE).is_file():
        if staging.exists():
            shutil.rmtree(staging)
        exported = export_vectors(client_factory(), export)
        SharedSystemClient.clear_system_cache()
        gc.collect()
        subprocess.run(
            [
                sys.executable,
                "-m",
                "afterworlds.operations.compaction",
                str(export),
                str(staging),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
        )
        imported = json.loads((staging / _COMPLETE).read_text(encoding="utf-8"))
        if imported != exported:
            raise RuntimeError("rebuilt vector store does not match the export")
    SharedSystemClient.clear_system_cache()
    gc.collect()
    imported = json.loads((staging / _COMPLETE).read_text(encoding="utf-8"))
    _clear(vector_dir, {VECTOR_LOCK, VECTOR_MARKER})
    for entry in staging.iterdir():
        if entry.name in (_COMPLETE, VECTOR_MARKER, VECTOR_LOCK):
            continue
        if entry.is_dir():
            shutil.copytree(entry, vector_dir / entry.name)
        else:
            shutil.copy2(entry, vector_dir / entry.name)
    shutil.rmtree(staging)
    export.unlink(missing_ok=True)
    return {"collections": imported}


def compact_stores(
    database_path: Path,
    vector_dir: Path,
    client_factory: Callable[[], ClientAPI],
) -> dict[str, Any]:
    """Physically dispose of logically deleted content in both live stores
    (app stopped). Raises on any failure; evidence otherwise."""
    evidence: dict[str, Any] = {"content": vacuum_sqlite(database_path)}
    if (vector_dir / "chroma.sqlite3").is_file() or _staging(vector_dir)[0].exists():
        evidence["vector"] = compact_vector_store(vector_dir, client_factory)
    return evidence


if __name__ == "__main__":
    import_vectors(Path(sys.argv[1]), Path(sys.argv[2]))
