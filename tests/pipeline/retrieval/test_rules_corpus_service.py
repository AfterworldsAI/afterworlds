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
from sqlalchemy import delete, select

from afterworlds.models.enums import SourceLocatorTypeEnum
from afterworlds.persistence.database import create_session_factory
from afterworlds.persistence.orm.rules_package import (
    RuleChunkORM,
    RuleSourceORM,
    RulesPackageORM,
)
from afterworlds.pipeline.retrieval.client import build_isolated_test_chroma_client
from afterworlds.pipeline.retrieval.config import RetrievalMemoryConfig
from afterworlds.pipeline.retrieval.embedding import DeterministicFakeEmbeddingFunction
from afterworlds.pipeline.retrieval.rules_corpus_service import RulesCorpusService

_NOW = datetime(2026, 1, 1, tzinfo=UTC).isoformat()


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
