"""Content late in a long chunk is actually retrievable -- CRD Issue 5c/5d.

The bounded-window derivation is only worth anything if a query for something
buried at the end of a long unit finds that unit. That cannot be shown with the
deterministic fake embedding function: its vectors are SHA256-derived, so
nearest-neighbour order carries no meaning and any "match" is an artifact. These
tests therefore run the **real** local ONNX MiniLM function -- the production
default -- through the production path: ``reindex_from_sql`` writes, and
``diagnostic_query`` reads and hydrates.

They skip, loudly, when the ONNX model is not cached locally. A skipped proof is
reported as a proof that did not run; it is never replaced with a fake-embedder
substitute that would pass for the wrong reason.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

import pytest

from afterworlds.models.enums import SourceLocatorTypeEnum
from afterworlds.models.retrieval import rules_corpus_collection_name
from afterworlds.persistence.database import create_session_factory
from afterworlds.persistence.orm.corpus import CorpusReleaseORM
from afterworlds.persistence.orm.rules_package import (
    RuleChunkORM,
    RuleSourceORM,
    RulesPackageORM,
)
from afterworlds.pipeline.retrieval.client import build_isolated_test_chroma_client
from afterworlds.pipeline.retrieval.collections import get_rules_corpus_collection
from afterworlds.pipeline.retrieval.config import RetrievalMemoryConfig
from afterworlds.pipeline.retrieval.corpus_windows import (
    derive_retrieval_documents,
    derive_windows,
    visible_text,
)
from afterworlds.pipeline.retrieval.rules_corpus_service import RulesCorpusService

_NOW = datetime(2026, 1, 1, tzinfo=UTC).isoformat()

MODEL_PATH = Path.home() / ".cache/chroma/onnx_models/all-MiniLM-L6-v2/onnx/model.onnx"

real_embedder_only = pytest.mark.skipif(
    not MODEL_PATH.exists(),
    reason=(
        f"ONNX MiniLM model not cached at {MODEL_PATH}; the late-content "
        "retrieval proof needs the real embedding function and will not be "
        "run against the deterministic fake"
    ),
)


def _table(rows: list[str], caption: str) -> str:
    body = "\n".join(f"    <tr><td>{row}</td></tr>" for row in rows)
    return f"**{caption}**\n\n<table>\n  <tbody>\n{body}\n  </tbody>\n</table>"


#: Three long units, each with its own distinctive fact placed at the very end,
#: well past the 256-token ceiling of the whole text.
#:
#: The captions, labels and filler rows are deliberately identical-in-kind and
#: say nothing about the late facts. An earlier version of this fixture named the
#: units Weapons/Trinkets/Bard, and truncated whole-content embedding retrieved
#: all three late facts correctly -- from the caption alone, which sits in the
#: first few tokens. The fixture has to make the late content the *only* thing
#: that distinguishes the three units, or it proves nothing about reading past
#: the ceiling.
LATE_FACTS = {
    "a": (
        "Table A",
        "Reference > Table A",
        "Thundercleft Halberd, two-handed reach weapon, 1d12 slashing",
    ),
    "b": (
        "Table B",
        "Reference > Table B",
        "A tarnished brass spyglass that only shows yesterday's sky",
    ),
    "c": (
        "Table C",
        "Reference > Table C",
        "Superior Inspiration grants two uses of Words of Creation",
    ),
}


def _seed_long_package(session, package_id):  # type: ignore[no-untyped-def]
    """Seed one package of three long chunks plus one short one, published."""
    session.add(
        RulesPackageORM(
            rules_package_id=str(package_id),
            name="Windowing Fixture",
            system="dnd5e",
            version="1.0",
            created_at=_NOW,
            updated_at=_NOW,
            publication_status="published",
            is_enabled=True,
        )
    )
    session.flush()
    source_id = str(uuid4())
    session.add(
        RuleSourceORM(
            source_id=source_id,
            rules_package_id=str(package_id),
            name="Fixture Source",
            category="core",
            precedence_rank=1,
            created_at=_NOW,
        )
    )
    session.flush()

    ids: dict[str, str] = {}
    for key, (caption, label, late) in LATE_FACTS.items():
        # Identical filler in all three units: the shared prefix is what the
        # truncated embedding used to see, and it discriminates nothing.
        rows = [f"Ordinary reference entry number {index}" for index in range(120)]
        rows.append(late)
        chunk_id = str(uuid4())
        ids[key] = chunk_id
        session.add(
            RuleChunkORM(
                chunk_id=chunk_id,
                rules_package_id=str(package_id),
                source_id=source_id,
                subsystem="general",
                content=_table(rows, caption),
                source_document="fixture.md",
                source_locator_type=SourceLocatorTypeEnum.PAGE.value,
                source_locator_value="p. 1",
                source_section_label=label,
                is_enabled=True,
                created_at=_NOW,
            )
        )
    ids["short"] = str(uuid4())
    session.add(
        RuleChunkORM(
            chunk_id=ids["short"],
            rules_package_id=str(package_id),
            source_id=source_id,
            subsystem="general",
            content="A short unit about nothing in particular.",
            source_document="fixture.md",
            source_locator_type=SourceLocatorTypeEnum.PAGE.value,
            source_locator_value="p. 2",
            source_section_label="Appendix",
            is_enabled=True,
            created_at=_NOW,
        )
    )
    session.add(
        CorpusReleaseORM(
            package_uuid=str(package_id),
            release_version="v1",
            authoritative_source_hash="0" * 64,
            transform_config_hash="0" * 64,
            bundle_root_hash="0" * 64,
            ledger_hash="0" * 64,
            policy_hash="0" * 64,
            reconciliation_hash="0" * 64,
            transform_config={},
            publication_status="published",
            created_at=_NOW,
        )
    )
    session.commit()
    return ids


@pytest.fixture()
def session_factory(engine):  # type: ignore[no-untyped-def]
    return create_session_factory(engine)


# ---------------------------------------------------------------------------
# The derivation itself
# ---------------------------------------------------------------------------


def test_derived_documents_cover_the_whole_chunk_and_name_their_chunk() -> None:
    """Mapping back is by durable chunk_id in metadata, not by parsing the ID."""
    package_id = uuid4()
    chunk_id = uuid4()

    class _Row:
        pass

    row = _Row()
    row.chunk_id = str(chunk_id)  # type: ignore[attr-defined]
    row.subsystem = "general"  # type: ignore[attr-defined]
    row.content = _table(  # type: ignore[attr-defined]
        [f"Entry {index}" for index in range(60)], "Things"
    )
    row.source_document = "fixture.md"  # type: ignore[attr-defined]
    row.source_locator_type = "page"  # type: ignore[attr-defined]
    row.source_locator_value = "p. 7"  # type: ignore[attr-defined]
    row.source_section_label = "Chapter > Things"  # type: ignore[attr-defined]

    documents = derive_retrieval_documents(row, package_id, "model-x")  # type: ignore[arg-type]

    assert len(documents) > 1
    assert [doc_id for doc_id, _, _ in documents] == [
        f"rules:{package_id}:chunk:{chunk_id}:w{index}"
        for index in range(len(documents))
    ]
    assert all(
        metadata.source_chunk_id == str(chunk_id)
        and metadata.window_count == len(documents)
        and metadata.window_index == index
        and metadata.embedding_model_id == "model-x"
        and metadata.source_locator_value == "p. 7"
        for index, (_, _, metadata) in enumerate(documents)
    )
    recovered = " ".join(text for _, text, _ in documents).split()
    label_words = ["Chapter", ">", "Things"]
    stripped = [word for word in recovered if word not in label_words]
    assert stripped == [
        word
        for word in visible_text(row.content).split()  # type: ignore[attr-defined]
        if word not in label_words
    ]


def test_derivation_is_deterministic() -> None:
    content = _table([f"Entry {index}" for index in range(90)], "Things")
    first = derive_windows(content, "A > B")
    assert first == derive_windows(content, "A > B")
    assert first != derive_windows(content, "A > C")


# ---------------------------------------------------------------------------
# Retrieval, through the real embedding function
# ---------------------------------------------------------------------------


@real_embedder_only
@pytest.mark.parametrize("key", sorted(LATE_FACTS))
def test_a_query_for_late_content_retrieves_the_chunk_that_holds_it(
    session_factory, tmp_path: Path, key: str
) -> None:
    """The point of the whole change, one long unit at a time.

    Each fact sits at the end of a unit whose full text is thousands of tokens
    -- far past where the embedding function stops reading. The query asks for
    the fact; the answer must be the unit that contains it, hydrated whole.
    """
    session = session_factory()
    package_id = uuid4()
    ids = _seed_long_package(session, package_id)
    client = build_isolated_test_chroma_client(str(tmp_path))
    config = RetrievalMemoryConfig()

    # No embedding_function argument: resolve_default_embedding_function gives
    # the real production ONNX MiniLM, which is the whole point here.
    service = RulesCorpusService(client, config)
    written = service.reindex_from_sql(session, package_id)
    assert written > len(ids)

    _, _, late = LATE_FACTS[key]
    results = service.diagnostic_query(session, package_id, late, n_results=2)

    assert results, "no diagnostic results at all"
    assert late in results[0], results[0][:200]
    # Hydrated to the authoritative unit, not the derived window.
    expected = session.get(RuleChunkORM, ids[key])
    assert results[0] == expected.content


@real_embedder_only
def test_the_same_query_finds_nothing_late_when_whole_content_is_embedded(
    session_factory, tmp_path: Path
) -> None:
    """Negative control: the defect, reproduced beside the fix.

    Writes the unwindowed documents the old code wrote, into its own collection,
    with the same real embedding function, and asks the same question. The late
    fact is not found -- which is what makes the test above evidence of the
    windowing rather than of the query happening to be easy.
    """
    session = session_factory()
    package_id = uuid4()
    ids = _seed_long_package(session, package_id)
    client = build_isolated_test_chroma_client(str(tmp_path))
    config = RetrievalMemoryConfig()

    collection = get_rules_corpus_collection(
        client, rules_corpus_collection_name(package_id), config
    )
    rows = [session.get(RuleChunkORM, chunk_id) for chunk_id in ids.values()]
    collection.upsert(
        ids=[str(row.chunk_id) for row in rows],
        documents=[row.content for row in rows],
    )

    found_at_top = 0
    for key, (_, _, late) in LATE_FACTS.items():
        result = collection.query(query_texts=[late], n_results=1)
        top = (result.get("ids") or [[]])[0]
        found_at_top += bool(top) and top[0] == ids[key]
    # Truncated embeddings cannot reliably distinguish three units whose first
    # 256 tokens are near-identical filler; at least one query must land wrong.
    assert found_at_top < len(LATE_FACTS), (
        "whole-content embedding retrieved every late fact correctly, so this "
        "fixture no longer demonstrates the truncation defect"
    )


@real_embedder_only
def test_hydration_deduplicates_windows_of_one_chunk(
    session_factory, tmp_path: Path
) -> None:
    """Several windows of one unit must not fill the result list with it."""
    session = session_factory()
    package_id = uuid4()
    ids = _seed_long_package(session, package_id)
    client = build_isolated_test_chroma_client(str(tmp_path))
    service = RulesCorpusService(client, RetrievalMemoryConfig())
    service.reindex_from_sql(session, package_id)

    results = service.diagnostic_query(
        session, package_id, "Ordinary reference entry number 40", n_results=3
    )
    assert len(results) == len(set(results))
    contents = {
        session.get(RuleChunkORM, chunk_id).content for chunk_id in ids.values()
    }
    assert all(result in contents for result in results)


@real_embedder_only
def test_a_disabled_chunk_is_not_served_from_the_vector_copy(
    session_factory, tmp_path: Path
) -> None:
    """SQL is ground truth on the read path too, not only the write path."""
    session = session_factory()
    package_id = uuid4()
    ids = _seed_long_package(session, package_id)
    client = build_isolated_test_chroma_client(str(tmp_path))
    service = RulesCorpusService(client, RetrievalMemoryConfig())
    service.reindex_from_sql(session, package_id)

    _, _, late = LATE_FACTS["b"]
    assert service.diagnostic_query(session, package_id, late, n_results=1)

    row = session.get(RuleChunkORM, ids["b"])
    row.is_enabled = False
    session.commit()

    survivors = service.diagnostic_query(session, package_id, late, n_results=3)
    assert all(row.content != result for result in survivors)


@real_embedder_only
def test_reindex_and_query_are_idempotent(session_factory, tmp_path: Path) -> None:
    """A second rebuild writes the same documents and answers the same way."""
    session = session_factory()
    package_id = uuid4()
    _seed_long_package(session, package_id)
    client = build_isolated_test_chroma_client(str(tmp_path))
    service = RulesCorpusService(client, RetrievalMemoryConfig())

    first = service.reindex_from_sql(session, package_id)
    stored_first = set(
        get_rules_corpus_collection(
            client, rules_corpus_collection_name(package_id), RetrievalMemoryConfig()
        ).get()["ids"]
    )
    second = service.reindex_from_sql(session, package_id)
    stored_second = set(
        get_rules_corpus_collection(
            client, rules_corpus_collection_name(package_id), RetrievalMemoryConfig()
        ).get()["ids"]
    )

    assert first == second == len(stored_first) == len(stored_second)
    assert stored_first == stored_second
    assert all(UUID(doc_id.split(":")[3]) for doc_id in stored_first)
