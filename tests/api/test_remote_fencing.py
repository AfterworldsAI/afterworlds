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
from afterworlds.api.story_bootstrap import ensure_story_turn_anchor_node
from afterworlds.entitlement.enums import RuntimeAccessPath
from afterworlds.models.enums import StoryMode
from afterworlds.persistence.orm.node import TurnORM
from afterworlds.remote.access import (
    DelayedWorkScope,
    StoryAccessDenied,
    work_scope,
)
from afterworlds.remote.storage import record_suppression
from tests.api._remote import PASSWORD, RemoteHarness
from tests.api.test_remote_isolation import _branching_in_play, _seed_hosted

HOSTED = RuntimeAccessPath.HOSTED


def _anchor(remote: RemoteHarness, sid: Any) -> uuid.UUID:
    with remote.app.state.session_factory() as s:
        node = ensure_story_turn_anchor_node(
            s, uuid.UUID(str(sid)), StoryMode.BRANCHING
        )
        s.commit()
        return node.node_id


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
    remote.app.state.identity.close_fence_timeout = 0.3
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
    node = _anchor(remote, sid)
    for call in (
        lambda: orchestrator.orchestrate_turn(sid, node, "x", a_id, HOSTED),
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
        # The scope's account must be the entitlement subject, however the
        # caller spells the arguments (review P1-A).
        for mismatched in (
            lambda: orchestrator.orchestrate_turn(sid, node, "x", b_id, HOSTED),
            lambda: orchestrator.orchestrate_turn(
                sid, node, "x", sojourner_id=b_id, access_path=HOSTED
            ),
            lambda: orchestrator.orchestrate_turn(
                story_id=sid,
                node_id=node,
                user_input="x",
                sojourner_id=b_id,
                access_path=HOSTED,
            ),
            lambda: orchestrator.orchestrate_branching_start(sid, node, b_id, HOSTED),
            lambda: orchestrator.orchestrate_branching_start(
                sid, node, sojourner_id=b_id, access_path=HOSTED
            ),
            lambda: orchestrator.orchestrate_rpg_resume(
                sid, node, uuid.uuid4(), access_path=HOSTED, sojourner_id=b_id
            ),
        ):
            with pytest.raises(StoryAccessDenied):
                mismatched()
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


def test_direct_scoped_work_holds_the_fence_against_http_closure(
    remote: RemoteHarness, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Review P1-B (1): an accepted direct service call holds the account
    fence for its lifetime, so HTTP closure waits for its late commit."""
    writer = _PausedWriter(monkeypatch)
    a, closer, sid = _turn_setup(remote)
    account = uuid.UUID(remote.account_id(a))
    node = _anchor(remote, sid)
    before = _turns(remote)
    writer.armed = True

    def direct_turn() -> Any:
        with work_scope(DelayedWorkScope(account, None, "direct")):
            return remote.app.state.orchestrator.orchestrate_turn(
                uuid.UUID(sid), node, "I act directly.", account, HOSTED
            )

    work, work_out = _in_thread(direct_turn)
    assert writer.entered.wait(30)

    def close() -> tuple[int, int]:
        resp = closer.post("/api/account/close", json={"password": PASSWORD})
        return resp.status_code, _turns(remote)

    closing, close_out = _in_thread(close)
    closing.join(0.5)
    assert closing.is_alive()
    writer.release.set()
    work.join(60)
    closing.join(60)
    assert work_out[0].disposition.value == "delivered"
    status, turns_at_close = close_out[0]
    assert status == 200
    assert turns_at_close == _turns(remote) > before


def test_direct_service_closure_waits_for_the_http_turn(
    remote: RemoteHarness, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Review P1-B (2): IdentityService.close_account takes the fence itself."""
    from afterworlds.remote.identity import SessionContext

    writer = _PausedWriter(monkeypatch)
    a, closer, sid = _turn_setup(remote)
    identity = remote.app.state.identity
    actor = identity.resolve(closer.cookies.get("aw_session"), SessionContext.SOJOURNER)
    before = _turns(remote)
    writer.armed = True
    turn, turn_out = _in_thread(
        lambda: a.post(f"/api/stories/{sid}/turns", json={"user_input": "I wait."})
    )
    assert writer.entered.wait(30)

    def close() -> int:
        identity.close_account(actor, PASSWORD)
        return _turns(remote)

    closing, close_out = _in_thread(close)
    closing.join(0.5)
    assert closing.is_alive()
    writer.release.set()
    turn.join(60)
    closing.join(60)
    assert turn_out[0].status_code == 200
    assert close_out[0] == _turns(remote) > before
    assert a.get("/api/stories").status_code == 401


def test_account_suppression_admits_no_new_story(remote: RemoteHarness) -> None:
    """Review P1-C: after an account-scope suppression returns, a still-valid
    session cannot create account-owned data; other accounts are unaffected."""
    from afterworlds.remote.access import record_suppression_fenced

    a = remote.enroll("a@example.test")
    b = remote.enroll("b@example.test")
    account = uuid.UUID(remote.account_id(a))
    record_suppression_fenced(
        remote.app.state.account_fence,
        remote.app.state.control_factory,
        account_id=account,
        story_refs=[],
        request_id="r",
        scope="account",
        effective_boundary_at=datetime.now(UTC),
        now=datetime.now(UTC),
        timeout=5,
    )
    resp = a.post("/api/stories", json={"title": "late", "mode": "branching"})
    assert resp.status_code == 409
    assert resp.json()["error_code"] == "account_operation_in_progress"
    assert a.get("/api/stories").json()["stories"] == []
    with remote.app.state.session_factory() as s:
        assert s.execute(sa.text("SELECT COUNT(*) FROM stories")).scalar() == 0
    assert (
        b.post("/api/stories", json={"title": "B", "mode": "branching"}).status_code
        == 201
    )


class _PausedWrites:
    """A vector write service whose ingest pauses inside the inner effect."""

    def __init__(self) -> None:
        self.entered = threading.Event()
        self.release = threading.Event()
        self.writes: list[str] = []

    def ingest_turn(self, story_id: Any, turn_id: Any, *_a: Any) -> None:
        self.entered.set()
        assert self.release.wait(30)
        self.writes.append(str(turn_id))

    def delete_turn(self, story_id: Any, turn_id: Any) -> None:
        self.writes.append(f"delete:{turn_id}")

    def count_for_story(self, story_id: Any) -> int:
        return 0

    def delete_story(self, story_id: Any) -> int:
        self.writes.append(f"delete-story:{story_id}")
        return 0


@pytest.mark.parametrize("terminal", ["http_closure", "fenced_suppression"])
def test_direct_guarded_vector_write_cannot_land_after_closure_or_suppression(
    remote: RemoteHarness, terminal: str
) -> None:
    """Review residue 1: a supported direct GuardedRetrievalWrites call holds
    the account fence for its lifetime; closure/suppression wait for it, and
    every later vector operation of that account/Story is refused."""
    from afterworlds.remote.access import record_suppression_fenced
    from afterworlds.remote.retrieval_guard import (
        GuardedRetrievalMemory,
        GuardedRetrievalWrites,
    )

    a = remote.enroll("a@example.test")
    closer = remote.client()
    closer.post(
        "/api/auth/sign-in",
        json={"contact_address": "a@example.test", "password": PASSWORD},
    )
    account = uuid.UUID(remote.account_id(a))
    sid = uuid.UUID(
        a.post("/api/stories", json={"title": "S", "mode": "branching"}).json()[
            "story_id"
        ]
    )
    inner = _PausedWrites()
    policy = remote.app.state.access_policy
    factory = remote.app.state.session_factory
    writes = GuardedRetrievalWrites(inner, policy, factory)  # type: ignore[arg-type]
    reads = GuardedRetrievalMemory(
        type("R", (), {"retrieve": lambda *_a: None})(), policy, factory
    )

    def direct_ingest() -> None:
        with work_scope(DelayedWorkScope(account, None, "direct")):
            writes.ingest_turn(sid, uuid.uuid4(), None, "branching", "prose", "t")

    work, _ = _in_thread(direct_ingest)
    assert inner.entered.wait(30)

    def finish_terminal() -> int:
        if terminal == "http_closure":
            assert (
                closer.post(
                    "/api/account/close", json={"password": PASSWORD}
                ).status_code
                == 200
            )
        else:
            record_suppression_fenced(
                remote.app.state.account_fence,
                remote.app.state.control_factory,
                account_id=account,
                story_refs=[str(sid)],
                request_id="r",
                scope="story",
                effective_boundary_at=datetime.now(UTC),
                now=datetime.now(UTC),
                timeout=30,
            )
        return len(inner.writes)  # writes when the terminal step returned

    finishing, out = _in_thread(finish_terminal)
    finishing.join(0.5)
    assert finishing.is_alive()  # waits for the admitted vector write
    inner.release.set()
    work.join(30)
    finishing.join(30)
    assert out[0] == len(inner.writes) == 1  # it landed before, not after
    with work_scope(DelayedWorkScope(account, None, "direct")):
        for late in (
            lambda: writes.ingest_turn(sid, uuid.uuid4(), None, "branching", "x", "t"),
            lambda: writes.delete_turn(sid, uuid.uuid4()),
            lambda: writes.count_for_story(sid),
            lambda: writes.delete_story(sid),
            lambda: reads.retrieve(sid, "q"),
        ):
            with pytest.raises(StoryAccessDenied):
                late()
    assert len(inner.writes) == 1


# -- review 5572565473 r4314625062: worker lifetime survives cancellation ----


def _cancel_admitted_request(
    remote: RemoteHarness, client_of: Any, method: str, path: str, **kwargs: Any
) -> Any:
    """Coroutine factory: send an admitted request through the ASGI app and
    cancel the request task itself (twice) once its worker is paused."""
    import asyncio
    import contextlib

    import httpx

    from afterworlds.api.remote_access import CSRF_HEADER

    async def send_and_cancel(entered: threading.Event, during: Any) -> Any:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=remote.app),
            base_url="https://testserver",
            cookies=dict(client_of.cookies),
            headers={CSRF_HEADER: "1"},
        ) as client:
            task = asyncio.create_task(client.request(method, path, **kwargs))
            assert await asyncio.to_thread(entered.wait, 30)
            task.cancel()
            await asyncio.sleep(0)
            task.cancel()  # repeated raw cancellation
            await asyncio.sleep(0.1)
            assert not task.done()  # the cancelled request drains its worker
            result = await during()  # must release the worker
            with contextlib.suppress(asyncio.CancelledError):
                await task
            assert task.cancelled()
            return result

    return send_and_cancel


