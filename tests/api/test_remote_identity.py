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


def _break(remote: RemoteHarness, monkeypatch: pytest.MonkeyPatch, method: str) -> None:
    def broken(*_a: object, **_k: object) -> object:
        raise OperationalError("SELECT secret-ish", {}, Exception("store down"))

    monkeypatch.setattr(remote.app.state.identity, method, broken)


def _unavailable(resp) -> None:  # type: ignore[no-untyped-def]
    assert resp.status_code == 503, resp.text
    assert _error(resp) == "identity_unavailable"
    assert "store down" not in resp.text and "SELECT" not in resp.text
    # No false success: no session cookie is set or cleared.
    assert "set-cookie" not in resp.headers


class TestIdentityUnavailableOnHttpIdentityCalls:
    """Every HTTP identity operation answers a typed, sanitized 503 when the
    identity store fails -- public, staff and post-admission routes alike."""

    @pytest.mark.parametrize(
        ("method", "path", "body"),
        [
            ("register", "/api/auth/register", {"contact_address": "n@example.test"}),
            (
                "complete_enrollment",
                "/api/auth/register/complete",
                {
                    "contact_address": "n@example.test",
                    "code": "000000",
                    "password": PASSWORD,
                },
            ),
            (
                "sign_in",
                "/api/auth/sign-in",
                {"contact_address": "a@example.test", "password": PASSWORD},
            ),
            ("begin_recovery", "/api/auth/recovery", {"contact_address": "a@x.test"}),
            (
                "complete_recovery",
                "/api/auth/recovery/complete",
                {
                    "contact_address": "a@example.test",
                    "code": "000000",
                    "new_password": NEW_PASSWORD,
                },
            ),
            (
                "sign_in",
                "/api/admin/session",
                {"contact_address": "a@example.test", "password": PASSWORD},
            ),
        ],
    )
    def test_public_lifecycle_calls(
        self,
        remote: RemoteHarness,
        monkeypatch: pytest.MonkeyPatch,
        method: str,
        path: str,
        body: dict[str, str],
    ) -> None:
        remote.enroll("a@example.test")
        _break(remote, monkeypatch, method)
        _unavailable(remote.client().post(path, json=body))

    def test_sign_in_contact_lookup_sets_no_cookie(
        self, remote: RemoteHarness, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        remote.enroll("a@example.test")
        _break(remote, monkeypatch, "contact_address_for")
        anon = remote.client()
        _unavailable(
            anon.post(
                "/api/auth/sign-in",
                json={"contact_address": "a@example.test", "password": PASSWORD},
            )
        )
        assert anon.cookies.get("aw_session") is None

    def test_session_discovery(
        self, remote: RemoteHarness, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        a = remote.enroll("a@example.test")
        anon = remote.client()
        anon.cookies.set("aw_session", "not-a-real-token")
        with monkeypatch.context() as m:
            _break(remote, m, "contact_address_for")
            _unavailable(a.get("/api/auth/session"))
        with monkeypatch.context() as m:
            _break(remote, m, "resolve")
            # An unreachable store is never reported as signed out.
            _unavailable(a.get("/api/auth/session"))
            _unavailable(anon.get("/api/auth/session"))
        # Missing and invalid sessions remain ordinary signed-out answers.
        assert remote.client().get("/api/auth/session").json()["signed_in"] is False
        assert anon.get("/api/auth/session").json()["signed_in"] is False
        assert a.get("/api/auth/session").json()["signed_in"] is True

    def test_sign_out_is_not_confirmed(
        self, remote: RemoteHarness, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        a = remote.enroll("a@example.test")
        with monkeypatch.context() as m:
            _break(remote, m, "sign_out")
            _unavailable(a.post("/api/auth/sign-out"))
        # Nothing was revoked or cleared: the session still works.
        assert a.get("/api/stories").status_code == 200

    def test_closure_after_admission(
        self, remote: RemoteHarness, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        a = remote.enroll("a@example.test")
        with monkeypatch.context() as m:
            _break(remote, m, "close_account")
            _unavailable(a.post("/api/account/close", json={"password": PASSWORD}))
        assert a.get("/api/stories").status_code == 200

    def test_staff_calls_after_admission(
        self, remote: RemoteHarness, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        owner = remote.enroll("owner@example.test")
        target = remote.account_id(owner)
        identity = remote.app.state.identity
        assert (
            identity.bootstrap_owner_administrator("owner@example.test", PASSWORD).value
            == "provisioned"
        )
        staff = remote.client()
        assert (
            staff.post(
                "/api/admin/session",
                json={"contact_address": "owner@example.test", "password": PASSWORD},
            ).status_code
            == 200
        )
        for method, call in (
            ("get_account", lambda: staff.get(f"/api/admin/accounts/{target}")),
            (
                "revoke_account_sessions",
                lambda: staff.post(
                    f"/api/admin/accounts/{target}/sessions/revoke",
                    json={"reason": "store test"},
                ),
            ),
            ("sign_out", lambda: staff.delete("/api/admin/session")),
        ):
            with monkeypatch.context() as m:
                _break(remote, m, method)
                _unavailable(call())
        # The staff session and the target's session survived every failure.
        assert staff.get(f"/api/admin/accounts/{target}").status_code == 200
        assert owner.get("/api/stories").status_code == 200


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


class TestPostAdmissionControlFailures:
    """Review 5572565473 r4314625068: a control-authority read failing after
    admission is 503 identity_unavailable at its source -- never a false 404,
    an empty list or a relabelled content-store fault."""

    @staticmethod
    def _broken_control_read(*_a: object, **_k: object) -> object:
        raise OperationalError("SELECT secret-ish", {}, Exception("control down"))

    def test_story_authorization_and_listing(
        self, remote: RemoteHarness, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        a = remote.enroll("a@example.test")
        sid = a.post("/api/stories", json={"title": "S", "mode": "branching"}).json()[
            "story_id"
        ]
        monkeypatch.setattr(
            "afterworlds.remote.access.is_suppressed", self._broken_control_read
        )
        for resp in (a.get(f"/api/stories/{sid}"), a.get("/api/stories")):
            assert resp.status_code == 503 and _error(resp) == "identity_unavailable"
            assert "control down" not in resp.text and "SELECT" not in resp.text

    def test_suppression_admission(
        self, remote: RemoteHarness, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        a = remote.enroll("a@example.test")
        with monkeypatch.context() as m:
            m.setattr(
                "afterworlds.remote.access.active_suppressions",
                self._broken_control_read,
            )
            resp = a.post("/api/stories", json={"title": "S", "mode": "branching"})
        assert resp.status_code == 503 and _error(resp) == "identity_unavailable"
        assert a.get("/api/stories").json()["stories"] == []  # nothing created

    def test_owning_service_recheck(
        self, remote: RemoteHarness, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import sqlalchemy as sa

        from afterworlds.persistence.orm.node import TurnORM
        from tests.api.test_remote_isolation import _branching_in_play, _seed_hosted

        a = remote.enroll("a@example.test")
        _seed_hosted(remote, remote.account_id(a))
        sid = _branching_in_play(a)
        import afterworlds.remote.access as access

        real = access.is_suppressed
        calls = {"n": 0}

        def fails_after_authorization(*a_: object, **k: object) -> object:
            calls["n"] += 1
            if calls["n"] > 1:  # the route guard passed; the seam rechecks
                return self._broken_control_read()
            return real(*a_, **k)

        with remote.app.state.session_factory() as s:
            before = s.scalar(sa.select(sa.func.count()).select_from(TurnORM))
        monkeypatch.setattr(access, "is_suppressed", fails_after_authorization)
        resp = a.post(f"/api/stories/{sid}/turns", json={"user_input": "Go."})
        assert resp.status_code == 503 and _error(resp) == "identity_unavailable"
        assert calls["n"] >= 2
        with remote.app.state.session_factory() as s:
            assert s.scalar(sa.select(sa.func.count()).select_from(TurnORM)) == before

    def test_a_content_store_fault_is_not_relabelled(
        self, remote: RemoteHarness, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from fastapi.testclient import TestClient

        from afterworlds.api.remote_access import CSRF_HEADER

        a = remote.enroll("a@example.test")
        sid = a.post("/api/stories", json={"title": "S", "mode": "branching"}).json()[
            "story_id"
        ]
        monkeypatch.setattr(
            "afterworlds.remote.access.story_owner", self._broken_control_read
        )
        quiet = TestClient(
            remote.app,
            base_url="https://testserver",
            headers={CSRF_HEADER: "1"},
            cookies=dict(a.cookies),
            raise_server_exceptions=False,
        )
        with quiet:
            resp = quiet.get(f"/api/stories/{sid}")
        assert resp.status_code == 500 and _error(resp) == "internal_error"


class TestVerifierWork:
    """Review 5573568757 r4315408061: no usable verifier -- unknown address,
    pending enrollment, unknown scheme, malformed value -- costs exactly the
    same scrypt work as a real check and never authenticates."""

    @staticmethod
    def _spy(monkeypatch: pytest.MonkeyPatch) -> list[tuple[int, int, int]]:
        from afterworlds.remote import verifiers

        calls: list[tuple[int, int, int]] = []
        real = verifiers._scrypt

        def counted(password: str, salt: bytes, n: int, r: int, p: int) -> bytes:
            digest = real(password, salt, n, r, p)
            calls.append((n, r, p))  # a completed hash only
            return digest

        monkeypatch.setattr(verifiers, "_scrypt", counted)
        return calls

    @pytest.mark.parametrize(
        "stored",
        [
            None,
            "",
            "!",  # a pending enrollment's unusable marker
            "argon2$1$2$3$aa$bb",  # unknown scheme
            "scrypt$16384$8$1$aa",  # missing field
            "scrypt$sixteen$8$1$aa$bb",  # malformed number
            "scrypt$16384$8$1$zz$bb",  # malformed salt hex
            "scrypt$16384$8$1$aa$not-hex",  # malformed digest
            "scrypt$3$8$1$aa$bb",  # parameters hashlib rejects
        ],
    )
    def test_unusable_verifiers_cost_one_standard_hash_and_fail(
        self, monkeypatch: pytest.MonkeyPatch, stored: str | None
    ) -> None:
        from afterworlds.remote import verifiers

        calls = self._spy(monkeypatch)
        assert verifiers.verify_password(PASSWORD, stored) is False
        assert calls == [(verifiers._N, verifiers._R, verifiers._P)]

    def test_a_dummy_match_still_fails_closed(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from afterworlds.remote import verifiers

        digest = bytes(32)
        monkeypatch.setattr(verifiers, "_scrypt", lambda *_a: digest)
        unusable = f"scrypt$3$8$1$aa${digest.hex()}"
        for stored in (None, "!", unusable):
            assert verifiers.verify_password(PASSWORD, stored) is False

    @pytest.mark.parametrize(
        "stored",
        [
            f"scrypt${2**64}$8$1$aa$bb",
            f"scrypt$16384${2**64}$1$aa$bb",
            f"scrypt$16384$8${2**64}$aa$bb",
            f"scrypt${2**32}$8$1$aa$bb",  # a power of two beyond C unsigned long
            f"scrypt$16384${2**32}$1$aa$bb",
            f"scrypt$16384$8${2**32}$aa$bb",
        ],
    )
    def test_numeric_overflow_costs_one_standard_hash_and_fails(
        self, monkeypatch: pytest.MonkeyPatch, stored: str
    ) -> None:
        """Residue: hashlib raises TypeError (not ValueError) for parameters
        beyond a C unsigned long; such a verifier is unusable."""
        from afterworlds.remote import verifiers

        calls = self._spy(monkeypatch)
        assert verifiers.verify_password(PASSWORD, stored) is False
        assert calls == [(verifiers._N, verifiers._R, verifiers._P)]
        digest = bytes(32)
        monkeypatch.setattr(verifiers, "_scrypt", lambda *_a: digest)
        forged = stored.rsplit("$", 1)[0] + "$" + digest.hex()
        assert verifiers.verify_password(PASSWORD, forged) is False

    def test_valid_verifiers_keep_their_behavior_and_one_hash(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from afterworlds.remote import verifiers

        stored = verifiers.hash_password(PASSWORD)
        calls = self._spy(monkeypatch)
        assert verifiers.verify_password(PASSWORD, stored) is True
        assert verifiers.verify_password(NEW_PASSWORD, stored) is False
        assert calls == [(verifiers._N, verifiers._R, verifiers._P)] * 2

    @pytest.mark.parametrize("path", ["/api/auth/sign-in", "/api/admin/session"])
    def test_pending_enrollment_sign_in_does_the_same_work_as_an_unknown_address(
        self, remote: RemoteHarness, monkeypatch: pytest.MonkeyPatch, path: str
    ) -> None:
        anon = remote.client()
        assert (
            anon.post(
                "/api/auth/register", json={"contact_address": "pending@example.test"}
            ).status_code
            == 202
        )  # enrollment started, never completed
        calls = self._spy(monkeypatch)
        responses = []
        for address in ("pending@example.test", "nobody@example.test"):
            before = len(calls)
            resp = remote.client().post(
                path, json={"contact_address": address, "password": PASSWORD}
            )
            responses.append((resp.status_code, resp.json()))
            assert "set-cookie" not in resp.headers
            assert len(calls) - before == 1  # one hash each, same parameters
        assert len(set(calls)) == 1
        assert responses[0] == responses[1]
        assert responses[0][0] == 401
        assert responses[0][1]["error_code"] == "authentication_failed"
