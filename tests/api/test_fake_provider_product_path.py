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
from sqlalchemy import select

from afterworlds.api.app import create_app
from afterworlds.api.config import ApiSettings
from afterworlds.api.story_bootstrap import ensure_mode_session_state
from afterworlds.entitlement.enums import EntitlementEventType, HostedAccessPlan
from afterworlds.entitlement.payloads import (
    ByokLicenseActivatedPayload,
    HostedAccessActivatedPayload,
    SubscriptionCreditGrantPayload,
)
from afterworlds.entitlement.service import EntitlementService
from afterworlds.models.enums import (
    RpgTurnRetrievalCategory,
    StoryMode,
    WritingCanonEligibility,
    WritingWorkProductKind,
)
from afterworlds.models.story import Story
from afterworlds.persistence.crud.retrieval import (
    get_rpg_turn_retrieval_marker,
    get_turn_for_eligibility,
)
from afterworlds.persistence.crud.session_state import (
    delete_writing_session_state,
    get_writing_session_state_by_story,
    update_writing_session_state,
)
from afterworlds.persistence.crud.story import create_story
from afterworlds.persistence.orm.session_state import WritingSessionStateORM
from afterworlds.pipeline.orchestrator.models import PipelineDisposition
from afterworlds.pipeline.retrieval.eligibility import gather_turn_eligibility


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


def _seed_byok_entitlement(client) -> None:  # type: ignore[no-untyped-def]
    session = client.app.state.session_factory()
    try:
        service = EntitlementService(session)
        sojourner_id = client.app.state.sojourner_id
        service.receive_entitlement_event(
            sojourner_id,
            EntitlementEventType.BYOK_LICENSE_ACTIVATED,
            ByokLicenseActivatedPayload(purchased_at=datetime.now(UTC)),
        )
        session.commit()
    finally:
        session.close()


class _AlwaysByokReady:
    def is_byok_runnable(self, sojourner_id: UUID) -> bool:  # noqa: ARG002
        return True


