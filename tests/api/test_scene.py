"""The scene view and drawn routes over HTTP (issue #211, M1)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import sqlalchemy as sa

from afterworlds.api.deps import get_orchestrator
from afterworlds.mapper import fixture, store
from afterworlds.pipeline.orchestrator.models import OrchestrationResult
from afterworlds.pipeline.rpg.movement import MoverProfile
from afterworlds.pipeline.rpg.spatial_turn import Mover, SpatialTurnService
from tests.api._fixtures import make_delivered_result
from tests.api.test_turns import _seed_hosted
from tests.pipeline.rpg.movement_support import rules

NOW = datetime(2026, 11, 27, tzinfo=UTC)
STRAIGHT = ["B5", "C5", "D5", "E5", "F5", "G5", "H5"]


def _rpg_story(client: Any) -> str:
    resp = client.post("/api/stories", json={"title": "Mill", "mode": "rpg"})
    assert resp.status_code == 201, resp.text
    return str(resp.json()["story_id"])


def _seed_scene(client: Any, story: str) -> None:
    with client.app.state.session_factory() as s:
        store.begin_scene(
            s,
            story_id=UUID(story),
            place_key=fixture.PLACE_KEY,
            label=fixture.LABEL,
            snapshot=fixture.build(),
            seed=fixture.SEED,
            now=NOW,
        )
        s.commit()


def _revision_count(client: Any) -> int:
    with client.app.state.session_factory() as s:
        return int(
            s.execute(
                sa.text("SELECT COUNT(*) FROM spatial_map_revisions")
            ).scalar_one()
        )


class _Orchestrator:
    """The real spatial service with a fixed mover, and a recording turn."""

    def __init__(self, session_factory: Any) -> None:
        self.spatial_turn_service = SpatialTurnService(
            session_factory,
            lambda _sid, _truth: Mover(
                profile=MoverProfile(token_id="hero", walk_ft=30, strength=14),
                rules=rules(),
                roller=("character", "hero"),
            ),
        )
        self.calls: list[dict[str, Any]] = []

    def orchestrate_turn(self, *args: Any, **kwargs: Any) -> OrchestrationResult:
        self.calls.append(kwargs)
        return make_delivered_result()


def _stub(client: Any) -> _Orchestrator:
    stub = _Orchestrator(client.app.state.session_factory)
    client.app.dependency_overrides[get_orchestrator] = lambda: stub
    return stub


def test_a_story_without_a_scene_has_no_view(client: Any) -> None:
    story = _rpg_story(client)
    resp = client.get(f"/api/stories/{story}/scene")
    assert resp.status_code == 404
    assert resp.json()["error_code"] == "not_found"


def test_the_view_is_player_safe_and_read_only(client: Any) -> None:
    story = _rpg_story(client)
    _seed_scene(client, story)
    before = _revision_count(client)
    first = client.get(f"/api/stories/{story}/scene")
    second = client.get(f"/api/stories/{story}/scene")
    assert first.status_code == 200, first.text
    assert first.json() == second.json()
    assert _revision_count(client) == before
    body = first.json()
    text = str(body["snapshot"])
    for hidden in (fixture.HIDDEN_PIT, fixture.SECRET_DOOR, fixture.LURKER):
        assert hidden not in text
    assert len(body["view_hash"]) == 64


def test_the_view_carries_the_movers_allowance(client: Any) -> None:
    story = _rpg_story(client)
    _seed_scene(client, story)
    _stub(client)
    body = client.get(f"/api/stories/{story}/scene").json()
    assert body["viewer"] == "hero"
    assert body["allowance"]["speed_ft"] == 30
    assert body["allowance"]["costs"]["E5"] == 15  # the hidden pit looks like ground


def test_a_drawn_route_reaches_the_turn(client: Any) -> None:
    story = _rpg_story(client)
    _seed_scene(client, story)
    _seed_hosted(client)
    stub = _stub(client)
    view = client.get(f"/api/stories/{story}/scene").json()
    resp = client.post(
        f"/api/stories/{story}/turns",
        json={
            "user_input": "I go.",
            "move_path": {"squares": STRAIGHT, "view_hash": view["view_hash"]},
        },
    )
    assert resp.status_code == 200, resp.text
    [call] = stub.calls
    drawn = call["drawn_route"]
    assert drawn.squares == tuple(STRAIGHT)
    assert drawn.view_hash == view["view_hash"]


def test_a_stale_route_is_refused_before_the_turn(client: Any) -> None:
    story = _rpg_story(client)
    _seed_scene(client, story)
    _seed_hosted(client)
    stub = _stub(client)
    resp = client.post(
        f"/api/stories/{story}/turns",
        json={
            "user_input": "I go.",
            "move_path": {"squares": STRAIGHT, "view_hash": "0" * 64},
        },
    )
    assert resp.status_code == 409, resp.text
    assert resp.json()["error_code"] == "route_stale"
    assert resp.json()["detail"] == {"reason": "the scene changed since you looked"}
    assert stub.calls == []


def test_an_illegal_route_is_refused_with_a_player_safe_reason(client: Any) -> None:
    story = _rpg_story(client)
    _seed_scene(client, story)
    _seed_hosted(client)
    stub = _stub(client)
    resp = client.post(
        f"/api/stories/{story}/turns",
        json={"user_input": "I go.", "move_path": {"squares": ["B5", "D5"]}},
    )
    assert resp.status_code == 422, resp.text
    assert resp.json()["error_code"] == "route_refused"
    assert resp.json()["detail"]["reason"] == "not a step"
    assert stub.calls == []


def test_a_route_that_starts_elsewhere_is_refused(client: Any) -> None:
    story = _rpg_story(client)
    _seed_scene(client, story)
    _seed_hosted(client)
    _stub(client)
    resp = client.post(
        f"/api/stories/{story}/turns",
        json={"user_input": "I go.", "move_path": {"squares": ["C5", "D5"]}},
    )
    assert resp.status_code == 422
    assert resp.json()["detail"] == {
        "reason": "the route doesn't start at your character",
        "at": "C5",
    }


def test_a_malformed_route_fails_validation(client: Any) -> None:
    story = _rpg_story(client)
    resp = client.post(
        f"/api/stories/{story}/turns",
        json={"user_input": "I go.", "move_path": {"squares": ["b5", "nowhere"]}},
    )
    assert resp.status_code == 422
    assert resp.json()["error_code"] == "validation_failed"


def test_a_branching_story_takes_no_route(client: Any) -> None:
    resp = client.post("/api/stories", json={"title": "B", "mode": "branching"})
    story = resp.json()["story_id"]
    _seed_hosted(client)
    stub = _stub(client)
    resp = client.post(
        f"/api/stories/{story}/turns",
        json={"user_input": "I go.", "move_path": {"squares": STRAIGHT}},
    )
    assert resp.status_code == 422
    assert stub.calls == []
