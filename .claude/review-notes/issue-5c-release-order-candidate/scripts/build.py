"""Build the release from the working tree into a fresh scratch store OUT.

usage: build.py OUT. Mirrors .claude/_rc/build_new.py (itself mirroring
tests/ingestion/conftest.py::source_release_db) but refuses an existing OUT and
deletes nothing. Writes identity.json, leaves.json, containers.json and
afterworlds.db under OUT; nothing shared.
"""

import dataclasses
import hashlib
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, "src")

from sqlalchemy import event  # noqa: E402

from afterworlds.ingestion.corpus.persistence import finalize_source_release  # noqa: E402
from afterworlds.ingestion.corpus.pipeline import build_source_candidate  # noqa: E402
from afterworlds.ingestion.corpus.source_units import CORPUS_FILES  # noqa: E402
from afterworlds.persistence.database import (  # noqa: E402
    create_engine,
    create_session_factory,
)
from afterworlds.persistence.orm.base import Base  # noqa: E402
from afterworlds.pipeline.retrieval.client import (  # noqa: E402
    build_isolated_test_chroma_client,
)
from afterworlds.pipeline.retrieval.config import RetrievalMemoryConfig  # noqa: E402
from afterworlds.pipeline.retrieval.embedding import (  # noqa: E402
    DeterministicFakeEmbeddingFunction,
)

NOW = "2026-10-06T00:00:00Z"
OUT = Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=False)

cand = build_source_candidate(Path("."), retrieval_config=RetrievalMemoryConfig())
db = OUT / "afterworlds.db"
engine = create_engine(f"sqlite:///{db}")


@event.listens_for(engine, "connect")
def _fk(dbapi, _rec):  # type: ignore[no-untyped-def]
    dbapi.execute("PRAGMA foreign_keys=ON")


Base.metadata.create_all(engine)
client = build_isolated_test_chroma_client(tempfile.mkdtemp(prefix="ro-cand-chroma-"))
try:
    with create_session_factory(engine)() as session:
        result = finalize_source_release(
            session,
            cand,
            now=NOW,
            chroma_client=client,
            retrieval_config=RetrievalMemoryConfig(),
            embedding_function=DeterministicFakeEmbeddingFunction(),
        )
finally:
    engine.dispose()
assert result.published and result.artifacts is not None, result.gate
art = result.artifacts
identity = {
    "corpus_files": list(CORPUS_FILES),
    "package_uuid": cand.package_uuid,
    "release_version": cand.release_version,
    "transform_config_hash": cand.transform_config_hash,
    "ledger_hash": cand.ledger_hash,
    "bundle_root_hash": cand.bundle.bundle_root_hash,
    "authoritative_source_hash": cand.authoritative_source_hash,
    "persisted_corpus_digest": art.report.payload.get("persisted_corpus_digest"),
    "units": len(cand.ledger.leaves),
    "containers": len(cand.ledger.containers),
    "chunks": len(cand.members.chunks),
    "citation_report": cand.citation_report.payload() if cand.citation_report else None,
}
(OUT / "identity.json").write_text(json.dumps(identity, indent=1), encoding="utf-8")
chunks = {c.source_leaf_ids[0]: c for c in cand.members.chunks}
assert all(len(c.source_leaf_ids) == 1 for c in cand.members.chunks)
leaves = []
for leaf in cand.ledger.leaves:
    row = dataclasses.asdict(leaf)
    row["content_sha256"] = hashlib.sha256(row.pop("content").encode()).hexdigest()
    c = chunks.get(leaf.leaf_id)
    row["chunk"] = None if c is None else {
        "chunk_id": c.chunk_id,
        "content_sha256": hashlib.sha256(c.content.encode()).hexdigest(),
        "printed_page": c.printed_page,
        "section_label": c.section_label,
        "container_path": list(c.container_path),
        "locator": [c.source_document, c.source_locator_type, c.source_locator_value],
    }
    leaves.append(row)
(OUT / "leaves.json").write_text(json.dumps(leaves, indent=0), encoding="utf-8")
(OUT / "containers.json").write_text(
    json.dumps([dataclasses.asdict(c) for c in cand.ledger.containers], indent=0),
    encoding="utf-8",
)
print(json.dumps({k: v for k, v in identity.items() if k != "citation_report"}, indent=1))