def _create_writing_story_with_persona(client) -> str:  # type: ignore[no-untyped-def]
    resp = client.post("/api/stories", json={"title": "T", "mode": "writing"})
    assert resp.status_code == 201, resp.text
    story_id: str = resp.json()["story_id"]
    resp = client.post(
        f"/api/stories/{story_id}/setup",
        json={
            "mode": "writing",
            "persona_id": "chiron",
            "specific_goals": "Draft chapter one",
        },
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
    ("writing visible state service not wired for IN_PLAY turn"). That guard
    is gated on ``play_status is IN_PLAY``, so this needs a genuinely IN_PLAY
    turn to exercise it -- as of round 13, ``_create_writing_story_with_persona``
    completes setup but no longer promotes play_status itself (setup leaves
    the story in SETUP; only the setup-confirmation turn's own processing
    promotes to IN_PLAY -- see
    ``test_writing_setup_confirmation_turn_then_promotes_to_in_play``). The
    first turn here is therefore the setup-confirmation turn; the second is
    the genuinely IN_PLAY turn this test actually regression-tests.
    """
    client = fake_provider_client
    _seed_hosted_entitlement(client)
    story_id = _create_writing_story_with_persona(client)

    resp = client.post(
        f"/api/stories/{story_id}/turns", json={"user_input": "Let's begin."}
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["disposition"] == "delivered", resp.json()

    resp = client.post(
        f"/api/stories/{story_id}/turns", json={"user_input": "Continue the story."}
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["disposition"] == "delivered", body
    assert body["pipeline_error_summary"] is None
    assert body["visible_state"]["play_status"] == "in_play"


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
        json={
            "mode": "writing",
            "persona_id": "chiron",
            "specific_goals": "Draft chapter one",
        },
    )
    assert resp.status_code == 200, resp.text

    resp = client.post(
        f"/api/stories/{story_id}/turns", json={"user_input": "Tell me a story."}
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["disposition"] == "delivered", body
    assert body["pipeline_error_summary"] is None


def test_writing_setup_confirmation_turn_then_promotes_to_in_play(
    fake_provider_client,  # type: ignore[no-untyped-def]
) -> None:
    """Round 13 boundary-decision product-path test (owner-approved,
    supersedes round 5's promote-in-``/setup`` behavior): ``POST /setup``
    persists persona_id/specific_goals but no longer promotes play_status
    itself (see ``api/routes/setup.py``). ADR-017 Decision 9 / ADR-018 D6
    require the *first* turn after setup -- taken while play_status is
    still SETUP -- to be recorded as a setup-confirmation turn
    (SETUP_CONFIRMATION/NON_CANON_SUPPORT), not ordinary prose. The
    orchestrator itself (``_narrative_persist``) then promotes play_status
    to IN_PLAY atomically with that turn's own commit, so every *subsequent*
    turn is ordinary Writing prose: routed to Story Bible and eligible for
    Retrieval Memory.
    """
    client = fake_provider_client
    _seed_hosted_entitlement(client)
    story_id = _create_writing_story_with_persona(client)

    # Precondition: setup alone leaves play_status at SETUP.
    resp = client.get(f"/api/stories/{story_id}/visible-state")
    assert resp.status_code == 200, resp.text
    assert resp.json()["visible_state"]["play_status"] == "setup"

    # First turn after setup: play_status was SETUP when this turn began --
    # must be recorded as the setup-confirmation turn, not ordinary prose.
    # The response's visible_state already reflects the promotion this same
    # turn applies (atomic with its own commit) -- the mode_metadata
    # assertions below independently confirm the turn was classified using
    # the *pre*-promotion state, not this post-turn snapshot.
    resp = client.post(
        f"/api/stories/{story_id}/turns",
        json={"user_input": "Let's begin."},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["disposition"] == "delivered", body
    assert body["visible_state"]["play_status"] == "in_play"
    confirmation_turn_id = UUID(body["turn_id"])

    session = client.app.state.session_factory()
    try:
        turn = get_turn_for_eligibility(session, confirmation_turn_id)
        assert turn is not None
        assert turn.mode_metadata is not None
        assert (
            turn.mode_metadata.work_product_kind
            == WritingWorkProductKind.SETUP_CONFIRMATION.value
        )
        assert (
            turn.mode_metadata.canon_eligibility
            == WritingCanonEligibility.NON_CANON_SUPPORT.value
        )
        decision = gather_turn_eligibility(
            session, confirmation_turn_id, StoryMode.WRITING
        )
        assert decision.eligible is False, decision.reason
    finally:
        session.close()

    # Second turn: the confirmation turn has landed, so play_status is now
    # IN_PLAY -- this turn must be ordinary, eligible Writing prose.
    resp = client.post(
        f"/api/stories/{story_id}/turns", json={"user_input": "Continue the story."}
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["disposition"] == "delivered", body
    assert body["visible_state"]["play_status"] == "in_play"
    turn_id = UUID(body["turn_id"])

    session = client.app.state.session_factory()
    try:
        turn = get_turn_for_eligibility(session, turn_id)
        assert turn is not None
        assert turn.mode_metadata is not None
        assert (
            turn.mode_metadata.work_product_kind
            == WritingWorkProductKind.PROSE_CONTINUATION.value
        )
        assert (
            turn.mode_metadata.canon_eligibility
            == WritingCanonEligibility.EXTRACTOR_ELIGIBLE.value
        )

        decision = gather_turn_eligibility(session, turn_id, StoryMode.WRITING)
        assert decision.eligible is True, decision.reason
    finally:
        session.close()


def test_visible_state_reflects_promotion_even_if_row_was_cached_pre_turn(
    fake_provider_client,  # type: ignore[no-untyped-def]
) -> None:
    """Round 16 remediation (PR #126 P2): the route's session is opened once
    for the whole request; derive_writing_turn_request() reads
    WritingSessionState *before* orchestrate_turn() runs, which promotes
    play_status to IN_PLAY in its own, separate session and commits there.
    If the route's own session had already cached that row in its identity
    map, a plain re-query for build_visible_state() would return the
    pre-turn SETUP attributes instead of the orchestrator's committed
    write -- the ORM does not overwrite an already-loaded object from a
    fresh SELECT by default.

    In production this session normally does not retain a strong reference
    to the row across derive_writing_turn_request() (CPython frees it
    immediately, evicting it from the identity map before build_visible_state
    re-queries), which is exactly why this is worth pinning down with a test
    rather than trusting it to keep working by accident: any future change
    that holds a reference to the row for longer (a cache, a relationship
    load, a debugger) would silently resurrect the staleness. This test
    forces that worst case directly, by wrapping the app's session_factory
    so the very first WritingSessionState read on the route's session is
    pre-loaded and kept alive for the whole request -- then asserts the
    response still reflects the orchestrator's committed IN_PLAY promotion.

    Uses BYOK (not hosted) access so no settlement write runs: hosted
    settlement's own credit-deduction commit would itself expire the whole
    session as a side effect (SQLAlchemy's default expire_on_commit=True),
    incidentally masking the exact staleness this test exists to force
    independent of any other code path's behavior.
    """
    client = fake_provider_client
    _seed_byok_entitlement(client)
    story_id = _create_writing_story_with_persona(client)

    # Pre-create the turn-anchor node so _submit_turn_sync's own
    # ensure_story_turn_anchor_node() call below is a no-op (anchor.created
    # is False). Otherwise its own "anchor just created" pre-turn commit
    # would expire the whole session (SQLAlchemy's default
    # expire_on_commit=True) before build_visible_state() ever runs -- which
    # would mask the exact staleness this test forces, independent of
    # whether the expire_all() fix is present.
    from afterworlds.api.story_bootstrap import ensure_story_turn_anchor_node

    anchor_session = client.app.state.session_factory()
    try:
        ensure_story_turn_anchor_node(anchor_session, UUID(story_id), StoryMode.WRITING)
        anchor_session.commit()
    finally:
        anchor_session.close()

    real_factory = client.app.state.session_factory
    held_refs = []  # keeps the pre-turn ORM row alive for the whole request

    def forcing_factory():  # type: ignore[no-untyped-def]
        session = real_factory()
        row = session.scalars(
            select(WritingSessionStateORM).where(
                WritingSessionStateORM.story_id == story_id
            )
        ).first()
        assert row is not None
        assert row.play_status == "setup"
        held_refs.append(row)  # forces identity-map retention past this call
        return session

    from afterworlds.api.routes.turns import _submit_turn_sync

    response = _submit_turn_sync(
        forcing_factory,
        client.app.state.orchestrator,
        _AlwaysByokReady(),
        UUID(story_id),
        client.app.state.sojourner_id,
        "Let's begin.",
    )

    assert response.disposition is PipelineDisposition.DELIVERED
    assert response.visible_state is not None
    assert response.visible_state.play_status == "in_play"


def test_writing_turn_before_setup_stays_non_canon(
    fake_provider_client,  # type: ignore[no-untyped-def]
) -> None:
    """Regression guard for the SETUP side of the round-5 fix: a Writing
    story that has not completed setup (play_status still SETUP) must keep
    getting no derived ``writing_turn_request`` -- the orchestrator's
    existing SETUP-forcing logic still applies unchanged."""
    client = fake_provider_client
    _seed_hosted_entitlement(client)

    resp = client.post("/api/stories", json={"title": "T", "mode": "writing"})
    assert resp.status_code == 201, resp.text
    story_id = resp.json()["story_id"]

    resp = client.post(
        f"/api/stories/{story_id}/turns", json={"user_input": "Hello there."}
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    turn_id = UUID(body["turn_id"])

    session = client.app.state.session_factory()
    try:
        turn = get_turn_for_eligibility(session, turn_id)
        assert turn is not None
        assert turn.mode_metadata is not None
        assert (
            turn.mode_metadata.canon_eligibility
            == WritingCanonEligibility.NON_CANON_SUPPORT.value
        )
    finally:
        session.close()


def test_writing_turn_with_missing_session_state_does_not_invent_provenance(
    fake_provider_client,  # type: ignore[no-untyped-def]
) -> None:
    """P1 fail-closed requirement (PR #126 review round 5): if a Writing
    story's session state row is missing/corrupt, the route must not invent
    a derived ``writing_turn_request`` -- it must behave exactly as it did
    before this fix (no provenance derivation at all), leaving whatever
    already-existing typed handling applies."""
    client = fake_provider_client
    _seed_hosted_entitlement(client)
    story_id = _create_writing_story_with_persona(client)

    session = client.app.state.session_factory()
    try:
        state = get_writing_session_state_by_story(session, UUID(story_id))
        assert state is not None
        delete_writing_session_state(session, state.session_id)
        session.commit()
    finally:
        session.close()

    resp = client.post(
        f"/api/stories/{story_id}/turns", json={"user_input": "Continue the story."}
    )
    assert resp.status_code == 200, resp.text


def test_fake_provider_path_classifies_without_anthropic_api_key(
    fake_provider_client,  # type: ignore[no-untyped-def]
    monkeypatch,  # type: ignore[no-untyped-def]
) -> None:
    """Round 6 remediation (PR #126 P1) test: fake-provider CI mode must
    still classify (via FakeProviderAdapter's "intent_classifier" branch,
    reusing fake_intent_model_caller's canned response) with no
    ANTHROPIC_API_KEY set at all -- proving this path makes no real/external
    provider calls end-to-end through the actual product wiring."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    client = fake_provider_client
    _seed_hosted_entitlement(client)
    story_id = _create_writing_story_with_persona(client)

    resp = client.post(
        f"/api/stories/{story_id}/turns", json={"user_input": "Continue the story."}
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["disposition"] == "delivered", body
    assert body["pipeline_error_summary"] is None


def test_true_cyoa_freeform_turn_after_setup_is_interaction_rejected(
    fake_provider_client,  # type: ignore[no-untyped-def]
) -> None:
    """Round 7 remediation (PR #126 P1) regression: before this fix, Branching
    setup never promoted play_status past SETUP, so this freeform turn would
    have fallen through to the ordinary prose Writer path (delivered) instead
    of reaching the orchestrator's in-play True CYOA INTERACTION_REJECTED
    rail. The fake classifier's fixed in_character_action intent is exactly
    "not BRANCH_CHOICE", satisfying that rail's gate."""
    client = fake_provider_client
    _seed_hosted_entitlement(client)

    resp = client.post("/api/stories", json={"title": "T", "mode": "branching"})
    assert resp.status_code == 201, resp.text
    story_id = resp.json()["story_id"]

    resp = client.post(
        f"/api/stories/{story_id}/setup",
        json={
            "mode": "branching",
            "interaction_style": "true_cyoa",
            "branching_cadence": "balanced",
        },
    )
    assert resp.status_code == 200, resp.text

    resp = client.post(
        f"/api/stories/{story_id}/turns",
        json={"user_input": "I ignore the options and climb the wall."},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["disposition"] == "interaction_rejected", body


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


def test_writing_turn_delivers_even_when_persona_registry_is_stale(
    fake_provider_client,  # type: ignore[no-untyped-def]
) -> None:
    """Round 9 remediation (PR #126 P2) regression: ``POST /turns`` calls
    ``build_visible_state()`` after ``orchestrate_turn()`` has already
    produced a deliverable turn result.

    The orchestrator has its own, independent persona-registry guard
    (``pipeline/orchestrator/service.py``), but it only fires for IN_PLAY
    Writing turns -- a SETUP-phase turn with a persona_id already persisted
    (a legacy/partial-data shape: persona set but not yet promoted, reachable
    only via direct persistence, not the real setup route, which always sets
    both persona_id and specific_goals together) skips that guard entirely
    and reaches the ordinary base-mode Writer path. Before this fix, the
    post-orchestration ``build_visible_state()`` re-fetch would then raise
    ``ValueError`` from ``WritingVisibleStateService.build()``, turning a
    valid delivered turn into an unhandled 500 instead of a normal response
    with ``visible_state: null``.
    """
    client = fake_provider_client
    _seed_hosted_entitlement(client)

    resp = client.post("/api/stories", json={"title": "T", "mode": "writing"})
    assert resp.status_code == 201, resp.text
    story_id = resp.json()["story_id"]

    # Bypass the setup route (which always sets persona_id and specific_goals
    # together, promoting straight to IN_PLAY) -- directly persist a
    # persona_id on the auto-bootstrapped SETUP-phase row instead, to reach
    # the SETUP-phase-with-persona-set shape the orchestrator's own guard
    # does not cover.
    session = client.app.state.session_factory()
    try:
        state = get_writing_session_state_by_story(session, UUID(story_id))
        assert state is not None
        update_writing_session_state(
            session, state.model_copy(update={"persona_id": "does-not-exist"})
        )
        session.commit()
    finally:
        session.close()

    resp = client.post(
        f"/api/stories/{story_id}/turns",
        json={"user_input": "Tell me a story about the sea."},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["disposition"] == "delivered", body
    assert body["visible_state"] is None
