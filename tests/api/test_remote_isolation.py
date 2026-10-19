"""Prerequisite #205 §2/§3: two-account isolation, administrator separation
and local-BYOK separation through the built remote app.

Two ordinary accounts (A, B) and the Owner, each in its own client/cookie
jar. A drives a real fake-provider Branching story (setup, begin, turn,
transcript, Retrieval Memory ingestion); B probes every Story route with A's
IDs and forged identity fields and must see the same 404 as a random ID and
cause no effect.
"""

from __future__ import annotations

import io
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest
import sqlalchemy as sa
from fastapi.testclient import TestClient

from afterworlds.entitlement.enums import EntitlementEventType, HostedAccessPlan
from afterworlds.entitlement.payloads import (
    ByokLicenseActivatedPayload,
    HostedAccessActivatedPayload,
    SubscriptionCreditGrantPayload,
)
from afterworlds.entitlement.service import EntitlementService
from afterworlds.persistence.orm.node import TurnORM
from afterworlds.persistence.orm.story import StoryORM
from afterworlds.remote import bootstrap
from afterworlds.remote.control_orm import IdentityAuditEventORM
from tests.api._remote import PASSWORD, RemoteHarness

SYNTHETIC_KEY = "sk-ant-SYNTHETIC-REMOTE-MARKER-7f3a9c"  # pragma: allowlist secret


def _error(resp) -> str:  # type: ignore[no-untyped-def]
    return str(resp.json()["error_code"])


def _seed_hosted(remote: RemoteHarness, account_id: str) -> None:
    with remote.app.state.session_factory() as session:
        service = EntitlementService(session)
        subject = uuid.UUID(account_id)
        service.receive_entitlement_event(
            subject,
            EntitlementEventType.HOSTED_ACCESS_ACTIVATED,
            HostedAccessActivatedPayload(
                plan=HostedAccessPlan.SUBSCRIPTION, effective_at=datetime.now(UTC)
            ),
        )
        service.receive_entitlement_event(
            subject,
            EntitlementEventType.SUBSCRIPTION_CREDIT_GRANT,
            SubscriptionCreditGrantPayload(hosted_credit_delta=Decimal("1000")),
        )
        session.commit()


def _branching_in_play(c: TestClient) -> str:
    story_id = c.post("/api/stories", json={"title": "A's", "mode": "branching"})
    assert story_id.status_code == 201, story_id.text
    sid = str(story_id.json()["story_id"])
    resp = c.post(
        f"/api/stories/{sid}/setup",
        json={
            "mode": "branching",
            "interaction_style": "freeform_only",
            "branching_cadence": "balanced",
        },
    )
    assert resp.status_code == 200, resp.text
    resp = c.post(f"/api/stories/{sid}/begin")
    assert resp.status_code == 200 and resp.json()["outcome"] == "started", resp.text
    return sid


def _counts(remote: RemoteHarness) -> tuple[int, int]:
    with remote.app.state.session_factory() as s:
        stories = s.scalar(sa.select(sa.func.count()).select_from(StoryORM))
        turns = s.scalar(sa.select(sa.func.count()).select_from(TurnORM))
    return int(stories or 0), int(turns or 0)


def _story_probes(sid: str) -> list[tuple[str, str, dict[str, object] | None]]:
    seq = str(uuid.uuid4())
    return [
        ("GET", f"/api/stories/{sid}", None),
        ("GET", f"/api/stories/{sid}/turns", None),
        ("POST", f"/api/stories/{sid}/turns", {"user_input": "I steal the plot."}),
        ("POST", f"/api/stories/{sid}/begin", None),
        ("GET", f"/api/stories/{sid}/visible-state", None),
        ("GET", f"/api/stories/{sid}/setup", None),
        (
            "POST",
            f"/api/stories/{sid}/setup",
            {
                "mode": "branching",
                "interaction_style": "hybrid",
                "branching_cadence": "immersive",
            },
        ),
        ("GET", f"/api/stories/{sid}/rpg/setup", None),
        (
            "POST",
            f"/api/stories/{sid}/rpg/setup/confirm-world",
            {"expected_world_revision": 0},
        ),
        ("GET", f"/api/stories/{sid}/rpg/pending-interaction", None),
        (
            "POST",
            f"/api/stories/{sid}/rpg/rolls",
            {"pending_roll_request_id": seq, "kind": "raw", "values": [3]},
        ),
        ("POST", f"/api/stories/{sid}/rpg/sequences/{seq}/resume", None),
    ]


