"""Round 8 remediation (PR #126 P2): request DTOs carry schema_version.

Response DTOs already version via ``schema_version: Literal[1] = 1``; request
DTOs did not, so clients had no way to send a version and the contract was
one-sided. Each of the five request bodies (``CreateStoryRequest``,
``TurnSubmissionRequest``, ``RpgSetupRequest``, ``BranchingSetupRequest``,
``WritingSetupRequest``) must: accept an omitted ``schema_version`` (defaults
to 1), accept an explicit ``schema_version: 1``, and reject any other value
through the existing ``VALIDATION_FAILED`` envelope (not a bespoke error
shape).
"""

from __future__ import annotations


def _create_story(client, mode: str = "writing", **extra):  # type: ignore[no-untyped-def]
    resp = client.post("/api/stories", json={"title": "T", "mode": mode, **extra})
    assert resp.status_code == 201, resp.text
    return resp.json()["story_id"]


def _assert_validation_envelope(resp) -> None:  # type: ignore[no-untyped-def]
    assert resp.status_code == 422, resp.text
    body = resp.json()
    assert body["error_code"] == "validation_failed"
    assert body["schema_version"] == 1


class TestCreateStoryRequest:
    def test_omitted_schema_version_defaults_to_1(self, client) -> None:  # type: ignore[no-untyped-def]
        resp = client.post("/api/stories", json={"title": "T", "mode": "writing"})
        assert resp.status_code == 201, resp.text

    def test_explicit_schema_version_1_accepted(self, client) -> None:  # type: ignore[no-untyped-def]
        resp = client.post(
            "/api/stories",
            json={"title": "T", "mode": "writing", "schema_version": 1},
        )
        assert resp.status_code == 201, resp.text

    def test_schema_version_2_rejected(self, client) -> None:  # type: ignore[no-untyped-def]
        resp = client.post(
            "/api/stories",
            json={"title": "T", "mode": "writing", "schema_version": 2},
        )
        _assert_validation_envelope(resp)


class TestTurnSubmissionRequest:
    def test_omitted_schema_version_defaults_to_1(self, client) -> None:  # type: ignore[no-untyped-def]
        story_id = _create_story(client)
        resp = client.post(
            f"/api/stories/{story_id}/turns", json={"user_input": "hello"}
        )
        assert resp.status_code != 422, resp.text

    def test_explicit_schema_version_1_accepted(self, client) -> None:  # type: ignore[no-untyped-def]
        story_id = _create_story(client)
        resp = client.post(
            f"/api/stories/{story_id}/turns",
            json={"user_input": "hello", "schema_version": 1},
        )
        assert resp.status_code != 422, resp.text

    def test_schema_version_2_rejected(self, client) -> None:  # type: ignore[no-untyped-def]
        story_id = _create_story(client)
        resp = client.post(
            f"/api/stories/{story_id}/turns",
            json={"user_input": "hello", "schema_version": 2},
        )
        _assert_validation_envelope(resp)


class TestRpgSetupRequest:
    def test_omitted_schema_version_defaults_to_1(self, client) -> None:  # type: ignore[no-untyped-def]
        story_id = _create_story(client, mode="rpg")
        resp = client.post(
            f"/api/stories/{story_id}/setup",
            json={"mode": "rpg", "tone": "balanced"},
        )
        assert resp.status_code == 200, resp.text

    def test_explicit_schema_version_1_accepted(self, client) -> None:  # type: ignore[no-untyped-def]
        story_id = _create_story(client, mode="rpg")
        resp = client.post(
            f"/api/stories/{story_id}/setup",
            json={"mode": "rpg", "tone": "balanced", "schema_version": 1},
        )
        assert resp.status_code == 200, resp.text

    def test_schema_version_2_rejected(self, client) -> None:  # type: ignore[no-untyped-def]
        story_id = _create_story(client, mode="rpg")
        resp = client.post(
            f"/api/stories/{story_id}/setup",
            json={"mode": "rpg", "tone": "balanced", "schema_version": 2},
        )
        _assert_validation_envelope(resp)


class TestBranchingSetupRequest:
    def test_omitted_schema_version_defaults_to_1(self, client) -> None:  # type: ignore[no-untyped-def]
        story_id = _create_story(client, mode="branching")
        resp = client.post(
            f"/api/stories/{story_id}/setup",
            json={
                "mode": "branching",
                "interaction_style": "freeform_only",
                "branching_cadence": "balanced",
            },
        )
        assert resp.status_code == 200, resp.text

    def test_explicit_schema_version_1_accepted(self, client) -> None:  # type: ignore[no-untyped-def]
        story_id = _create_story(client, mode="branching")
        resp = client.post(
            f"/api/stories/{story_id}/setup",
            json={
                "mode": "branching",
                "interaction_style": "freeform_only",
                "branching_cadence": "balanced",
                "schema_version": 1,
            },
        )
        assert resp.status_code == 200, resp.text

    def test_schema_version_2_rejected(self, client) -> None:  # type: ignore[no-untyped-def]
        story_id = _create_story(client, mode="branching")
        resp = client.post(
            f"/api/stories/{story_id}/setup",
            json={
                "mode": "branching",
                "interaction_style": "freeform_only",
                "branching_cadence": "balanced",
                "schema_version": 2,
            },
        )
        _assert_validation_envelope(resp)


class TestWritingSetupRequest:
    def test_omitted_schema_version_defaults_to_1(self, client) -> None:  # type: ignore[no-untyped-def]
        story_id = _create_story(client, mode="writing")
        resp = client.post(
            f"/api/stories/{story_id}/setup",
            json={
                "mode": "writing",
                "persona_id": "chiron",
                "specific_goals": "Draft a chapter.",
            },
        )
        assert resp.status_code == 200, resp.text

    def test_explicit_schema_version_1_accepted(self, client) -> None:  # type: ignore[no-untyped-def]
        story_id = _create_story(client, mode="writing")
        resp = client.post(
            f"/api/stories/{story_id}/setup",
            json={
                "mode": "writing",
                "persona_id": "chiron",
                "specific_goals": "Draft a chapter.",
                "schema_version": 1,
            },
        )
        assert resp.status_code == 200, resp.text

    def test_schema_version_2_rejected(self, client) -> None:  # type: ignore[no-untyped-def]
        story_id = _create_story(client, mode="writing")
        resp = client.post(
            f"/api/stories/{story_id}/setup",
            json={
                "mode": "writing",
                "persona_id": "chiron",
                "specific_goals": "Draft a chapter.",
                "schema_version": 2,
            },
        )
        _assert_validation_envelope(resp)