@pytest.mark.parametrize("exclusive", ["closure", "suppression"])
def test_a_cancelled_turn_keeps_its_fence_and_story_lock_until_the_worker_ends(
    remote: RemoteHarness, monkeypatch: pytest.MonkeyPatch, exclusive: str
) -> None:
    import asyncio

    from afterworlds.remote.access import FenceBusy, record_suppression_fenced

    writer = _PausedWriter(monkeypatch)
    a, closer, sid = _turn_setup(remote)
    account = uuid.UUID(remote.account_id(a))
    before = _turns(remote)
    send_and_cancel = _cancel_admitted_request(
        remote, a, "POST", f"/api/stories/{sid}/turns", json={"user_input": "I wait."}
    )

    def close(timeout: float) -> tuple[int, int]:
        remote.app.state.identity.close_fence_timeout = timeout
        resp = closer.post("/api/account/close", json={"password": PASSWORD})
        return resp.status_code, _turns(remote)

    def suppress(timeout: float) -> tuple[int, int]:
        record_suppression_fenced(
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
        return 200, _turns(remote)

    async def during() -> tuple[int, int]:
        # The request is cancelled; its worker is paused before any effect.
        if exclusive == "closure":
            status, _ = await asyncio.to_thread(close, 0.3)
            assert status == 409  # bounded refusal, nothing changed
        else:
            with pytest.raises(FenceBusy):
                await asyncio.to_thread(suppress, 0.2)
        same_story = await asyncio.to_thread(
            closer.post, f"/api/stories/{sid}/turns", json={"user_input": "Me too."}
        )
        assert same_story.status_code == 409
        assert same_story.json()["error_code"] == "turn_in_flight"
        assert _turns(remote) == before
        waiting = asyncio.ensure_future(
            asyncio.to_thread(close if exclusive == "closure" else suppress, 30)
        )
        await asyncio.sleep(0.5)
        assert not waiting.done()  # exclusivity waits for the worker
        writer.release.set()
        return await waiting

    async def scenario() -> tuple[int, int]:
        writer.armed = True
        return await send_and_cancel(writer.entered, during)  # type: ignore[no-any-return]

    status, turns_at_return = asyncio.run(scenario())
    assert status == 200
    # The worker's effects all landed before exclusivity was granted.
    assert turns_at_return == _turns(remote) > before


def test_a_cancelled_setup_read_keeps_its_fence_until_the_worker_ends(
    remote: RemoteHarness, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The standalone RPG setup read can commit retained state: its worker
    owns a fence lease past request cancellation."""
    import asyncio

    from afterworlds.remote.access import FenceBusy, record_suppression_fenced

    a, _closer, sid = _turn_setup(remote)
    account = uuid.UUID(remote.account_id(a))
    entered, release = threading.Event(), threading.Event()
    order: list[str] = []

    def paused_read(*_a: Any) -> None:
        entered.set()
        assert release.wait(30)
        order.append("read committed")

    monkeypatch.setattr("afterworlds.api.routes.rpg_setup.read_setup_view", paused_read)
    send_and_cancel = _cancel_admitted_request(
        remote, a, "GET", f"/api/stories/{sid}/rpg/setup"
    )

    def suppress(timeout: float) -> None:
        record_suppression_fenced(
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
        order.append("suppressed")

    async def during() -> None:
        with pytest.raises(FenceBusy):
            await asyncio.to_thread(suppress, 0.2)
        waiting = asyncio.ensure_future(asyncio.to_thread(suppress, 30))
        await asyncio.sleep(0.5)
        assert not waiting.done()
        release.set()
        await waiting

    asyncio.run(send_and_cancel(entered, during))
    assert order == ["read committed", "suppressed"]


def _stories(remote: RemoteHarness) -> int:
    with remote.app.state.session_factory() as s:
        return int(s.execute(sa.text("SELECT COUNT(*) FROM stories")).scalar() or 0)


@pytest.mark.parametrize("exclusive", ["closure", "suppression"])
def test_a_cancelled_synchronous_handler_keeps_its_fence_until_it_ends(
    remote: RemoteHarness, monkeypatch: pytest.MonkeyPatch, exclusive: str
) -> None:
    """Residue: a synchronous effect handler (Story creation) runs as an
    admitted worker, so request cancellation cannot release its fence."""
    import asyncio

    import afterworlds.api.routes.stories as stories_routes
    from afterworlds.remote.access import FenceBusy, record_suppression_fenced

    a = remote.enroll("a@example.test")
    closer = remote.client()
    closer.post(
        "/api/auth/sign-in",
        json={"contact_address": "a@example.test", "password": PASSWORD},
    )
    account = uuid.UUID(remote.account_id(a))
    entered, release = threading.Event(), threading.Event()
    real = stories_routes.require_released_mode

    def paused(mode: Any) -> None:  # before any durable effect
        entered.set()
        assert release.wait(30)
        real(mode)

    monkeypatch.setattr(stories_routes, "require_released_mode", paused)
    send_and_cancel = _cancel_admitted_request(
        remote, a, "POST", "/api/stories", json={"title": "late", "mode": "branching"}
    )

    def exclusive_op(timeout: float) -> tuple[int, int]:
        if exclusive == "closure":
            remote.app.state.identity.close_fence_timeout = timeout
            status = closer.post(
                "/api/account/close", json={"password": PASSWORD}
            ).status_code
        else:
            try:
                record_suppression_fenced(
                    remote.app.state.account_fence,
                    remote.app.state.control_factory,
                    account_id=account,
                    story_refs=[],
                    request_id="r",
                    scope="account",
                    effective_boundary_at=datetime.now(UTC),
                    now=datetime.now(UTC),
                    timeout=timeout,
                )
                status = 200
            except FenceBusy:
                status = 409
        return status, _stories(remote)

    async def during() -> tuple[int, int]:
        assert await asyncio.to_thread(exclusive_op, 0.3) == (409, 0)
        waiting = asyncio.ensure_future(asyncio.to_thread(exclusive_op, 30))
        await asyncio.sleep(0.5)
        assert not waiting.done()
        release.set()
        return await waiting

    # The Story the handler was already admitted to create lands first.
    assert asyncio.run(send_and_cancel(entered, during)) == (200, 1)


def test_worker_protections_survive_repeated_cancellation() -> None:
    """Releasing depends on the synchronous worker's completion: repeated raw
    cancellation leaves the request draining, the Story lock held and the
    fence refused until the worker ends; a waiting exclusive comes after."""
    import asyncio
    import contextlib

    from afterworlds.api.deps import run_admitted_worker
    from afterworlds.remote.fence import AccountFence, FenceBusy, mark_fence_held

    fence, account = AccountFence(), uuid.uuid4()
    entered, release = threading.Event(), threading.Event()
    order: list[str] = []

    def work() -> None:
        entered.set()
        assert release.wait(30)
        order.append("effect")

    def take_exclusive(timeout: float) -> None:
        with fence.exclusive(account, timeout=timeout):
            order.append("exclusive")

    async def scenario() -> None:
        story_lock = asyncio.Lock()

        async def request() -> None:
            with fence.shared(account):  # the request's own admission lease
                mark_fence_held(account, fence)
                await story_lock.acquire()
                await run_admitted_worker(story_lock, work)
                order.append("request returned")  # never: it was cancelled

        task = asyncio.ensure_future(request())
        assert await asyncio.to_thread(entered.wait, 30)
        for _ in range(3):
            task.cancel()
            await asyncio.sleep(0)
        assert not task.done()  # draining the worker, not abandoning it
        assert story_lock.locked()
        with pytest.raises(FenceBusy):
            await asyncio.to_thread(take_exclusive, 0.2)
        waiting = asyncio.ensure_future(asyncio.to_thread(take_exclusive, 30))
        await asyncio.sleep(0.3)
        assert not waiting.done()
        release.set()
        with contextlib.suppress(asyncio.CancelledError):
            await task
        assert task.cancelled()
        await waiting
        assert not story_lock.locked()

    asyncio.run(scenario())
    assert order == ["effect", "exclusive"]


def test_a_failed_submission_keeps_no_protection() -> None:
    import asyncio

    import afterworlds.api.deps as deps
    from afterworlds.remote.fence import AccountFence, mark_fence_held

    fence, account = AccountFence(), uuid.uuid4()
    ran: list[str] = []

    class Refusing:
        def submit(self, *_a: Any, **_k: Any) -> Any:
            raise RuntimeError("executor unavailable")

    async def scenario() -> None:
        story_lock = asyncio.Lock()
        with fence.shared(account):
            mark_fence_held(account, fence)
            await story_lock.acquire()
            real = deps._WORKERS
            deps._WORKERS = Refusing()  # type: ignore[assignment]
            try:
                with pytest.raises(RuntimeError, match="executor unavailable"):
                    await deps.run_admitted_worker(story_lock, ran.append, "x")
            finally:
                deps._WORKERS = real
            await asyncio.sleep(0)
            assert not story_lock.locked()
        with fence.exclusive(account, timeout=0.1):  # no lease left behind
            pass

    asyncio.run(scenario())
    assert ran == []


@pytest.mark.parametrize("outcome", ["completes", "fails"])
def test_a_cancelled_story_creation_keeps_its_session_until_it_ends(
    remote: RemoteHarness, monkeypatch: pytest.MonkeyPatch, outcome: str
) -> None:
    """Paused after Story creation flushed and before its final commit: the
    cancelled request's dependency cleanup does not touch the worker's
    Session; the outcome is atomic (Story + ownership, or neither), and
    closure waits for it."""
    import asyncio

    import afterworlds.api.routes.stories as stories_routes

    a = remote.enroll("a@example.test")
    closer = remote.client()
    closer.post(
        "/api/auth/sign-in",
        json={"contact_address": "a@example.test", "password": PASSWORD},
    )
    entered, release = threading.Event(), threading.Event()
    real = stories_routes.ensure_mode_session_state

    def after_flush(session: Any, *a_: Any, **k: Any) -> Any:
        entered.set()  # create_story has flushed the Story row
        assert release.wait(30)
        if outcome == "fails":
            raise RuntimeError("worker failed before commit")
        return real(session, *a_, **k)

    monkeypatch.setattr(stories_routes, "ensure_mode_session_state", after_flush)
    send_and_cancel = _cancel_admitted_request(
        remote, a, "POST", "/api/stories", json={"title": "late", "mode": "branching"}
    )

    def counts() -> tuple[int, int]:
        with remote.app.state.session_factory() as s:
            return (
                int(s.execute(sa.text("SELECT COUNT(*) FROM stories")).scalar() or 0),
                int(
                    s.execute(
                        sa.text("SELECT COUNT(*) FROM account_resources")
                    ).scalar()
                    or 0
                ),
            )

    def close(timeout: float) -> tuple[int, tuple[int, int]]:
        remote.app.state.identity.close_fence_timeout = timeout
        resp = closer.post("/api/account/close", json={"password": PASSWORD})
        return resp.status_code, counts()

    async def during() -> tuple[int, tuple[int, int]]:
        assert await asyncio.to_thread(close, 0.3) == (409, (0, 0))
        waiting = asyncio.ensure_future(asyncio.to_thread(close, 30))
        await asyncio.sleep(0.5)
        assert not waiting.done()
        release.set()
        return await waiting

    status, at_close = asyncio.run(send_and_cancel(entered, during))
    assert status == 200
    assert at_close == ((1, 1) if outcome == "completes" else (0, 0))


def test_a_post_enqueue_submission_failure_never_runs_the_work() -> None:
    """A real executor whose thread start fails after the item was enqueued
    (CPython submit enqueues, then starts a thread): the request fails, its
    protections are released, and when a later submission starts a thread
    that drains the queue, the abandoned work never runs."""
    import asyncio
    from concurrent.futures import ThreadPoolExecutor

    import afterworlds.api.deps as deps
    from afterworlds.remote.fence import AccountFence, mark_fence_held

    fence, account = AccountFence(), uuid.uuid4()
    ran: list[str] = []
    executor = ThreadPoolExecutor(max_workers=1)
    real_start = threading.Thread.start

    def failing_start(self: threading.Thread) -> None:
        threading.Thread.start = real_start  # type: ignore[method-assign]
        raise RuntimeError("can't start new thread")

    async def scenario() -> None:
        story_lock = asyncio.Lock()
        real_workers = deps._WORKERS
        deps._WORKERS = executor
        try:
            with fence.shared(account):
                mark_fence_held(account, fence)
                await story_lock.acquire()
                threading.Thread.start = failing_start  # type: ignore[method-assign]
                try:
                    with pytest.raises(RuntimeError, match="start new thread"):
                        await deps.run_admitted_worker(
                            story_lock, ran.append, "abandoned"
                        )
                finally:
                    threading.Thread.start = real_start  # type: ignore[method-assign]
                assert executor._work_queue.qsize() == 1  # it was enqueued
                await asyncio.sleep(0)
                assert not story_lock.locked()  # released at once
                await story_lock.acquire()
                await deps.run_admitted_worker(story_lock, ran.append, "admitted")
                # One FIFO worker ran the abandoned item before this one.
                assert executor._work_queue.qsize() == 0
        finally:
            deps._WORKERS = real_workers
        executor.shutdown(wait=True)

    asyncio.run(scenario())
    assert ran == ["admitted"]
    with fence.exclusive(account, timeout=0.1):  # no lease left behind
        pass
