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


def test_branching_setup_with_both_required_fields_promotes_to_in_play(
    client,  # type: ignore[no-untyped-def]
) -> None:
    """Round 7 remediation (PR #126 P1): Branching setup must receive the
    same durable completion treatment as Writing -- once interaction_style
    and branching_cadence are both persisted, play_status must promote to
    IN_PLAY, not stay SETUP forever."""
    story_id = _create_story(client, "branching")
    resp = client.post(
        f"/api/stories/{story_id}/setup",
        json={
            "mode": "branching",
            "interaction_style": "true_cyoa",
            "branching_cadence": "balanced",
        },
    )
    assert resp.status_code == 200, resp.text

    from uuid import UUID

    from afterworlds.models.enums import BranchingPlayStatus
    from afterworlds.persistence.crud.session_state import (
        get_branching_session_state_by_story,
    )

    session = client.app.state.session_factory()
    try:
        state = get_branching_session_state_by_story(session, UUID(story_id))
        assert state is not None
        assert state.play_status is BranchingPlayStatus.IN_PLAY
    finally:
        session.close()


def test_branching_partial_setup_does_not_promote_to_in_play(
    client,  # type: ignore[no-untyped-def]
) -> None:
    """A setup call supplying only one of the two required fields must not
    promote play_status -- the effective persisted state still lacks
    branching_cadence."""
    story_id = _create_story(client, "branching")
    resp = client.post(
        f"/api/stories/{story_id}/setup",
        json={"mode": "branching", "interaction_style": "true_cyoa"},
    )
    assert resp.status_code == 200, resp.text

    from uuid import UUID

    from afterworlds.models.enums import BranchingPlayStatus
    from afterworlds.persistence.crud.session_state import (
        get_branching_session_state_by_story,
    )

    session = client.app.state.session_factory()
    try:
        state = get_branching_session_state_by_story(session, UUID(story_id))
        assert state is not None
        assert state.play_status is BranchingPlayStatus.SETUP
        assert state.branching_cadence is None
    finally:
        session.close()


def test_branching_setup_promotes_using_effective_state_across_two_partial_calls(
    client,  # type: ignore[no-untyped-def]
) -> None:
    """Do not infer completion from the incoming body alone: a second call
    supplying only the still-missing field must promote using the
    already-persisted field from the first call."""
    story_id = _create_story(client, "branching")
    resp = client.post(
        f"/api/stories/{story_id}/setup",
        json={"mode": "branching", "interaction_style": "hybrid"},
    )
    assert resp.status_code == 200, resp.text

    from uuid import UUID

    from afterworlds.models.enums import BranchingPlayStatus
    from afterworlds.persistence.crud.session_state import (
        get_branching_session_state_by_story,
    )

    session = client.app.state.session_factory()
    try:
        state = get_branching_session_state_by_story(session, UUID(story_id))
        assert state is not None
        assert state.play_status is BranchingPlayStatus.SETUP
    finally:
        session.close()

    resp = client.post(
        f"/api/stories/{story_id}/setup",
        json={"mode": "branching", "branching_cadence": "balanced"},
    )
    assert resp.status_code == 200, resp.text

    session = client.app.state.session_factory()
    try:
        state = get_branching_session_state_by_story(session, UUID(story_id))
        assert state is not None
        assert state.play_status is BranchingPlayStatus.IN_PLAY
        assert state.interaction_style.value == "hybrid"
    finally:
        session.close()


def test_branching_setup_promotion_is_idempotent(
    client,  # type: ignore[no-untyped-def]
) -> None:
    """Repeated setup calls after promotion must not error or regress
    play_status."""
    story_id = _create_story(client, "branching")
    for _ in range(2):
        resp = client.post(
            f"/api/stories/{story_id}/setup",
            json={
                "mode": "branching",
                "interaction_style": "true_cyoa",
                "branching_cadence": "balanced",
            },
        )
        assert resp.status_code == 200, resp.text

    from uuid import UUID

    from afterworlds.models.enums import BranchingPlayStatus
    from afterworlds.persistence.crud.session_state import (
        get_branching_session_state_by_story,
    )

    session = client.app.state.session_factory()
    try:
        state = get_branching_session_state_by_story(session, UUID(story_id))
        assert state is not None
        assert state.play_status is BranchingPlayStatus.IN_PLAY
    finally:
        session.close()


def test_writing_setup_requires_persona_id(client) -> None:  # type: ignore[no-untyped-def]
    story_id = _create_story(client, "writing")
    resp = client.post(
        f"/api/stories/{story_id}/setup",
        json={"mode": "writing", "specific_goals": "Draft chapter one"},
    )
    assert resp.status_code == 422


