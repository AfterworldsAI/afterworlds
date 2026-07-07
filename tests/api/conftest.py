"""Shared fixtures for API tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from afterworlds.api.app import create_app
from afterworlds.api.config import ApiSettings


@pytest.fixture()
def app_settings(tmp_path):  # type: ignore[no-untyped-def]
    # A file-backed DB, not "sqlite://" in-memory: FastAPI runs sync route
    # handlers in a threadpool, and SQLite's in-memory URL gives each thread
    # its own database under SingletonThreadPool -- data would vanish
    # between requests. A tmp file is shared across threads like production.
    db_path = tmp_path / "test.db"
    return ApiSettings(
        database_url=f"sqlite:///{db_path}",
        frontend_dist_dir=tmp_path / "frontend_dist_does_not_exist",
    )


@pytest.fixture()
def client(app_settings):  # type: ignore[no-untyped-def]
    app = create_app(app_settings)
    with TestClient(app) as c:
        yield c
