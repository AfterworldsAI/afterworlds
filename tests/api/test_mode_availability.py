"""Writing is unavailable in the v1 release (ADR-017b).

Product entry points refuse Writing with the typed ``mode_unavailable`` error
before any effect: no story, session state, anchor, turn, provider call,
access-path probe or entitlement event. The persona gallery offers nothing.
RPG and Branching stay released; ``StoryMode.WRITING`` stays representable.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

import pytest
from sqlalchemy import text

from afterworlds.api.deps import get_byok_readiness_provider, get_orchestrator
from afterworlds.api.story_bootstrap import ensure_mode_session_state
from afterworlds.models.enums import StoryMode
from afterworlds.models.story import Story
from afterworlds.modes.availability import RELEASED_STORY_MODES
from afterworlds.modes.personas.registry import SupportedMode, get_default_registry
from afterworlds.persistence.crud.session_state import (
    get_writing_session_state_by_story,
)
from afterworlds.persistence.crud.story import create_story
from tests.api._fixtures import make_delivered_result
from tests.api.test_turns import _seed_byok, _seed_hosted, _StubOrchestrator

_TABLES = (
    "stories",
    "arcs",
    "chapters",
    "nodes",
    "turns",
    "writing_session_states",
    "entitlement_event",
)


def _counts(client) -> dict[str, int]:  # type: ignore[no-untyped-def]
    session = client.app.state.session_factory()
    try:
        return {
            t: session.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar_one()
            for t in _TABLES
        }
    finally:
        session.close()


def _assert_mode_unavailable(resp) -> None:  # type: ignore[no-untyped-def]
    assert resp.status_code == 422, resp.text
    body = resp.json()
    assert body["error_code"] == "mode_unavailable"
    assert body["detail"] == {"mode": "writing"}
    assert "not available" in body["message"]


def _seed_writing_story(client) -> str:  # type: ignore[no-untyped-def]
    """Minimum fixture for the gate: a Writing row no product path can create
    (story + empty session state, no anchor), written through CRUD."""
    session = client.app.state.session_factory()
    try:
        now = datetime.now(UTC)
        story = create_story(
            session,
            Story(title="W", mode=StoryMode.WRITING, created_at=now, updated_at=now),
        )
        ensure_mode_session_state(session, story.story_id, StoryMode.WRITING)
        session.commit()
        return str(story.story_id)
    finally:
        session.close()


def test_release_policy_is_rpg_and_branching_with_writing_still_represented() -> None:
    assert {StoryMode.RPG, StoryMode.BRANCHING} == RELEASED_STORY_MODES
    assert StoryMode("writing") is StoryMode.WRITING


def test_create_writing_story_is_refused_without_writes(client) -> None:  # type: ignore[no-untyped-def]
    before = _counts(client)
    resp = client.post("/api/stories", json={"title": "W", "mode": "writing"})
    _assert_mode_unavailable(resp)
    assert _counts(client) == before
    assert client.get("/api/stories").json()["stories"] == []


@pytest.mark.parametrize(
    ("mode", "extra"), [("rpg", {"character_name": "Arden"}), ("branching", {})]
)
def test_released_modes_are_still_created(client, mode, extra) -> None:  # type: ignore[no-untyped-def]
    resp = client.post("/api/stories", json={"title": "T", "mode": mode, **extra})
    assert resp.status_code == 201, resp.text
    assert resp.json()["mode"] == mode


def test_writing_setup_is_refused_without_writes(client) -> None:  # type: ignore[no-untyped-def]
    writing_story = _seed_writing_story(client)
    branching_story = client.post(
        "/api/stories", json={"title": "B", "mode": "branching"}
    ).json()["story_id"]
    before = _counts(client)
    for story_id in (writing_story, branching_story):
        resp = client.post(
            f"/api/stories/{story_id}/setup",
            json={
                "mode": "writing",
                "persona_id": "chiron",
                "specific_goals": "Draft chapter one",
            },
        )
        _assert_mode_unavailable(resp)
    assert _counts(client) == before

    session = client.app.state.session_factory()
    try:
        state = get_writing_session_state_by_story(session, UUID(writing_story))
        assert state is not None
        assert state.persona_id is None
        assert not state.specific_goals
    finally:
        session.close()


class _ReadinessSpy:
    def __init__(self) -> None:
        self.calls = 0

    def is_byok_runnable(self, sojourner_id: UUID) -> bool:  # noqa: ARG002
        self.calls += 1
        return True


@pytest.mark.parametrize("seed", [_seed_hosted, _seed_byok], ids=["hosted", "byok"])
def test_writing_turn_is_refused_before_access_selection_and_effects(
    client, seed  # type: ignore[no-untyped-def]
) -> None:
    story_id = _seed_writing_story(client)
    seed(client)
    stub = _StubOrchestrator(make_delivered_result)
    readiness = _ReadinessSpy()
    client.app.dependency_overrides[get_orchestrator] = lambda: stub
    client.app.dependency_overrides[get_byok_readiness_provider] = lambda: readiness
    before = _counts(client)

    resp = client.post(f"/api/stories/{story_id}/turns", json={"user_input": "hi"})

    _assert_mode_unavailable(resp)
    assert stub.calls == []
    assert readiness.calls == 0
    # No anchor (arcs/chapters/nodes), turn or entitlement event was written.
    assert _counts(client) == before


def test_persona_gallery_offers_no_personas(client) -> None:  # type: ignore[no-untyped-def]
    # The six Writing profiles are retained and active in the registry...
    assert len(get_default_registry().list_active(SupportedMode.WRITING)) == 6
    # ...but nothing is selectable, and no fallback persona appears.
    resp = client.get("/api/personas")
    assert resp.status_code == 200, resp.text
    assert resp.json() == {"mentors": [], "peers": [], "schema_version": 1}
