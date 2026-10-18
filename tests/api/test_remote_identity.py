"""Prerequisite #205 §1/§6: trusted remote identity through the built app.

Enrollment, sign-in/out, expiry, revocation, recovery, closure, CSRF, no
account disclosure, and the default-deny route boundary -- all through
``create_app`` in remote mode with disposable stores.
"""

from __future__ import annotations

import re
import uuid
from datetime import timedelta

import pytest
from sqlalchemy.exc import OperationalError

from afterworlds.api.remote_access import PUBLIC_PATHS, enforce_access
from afterworlds.remote.control_store import utc_now
from tests.api._remote import PASSWORD, RemoteHarness, latest_code

NEW_PASSWORD = "an entirely new passphrase"  # pragma: allowlist secret


def _error(resp) -> str:  # type: ignore[no-untyped-def]
    body = resp.json()
    assert body["schema_version"] == 1
    return str(body["error_code"])


class TestDefaultDeny:
    def test_enforce_access_is_app_level(self, remote: RemoteHarness) -> None:
        assert any(
            d.dependency is enforce_access for d in remote.app.router.dependencies
        )

    def test_every_non_public_route_requires_a_session(
        self, remote: RemoteHarness
    ) -> None:
        # Walk the one generated contract: every operation it publishes.
        anon = remote.client()
        checked = 0
        for template, operations in remote.app.openapi()["paths"].items():
            if not template.startswith("/api"):
                continue
            path = re.sub(r"\{provider\}", "anthropic", template)
            path = re.sub(r"\{[a-z_]+\}", lambda _m: str(uuid.uuid4()), path)
            for method in operations:
                resp = anon.request(method.upper(), path, json={})
                checked += 1
                if template in PUBLIC_PATHS:
                    body = resp.json()
                    assert body.get("error_code") != "authentication_required", (
                        method,
                        path,
                    )
                elif template.startswith("/api/account/byok/"):
                    assert _error(resp) == "byok_local_only", (method, path)
                else:
                    assert resp.status_code == 401, (method, path, resp.text)
                    assert _error(resp) == "authentication_required"
        assert checked > 30

    def test_health_is_public_and_carries_no_account_data(
        self, remote: RemoteHarness
    ) -> None:
        resp = remote.client().get("/api/health")
        assert resp.status_code == 200
        assert set(resp.json()) == {"status", "db_reachable", "schema_version"}

    def test_unsafe_request_without_client_header_is_rejected(
        self, remote: RemoteHarness
    ) -> None:
        c = remote.enroll("a@example.test")
        foreign = remote.client(csrf=False)
        foreign.cookies.update(c.cookies)
        resp = foreign.post("/api/stories", json={"title": "T", "mode": "branching"})
        assert resp.status_code == 403 and _error(resp) == "request_origin_rejected"
        # Sign-in too (login CSRF), and nothing was created.
        resp = foreign.post(
            "/api/auth/sign-in",
            json={"contact_address": "a@example.test", "password": PASSWORD},
        )
        assert _error(resp) == "request_origin_rejected"
        assert c.get("/api/stories").json()["stories"] == []


