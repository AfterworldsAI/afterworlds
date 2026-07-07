"""P1 regression (PR #126 review round 2): retrieval query/write services and
``writing_visible_state_service`` are wired into the real product
``build_orchestrator()`` path.

These exercise the actual ``create_app()`` -> ``build_orchestrator()`` wiring
end-to-end through real HTTP turn submissions, using the fake provider
(DoR-B: ``AFTERWORLDS_FAKE_PROVIDER=1``, no real model/network calls) --
unlike ``tests/api/test_turns.py``, which stubs the orchestrator entirely via
``app.dependency_overrides`` and therefore never touches this wiring.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from afterworlds.api.app import create_app
from afterworlds.api.config import ApiSettings
from afterworlds.api.story_bootstrap import ensure_mode_session_state
from afterworlds.entitlement.enums import EntitlementEventType, HostedAccessPlan
from afterworlds.entitlement.payloads import (
    HostedAccessActivatedPayload,
    SubscriptionCreditGrantPayload,
)
from afterworlds.entitlement.service import EntitlementService
from afterworlds.models.enums import (
    RpgTurnRetrievalCategory,
    StoryMode,
    WritingPlayStatus,
)
from afterworlds.models.story import Story
from afterworlds.persistence.crud.retrieval import get_rpg_turn_retrieval_marker
from afterworlds.persistence.crud.session_state import apply_writing_config_update
from afterworlds.persistence.crud.story import create_story


@pytest.fixture()
def fake_provider_client(tmp_path, monkeypatch):  # type: ignore[no-untyped-def]
    monkeypatch.setenv("AFTERWORLDS_FAKE_PROVIDER", "1")
    monkeypatch.setenv(
        "AFTERWORLDS_RETRIEVAL_PERSIST_DIRECTORY", str(tmp_path / "chroma_data")
    )
    settings = ApiSettings(
        database_url=f"sqlite:///{tmp_path / 'test.db'}",
        frontend_dist_dir=tmp_path / "dist_does_not_exist",
    )
    app = create_app(settings)
    with TestClient(app) as c:
        yield c


def _seed_hosted_entitlement(client) -> None:  # type: ignore[no-untyped-def]
    session = client.app.state.session_factory()
    try:
        service = EntitlementService(session)
        sojourner_id = client.app.state.sojourner_id
        service.receive_entitlement_event(
            sojourner_id,
            EntitlementEventType.HOSTED_ACCESS_ACTIVATED,
            HostedAccessActivatedPayload(
                plan=HostedAccessPlan.SUBSCRIPTION, effective_at=datetime.now(UTC)
            ),
        )
        service.receive_entitlement_event(
            sojourner_id,
            EntitlementEventType.SUBSCRIPTION_CREDIT_GRANT,
            SubscriptionCreditGrantPayload(hosted_credit_delta=Decimal("1000")),
        )
        session.commit()
    finally:
        session.close()


def _create_writing_story_with_persona(client) -> str:  # type: ignore[no-untyped-def]
    resp = client.post("/api/stories", json={"title": "T", "mode": "writing"})
    assert resp.status_code == 201, resp.text
    story_id: str = resp.json()["story_id"]
    resp = client.post(
        f"/api/stories/{story_id}/setup",
        json={"mode": "writing", "persona_id": "chiron"},
    )
    assert resp.status_code == 200, resp.text
    return story_id


def test_delivered_turn_exercises_retrieval_query_and_write_wiring(
    fake_provider_client,  # type: ignore[no-untyped-def]
) -> None:
    """A real delivered turn must not crash now that retrieval_query_builder /
    retrieval_write_service are wired -- previously both were None, so
    production turns silently skipped the Issue 18 Retrieval Memory layer
    entirely (never exercised, never verified to actually work end-to-end)."""
    client = fake_provider_client
    _seed_hosted_entitlement(client)
    story_id = _create_writing_story_with_persona(client)

    # First turn: retrieval query builder runs with an empty recent-turn
    # tail (no eligibility-predicate crash on an empty window).
    resp = client.post(
        f"/api/stories/{story_id}/turns", json={"user_input": "Tell me a story."}
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["disposition"] == "delivered", resp.json()

    # Second turn: the query builder now has a real prior committed turn in
    # its recent-turns tail window (exercises gather_turn_eligibility against
    # a real row), and the post-commit ingestion gate has a real DELIVERED
    # turn from the first request to have written.
    resp = client.post(
        f"/api/stories/{story_id}/turns", json={"user_input": "Continue the story."}
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["disposition"] == "delivered", resp.json()


def test_writing_in_play_turn_does_not_fail_for_missing_visible_state_service(
    fake_provider_client,  # type: ignore[no-untyped-def]
) -> None:
    """Regression for the exact P1: without ``writing_visible_state_service``
    wired, every Writing turn submitted while IN_PLAY returned PIPELINE_ERROR
    ("writing visible state service not wired for IN_PLAY turn")."""
    client = fake_provider_client
    _seed_hosted_entitlement(client)
    story_id = _create_writing_story_with_persona(client)

    # Issue 19 does not wire the Writing OOC config extractor (a mode-
    # specific pass SERVICE, deliberately out of scope per
    # pipeline_wiring.py's module docstring), so nothing in today's product
    # HTTP path promotes play_status SETUP -> IN_PLAY. Promote directly via
    # the same typed CRUD the orchestrator itself uses, to construct the
    # "IN_PLAY Writing story with a valid persona" precondition this
    # regression needs without adding new mode policy.
    session = client.app.state.session_factory()
    try:
        apply_writing_config_update(
            session, UUID(story_id), play_status=WritingPlayStatus.IN_PLAY
        )
        session.commit()
    finally:
        session.close()

    resp = client.post(
        f"/api/stories/{story_id}/turns", json={"user_input": "Continue the story."}
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["disposition"] == "delivered", body
    assert body["pipeline_error_summary"] is None


def test_first_turn_for_anchor_less_legacy_story_does_not_fail(
    fake_provider_client,  # type: ignore[no-untyped-def]
) -> None:
    """P2 regression: a story created without a turn-anchor node (as any
    story predating this API's ``ensure_story_turn_anchor_node`` call would
    be) must still succeed on its first turn. Before the fix, the anchor
    created inside ``_submit_turn_sync``'s route session was only flushed,
    not committed, before ``orchestrate_turn`` opened its own separate
    session -- ``WriterService``'s ``node_belongs_to_story`` check in that
    second session could not see the brand-new anchor, so the first turn
    failed as PIPELINE_ERROR and only the *retried* turn succeeded.
    """
    client = fake_provider_client
    _seed_hosted_entitlement(client)

    # Bypass POST /stories deliberately: it already calls
    # ensure_story_turn_anchor_node at creation time, which would not
    # reproduce this defect. Build the story via CRUD only, mirroring
    # exactly what a story created before that anchor-bootstrap call
    # existed would look like.
    session = client.app.state.session_factory()
    try:
        now = datetime.now(UTC)
        story = create_story(
            session,
            Story(
                title="Legacy Story",
                mode=StoryMode.WRITING,
                created_at=now,
                updated_at=now,
            ),
        )
        ensure_mode_session_state(session, story.story_id, StoryMode.WRITING)
        session.commit()
        story_id = str(story.story_id)
    finally:
        session.close()

    resp = client.post(
        f"/api/stories/{story_id}/setup",
        json={"mode": "writing", "persona_id": "chiron"},
    )
    assert resp.status_code == 200, resp.text

    resp = client.post(
        f"/api/stories/{story_id}/turns", json={"user_input": "Tell me a story."}
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["disposition"] == "delivered", body
    assert body["pipeline_error_summary"] is None


def test_rpg_setup_turn_does_not_require_completed_character_sheet(
    fake_provider_client,  # type: ignore[no-untyped-def]
) -> None:
    """P1 regression (PR #126 review round 3): a newly created RPG story
    only has ``RpgCharacterSheetBase`` bootstrapped at creation time -- the
    concrete ``Dnd5eCharacterSheet`` does not exist until Issue 15's
    conversational character-creation flow completes. ``POST /turns`` for
    the RPG setup conversation must still reach the prose Writer path
    (ordinary turns, per this PR's own notes), not fail as PIPELINE_ERROR
    solely because the concrete sheet is missing.
    """
    client = fake_provider_client
    _seed_hosted_entitlement(client)

    resp = client.post(
        "/api/stories",
        json={"title": "New RPG Story", "mode": "rpg", "character_name": "Zed"},
    )
    assert resp.status_code == 201, resp.text
    story_id = resp.json()["story_id"]

    resp = client.post(
        f"/api/stories/{story_id}/turns",
        json={"user_input": "I want to play a half-elf ranger."},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["disposition"] == "delivered", body
    assert body["pipeline_error_summary"] is None

    session = client.app.state.session_factory()
    try:
        category = get_rpg_turn_retrieval_marker(session, UUID(body["turn_id"]))
    finally:
        session.close()
    assert category is RpgTurnRetrievalCategory.SETUP_CONFIRMATION
