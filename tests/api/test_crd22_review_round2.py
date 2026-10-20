"""Codex review of f1580647 (CRD Issue 22 #206): proofs for the local
execution boundary, the export precondition at the deletion boundary,
positive delivery evidence, adjustment identity under concurrency and the
durable settlement source."""

from __future__ import annotations

import contextlib
import threading
import time
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest
import sqlalchemy as sa
from fastapi.testclient import TestClient

from afterworlds.api.app import create_app
from afterworlds.api.config import ApiSettings
from afterworlds.operations import deletion as deletion_module
from afterworlds.operations.orm import ExportArtifactORM, SupportActionEventORM
from afterworlds.operations.support import SupportService
from tests.api._remote import PASSWORD, RemoteHarness
from tests.operations._data import play_branching, rows_with


def _error(resp: Any) -> str:
    return str(resp.json()["error_code"])


def _request(
    c: Any, kind: str, scope: str, story_id: str | None = None
) -> dict[str, Any]:
    resp = c.post(
        "/api/data-requests", json={"kind": kind, "scope": scope, "story_id": story_id}
    )
    assert resp.status_code == 201, resp.text
    return dict(resp.json())


def _confirm(
    c: Any, req: dict[str, Any], password: str | None = None
) -> dict[str, Any]:
    preview = c.get(f"/api/data-requests/{req['request_id']}/deletion-preview").json()
    resp = c.post(
        f"/api/data-requests/{req['request_id']}/confirm",
        json={
            "expected_revision": req["revision"],
            "scope_revision": preview["scope_revision"],
            "password": password,
        },
    )
    assert resp.status_code == 200, resp.text
    return dict(resp.json()["request"])


def _approve(staff: Any, rid: str) -> None:
    view = staff.get(f"/api/admin/data-requests/{rid}").json()
    resp = staff.post(
        f"/api/admin/data-requests/{rid}/approve",
        json={"expected_revision": view["revision"], "reason": "verified owner"},
    )
    assert resp.status_code == 200, resp.text


def _execute(staff: Any, rid: str) -> dict[str, Any]:
    view = staff.get(f"/api/admin/data-requests/{rid}").json()
    resp = staff.post(
        f"/api/admin/data-requests/{rid}/execute",
        json={"expected_revision": view["revision"]},
    )
    assert resp.status_code == 200, resp.text
    return dict(resp.json())


def _phase(view: dict[str, Any], code: str) -> str | None:
    return next(
        (p["outcome_code"] for p in view["phases"] if p["phase_code"] == code), None
    )


def _seed_local(app: Any) -> None:
    from afterworlds.entitlement.enums import EntitlementEventType, HostedAccessPlan
    from afterworlds.entitlement.payloads import (
        HostedAccessActivatedPayload,
        SubscriptionCreditGrantPayload,
    )
    from afterworlds.entitlement.service import EntitlementService

    with app.state.session_factory() as s:
        service = EntitlementService(s)
        service.receive_entitlement_event(
            app.state.sojourner_id,
            EntitlementEventType.HOSTED_ACCESS_ACTIVATED,
            HostedAccessActivatedPayload(
                plan=HostedAccessPlan.SUBSCRIPTION, effective_at=datetime.now(UTC)
            ),
        )
        service.receive_entitlement_event(
            app.state.sojourner_id,
            EntitlementEventType.SUBSCRIPTION_CREDIT_GRANT,
            SubscriptionCreditGrantPayload(hosted_credit_delta=Decimal("100")),
        )


