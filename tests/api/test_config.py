"""load_settings(): frontend-dist resolution and the packaged-install fail-loud
guard (Round 6 P2 remediation, PR #126).
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from afterworlds.api import config as config_module
from afterworlds.api.app import create_app
from afterworlds.api.config import ApiSettings, load_settings


def test_default_resolves_to_repo_frontend_dist_when_present(
    monkeypatch, tmp_path
) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.delenv("AFTERWORLDS_FRONTEND_DIST", raising=False)
    fake_default = tmp_path / "frontend" / "dist"
    fake_default.mkdir(parents=True)
    monkeypatch.setattr(config_module, "_DEFAULT_FRONTEND_DIST", fake_default)

    settings = load_settings()
    assert settings.frontend_dist_dir == fake_default


def test_override_env_var_is_trusted_even_if_missing(
    monkeypatch, tmp_path
) -> None:  # type: ignore[no-untyped-def]
    missing_default = tmp_path / "frontend" / "dist"
    monkeypatch.setattr(config_module, "_DEFAULT_FRONTEND_DIST", missing_default)
    override = tmp_path / "custom_dist"
    monkeypatch.setenv("AFTERWORLDS_FRONTEND_DIST", str(override))

    settings = load_settings()
    assert settings.frontend_dist_dir == override


def test_missing_default_and_no_override_fails_loudly(
    monkeypatch, tmp_path
) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.delenv("AFTERWORLDS_FRONTEND_DIST", raising=False)
    missing_default = tmp_path / "frontend" / "dist"
    monkeypatch.setattr(config_module, "_DEFAULT_FRONTEND_DIST", missing_default)

    with pytest.raises(RuntimeError, match="AFTERWORLDS_FRONTEND_DIST"):
        load_settings()


def test_create_app_mounts_static_files_when_dist_exists(
    monkeypatch, tmp_path
) -> None:  # type: ignore[no-untyped-def]
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<html></html>")
    monkeypatch.setenv(
        "AFTERWORLDS_RETRIEVAL_PERSIST_DIRECTORY", str(tmp_path / "chroma_data")
    )
    settings = ApiSettings(
        database_url=f"sqlite:///{tmp_path / 'test.db'}",
        frontend_dist_dir=dist,
    )
    app = create_app(settings)
    with TestClient(app) as client:
        resp = client.get("/")
    assert resp.status_code == 200
    assert "<html>" in resp.text
