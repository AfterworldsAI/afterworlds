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

    @pytest.mark.parametrize("store", ["none", "failing"])
    def test_an_unrecordable_failure_degrades_the_source(
        self, remote: RemoteHarness, monkeypatch: pytest.MonkeyPatch, store: str
    ) -> None:
        from sqlalchemy.exc import OperationalError

        from afterworlds.operations import anomalies

        monkeypatch.setattr(anomalies, "_UNRECORDED", threading.Event())
        staff = remote.staff()
        report = staff.get("/api/admin/anomalies").json()
        assert report["sources"]["settlement_failures"] == "available"

        class Failing:
            def begin(self) -> Any:
                raise OperationalError("INSERT", {}, Exception("disk full"))

        anomalies.record_settlement_failure(
            None if store == "none" else anomalies.SettlementSink(Failing()),  # type: ignore[arg-type]
            subject_ref="s",
            turn_id="t",
            error_class="EntitlementSettlementError",
            now=datetime.now(UTC),
        )
        report = staff.get("/api/admin/anomalies").json()
        assert report["sources"]["settlement_failures"] == "degraded"


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


class TestBoundedText:
    """Bounded verification concern: an explanation admits ordinary reasons
    and refuses the listed shapes (pattern-limited, not PII detection)."""

    @pytest.mark.parametrize(
        "text",
        [
            "Goodwill after an outage",
            "Refund for 3 failed turns on 2026-10-19",
            "crd22_settlement_failure investigated",
            "Duplicate of request 550e8400-e29b-41d4-a716-446655440000",
        ],
    )
    def test_admits_ordinary_reasons(self, text: str) -> None:
        from afterworlds.operations.support import bounded_text

        assert bounded_text(f"  {text} ") == text

    @pytest.mark.parametrize(
        "text",
        [
            "write to owner@example.test",
            "see https://example.test/x",
            "see www.example.test",
            "card 4111 1111 1111 1111",
            "call +1 555 123 4567",
            "token abcdEFGH1234ijklMNOP5678qrst",
            "sk-ant-abcdefgh12345",
            "two\nlines",
            "hidden\u202eoverride",
            "",
            "x" * 281,
        ],
    )
    def test_refuses_listed_shapes(self, text: str) -> None:
        from afterworlds.operations.errors import OperationError
        from afterworlds.operations.support import bounded_text

        with pytest.raises(OperationError) as refused:
            bounded_text(text)
        assert text.strip() == "" or text not in str(refused.value)  # never echoed


class TestRpgExport:
    """Bounded verification concern: an RPG Story's export carries its
    transcript, player-visible state and setup view and no hidden mechanics
    (world-setup phase; see the in-play limit below)."""

    def test_rpg_story_export_scope_and_visibility(self, remote: RemoteHarness) -> None:
        from tests.operations._data import plant, unzip

        a = remote.enroll("a@example.test")
        remote.seed_hosted(remote.account_id(a))
        story_id = a.post(
            "/api/stories",
            json={"title": "Isles", "mode": "rpg", "character_name": "Ilse"},
        ).json()["story_id"]
        turn = a.post(
            f"/api/stories/{story_id}/turns",
            json={"user_input": "A storm-wracked archipelago."},
        )
        assert turn.status_code == 200, turn.text
        setup = a.get(f"/api/stories/{story_id}/rpg/setup").json()
        plant(
            remote.app.state.session_factory,
            story_id,
            "RPGHIDDENMARK",
            orphan_marker="RPGORPHANOK",
        )

        req = _request(a, "export", "story", story_id)
        staff = remote.staff()
        _approve(staff, req["request_id"])
        assert _execute(staff, req["request_id"])["state"] == "completed"
        files = unzip(a.get(f"/api/data-requests/{req['request_id']}/artifact").content)
        story = files[f"stories/{story_id}/story.json"]
        assert story["story"]["mode"] == "rpg"
        assert any("storm-wracked" in t["user_input"] for t in story["transcript"])
        # The same projections the player sees (in world setup there is no
        # sheet yet; an in-play sheet needs the published-release fixture --
        # a recorded verification limit).
        visible = a.get(f"/api/stories/{story_id}/visible-state").json()
        assert story["visible_state"] == visible["visible_state"]
        assert setup["phase"] == "world_setup"
        shown = a.get(f"/api/stories/{story_id}/setup").json()
        assert story["setup_state"] == shown["setup_state"] is not None
        everything = str(files)
        assert "RPGHIDDENMARK" not in everything
        assert "RPGORPHANOK" in everything  # the player's own orphan prose
        codes = {e["code"] for e in files["manifest.json"]["exclusions"]}
        assert "hidden_rpg_mechanics" in codes


