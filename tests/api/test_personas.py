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


def test_personas_gallery_items_carry_schema_version(client) -> None:  # type: ignore[no-untyped-def]
    # Round 10 remediation (PR #126 P2): PersonaDTO (embedded in
    # PersonaGalleryResponse) lacked schema_version, unlike every other DTO.
    resp = client.get("/api/personas")
    assert resp.status_code == 200
    body = resp.json()
    for persona in body["mentors"] + body["peers"]:
        assert persona["schema_version"] == 1