class TestTwoAccountIsolation:
    def test_foreign_story_is_indistinguishable_and_untouched(
        self, remote: RemoteHarness
    ) -> None:
        a = remote.enroll("a@example.test")
        b = remote.enroll("b@example.test")
        _seed_hosted(remote, remote.account_id(a))
        sid = _branching_in_play(a)
        delivered = a.post(
            f"/api/stories/{sid}/turns", json={"user_input": "I look around."}
        )
        assert delivered.status_code == 200, delivered.text
        transcript = a.get(f"/api/stories/{sid}/turns").json()["turns"]
        assert transcript

        before = _counts(remote)
        assert b.get("/api/stories").json()["stories"] == []
        for method, path, body in _story_probes(sid):
            other = str(uuid.uuid4())
            foreign = b.request(method, path, json=body)
            random = b.request(method, path.replace(sid, other), json=body)
            assert foreign.status_code == random.status_code == 404, (method, path)
            # Same envelope; the message names only the ID the caller sent.
            assert foreign.json() == {
                **random.json(),
                "message": random.json()["message"].replace(other, sid),
            }
            assert "A's" not in foreign.text
        assert _counts(remote) == before
        # A's view is intact and B's attempts left no trace.
        assert a.get(f"/api/stories/{sid}/turns").json()["turns"] == transcript
        assert [s["story_id"] for s in a.get("/api/stories").json()["stories"]] == [sid]

    def test_enumeration_is_per_account(self, remote: RemoteHarness) -> None:
        a = remote.enroll("a@example.test")
        b = remote.enroll("b@example.test")
        a_ids = {
            a.post("/api/stories", json={"title": f"A{i}", "mode": "branching"}).json()[
                "story_id"
            ]
            for i in range(3)
        }
        b_ids = {
            b.post("/api/stories", json={"title": "B0", "mode": "rpg"}).json()[
                "story_id"
            ]
        }
        assert {s["story_id"] for s in a.get("/api/stories").json()["stories"]} == a_ids
        assert {s["story_id"] for s in b.get("/api/stories").json()["stories"]} == b_ids

    def test_forged_identity_fields_cannot_select_the_actor(
        self, remote: RemoteHarness
    ) -> None:
        a = remote.enroll("a@example.test")
        b = remote.enroll("b@example.test")
        a_id = remote.account_id(a)
        sid = a.post("/api/stories", json={"title": "A", "mode": "branching"}).json()[
            "story_id"
        ]
        forged = {
            "X-Sojourner-Id": a_id,
            "X-Account-Id": a_id,
            "X-Afterworlds-Role": "owner_administrator",
        }
        resp = b.get(f"/api/stories/{sid}", headers=forged, params={"account_id": a_id})
        assert resp.status_code == 404
        resp = b.post(
            "/api/stories",
            json={"title": "x", "mode": "branching", "sojourner_id": a_id},
        )
        assert resp.status_code == 422  # extra fields are refused, never trusted
        assert b.get("/api/stories", headers=forged).json()["stories"] == []
        resp = b.get(f"/api/admin/accounts/{a_id}", headers=forged)
        assert _error(resp) == "staff_authority_required"

    def test_entitlement_views_are_per_account(self, remote: RemoteHarness) -> None:
        a = remote.enroll("a@example.test")
        b = remote.enroll("b@example.test")
        _seed_hosted(remote, remote.account_id(a))
        assert a.get("/api/account").json()["credits"]["total"] == "1000.0000"
        assert b.get("/api/account").json()["credits"]["total"] is None

    def test_unowned_rows_stay_inaccessible(self, remote: RemoteHarness) -> None:
        a = remote.enroll("a@example.test")
        orphan = str(uuid.uuid4())
        now = datetime.now(UTC).isoformat()
        with remote.app.state.session_factory.begin() as s:
            s.add(
                StoryORM(
                    story_id=orphan,
                    title="Unowned",
                    mode="branching",
                    created_at=now,
                    updated_at=now,
                )
            )
        assert a.get("/api/stories").json()["stories"] == []
        assert a.get(f"/api/stories/{orphan}").status_code == 404


