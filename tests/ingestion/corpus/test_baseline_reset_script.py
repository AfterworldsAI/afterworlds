"""Baseline-reset preflight against the REAL published corpus — PR #134 R23.

The one-time reset command clears the whole Chroma store and rebuilds the rules
corpus from SQLite. Structural checks on the chunk rows are not enough to make
that safe: content, provenance, or a locator can be swapped for another
perfectly valid value and every structural check still passes, so the rebuild
would write a silently wrong projection with the proven one already deleted.

Preflight therefore verifies Issue 5c's own canonical proof — expected vector
logical state built from SQL, persisted-corpus digest recomputed by the
canonical implementation, compared to the digest recorded at publication.
Proving that requires a genuinely proof-bound corpus, so these tests run against
the real full-SRD release persisted into a file-backed SQLite database (built
once per module, copied per test so each mutation is isolated). A hand-built
fixture cannot exercise this: it has no valid digest to match.
"""

from __future__ import annotations

import importlib.util
import shutil
import sys
from pathlib import Path

import pytest
from sqlalchemy import delete as sa_delete
from sqlalchemy import select, update

from afterworlds.ingestion.corpus.persistence import persist_release
from afterworlds.persistence.database import create_engine, create_session_factory
from afterworlds.persistence.orm.base import Base
from afterworlds.persistence.orm.corpus import (
    CorpusProjectionORM,
    CorpusReleaseORM,
    LedgerLeafORM,
)
from afterworlds.persistence.orm.rules_package import RuleChunkORM, RulesPackageORM
from afterworlds.pipeline.retrieval.config import RetrievalMemoryConfig

_NOW = "2026-07-23T00:00:00Z"
_SCRIPT_PATH = (
    Path(__file__).resolve().parents[3] / "scripts" / "reset_corpus_baseline.py"
)