class TestNoticeErasure:
    """F6 through the real executor: an outbox notice that cannot be
    attributed fails the identity phase visibly, erases nothing, and a retry
    after the operator resolves it completes the erasure."""

    def test_unattributable_notice_fails_visibly_then_retries(
        self, remote: RemoteHarness
    ) -> None:
        a = remote.enroll("gone@example.test")
        remote.seed_hosted(remote.account_id(a))
        staff = remote.staff()
        req = _request(a, "deletion", "account")
        _confirm(a, req, password=PASSWORD)
        _approve(staff, req["request_id"])
        torn = remote.outbox / "recovery-torn.json"
        torn.write_text('{"to": "gone@', encoding="utf-8")

        failed = _execute(staff, req["request_id"])
        assert failed["state"] == "failed"
        assert _phase(failed, "identity") == "failed"
        # Nothing was erased: the owner can still sign in.
        again = remote.client()
        signed_in = again.post(
            "/api/auth/sign-in",
            json={"contact_address": "gone@example.test", "password": PASSWORD},
        )
        assert signed_in.status_code == 200, signed_in.text

        torn.unlink()  # the operator resolved the copy
        done = _execute(staff, req["request_id"])
        assert _phase(done, "identity") == "succeeded"
        assert not any(
            b"gone@" in p.read_bytes() for p in remote.outbox.iterdir() if p.is_file()
        )