def test_writing_setup_rejects_unknown_persona(client) -> None:  # type: ignore[no-untyped-def]
    story_id = _create_story(client, "writing")
    resp = client.post(
        f"/api/stories/{story_id}/setup",
        json={
            "mode": "writing",
            "persona_id": "does-not-exist",
            "specific_goals": "Draft chapter one",
        },
    )
    assert resp.status_code == 422
    assert resp.json()["error_code"] == "validation_failed"


def test_writing_setup_requires_specific_goals(client) -> None:  # type: ignore[no-untyped-def]
    # P1 remediation (PR #126 review round 5, owner decision): specific_goals
    # is required so play_status can only legitimately promote to IN_PLAY
    # once a real, Sojourner-authored goal exists -- never a synthesized
    # placeholder.
    story_id = _create_story(client, "writing")
    resp = client.post(
        f"/api/stories/{story_id}/setup",
        json={"mode": "writing", "persona_id": "chiron"},
    )
    assert resp.status_code == 422
    assert resp.json()["error_code"] == "validation_failed"


def test_writing_setup_rejects_blank_specific_goals(client) -> None:  # type: ignore[no-untyped-def]
    story_id = _create_story(client, "writing")
    resp = client.post(
        f"/api/stories/{story_id}/setup",
        json={"mode": "writing", "persona_id": "chiron", "specific_goals": "   "},
    )
    assert resp.status_code == 422
    assert resp.json()["error_code"] == "validation_failed"


def test_writing_setup_promotes_play_status_to_in_play(client) -> None:  # type: ignore[no-untyped-def]
    # P1 remediation (PR #126 review round 5): once persona_id and a real
    # specific_goals are both persisted through the one legitimate entry
    # point, play_status promotes to IN_PLAY -- the durable signal turns.py
    # uses to derive server-owned Writing turn provenance.
    story_id = _create_story(client, "writing")
    resp = client.post(
        f"/api/stories/{story_id}/setup",
        json={
            "mode": "writing",
            "persona_id": "chiron",
            "specific_goals": "Draft the opening chapter of a mystery novel",
        },
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["visible_state"]["play_status"] == "in_play"

    from uuid import UUID

    from afterworlds.models.enums import WritingPlayStatus
    from afterworlds.persistence.crud.session_state import (
        get_writing_session_state_by_story,
    )

    session = client.app.state.session_factory()
    try:
        state = get_writing_session_state_by_story(session, UUID(story_id))
        assert state is not None
        assert state.play_status is WritingPlayStatus.IN_PLAY
        assert state.specific_goals == "Draft the opening chapter of a mystery novel"
    finally:
        session.close()


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
        json={
            "mode": "writing",
            "persona_id": "chiron",
            "specific_goals": "Draft chapter one",
        },
    )
    assert resp.status_code == 409
    assert resp.json()["error_code"] == "setup_state_conflict"


def _assert_writing_setup_validation_envelope(resp) -> None:  # type: ignore[no-untyped-def]
    # P2 remediation (PR #126 review round 4): out-of-range
    # dialogue_narration_ratio or a blank beat_constraints entry must be
    # rejected at the API boundary with the typed envelope, not flushed and
    # then hit WritingSessionState's own validators during the setup route's
    # immediately-following build_visible_state re-read (which previously
    # surfaced as an internal 500, not a 422).
    assert resp.status_code == 422, resp.text
    assert resp.json()["error_code"] == "validation_failed"


def test_writing_setup_rejects_ratio_below_zero(client) -> None:  # type: ignore[no-untyped-def]
    story_id = _create_story(client, "writing")
    resp = client.post(
        f"/api/stories/{story_id}/setup",
        json={
            "mode": "writing",
            "persona_id": "chiron",
            "specific_goals": "Draft chapter one",
            "dialogue_narration_ratio": -1,
        },
    )
    _assert_writing_setup_validation_envelope(resp)


def test_writing_setup_rejects_ratio_above_hundred(client) -> None:  # type: ignore[no-untyped-def]
    story_id = _create_story(client, "writing")
    resp = client.post(
        f"/api/stories/{story_id}/setup",
        json={
            "mode": "writing",
            "persona_id": "chiron",
            "specific_goals": "Draft chapter one",
            "dialogue_narration_ratio": 101,
        },
    )
    _assert_writing_setup_validation_envelope(resp)


def test_writing_setup_rejects_empty_beat_constraint(client) -> None:  # type: ignore[no-untyped-def]
    story_id = _create_story(client, "writing")
    resp = client.post(
        f"/api/stories/{story_id}/setup",
        json={
            "mode": "writing",
            "persona_id": "chiron",
            "specific_goals": "Draft chapter one",
            "beat_constraints": [""],
        },
    )
    _assert_writing_setup_validation_envelope(resp)


