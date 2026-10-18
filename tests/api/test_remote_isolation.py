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
