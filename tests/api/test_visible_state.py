from __future__ import annotations

from uuid import uuid4


def _create_story(client, mode: str, **extra):  # type: ignore[no-untyped-def]
    resp = client.post("/api/stories", json={"title": "T", "mode": mode, **extra})
    assert resp.status_code == 201, resp.text
    return resp.json()["story_id"]


def test_visible_state_none_before_setup_for_writing(client) -> None:  # type: ignore[no-untyped-def]
    story_id = _create_story(client, "writing")
    resp = client.get(f"/api/stories/{story_id}/visible-state")
    assert resp.status_code == 200
    assert resp.json()["visible_state"] is None


def test_visible_state_populated_after_writing_setup(client) -> None:  # type: ignore[no-untyped-def]
    story_id = _create_story(client, "writing")
    setup_resp = client.post(
        f"/api/stories/{story_id}/setup",
        json={
            "mode": "writing",
            "persona_id": "chiron",
            "specific_goals": "Draft chapter one",
        },
    )
    assert setup_resp.status_code == 200, setup_resp.text
    assert setup_resp.json()["visible_state"]["persona_id"] == "chiron"

    resp = client.get(f"/api/stories/{story_id}/visible-state")
    assert resp.status_code == 200
    assert resp.json()["visible_state"]["persona_id"] == "chiron"


def test_visible_state_none_before_branching_setup(client) -> None:  # type: ignore[no-untyped-def]
    # BranchingVisibleStateService.build requires interaction_style AND
    # branching_cadence configured -- neither is set until setup runs.
    story_id = _create_story(client, "branching")
    resp = client.get(f"/api/stories/{story_id}/visible-state")
    assert resp.status_code == 200
    assert resp.json()["visible_state"] is None


def test_visible_state_populated_after_branching_setup(client) -> None:  # type: ignore[no-untyped-def]
    story_id = _create_story(client, "branching")
    client.post(
        f"/api/stories/{story_id}/setup",
        json={
            "mode": "branching",
            "interaction_style": "hybrid",
            "branching_cadence": "interactive",
        },
    )
    resp = client.get(f"/api/stories/{story_id}/visible-state")
    assert resp.status_code == 200
    assert resp.json()["visible_state"]["interaction_style"] == "hybrid"


def test_visible_state_rpg_none_until_full_sheet_exists(client) -> None:  # type: ignore[no-untyped-def]
    # Only a minimal RpgCharacterSheetBase exists at bootstrap (Phase 1) --
    # no Dnd5eCharacterSheet until the RPG conversational setup pipeline
    # (Issue 15) creates one, which is out of Issue 19's scope to fabricate.
    story_id = _create_story(client, "rpg", character_name="Arden")
    resp = client.get(f"/api/stories/{story_id}/visible-state")
    assert resp.status_code == 200
    assert resp.json()["visible_state"] is None


def test_visible_state_missing_story_404(client) -> None:  # type: ignore[no-untyped-def]
    resp = client.get(f"/api/stories/{uuid4()}/visible-state")
    assert resp.status_code == 404
