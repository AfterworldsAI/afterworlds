"""P2 regression: FastAPI/Pydantic validation failures return the single
``ApiError`` envelope (Binding Decision 10), not FastAPI's default
``{"detail": [...]}`` 422 body.

Covers the four representative cases named in PR #126 review round 1:
extra field on a request body, an invalid setup enum, a malformed UUID path
parameter, and a non-integer transcript ``limit`` query parameter.
"""

from __future__ import annotations

from uuid import uuid4


def _create_story(client, mode: str = "writing"):  # type: ignore[no-untyped-def]
    resp = client.post("/api/stories", json={"title": "T", "mode": mode})
    assert resp.status_code == 201, resp.text
    return resp.json()["story_id"]


def _assert_validation_envelope(resp) -> None:  # type: ignore[no-untyped-def]
    assert resp.status_code == 422, resp.text
    body = resp.json()
    assert body["error_code"] == "validation_failed"
    assert body["message"] == "Request validation failed."
    assert body["schema_version"] == 1
    # detail is either a dict[str, str] of dotted-path -> message, or None --
    # never FastAPI's raw list-of-dicts shape (which could echo client input).
    assert body["detail"] is None or isinstance(body["detail"], dict)
    if isinstance(body["detail"], dict):
        for key, value in body["detail"].items():
            assert isinstance(key, str)
            assert isinstance(value, str)


def test_extra_field_on_turn_submission_uses_envelope(client) -> None:  # type: ignore[no-untyped-def]
    story_id = _create_story(client)
    resp = client.post(
        f"/api/stories/{story_id}/turns",
        json={"user_input": "hello", "access_path": "byok"},
    )
    _assert_validation_envelope(resp)


def test_extra_field_on_story_creation_uses_envelope(client) -> None:  # type: ignore[no-untyped-def]
    resp = client.post(
        "/api/stories",
        json={"title": "X", "mode": "writing", "sojourner_id": str(uuid4())},
    )
    _assert_validation_envelope(resp)


def test_invalid_setup_enum_uses_envelope(client) -> None:  # type: ignore[no-untyped-def]
    story_id = _create_story(client, "branching")
    resp = client.post(
        f"/api/stories/{story_id}/setup",
        json={
            "mode": "branching",
            "interaction_style": "not_a_real_style",
            "branching_cadence": "balanced",
        },
    )
    _assert_validation_envelope(resp)


def test_malformed_uuid_path_param_uses_envelope(client) -> None:  # type: ignore[no-untyped-def]
    resp = client.get("/api/stories/not-a-uuid")
    _assert_validation_envelope(resp)


def test_non_integer_transcript_limit_uses_envelope(client) -> None:  # type: ignore[no-untyped-def]
    story_id = _create_story(client)
    resp = client.get(
        f"/api/stories/{story_id}/turns", params={"limit": "not-a-number"}
    )
    _assert_validation_envelope(resp)
