"""Codex review of a881bf5e (CRD Issue 22 #206): proofs for the deletion
boundary, export coordination, export delivery before closure, suppression
release, orphan transcript export, receipt-credential recovery and the
administrator approval reason."""

from __future__ import annotations

import threading
import time
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
import sqlalchemy as sa

from afterworlds.operations import export as export_module
from afterworlds.operations.retention import release_suppression
from afterworlds.remote.control_orm import DeletionSuppressionORM
from tests.api._remote import PASSWORD, RemoteHarness
from tests.operations._data import chunk_count, plant, play_branching, rows_with, unzip


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
    return dict(resp.json())


def _approve(staff: Any, rid: str) -> dict[str, Any]:
    view = staff.get(f"/api/admin/data-requests/{rid}").json()
    resp = staff.post(
        f"/api/admin/data-requests/{rid}/approve",
        json={
            "expected_revision": view["revision"],
            "reason": "verified owner request",
        },
    )
    assert resp.status_code == 200, resp.text
    return dict(resp.json())


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


def _account(remote: RemoteHarness, address: str) -> tuple[Any, str]:
    c = remote.enroll(address)
    account_id = remote.account_id(c)
    remote.seed_hosted(account_id)
    return c, account_id


class TestDeletionBoundary:
    """P1-1: the enforced write boundary precedes the final inventory."""

    def test_turn_admitted_before_the_fence_is_inventoried_and_removed(
        self, remote: RemoteHarness, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        a, _ = _account(remote, "a@example.test")
        sid = play_branching(a, "Racing", "First.")
        staff = remote.staff()
        req = _request(a, "deletion", "story", sid)
        _confirm(a, req)
        _approve(staff, req["request_id"])

        entered, release = threading.Event(), threading.Event()
        from afterworlds.api.routes import turns as turns_route

        real = turns_route.ensure_story_turn_anchor_node

        # Inside the admitted turn, before its Turn commits.
        def held(*args: Any, **kwargs: Any) -> Any:
            entered.set()
            assert release.wait(30)
            return real(*args, **kwargs)

        monkeypatch.setattr(turns_route, "ensure_story_turn_anchor_node", held)
        turn: list[Any] = []
        t = threading.Thread(
            target=lambda: turn.append(
                a.post(f"/api/stories/{sid}/turns", json={"user_input": "LATEMARK now"})
            )
        )
        t.start()
        assert entered.wait(30)
        done: list[dict[str, Any]] = []
        d = threading.Thread(
            target=lambda: done.append(_execute(staff, req["request_id"]))
        )
        d.start()
        time.sleep(1.0)  # the deletion is now waiting on the account fence
        release.set()
        t.join(60)
        d.join(60)
        assert turn and turn[0].status_code == 200
        assert done and _phase(done[0], "sql_content") == "succeeded", done
        assert rows_with(remote.app.state.session_factory, "LATEMARK") == []
        assert chunk_count(sid) == 0

    def test_story_created_before_the_fence_is_deleted_with_the_account(
        self, remote: RemoteHarness, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        a, a_id = _account(remote, "a@example.test")
        play_branching(a, "Old", "Hello.")
        staff = remote.staff()
        req = _request(a, "deletion", "account")
        _confirm(a, req, password=PASSWORD)
        _approve(staff, req["request_id"])

        from afterworlds.api.routes import stories as stories_route

        entered, release = threading.Event(), threading.Event()
        real = stories_route.record_story_owner

        def held(*args: Any, **kwargs: Any) -> Any:
            entered.set()
            assert release.wait(30)
            return real(*args, **kwargs)

        monkeypatch.setattr(stories_route, "record_story_owner", held)
        created: list[Any] = []
        t = threading.Thread(
            target=lambda: created.append(
                a.post("/api/stories", json={"title": "LATESTORY", "mode": "branching"})
            )
        )
        t.start()
        assert entered.wait(30)
        done: list[dict[str, Any]] = []
        d = threading.Thread(
            target=lambda: done.append(_execute(staff, req["request_id"]))
        )
        d.start()
        time.sleep(1.0)
        release.set()
        t.join(60)
        d.join(60)
        assert created and created[0].status_code == 201
        assert done and _phase(done[0], "sql_content") == "succeeded", done
        assert rows_with(remote.app.state.session_factory, "LATESTORY") == []
        with remote.app.state.session_factory() as s:
            assert (
                s.scalar(
                    sa.text(
                        "SELECT count(*) FROM account_resources WHERE account_id = :a"
                    ),
                    {"a": a_id},
                )
                == 0
            )


class TestExportCoordination:
    """P1-2: every exported Story passes the owner/suppression boundary, and
    an export cannot publish deleted content after the deletion's cleanup."""

    def test_account_export_excludes_a_story_under_failed_deletion(
        self, remote: RemoteHarness
    ) -> None:
        a, _ = _account(remote, "a@example.test")
        s1 = play_branching(a, "Doomed", "DOOMEDMARK here.")
        s2 = play_branching(a, "Kept", "Kept here.")
        staff = remote.staff()
        req = _request(a, "deletion", "story", s1)
        _confirm(a, req)
        _approve(staff, req["request_id"])
        ctx = remote.app.state.data_requests.deletion
        real = ctx.delete_story_chunks

        def broken(_: str) -> int:
            raise RuntimeError("chroma down")

        ctx.delete_story_chunks = broken
        assert _execute(staff, req["request_id"])["state"] == "failed"
        ctx.delete_story_chunks = real

        exp = _request(a, "export", "account")
        _approve(staff, exp["request_id"])
        assert _execute(staff, exp["request_id"])["state"] == "completed"
        files = unzip(a.get(f"/api/data-requests/{exp['request_id']}/artifact").content)
        assert "DOOMEDMARK" not in str(files)
        manifest = files["manifest.json"]
        assert set(manifest["snapshot_boundary"]["stories"]) == {s2}
        excluded = {e["code"]: e for e in manifest["exclusions"]}
        assert excluded["stories_under_deletion"]["count"] == 1

    def test_an_export_in_flight_cannot_publish_after_deletion_cleanup(
        self, remote: RemoteHarness, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        a, _ = _account(remote, "a@example.test")
        s1 = play_branching(a, "Racing export", "RACEMARK prose.")
        staff = remote.staff()
        exp = _request(a, "export", "story", s1)
        _approve(staff, exp["request_id"])
        dele = _request(a, "deletion", "story", s1)
        _confirm(a, dele)
        _approve(staff, dele["request_id"])

        entered, release = threading.Event(), threading.Event()
        real = export_module.build_archive

        def held(*args: Any, **kwargs: Any) -> Any:
            built = real(*args, **kwargs)
            entered.set()
            assert release.wait(30)
            return built

        monkeypatch.setattr(export_module, "build_archive", held)
        from afterworlds.operations import service as service_module

        monkeypatch.setattr(service_module, "build_archive", held)
        out: list[dict[str, Any]] = []
        t = threading.Thread(
            target=lambda: out.append(_execute(staff, exp["request_id"]))
        )
        t.start()
        assert entered.wait(30)
        d = threading.Thread(
            target=lambda: out.append(_execute(staff, dele["request_id"]))
        )
        d.start()
        time.sleep(1.0)
        release.set()
        t.join(60)
        d.join(60)
        view = a.get(f"/api/data-requests/{exp['request_id']}").json()
        download = a.get(f"/api/data-requests/{exp['request_id']}/artifact")
        if download.status_code == 200:
            assert "RACEMARK" not in str(unzip(download.content))
        else:
            assert view["artifact"] is None or view["artifact"]["status"] != "available"
        assert rows_with(remote.app.state.session_factory, "RACEMARK") == []


class TestExportBeforeClosure:
    """P1-3: account deletion never strands a requested export."""

    def test_open_or_undelivered_exports_block_account_erasure_visibly(
        self, remote: RemoteHarness, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        a, _ = _account(remote, "a@example.test")
        play_branching(a, "Mine", "My prose.")
        staff = remote.staff()
        exp = _request(a, "export", "account")
        dele = _request(a, "deletion", "account")
        _confirm(a, dele, password=PASSWORD)
        _approve(staff, dele["request_id"])

        # A queued export blocks closure: visible failure, nothing erased.
        blocked = _execute(staff, dele["request_id"])
        assert blocked["state"] == "failed"
        assert _phase(blocked, "exports") == "failed"
        assert a.get("/api/data-requests").status_code == 200

        # Generated but not yet downloaded: still blocked.
        _approve(staff, exp["request_id"])
        assert _execute(staff, exp["request_id"])["state"] == "completed"
        blocked = _execute(staff, dele["request_id"])
        assert blocked["state"] == "failed"
        assert _phase(blocked, "exports") == "failed"

        # A download whose delivery is not confirmed does not count.
        from afterworlds.operations import service as service_module

        def lost(*_: Any, **__: Any) -> None:
            raise RuntimeError("client went away")

        monkeypatch.setattr(service_module.DataRequestService, "mark_delivered", lost)
        with pytest.raises(RuntimeError):
            a.get(f"/api/data-requests/{exp['request_id']}/artifact")
        monkeypatch.undo()
        assert _execute(staff, dele["request_id"])["state"] == "failed"

        # Delivered: closure proceeds and the export history is preserved.
        assert (
            a.get(f"/api/data-requests/{exp['request_id']}/artifact").status_code == 200
        )
        done = _execute(staff, dele["request_id"])
        assert _phase(done, "exports") == "succeeded"
        assert _phase(done, "identity") == "succeeded"
        export_view = staff.get(f"/api/admin/data-requests/{exp['request_id']}").json()
        assert export_view["state"] == "completed"


class TestSuppressionRelease:
    """P1-5: a suppression is never released over undeleted live content."""

    def test_release_refused_while_live_deletion_is_incomplete(
        self, remote: RemoteHarness
    ) -> None:
        a, _ = _account(remote, "a@example.test")
        s1 = play_branching(a, "Undeleted", "Still here.")
        staff = remote.staff()
        req = _request(a, "deletion", "story", s1)
        _confirm(a, req)
        _approve(staff, req["request_id"])
        ctx = remote.app.state.data_requests.deletion
        real = ctx.delete_story_chunks

        def broken(_: str) -> int:
            raise RuntimeError("chroma down")

        ctx.delete_story_chunks = broken
        assert _execute(staff, req["request_id"])["state"] == "failed"
        ctx.delete_story_chunks = real
        control = remote.app.state.control_factory
        with control() as s:
            sup = s.scalars(
                sa.select(DeletionSuppressionORM).where(
                    DeletionSuppressionORM.request_id == req["request_id"]
                )
            ).one()
        later = datetime.now(UTC) + timedelta(days=400)
        assert not release_suppression(
            control,
            sup.suppression_id,
            now=later,
            content=remote.app.state.session_factory,
            story_chunk_count=chunk_count,
        )
        assert a.get(f"/api/stories/{s1}").status_code == 404


class TestOrphanTranscript:
    """P2-7: attributable orphan Turns are exported; hidden state is not."""

    def test_orphan_turn_prose_is_exported_and_hidden_state_is_not(
        self, remote: RemoteHarness
    ) -> None:
        a, _ = _account(remote, "a@example.test")
        sid = play_branching(a, "Orphans", "Begin.")
        plant(
            remote.app.state.session_factory,
            sid,
            "HIDDENONLY",
            orphan_marker="ORPHANPROSE",
        )
        staff = remote.staff()
        exp = _request(a, "export", "story", sid)
        _approve(staff, exp["request_id"])
        assert _execute(staff, exp["request_id"])["state"] == "completed"
        files = unzip(a.get(f"/api/data-requests/{exp['request_id']}/artifact").content)
        story = files[f"stories/{sid}/story.json"]
        assert any(
            "ORPHANPROSE" in (t["assistant_output"] or "") for t in story["transcript"]
        )
        assert files["manifest.json"]["snapshot_boundary"]["stories"][sid][
            "turns"
        ] == len(story["transcript"])
        assert "HIDDENONLY" not in str(files)


class TestReceiptCredentialRecovery:
    """P2-8: a lost confirmation response does not lose post-closure access."""

    def test_authenticated_reissue_before_closure(self, remote: RemoteHarness) -> None:
        a, _ = _account(remote, "a@example.test")
        staff = remote.staff()
        req = _request(a, "deletion", "account")
        first = _confirm(a, req, password=PASSWORD)  # pretend this response was lost
        confirmed_at = first["request"]["confirmed_at"]
        b = remote.enroll("b@example.test")
        assert (
            b.post(
                f"/api/data-requests/{req['request_id']}/receipt-credential",
                json={"password": PASSWORD},
            ).status_code
            == 404
        )
        assert (
            _error(
                a.post(
                    f"/api/data-requests/{req['request_id']}/receipt-credential",
                    json={"password": "wrong password!!"},
                )
            )
            == "operation_precondition_failed"
        )
        again = a.post(
            f"/api/data-requests/{req['request_id']}/receipt-credential",
            json={"password": PASSWORD},
        )
        assert again.status_code == 200, again.text
        credential = again.json()["receipt_credential"]
        assert credential and credential != first["receipt_credential"]
        assert again.json()["request"]["confirmed_at"] == confirmed_at
        _approve(staff, req["request_id"])
        _execute(staff, req["request_id"])
        anon = remote.client()
        ok = anon.post(
            "/api/data-requests/receipt",
            json={"request_id": req["request_id"], "credential": credential},
        )
        assert ok.status_code == 200
        stale = anon.post(
            "/api/data-requests/receipt",
            json={
                "request_id": req["request_id"],
                "credential": first["receipt_credential"],
            },
        )
        assert stale.status_code == 404


class TestApprovalReason:
    """P2-9: privileged approval records a nonblank, safe reason."""

    def test_approval_without_a_safe_reason_has_no_effect(
        self, remote: RemoteHarness
    ) -> None:
        a, _ = _account(remote, "a@example.test")
        staff = remote.staff()
        req = _request(a, "export", "account")
        url = f"/api/admin/data-requests/{req['request_id']}/approve"
        for body in (
            {"expected_revision": 1},
            {"expected_revision": 1, "reason": "   "},
            {"expected_revision": 1, "reason": "token sk-ant-abcdefghijklmnop"},
        ):
            resp = staff.post(url, json=body)
            assert _error(resp) == "validation_failed", resp.text
        view = staff.get(f"/api/admin/data-requests/{req['request_id']}").json()
        assert view["revision"] == 1 and view["state"] == "awaiting_authorization"
        ok = staff.post(url, json={"expected_revision": 1, "reason": "verified owner"})
        assert ok.status_code == 200
        assert ok.json()["transitions"][-1]["reason_text"] == "verified owner"
        assert uuid.UUID(ok.json()["request_id"])
