from __future__ import annotations

from uuid import uuid4


def test_create_and_get_story_rpg(client) -> None:  # type: ignore[no-untyped-def]
    resp = client.post(
        "/api/stories",
        json={"title": "My Quest", "mode": "rpg", "character_name": "Arden"},
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["title"] == "My Quest"
    assert body["mode"] == "rpg"
    assert body["status"] == "setup"
    story_id = body["story_id"]

    detail = client.get(f"/api/stories/{story_id}")
    assert detail.status_code == 200
    assert detail.json()["story_id"] == story_id


def test_create_story_branching_and_writing(client) -> None:  # type: ignore[no-untyped-def]
    for mode in ("branching", "writing"):
        resp = client.post(
            "/api/stories", json={"title": f"{mode} story", "mode": mode}
        )
        assert resp.status_code == 201, resp.text
        assert resp.json()["mode"] == mode


def test_list_stories_reflects_created(client) -> None:  # type: ignore[no-untyped-def]
    client.post("/api/stories", json={"title": "A", "mode": "writing"})
    client.post("/api/stories", json={"title": "B", "mode": "branching"})
    resp = client.get("/api/stories")
    assert resp.status_code == 200
    titles = {s["title"] for s in resp.json()["stories"]}
    assert {"A", "B"} <= titles


def test_get_story_not_found(client) -> None:  # type: ignore[no-untyped-def]
    resp = client.get(f"/api/stories/{uuid4()}")
    assert resp.status_code == 404
    body = resp.json()
    assert body["error_code"] == "not_found"
    assert body["schema_version"] == 1


def test_create_story_rejects_extra_fields(client) -> None:  # type: ignore[no-untyped-def]
    resp = client.post(
        "/api/stories",
        json={"title": "X", "mode": "writing", "sojourner_id": str(uuid4())},
    )
    assert resp.status_code == 422


def test_create_story_bootstraps_turn_anchor_and_session_state(client) -> None:  # type: ignore[no-untyped-def]
    from afterworlds.persistence.orm.node import NodeORM
    from afterworlds.persistence.orm.session_state import RpgSessionStateORM

    resp = client.post(
        "/api/stories",
        json={"title": "Anchor Test", "mode": "rpg", "character_name": "Zed"},
    )
    story_id = resp.json()["story_id"]

    app = client.app
    session = app.state.session_factory()
    try:
        session_state = (
            session.query(RpgSessionStateORM)
            .filter(RpgSessionStateORM.story_id == story_id)
            .first()
        )
        assert session_state is not None
        node = session.query(NodeORM).first()
        assert node is not None
    finally:
        session.close()
