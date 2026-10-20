"""CRD Issue 22 §8 / AC 11: synthetic secrets in malformed input, operator
text and upstream failures never reach responses, logs, durable records or
artifacts; an interrupted deletion attempt resumes after restart without
false completion."""

from __future__ import annotations

import logging
import uuid
from pathlib import Path
from typing import Any

import pytest
import sqlalchemy as sa

from afterworlds.operations import deletion
from tests.api._remote import PASSWORD, RemoteHarness, make_remote
from tests.operations._data import SECRET, files_with, play_branching, rows_with


def _error(resp: Any) -> str:
    return str(resp.json()["error_code"])


def test_secrets_never_echo_or_persist(
    remote: RemoteHarness, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.DEBUG)
    a = remote.enroll("a@example.test")
    a_id = remote.account_id(a)
    remote.seed_hosted(a_id)
    staff = remote.staff()
    probes = [
        (
            a,
            "post",
            "/api/data-requests",
            {SECRET: 1, "kind": "export", "scope": "account"},
        ),
        (a, "post", "/api/data-requests", {"kind": SECRET, "scope": "account"}),
        (
            a,
            "post",
            "/api/data-requests/receipt",
            {"request_id": str(uuid.uuid4()), "credential": SECRET},
        ),
        (
            staff,
            "post",
            f"/api/admin/accounts/{a_id}/credit-adjustments",
            {
                "operation_id": str(uuid.uuid4()),
                "hosted_credit_delta": "1",
                "reason": f"customer pasted {SECRET}",
                "expected_last_entitlement_event_id": None,
            },
        ),
        (
            staff,
            "post",
            f"/api/admin/accounts/{a_id}/credit-adjustments/preview",
            {"hosted_credit_delta": SECRET},
        ),
        (
            staff,
            "post",
            f"/api/admin/anomalies/{SECRET}/notes",
            {"state": "open", "note_code": "other"},
        ),
    ]
    for client, method, path, body in probes:
        resp = getattr(client, method)(path, json=body)
        assert resp.status_code in (404, 422), (path, resp.text)
        assert SECRET not in resp.text, path
    for factory in (remote.app.state.session_factory, remote.app.state.control_factory):
        assert rows_with(factory, SECRET) == []
    # The server's own logs (the test client's request log is client-side).
    assert not [
        r
        for r in caplog.records
        if r.name.startswith("afterworlds") and SECRET in r.getMessage()
    ]
    # Raw bytes of every store file (journals included) carry no trace.
    assert files_with(remote.tmp_path, SECRET) == []


class Interrupted(RuntimeError):
    """Stands in for the process dying mid-attempt (outside any step's own
    failure handling)."""


def test_interrupted_deletion_resumes_after_restart(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(
        "AFTERWORLDS_RETRIEVAL_PERSIST_DIRECTORY", str(tmp_path / "chroma")
    )
    monkeypatch.setenv("AFTERWORLDS_FAKE_PROVIDER", "1")
    h = make_remote(tmp_path)
    try:
        a = h.enroll("a@example.test")
        h.seed_hosted(h.account_id(a))
        sid = play_branching(a, "Cut short", "Begin.")
        staff = h.staff()
        req = a.post(
            "/api/data-requests",
            json={"kind": "deletion", "scope": "story", "story_id": sid},
        ).json()
        rev = a.get(f"/api/data-requests/{req['request_id']}/deletion-preview").json()
        a.post(
            f"/api/data-requests/{req['request_id']}/confirm",
            json={"expected_revision": 1, "scope_revision": rev["scope_revision"]},
        )
        staff.post(
            f"/api/admin/data-requests/{req['request_id']}/approve",
            json={"expected_revision": 2},
        )

        def die(*_: Any, **__: Any) -> Any:
            raise Interrupted

        monkeypatch.setattr(deletion, "_remove_artifacts", die)
        with pytest.raises(Interrupted):
            staff.post(
                f"/api/admin/data-requests/{req['request_id']}/execute",
                json={"expected_revision": 3},
            )
        monkeypatch.undo()
        monkeypatch.setenv(
            "AFTERWORLDS_RETRIEVAL_PERSIST_DIRECTORY", str(tmp_path / "chroma")
        )
        monkeypatch.setenv("AFTERWORLDS_FAKE_PROVIDER", "1")
    finally:
        h.close()

    h = make_remote(tmp_path)
    try:
        staff = h.staff(enroll=False)
        view = staff.get(f"/api/admin/data-requests/{req['request_id']}").json()
        # The interruption left it visibly in progress -- never completed.
        assert view["state"] == "in_progress"
        assert "artifacts" not in {p["phase_code"] for p in view["phases"]}
        resumed = staff.post(
            f"/api/admin/data-requests/{req['request_id']}/execute",
            json={"expected_revision": view["revision"]},
        ).json()
        phases = {p["phase_code"]: p["outcome_code"] for p in resumed["phases"]}
        assert phases["artifacts"] == "succeeded"
        assert phases["sql_content"] == "succeeded"
        assert phases["vector_logical"] == "succeeded"
        attempts = {t["attempt_id"] for t in resumed["transitions"] if t["attempt_id"]}
        assert len(attempts) == 2
        a = h.client()
        a.post(
            "/api/auth/sign-in",
            json={"contact_address": "a@example.test", "password": PASSWORD},
        )
        assert a.get(f"/api/stories/{sid}").status_code == 404
        with h.app.state.session_factory() as s:
            assert s.scalar(sa.text("SELECT count(*) FROM stories")) == 0
    finally:
        h.close()


def test_concurrent_execution_of_one_request_is_refused(remote: RemoteHarness) -> None:
    import threading

    a = remote.enroll("a@example.test")
    staff = remote.staff()
    req = a.post(
        "/api/data-requests", json={"kind": "export", "scope": "account"}
    ).json()
    staff.post(
        f"/api/admin/data-requests/{req['request_id']}/approve",
        json={"expected_revision": 1},
    )
    codes: list[int] = []

    def run() -> None:
        codes.append(
            staff.post(
                f"/api/admin/data-requests/{req['request_id']}/execute",
                json={"expected_revision": 2},
            ).status_code
        )

    threads = [threading.Thread(target=run) for _ in range(3)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert codes.count(200) == 1 and set(codes) <= {200, 409}
    final = staff.get(f"/api/admin/data-requests/{req['request_id']}").json()
    assert final["state"] == "completed"
    assert [t["state"] for t in final["transitions"]].count("in_progress") == 1
