"""Prerequisite #205 §1/§2/§5: effects are fenced against closure/suppression,
and owning-service seams refuse unscoped or cross-account calls.

The Writer pass of a real fake-provider Branching turn is held open with an
Event while the same account is closed from a second session.
"""

from __future__ import annotations

import threading
import uuid
from datetime import UTC, datetime
from typing import Any

import pytest
import sqlalchemy as sa

from afterworlds.api.fake_pipeline import FakeProviderAdapter
from afterworlds.persistence.orm.node import TurnORM
from afterworlds.remote.access import (
    DelayedWorkScope,
    StoryAccessDenied,
    work_scope,
)
from afterworlds.remote.storage import record_suppression
from tests.api._remote import PASSWORD, RemoteHarness
from tests.api.test_remote_isolation import _branching_in_play, _seed_hosted


def _turns(remote: RemoteHarness) -> int:
    with remote.app.state.session_factory() as s:
        return int(s.scalar(sa.select(sa.func.count()).select_from(TurnORM)) or 0)


class _PausedWriter:
    def __init__(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self.armed = False
        self.entered = threading.Event()
        self.release = threading.Event()
        real = FakeProviderAdapter.call

        def call(adapter: Any, request: Any) -> Any:
            if self.armed and request.pass_id.value == "writer":
                self.armed = False
                self.entered.set()
                assert self.release.wait(30)
            return real(adapter, request)

        monkeypatch.setattr(FakeProviderAdapter, "call", call)


def _in_thread(fn: Any) -> tuple[threading.Thread, list[Any]]:
    out: list[Any] = []
    thread = threading.Thread(target=lambda: out.append(fn()), daemon=True)
    thread.start()
    return thread, out


def _turn_setup(remote: RemoteHarness) -> tuple[Any, Any, str]:
    a = remote.enroll("a@example.test")
    _seed_hosted(remote, remote.account_id(a))
    sid = _branching_in_play(a)
    closer = remote.client()
    closer.post(
        "/api/auth/sign-in",
        json={"contact_address": "a@example.test", "password": PASSWORD},
    )
    return a, closer, sid


def test_closure_waits_for_the_in_flight_turn_and_nothing_lands_after_it(
    remote: RemoteHarness, monkeypatch: pytest.MonkeyPatch
) -> None:
    writer = _PausedWriter(monkeypatch)
    a, closer, sid = _turn_setup(remote)
    before = _turns(remote)
    writer.armed = True
    turn, turn_out = _in_thread(
        lambda: a.post(f"/api/stories/{sid}/turns", json={"user_input": "I wait."})
    )
    assert writer.entered.wait(30)

    def close() -> tuple[int, int]:
        resp = closer.post("/api/account/close", json={"password": PASSWORD})
        return resp.status_code, _turns(remote)  # Turns when closure returned

    closing, close_out = _in_thread(close)
    closing.join(0.5)
    assert closing.is_alive()  # closure is waiting on the in-flight turn
    writer.release.set()
    turn.join(60)
    closing.join(60)
    assert turn_out[0].status_code == 200
    status, turns_at_close = close_out[0]
    assert status == 200
    # Every effect of the admitted turn landed before closure completed.
    assert turns_at_close == _turns(remote) > before
    assert a.get("/api/stories").status_code == 401


def test_closure_that_cannot_drain_changes_nothing(
    remote: RemoteHarness, monkeypatch: pytest.MonkeyPatch
) -> None:
    writer = _PausedWriter(monkeypatch)
    a, closer, sid = _turn_setup(remote)
    remote.app.state.close_fence_timeout = 0.3
    writer.armed = True
    turn, turn_out = _in_thread(
        lambda: a.post(f"/api/stories/{sid}/turns", json={"user_input": "I wait."})
    )
    assert writer.entered.wait(30)
    resp = closer.post("/api/account/close", json={"password": PASSWORD})
    assert resp.status_code == 409
    assert resp.json()["error_code"] == "account_operation_in_progress"
    writer.release.set()
    turn.join(60)
    assert turn_out[0].status_code == 200
    # Not closed: both sessions still work.
    assert closer.get("/api/stories").status_code == 200
    assert a.get("/api/stories").status_code == 200


def test_requests_are_refused_while_closure_holds_the_fence(
    remote: RemoteHarness, monkeypatch: pytest.MonkeyPatch
) -> None:
    writer = _PausedWriter(monkeypatch)
    a, closer, sid = _turn_setup(remote)
    third = remote.client()
    third.post(
        "/api/auth/sign-in",
        json={"contact_address": "a@example.test", "password": PASSWORD},
    )
    writer.armed = True
    turn, _ = _in_thread(
        lambda: a.post(f"/api/stories/{sid}/turns", json={"user_input": "I wait."})
    )
    assert writer.entered.wait(30)
    closing, close_out = _in_thread(
        lambda: closer.post("/api/account/close", json={"password": PASSWORD})
    )
    closing.join(0.5)
    resp = third.post("/api/stories", json={"title": "late", "mode": "branching"})
    assert resp.status_code == 409  # no new admission while closure waits
    writer.release.set()
    turn.join(60)
    closing.join(60)
    assert close_out[0].status_code == 200
    assert third.get("/api/stories").status_code == 401


def test_suppression_under_the_fence_stops_later_work(remote: RemoteHarness) -> None:
    a = remote.enroll("a@example.test")
    account = uuid.UUID(remote.account_id(a))
    sid = a.post("/api/stories", json={"title": "S", "mode": "branching"}).json()[
        "story_id"
    ]
    fence = remote.app.state.account_fence
    with fence.exclusive(account, timeout=5):
        assert a.get(f"/api/stories/{sid}").status_code == 409
        record_suppression(
            remote.app.state.control_factory,
            subject_ref=str(account),
            story_refs=[sid],
            request_id="r",
            scope="story",
            effective_boundary_at=datetime.now(UTC),
            now=datetime.now(UTC),
        )
    assert a.get(f"/api/stories/{sid}").status_code == 404


def test_owning_service_seams_refuse_unscoped_and_cross_account_calls(
    remote: RemoteHarness,
) -> None:
    a = remote.enroll("a@example.test")
    b = remote.enroll("b@example.test")
    sid = uuid.UUID(
        a.post("/api/stories", json={"title": "S", "mode": "branching"}).json()[
            "story_id"
        ]
    )
    a_id, b_id = uuid.UUID(remote.account_id(a)), uuid.UUID(remote.account_id(b))
    orchestrator = remote.app.state.orchestrator
    actions = remote.app.state.rpg_actions
    for call in (
        lambda: orchestrator.orchestrate_turn(sid, "x", sojourner_id=a_id),
        lambda: actions.current(sid),
    ):
        with pytest.raises(StoryAccessDenied):
            call()  # no trusted scope
        with (
            work_scope(DelayedWorkScope(b_id, None, "direct")),
            pytest.raises(StoryAccessDenied),
        ):
            call()  # another account's scope
    with work_scope(DelayedWorkScope(a_id, None, "direct")):
        with pytest.raises(StoryAccessDenied):
            # The scope's account must be the entitlement subject passed.
            orchestrator.orchestrate_turn(sid, "x", sojourner_id=b_id)
        assert actions.current(sid) is None  # owner's own scope passes


def test_fenced_suppression_waits_for_the_in_flight_turn(
    remote: RemoteHarness, monkeypatch: pytest.MonkeyPatch
) -> None:
    from afterworlds.remote.access import FenceBusy, record_suppression_fenced

    writer = _PausedWriter(monkeypatch)
    a, _closer, sid = _turn_setup(remote)
    account = uuid.UUID(remote.account_id(a))
    before = _turns(remote)
    writer.armed = True
    turn, turn_out = _in_thread(
        lambda: a.post(f"/api/stories/{sid}/turns", json={"user_input": "I wait."})
    )
    assert writer.entered.wait(30)

    def suppress(timeout: float) -> tuple[str, int]:
        sup = record_suppression_fenced(
            remote.app.state.account_fence,
            remote.app.state.control_factory,
            account_id=account,
            story_refs=[sid],
            request_id="r",
            scope="story",
            effective_boundary_at=datetime.now(UTC),
            now=datetime.now(UTC),
            timeout=timeout,
        )
        return sup, _turns(remote)

    # A bounded wait that expires records nothing.
    with pytest.raises(FenceBusy):
        suppress(0.2)
    assert a.get(f"/api/stories/{sid}").status_code == 200
    suppressing, out = _in_thread(lambda: suppress(30))
    suppressing.join(0.5)
    assert suppressing.is_alive()  # waiting on the admitted turn
    writer.release.set()
    turn.join(60)
    suppressing.join(60)
    assert turn_out[0].status_code == 200
    _sup, turns_at_return = out[0]
    assert turns_at_return == _turns(remote) > before  # nothing landed after
    assert a.get(f"/api/stories/{sid}").status_code == 404
