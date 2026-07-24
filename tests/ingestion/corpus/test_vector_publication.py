"""Vector persistence + read-back verification tests — Issue 5c, DF1 (PR #134).

Fast tests on small hand-seeded packages (not the full 13k corpus): the actual
Issue 18 rules-corpus reindex is driven against a real isolated Chroma store
with the deterministic offline embedding function, then read back and verified.
Covers: exact expected documents before publication; write failure; empty /
missing / extra / stale document; metadata and embedding-model mismatch; and
the reuse verify-only path against a corrupted collection.
"""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest
from sqlalchemy import update

from afterworlds.ingestion.corpus.vector_publication import (
    VectorDocumentState,
    VectorLogicalState,
    expected_vector_state_from_sql,
    read_actual_vector_state,
    reindex_and_verify,
    verify_only,
    verify_vector_state,
)
from afterworlds.models.enums import SourceLocatorTypeEnum
from afterworlds.models.retrieval import (
    build_rules_corpus_chunk_id,
    rules_corpus_collection_name,
)
from afterworlds.persistence.database import create_engine, create_session_factory
from afterworlds.persistence.orm.base import Base
from afterworlds.persistence.orm.rules_package import (
    RuleChunkORM,
    RuleSourceORM,
    RulesPackageORM,
)
from afterworlds.pipeline.retrieval.client import build_isolated_test_chroma_client
from afterworlds.pipeline.retrieval.collections import get_rules_corpus_collection
from afterworlds.pipeline.retrieval.config import RetrievalMemoryConfig
from afterworlds.pipeline.retrieval.embedding import DeterministicFakeEmbeddingFunction

_NOW = "2026-01-01T00:00:00Z"


@pytest.fixture()
def sql_session():  # type: ignore[no-untyped-def]
    eng = create_engine("sqlite://")
    Base.metadata.create_all(eng)
    sess = create_session_factory(eng)()
    try:
        yield sess
    finally:
        sess.close()
        eng.dispose()


def _config() -> RetrievalMemoryConfig:
    return RetrievalMemoryConfig()


def _ef() -> DeterministicFakeEmbeddingFunction:
    return DeterministicFakeEmbeddingFunction()


def _seed(session, pkg: str, chunk_specs):  # type: ignore[no-untyped-def]
    """chunk_specs: list of (chunk_id, content, locator_value)."""
    session.add(
        RulesPackageORM(
            rules_package_id=pkg,
            name="SRD 5.2.1 Corpus",
            system="d20",
            version="5.2.1-corpus.test",
            is_enabled=True,
            publication_status="draft",
            created_at=_NOW,
            updated_at=_NOW,
        )
    )
    session.flush()
    session.add(
        RuleSourceORM(
            source_id=pkg,
            rules_package_id=pkg,
            name="SRD 5.2.1",
            category="core_rulebook",
            precedence_rank=1,
            is_enabled=True,
            created_at=_NOW,
        )
    )
    session.flush()
    for chunk_id, content, locator in chunk_specs:
        session.add(
            RuleChunkORM(
                chunk_id=chunk_id,
                rules_package_id=pkg,
                source_id=pkg,
                subsystem="general",
                content=content,
                source_document="D&D SRD 5.2.1",
                source_locator_type=SourceLocatorTypeEnum.PAGE.value,
                source_locator_value=locator,
                is_enabled=True,
                created_at=_NOW,
            )
        )
    session.commit()


@pytest.fixture()
def seeded(sql_session):  # type: ignore[no-untyped-def]
    """Return (session, pkg, specs) for a small 2-chunk package."""
    pkg = str(uuid4())
    specs = [
        (str(uuid4()), "Fireball deals fire damage.", "p. 131"),
        (str(uuid4()), "Cure Wounds restores hit points.", "p. 121"),
    ]
    _seed(sql_session, pkg, specs)
    return sql_session, pkg, specs


# --- happy path: exact expected documents written before publication ---------


def test_reindex_writes_exactly_the_expected_documents(seeded, tmp_path):
    session, pkg, specs = seeded
    client = build_isolated_test_chroma_client(str(tmp_path))
    config, ef = _config(), _ef()

    result = reindex_and_verify(session, pkg, client, config, ef)

    assert result.ok, result.failures
    assert result.written == len(specs)
    expected_ids = {
        build_rules_corpus_chunk_id(UUID(pkg), UUID(cid)) for cid, _, _ in specs
    }
    assert {d.doc_id for d in result.state.documents} == expected_ids
    assert result.state.count == len(specs)
    assert result.state.embedding_model_id == config.embedding_model_id


def test_expected_state_matches_actual_after_reindex(seeded, tmp_path):
    session, pkg, _ = seeded
    client = build_isolated_test_chroma_client(str(tmp_path))
    config, ef = _config(), _ef()
    reindex_and_verify(session, pkg, client, config, ef)

    expected = expected_vector_state_from_sql(session, pkg, config)
    actual = read_actual_vector_state(client, pkg, config, ef)
    assert verify_vector_state(expected, actual, config) == ()


