from __future__ import annotations


def _create_story(client, mode: str, **extra):  # type: ignore[no-untyped-def]
    resp = client.post("/api/stories", json={"title": "T", "mode": mode, **extra})
    assert resp.status_code == 201, resp.text
    return resp.json()["story_id"]


def test_branching_setup_applies_structured_fields(client) -> None:  # type: ignore[no-untyped-def]
    story_id = _create_story(client, "branching")
    # Visible state requires BOTH interaction_style and branching_cadence
    # configured (BranchingVisibleStateService.build raises otherwise).
    resp = client.post(
        f"/api/stories/{story_id}/setup",
        json={
            "mode": "branching",
            "interaction_style": "true_cyoa",
            "branching_cadence": "balanced",
        },
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["visible_state"]["interaction_style"] == "true_cyoa"
    assert resp.json()["visible_state"]["branching_cadence"] == "balanced"


def test_writing_setup_requires_persona_id(client) -> None:  # type: ignore[no-untyped-def]
    story_id = _create_story(client, "writing")
    resp = client.post(f"/api/stories/{story_id}/setup", json={"mode": "writing"})
    assert resp.status_code == 422


def test_writing_setup_rejects_unknown_persona(client) -> None:  # type: ignore[no-untyped-def]
    story_id = _create_story(client, "writing")
    resp = client.post(
        f"/api/stories/{story_id}/setup",
        json={"mode": "writing", "persona_id": "does-not-exist"},
    )
    assert resp.status_code == 422
    assert resp.json()["error_code"] == "validation_failed"


def test_rpg_setup_applies_play_config_fields(client) -> None:  # type: ignore[no-untyped-def]
    story_id = _create_story(client, "rpg", character_name="Arden")
    resp = client.post(
        f"/api/stories/{story_id}/setup",
        json={"mode": "rpg", "dice_handling": "player_rolls", "gm_cheating": False},
    )
    assert resp.status_code == 200, resp.text

    from uuid import UUID

    from afterworlds.persistence.crud.session_state import (
        get_rpg_session_state_by_story,
    )

    session = client.app.state.session_factory()
    try:
        state = get_rpg_session_state_by_story(session, UUID(story_id))
        assert state is not None
        assert state.dice_handling.value == "player_rolls"
        assert state.gm_cheating is False
    finally:
        session.close()


def test_setup_mode_mismatch_returns_conflict(client) -> None:  # type: ignore[no-untyped-def]
    story_id = _create_story(client, "branching")
    resp = client.post(
        f"/api/stories/{story_id}/setup",
        json={"mode": "writing", "persona_id": "chiron"},
    )
    assert resp.status_code == 409
    assert resp.json()["error_code"] == "setup_state_conflict"