def _load_script():  # type: ignore[no-untyped-def]
    module_name = "reset_corpus_baseline_script_under_test"
    if module_name in sys.modules:
        return sys.modules[module_name]
    spec = importlib.util.spec_from_file_location(module_name, _SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def published_db(tmp_path_factory, full_release):  # type: ignore[no-untyped-def]
    """The real full-SRD release persisted into a file-backed SQLite DB.

    File-backed (not in-memory) because the script opens its own engine from a
    URL. Built once; every test copies it, so mutations never leak between
    tests.
    """
    db_path = tmp_path_factory.mktemp("published") / "afterworlds.db"
    url = f"sqlite:///{db_path}"
    engine = create_engine(url)
    Base.metadata.create_all(engine)
    factory = create_session_factory(engine)
    with factory() as session:
        persist_release(session, full_release, now=_NOW)
        # persist_release writes the draft rows; publication is the flip that
        # finalize_release performs on a passing gate. The command only ever
        # selects *published* releases, so mirror that end state here.
        pkg = full_release.release.package_uuid
        session.execute(
            update(CorpusReleaseORM)
            .where(CorpusReleaseORM.package_uuid == pkg)
            .values(publication_status="published")
        )
        session.execute(
            update(RulesPackageORM)
            .where(RulesPackageORM.rules_package_id == pkg)
            .values(publication_status="published", is_enabled=True, published_at=_NOW)
        )
        session.commit()
    engine.dispose()
    return db_path


@pytest.fixture()
def db_url(published_db, tmp_path):  # type: ignore[no-untyped-def]
    """A private copy of the published DB for this test to mutate freely."""
    copied = tmp_path / "afterworlds.db"
    shutil.copy(published_db, copied)
    return f"sqlite:///{copied}"


class _Client:
    """Stand-in for the constructed Chroma client."""


def _arm(script, monkeypatch, db_url):  # type: ignore[no-untyped-def]
    """Record the destructive steps and the rebuild instead of performing them,
    and return an ordered event trace. The payload proof itself is never stubbed
    — it is what these tests exercise."""
    events: list[str] = []
    reindexed: list[str] = []

    def recording_print(*args, **kwargs):  # type: ignore[no-untyped-def]
        events.append("print: " + " ".join(str(a) for a in args))
        print(*args, **kwargs)

    class _Service:
        def __init__(self, client, config):  # type: ignore[no-untyped-def]
            pass

        def reindex_from_sql(self, session, pkg):  # type: ignore[no-untyped-def]
            reindexed.append(str(pkg))
            return 7

    def fake_build_client(config):  # type: ignore[no-untyped-def]
        events.append("CLIENT")
        return _Client()

    def fake_reset(client):  # type: ignore[no-untyped-def]
        events.append("RESET")
        return []

    monkeypatch.setattr(script, "print", recording_print, raising=False)
    monkeypatch.setattr(script, "resolve_reset_target", lambda p: Path(p))
    monkeypatch.setattr(script, "build_chroma_client", fake_build_client)
    monkeypatch.setattr(script, "reset_chroma_store", fake_reset)
    monkeypatch.setattr(script, "RulesCorpusService", _Service)
    monkeypatch.setattr(sys, "argv", ["reset_corpus_baseline.py", "--db-url", db_url])
    return events, reindexed


def _mutate(db_url, fn):  # type: ignore[no-untyped-def]
    engine = create_engine(db_url)
    factory = create_session_factory(engine)
    with factory() as session:
        fn(session)
        session.commit()
    engine.dispose()


def _first_chunk(session):  # type: ignore[no-untyped-def]
    return (
        session.execute(select(RuleChunkORM).order_by(RuleChunkORM.chunk_id))
        .scalars()
        .first()
    )


def _swap_chunk_content(session):  # type: ignore[no-untyped-def]
    """Replace one chunk's content with a different, perfectly valid string —
    non-empty, right type, right length class. Only the proof can see this."""
    row = _first_chunk(session)
    row.content = "A different but entirely well-formed rule paragraph."


def _swap_locator_value(session):  # type: ignore[no-untyped-def]
    """Repoint one chunk at another syntactically valid page locator."""
    row = _first_chunk(session)
    row.source_locator_value = "999" if row.source_locator_value != "999" else "998"


def test_untampered_published_corpus_passes_preflight_and_rebuilds(
    monkeypatch, db_url, retrieval_config
):  # type: ignore[no-untyped-def]
    """Positive control, and the one that matters most operationally: the gate
    stands between an operator and the one-time reset, so the genuine published
    corpus must pass it and rebuild. A gate that rejected real data would look
    green in every negative test and fail only when someone ran the command."""
    script = _load_script()
    monkeypatch.setenv(
        "AFTERWORLDS_RETRIEVAL_PERSIST_DIRECTORY", str(Path(db_url[10:]).parent / "ch")
    )
    events, reindexed = _arm(script, monkeypatch, db_url)

    assert script.main() == 0
    assert "RESET" in events
    assert len(reindexed) == 1


@pytest.mark.parametrize(
    "tamper",
    [_swap_chunk_content, _swap_locator_value],
    ids=["chunk-content-swapped", "locator-value-swapped"],
)
def test_valid_looking_tamper_fails_before_any_chroma_mutation(
    monkeypatch, db_url, tamper
):  # type: ignore[no-untyped-def]
    """Content or a locator replaced by another *syntactically valid* value —
    invisible to any structural check — is caught by the canonical digest proof,
    and caught early: exit 1 with no client constructed, no reset, no rebuild."""
    script = _load_script()
    monkeypatch.setenv(
        "AFTERWORLDS_RETRIEVAL_PERSIST_DIRECTORY", str(Path(db_url[10:]).parent / "ch")
    )
    _mutate(db_url, tamper)
    events, reindexed = _arm(script, monkeypatch, db_url)

    assert script.main() == 1
    assert "CLIENT" not in events
    assert "RESET" not in events
    assert reindexed == []
    # And rejected for the stated reason — the canonical digest proof, not some
    # incidental structural check that happens to trip.
    assert any(
        "Preflight FAILED" in e and "NOT modified" in e and "digest does not match" in e
        for e in events
    )


def test_proof_completes_before_the_reset(monkeypatch, db_url):  # type: ignore[no-untyped-def]
    """Ordering: the payload is reported validated and materialized before the
    client is constructed and before the store is reset."""
    script = _load_script()
    monkeypatch.setenv(
        "AFTERWORLDS_RETRIEVAL_PERSIST_DIRECTORY", str(Path(db_url[10:]).parent / "ch")
    )
    events, _ = _arm(script, monkeypatch, db_url)

    assert script.main() == 0
    validated_at = next(
        i
        for i, e in enumerate(events)
        if "Preflight OK" in e and "validated and materialized" in e
    )
    assert validated_at < events.index("CLIENT") < events.index("RESET")


def test_digest_proof_is_the_canonical_one_not_a_local_reimplementation(
    published_db, retrieval_config
):  # type: ignore[no-untyped-def]
    """The validator's verdict must be the canonical proof's verdict: it agrees
    with ``verify_persisted_digest`` over the expected-from-SQL vector state on
    the untampered corpus, with no violations of any kind."""
    from afterworlds.ingestion.corpus.persistence import verify_persisted_digest
    from afterworlds.ingestion.corpus.vector_publication import (
        expected_vector_state_from_sql,
    )

    script = _load_script()
    engine = create_engine(f"sqlite:///{published_db}")
    factory = create_session_factory(engine)
    try:
        with factory() as session:
            pkg = (
                session.execute(select(RuleChunkORM.rules_package_id)).scalars().first()
            )
            expected = expected_vector_state_from_sql(
                session, pkg, RetrievalMemoryConfig()
            ).to_payload()
            assert verify_persisted_digest(session, pkg, expected)
            assert (
                script.validate_corpus_payload(session, pkg, RetrievalMemoryConfig())
                == []
            )
    finally:
        engine.dispose()


def _delete_all_chunks(session):  # type: ignore[no-untyped-def]
    session.execute(sa_delete(RuleChunkORM))


def _drop_a_page(session):  # type: ignore[no-untyped-def]
    session.execute(sa_delete(LedgerLeafORM).where(LedgerLeafORM.printed_page == 7))


def _orphan_a_chunk(session):  # type: ignore[no-untyped-def]
    """Remove a chunk's declared projection: runtime reads (and the rebuild)
    would serve a chunk the digest/report never proved."""
    row = _first_chunk(session)
    session.execute(
        sa_delete(CorpusProjectionORM).where(
            CorpusProjectionORM.chunk_id == row.chunk_id
        )
    )


@pytest.mark.parametrize(
    ("corrupt", "expected"),
    [
        (_delete_all_chunks, "no enabled rp_chunks rows"),
        (_drop_a_page, "page"),
        (_orphan_a_chunk, "orphan rp_chunks row"),
    ],
    ids=["chunks-deleted", "incomplete-page-coverage", "orphan-chunk"],
)
def test_structurally_broken_payload_also_fails_before_any_chroma_mutation(
    monkeypatch, db_url, corrupt, expected
):  # type: ignore[no-untyped-def]
    """The coarser failures — a payload that is gone, incomplete, or serving
    unproven rows — are reported precisely (not only as a digest mismatch) and
    still abort before the client is constructed."""
    script = _load_script()
    monkeypatch.setenv(
        "AFTERWORLDS_RETRIEVAL_PERSIST_DIRECTORY", str(Path(db_url[10:]).parent / "ch")
    )
    _mutate(db_url, corrupt)
    events, reindexed = _arm(script, monkeypatch, db_url)

    assert script.main() == 1
    assert "CLIENT" not in events
    assert "RESET" not in events
    assert reindexed == []
    assert any("Preflight FAILED" in e and expected in e for e in events)
