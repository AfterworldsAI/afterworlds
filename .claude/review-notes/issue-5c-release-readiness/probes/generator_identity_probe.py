"""Read-only probe: do historical generators reproduce current-release identities?

Builds the current source release into a private temp SQLite file and Chroma
directory (as tests/ingestion/conftest.py source_release_db does), runs the
classes and rules-glossary-completion generators over it, and compares each
proposal identity with the 8781 oracle's batch identity, the Owner-accepted
rebound identity, and the historical (3fe-chain) identity. Writes nothing in
the repository.
"""

import importlib.util
import json
import sys
import tempfile
from pathlib import Path

REPO = Path.cwd()
sys.path.insert(0, str(REPO))
from sqlalchemy import event  # noqa: E402

from afterworlds.ingestion.corpus.persistence import finalize_source_release  # noqa: E402
from afterworlds.ingestion.corpus.pipeline import build_source_candidate  # noqa: E402
from afterworlds.ingestion.mechanical.oracle import (  # noqa: E402
    COMMITTED_ORACLE_DIR,
    load_accepted_inputs,
)
from afterworlds.ingestion.mechanical.proposal import proposal_identity  # noqa: E402
from afterworlds.persistence.database import create_engine, create_session_factory  # noqa: E402
from afterworlds.persistence.orm.base import Base  # noqa: E402
from afterworlds.pipeline.retrieval.client import build_isolated_test_chroma_client  # noqa: E402
from afterworlds.pipeline.retrieval.config import RetrievalMemoryConfig  # noqa: E402
from afterworlds.pipeline.retrieval.embedding import DeterministicFakeEmbeddingFunction  # noqa: E402

NOTES = REPO / ".claude" / "review-notes"
HISTORICAL = {
    b: i
    for b, i, _ in __import__(
        "tests.ingestion.mechanical._replacement_chain", fromlist=["REPLACEMENT"]
    ).REPLACEMENT.BATCHES
}
REBOUND = {
    b["batch_id"]: b["proposal_identity"]
    for b in json.loads(
        (NOTES / "issue-5c-release-order-recording/accepted-new-proposal-identities.json").read_text("utf-8")
    )["batches"]
}
CURRENT = {
    b.batch_id: b.proposal_identity
    for b in load_accepted_inputs(
        COMMITTED_ORACLE_DIR / "srd-5-2-1-corpus-8781d4e0-a3b.json"
    ).batches
}


def load(name: str, path: Path):  # type: ignore[no-untyped-def]
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


db = Path(tempfile.mkdtemp(prefix="probe-release-")) / "afterworlds.db"
engine = create_engine(f"sqlite:///{db}")
event.listen(engine, "connect", lambda c, _r: c.execute("PRAGMA foreign_keys=ON"))
Base.metadata.create_all(engine)
factory = create_session_factory(engine)
candidate = build_source_candidate(REPO, retrieval_config=RetrievalMemoryConfig())
with factory() as session:
    result = finalize_source_release(
        session,
        candidate,
        now="2026-07-23T00:00:00Z",
        chroma_client=build_isolated_test_chroma_client(tempfile.mkdtemp(prefix="probe-chroma-")),
        retrieval_config=RetrievalMemoryConfig(),
        embedding_function=DeterministicFakeEmbeddingFunction(),
    )
assert result.published
with factory() as session:
    for batch, gen, fn in (
        ("classes", "issue-5d-classes-generator.py", "build"),
        ("class-option-catalogues", "issue-5d-classes-generator.py", "build_options"),
        ("rules-glossary-completion", "issue-5d-rules-glossary-completion-generator.py", "build"),
    ):
        built = getattr(load(gen.replace("-", "_")[:-3], NOTES / gen), fn)(session)
        got = proposal_identity(built.proposal)
        print(batch, "binding", built.binding.release_version)
        print("  built      ", got)
        print("  current    ", CURRENT.get(batch), got == CURRENT.get(batch))
        print("  rebound    ", REBOUND.get(batch), got == REBOUND.get(batch))
        print("  historical ", HISTORICAL.get(batch), got == HISTORICAL.get(batch))
engine.dispose()