def test_writing_setup_rejects_whitespace_only_beat_constraint(client) -> None:  # type: ignore[no-untyped-def]
    story_id = _create_story(client, "writing")
    resp = client.post(
        f"/api/stories/{story_id}/setup",
        json={
            "mode": "writing",
            "persona_id": "chiron",
            "specific_goals": "Draft chapter one",
            "beat_constraints": ["   "],
        },
    )
    _assert_writing_setup_validation_envelope(resp)


def test_writing_setup_accepts_boundary_ratio_and_nonblank_constraints(
    client,  # type: ignore[no-untyped-def]
) -> None:
    story_id = _create_story(client, "writing")
    for ratio in (0, 100):
        resp = client.post(
            f"/api/stories/{story_id}/setup",
            json={
                "mode": "writing",
                "persona_id": "chiron",
                "specific_goals": "Draft chapter one",
                "dialogue_narration_ratio": ratio,
                "beat_constraints": ["Introduce the antagonist", "Raise the stakes"],
            },
        )
        assert resp.status_code == 200, resp.text


def test_get_setup_state_for_unconfigured_rpg_story_returns_creation_defaults(
    client,  # type: ignore[no-untyped-def]
) -> None:
    # P2 remediation (PR #126 review round 5): RPG session state exists from
    # story creation (ensure_mode_session_state), independent of whether a
    # concrete character sheet exists yet -- so GET .../setup must return
    # something even before the first POST .../setup call, not 404.
    story_id = _create_story(client, "rpg", character_name="Arden")
    resp = client.get(f"/api/stories/{story_id}/setup")
    assert resp.status_code == 200, resp.text
    state = resp.json()["setup_state"]
    assert state["mode"] == "rpg"
    assert state["dice_handling"] == "ai_rolls"
    assert state["tone"] == "balanced"


def test_get_setup_state_reflects_saved_rpg_config_after_reload(
    client,  # type: ignore[no-untyped-def]
) -> None:
    # P2 remediation (PR #126 review round 5): the exact reload-preservation
    # scenario -- save non-default values, then a fresh GET (simulating a
    # page reload) must reflect them, not the ai_rolls/balanced defaults.
    story_id = _create_story(client, "rpg", character_name="Arden")
    resp = client.post(
        f"/api/stories/{story_id}/setup",
        json={"mode": "rpg", "dice_handling": "player_rolls", "tone": "gritty"},
    )
    assert resp.status_code == 200, resp.text

    resp = client.get(f"/api/stories/{story_id}/setup")
    assert resp.status_code == 200, resp.text
    state = resp.json()["setup_state"]
    assert state["dice_handling"] == "player_rolls"
    assert state["tone"] == "gritty"


def test_get_setup_state_for_missing_story_returns_not_found(
    client,  # type: ignore[no-untyped-def]
) -> None:
    from uuid import uuid4

    resp = client.get(f"/api/stories/{uuid4()}/setup")
    assert resp.status_code == 404
    assert resp.json()["error_code"] == "not_found"


def test_get_setup_state_for_branching_and_writing_reflects_saved_config(
    client,  # type: ignore[no-untyped-def]
) -> None:
    # Sibling audit (PR #126 review round 5): Branching/Writing already
    # bypass SetupForm safely on reload via persisted visible state
    # (StoryView's structuredSetupPersisted), so no frontend hydration
    # consumes this for them -- this only confirms the GET endpoint itself
    # is honest and symmetric across all three modes.
    story_id = _create_story(client, "branching")
    resp = client.post(
        f"/api/stories/{story_id}/setup",
        json={
            "mode": "branching",
            "interaction_style": "true_cyoa",
            "branching_cadence": "balanced",
        },
    )
    assert resp.status_code == 200, resp.text
    resp = client.get(f"/api/stories/{story_id}/setup")
    assert resp.status_code == 200, resp.text
    state = resp.json()["setup_state"]
    assert state["mode"] == "branching"
    assert state["interaction_style"] == "true_cyoa"
    assert state["branching_cadence"] == "balanced"

    story_id = _create_story(client, "writing")
    resp = client.post(
        f"/api/stories/{story_id}/setup",
        json={
            "mode": "writing",
            "persona_id": "chiron",
            "specific_goals": "Draft chapter one",
        },
    )
    assert resp.status_code == 200, resp.text
    resp = client.get(f"/api/stories/{story_id}/setup")
    assert resp.status_code == 200, resp.text
    state = resp.json()["setup_state"]
    assert state["mode"] == "writing"
    assert state["persona_id"] == "chiron"
    assert state["specific_goals"] == "Draft chapter one"
