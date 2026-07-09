"""P2 remediation (PR #126): framework-raised Starlette/FastAPI HTTPException
(unmatched route, wrong method, StaticFiles asset 404) returns the single
``ApiError`` envelope (Binding Decision 10), not FastAPI's default
``{"detail": ...}`` body.
"""

from __future__ import annotations

from dataclasses import replace
from uuid import uuid4

from fastapi.testclient import TestClient

from afterworlds.api.app import create_app


def test_unmatched_api_route_returns_not_found_envelope(client) -> None:  # type: ignore[no-untyped-def]
    resp = client.get("/api/does-not-exist")
    assert resp.status_code == 404, resp.text
    body = resp.json()
    assert body["error_code"] == "not_found"
    assert body["message"] == "Not found."
    assert body["schema_version"] == 1
    assert body["detail"] is None


def test_wrong_method_on_existing_route_returns_405_envelope(client) -> None:  # type: ignore[no-untyped-def]
    """``/api/health`` is GET-only; POSTing it must 405 with the ApiError
    envelope and preserve the framework's ``Allow`` header."""
    resp = client.post("/api/health")
    assert resp.status_code == 405, resp.text
    body = resp.json()
    assert body["error_code"] == "validation_failed"
    assert body["message"] == "Method not allowed."
    assert body["schema_version"] == 1
    assert "Allow" in resp.headers
    assert "GET" in resp.headers["Allow"]


def test_existing_api_error_response_404_unchanged(client) -> None:  # type: ignore[no-untyped-def]
    """Regression: ApiErrorResponse-raised 404s (a real not-found story) are
    untouched by the new HTTPException handler -- different exception type,
    same envelope shape as before."""
    story_id = uuid4()
    resp = client.get(f"/api/stories/{story_id}")
    assert resp.status_code == 404, resp.text
    body = resp.json()
    assert body["error_code"] == "not_found"
    assert body["message"] == f"Story {story_id} not found"
    assert body["schema_version"] == 1


def test_static_frontend_route_unaffected_when_dist_present(  # type: ignore[no-untyped-def]
    app_settings, tmp_path
) -> None:
    """Frontend static serving still works when a built frontend is present
    -- the new handler only fires for genuinely unmatched paths."""
    dist_dir = tmp_path / "frontend_dist_present"
    dist_dir.mkdir()
    (dist_dir / "index.html").write_text("<html>ok</html>", encoding="utf-8")
    app_settings = replace(app_settings, frontend_dist_dir=dist_dir)

    app = create_app(app_settings)
    with TestClient(app) as c:
        resp = c.get("/")
        assert resp.status_code == 200
        assert "ok" in resp.text
