"""Round 16 remediation (PR #126 P2): Writing setup must enforce
``PersonaAvailability.ACTIVE`` at the API boundary, not just rely on the
frontend only offering ACTIVE personas via ``GET /api/personas``. A direct
API client naming a HIDDEN/DEPRECATED persona_id by hand must be rejected.

``get_default_registry()`` itself stays unrestricted (existing persisted
stories resolve HIDDEN/DEPRECATED personas via ``build_visible_state``), so
these tests swap in a temporary registry containing one profile of each
availability tier and monkeypatch the module-level ``get_default_registry``
reference used by each importing module.
"""

from __future__ import annotations

import json
from uuid import UUID

import pytest

from afterworlds.modes.personas.registry import JsonPersonaRegistry
from afterworlds.persistence.crud.session_state import (
    get_writing_session_state_by_story,
    update_writing_session_state,
)


def _profile(persona_id: str, availability: str) -> dict:  # type: ignore[no-untyped-def]
    return {
        "schema_version": 1,
        "persona_id": persona_id,
        "display_name": persona_id.title(),
        "orientation": "mentor",
        "availability": availability,
        "supported_modes": ["writing"],
        "source_tradition": "test fixture",
        "source_anchors": ["test anchor"],
        "source_note": None,
        "ui_short_description": "test persona",
        "ui_long_description": "test persona for availability enforcement tests",
        "demeanor_tags": ["calm"],
        "signature_move": "listens closely",
        "opening_question_style": "curious",
        "prompt_fragment": "You are a test persona.",
        "negative_constraints": ["no spoilers"],
        "profile_version": 1,
        "prompt_fingerprint": None,
    }


@pytest.fixture()
def patched_registry(tmp_path, monkeypatch):  # type: ignore[no-untyped-def]
    """Swap in a registry with one ACTIVE, one HIDDEN, and one DEPRECATED
    persona, patched into every module that imported get_default_registry
    directly (setup.py, visible_state.py, personas.py)."""
    registry_path = tmp_path / "test_personas.json"
    registry_path.write_text(
        json.dumps(
            {
                "registry_version": 1,
                "profiles": [
                    _profile("test-active", "active"),
                    _profile("test-hidden", "hidden"),
                    _profile("test-deprecated", "deprecated"),
                ],
            }
        ),
        encoding="utf-8",
    )
    registry = JsonPersonaRegistry(path=registry_path)
    monkeypatch.setattr(
        "afterworlds.api.routes.setup.get_default_registry", lambda: registry
    )
    monkeypatch.setattr(
        "afterworlds.api.visible_state.get_default_registry", lambda: registry
    )
    monkeypatch.setattr(
        "afterworlds.api.routes.personas.get_default_registry", lambda: registry
    )
    return registry


def _create_writing_story(client) -> str:  # type: ignore[no-untyped-def]
    resp = client.post("/api/stories", json={"title": "T", "mode": "writing"})
    assert resp.status_code == 201, resp.text
    return resp.json()["story_id"]


def test_setup_accepts_active_persona(client, patched_registry) -> None:  # type: ignore[no-untyped-def]
    story_id = _create_writing_story(client)
    resp = client.post(
        f"/api/stories/{story_id}/setup",
        json={
            "mode": "writing",
            "persona_id": "test-active",
            "specific_goals": "Draft chapter one",
        },
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["visible_state"]["persona_id"] == "test-active"


def test_setup_rejects_hidden_persona(client, patched_registry) -> None:  # type: ignore[no-untyped-def]
    story_id = _create_writing_story(client)
    resp = client.post(
        f"/api/stories/{story_id}/setup",
        json={
            "mode": "writing",
            "persona_id": "test-hidden",
            "specific_goals": "Draft chapter one",
        },
    )
    assert resp.status_code == 422, resp.text
    body = resp.json()
    assert body["error_code"] == "validation_failed"
    assert body["schema_version"] == 1

    session = client.app.state.session_factory()
    try:
        state = get_writing_session_state_by_story(session, UUID(story_id))
        assert state is not None
        assert state.persona_id is None
        assert state.specific_goals in (None, "")
    finally:
        session.close()


def test_setup_rejects_deprecated_persona(client, patched_registry) -> None:  # type: ignore[no-untyped-def]
    story_id = _create_writing_story(client)
    resp = client.post(
        f"/api/stories/{story_id}/setup",
        json={
            "mode": "writing",
            "persona_id": "test-deprecated",
            "specific_goals": "Draft chapter one",
        },
    )
    assert resp.status_code == 422, resp.text
    body = resp.json()
    assert body["error_code"] == "validation_failed"

    session = client.app.state.session_factory()
    try:
        state = get_writing_session_state_by_story(session, UUID(story_id))
        assert state is not None
        assert state.persona_id is None
    finally:
        session.close()


def test_persisted_hidden_persona_still_resolves_for_existing_story(
    client, patched_registry  # type: ignore[no-untyped-def]
) -> None:
    """Preserve existing behavior: a story that was set up before a persona
    was hidden/deprecated must still resolve it for visible-state/profile
    reads -- get_profile() itself is not restricted to ACTIVE."""
    story_id = _create_writing_story(client)
    resp = client.post(
        f"/api/stories/{story_id}/setup",
        json={
            "mode": "writing",
            "persona_id": "test-active",
            "specific_goals": "Draft chapter one",
        },
    )
    assert resp.status_code == 200, resp.text

    # Simulate the catalog changing after setup: directly persist a
    # now-hidden persona_id, bypassing the setup route entirely (mirrors
    # tests/api/test_visible_state.py's _stale_writing_persona pattern).
    session = client.app.state.session_factory()
    try:
        state = get_writing_session_state_by_story(session, UUID(story_id))
        assert state is not None
        update_writing_session_state(
            session, state.model_copy(update={"persona_id": "test-hidden"})
        )
        session.commit()
    finally:
        session.close()

    resp = client.get(f"/api/stories/{story_id}/visible-state")
    assert resp.status_code == 200, resp.text
    assert resp.json()["visible_state"]["persona_id"] == "test-hidden"


def test_personas_gallery_excludes_hidden_and_deprecated(
    client, patched_registry  # type: ignore[no-untyped-def]
) -> None:
    resp = client.get("/api/personas")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    ids = {p["persona_id"] for p in body["mentors"] + body["peers"]}
    assert "test-active" in ids
    assert "test-hidden" not in ids
    assert "test-deprecated" not in ids
