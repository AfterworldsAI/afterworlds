"""Tests for RulesCorpusService — CRD Issue 18 / ADR-018 D10/D11.

Covers reindex-from-SQL-ground-truth and the diagnostic-only contract: no
runtime pass may consume this service (verified structurally by absence of
any import from a pass service, not just by a passing test — see the
docstring on ``test_no_pass_service_imports_rules_corpus_service``).
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest
from chromadb.errors import NotFoundError
from sqlalchemy import delete, select

import afterworlds.pipeline.retrieval.rules_corpus_service as rcs_module
from afterworlds.models.enums import SourceLocatorTypeEnum
from afterworlds.models.retrieval import rules_corpus_collection_name
from afterworlds.persistence.database import create_session_factory
from afterworlds.persistence.orm.rules_package import (
    RuleChunkORM,
    RuleSourceORM,
    RulesPackageORM,
)
from afterworlds.pipeline.retrieval.client import build_isolated_test_chroma_client
from afterworlds.pipeline.retrieval.collections import get_rules_corpus_collection
from afterworlds.pipeline.retrieval.config import RetrievalMemoryConfig
from afterworlds.pipeline.retrieval.embedding import DeterministicFakeEmbeddingFunction
from afterworlds.pipeline.retrieval.rules_corpus_service import RulesCorpusService

_NOW = datetime(2026, 1, 1, tzinfo=UTC).isoformat()


def _seed_package_with_explicit_chunks(
    session, package_id, chunk_specs  # type: ignore[no-untyped-def]
):
    """Like _seed_package_with_chunks but with full control over chunk_id
    and source_locator_value per chunk. chunk_specs is a list of
    (chunk_id, content, locator_value) tuples, inserted in list order."""
    session.add(
        RulesPackageORM(
            rules_package_id=str(package_id),
            name="Test SRD",
            system="dnd5e",
            version="1.0",
            created_at=_NOW,
            updated_at=_NOW,
        )
    )
    session.flush()
    source_id = str(uuid4())
    session.add(
        RuleSourceORM(
            source_id=source_id,
            rules_package_id=str(package_id),
            name="Test Source",
            category="core",
            precedence_rank=1,
            created_at=_NOW,
        )
    )
    session.flush()
    for chunk_id, content, locator_value in chunk_specs:
        session.add(
            RuleChunkORM(
                chunk_id=str(chunk_id),
                rules_package_id=str(package_id),
                source_id=source_id,
                subsystem="combat",
                content=content,
                source_document="srd.json",
                source_locator_type=SourceLocatorTypeEnum.PAGE.value,
                source_locator_value=locator_value,
                is_enabled=True,
                created_at=_NOW,
            )
        )
    session.commit()
    return source_id


@pytest.fixture()
def session_factory(engine):  # type: ignore[no-untyped-def]
    return create_session_factory(engine)


def _seed_package_with_chunks(session, package_id, chunk_contents):  # type: ignore[no-untyped-def]
    # Flushed in separate steps (package, then source, then chunks): SQLAlchemy's
    # unit-of-work dependency sort does not reliably order this schema's
    # multi-FK chain (rp_chunks -> rp_packages AND rp_chunks -> rp_sources
    # composite) within a single flush spanning all three new parent/child
    # rows — confirmed via raw-SQL insert working fine in the same order.
    session.add(
        RulesPackageORM(
            rules_package_id=str(package_id),
            name="Test SRD",
            system="dnd5e",
            version="1.0",
            created_at=_NOW,
            updated_at=_NOW,
        )
    )
    session.flush()
    source_id = str(uuid4())
    session.add(
        RuleSourceORM(
            source_id=source_id,
            rules_package_id=str(package_id),
            name="Test Source",
            category="core",
            precedence_rank=1,
            created_at=_NOW,
        )
    )
    session.flush()
    for i, content in enumerate(chunk_contents):
        session.add(
            RuleChunkORM(
                chunk_id=str(uuid4()),
                rules_package_id=str(package_id),
                source_id=source_id,
                subsystem="combat",
                content=content,
                source_document="srd.json",
                source_locator_type=SourceLocatorTypeEnum.PAGE.value,
                source_locator_value=f"p. {i}",
                is_enabled=True,
                created_at=_NOW,
            )
        )
    session.commit()


class TestReindexFromSql:
    def test_reindex_writes_all_enabled_chunks(
        self, session_factory, tmp_path: Path
    ) -> None:  # type: ignore[no-untyped-def]
        session = session_factory()
        package_id = uuid4()
        _seed_package_with_chunks(
            session, package_id, ["Fireball deals damage.", "Shield blocks."]
        )

        client = build_isolated_test_chroma_client(str(tmp_path))
        config = RetrievalMemoryConfig()
        service = RulesCorpusService(
            client, config, DeterministicFakeEmbeddingFunction()
        )

        written = service.reindex_from_sql(session, package_id)

        assert written == 2
        results = service.diagnostic_query(
            package_id, "Fireball deals damage.", n_results=1
        )
        assert results == ["Fireball deals damage."]

    def test_disabled_chunks_excluded(
        self, session_factory, tmp_path: Path
    ) -> None:  # type: ignore[no-untyped-def]
        session = session_factory()
        package_id = uuid4()
        _seed_package_with_chunks(session, package_id, ["Enabled chunk."])
        # Add a disabled chunk directly.
        session.add(
            RuleChunkORM(
                chunk_id=str(uuid4()),
                rules_package_id=str(package_id),
                source_id=session.execute(select(RuleSourceORM.source_id)).scalar_one(),
                subsystem="combat",
                content="Disabled chunk.",
                source_document="srd.json",
                source_locator_type=SourceLocatorTypeEnum.PAGE.value,
                source_locator_value="p. 99",
                is_enabled=False,
                created_at=_NOW,
            )
        )
        session.commit()

        client = build_isolated_test_chroma_client(str(tmp_path))
        config = RetrievalMemoryConfig()
        service = RulesCorpusService(
            client, config, DeterministicFakeEmbeddingFunction()
        )

        written = service.reindex_from_sql(session, package_id)
        assert written == 1

    def test_reindex_wipes_prior_state(self, session_factory, tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
        session = session_factory()
        package_id = uuid4()
        _seed_package_with_chunks(session, package_id, ["First version."])

        client = build_isolated_test_chroma_client(str(tmp_path))
        config = RetrievalMemoryConfig()
        service = RulesCorpusService(
            client, config, DeterministicFakeEmbeddingFunction()
        )
        service.reindex_from_sql(session, package_id)

        # Simulate a chunk being removed from SQL ground truth, then reindex.
        session.execute(
            delete(RuleChunkORM).where(RuleChunkORM.rules_package_id == str(package_id))
        )
        session.commit()
        existing_source_id = session.execute(
            select(RuleSourceORM.source_id).where(
                RuleSourceORM.rules_package_id == str(package_id)
            )
        ).scalar_one()
        session.add(
            RuleChunkORM(
                chunk_id=str(uuid4()),
                rules_package_id=str(package_id),
                source_id=existing_source_id,
                subsystem="combat",
                content="Only surviving chunk.",
                source_document="srd.json",
                source_locator_type=SourceLocatorTypeEnum.PAGE.value,
                source_locator_value="p. 0",
                is_enabled=True,
                created_at=_NOW,
            )
        )
        session.commit()

        written = service.reindex_from_sql(session, package_id)
        assert written == 1
        results = service.diagnostic_query(package_id, "surviving", n_results=10)
        assert results == ["Only surviving chunk."]


class TestReindexPropagatesWipeFailure:
    """Codex review (PR #119) round 7: reindex_from_sql() must ignore only a
    genuinely absent collection when wiping -- an operational Chroma
    failure (locked/corrupt store, permission error) must propagate and
    must abort before get_rules_corpus_collection()/upsert() ever runs, so
    stale disabled/deleted chunks can never remain silently retrievable
    after a supposed rebuild."""

    def test_operational_delete_failure_propagates(
        self, session_factory, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:  # type: ignore[no-untyped-def]
        session = session_factory()
        package_id = uuid4()
        _seed_package_with_chunks(session, package_id, ["Some content."])
        client = build_isolated_test_chroma_client(str(tmp_path))
        config = RetrievalMemoryConfig()
        service = RulesCorpusService(
            client, config, DeterministicFakeEmbeddingFunction()
        )
        service.reindex_from_sql(session, package_id)  # creates the collection

        def _boom(name: str) -> None:
            raise RuntimeError("store locked")

        monkeypatch.setattr(client, "delete_collection", _boom)

        with pytest.raises(RuntimeError, match="store locked"):
            service.reindex_from_sql(session, package_id)

    def test_operational_delete_failure_skips_get_collection_and_upsert(
        self, session_factory, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:  # type: ignore[no-untyped-def]
        session = session_factory()
        package_id = uuid4()
        _seed_package_with_chunks(session, package_id, ["Some content."])
        client = build_isolated_test_chroma_client(str(tmp_path))
        config = RetrievalMemoryConfig()
        service = RulesCorpusService(
            client, config, DeterministicFakeEmbeddingFunction()
        )

        def _boom(name: str) -> None:
            raise RuntimeError("store locked")

        monkeypatch.setattr(client, "delete_collection", _boom)

        import afterworlds.pipeline.retrieval.rules_corpus_service as rcs_module

        get_collection_calls: list[object] = []
        monkeypatch.setattr(
            rcs_module,
            "get_rules_corpus_collection",
            lambda *a, **k: get_collection_calls.append(1),
        )

        with pytest.raises(RuntimeError, match="store locked"):
            service.reindex_from_sql(session, package_id)

        assert get_collection_calls == []

    def test_stale_chunks_remain_visible_not_silently_hidden_after_failed_wipe(
        self, session_factory, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:  # type: ignore[no-untyped-def]
        session = session_factory()
        package_id = uuid4()
        _seed_package_with_chunks(session, package_id, ["Stale content."])
        client = build_isolated_test_chroma_client(str(tmp_path))
        config = RetrievalMemoryConfig()
        service = RulesCorpusService(
            client, config, DeterministicFakeEmbeddingFunction()
        )
        service.reindex_from_sql(session, package_id)

        def _boom(name: str) -> None:
            raise RuntimeError("store locked")

        monkeypatch.setattr(client, "delete_collection", _boom)
        with pytest.raises(RuntimeError, match="store locked"):
            service.reindex_from_sql(session, package_id)

        # The old collection is untouched -- the failure is loud (an
        # exception), not a silently-empty or silently-stale "success".
        results = service.diagnostic_query(package_id, "Stale content.", n_results=1)
        assert results == ["Stale content."]

    def test_absent_collection_is_ignored_and_reindex_rebuilds_normally(
        self, session_factory, tmp_path: Path
    ) -> None:  # type: ignore[no-untyped-def]
        """The expected no-op case: no prior collection exists at all."""
        session = session_factory()
        package_id = uuid4()
        _seed_package_with_chunks(session, package_id, ["Fresh content."])
        client = build_isolated_test_chroma_client(str(tmp_path))
        config = RetrievalMemoryConfig()
        service = RulesCorpusService(
            client, config, DeterministicFakeEmbeddingFunction()
        )

        written = service.reindex_from_sql(session, package_id)

        assert written == 1
        assert service.diagnostic_query(package_id, "Fresh content.", n_results=1) == [
            "Fresh content."
        ]


class TestRulesCorpusIdStability:
    """Codex review (PR #119) round 4: rules-corpus Chroma IDs must derive
    from RuleChunkORM.chunk_id (durable SQL identity), not a per-run
    occurrence index over (locator_type, locator_value) -- that ordinal
    depended on SQL row-iteration order, so it could reassign different
    Chroma IDs to the same SQL ground truth across reindex runs."""

    def _stored_ids(self, client, package_id, config, ef):  # type: ignore[no-untyped-def]
        collection_name = rules_corpus_collection_name(package_id)
        collection = get_rules_corpus_collection(client, collection_name, config, ef)
        return set(collection.get()["ids"])

    def test_same_locator_different_chunk_ids_produce_distinct_stable_ids(
        self, session_factory, tmp_path: Path
    ) -> None:  # type: ignore[no-untyped-def]
        session = session_factory()
        package_id = uuid4()
        chunk_id_a, chunk_id_b = uuid4(), uuid4()
        # Both chunks share the same source locator -- the exact shape the
        # old per-locator ordinal existed to handle, but must not collide on.
        _seed_package_with_explicit_chunks(
            session,
            package_id,
            [
                (chunk_id_a, "First half of the page.", "p. 72"),
                (chunk_id_b, "Second half of the page.", "p. 72"),
            ],
        )

        client = build_isolated_test_chroma_client(str(tmp_path))
        config = RetrievalMemoryConfig()
        ef = DeterministicFakeEmbeddingFunction()
        service = RulesCorpusService(client, config, ef)
        written = service.reindex_from_sql(session, package_id)

        assert written == 2
        ids = self._stored_ids(client, package_id, config, ef)
        assert len(ids) == 2
        assert f"rules:{package_id}:chunk:{chunk_id_a}" in ids
        assert f"rules:{package_id}:chunk:{chunk_id_b}" in ids

    def test_reindex_in_reversed_insertion_order_produces_same_id_set(
        self, session_factory, tmp_path: Path
    ) -> None:  # type: ignore[no-untyped-def]
        client = build_isolated_test_chroma_client(str(tmp_path))
        config = RetrievalMemoryConfig()
        ef = DeterministicFakeEmbeddingFunction()
        chunk_id_a, chunk_id_b = uuid4(), uuid4()

        session_forward = session_factory()
        package_id = uuid4()
        _seed_package_with_explicit_chunks(
            session_forward,
            package_id,
            [
                (chunk_id_a, "Content A.", "p. 1"),
                (chunk_id_b, "Content B.", "p. 1"),
            ],
        )
        service = RulesCorpusService(client, config, ef)
        service.reindex_from_sql(session_forward, package_id)
        ids_forward = self._stored_ids(client, package_id, config, ef)

        # Delete and re-insert the same two chunk_ids/content in reversed
        # order -- genuinely changes on-disk row order, not just a relabel.
        session_forward.execute(
            delete(RuleChunkORM).where(RuleChunkORM.rules_package_id == str(package_id))
        )
        session_forward.commit()
        existing_source_id = session_forward.execute(
            select(RuleSourceORM.source_id).where(
                RuleSourceORM.rules_package_id == str(package_id)
            )
        ).scalar_one()
        session_forward.add(
            RuleChunkORM(
                chunk_id=str(chunk_id_b),
                rules_package_id=str(package_id),
                source_id=existing_source_id,
                subsystem="combat",
                content="Content B.",
                source_document="srd.json",
                source_locator_type=SourceLocatorTypeEnum.PAGE.value,
                source_locator_value="p. 1",
                is_enabled=True,
                created_at=_NOW,
            )
        )
        session_forward.add(
            RuleChunkORM(
                chunk_id=str(chunk_id_a),
                rules_package_id=str(package_id),
                source_id=existing_source_id,
                subsystem="combat",
                content="Content A.",
                source_document="srd.json",
                source_locator_type=SourceLocatorTypeEnum.PAGE.value,
                source_locator_value="p. 1",
                is_enabled=True,
                created_at=_NOW,
            )
        )
        session_forward.commit()

        service.reindex_from_sql(session_forward, package_id)
        ids_reversed = self._stored_ids(client, package_id, config, ef)

        assert ids_forward == ids_reversed

    def test_adding_sibling_locator_row_does_not_change_existing_ids(
        self, session_factory, tmp_path: Path
    ) -> None:  # type: ignore[no-untyped-def]
        session = session_factory()
        package_id = uuid4()
        chunk_id_a, chunk_id_b = uuid4(), uuid4()
        _seed_package_with_explicit_chunks(
            session,
            package_id,
            [
                (chunk_id_a, "First half.", "p. 5"),
                (chunk_id_b, "Second half.", "p. 5"),
            ],
        )
        client = build_isolated_test_chroma_client(str(tmp_path))
        config = RetrievalMemoryConfig()
        ef = DeterministicFakeEmbeddingFunction()
        service = RulesCorpusService(client, config, ef)
        service.reindex_from_sql(session, package_id)
        id_a_before = f"rules:{package_id}:chunk:{chunk_id_a}"
        ids_before = self._stored_ids(client, package_id, config, ef)
        assert id_a_before in ids_before

        # Add a third chunk sharing the same locator, reindex again.
        chunk_id_c = uuid4()
        source_id = session.execute(select(RuleSourceORM.source_id)).scalar_one()
        session.add(
            RuleChunkORM(
                chunk_id=str(chunk_id_c),
                rules_package_id=str(package_id),
                source_id=source_id,
                subsystem="combat",
                content="Third chunk, same locator.",
                source_document="srd.json",
                source_locator_type=SourceLocatorTypeEnum.PAGE.value,
                source_locator_value="p. 5",
                is_enabled=True,
                created_at=_NOW,
            )
        )
        session.commit()
        service.reindex_from_sql(session, package_id)
        ids_after_add = self._stored_ids(client, package_id, config, ef)

        assert id_a_before in ids_after_add
        assert len(ids_after_add) == 3

        # Remove the added chunk, reindex again -- id_a must still be stable.
        session.execute(
            delete(RuleChunkORM).where(RuleChunkORM.chunk_id == str(chunk_id_c))
        )
        session.commit()
        service.reindex_from_sql(session, package_id)
        ids_after_remove = self._stored_ids(client, package_id, config, ef)

        assert id_a_before in ids_after_remove
        assert len(ids_after_remove) == 2

    def test_reindex_uses_shared_id_builder_not_local_formula(
        self, session_factory, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:  # type: ignore[no-untyped-def]
        session = session_factory()
        package_id = uuid4()
        _seed_package_with_chunks(session, package_id, ["Some content."])

        calls: list[tuple[object, object]] = []
        import afterworlds.pipeline.retrieval.rules_corpus_service as rcs_module

        original = rcs_module.build_rules_corpus_chunk_id

        def _spy(pkg_id, chunk_id):  # type: ignore[no-untyped-def]
            calls.append((pkg_id, chunk_id))
            return original(pkg_id, chunk_id)

        monkeypatch.setattr(rcs_module, "build_rules_corpus_chunk_id", _spy)

        client = build_isolated_test_chroma_client(str(tmp_path))
        config = RetrievalMemoryConfig()
        service = RulesCorpusService(
            client, config, DeterministicFakeEmbeddingFunction()
        )
        service.reindex_from_sql(session, package_id)

        assert len(calls) == 1
        assert calls[0][0] == package_id


class _FailOnNthUpsertCollection:
    """Wraps a real Chroma collection; the Nth ``upsert`` call raises.

    Everything else (``get``, ``count``, ``query``) delegates to the real
    collection, so batches before the Nth genuinely land — letting a test prove
    that a mid-rebuild failure with earlier batches already written is
    compensated (the whole attempt collection is removed)."""

    def __init__(self, real, fail_on_call: int) -> None:  # type: ignore[no-untyped-def]
        self._real = real
        self._fail_on_call = fail_on_call
        self.upsert_calls = 0

    def upsert(self, **kwargs):  # type: ignore[no-untyped-def]
        self.upsert_calls += 1
        if self.upsert_calls == self._fail_on_call:
            raise RuntimeError(f"upsert batch {self.upsert_calls} failed")
        return self._real.upsert(**kwargs)

    def __getattr__(self, name):  # type: ignore[no-untyped-def]
        return getattr(self._real, name)


def _collection_absent(client, package_id) -> bool:  # type: ignore[no-untyped-def]
    """True iff the rules_corpus collection was removed (not merely emptied)."""
    name = rules_corpus_collection_name(package_id)
    try:
        client.get_collection(name=name)
        return False
    except NotFoundError:
        return True


def _patch_get_collection_failing_on_batch(
    monkeypatch, fail_on_call: int  # type: ignore[no-untyped-def]
):
    """Make get_rules_corpus_collection return a wrapper that fails on the Nth
    upsert; return the original function so a test can read back the real store."""
    real_get = rcs_module.get_rules_corpus_collection

    def _wrapped(client, name, config, ef=None):  # type: ignore[no-untyped-def]
        return _FailOnNthUpsertCollection(
            real_get(client, name, config, ef), fail_on_call=fail_on_call
        )

    monkeypatch.setattr(rcs_module, "get_rules_corpus_collection", _wrapped)
    return real_get


class TestReindexCompensatesPartialRebuild:
    """PR #134 P2: reindex_from_sql is exception-safe at its own boundary. After
    the wipe succeeds, a create/transform/upsert/later-batch failure removes this
    attempt's (possibly partially populated) collection and propagates — a
    partial rebuild that contradicts SQLite ground truth is never left queryable.
    ADR-018 D11: in-place re-upsert, no temp/swap collection."""

    def test_later_batch_failure_removes_all_partial_documents(
        self, session_factory, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:  # type: ignore[no-untyped-def]
        session = session_factory()
        package_id = uuid4()
        _seed_package_with_chunks(session, package_id, [f"c{i}" for i in range(4)])
        client = build_isolated_test_chroma_client(str(tmp_path))
        config = RetrievalMemoryConfig()
        service = RulesCorpusService(
            client, config, DeterministicFakeEmbeddingFunction()
        )

        monkeypatch.setattr(
            client, "get_max_batch_size", lambda: 2
        )  # 4 chunks -> 2 batches
        real_get = _patch_get_collection_failing_on_batch(monkeypatch, fail_on_call=2)

        with pytest.raises(RuntimeError, match="upsert batch 2 failed"):
            service.reindex_from_sql(session, package_id)

        # The whole attempt collection was removed — batch 1's documents are gone.
        assert _collection_absent(client, package_id)
        # Re-reading the store (bypassing the wrapper) shows nothing partial.
        name = rules_corpus_collection_name(package_id)
        ef = DeterministicFakeEmbeddingFunction()
        assert real_get(client, name, config, ef).count() == 0

    def test_first_batch_failure_removes_the_attempt_collection(
        self, session_factory, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:  # type: ignore[no-untyped-def]
        """A failure after the successful wipe but before the first batch
        completes still removes the (newly created, empty-or-partial) collection,
        so an incomplete rebuild is not left standing as if it were complete."""
        session = session_factory()
        package_id = uuid4()
        _seed_package_with_chunks(session, package_id, ["only chunk"])
        client = build_isolated_test_chroma_client(str(tmp_path))
        config = RetrievalMemoryConfig()
        service = RulesCorpusService(
            client, config, DeterministicFakeEmbeddingFunction()
        )

        _patch_get_collection_failing_on_batch(monkeypatch, fail_on_call=1)

        with pytest.raises(RuntimeError, match="upsert batch 1 failed"):
            service.reindex_from_sql(session, package_id)

        assert _collection_absent(client, package_id)

    def test_successful_multi_batch_rebuild_writes_exact_complete_set(
        self, session_factory, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:  # type: ignore[no-untyped-def]
        session = session_factory()
        package_id = uuid4()
        _seed_package_with_chunks(session, package_id, [f"chunk {i}" for i in range(5)])
        client = build_isolated_test_chroma_client(str(tmp_path))
        config = RetrievalMemoryConfig()
        ef = DeterministicFakeEmbeddingFunction()
        service = RulesCorpusService(client, config, ef)

        monkeypatch.setattr(
            client, "get_max_batch_size", lambda: 2
        )  # 5 chunks -> 3 batches

        written = service.reindex_from_sql(session, package_id)

        assert written == 5
        name = rules_corpus_collection_name(package_id)
        stored = get_rules_corpus_collection(client, name, config, ef).get()
        assert len(stored["ids"]) == 5
        assert set(stored["documents"]) == {f"chunk {i}" for i in range(5)}

    def test_invalid_max_batch_size_fails_clearly(
        self, session_factory, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:  # type: ignore[no-untyped-def]
        """Invalid/unavailable capability data fails clearly (and compensates the
        attempt collection) — it never silently reverts to a fixed limit."""
        session = session_factory()
        package_id = uuid4()
        _seed_package_with_chunks(session, package_id, ["c"])
        client = build_isolated_test_chroma_client(str(tmp_path))
        config = RetrievalMemoryConfig()
        service = RulesCorpusService(
            client, config, DeterministicFakeEmbeddingFunction()
        )

        monkeypatch.setattr(client, "get_max_batch_size", lambda: 0)

        with pytest.raises(RuntimeError, match="max batch size"):
            service.reindex_from_sql(session, package_id)
        assert _collection_absent(client, package_id)

    def test_cleanup_failure_is_surfaced_not_swallowed(
        self, session_factory, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:  # type: ignore[no-untyped-def]
        """When compensating cleanup itself fails, the cleanup failure is
        surfaced (not swallowed) and the originating upsert failure is preserved
        in the chain — never a clean-failure claim while partial content remains."""
        session = session_factory()
        package_id = uuid4()
        _seed_package_with_chunks(session, package_id, [f"c{i}" for i in range(4)])
        client = build_isolated_test_chroma_client(str(tmp_path))
        config = RetrievalMemoryConfig()
        service = RulesCorpusService(
            client, config, DeterministicFakeEmbeddingFunction()
        )

        monkeypatch.setattr(client, "get_max_batch_size", lambda: 2)
        real_get = _patch_get_collection_failing_on_batch(monkeypatch, fail_on_call=2)

        # delete_collection: 1st call is the wipe (no prior collection -> Chroma
        # raises NotFoundError, suppressed by delete_collection_ignoring_absence);
        # the 2nd call is the compensating cleanup, which fails operationally.
        real_delete = client.delete_collection
        calls = {"n": 0}

        def _delete(name):  # type: ignore[no-untyped-def]
            calls["n"] += 1
            if calls["n"] >= 2:
                raise RuntimeError("cleanup boom")
            return real_delete(name)

        monkeypatch.setattr(client, "delete_collection", _delete)

        with pytest.raises(RuntimeError, match="cleanup boom") as exc_info:
            service.reindex_from_sql(session, package_id)

        # Originating upsert failure preserved (chained), cleanup failure surfaced.
        assert isinstance(exc_info.value.__context__, RuntimeError)
        assert "upsert batch 2 failed" in str(exc_info.value.__context__)
        # Cleanup genuinely failed, so batch 1's partial content is still present —
        # the failure was surfaced rather than pretending a clean rollback.
        name = rules_corpus_collection_name(package_id)
        ef = DeterministicFakeEmbeddingFunction()
        assert real_get(client, name, config, ef).count() == 2


def test_no_pass_service_imports_rules_corpus_service() -> None:
    """D10: no Context Builder / adjudication / Writer / Planner / pass
    service may import RulesCorpusService — semantic rules retrieval stays
    internal/admin-diagnostic only in v1."""
    import ast
    from pathlib import Path as _Path

    src_root = _Path(__file__).resolve().parents[3] / "src" / "afterworlds"
    forbidden_dirs = {
        src_root / "services" / "context_builder.py",
        src_root / "pipeline" / "rpg",
        src_root / "pipeline" / "writer",
        src_root / "pipeline" / "planner",
        src_root / "pipeline" / "extractor",
        src_root / "pipeline" / "contradiction",
        src_root / "pipeline" / "safety",
        src_root / "pipeline" / "branching",
        src_root / "pipeline" / "writing",
    }
    offending: list[str] = []
    for path in forbidden_dirs:
        candidates = [path] if path.is_file() else list(path.rglob("*.py"))
        for file_path in candidates:
            tree = ast.parse(file_path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if (
                    isinstance(node, ast.ImportFrom)
                    and node.module
                    and "rules_corpus_service" in node.module
                ):
                    offending.append(str(file_path))
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if "rules_corpus_service" in alias.name:
                            offending.append(str(file_path))
    assert offending == []