class TestIdenticalRetryOutcome:
    """Review of 03506df9, P1-1: an identical retry while the original is
    paused at the pre-effect point, beside an unrelated authorized event,
    never records an outcome that disagrees with the one effect."""

    def test_retry_beside_an_effect_in_flight_agrees_with_it(
        self, remote: RemoteHarness, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from afterworlds.entitlement.enums import EntitlementEventType
        from afterworlds.entitlement.orm import EntitlementEvent
        from afterworlds.entitlement.payloads import SubscriptionCreditGrantPayload
        from afterworlds.entitlement.service import EntitlementService

        a = remote.enroll("a@example.test")
        a_id = remote.account_id(a)
        remote.seed_hosted(a_id)
        staff = remote.staff()
        op = str(uuid.uuid4())
        expected = staff.get(f"/api/admin/accounts/{a_id}").json()[
            "last_entitlement_event_id"
        ]
        body = {
            "operation_id": op,
            "hosted_credit_delta": "5",
            "reason": "goodwill",
            "expected_last_entitlement_event_id": expected,
        }
        paused, go = threading.Event(), threading.Event()
        real = EntitlementService.receive_entitlement_event

        def at_pre_effect(
            self: Any, subject: Any, kind: Any, *a_: Any, **kw: Any
        ) -> Any:
            if (
                kind is EntitlementEventType.MANUAL_CREDIT_ADJUSTMENT
                and not paused.is_set()
            ):
                paused.set()
                go.wait(10)
            return real(self, subject, kind, *a_, **kw)

        monkeypatch.setattr(
            EntitlementService, "receive_entitlement_event", at_pre_effect
        )

        def unrelated() -> None:  # another authorized owner event (CRD Issue 13)
            with remote.app.state.session_factory() as s:
                real(
                    EntitlementService(s),
                    uuid.UUID(a_id),
                    EntitlementEventType.SUBSCRIPTION_CREDIT_GRANT,
                    SubscriptionCreditGrantPayload(hosted_credit_delta=Decimal("1")),
                )

        url = f"/api/admin/accounts/{a_id}/credit-adjustments"
        out: dict[str, Any] = {}
        original = threading.Thread(
            target=lambda: out.__setitem__("a", staff.post(url, json=body))
        )
        original.start()
        assert paused.wait(10)
        other = threading.Thread(target=unrelated)
        other.start()
        time.sleep(0.3)
        retry = threading.Thread(
            target=lambda: out.__setitem__("r", staff.post(url, json=body))
        )
        retry.start()
        time.sleep(0.3)
        go.set()
        for t in (original, other, retry):
            t.join(30)
        monkeypatch.undo()

        assert out["a"].status_code == 200, out["a"].text
        assert out["r"].status_code == 200, out["r"].text
        first, again = out["a"].json(), out["r"].json()
        assert first["outcome_code"] == again["outcome_code"] == "committed"
        with remote.app.state.session_factory() as s:
            effects = list(
                s.scalars(
                    sa.select(EntitlementEvent.event_id).where(
                        EntitlementEvent.idempotency_key
                        == f"crd22-support-adjustment:{op}"
                    )
                )
            )
        assert [str(e) for e in effects] == [first["source_entitlement_event_id"]]
        assert (
            again["source_entitlement_event_id"] == first["source_entitlement_event_id"]
        )
        # After a restart the recorded outcome is the same.
        fresh = SupportService(
            remote.app.state.control_factory,
            remote.app.state.session_factory,
            remote.app.state.identity,
        )
        status = fresh.status(uuid.UUID(op))
        assert status.outcome_code == "committed"
        assert (
            status.source_entitlement_event_id == first["source_entitlement_event_id"]
        )


class TestSettlementCoverageAcrossRestart:
    """Review of 03506df9, P1-2: a delivered turn whose settlement failed and
    whose anomaly could not be recorded leaves durable, content-free
    evidence; after a restart the source is still degraded -- not
    "available" just because the table is readable -- until staff close it."""

    def test_unrecorded_failure_stays_degraded_after_restart(
        self, tmp_path: Any, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from sqlalchemy.exc import OperationalError

        from afterworlds.api.routes import turns as turns_route
        from afterworlds.entitlement.errors import EntitlementSettlementError
        from afterworlds.entitlement.service import EntitlementService
        from afterworlds.operations import anomalies
        from tests.api._remote import make_remote

        monkeypatch.setenv(
            "AFTERWORLDS_RETRIEVAL_PERSIST_DIRECTORY", str(tmp_path / "chroma")
        )
        monkeypatch.setenv("AFTERWORLDS_FAKE_PROVIDER", "1")
        monkeypatch.setattr(anomalies, "_UNRECORDED", threading.Event())
        first = make_remote(tmp_path)
        try:
            a = first.enroll("a@example.test")
            first.seed_hosted(first.account_id(a))
            sid = play_branching(a, "Tale", "Warm up.")

            def fail(*_: Any, **__: Any) -> Any:
                raise EntitlementSettlementError("metrics missing")

            class Refusing:
                def begin(self) -> Any:
                    raise OperationalError("INSERT", {}, Exception("disk full"))

            monkeypatch.setattr(EntitlementService, "settle_hosted_turn_cost", fail)
            monkeypatch.setattr(
                turns_route,
                "_settlement_sink",
                lambda request: anomalies.SettlementSink(
                    Refusing(),  # type: ignore[arg-type]
                    request.app.state.session_factory,
                ),
            )
            turn = a.post(f"/api/stories/{sid}/turns", json={"user_input": "Go on."})
            assert turn.status_code == 200, turn.text  # delivered, not blocked
            assert turn.json()["settlement_warning"]
        finally:
            first.close()
        monkeypatch.undo()

        # Restart: a fresh process (no in-memory flag), stores readable.
        monkeypatch.setenv(
            "AFTERWORLDS_RETRIEVAL_PERSIST_DIRECTORY", str(tmp_path / "chroma")
        )
        monkeypatch.setenv("AFTERWORLDS_FAKE_PROVIDER", "1")
        monkeypatch.setattr(anomalies, "_UNRECORDED", threading.Event())
        second = make_remote(tmp_path)
        try:
            staff = second.staff()
            report = staff.get("/api/admin/anomalies").json()
            assert report["sources"]["settlement_failures"] == "degraded"
            (gap,) = [
                x
                for x in report["anomalies"]
                if x["source_kind"] == "settlement_coverage"
            ]
            assert gap["subject_ref"] is None  # content-free: no subject, no Turn
            assert "a@example.test" not in str(gap)
            # Investigating keeps it degraded; only a staff close restores it.
            for state, degraded in (("investigating", True), ("closed", False)):
                noted = staff.post(
                    f"/api/admin/anomalies/{gap['anomaly_id']}/notes",
                    json={"state": state, "note_code": "resolved"},
                )
                assert noted.status_code == 200, noted.text
                report = staff.get("/api/admin/anomalies").json()
                assert (
                    report["sources"]["settlement_failures"] == "degraded"
                ) is degraded
            assert report["sources"]["settlement_failures"] == "available"
        finally:
            second.close()
