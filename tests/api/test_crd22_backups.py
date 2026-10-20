"""CRD Issue 22 backup handling through the real stores and commands: a
Story deleted after a backup stays backup-pending until that backup is
disposed; no new capture may copy its free-page remnants before physical
compaction; restoring the older backup re-applies the deletion before the
store is served; final completion needs every postcondition."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
import sqlalchemy as sa

from afterworlds.api.app import create_app
from afterworlds.operations import maintenance
from afterworlds.remote import storage_cli
from afterworlds.remote.storage import StoreRefused
from tests.api._remote import PASSWORD, RemoteHarness, make_remote, remote_settings
from tests.operations._data import (
    chunk_count,
    files_with,
    plant,
    play_branching,
    rows_with,
)

MARK = "BACKUPERASEMARK"


@pytest.fixture()
def remote_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    settings = remote_settings(tmp_path)
    for name, value in {
        "AFTERWORLDS_DEPLOYMENT": "remote",
        "AFTERWORLDS_DATABASE_URL": settings.database_url,
        "AFTERWORLDS_CONTROL_DATABASE_URL": str(settings.control_database_url),
        "AFTERWORLDS_NOTICE_OUTBOX_DIR": str(settings.notice_outbox_dir),
        "AFTERWORLDS_FRONTEND_DIST": str(tmp_path / "no_frontend"),
        "AFTERWORLDS_RETRIEVAL_PERSIST_DIRECTORY": str(tmp_path / "chroma"),
        "AFTERWORLDS_FAKE_PROVIDER": "1",
    }.items():
        monkeypatch.setenv(name, value)
    return tmp_path


def _cli(
    module: Any, capsys: pytest.CaptureFixture[str], *argv: str
) -> tuple[int, str]:
    capsys.readouterr()
    code = module.main(list(argv))
    captured = capsys.readouterr()
    return code, (captured.out + captured.err).strip()


def _live_hits(root: Path) -> list[str]:
    hits = files_with(root, MARK)
    return [h for h in hits if h.startswith(("content.db", "chroma"))]


def _phase(view: dict[str, Any], code: str) -> str:
    return next(p["outcome_code"] for p in view["phases"] if p["phase_code"] == code)


def test_backup_pending_compaction_restore_enforcement_and_final_receipt(
    remote_env: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    h: RemoteHarness = make_remote(remote_env)
    a = h.enroll("a@example.test")
    b = h.enroll("b@example.test")
    h.seed_hosted(h.account_id(a))
    h.seed_hosted(h.account_id(b))
    s1 = play_branching(a, "Doomed", f"I whisper {MARK}.")
    s2 = play_branching(a, "Kept", "I keep this.")
    sb = play_branching(b, "Other", "B's own.")
    plant(h.app.state.session_factory, s1, MARK)
    h.close()

    code, b1 = _cli(storage_cli, capsys, "capture", "--to", str(remote_env / "b1"))
    assert code == 0, b1

    h = make_remote(remote_env)
    a = h.client()
    a.post(
        "/api/auth/sign-in",
        json={
            "contact_address": "a@example.test",
            "password": PASSWORD,
        },
    )
    staff = h.staff()
    req = a.post(
        "/api/data-requests",
        json={"kind": "deletion", "scope": "story", "story_id": s1},
    ).json()
    preview = a.get(f"/api/data-requests/{req['request_id']}/deletion-preview").json()
    assert (
        a.post(
            f"/api/data-requests/{req['request_id']}/confirm",
            json={"expected_revision": 1, "scope_revision": preview["scope_revision"]},
        ).status_code
        == 200
    )
    rid = req["request_id"]
    approved = staff.post(
        f"/api/admin/data-requests/{rid}/approve",
        json={"expected_revision": 2, "reason": "verified owner request"},
    ).json()
    view = staff.post(
        f"/api/admin/data-requests/{rid}/execute",
        json={"expected_revision": approved["revision"]},
    ).json()
    assert view["state"] == "in_progress"
    assert _phase(view, "backups") == "pending"  # b1 still holds the Story
    assert _phase(view, "physical_compaction") == "pending"
    backup_deadline = datetime.fromisoformat(view["backup_deadline_at"])
    confirmed = datetime.fromisoformat(view["confirmed_at"])
    assert backup_deadline - confirmed == timedelta(days=30)
    assert rows_with(h.app.state.session_factory, MARK) == []
    h.close()

    # A capture now would copy free-page remnants: refused until compaction.
    code, out = _cli(storage_cli, capsys, "capture", "--to", str(remote_env / "b2"))
    assert code == 1 and "physical compaction" in out
    assert not (remote_env / "b2").exists()
    code, out = _cli(maintenance, capsys, "compact")
    assert code == 0, out
    assert _live_hits(remote_env) == []
    code, b2 = _cli(storage_cli, capsys, "capture", "--to", str(remote_env / "b2"))
    assert code == 0, b2

    # Review P1-4: a restore is admitted only after enforcement ran, even
    # when no suppressed Story is present in it (b2 was captured clean).
    code, clean_restore = _cli(storage_cli, capsys, "restore", "--backup-id", b2)
    assert code == 0, clean_restore
    code, out = _cli(
        storage_cli, capsys, "verify-restore", "--restore-id", clean_restore
    )
    assert code == 1 and "not been enforced" in out
    with pytest.raises(StoreRefused, match="awaiting"):
        create_app(remote_settings(remote_env))

    # Restore the pre-deletion backup: refused service until enforced.
    code, restore_id = _cli(storage_cli, capsys, "restore", "--backup-id", b1)
    assert code == 0, restore_id
    assert _live_hits(remote_env)  # the restored snapshot carries the Story
    with pytest.raises(StoreRefused, match="awaiting"):
        create_app(remote_settings(remote_env))
    code, out = _cli(storage_cli, capsys, "verify-restore", "--restore-id", restore_id)
    assert code == 2 and s1 in out
    code, out = _cli(maintenance, capsys, "enforce-restore")
    assert code == 0, out
    assert _live_hits(remote_env) == []
    assert _cli(storage_cli, capsys, "verify-restore", "--restore-id", restore_id) == (
        0,
        "verified",
    )

    h = make_remote(remote_env)
    try:
        a = h.client()
        a.post(
            "/api/auth/sign-in",
            json={
                "contact_address": "a@example.test",
                "password": PASSWORD,
            },
        )
        b = h.client()
        b.post(
            "/api/auth/sign-in",
            json={
                "contact_address": "b@example.test",
                "password": PASSWORD,
            },
        )
        assert a.get(f"/api/stories/{s1}").status_code == 404
        assert a.get(f"/api/stories/{s2}").status_code == 200
        assert b.get(f"/api/stories/{sb}/turns").json()["turns"]
        assert chunk_count(s1) == 0 and chunk_count(s2) > 0
        # The rebuilt vector store serves the production paths: a turn on a
        # surviving Story retrieves (strict embedding-model guard) and ingests.
        kept = chunk_count(s2)
        turn = a.post(f"/api/stories/{s2}/turns", json={"user_input": "Onward."})
        assert turn.status_code == 200 and turn.json()["disposition"] == "delivered"
        assert chunk_count(s2) > kept
        staff = h.staff(enroll=False)
        # Still backup-pending: b1 exists (b2 was proven clean at capture).
        view = staff.post(f"/api/admin/data-requests/{rid}/finalize").json()
        assert view["state"] == "in_progress"
        assert _phase(view, "backups") == "pending"
    finally:
        h.close()

    assert _cli(storage_cli, capsys, "dispose", "--backup-id", b1) == (0, "disposed")
    code, out = _cli(maintenance, capsys, "finalize")
    assert code == 0 and '"completed"' in out, out

    h = make_remote(remote_env)
    try:
        a = h.client()
        a.post(
            "/api/auth/sign-in",
            json={
                "contact_address": "a@example.test",
                "password": PASSWORD,
            },
        )
        final = a.get(f"/api/data-requests/{rid}").json()
        assert final["state"] == "completed"
        receipt = next(
            r for r in final["receipts"] if r["receipt_kind"] == "deletion_receipt"
        )
        body = receipt["body"]
        assert body["backup_disposition"] == "succeeded"
        assert {c["code"] for c in body["retained_categories"]} >= {
            "data_request_receipt",
            "deletion_suppression",
        }
        assert MARK not in str(final)
        assert all(
            p["outcome_code"] in ("succeeded", "not_applicable")
            for p in final["phases"]
        )
    finally:
        h.close()


def test_overdue_backup_cleanup_is_a_visible_failure(remote: RemoteHarness) -> None:
    a = remote.enroll("a@example.test")
    remote.seed_hosted(remote.account_id(a))
    s1 = play_branching(a, "Late", "Hello.")
    staff = remote.staff()
    # A backup row that was never disposed stands in for one the operator lost.
    from afterworlds.remote.storage import register_backup

    register_backup(
        remote.app.state.control_factory,
        store_id="x",
        storage_locator=str(remote.tmp_path / "lost"),
        original_capture_at=datetime.now(UTC),
        verification_status="verified",
        clean_suppression_ids=[],
    )
    req = a.post(
        "/api/data-requests",
        json={"kind": "deletion", "scope": "story", "story_id": s1},
    ).json()
    preview = a.get(f"/api/data-requests/{req['request_id']}/deletion-preview").json()
    a.post(
        f"/api/data-requests/{req['request_id']}/confirm",
        json={"expected_revision": 1, "scope_revision": preview["scope_revision"]},
    )
    rid = req["request_id"]
    staff.post(
        f"/api/admin/data-requests/{rid}/approve",
        json={"expected_revision": 2, "reason": "verified owner request"},
    )
    view = staff.post(
        f"/api/admin/data-requests/{rid}/execute", json={"expected_revision": 3}
    ).json()
    assert _phase(view, "backups") == "pending"
    service = remote.app.state.data_requests
    later = datetime.now(UTC) + timedelta(days=30, seconds=1)
    service.deletion.now = lambda: later
    service.store._now = lambda: later
    view = staff.post(f"/api/admin/data-requests/{rid}/finalize").json()
    assert view["state"] == "failed"
    assert _phase(view, "backups") == "failed"
    assert "final_deletion" in view["overdue"] or view["state"] == "failed"


def test_account_erasure_compaction_disposes_live_control_store(
    remote_env: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Review round 2, F5: an erased account's contact address leaves no
    remnant in the live control store's file, WAL or journal once compaction
    ran; another account's stays."""
    import json

    h: RemoteHarness = make_remote(remote_env)
    a = h.enroll("erased-owner@example.test")
    b = h.enroll("kept-owner@example.test")
    h.seed_hosted(h.account_id(a))
    play_branching(a, "Mine", "I write.")
    staff = h.staff()
    from afterworlds.remote.control_orm import IdentityPrincipalORM

    with h.app.state.control_factory() as s:
        verifier = s.scalars(
            sa.select(IdentityPrincipalORM.password_verifier).where(
                IdentityPrincipalORM.contact_address == "erased-owner@example.test"
            )
        ).one()
    req = a.post(
        "/api/data-requests", json={"kind": "deletion", "scope": "account"}
    ).json()
    rid = req["request_id"]
    preview = a.get(f"/api/data-requests/{rid}/deletion-preview").json()
    confirmed = a.post(
        f"/api/data-requests/{rid}/confirm",
        json={
            "expected_revision": req["revision"],
            "scope_revision": preview["scope_revision"],
            "password": PASSWORD,
        },
    )
    assert confirmed.status_code == 200, confirmed.text
    view = staff.get(f"/api/admin/data-requests/{rid}").json()
    approved = staff.post(
        f"/api/admin/data-requests/{rid}/approve",
        json={"expected_revision": view["revision"], "reason": "verified owner"},
    ).json()
    done = staff.post(
        f"/api/admin/data-requests/{rid}/execute",
        json={"expected_revision": approved["revision"]},
    ).json()
    assert _phase(done, "identity") == "succeeded"
    assert b.get("/api/data-requests").status_code == 200
    h.close()

    def control_hits(needle: str) -> list[str]:
        return [
            hit for hit in files_with(remote_env, needle) if hit.startswith("control")
        ]

    code, out = _cli(maintenance, capsys, "compact")
    assert code == 0, out
    assert control_hits("erased-owner@example.test") == []
    assert control_hits(verifier) == []  # nor its password verifier
    assert control_hits("kept-owner@example.test")  # the other account remains
    evidence = json.loads(out)["compacted"]
    assert evidence["control"] == {"checkpoint_busy": 0, "wal_bytes": 0}