# --- verify_vector_state unit tests (fast, no Chroma) ------------------------


def _state(docs, model="chroma-onnx-minilm-l6-v2"):  # type: ignore[no-untyped-def]
    return VectorLogicalState(
        collection_name="rules_corpus_x",
        embedding_model_id=model,
        count=len(docs),
        documents=tuple(sorted(docs, key=lambda d: d.doc_id)),
    )


def _doc(doc_id, content="c", meta=None):  # type: ignore[no-untyped-def]
    return VectorDocumentState(
        doc_id=doc_id, content=content, metadata=meta or {"k": "v"}
    )


def test_verify_passes_on_identical_state():
    exp = _state([_doc("a"), _doc("b")])
    act = _state([_doc("a"), _doc("b")])
    assert verify_vector_state(exp, act, _config()) == ()


def test_verify_flags_missing_document():
    exp = _state([_doc("a"), _doc("b")])
    act = _state([_doc("a")])
    failures = verify_vector_state(exp, act, _config())
    assert any("missing expected document b" in f for f in failures)
    assert any("count" in f for f in failures)


def test_verify_flags_extra_document():
    exp = _state([_doc("a")])
    act = _state([_doc("a"), _doc("b")])
    failures = verify_vector_state(exp, act, _config())
    assert any("unexpected document b" in f for f in failures)


def test_verify_flags_stale_content():
    exp = _state([_doc("a", content="fresh")])
    act = _state([_doc("a", content="stale")])
    failures = verify_vector_state(exp, act, _config())
    assert any("stale/altered content" in f for f in failures)


def test_verify_flags_metadata_mismatch():
    exp = _state([_doc("a", meta={"source_locator_value": "p. 1"})])
    act = _state([_doc("a", meta={"source_locator_value": "p. 999"})])
    failures = verify_vector_state(exp, act, _config())
    assert any("mismatched metadata" in f for f in failures)


def test_verify_flags_embedding_model_mismatch():
    exp = _state([_doc("a")])
    act = _state([_doc("a")], model="some-other-model")
    failures = verify_vector_state(exp, act, _config())
    assert any("embedding_model_id" in f for f in failures)


# --- read-back + failure-injection against real Chroma -----------------------


def test_read_actual_vector_state_missing_collection_is_empty(tmp_path):
    client = build_isolated_test_chroma_client(str(tmp_path))
    state = read_actual_vector_state(client, str(uuid4()), _config(), _ef())
    assert state.count == 0
    assert state.documents == ()


def test_reindex_failure_blocks_with_failures(seeded, tmp_path, monkeypatch):
    session, pkg, _ = seeded
    client = build_isolated_test_chroma_client(str(tmp_path))
    import afterworlds.ingestion.corpus.vector_publication as vp

    def _boom(self, sess, rules_package_id):  # type: ignore[no-untyped-def]
        raise RuntimeError("chroma write exploded")

    monkeypatch.setattr(vp.RulesCorpusService, "reindex_from_sql", _boom)
    result = reindex_and_verify(session, pkg, client, _config(), _ef())
    assert not result.ok
    assert any("reindex failed" in f for f in result.failures)


def test_verify_only_detects_deleted_document(seeded, tmp_path):
    session, pkg, specs = seeded
    client = build_isolated_test_chroma_client(str(tmp_path))
    config, ef = _config(), _ef()

    assert reindex_and_verify(session, pkg, client, config, ef).ok

    # Corrupt the collection: drop one document out from under a "reuse".
    collection = get_rules_corpus_collection(
        client, rules_corpus_collection_name(UUID(pkg)), config, ef
    )
    victim = build_rules_corpus_chunk_id(UUID(pkg), UUID(specs[0][0]))
    collection.delete(ids=[victim])

    result = verify_only(session, pkg, client, config, ef)
    assert not result.ok
    assert any(
        "missing expected document" in f or "count" in f for f in result.failures
    )


def test_verify_only_detects_altered_content(seeded, tmp_path):
    session, pkg, specs = seeded
    client = build_isolated_test_chroma_client(str(tmp_path))
    config, ef = _config(), _ef()
    assert reindex_and_verify(session, pkg, client, config, ef).ok

    collection = get_rules_corpus_collection(
        client, rules_corpus_collection_name(UUID(pkg)), config, ef
    )
    victim = build_rules_corpus_chunk_id(UUID(pkg), UUID(specs[0][0]))
    collection.update(ids=[victim], documents=["TAMPERED CONTENT"])

    result = verify_only(session, pkg, client, config, ef)
    assert not result.ok
    assert any("stale/altered content" in f for f in result.failures)


def test_expected_state_excludes_disabled_source(seeded, tmp_path):
    session, pkg, _ = seeded
    session.execute(
        update(RuleSourceORM)
        .where(RuleSourceORM.rules_package_id == pkg)
        .values(is_enabled=False)
    )
    session.commit()
    expected = expected_vector_state_from_sql(session, pkg, _config())
    assert expected.count == 0
