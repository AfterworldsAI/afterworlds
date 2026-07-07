"""Turn submission: entitlement gating, disposition envelope, and the
Binding Decision 8 per-story lock.

The real orchestrator makes real provider calls, so these tests inject a
stub via ``app.dependency_overrides[get_orchestrator]`` -- exactly the
seam ``api/deps.py::get_orchestrator`` exists for.
"""

from __future__ import annotations

import contextlib
import threading
import time
from uuid import UUID, uuid4

from afterworlds.api.deps import get_orchestrator
from afterworlds.entitlement.service import EntitlementService
from tests.api._fixtures import make_delivered_result, make_pipeline_error_result
from tests.entitlement.conftest import (
    activate_byok,
    activate_hosted,
    grant_subscription_credits,
)


class _StubOrchestrator:
    def __init__(self, result_factory, *, delay: float = 0.0):
        self._result_factory = result_factory
        self._delay = delay
        self.calls: list[tuple] = []

    def orchestrate_turn(
        self, story_id, node_id, user_input, sojourner_id, access_path, **kw
    ):
        self.calls.append((story_id, node_id, user_input, sojourner_id, access_path))
        if self._delay:
            time.sleep(self._delay)
        return self._result_factory()


def _create_story(client) -> str:  # type: ignore[no-untyped-def]
    resp = client.post("/api/stories", json={"title": "T", "mode": "writing"})
    assert resp.status_code == 201, resp.text
    return resp.json()["story_id"]  # type: ignore[no-any-return]


def _seed_hosted(client) -> None:  # type: ignore[no-untyped-def]
    session = client.app.state.session_factory()
    try:
        service = EntitlementService(session)
        sojourner_id = client.app.state.sojourner_id
        activate_hosted(service, sojourner_id)
        grant_subscription_credits(service, sojourner_id)
        session.commit()
    finally:
        session.close()


def _seed_byok(client) -> None:  # type: ignore[no-untyped-def]
    session = client.app.state.session_factory()
    try:
        service = EntitlementService(session)
        activate_byok(service, client.app.state.sojourner_id)
        session.commit()
    finally:
        session.close()


def test_no_entitlement_blocks_before_orchestrator_call(client) -> None:  # type: ignore[no-untyped-def]
    story_id = _create_story(client)
    stub = _StubOrchestrator(make_pipeline_error_result)
    client.app.dependency_overrides[get_orchestrator] = lambda: stub

    resp = client.post(f"/api/stories/{story_id}/turns", json={"user_input": "hello"})
    assert resp.status_code == 403
    assert resp.json()["error_code"] == "entitlement_blocked"
    assert stub.calls == []


def test_byok_licensed_without_credentials_blocks(client) -> None:  # type: ignore[no-untyped-def]
    story_id = _create_story(client)
    _seed_byok(client)
    stub = _StubOrchestrator(make_pipeline_error_result)
    client.app.dependency_overrides[get_orchestrator] = lambda: stub

    resp = client.post(f"/api/stories/{story_id}/turns", json={"user_input": "hello"})
    assert resp.status_code == 403
    assert resp.json()["error_code"] == "byok_credentials_required"
    assert stub.calls == []


def test_delivered_turn_settles_hosted_cost(client) -> None:  # type: ignore[no-untyped-def]
    story_id = _create_story(client)
    _seed_hosted(client)
    turn_id = uuid4()
    stub = _StubOrchestrator(lambda: make_delivered_result(turn_id))
    client.app.dependency_overrides[get_orchestrator] = lambda: stub

    resp = client.post(f"/api/stories/{story_id}/turns", json={"user_input": "hello"})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["disposition"] == "delivered"
    assert body["turn_id"] == str(turn_id)
    assert body["settlement_warning"] is None
    assert len(stub.calls) == 1
    assert stub.calls[0][4].value == "hosted"

    # Settlement actually ran: a CREDIT_DEDUCTION event exists for this turn.
    from afterworlds.entitlement.orm import EntitlementEvent

    session = client.app.state.session_factory()
    try:
        events = (
            session.query(EntitlementEvent)
            .filter(EntitlementEvent.turn_id == turn_id)
            .all()
        )
        assert len(events) == 1
    finally:
        session.close()


def test_settlement_failure_survives_turn_and_surfaces_warning(client) -> None:  # type: ignore[no-untyped-def]
    """Binding Decision 5 / DoR-D: settlement failure never rolls back or
    hides the delivered turn -- it's a non-blocking warning field."""
    story_id = _create_story(client)
    _seed_hosted(client)
    turn_id = uuid4()
    stub = _StubOrchestrator(
        lambda: make_delivered_result(turn_id, with_usage_metrics=False)
    )
    client.app.dependency_overrides[get_orchestrator] = lambda: stub

    resp = client.post(f"/api/stories/{story_id}/turns", json={"user_input": "hello"})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["disposition"] == "delivered"
    assert body["turn_id"] == str(turn_id)
    assert body["settlement_warning"] is not None

    from afterworlds.entitlement.orm import EntitlementEvent

    session = client.app.state.session_factory()
    try:
        events = (
            session.query(EntitlementEvent)
            .filter(EntitlementEvent.turn_id == turn_id)
            .all()
        )
        # No acknowledgement/deduction row created on settlement failure.
        assert events == []
    finally:
        session.close()