class TestAdministrator:
    def _bootstrap(self, remote: RemoteHarness, address: str, password: str) -> int:
        url = remote.settings.control_database_url
        assert url is not None
        stdin = io.StringIO(password + "\n")
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr("sys.stdin", stdin)
            return bootstrap.main(
                ["--contact-address", address, "--control-db", url, "--password-stdin"]
            )

    def _staff(self, remote: RemoteHarness, address: str) -> TestClient:
        staff = remote.client()
        resp = staff.post(
            "/api/admin/session",
            json={"contact_address": address, "password": PASSWORD},
        )
        assert resp.status_code == 200, resp.text
        return staff

    def test_owner_needs_controlled_bootstrap_and_a_staff_session(
        self, remote: RemoteHarness
    ) -> None:
        owner = remote.enroll("owner@example.test")
        b = remote.enroll("b@example.test")
        b_id = remote.account_id(b)
        b.post("/api/stories", json={"title": "B", "mode": "branching"})

        # Before bootstrap nobody, the Owner included, has staff authority.
        resp = remote.client().post(
            "/api/admin/session",
            json={"contact_address": "owner@example.test", "password": PASSWORD},
        )
        assert _error(resp) == "staff_authority_required"
        assert self._bootstrap(remote, "owner@example.test", "wrong password!") == 1
        assert self._bootstrap(remote, "owner@example.test", PASSWORD) == 0
        assert self._bootstrap(remote, "owner@example.test", PASSWORD) == 0  # no-op
        # A second principal can never be provisioned.
        assert self._bootstrap(remote, "b@example.test", PASSWORD) == 1

        # The Owner's ordinary session still carries no staff authority.
        resp = owner.get(f"/api/admin/accounts/{b_id}")
        assert resp.status_code == 403 and _error(resp) == "staff_authority_required"

        staff = self._staff(remote, "owner@example.test")
        view = staff.get(f"/api/admin/accounts/{b_id}")
        assert view.status_code == 200, view.text
        body = view.json()
        assert body["owned_story_count"] == 1 and body["status"] == "active"
        assert body["byok_readiness_source"] == "unavailable_remotely"
        assert "b@example.test" not in view.text
        # A staff session is not an ordinary session.
        assert staff.get("/api/stories").status_code == 401
        # Ordinary B cannot target anyone.
        assert (
            _error(b.get(f"/api/admin/accounts/{b_id}")) == "staff_authority_required"
        )
        assert staff.get(f"/api/admin/accounts/{uuid.uuid4()}").status_code == 404

    def _bootstrap_receipts(self, remote: RemoteHarness) -> list[tuple[str, ...]]:
        with remote.app.state.control_factory() as s:  # a fresh session
            return [
                (
                    r.actor_ref,
                    r.outcome_code,
                    str(r.reason_code),
                    str(r.target_ref),
                    str(r.reason_text),
                )
                for r in s.scalars(
                    sa.select(IdentityAuditEventORM)
                    .where(IdentityAuditEventORM.action_code == "owner_admin_bootstrap")
                    .order_by(IdentityAuditEventORM.event_order)
                )
            ]

    def test_bootstrap_refusals_leave_minimized_receipts(
        self, remote: RemoteHarness, capsys: pytest.CaptureFixture[str]
    ) -> None:
        import hashlib
        import sqlite3
        from contextlib import closing

        from afterworlds.remote.control_orm import AdminBindingORM, AuthSessionORM
        from afterworlds.remote.identity import UNAUTHENTICATED_ACTOR, SessionContext

        remote.enroll("owner@example.test")
        closed = remote.enroll("closed@example.test")
        assert closed.post("/api/account/close", json={"password": PASSWORD}).is_success
        remote.client().post(
            "/api/auth/register", json={"contact_address": "unverified@example.test"}
        )
        capsys.readouterr()
        refusals = [
            ("not-an-address-zq7marker", PASSWORD),
            ("ghost-zq7marker@example.test", PASSWORD),
            ("owner@example.test", "wrong-zq7marker-passphrase"),
            ("unverified@example.test", PASSWORD),
            ("closed@example.test", PASSWORD),
        ]
        for address, password in refusals:
            assert self._bootstrap(remote, address, password) == 1
        out = capsys.readouterr()
        assert "zq7marker" not in out.out + out.err
        assert "@" not in out.out + out.err

        # Durable after the raise, unauthenticated, codes only.
        assert (
            self._bootstrap_receipts(remote)
            == [(UNAUTHENTICATED_ACTOR, "refused", "invalid_input", "None", "None")]
            + [
                (
                    UNAUTHENTICATED_ACTOR,
                    "refused",
                    "authentication_failed",
                    "None",
                    "None",
                )
            ]
            * 4
        )
        url = remote.settings.control_database_url
        assert url is not None
        with closing(sqlite3.connect(url.removeprefix("sqlite:///"))) as db:
            dump = "\n".join(db.iterdump()).lower()
        assert "zq7marker" not in dump
        ghost = hashlib.sha256(b"ghost-zq7marker@example.test").hexdigest()
        assert ghost not in dump
        # No authority was granted by any refusal.
        with remote.app.state.control_factory() as s:
            assert (
                s.scalar(sa.select(sa.func.count()).select_from(AdminBindingORM)) == 0
            )
            assert (
                s.scalar(
                    sa.select(sa.func.count())
                    .select_from(AuthSessionORM)
                    .where(AuthSessionORM.context == SessionContext.STAFF.value)
                )
                == 0
            )

        # Success, repetition and another principal keep their receipts.
        assert self._bootstrap(remote, "owner@example.test", PASSWORD) == 0
        assert self._bootstrap(remote, "owner@example.test", PASSWORD) == 0
        remote.enroll("b@example.test")
        assert self._bootstrap(remote, "b@example.test", PASSWORD) == 1
        tail = self._bootstrap_receipts(remote)[5:]
        assert [(r[1], r[3] != "None") for r in tail] == [
            ("provisioned", True),
            ("already_provisioned", True),
            ("refused", True),
        ]
        assert all(r[0] != UNAUTHENTICATED_ACTOR for r in tail)

    def test_bootstrap_grants_nothing_without_its_receipt(
        self,
        remote: RemoteHarness,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from sqlalchemy.exc import OperationalError

        from afterworlds.remote.control_orm import AdminBindingORM
        from afterworlds.remote.identity import IdentityService

        remote.enroll("owner@example.test")

        def broken(*_a: object, **_k: object) -> None:
            raise OperationalError(
                "INSERT owner@example.test", {}, Exception("disk full")
            )

        capsys.readouterr()
        with monkeypatch.context() as m:
            m.setattr(IdentityService, "_audit", staticmethod(broken))
            # Neither a success nor a refusal is reported without its receipt.
            assert self._bootstrap(remote, "owner@example.test", PASSWORD) == 2
            assert self._bootstrap(remote, "owner@example.test", "wrong pass!") == 2
            assert self._bootstrap(remote, "not-an-address", PASSWORD) == 2
        out = capsys.readouterr()
        assert "@" not in out.out + out.err and "disk full" not in out.err
        assert "owner administrator" not in out.out
        assert self._bootstrap_receipts(remote) == []
        with remote.app.state.control_factory() as s:
            assert (
                s.scalar(sa.select(sa.func.count()).select_from(AdminBindingORM)) == 0
            )

    @pytest.mark.parametrize("failure", ["unopenable", "migration"])
    def test_bootstrap_store_failures_are_sanitized(
        self,
        remote: RemoteHarness,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
        failure: str,
    ) -> None:
        """Review r4313982112: opening or migrating the control store fails
        closed with the fixed message, no driver text, no grant."""
        import hashlib

        remote.enroll("owner@example.test")
        content = remote.tmp_path / "content.db"
        url = (
            f"sqlite:///{remote.tmp_path / 'zq9marker-missing' / 'control.db'}"
            if failure == "unopenable"
            else f"sqlite:///{content}"  # not a control store: migration fails
        )
        before = hashlib.sha256(content.read_bytes()).hexdigest()
        monkeypatch.setattr("sys.stdin", io.StringIO("zq9marker-passphrase\n"))
        capsys.readouterr()
        code = bootstrap.main(
            [
                "--contact-address",
                "zq9marker@example.test",
                "--control-db",
                url,
                "--password-stdin",
            ]
        )
        out = capsys.readouterr()
        assert code == 2
        assert "nothing was provisioned" in out.err
        assert "zq9marker" not in out.out + out.err
        assert "Traceback" not in out.err and "owner administrator" not in out.out
        assert hashlib.sha256(content.read_bytes()).hexdigest() == before
        assert self._bootstrap_receipts(remote) == []

    def test_targeted_revocation_is_reasoned_and_audited(
        self, remote: RemoteHarness
    ) -> None:
        remote.enroll("owner@example.test")
        b = remote.enroll("b@example.test")
        b_id = remote.account_id(b)
        assert self._bootstrap(remote, "owner@example.test", PASSWORD) == 0
        staff = self._staff(remote, "owner@example.test")
        blank = staff.post(
            f"/api/admin/accounts/{b_id}/sessions/revoke", json={"reason": " "}
        )
        assert blank.status_code == 422
        assert b.get("/api/stories").status_code == 200  # nothing happened
        resp = staff.post(
            f"/api/admin/accounts/{b_id}/sessions/revoke",
            json={"reason": "suspected credential sharing"},
        )
        assert resp.status_code == 200 and resp.json()["revoked_sessions"] == 1
        assert b.get("/api/stories").status_code == 401
        with remote.app.state.control_factory() as s:
            event = s.scalars(
                sa.select(IdentityAuditEventORM).where(
                    IdentityAuditEventORM.action_code == "account_sessions_revoked"
                )
            ).one()
        assert event.target_ref == b_id
        assert event.reason_text == "suspected credential sharing"
        assert event.actor_ref != b_id  # the staff principal, from the session

    def test_owner_recovery_revokes_staff_sessions_keeps_binding(
        self, remote: RemoteHarness
    ) -> None:
        from tests.api._remote import latest_code

        remote.enroll("owner@example.test")
        assert self._bootstrap(remote, "owner@example.test", PASSWORD) == 0
        staff = self._staff(remote, "owner@example.test")
        anon = remote.client()
        anon.post("/api/auth/recovery", json={"contact_address": "owner@example.test"})
        code = latest_code(remote.outbox, "owner@example.test", "recovery")
        new = "owner's replacement passphrase"  # pragma: allowlist secret
        anon.post(
            "/api/auth/recovery/complete",
            json={
                "contact_address": "owner@example.test",
                "code": code,
                "new_password": new,
            },
        )
        assert staff.get(f"/api/admin/accounts/{uuid.uuid4()}").status_code == 401
        resp = remote.client().post(
            "/api/admin/session",
            json={"contact_address": "owner@example.test", "password": new},
        )
        assert resp.status_code == 200  # binding preserved, re-proven by sign-in


class TestLocalByokSeparation:
    def test_remote_never_accepts_or_infers_byok_keys(
        self, remote: RemoteHarness, caplog: pytest.LogCaptureFixture
    ) -> None:
        a = remote.enroll("a@example.test")
        with remote.app.state.session_factory() as session:
            EntitlementService(session).receive_entitlement_event(
                uuid.UUID(remote.account_id(a)),
                EntitlementEventType.BYOK_LICENSE_ACTIVATED,
                ByokLicenseActivatedPayload(purchased_at=datetime.now(UTC)),
            )
            session.commit()
        view = a.get("/api/account").json()
        assert view["byok"]["license_active"] is True
        assert view["byok"]["readiness_source"] == "unavailable_remotely"
        assert view["byok"]["byok_ready"] is None and view["byok"]["providers"] == []
        # A licence alone never makes BYOK runnable on the server.
        assert view["selected_access_path"] is None

        for method, path, body in (
            (
                "PUT",
                "/api/account/byok/anthropic/credential",
                {"api_key": SYNTHETIC_KEY},
            ),
            (
                "POST",
                "/api/account/byok/anthropic/validate",
                {"acknowledge_provider_contact": True},
            ),
            ("PUT", "/api/account/byok/anthropic/enabled", {"enabled": True}),
            ("DELETE", "/api/account/byok/anthropic/credential", None),
        ):
            resp = a.request(method, path, json=body)
            assert resp.status_code == 409 and _error(resp) == "byok_local_only"
            assert SYNTHETIC_KEY not in resp.text
        # Not in any durable remote store, outbox or log.
        assert SYNTHETIC_KEY not in caplog.text
        for path in remote.tmp_path.rglob("*"):
            # Lock files hold no data and are byte-locked by the live process.
            if path.is_file() and path.suffix not in (".lock", ".owner"):
                assert SYNTHETIC_KEY.encode() not in path.read_bytes(), path

    def test_remote_constructs_no_credential_store(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from tests.api._remote import remote_harness

        def forbidden() -> object:
            raise AssertionError("remote deployment must not build a credential store")

        monkeypatch.setattr("afterworlds.api.app.make_credential_store", forbidden)
        for harness in remote_harness(tmp_path, monkeypatch):
            assert harness.app.state.byok_settings is None

    def test_local_deployment_needs_no_account(self, client: TestClient) -> None:
        status = client.get("/api/auth/session").json()
        assert status == {
            "deployment": "local",
            "signed_in": False,
            "account_id": None,
            "contact_address": None,
            "schema_version": 1,
        }
        assert (
            client.post(
                "/api/stories", json={"title": "L", "mode": "branching"}
            ).status_code
            == 201
        )
        assert (
            client.get("/api/account").json()["byok"]["readiness_source"]
            == "local_device"
        )
        for path in ("/api/auth/sign-in", "/api/admin/session", "/api/account/close"):
            resp = client.post(path, json={})
            assert resp.status_code == 404
            assert _error(resp) == "deployment_route_unavailable"


def test_real_provider_wiring_has_no_server_byok_custody(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Non-fake remote construction: no credential store is built and BYOK
    resolution below HTTP access selection fails closed. No key is set, so
    no provider transport is ever constructed or called."""
    from afterworlds.api.access_path import NoServerCredentials
    from afterworlds.entitlement.enums import RuntimeAccessPath
    from afterworlds.pipeline.provider import ProviderConfigError
    from tests.api._remote import make_remote

    def forbidden() -> object:
        raise AssertionError("remote deployment must not build a credential store")

    monkeypatch.delenv("AFTERWORLDS_FAKE_PROVIDER", raising=False)
    for name in ("ANTHROPIC_API_KEY", "OPENROUTER_API_KEY"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv(
        "AFTERWORLDS_RETRIEVAL_PERSIST_DIRECTORY", str(tmp_path / "chroma")
    )
    monkeypatch.setattr("afterworlds.api.app.make_credential_store", forbidden)
    monkeypatch.setattr(
        "afterworlds.api.pipeline_wiring.make_credential_store", forbidden
    )
    harness = make_remote(tmp_path)
    try:
        resolver = harness.app.state.orchestrator._inner._provider_resolver
        store = resolver._credential_store
        assert isinstance(store, NoServerCredentials)
        with pytest.raises(PermissionError):
            store.set(uuid.uuid4(), "anthropic", SYNTHETIC_KEY)
        with pytest.raises(ProviderConfigError, match="no configured credentials"):
            resolver.resolve_for_turn(RuntimeAccessPath.BYOK, uuid.uuid4())
    finally:
        harness.close()