class TestLocalBoundary:
    """F1: local Story creation and turn admission are ordered with a local
    deletion's final scope."""

    def test_new_story_turn_cannot_survive_a_local_account_deletion(
        self, app_settings: ApiSettings, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("AFTERWORLDS_FAKE_PROVIDER", "1")
        app = create_app(app_settings)
        with TestClient(app) as c:
            _seed_local(app)
            s1 = play_branching(c, "Existing", "Hello.")
            req = _request(c, "deletion", "account")
            confirmed = _confirm(c, req)

            from afterworlds.api.routes import turns as turns_route

            gates = {s1: threading.Event()}
            entered = {s1: threading.Event()}
            real = turns_route.ensure_story_turn_anchor_node

            def held(session: Any, story_id: Any, mode: Any) -> Any:
                key = str(story_id)
                if key in gates:
                    entered[key].set()
                    assert gates[key].wait(30)
                return real(session, story_id, mode)

            monkeypatch.setattr(turns_route, "ensure_story_turn_anchor_node", held)
            t1 = threading.Thread(
                target=lambda: c.post(
                    f"/api/stories/{s1}/turns", json={"user_input": "x"}
                )
            )
            t1.start()
            assert entered[s1].wait(30)
            done: list[Any] = []
            d = threading.Thread(
                target=lambda: done.append(
                    c.post(
                        f"/api/data-requests/{req['request_id']}/execute",
                        json={"expected_revision": confirmed["revision"]},
                    )
                )
            )
            d.start()
            time.sleep(1.0)  # the deletion is waiting for the in-flight turn

            late: list[Any] = []
            created = c.post(
                "/api/stories", json={"title": "Late", "mode": "branching"}
            )
            if created.status_code == 201:
                s2 = str(created.json()["story_id"])
                gates[s2], entered[s2] = threading.Event(), threading.Event()
                real_inventory = deletion_module.ensure_inventory

                def inventory_then_turn(ctx: Any, view: Any) -> Any:
                    result = real_inventory(ctx, view)
                    gates[s2].set()  # the new Story's turn commits now
                    t2.join(30)
                    return result

                monkeypatch.setattr(
                    deletion_module, "ensure_inventory", inventory_then_turn
                )
                c.post(
                    f"/api/stories/{s2}/setup",
                    json={
                        "mode": "branching",
                        "interaction_style": "freeform_only",
                        "branching_cadence": "balanced",
                    },
                )
                t2 = threading.Thread(
                    target=lambda: late.append(
                        c.post(
                            f"/api/stories/{s2}/turns",
                            json={"user_input": "LATELOCALMARK"},
                        )
                    )
                )
                t2.start()
            else:
                assert created.status_code == 409  # admission refused during deletion
            gates[s1].set()
            t1.join(60)
            d.join(60)
            assert done, "deletion did not finish"
            assert rows_with(app.state.session_factory, "LATELOCALMARK") == []
            stories = c.get("/api/stories").json()["stories"]
            assert stories == [] or done[0].json()["state"] != "completed"


class TestExportPrecondition:
    """F2: an export admitted just before the deletion boundary stays
    fulfillable; the deletion does not suppress the account over it."""

    def test_export_admitted_before_the_fence_stays_fulfillable(
        self, remote: RemoteHarness, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        a = remote.enroll("a@example.test")
        remote.seed_hosted(remote.account_id(a))
        play_branching(a, "Mine", "Prose.")
        staff = remote.staff()
        dele = _request(a, "deletion", "account")
        _confirm(a, dele, password=PASSWORD)
        _approve(staff, dele["request_id"])

        from afterworlds.remote import access as access_module

        real = access_module.record_suppression_fenced
        created: list[dict[str, Any]] = []

        def racing(*args: Any, **kwargs: Any) -> Any:
            # A valid export is admitted just before the deletion takes the
            # account fence.
            if not created:
                created.append(_request(a, "export", "account"))
            return real(*args, **kwargs)

        monkeypatch.setattr(access_module, "record_suppression_fenced", racing)
        first = _execute(staff, dele["request_id"])
        assert first["state"] == "failed"
        assert _phase(first, "exports") == "failed"
        assert _phase(first, "fence") is None  # nothing was suppressed
        monkeypatch.undo()
        exp = created[0]
        _approve(staff, exp["request_id"])
        done = _execute(staff, exp["request_id"])
        assert done["state"] == "completed", done  # not trapped behind suppression
        assert (
            a.get(f"/api/data-requests/{exp['request_id']}/artifact").status_code == 200
        )
        final = _execute(staff, dele["request_id"])
        assert _phase(final, "identity") == "succeeded"


class TestDeliveryEvidence:
    """F3: only a fully transmitted artifact counts as delivered."""

    def _export(self, remote: RemoteHarness) -> tuple[Any, str]:
        a = remote.enroll("a@example.test")
        remote.seed_hosted(remote.account_id(a))
        play_branching(a, "Mine", "Prose.")
        staff = remote.staff()
        exp = _request(a, "export", "account")
        _approve(staff, exp["request_id"])
        assert _execute(staff, exp["request_id"])["state"] == "completed"
        return a, exp["request_id"]

    def _delivered(self, remote: RemoteHarness, rid: str) -> str | None:
        with remote.app.state.control_factory() as s:
            row = s.scalars(
                sa.select(ExportArtifactORM).where(ExportArtifactORM.request_id == rid)
            ).one()
            return row.delivered_at

    def test_a_range_request_is_not_delivery(self, remote: RemoteHarness) -> None:
        a, rid = self._export(remote)
        url = f"/api/data-requests/{rid}/artifact"
        partial = a.get(url, headers={"Range": "bytes=0-0"})
        assert partial.status_code == 200 and len(partial.content) > 1
        full = a.get(url)
        assert self._delivered(remote, rid) is not None
        assert partial.content == full.content

    def test_an_interrupted_transfer_is_not_delivery(
        self, remote: RemoteHarness, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import anyio

        a, rid = self._export(remote)
        from afterworlds.api.routes import data_requests as route

        monkeypatch.setattr(route, "DOWNLOAD_CHUNK", 64)
        account_cookie = a.cookies.get("aw_session")
        sent: list[dict[str, Any]] = []
        gone = anyio.Event()
        requested = {"done": False}

        async def receive() -> dict[str, Any]:
            # The request body once, then -- like a real server -- a
            # disconnect only after the client went away.
            if not requested["done"]:
                requested["done"] = True
                return {"type": "http.request", "body": b"", "more_body": False}
            await gone.wait()
            return {"type": "http.disconnect"}

        async def send(message: dict[str, Any]) -> None:
            sent.append(message)
            if message["type"] == "http.response.body" and len(sent) >= 3:
                gone.set()
                raise OSError("client disconnected")

        scope = {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "method": "GET",
            "scheme": "https",
            "path": f"/api/data-requests/{rid}/artifact",
            "raw_path": f"/api/data-requests/{rid}/artifact".encode(),
            "query_string": b"",
            "root_path": "",
            "headers": [
                (b"host", b"testserver"),
                (b"cookie", f"aw_session={account_cookie}".encode()),
            ],
            "client": ("127.0.0.1", 1),
            "server": ("testserver", 443),
        }

        async def run() -> None:
            with contextlib.suppress(OSError):
                await remote.app(scope, receive, send)

        anyio.run(run)
        assert any(m["type"] == "http.response.start" for m in sent)
        assert self._delivered(remote, rid) is None


class TestAdjustmentIdentity:
    """F7: one operation ID binds one logical action, even concurrently."""

    def test_concurrent_reuse_of_an_operation_id_never_misbinds(
        self, remote: RemoteHarness, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        a = remote.enroll("a@example.test")
        b = remote.enroll("b@example.test")
        a_id, b_id = remote.account_id(a), remote.account_id(b)
        remote.seed_hosted(a_id)
        remote.seed_hosted(b_id)
        staff = remote.staff()
        op = str(uuid.uuid4())
        barrier = threading.Barrier(2, timeout=20)
        real = SupportService._events

        def synced(self: SupportService, operation_id: Any) -> Any:
            found = real(self, operation_id)
            if not found:
                with contextlib.suppress(threading.BrokenBarrierError):
                    barrier.wait()
            return found

        monkeypatch.setattr(SupportService, "_events", synced)

        def adjust(account: str, delta: str) -> Any:
            expected = staff.get(f"/api/admin/accounts/{account}").json()[
                "last_entitlement_event_id"
            ]
            return staff.post(
                f"/api/admin/accounts/{account}/credit-adjustments",
                json={
                    "operation_id": op,
                    "hosted_credit_delta": delta,
                    "reason": "goodwill",
                    "expected_last_entitlement_event_id": expected,
                },
            )

        out: dict[str, Any] = {}
        threads = [
            threading.Thread(target=lambda: out.__setitem__("a", adjust(a_id, "5"))),
            threading.Thread(target=lambda: out.__setitem__("b", adjust(b_id, "50"))),
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join(60)
        monkeypatch.undo()
        codes = sorted(r.status_code for r in out.values())
        assert codes == [200, 409], {k: v.text for k, v in out.items()}
        loser = next(k for k, v in out.items() if v.status_code == 409)
        assert _error(out[loser]) == "operation_conflict"
        with remote.app.state.control_factory() as s:
            targets = set(
                s.scalars(
                    sa.select(SupportActionEventORM.target_ref).where(
                        SupportActionEventORM.operation_id == op
                    )
                )
            )
        assert len(targets) == 1  # the loser left no row under this operation
        status = staff.get(f"/api/admin/support-operations/{op}").json()
        assert status["outcome_code"] == "committed"


class TestSettlementSource:
    """F9: a delivered turn's settlement failure is recorded inside the
    admitted work, so losing the HTTP response cannot drop it."""

    def test_settlement_anomaly_survives_a_lost_request(
        self, remote: RemoteHarness, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from afterworlds.api.routes import turns as turns_route
        from afterworlds.entitlement.errors import EntitlementSettlementError
        from afterworlds.entitlement.service import EntitlementService

        a = remote.enroll("a@example.test")
        remote.seed_hosted(remote.account_id(a))
        staff = remote.staff()
        sid = play_branching(a, "Tale", "Warm up.")

        def fail(*_: Any, **__: Any) -> Any:
            raise EntitlementSettlementError("metrics missing")

        monkeypatch.setattr(EntitlementService, "settle_hosted_turn_cost", fail)
        real = turns_route.run_under_story_lock

        async def lost(*args: Any, **kwargs: Any) -> Any:
            await real(*args, **kwargs)  # the worker delivered the turn
            raise RuntimeError("client went away before the response")

        monkeypatch.setattr(turns_route, "run_under_story_lock", lost)
        with pytest.raises(RuntimeError):
            a.post(f"/api/stories/{sid}/turns", json={"user_input": "Go on."})
        monkeypatch.undo()
        report = staff.get("/api/admin/anomalies").json()
        assert [x for x in report["anomalies"] if x["source_kind"] == "turn_settlement"]


class TestNoticeOwnership:
    """F6: a notice is published complete; an interrupted write to the
    erased address is still found and removed; unrelated notices stay; a
    notice that cannot be attributed makes the purge fail visibly."""

    def test_interrupted_write_is_purged_and_unrelated_kept(
        self, tmp_path: Any, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from afterworlds.remote import notices

        outbox = notices.OutboxDirectoryTransport(tmp_path)
        outbox.send(contact_address="other@example.test", kind="recovery", code="1")
        real = notices.os.replace

        def torn(*args: Any) -> None:
            raise OSError("power loss")

        monkeypatch.setattr(notices.os, "replace", torn)
        for address in ("gone@example.test", "other@example.test"):
            with pytest.raises(OSError):
                outbox.send(contact_address=address, kind="recovery", code="2")
        monkeypatch.setattr(notices.os, "replace", real)
        assert not any("gone" in p.read_text() for p in tmp_path.glob("*.json"))

        assert outbox.purge("gone@example.test") == 1
        remaining = sorted(p.read_text(encoding="utf-8") for p in tmp_path.iterdir())
        assert len(remaining) == 2
        assert all("other@example.test" in body for body in remaining)
        assert not any(b"gone@" in p.read_bytes() for p in tmp_path.iterdir())

    def test_unattributable_final_notice_fails_the_purge(self, tmp_path: Any) -> None:
        from afterworlds.remote import notices

        outbox = notices.OutboxDirectoryTransport(tmp_path)
        outbox.send(contact_address="gone@example.test", kind="recovery", code="1")
        (tmp_path / "recovery-legacy.json").write_text('{"to": "gone@', "utf-8")
        with pytest.raises(OSError, match="unattributable"):
            outbox.purge("gone@example.test")
        assert (tmp_path / "recovery-legacy.json").exists()