class TestEnrollmentAndSignIn:
    def test_register_reveals_nothing_about_existing_accounts(
        self, remote: RemoteHarness
    ) -> None:
        remote.enroll("taken@example.test")
        c = remote.client()
        new = c.post("/api/auth/register", json={"contact_address": "new@example.test"})
        taken = c.post(
            "/api/auth/register", json={"contact_address": "taken@example.test"}
        )
        assert new.status_code == taken.status_code == 202
        assert new.json() == taken.json()
        # The enrolled address received no new code.
        assert len(list(remote.outbox.glob("enrollment-*.json"))) == 2

    def test_enrollment_requires_the_emailed_code(self, remote: RemoteHarness) -> None:
        c = remote.client()
        c.post("/api/auth/register", json={"contact_address": "v@example.test"})
        resp = c.post(
            "/api/auth/register/complete",
            json={
                "contact_address": "v@example.test",
                "code": "guess",
                "password": PASSWORD,
            },
        )
        assert resp.status_code == 401 and _error(resp) == "authentication_failed"
        resp = c.post(
            "/api/auth/sign-in",
            json={"contact_address": "v@example.test", "password": PASSWORD},
        )
        assert _error(resp) == "authentication_failed"

    def test_squatter_cannot_preset_the_password(self, remote: RemoteHarness) -> None:
        # Registration takes no password: only the code holder sets it.
        resp = remote.client().post(
            "/api/auth/register",
            json={
                "contact_address": "x@example.test",
                "password": "squatter-pass",  # pragma: allowlist secret
            },
        )
        assert resp.status_code == 422

    def test_failed_sign_in_is_generic(self, remote: RemoteHarness) -> None:
        remote.enroll("a@example.test")
        c = remote.client()
        wrong = c.post(
            "/api/auth/sign-in",
            json={
                "contact_address": "a@example.test",
                "password": "wrong password!",  # pragma: allowlist secret
            },
        )
        unknown = c.post(
            "/api/auth/sign-in",
            json={"contact_address": "nobody@example.test", "password": PASSWORD},
        )
        assert wrong.status_code == unknown.status_code == 401
        assert wrong.json() == unknown.json()
        assert "set-cookie" not in wrong.headers

    def test_session_cookie_is_hardened_and_rotated(
        self, remote: RemoteHarness
    ) -> None:
        c = remote.enroll("a@example.test")
        first = c.cookies.get("aw_session")
        resp = c.post(
            "/api/auth/sign-in",
            json={"contact_address": "a@example.test", "password": PASSWORD},
        )
        cookie = resp.headers["set-cookie"].lower()
        assert (
            "httponly" in cookie and "secure" in cookie and "samesite=strict" in cookie
        )
        assert c.cookies.get("aw_session") != first

    def test_presented_unknown_cookie_never_becomes_a_session(
        self, remote: RemoteHarness
    ) -> None:
        remote.enroll("a@example.test")
        c = remote.client()
        c.cookies.set("aw_session", "attacker-chosen-value", domain="testserver.local")
        assert c.get("/api/stories").status_code == 401
        c.post(
            "/api/auth/sign-in",
            json={"contact_address": "a@example.test", "password": PASSWORD},
        )
        assert c.cookies.get("aw_session") != "attacker-chosen-value"

    def test_sign_out_revokes_server_side(self, remote: RemoteHarness) -> None:
        c = remote.enroll("a@example.test")
        stolen = dict(c.cookies)
        assert c.post("/api/auth/sign-out").json()["signed_in"] is False
        replay = remote.client()
        replay.cookies.update(stolen)
        assert replay.get("/api/stories").status_code == 401

    def test_expired_session_fails_closed(self, remote: RemoteHarness) -> None:
        c = remote.enroll("a@example.test")
        later = utc_now() + timedelta(hours=25)
        remote.app.state.identity._now = lambda: later
        resp = c.get("/api/stories")
        assert resp.status_code == 401 and _error(resp) == "authentication_required"
        assert c.get("/api/auth/session").json()["signed_in"] is False

    def test_identity_store_unavailable_fails_closed(
        self, remote: RemoteHarness, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        c = remote.enroll("a@example.test")

        def broken(*_a: object, **_k: object) -> object:
            raise OperationalError("SELECT secret-ish", {}, Exception("store down"))

        monkeypatch.setattr(remote.app.state.identity, "resolve", broken)
        resp = c.get("/api/stories")
        assert resp.status_code == 503 and _error(resp) == "identity_unavailable"
        assert "store down" not in resp.text and "SELECT" not in resp.text


class TestRecovery:
    def test_recovery_rotates_credentials_and_revokes_sessions(
        self, remote: RemoteHarness
    ) -> None:
        a = remote.enroll("a@example.test")
        story = a.post("/api/stories", json={"title": "Mine", "mode": "branching"})
        story_id = story.json()["story_id"]
        anon = remote.client()
        assert (
            anon.post(
                "/api/auth/recovery", json={"contact_address": "a@example.test"}
            ).status_code
            == 202
        )
        code = latest_code(remote.outbox, "a@example.test", "recovery")
        resp = anon.post(
            "/api/auth/recovery/complete",
            json={
                "contact_address": "a@example.test",
                "code": code,
                "new_password": NEW_PASSWORD,
            },
        )
        assert resp.status_code == 200, resp.text
        assert a.get("/api/stories").status_code == 401  # old session revoked
        old = anon.post(
            "/api/auth/sign-in",
            json={"contact_address": "a@example.test", "password": PASSWORD},
        )
        assert old.status_code == 401
        assert (
            anon.post(
                "/api/auth/sign-in",
                json={"contact_address": "a@example.test", "password": NEW_PASSWORD},
            ).status_code
            == 200
        )
        # Ownership unchanged; no staff authority gained.
        assert [s["story_id"] for s in anon.get("/api/stories").json()["stories"]] == [
            story_id
        ]
        assert _error(anon.get(f"/api/admin/accounts/{uuid.uuid4()}")) == (
            "staff_authority_required"
        )
        # The code is single-use.
        again = anon.post(
            "/api/auth/recovery/complete",
            json={
                "contact_address": "a@example.test",
                "code": code,
                "new_password": PASSWORD,
            },
        )
        assert _error(again) == "authentication_failed"

    def test_recovery_for_unknown_address_is_indistinguishable(
        self, remote: RemoteHarness
    ) -> None:
        remote.enroll("a@example.test")
        c = remote.client()
        known = c.post("/api/auth/recovery", json={"contact_address": "a@example.test"})
        unknown = c.post(
            "/api/auth/recovery", json={"contact_address": "z@example.test"}
        )
        assert known.status_code == unknown.status_code == 202
        assert known.json() == unknown.json()
        assert len(list(remote.outbox.glob("recovery-*.json"))) == 1

    def test_identifiers_alone_cannot_recover(self, remote: RemoteHarness) -> None:
        a = remote.enroll("a@example.test")
        account_id = remote.account_id(a)
        c = remote.client()
        c.post("/api/auth/recovery", json={"contact_address": "a@example.test"})
        for guess in (account_id, "a@example.test", a.cookies.get("aw_session") or "x"):
            resp = c.post(
                "/api/auth/recovery/complete",
                json={
                    "contact_address": "a@example.test",
                    "code": guess,
                    "new_password": NEW_PASSWORD,
                },
            )
            assert _error(resp) == "authentication_failed"

    def test_recovery_code_attempts_are_limited(self, remote: RemoteHarness) -> None:
        remote.enroll("a@example.test")
        c = remote.client()
        c.post("/api/auth/recovery", json={"contact_address": "a@example.test"})
        code = latest_code(remote.outbox, "a@example.test", "recovery")
        for _ in range(5):
            c.post(
                "/api/auth/recovery/complete",
                json={
                    "contact_address": "a@example.test",
                    "code": "wrong",
                    "new_password": NEW_PASSWORD,
                },
            )
        resp = c.post(
            "/api/auth/recovery/complete",
            json={
                "contact_address": "a@example.test",
                "code": code,
                "new_password": NEW_PASSWORD,
            },
        )
        assert _error(resp) == "authentication_failed"


class TestClosure:
    def test_closure_revokes_and_denies(self, remote: RemoteHarness) -> None:
        a = remote.enroll("a@example.test")
        story_id = a.post(
            "/api/stories", json={"title": "Mine", "mode": "branching"}
        ).json()["story_id"]
        stolen = dict(a.cookies)
        wrong = a.post("/api/account/close", json={"password": "not my password"})
        assert _error(wrong) == "authentication_failed"
        assert (
            a.post("/api/account/close", json={"password": PASSWORD}).status_code == 200
        )
        replay = remote.client()
        replay.cookies.update(stolen)
        assert replay.get(f"/api/stories/{story_id}").status_code == 401
        resp = replay.post(
            "/api/auth/sign-in",
            json={"contact_address": "a@example.test", "password": PASSWORD},
        )
        assert _error(resp) == "authentication_failed"
        # A closed account cannot be recovered or re-enrolled into.
        replay.post("/api/auth/recovery", json={"contact_address": "a@example.test"})
        assert not list(remote.outbox.glob("recovery-*.json"))
        replay.post("/api/auth/register", json={"contact_address": "a@example.test"})
        assert len(list(remote.outbox.glob("enrollment-*.json"))) == 1