def test_pipeline_error_result_returns_200_with_envelope(client) -> None:  # type: ignore[no-untyped-def]
    story_id = _create_story(client)
    _seed_hosted(client)
    stub = _StubOrchestrator(lambda: make_pipeline_error_result("boom"))
    client.app.dependency_overrides[get_orchestrator] = lambda: stub

    resp = client.post(f"/api/stories/{story_id}/turns", json={"user_input": "hello"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["disposition"] == "pipeline_error"
    assert body["pipeline_error_summary"] == "boom"
    assert body["turn_id"] is None


def test_extra_field_in_request_rejected(client) -> None:  # type: ignore[no-untyped-def]
    story_id = _create_story(client)
    resp = client.post(
        f"/api/stories/{story_id}/turns",
        json={"user_input": "hello", "access_path": "byok"},
    )
    assert resp.status_code == 422


def test_missing_story_returns_404(client) -> None:  # type: ignore[no-untyped-def]
    resp = client.post(f"/api/stories/{uuid4()}/turns", json={"user_input": "hi"})
    assert resp.status_code == 404


def test_concurrent_submissions_same_story_one_call_one_409(client) -> None:  # type: ignore[no-untyped-def]
    story_id = _create_story(client)
    _seed_hosted(client)
    stub = _StubOrchestrator(make_delivered_result, delay=0.3)
    client.app.dependency_overrides[get_orchestrator] = lambda: stub

    results: list[int] = []

    def _fire() -> None:
        r = client.post(f"/api/stories/{story_id}/turns", json={"user_input": "x"})
        results.append(r.status_code)

    t1 = threading.Thread(target=_fire)
    t1.start()
    time.sleep(0.05)  # let t1 acquire the lock first
    t2 = threading.Thread(target=_fire)
    t2.start()
    t1.join(timeout=5)
    t2.join(timeout=5)

    assert sorted(results) == [200, 409]
    assert len(stub.calls) == 1


def test_concurrent_submissions_different_stories_do_not_serialize(client) -> None:  # type: ignore[no-untyped-def]
    story_a = _create_story(client)
    story_b = _create_story(client)
    _seed_hosted(client)
    stub = _StubOrchestrator(make_delivered_result, delay=0.3)
    client.app.dependency_overrides[get_orchestrator] = lambda: stub

    results: dict[str, int] = {}

    def _fire(story_id: str) -> None:
        r = client.post(f"/api/stories/{story_id}/turns", json={"user_input": "x"})
        results[story_id] = r.status_code

    start = time.monotonic()
    t1 = threading.Thread(target=_fire, args=(story_a,))
    t2 = threading.Thread(target=_fire, args=(story_b,))
    t1.start()
    t2.start()
    t1.join(timeout=5)
    t2.join(timeout=5)
    elapsed = time.monotonic() - start

    assert results == {story_a: 200, story_b: 200}
    # Serialized would take ~2x the per-call delay; concurrent should be ~1x.
    assert elapsed < 0.55


def test_lock_released_after_delivered_non_delivered_and_error(client) -> None:  # type: ignore[no-untyped-def]
    story_id = _create_story(client)
    _seed_hosted(client)
    story_uuid = UUID(story_id)

    for result_factory in (make_delivered_result, make_pipeline_error_result):
        stub = _StubOrchestrator(result_factory)
        client.app.dependency_overrides[get_orchestrator] = lambda s=stub: s
        resp = client.post(f"/api/stories/{story_id}/turns", json={"user_input": "x"})
        assert resp.status_code == 200
        assert not client.app.state.story_locks[story_uuid].locked()

    def _raise(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise RuntimeError("unexpected")

    stub = _StubOrchestrator(make_delivered_result)
    stub.orchestrate_turn = _raise  # type: ignore[method-assign]
    client.app.dependency_overrides[get_orchestrator] = lambda: stub
    # Starlette's TestClient re-raises exceptions handled only by the
    # top-level Exception handler (so uvicorn-style server logs still see
    # them); the route's `finally: lock.release()` already ran server-side
    # by the time it propagates here.
    with contextlib.suppress(RuntimeError):
        client.post(f"/api/stories/{story_id}/turns", json={"user_input": "x"})
    assert not client.app.state.story_locks[story_uuid].locked()
