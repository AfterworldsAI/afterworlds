"""Remote-deployment harness (prerequisite #205): disposable content, control
and outbox stores, one ``create_app`` per test, and per-identity clients.

Each identity gets its own ``TestClient`` (its own cookie jar), so two
accounts and the Owner's staff session never share browser state. Clients
use ``https://testserver`` because session cookies are ``Secure``.
"""

from __future__ import annotations

import json
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
        code = latest_code(self.outbox, address, "enrollment")
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

    def account_id(self, c: TestClient) -> str:
        body = c.get("/api/auth/session").json()
        assert body["signed_in"], body
        return str(body["account_id"])

    def close(self) -> None:
        for c in self.clients:
            c.__exit__(None, None, None)
        self.app.state.store_lock.close()


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
