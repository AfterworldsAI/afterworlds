from __future__ import annotations


def test_health_ok(client) -> None:  # type: ignore[no-untyped-def]
    resp = client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body == {"status": "ok", "db_reachable": True, "schema_version": 1}
