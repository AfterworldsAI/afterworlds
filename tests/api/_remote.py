"""Remote-deployment harness (prerequisite #205): disposable content, control
and outbox stores, one ``create_app`` per test, and per-identity clients.

Each identity gets its own ``TestClient`` (its own cookie jar), so two
accounts and the Owner's staff session never share browser state. Clients
use ``https://testserver`` because session cookies are ``Secure``.
"""

from __future__ import annotations

import gc
import json
import sys
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient

from afterworlds.api.app import create_app
from afterworlds.api.config import ApiSettings
from afterworlds.api.remote_access import CSRF_HEADER

PASSWORD = "correct horse battery staple"  # pragma: allowlist secret


def remote_settings(tmp_path: Path) -> ApiSettings:
    return ApiSettings(
        database_url=f"sqlite:///{tmp_path / 'content.db'}",
        frontend_dist_dir=tmp_path / "no_frontend",
        deployment="remote",
        control_database_url=f"sqlite:///{tmp_path / 'control.db'}",
        notice_outbox_dir=tmp_path / "outbox",
    )


def latest_code(outbox: Path, address: str, kind: str) -> str:
    notices = sorted(outbox.glob(f"{kind}-*.json"), key=lambda p: p.stat().st_mtime_ns)
    for path in reversed(notices):
        notice = json.loads(path.read_text(encoding="utf-8"))
        if notice["to"] == address:
            return str(notice["code"])
    raise AssertionError(f"no {kind} notice for {address}")


@dataclass
class RemoteHarness:
    app: FastAPI
    settings: ApiSettings
    tmp_path: Path
    clients: list[TestClient] = field(default_factory=list)

    @property
    def outbox(self) -> Path:
        assert self.settings.notice_outbox_dir is not None
        return self.settings.notice_outbox_dir

    def client(self, *, csrf: bool = True) -> TestClient:
        headers = {CSRF_HEADER: "1"} if csrf else {}
        c = TestClient(self.app, base_url="https://testserver", headers=headers)
        c.__enter__()
        self.clients.append(c)
        return c

    def enroll(self, address: str, password: str = PASSWORD) -> TestClient:
        """Register, verify and sign in; returns that identity's client."""
        c = self.client()
        assert (
            c.post("/api/auth/register", json={"contact_address": address}).status_code
            == 202
        )
        code = self.code(address, "enrollment")
        resp = c.post(
            "/api/auth/register/complete",
            json={"contact_address": address, "code": code, "password": password},
        )
        assert resp.status_code == 200, resp.text
        resp = c.post(
            "/api/auth/sign-in", json={"contact_address": address, "password": password}
        )
        assert resp.status_code == 200, resp.text
        return c

    def code(self, address: str, kind: str) -> str:
        """The latest mailed code, after the background delivery settled."""
        self.app.state.identity.drain_notices()
        return latest_code(self.outbox, address, kind)

    def account_id(self, c: TestClient) -> str:
        body = c.get("/api/auth/session").json()
        assert body["signed_in"], body
        return str(body["account_id"])

    def staff(
        self, address: str = "owner@example.test", *, enroll: bool = True
    ) -> TestClient:
        """Enroll *address* if needed, provision it as the Owner administrator
        through the real bootstrap command, and return its staff client."""
        import io

        from afterworlds.remote import bootstrap

        assert self.settings.control_database_url is not None
        if enroll:
            self.enroll(address)
        stdin = sys.stdin
        try:
            sys.stdin = io.StringIO(PASSWORD + "\n")
            code = bootstrap.main(
                [
                    "--contact-address",
                    address,
                    "--control-db",
                    self.settings.control_database_url,
                    "--password-stdin",
                ]
            )
        finally:
            sys.stdin = stdin
        assert code == 0
        staff = self.client()
        resp = staff.post(
            "/api/admin/session",
            json={"contact_address": address, "password": PASSWORD},
        )
        assert resp.status_code == 200, resp.text
        return staff

    def seed_hosted(self, account_id: str, credits: str = "1000") -> None:
        """Activate hosted access and grant credits through the entitlement
        owner (stands in for CRD Issue 23's commercial events)."""
        import uuid
        from datetime import UTC, datetime
        from decimal import Decimal

        from afterworlds.entitlement.enums import (
            EntitlementEventType,
            HostedAccessPlan,
        )
        from afterworlds.entitlement.payloads import (
            HostedAccessActivatedPayload,
            SubscriptionCreditGrantPayload,
        )
        from afterworlds.entitlement.service import EntitlementService

        with self.app.state.session_factory() as session:
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
                SubscriptionCreditGrantPayload(hosted_credit_delta=Decimal(credits)),
            )

    def close(self) -> None:
        for c in self.clients:
            c.__exit__(None, None, None)
        # Like process exit: release pooled connections and the store lock.
        self.app.state.session_factory.kw["bind"].dispose()
        self.app.state.control_factory.kw["bind"].dispose()
        from chromadb.api.shared_system_client import SharedSystemClient

        SharedSystemClient.clear_system_cache()
        self.app.state.orchestrator = None
        self.app.state.rpg_actions = None
        gc.collect()
        self.app.state.store_lock.close()
        self.app.state.vector_lock.close()
        if getattr(self.app.state, "control_lock", None) is not None:
            self.app.state.control_lock.close()


def make_remote(tmp_path: Path, **_: Any) -> RemoteHarness:
    settings = remote_settings(tmp_path)
    return RemoteHarness(app=create_app(settings), settings=settings, tmp_path=tmp_path)


def remote_harness(tmp_path: Path, monkeypatch: Any) -> Iterator[RemoteHarness]:
    monkeypatch.setenv(
        "AFTERWORLDS_RETRIEVAL_PERSIST_DIRECTORY", str(tmp_path / "chroma")
    )
    monkeypatch.setenv("AFTERWORLDS_FAKE_PROVIDER", "1")
    harness = make_remote(tmp_path)
    try:
        yield harness
    finally:
        harness.close()
