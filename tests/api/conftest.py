"""Shared fixtures for API tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from afterworlds.api.app import create_app
from afterworlds.api.config import ApiSettings
from afterworlds.models.enums import StoryMode


@pytest.fixture()
def app_settings(tmp_path, monkeypatch):  # type: ignore[no-untyped-def]
    # A file-backed DB, not "sqlite://" in-memory: FastAPI runs sync route
    # handlers in a threadpool, and SQLite's in-memory URL gives each thread
    # its own database under SingletonThreadPool -- data would vanish
    # between requests. A tmp file is shared across threads like production.
    db_path = tmp_path / "test.db"
    # build_orchestrator() constructs a real ChromaRetrievalMemoryProvider;
    # point its persist directory at tmp_path so tests never write to (or
    # share) the repo-root default.
    monkeypatch.setenv(
        "AFTERWORLDS_RETRIEVAL_PERSIST_DIRECTORY", str(tmp_path / "chroma_data")
    )
    return ApiSettings(
        database_url=f"sqlite:///{db_path}",
        frontend_dist_dir=tmp_path / "frontend_dist_does_not_exist",
    )


@pytest.fixture()
def client(app_settings):  # type: ignore[no-untyped-def]
    app = create_app(app_settings)
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def writing_released(monkeypatch):  # type: ignore[no-untyped-def]
    """Retained-internals proof only (ADR-017b): re-admits Writing at the API
    release gate so tests keep exercising the preserved Writing routes and
    pipeline. Not a release configuration -- the shipped policy refuses
    Writing; see test_mode_availability.py for that product behavior."""
    monkeypatch.setattr(
        "afterworlds.modes.availability.RELEASED_STORY_MODES", frozenset(StoryMode)
    )
