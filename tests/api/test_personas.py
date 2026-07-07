from __future__ import annotations


def test_personas_gallery_splits_mentors_and_peers(client) -> None:  # type: ignore[no-untyped-def]
    resp = client.get("/api/personas")
    assert resp.status_code == 200
    body = resp.json()
    assert body["mentors"]
    assert body["peers"]
    for persona in body["mentors"]:
        assert persona["orientation"] == "mentor"
    for persona in body["peers"]:
        assert persona["orientation"] == "peer"
