"""Prerequisite #205 §4: the operator storage runbook commands end to end.

capture -> (suppression recorded) -> restore -> the app refuses to serve ->
verify-restore fails while the suppressed Story is present -> enforcement
fixture deletes it -> verify-restore passes -> the app serves again.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from afterworlds.api.app import create_app
from afterworlds.persistence.crud.story import delete_story
from afterworlds.persistence.database import create_engine, create_session_factory
from afterworlds.remote import storage_cli
from afterworlds.remote.control_store import open_control_store
from afterworlds.remote.storage import (
    SNAPSHOT_CONTENT_FILE,
    StoreRefused,
    record_suppression,
)
from tests.api._remote import make_remote, remote_settings


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


def _run(capsys: pytest.CaptureFixture[str], *argv: str) -> tuple[int, str]:
    code = storage_cli.main(list(argv))
    return code, capsys.readouterr().out.strip()


def test_capture_restore_verify_runbook(
    remote_env: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    h = make_remote(remote_env)
    a = h.enroll("a@example.test")
    story = a.post("/api/stories", json={"title": "S", "mode": "branching"}).json()[
        "story_id"
    ]
    account = h.account_id(a)
    # Maintenance commands refuse to run while the app serves the store.
    with pytest.raises(StoreRefused, match="another process"):
        storage_cli.main(["capture", "--to", str(remote_env / "never")])
    h.close()

    code, backup_id = _run(capsys, "capture", "--to", str(remote_env / "b1"))
    assert code == 0 and uuid.UUID(backup_id)
    control = open_control_store(f"sqlite:///{remote_env / 'control.db'}")
    record_suppression(
        control,
        subject_ref=account,
        story_refs=[story],
        request_id=str(uuid.uuid4()),
        scope="story",
        effective_boundary_at=datetime.now(UTC),
        now=datetime.now(UTC),
    )

    code, restore_id = _run(capsys, "restore", "--backup-id", backup_id)
    assert code == 0
    with pytest.raises(StoreRefused, match="awaiting"):
        create_app(remote_settings(remote_env))
    code, out = _run(capsys, "verify-restore", "--restore-id", restore_id)
    assert code == 2 and story in out

    # Enforcement fixture standing in for CRD Issue 22's deletion.
    engine = create_engine(f"sqlite:///{remote_env / 'content.db'}")
    with create_session_factory(engine).begin() as s:
        delete_story(s, uuid.UUID(story))
    engine.dispose()
    assert _run(capsys, "verify-restore", "--restore-id", restore_id) == (0, "verified")
    assert _run(capsys, "due") == (0, "")
    assert _run(capsys, "dispose", "--backup-id", backup_id) == (0, "disposed")
    assert not (remote_env / "b1").exists()
    assert _run(capsys, "dispose", "--backup-id", str(uuid.uuid4()))[0] == 1
    assert _run(capsys, "restore", "--backup-id", str(uuid.uuid4()))[0] == 1

    served = make_remote(remote_env)
    try:
        signed_in = served.client().post(
            "/api/auth/sign-in",
            json={
                "contact_address": "a@example.test",
                "password": "correct horse battery staple",  # pragma: allowlist secret
            },
        )
        assert signed_in.status_code == 200
    finally:
        served.close()


def test_storage_commands_require_a_remote_deployment(
    remote_env: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("AFTERWORLDS_DEPLOYMENT", "local")
    with pytest.raises(SystemExit):
        storage_cli.main(["due"])


def test_restore_refuses_to_rewind_the_entitlement_ledger(
    remote_env: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from afterworlds.entitlement.enums import EntitlementEventType
    from afterworlds.entitlement.payloads import ByokLicenseActivatedPayload
    from afterworlds.entitlement.service import EntitlementService

    h = make_remote(remote_env)
    account = h.account_id(h.enroll("a@example.test"))
    h.close()
    code, backup_id = _run(capsys, "capture", "--to", str(remote_env / "b1"))
    assert code == 0
    engine = create_engine(f"sqlite:///{remote_env / 'content.db'}")
    with create_session_factory(engine)() as session:
        EntitlementService(session).receive_entitlement_event(
            uuid.UUID(account),
            EntitlementEventType.BYOK_LICENSE_ACTIVATED,
            ByokLicenseActivatedPayload(purchased_at=datetime.now(UTC)),
        )
        session.commit()
    engine.dispose()
    before = (remote_env / "content.db").read_bytes()
    assert storage_cli.main(["restore", "--backup-id", backup_id]) == 1
    assert "discard 1 entitlement event" in capsys.readouterr().err
    # Nothing was copied and no restore is pending.
    assert (remote_env / "content.db").read_bytes() == before
    make_remote(remote_env).close()


def _inventory(remote_env: Path, backup_id: str) -> Any:
    from afterworlds.remote.control_orm import BackupInventoryORM

    control = open_control_store(f"sqlite:///{remote_env / 'control.db'}")
    with control() as s:
        return s.get(BackupInventoryORM, backup_id)


def _restore_status(remote_env: Path, restore_id: str) -> str:
    from afterworlds.remote.control_orm import RestoreRecordORM

    control = open_control_store(f"sqlite:///{remote_env / 'control.db'}")
    with control() as s:
        row = s.get(RestoreRecordORM, restore_id)
        assert row is not None
        return row.status


def test_capture_refuses_while_suppressed_content_remains(
    remote_env: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    h = make_remote(remote_env)
    a = h.enroll("a@example.test")
    story = a.post("/api/stories", json={"title": "S", "mode": "branching"}).json()[
        "story_id"
    ]
    account = h.account_id(a)
    h.close()
    record_suppression(
        open_control_store(f"sqlite:///{remote_env / 'control.db'}"),
        subject_ref=account,
        story_refs=[story],
        request_id=str(uuid.uuid4()),
        scope="story",
        effective_boundary_at=datetime.now(UTC),
        now=datetime.now(UTC),
    )
    assert storage_cli.main(["capture", "--to", str(remote_env / "b1")]) == 1
    assert "suppressed content is still present" in capsys.readouterr().err
    assert not (remote_env / "b1").exists()
    # Once enforced (fixture), a capture is proven clean of that suppression.
    engine = create_engine(f"sqlite:///{remote_env / 'content.db'}")
    with create_session_factory(engine).begin() as s:
        delete_story(s, uuid.UUID(story))
    engine.dispose()
    code, backup_id = _run(capsys, "capture", "--to", str(remote_env / "b2"))
    assert code == 0
    assert _inventory(remote_env, backup_id).clean_suppression_ids != "[]"


def test_an_interrupted_capture_stays_inventoried_and_unverified(
    remote_env: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from afterworlds.remote import storage

    make_remote(remote_env).close()

    def vector_copy_fails(*_a: object, **_k: object) -> None:
        raise OSError("disk full during vector copy")

    with pytest.MonkeyPatch.context() as mp, pytest.raises(OSError):
        mp.setattr(storage.shutil, "copytree", vector_copy_fails)
        storage_cli.main(["capture", "--to", str(remote_env / "b1")])
    # The SQL copy that did happen is inventoried with its original age.
    control = open_control_store(f"sqlite:///{remote_env / 'control.db'}")
    from afterworlds.remote.control_orm import BackupInventoryORM

    with control() as s:
        [row] = s.query(BackupInventoryORM).all()
        assert row.verification_status == "unverified"
        assert Path(row.storage_locator) == remote_env / "b1"
        assert (remote_env / "b1" / SNAPSHOT_CONTENT_FILE).exists()
        partial = row.backup_id
    # It can neither be restored nor counted as clean, and a retry works.
    assert storage_cli.main(["restore", "--backup-id", partial]) == 1
    assert "unverified" in capsys.readouterr().err
    code, retried = _run(capsys, "capture", "--to", str(remote_env / "b2"))
    assert code == 0 and _inventory(remote_env, retried).verification_status == (
        "verified"
    )
    # The partial copy is still disposable through the normal path.
    assert _run(capsys, "dispose", "--backup-id", partial) == (0, "disposed")


def test_an_interrupted_restore_keeps_serving_fenced_until_retried(
    remote_env: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from afterworlds.remote import storage

    make_remote(remote_env).close()
    code, backup_id = _run(capsys, "capture", "--to", str(remote_env / "b1"))
    assert code == 0

    def vector_copy_fails(*_a: object, **_k: object) -> None:
        raise OSError("vector copy interrupted")

    with pytest.MonkeyPatch.context() as mp, pytest.raises(OSError):
        mp.setattr(storage.shutil, "copytree", vector_copy_fails)
        storage_cli.main(["restore", "--backup-id", backup_id])
    control = open_control_store(f"sqlite:///{remote_env / 'control.db'}")
    from afterworlds.remote.storage import pending_restores

    [failed] = pending_restores(control)
    assert _restore_status(remote_env, failed) == "copying"
    with pytest.raises(StoreRefused, match="awaiting"):
        create_app(remote_settings(remote_env))
    # No suppression exists, yet the incomplete restore cannot be verified.
    assert storage_cli.main(["verify-restore", "--restore-id", failed]) == 1
    assert "copying" in capsys.readouterr().err
    code, restore_id = _run(capsys, "restore", "--backup-id", backup_id)
    assert code == 0
    assert _restore_status(remote_env, failed) == "superseded"
    assert _run(capsys, "verify-restore", "--restore-id", restore_id) == (
        0,
        "verified",
    )
    make_remote(remote_env).close()  # serves again


def test_dispose_is_retry_safe_and_never_guesses_absence(
    remote_env: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from afterworlds.remote import storage
    from afterworlds.remote.storage import register_backup

    make_remote(remote_env).close()
    code, backup_id = _run(capsys, "capture", "--to", str(remote_env / "b1"))
    assert code == 0

    def record_fails(*_a: object, **_k: object) -> None:
        raise RuntimeError("control store write lost")

    with pytest.MonkeyPatch.context() as mp, pytest.raises(RuntimeError):
        mp.setattr(storage, "dispose_backup", record_fails)
        storage_cli.main(["dispose", "--backup-id", backup_id])
    assert not (remote_env / "b1").exists()
    assert _inventory(remote_env, backup_id).disposed_at is None
    # Retry: the files are verifiably gone, so the disposal is recorded.
    assert _run(capsys, "dispose", "--backup-id", backup_id) == (0, "disposed")
    assert _inventory(remote_env, backup_id).disposed_at is not None

    unreachable = register_backup(
        open_control_store(f"sqlite:///{remote_env / 'control.db'}"),
        store_id="s",
        storage_locator=str(remote_env / "no-such-volume" / "b9"),
        original_capture_at=datetime.now(UTC),
    )
    assert storage_cli.main(["dispose", "--backup-id", unreachable]) == 1
    row = _inventory(remote_env, unreachable)
    assert row.disposed_at is None and row.verification_status == "inaccessible"


def test_capture_never_claims_an_existing_directory(
    remote_env: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from afterworlds.remote.control_orm import BackupInventoryORM

    make_remote(remote_env).close()
    existing = remote_env / "operator-files"
    existing.mkdir()
    (existing / "keep.txt").write_text("not a backup", encoding="utf-8")
    assert storage_cli.main(["capture", "--to", str(existing)]) == 1
    assert "already exists" in capsys.readouterr().err
    assert [p.name for p in existing.iterdir()] == ["keep.txt"]
    control = open_control_store(f"sqlite:///{remote_env / 'control.db'}")
    with control() as s:
        assert s.query(BackupInventoryORM).count() == 0  # nothing to dispose


def _disposition(remote_env: Path, suppression: str) -> Any:
    from afterworlds.remote.storage import backup_disposition

    control = open_control_store(f"sqlite:///{remote_env / 'control.db'}")
    return backup_disposition(control, suppression, now=datetime.now(UTC))


def test_proven_disposal_reconciles_failed_and_inaccessible_backups(
    remote_env: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Review R1: a verified disposal discharges the obligation of an
    interrupted or once-inaccessible backup; unverifiable storage never does."""
    from afterworlds.remote import storage
    from afterworlds.remote.storage import register_backup

    make_remote(remote_env).close()
    control = open_control_store(f"sqlite:///{remote_env / 'control.db'}")

    def vector_copy_fails(*_a: object, **_k: object) -> None:
        raise OSError("interrupted")

    with pytest.MonkeyPatch.context() as mp, pytest.raises(OSError):
        mp.setattr(storage.shutil, "copytree", vector_copy_fails)
        storage_cli.main(["capture", "--to", str(remote_env / "b1")])
    # Recorded after the capture, which therefore proved nothing about it.
    sup = record_suppression(
        control,
        subject_ref=str(uuid.uuid4()),
        story_refs=[str(uuid.uuid4())],  # no such content: capture is allowed
        request_id="r",
        scope="story",
        effective_boundary_at=datetime.now(UTC),
        now=datetime.now(UTC),
    )

    later = remote_env / "offline-volume" / "b2"
    lost = register_backup(
        control,
        store_id="s",
        storage_locator=str(later),
        original_capture_at=datetime.now(UTC),
        verification_status="unverified",
    )
    partial = _disposition(remote_env, sup).unverified_backup_ids
    assert lost in partial and len(partial) == 2
    [interrupted] = [b for b in partial if b != lost]
    original_age = _inventory(remote_env, interrupted).original_capture_at

    assert _run(capsys, "dispose", "--backup-id", interrupted) == (0, "disposed")
    assert storage_cli.main(["dispose", "--backup-id", lost]) == 1  # unverifiable
    capsys.readouterr()
    report = _disposition(remote_env, sup)
    assert report.unverified_backup_ids == (lost,) and not report.complete
    assert _inventory(remote_env, lost).verification_status == "inaccessible"
    # The volume comes back: the path is now verifiably absent.
    later.parent.mkdir()
    assert _run(capsys, "dispose", "--backup-id", lost) == (0, "disposed")
    report = _disposition(remote_env, sup)
    assert report.complete and report.pending_backup_ids == ()
    assert _inventory(remote_env, lost).disposal_evidence == "verified_absent"
    assert _inventory(remote_env, interrupted).disposal_evidence == "removed"
    assert _inventory(remote_env, interrupted).original_capture_at == original_age


def test_restore_cleanup_interrupted_before_rebind_is_retryable(
    remote_env: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Review R2: an interruption while clearing the vector store keeps the
    deployment marker, so the documented retry and verification work."""
    from afterworlds.remote import storage

    make_remote(remote_env).close()
    code, backup_id = _run(capsys, "capture", "--to", str(remote_env / "b1"))
    assert code == 0
    (remote_env / "chroma" / "segment-after-capture").mkdir()

    def cleanup_fails(*_a: object, **_k: object) -> None:
        raise OSError("interrupted while clearing the vector store")

    with pytest.MonkeyPatch.context() as mp, pytest.raises(OSError):
        mp.setattr(storage.shutil, "rmtree", cleanup_fails)
        storage_cli.main(["restore", "--backup-id", backup_id])
    assert (remote_env / "chroma" / "afterworlds-deployment.json").exists()
    with pytest.raises(StoreRefused, match="awaiting"):
        create_app(remote_settings(remote_env))
    code, restore_id = _run(capsys, "restore", "--backup-id", backup_id)
    assert code == 0
    assert _run(capsys, "verify-restore", "--restore-id", restore_id) == (
        0,
        "verified",
    )
    assert not (remote_env / "chroma" / "segment-after-capture").exists()
    make_remote(remote_env).close()


def test_maintenance_refuses_a_swapped_content_store_untouched(
    remote_env: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Review R3: deployment A's control and vector stores with another
    deployment's (or a local) content file are refused before any copy."""
    from afterworlds.api.config import ApiSettings

    make_remote(remote_env).close()
    code, backup_id = _run(capsys, "capture", "--to", str(remote_env / "b1"))
    assert code == 0
    # Deployment B: its own content/control/vectors, same content filename.
    other = remote_env / "other"
    other.mkdir()
    with pytest.MonkeyPatch.context() as mp:
        mp.setenv("AFTERWORLDS_RETRIEVAL_PERSIST_DIRECTORY", str(other / "chroma"))
        make_remote(other).close()
    # A local install's store, also named content.db.
    local = remote_env / "local"
    local.mkdir()
    with pytest.MonkeyPatch.context() as mp:
        mp.setenv("AFTERWORLDS_RETRIEVAL_PERSIST_DIRECTORY", str(local / "chroma"))
        app = create_app(
            ApiSettings(
                database_url=f"sqlite:///{local / 'content.db'}",
                frontend_dist_dir=local / "x",
            )
        )
        app.state.session_factory.kw["bind"].dispose()
    for foreign in (other / "content.db", local / "content.db"):
        before = foreign.read_bytes()
        monkeypatch.setenv("AFTERWORLDS_DATABASE_URL", f"sqlite:///{foreign}")
        for argv in (
            ["capture", "--to", str(remote_env / f"never-{foreign.parent.name}")],
            ["restore", "--backup-id", backup_id],
        ):
            with pytest.raises(StoreRefused, match="different deployment"):
                storage_cli.main(argv)
        assert foreign.read_bytes() == before
        assert not (remote_env / f"never-{foreign.parent.name}").exists()


def _ledger_rows(db: Path) -> list[tuple[int, str]]:
    import sqlite3
    from contextlib import closing

    with closing(sqlite3.connect(db)) as conn:
        return [
            (int(seq), str(eid))
            for seq, eid in conn.execute(
                "SELECT global_sequence, event_id FROM entitlement_event"
                " ORDER BY global_sequence"
            )
        ]


@pytest.mark.parametrize("failure", ["mid_copy", "before_swap"])
def test_an_interrupted_sql_replacement_never_leaves_a_partial_store(
    remote_env: Path,
    capsys: pytest.CaptureFixture[str],
    failure: str,
) -> None:
    """The live content path holds the old store or the full snapshot, so the
    documented retry runs and the restored ledger is exactly the snapshot's."""
    from afterworlds.remote import storage
    from tests.api.test_remote_isolation import _seed_hosted

    h = make_remote(remote_env)
    _seed_hosted(h, h.account_id(h.enroll("a@example.test")))
    h.close()
    code, backup_id = _run(capsys, "capture", "--to", str(remote_env / "b1"))
    assert code == 0
    snapshot_ledger = _ledger_rows(remote_env / "b1" / SNAPSHOT_CONTENT_FILE)
    live = remote_env / "content.db"
    assert _ledger_rows(live) == snapshot_ledger

    real_copyfile = storage.shutil.copyfile

    def partial_copy(src: Any, dst: Any) -> None:
        Path(dst).write_bytes(Path(src).read_bytes()[:4096])
        raise OSError("interrupted mid-copy")

    def no_swap(*_a: object, **_k: object) -> None:
        raise OSError("interrupted before the swap")

    with pytest.MonkeyPatch.context() as mp, pytest.raises(OSError):
        if failure == "mid_copy":
            mp.setattr(storage.shutil, "copyfile", partial_copy)
        else:
            mp.setattr(storage.os, "replace", no_swap)
        storage_cli.main(["restore", "--backup-id", backup_id])
    assert storage.shutil.copyfile is real_copyfile
    assert _ledger_rows(live) == snapshot_ledger  # never a partial live file
    with pytest.raises(StoreRefused, match="awaiting"):
        create_app(remote_settings(remote_env))
    code, restore_id = _run(capsys, "restore", "--backup-id", backup_id)
    assert code == 0
    assert _run(capsys, "verify-restore", "--restore-id", restore_id) == (
        0,
        "verified",
    )
    assert _ledger_rows(live) == snapshot_ledger
    make_remote(remote_env).close()


def test_backup_expiry_and_disposal_survive_a_damaged_live_store(
    remote_env: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    make_remote(remote_env).close()
    code, backup_id = _run(capsys, "capture", "--to", str(remote_env / "b1"))
    assert code == 0
    live = remote_env / "content.db"
    live.write_bytes(b"not a database any more")
    for suffix in ("-wal", "-shm"):
        (remote_env / f"content.db{suffix}").unlink(missing_ok=True)
    # Touching the live stores is refused, distinctly from a foreign store.
    with pytest.raises(StoreRefused, match="unreadable"):
        storage_cli.main(["capture", "--to", str(remote_env / "b2")])
    # Expiry and disposal of backup copies stay possible.
    assert _run(capsys, "due") == (0, "")
    assert _run(capsys, "dispose", "--backup-id", backup_id) == (0, "disposed")


def test_restore_copy_interrupted_keeps_the_marker_and_is_retryable(
    remote_env: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Review residue 2: the copy phase never rewrites the trusted marker, so
    an interruption mid-copy leaves a store the documented retry accepts."""
    import shutil as real_shutil

    from afterworlds.remote import storage

    make_remote(remote_env).close()
    code, backup_id = _run(capsys, "capture", "--to", str(remote_env / "b1"))
    assert code == 0
    marker = remote_env / "chroma" / "afterworlds-deployment.json"
    trusted = marker.read_bytes()
    copied: list[str] = []

    def copy_then_fail(src: Any, dst: Any, *a: Any, **k: Any) -> Any:
        copied.append(Path(dst).name)
        raise OSError("interrupted mid-copy")

    real_copytree = real_shutil.copytree

    def interrupted_copytree(src: Any, dst: Any, *args: Any, **kwargs: Any) -> Any:
        # shutil recurses through the module-level name, so subdirectories
        # come back here too; every file copy goes through copy_then_fail.
        kwargs["copy_function"] = copy_then_fail
        if len(args) >= 3:
            args = (*args[:2], copy_then_fail, *args[3:])
            kwargs.pop("copy_function")
        return real_copytree(src, dst, *args, **kwargs)

    with pytest.MonkeyPatch.context() as mp, pytest.raises(OSError):
        mp.setattr(storage.shutil, "copytree", interrupted_copytree)
        storage_cli.main(["restore", "--backup-id", backup_id])
    assert "afterworlds-deployment.json" not in copied  # never copied over
    assert marker.read_bytes() == trusted
    with pytest.raises(StoreRefused, match="awaiting"):
        create_app(remote_settings(remote_env))
    code, restore_id = _run(capsys, "restore", "--backup-id", backup_id)
    assert code == 0
    assert _run(capsys, "verify-restore", "--restore-id", restore_id) == (
        0,
        "verified",
    )
    assert marker.read_bytes() == trusted
    make_remote(remote_env).close()


def _inventory_row(remote_env: Path, backup_id: str) -> Any:
    from afterworlds.remote.control_orm import BackupInventoryORM

    control = open_control_store(f"sqlite:///{remote_env / 'control.db'}")
    with control() as s:
        return s.get(BackupInventoryORM, backup_id)


def test_a_stale_disposal_retry_never_removes_a_newer_backup(
    remote_env: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Review r4313719098: a disposal whose record was lost keeps its location
    until the retry records it; a later backup there is never touched."""
    from afterworlds.remote import storage
    from afterworlds.remote.storage import copy_backup

    make_remote(remote_env).close()
    b1 = remote_env / "b1"
    code, old = _run(capsys, "capture", "--to", str(b1))
    assert code == 0

    def record_fails(*_a: object, **_k: object) -> None:
        raise RuntimeError("control store write lost")

    with pytest.MonkeyPatch.context() as mp, pytest.raises(RuntimeError):
        mp.setattr(storage, "dispose_backup", record_fails)
        storage_cli.main(["dispose", "--backup-id", old])
    assert not b1.exists() and _inventory_row(remote_env, old).disposed_at is None

    # The location still belongs to the undisposed backup: no reuse.
    assert storage_cli.main(["capture", "--to", str(b1)]) == 1
    assert "still belongs to an undisposed backup" in capsys.readouterr().err
    assert not b1.exists()
    control = open_control_store(f"sqlite:///{remote_env / 'control.db'}")
    other = remote_env / "b0"
    code, source = _run(capsys, "capture", "--to", str(other))
    with pytest.raises(StoreRefused, match="undisposed"):
        copy_backup(control, source, storage_locator=str(b1))
    # Nor beneath it (the retry's rmtree would take it) or around it.
    assert storage_cli.main(["capture", "--to", str(b1 / "nested")]) == 1
    assert "undisposed backup" in capsys.readouterr().err
    assert not b1.exists()
    with pytest.raises(StoreRefused, match="undisposed"):
        copy_backup(control, source, storage_locator=str(other / "inner"))
    with pytest.raises(StoreRefused, match="undisposed"):
        copy_backup(control, source, storage_locator=str(remote_env))

    # The retry records the verified absence and releases the location.
    assert _run(capsys, "dispose", "--backup-id", old) == (0, "disposed")
    code, new = _run(capsys, "capture", "--to", str(b1))
    assert code == 0
    newer = sorted(p.name for p in b1.rglob("*"))
    # Repeating the terminal disposal acts on nothing.
    assert _run(capsys, "dispose", "--backup-id", old) == (0, "disposed")
    assert sorted(p.name for p in b1.rglob("*")) == newer
    assert _inventory_row(remote_env, new).disposed_at is None
    assert _inventory_row(remote_env, old).disposal_evidence == "verified_absent"


def test_locators_are_fixed_when_recorded(
    remote_env: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Review r4313719114: a relative locator recorded from A is never
    reinterpreted from B; canonical aliases are one location."""
    from afterworlds.remote.storage import copy_backup

    make_remote(remote_env).close()
    site_a, site_b = remote_env / "site_a", remote_env / "site_b"
    site_a.mkdir()
    (site_b / "rel-backup").mkdir(parents=True)
    sentinel = site_b / "rel-backup" / "sentinel.txt"
    sentinel.write_text("unrelated operator data", encoding="utf-8")

    monkeypatch.chdir(site_a)
    code, backup = _run(capsys, "capture", "--to", "rel-backup")
    assert code == 0
    assert (
        Path(_inventory_row(remote_env, backup).storage_locator)
        == (site_a / "rel-backup").resolve()
    )
    control = open_control_store(f"sqlite:///{remote_env / 'control.db'}")
    copy_id = copy_backup(control, backup, storage_locator="rel-copy")
    assert (
        Path(_inventory_row(remote_env, copy_id).storage_locator)
        == (site_a / "rel-copy").resolve()
    )
    # A canonical alias of an inventoried location is that location.
    with pytest.raises(StoreRefused, match="undisposed"):
        copy_backup(
            control,
            backup,
            storage_locator=str(site_b / ".." / "site_a" / "rel-backup"),
        )

    monkeypatch.chdir(site_b)
    code, restore_id = _run(capsys, "restore", "--backup-id", backup)
    assert code == 0, restore_id
    assert _run(capsys, "dispose", "--backup-id", backup) == (0, "disposed")
    assert not (site_a / "rel-backup").exists()
    assert sentinel.read_text(encoding="utf-8") == "unrelated operator data"


@pytest.mark.parametrize("alias", ["same_path", "hard_link"])
def test_aliased_control_and_content_stores_are_refused_before_any_effect(
    remote_env: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    alias: str,
) -> None:
    """Review r4313719122: a control store that is physically the content
    store is refused before it is opened or migrated, by every entry point."""
    import hashlib
    import os
    import sqlite3
    from contextlib import closing

    from afterworlds.api.config import ApiSettings
    from afterworlds.remote import rules_provisioning
    from afterworlds.remote.storage import acquire_store_lock, acquire_vector_lock
    from scripts import retrieval_backfill

    make_remote(remote_env).close()
    content = remote_env / "content.db"
    if alias == "same_path":
        control_url = f"sqlite:///{content}"
    else:
        os.link(content, remote_env / "alias.db")
        control_url = f"sqlite:///{remote_env / 'alias.db'}"
    monkeypatch.setenv("AFTERWORLDS_CONTROL_DATABASE_URL", control_url)

    def state() -> tuple[str, list[str]]:
        with closing(sqlite3.connect(content)) as db:
            tables = sorted(
                n
                for (n,) in db.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            )
        return hashlib.sha256(content.read_bytes()).hexdigest(), tables

    before = state()
    settings = ApiSettings(
        **{**remote_settings(remote_env).__dict__, "control_database_url": control_url}
    )
    with pytest.raises(StoreRefused, match="same database file"):
        create_app(settings)
    assert storage_cli.main(["due"]) == 1
    assert rules_provisioning.main([]) == 1
    with pytest.raises(SystemExit) as exc:
        retrieval_backfill.main(
            [
                "--story-id",
                str(uuid.uuid4()),
                "--mode",
                "delete",
                "--db-url",
                f"sqlite:///{content}",
                "--account-id",
                str(uuid.uuid4()),
            ]
        )
    assert exc.value.code == 3
    assert capsys.readouterr().err.count("same database file") == 3
    assert state() == before
    acquire_store_lock(f"sqlite:///{content}").close()
    acquire_vector_lock(remote_env / "chroma").close()


@pytest.mark.parametrize("spelling", ["direct", "alias"])
def test_capture_never_targets_the_live_vector_store(
    remote_env: Path, capsys: pytest.CaptureFixture[str], spelling: str
) -> None:
    """Review r4313982102: a target inside the live vector store is refused
    before anything is created, inventoried or copied."""
    from afterworlds.remote.control_orm import BackupInventoryORM

    make_remote(remote_env).close()
    vectors = remote_env / "chroma"
    target = (
        vectors / "snapshots" / "b1"
        if spelling == "direct"
        else remote_env / "elsewhere" / ".." / "chroma" / "b1"
    )
    before = sorted(str(p.relative_to(vectors)) for p in vectors.rglob("*"))
    assert storage_cli.main(["capture", "--to", str(target)]) == 1
    assert "overlaps the live vector store" in capsys.readouterr().err
    assert sorted(str(p.relative_to(vectors)) for p in vectors.rglob("*")) == before
    control = open_control_store(f"sqlite:///{remote_env / 'control.db'}")
    with control() as s:
        assert s.query(BackupInventoryORM).count() == 0
    # An ordinary separate target still captures.
    assert _run(capsys, "capture", "--to", str(remote_env / "b1"))[0] == 0


def _restore_statuses(remote_env: Path, restore_id: str | None = None) -> list[str]:
    from afterworlds.remote.control_orm import RestoreRecordORM

    control = open_control_store(f"sqlite:///{remote_env / 'control.db'}")
    with control() as s:
        rows = s.query(RestoreRecordORM).order_by(RestoreRecordORM.restored_at).all()
        return [r.status for r in rows if restore_id in (None, r.restore_id)]


def _interrupted_restore(
    capsys: pytest.CaptureFixture[str], backup: str, fault: str
) -> None:
    """A restore of *backup* interrupted while copying (status stays copying)."""
    from afterworlds.remote import storage

    def fails(*_a: object, **_k: object) -> None:
        raise OSError("interrupted restore")

    with pytest.MonkeyPatch.context() as mp, pytest.raises(OSError):
        if fault == "vector_copy":
            mp.setattr(storage.shutil, "copytree", fails)
        else:  # the copied-status commit is lost
            mp.setattr(storage, "mark_restore_copied", fails)
        storage_cli.main(["restore", "--backup-id", backup])
    capsys.readouterr()


@pytest.mark.parametrize("fault", ["vector_copy", "lost_copied_commit"])
def test_a_copying_restore_keeps_its_source_until_it_finishes(
    remote_env: Path, capsys: pytest.CaptureFixture[str], fault: str
) -> None:
    """Review r4314309653: neither disposal path removes the source of a
    restore still copying; once both stores are replaced, disposal works
    while the serving fence stays until verification."""
    from afterworlds.remote.storage import dispose_backup

    make_remote(remote_env).close()
    b1 = remote_env / "b1"
    code, backup = _run(capsys, "capture", "--to", str(b1))
    assert code == 0
    _interrupted_restore(capsys, backup, fault)
    assert _restore_statuses(remote_env) == ["copying"]
    files = sorted(str(p.relative_to(b1)) for p in b1.rglob("*"))

    assert storage_cli.main(["dispose", "--backup-id", backup]) == 1
    assert "still copying" in capsys.readouterr().err
    control = open_control_store(f"sqlite:///{remote_env / 'control.db'}")
    with pytest.raises(StoreRefused, match="still copying"):
        dispose_backup(control, backup, now=datetime.now(UTC), evidence="removed")
    assert sorted(str(p.relative_to(b1)) for p in b1.rglob("*")) == files
    assert _inventory_row(remote_env, backup).disposed_at is None

    # The pre-expiry retry still works from the protected source.
    code, restore_id = _run(capsys, "restore", "--backup-id", backup)
    assert code == 0
    assert _restore_statuses(remote_env, restore_id) == ["pending_enforcement"]
    assert _run(capsys, "dispose", "--backup-id", backup) == (0, "disposed")
    assert not b1.exists()
    with pytest.raises(StoreRefused, match="awaiting"):
        create_app(remote_settings(remote_env))  # fence until verification
    code, out = _run(capsys, "verify-restore", "--restore-id", restore_id)
    assert (code, out) == (0, "verified")
    make_remote(remote_env).close()


def test_only_the_current_copying_restore_protects_a_source(
    remote_env: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    make_remote(remote_env).close()
    code, first = _run(capsys, "capture", "--to", str(remote_env / "b1"))
    code, second = _run(capsys, "capture", "--to", str(remote_env / "b2"))
    # Retrying the same source supersedes the old attempt; the new one
    # still protects it.
    _interrupted_restore(capsys, first, "vector_copy")
    _interrupted_restore(capsys, first, "vector_copy")
    assert _restore_statuses(remote_env) == ["superseded", "copying"]
    assert storage_cli.main(["dispose", "--backup-id", first]) == 1
    capsys.readouterr()
    # A restore from another backup supersedes it: the first is free again.
    _interrupted_restore(capsys, second, "vector_copy")
    assert _restore_statuses(remote_env) == ["superseded", "superseded", "copying"]
    assert _run(capsys, "dispose", "--backup-id", first) == (0, "disposed")
    assert storage_cli.main(["dispose", "--backup-id", second]) == 1


def _copying_source(
    remote_env: Path,
    capsys: pytest.CaptureFixture[str],
    *,
    clean_horizon_days: int | None = None,
    affected_horizon_days: int | None = None,
) -> tuple[Any, str, datetime | None]:
    """A backup whose restore is stuck copying. Optionally an active
    suppression recorded before capture (the backup is proven clean of it)
    and/or one recorded after (affected); each horizon is that many days
    after now. Returns (control, backup, affected horizon)."""
    from datetime import timedelta

    from afterworlds.remote.storage import DELETION_BACKUP_DEADLINE

    make_remote(remote_env).close()
    control = open_control_store(f"sqlite:///{remote_env / 'control.db'}")

    def suppress(horizon_days: int) -> datetime:
        now = datetime.now(UTC)
        boundary = now + timedelta(days=horizon_days) - DELETION_BACKUP_DEADLINE
        sup = record_suppression(
            control,
            subject_ref=str(uuid.uuid4()),
            story_refs=[str(uuid.uuid4())],  # no such content: capture allowed
            request_id=str(uuid.uuid4()),
            scope="story",
            effective_boundary_at=boundary,
            now=now,
        )
        return datetime.fromisoformat(_suppression_horizon(control, sup))

    if clean_horizon_days is not None:
        suppress(clean_horizon_days)
    code, backup = _run(capsys, "capture", "--to", str(remote_env / "b1"))
    assert code == 0
    horizon = (
        suppress(affected_horizon_days) if affected_horizon_days is not None else None
    )
    _interrupted_restore(capsys, backup, "lost_copied_commit")
    return control, backup, horizon


def _suppression_horizon(control: Any, suppression_id: str) -> str:
    from afterworlds.remote.control_orm import DeletionSuppressionORM

    with control() as s:
        row = s.get(DeletionSuppressionORM, suppression_id)
        assert row is not None
        return str(row.backup_horizon_at)


def _disposal_boundary(
    remote_env: Path, control: Any, backup: str, deadline: datetime
) -> None:
    """Refused an instant before *deadline*; ordinary disposal exactly at it,
    with the restore still copying and the app still fenced."""
    from datetime import timedelta

    from afterworlds.remote.storage import dispose_snapshot

    row = _inventory_row(remote_env, backup)
    clocks = (row.original_capture_at, row.expires_at)
    with pytest.raises(StoreRefused, match="still copying"):
        dispose_snapshot(control, backup, now=deadline - timedelta(microseconds=1))
    assert (remote_env / "b1").exists()
    dispose_snapshot(control, backup, now=deadline)
    row = _inventory_row(remote_env, backup)
    assert row.disposal_evidence == "removed" and not (remote_env / "b1").exists()
    assert (row.original_capture_at, row.expires_at) == clocks
    assert _restore_statuses(remote_env) == ["copying"]  # not completed or cancelled
    with pytest.raises(StoreRefused, match="awaiting"):
        create_app(remote_settings(remote_env))


def test_a_copying_source_is_disposable_at_its_21_day_expiry(
    remote_env: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from afterworlds.remote.storage import begin_restore, due_backups

    control, backup, _ = _copying_source(remote_env, capsys)
    expires = datetime.fromisoformat(_inventory_row(remote_env, backup).expires_at)
    assert backup in due_backups(control, now=expires)  # 21-day rule unchanged
    with pytest.raises(StoreRefused, match="21-day"):
        begin_restore(
            control, backup, live_database=remote_env / "content.db", now=expires
        )
    _disposal_boundary(remote_env, control, backup, expires)


def test_an_earlier_affected_30_day_horizon_is_the_deadline(
    remote_env: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from afterworlds.remote.storage import backup_disposition

    control, backup, horizon = _copying_source(
        remote_env, capsys, affected_horizon_days=5
    )
    assert horizon is not None
    assert horizon < datetime.fromisoformat(
        _inventory_row(remote_env, backup).expires_at
    )
    [sup] = [
        s
        for s in _active_suppression_ids(control)
        if _suppression_horizon(control, s) == horizon.isoformat()
    ]
    report = backup_disposition(control, sup, now=horizon)
    assert report.overdue and backup in report.pending_backup_ids  # 30-day rule
    _disposal_boundary(remote_env, control, backup, horizon)


def test_a_clean_backup_does_not_inherit_a_suppression_horizon(
    remote_env: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from afterworlds.remote.storage import dispose_snapshot

    control, backup, _ = _copying_source(remote_env, capsys, clean_horizon_days=5)
    [sup] = _active_suppression_ids(control)
    early = datetime.fromisoformat(_suppression_horizon(control, sup))
    # The backup proved that suppression's content absent: still protected.
    with pytest.raises(StoreRefused, match="still copying"):
        dispose_snapshot(control, backup, now=early)
    expires = datetime.fromisoformat(_inventory_row(remote_env, backup).expires_at)
    _disposal_boundary(remote_env, control, backup, expires)


def _active_suppression_ids(control: Any) -> list[str]:
    from afterworlds.remote.storage import active_suppressions

    return [s.suppression_id for s in active_suppressions(control)]


@pytest.mark.parametrize(
    "layout",
    ["vector_inside", "vector_alias", "vector_ancestor", "static_inside", "link_alias"],
)
def test_the_notice_store_must_be_separate_before_any_effect(
    remote_env: Path, layout: str
) -> None:
    """Review 5572565473 r4314625054: the outbox (raw codes) may not overlap
    the live vector store (backed up) or the public static root."""
    import os
    import subprocess

    from afterworlds.api.config import ApiSettings
    from afterworlds.remote.storage import acquire_store_lock, acquire_vector_lock

    settings = remote_settings(remote_env)
    vectors = remote_env / "chroma"
    static = remote_env / "no_frontend"
    if layout == "vector_inside":
        outbox = vectors / "outbox"
    elif layout == "vector_alias":
        outbox = remote_env / "elsewhere" / ".." / "chroma" / "notices"
    elif layout == "vector_ancestor":
        outbox = remote_env
    elif layout == "static_inside":
        outbox = static / "notices"
    else:
        vectors.mkdir()
        link = remote_env / "link"
        if os.name == "nt":  # a junction needs no symlink privilege
            subprocess.run(
                ["cmd", "/c", "mklink", "/J", str(link), str(vectors)],
                check=True,
                capture_output=True,
            )
        else:
            link.symlink_to(vectors, target_is_directory=True)
        outbox = link / "notices"
    unsafe = ApiSettings(**{**settings.__dict__, "notice_outbox_dir": outbox})
    with pytest.raises(StoreRefused, match="notice outbox"):
        create_app(unsafe)
    # Refused before any lock, migration or notice write.
    assert not (remote_env / "content.db").exists()
    assert not (remote_env / "control.db").exists()
    assert layout == "vector_ancestor" or not outbox.exists()
    acquire_store_lock(settings.database_url).close()
    acquire_vector_lock(vectors).close()
    # A disjoint layout works.
    make_remote(remote_env).close()


def test_maintenance_refuses_an_overlapping_notice_store(
    remote_env: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from afterworlds.remote.control_orm import BackupInventoryORM

    make_remote(remote_env).close()
    code, backup = _run(capsys, "capture", "--to", str(remote_env / "b1"))
    assert code == 0
    leaked = remote_env / "chroma" / "outbox"
    leaked.mkdir()
    marker = leaked / "recovery-1.json"
    marker.write_text('{"code": "zq5code"}', encoding="utf-8")
    monkeypatch.setenv("AFTERWORLDS_NOTICE_OUTBOX_DIR", str(leaked))
    for argv in (
        ["capture", "--to", str(remote_env / "b2")],
        ["restore", "--backup-id", backup],
    ):
        assert storage_cli.main(argv) == 1
        assert "notice outbox" in capsys.readouterr().err
    assert not (remote_env / "b2").exists()
    assert marker.read_text(encoding="utf-8") == '{"code": "zq5code"}'
    control = open_control_store(f"sqlite:///{remote_env / 'control.db'}")
    with control() as s:
        assert s.query(BackupInventoryORM).count() == 1


def _link_dir(link: Path, target: Path) -> None:
    import os
    import subprocess

    if os.name == "nt":  # a junction needs no symlink privilege
        subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(link), str(target)],
            check=True,
            capture_output=True,
        )
    else:
        link.symlink_to(target, target_is_directory=True)


def test_a_link_into_the_notice_store_is_never_copied(
    remote_env: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Residue: disjoint roots, but vector_dir/shortcut -> notice outbox.
    copytree follows links, so capture and restore refuse before copying."""
    from afterworlds.remote.control_orm import BackupInventoryORM, RestoreRecordORM

    make_remote(remote_env).close()
    code, backup = _run(capsys, "capture", "--to", str(remote_env / "b1"))
    assert code == 0
    outbox = remote_env / "outbox"
    outbox.mkdir(exist_ok=True)
    marker = outbox / "recovery-1.json"
    marker.write_text('{"code": "zq6code"}', encoding="utf-8")
    shortcut = remote_env / "chroma" / "deep" / "shortcut"
    shortcut.parent.mkdir()
    _link_dir(shortcut, outbox)

    assert storage_cli.main(["capture", "--to", str(remote_env / "b2")]) == 1
    assert "confidential store" in capsys.readouterr().err
    assert not (remote_env / "b2").exists()
    # A snapshot carrying such a link is not restored either.
    _link_dir(remote_env / "b1" / "chroma" / "shortcut", outbox)
    assert storage_cli.main(["restore", "--backup-id", backup]) == 1
    assert "confidential store" in capsys.readouterr().err
    assert marker.read_text(encoding="utf-8") == '{"code": "zq6code"}'
    control = open_control_store(f"sqlite:///{remote_env / 'control.db'}")
    with control() as s:
        assert s.query(BackupInventoryORM).count() == 1
        assert s.query(RestoreRecordORM).count() == 0
    # Without the link, a disjoint layout captures as usual.
    if shortcut.is_symlink():
        shortcut.unlink()
    else:
        os_rmdir(shortcut)
    assert _run(capsys, "capture", "--to", str(remote_env / "b2"))[0] == 0
    assert not list((remote_env / "b2").rglob("recovery-*.json"))


def os_rmdir(path: Path) -> None:
    import os

    os.rmdir(path)  # removes a junction without touching its target


# -- review 5573874599: the public static root holds no confidential store --


def _public(remote_env: Path, root: Path) -> Any:
    from afterworlds.api.config import ApiSettings

    return ApiSettings(
        **{**remote_settings(remote_env).__dict__, "frontend_dist_dir": root}
    )


@pytest.mark.parametrize(
    "layout", ["store_dir", "vector_dir", "control_dir", "alias", "link_alias"]
)
def test_startup_refuses_a_public_root_over_a_live_store(
    remote_env: Path, layout: str
) -> None:
    """r4315655748: refused before any store is created, migrated or served."""
    from afterworlds.api.config import ApiSettings
    from afterworlds.remote.storage import acquire_store_lock, acquire_vector_lock

    settings = remote_settings(remote_env)
    data = remote_env / "data"  # the content store's own directory
    data.mkdir()
    settings = ApiSettings(
        **{**settings.__dict__, "database_url": f"sqlite:///{data / 'content.db'}"}
    )
    if layout == "store_dir":  # holds content.db (and its journals)
        root = data
    elif layout == "vector_dir":
        root = remote_env / "chroma"
    elif layout == "control_dir":
        (remote_env / "ctl").mkdir()
        control = remote_env / "ctl" / "control.db"
        settings = ApiSettings(
            **{**settings.__dict__, "control_database_url": f"sqlite:///{control}"}
        )
        root = remote_env / "ctl"
    elif layout == "alias":
        root = remote_env / "elsewhere" / ".." / "data"
    else:
        root = remote_env / "link"
        _link_dir(root, data)
    unsafe = ApiSettings(**{**settings.__dict__, "frontend_dist_dir": root})
    with pytest.raises(StoreRefused, match="public static root"):
        create_app(unsafe)
    assert not (data / "content.db").exists()
    assert not (remote_env / "control.db").exists()
    assert not (remote_env / "ctl" / "control.db").exists()
    acquire_store_lock(settings.database_url).close()
    acquire_vector_lock(remote_env / "chroma").close()


def test_a_disjoint_public_root_still_serves_its_assets(remote_env: Path) -> None:
    from fastapi.testclient import TestClient

    dist = remote_env / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<p>afterworlds</p>", encoding="utf-8")
    app = create_app(_public(remote_env, dist))
    try:
        with TestClient(app, base_url="https://testserver") as client:
            assert "afterworlds" in client.get("/").text
            assert client.get("/content.db").status_code == 404
    finally:
        app.state.session_factory.kw["bind"].dispose()
        app.state.control_factory.kw["bind"].dispose()
        from chromadb.api.shared_system_client import SharedSystemClient

        SharedSystemClient.clear_system_cache()
        app.state.store_lock.close()
        app.state.vector_lock.close()
        if getattr(app.state, "control_lock", None) is not None:
            app.state.control_lock.close()


@pytest.mark.parametrize("spelling", ["inside", "alias", "around"])
def test_capture_never_targets_the_public_root(
    remote_env: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    spelling: str,
) -> None:
    """r4315655762: refused before the target, inventory or any copy."""
    from afterworlds.remote.control_orm import BackupInventoryORM

    make_remote(remote_env).close()
    site = remote_env / "site"
    dist = site / "dist"
    dist.mkdir(parents=True)
    monkeypatch.setenv("AFTERWORLDS_FRONTEND_DIST", str(dist))
    target = {
        "inside": dist / "b1",
        "alias": remote_env / "x" / ".." / "site" / "dist" / "b1",
        "around": site,  # the target would contain the public root
    }[spelling]
    before = sorted(p.name for p in site.rglob("*"))
    assert storage_cli.main(["capture", "--to", str(target)]) == 1
    assert "public static root" in capsys.readouterr().err
    assert sorted(p.name for p in site.rglob("*")) == before
    control = open_control_store(f"sqlite:///{remote_env / 'control.db'}")
    with control() as s:
        assert s.query(BackupInventoryORM).count() == 0


@pytest.mark.parametrize("status", ["verified", "unverified"])
def test_startup_refuses_a_public_root_exposing_an_undisposed_backup(
    remote_env: Path, capsys: pytest.CaptureFixture[str], status: str
) -> None:
    """Re-pointing the public root at an existing backup is refused before
    mounting, whatever the backup's verification; disposal frees it."""
    from afterworlds.remote.storage import register_backup

    make_remote(remote_env).close()
    site = remote_env / "site"
    site.mkdir()
    if status == "verified":
        code, backup = _run(capsys, "capture", "--to", str(site / "b1"))
        assert code == 0
    else:
        control = open_control_store(f"sqlite:///{remote_env / 'control.db'}")
        backup = register_backup(
            control,
            store_id="s",
            storage_locator=str(site / "b1"),
            original_capture_at=datetime.now(UTC),
            verification_status="unverified",
        )
    with pytest.raises(StoreRefused, match="undisposed backup"):
        create_app(_public(remote_env, site))
    # Cleanup stays possible despite the unsafe public configuration.
    import os

    os.environ["AFTERWORLDS_FRONTEND_DIST"] = str(site)
    try:
        assert _run(capsys, "dispose", "--backup-id", backup) == (0, "disposed")
    finally:
        os.environ["AFTERWORLDS_FRONTEND_DIST"] = str(remote_env / "no_frontend")
    make_remote(remote_env).close()  # disjoint again: serves
    app = create_app(_public(remote_env, site))  # disposed: reserves nothing
    app.state.session_factory.kw["bind"].dispose()
    app.state.control_factory.kw["bind"].dispose()
    from chromadb.api.shared_system_client import SharedSystemClient

    SharedSystemClient.clear_system_cache()
    app.state.store_lock.close()
    app.state.vector_lock.close()
    if getattr(app.state, "control_lock", None) is not None:
        app.state.control_lock.close()


def test_register_copy_and_restore_refuse_public_locations(
    remote_env: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from afterworlds.remote.control_orm import RestoreRecordORM
    from afterworlds.remote.storage import copy_backup, register_backup

    make_remote(remote_env).close()
    code, backup = _run(capsys, "capture", "--to", str(remote_env / "b1"))
    assert code == 0
    dist = remote_env / "dist"
    dist.mkdir()
    control = open_control_store(f"sqlite:///{remote_env / 'control.db'}")
    with pytest.raises(StoreRefused, match="public static root"):
        register_backup(
            control,
            store_id="s",
            storage_locator=str(dist / "b9"),
            original_capture_at=datetime.now(UTC),
            public_root=dist,
        )
    with pytest.raises(StoreRefused, match="public static root"):
        copy_backup(control, backup, storage_locator=str(dist / "c1"), public_root=dist)
    # A snapshot that is public (re-pointed root) is not restored.
    monkeypatch.setenv("AFTERWORLDS_FRONTEND_DIST", str(remote_env / "b1"))
    assert storage_cli.main(["restore", "--backup-id", backup]) == 1
    assert "public static root" in capsys.readouterr().err
    with control() as s:
        assert s.query(RestoreRecordORM).count() == 0
    # With a safe public root the same restore runs.
    monkeypatch.setenv("AFTERWORLDS_FRONTEND_DIST", str(dist))
    assert _run(capsys, "restore", "--backup-id", backup)[0] == 0


# -- review 5574610859: snapshot layout independent of the live basename ----


def test_a_content_store_named_chroma_captures_restores_and_verifies(
    remote_env: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """r4316274742: a live SQLite named ``chroma`` no longer collides with
    the snapshot's vector directory."""
    from afterworlds.api.config import ApiSettings
    from afterworlds.remote.storage import SNAPSHOT_VECTOR_DIR, read_vector_marker
    from tests.api._remote import RemoteHarness

    data = remote_env / "data"
    data.mkdir()
    url = f"sqlite:///{data / 'chroma'}"
    settings = ApiSettings(
        **{**remote_settings(remote_env).__dict__, "database_url": url}
    )
    monkeypatch.setenv("AFTERWORLDS_DATABASE_URL", url)
    RemoteHarness(
        app=create_app(settings), settings=settings, tmp_path=remote_env
    ).close()

    code, backup = _run(capsys, "capture", "--to", str(remote_env / "b1"))
    assert code == 0, backup
    row = _inventory_row(remote_env, backup)
    assert row.verification_status == "verified"
    snapshot = remote_env / "b1"
    assert (snapshot / SNAPSHOT_CONTENT_FILE).is_file()
    assert read_vector_marker(snapshot / SNAPSHOT_VECTOR_DIR) == row.store_id
    code, restore_id = _run(capsys, "restore", "--backup-id", backup)
    assert code == 0, restore_id
    assert _run(capsys, "verify-restore", "--restore-id", restore_id) == (0, "verified")
    RemoteHarness(
        app=create_app(settings), settings=settings, tmp_path=remote_env
    ).close()
    assert (
        _inventory_row(remote_env, backup).original_capture_at
        == row.original_capture_at
    )


def test_snapshots_in_the_earlier_layout_stay_restorable(
    remote_env: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A snapshot captured before the reserved name (SQL at the live
    basename) is still validated, ledger-checked and restored; a snapshot with
    no SQL file is refused before any restore state."""
    from afterworlds.remote.control_orm import RestoreRecordORM

    make_remote(remote_env).close()
    code, legacy = _run(capsys, "capture", "--to", str(remote_env / "b1"))
    code, missing = _run(capsys, "capture", "--to", str(remote_env / "b2"))
    (remote_env / "b1" / SNAPSHOT_CONTENT_FILE).rename(remote_env / "b1" / "content.db")
    (remote_env / "b2" / SNAPSHOT_CONTENT_FILE).unlink()

    assert storage_cli.main(["restore", "--backup-id", missing]) == 1
    assert "content snapshot is missing" in capsys.readouterr().err
    control = open_control_store(f"sqlite:///{remote_env / 'control.db'}")
    with control() as s:
        assert s.query(RestoreRecordORM).count() == 0
    code, restore_id = _run(capsys, "restore", "--backup-id", legacy)
    assert code == 0, restore_id
    assert _run(capsys, "verify-restore", "--restore-id", restore_id) == (0, "verified")
    make_remote(remote_env).close()


# -- review 5574902607: operational opening never migrates the control store -


def _control_schema(remote_env: Path, name: str = "control.db") -> tuple[Any, ...]:
    import sqlite3
    from contextlib import closing

    with closing(sqlite3.connect(remote_env / name)) as db:
        version = db.execute("SELECT version_num FROM alembic_version").fetchall()
        schema = db.execute(
            "SELECT name, sql FROM sqlite_master ORDER BY name"
        ).fetchall()
    return tuple(version), tuple(schema)


def _no_migration(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    from afterworlds.remote import control_store

    calls: list[str] = []

    def forbidden(url: str) -> None:
        calls.append(url)
        raise AssertionError("an operational path migrated the control store")

    monkeypatch.setattr(control_store, "upgrade_control_to_head", forbidden)
    return calls


def test_maintenance_beside_a_serving_app_never_migrates(
    remote_env: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import io

    from afterworlds.remote import bootstrap, rules_provisioning
    from afterworlds.remote.storage import acquire_store_lock
    from scripts import retrieval_backfill

    serving = make_remote(remote_env)
    try:
        owner = serving.enroll("owner@example.test")
        account = serving.account_id(owner)
        story = owner.post(
            "/api/stories", json={"title": "S", "mode": "branching"}
        ).json()["story_id"]
        before = _control_schema(remote_env)
        calls = _no_migration(monkeypatch)
        for argv in (
            ["capture", "--to", str(remote_env / "b1")],
            ["due"],
            ["dispose", "--backup-id", str(uuid.uuid4())],
        ):
            with pytest.raises(StoreRefused, match="another process"):
                storage_cli.main(argv)
        assert rules_provisioning.main([]) == 1
        with pytest.raises(SystemExit) as exc:
            retrieval_backfill.main(
                [
                    "--story-id",
                    story,
                    "--mode",
                    "delete",
                    "--db-url",
                    f"sqlite:///{remote_env / 'content.db'}",
                    "--account-id",
                    account,
                ]
            )
        assert exc.value.code == 3
        # The audited bootstrap and the direct scope guard work beside it.
        monkeypatch.setattr("sys.stdin", io.StringIO("correct horse battery staple\n"))
        assert (
            bootstrap.main(
                [
                    "--contact-address",
                    "owner@example.test",
                    "--control-db",
                    str(serving.settings.control_database_url),
                    "--password-stdin",
                ]
            )
            == 0
        )
        factory = serving.app.state.session_factory
        retrieval_backfill.remote_scope_check(
            factory, uuid.UUID(story), account, "backfill"
        )
        with pytest.raises(SystemExit):
            retrieval_backfill.remote_scope_check(
                factory, uuid.UUID(story), str(uuid.uuid4()), "backfill"
            )
        assert calls == []
        version, schema = _control_schema(remote_env)
        assert (version, schema) == before
        # The serving app's locks were never released by the refusals.
        with pytest.raises(StoreRefused, match="another process"):
            acquire_store_lock(serving.settings.database_url)
    finally:
        serving.close()


@pytest.mark.parametrize("state", ["missing", "older_revision"])
def test_operational_paths_refuse_a_missing_or_older_control_schema(
    remote_env: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    state: str,
) -> None:
    import io
    import sqlite3
    from contextlib import closing

    from afterworlds.remote import bootstrap, rules_provisioning
    from scripts import retrieval_backfill

    make_remote(remote_env).close()
    if state == "missing":
        url = f"sqlite:///{remote_env / 'absent' / 'control.db'}"
        monkeypatch.setenv("AFTERWORLDS_CONTROL_DATABASE_URL", url)
    else:
        url = f"sqlite:///{remote_env / 'control.db'}"
        with closing(sqlite3.connect(remote_env / "control.db")) as db, db:
            db.execute("UPDATE alembic_version SET version_num = 'c0000'")
    calls = _no_migration(monkeypatch)
    capsys.readouterr()
    assert storage_cli.main(["due"]) == 1
    assert storage_cli.main(["dispose", "--backup-id", str(uuid.uuid4())]) == 1
    assert rules_provisioning.main([]) == 1
    with pytest.raises(SystemExit) as exc:
        retrieval_backfill.main(
            [
                "--story-id",
                str(uuid.uuid4()),
                "--mode",
                "delete",
                "--db-url",
                f"sqlite:///{remote_env / 'content.db'}",
                "--account-id",
                str(uuid.uuid4()),
            ]
        )
    assert exc.value.code == 3
    monkeypatch.setattr("sys.stdin", io.StringIO("zq7marker-passphrase\n"))
    assert (
        bootstrap.main(
            [
                "--contact-address",
                "zq7marker@example.test",
                "--control-db",
                url,
                "--password-stdin",
            ]
        )
        == 2
    )
    err = capsys.readouterr().err
    assert "zq7marker" not in err and "Traceback" not in err
    assert calls == []
    if state == "missing":
        assert not (remote_env / "absent").exists()  # nothing was created
    else:
        assert _control_schema(remote_env)[0] == (("c0000",),)  # not upgraded


def test_fresh_startup_migrates_the_control_store_under_both_locks(
    remote_env: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from afterworlds.remote import control_store
    from afterworlds.remote.storage import acquire_store_lock, acquire_vector_lock

    real = control_store.upgrade_control_to_head
    held: list[bool] = []

    def while_locked(url: str) -> None:
        for acquire in (
            lambda: acquire_store_lock(f"sqlite:///{remote_env / 'content.db'}"),
            lambda: acquire_vector_lock(remote_env / "chroma"),
        ):
            with pytest.raises(StoreRefused, match="another process"):
                acquire()
        held.append(True)
        real(url)

    monkeypatch.setattr(control_store, "upgrade_control_to_head", while_locked)
    make_remote(remote_env).close()
    assert held == [True]


def test_a_control_store_recording_the_head_plus_another_revision_is_refused(
    remote_env: Path,
) -> None:
    """Residue 1: exactly the supported singleton head, not first-row
    equality; refused without touching the store."""
    import sqlite3
    from contextlib import closing

    from afterworlds.remote.control_store import (
        ControlStoreUnavailable,
        connect_control_store,
    )

    make_remote(remote_env).close()
    with closing(sqlite3.connect(remote_env / "control.db")) as db, db:
        db.execute("INSERT INTO alembic_version (version_num) VALUES ('zz_branch')")
    before = _control_schema(remote_env)
    with pytest.raises(ControlStoreUnavailable, match="not at this release"):
        connect_control_store(f"sqlite:///{remote_env / 'control.db'}")
    assert _control_schema(remote_env) == before


@pytest.mark.parametrize("authority", ["broken_scripts", "ambiguous_heads", "no_head"])
def test_unavailable_schema_authority_fails_typed_before_any_connection(
    remote_env: Path, monkeypatch: pytest.MonkeyPatch, authority: str
) -> None:
    """Residue 2: the supported head is resolved before an engine exists;
    broken, ambiguous or empty authority is ControlStoreUnavailable without
    repository paths, and no engine is created or kept."""
    from alembic.script import ScriptDirectory
    from alembic.util.exc import CommandError

    from afterworlds.remote import control_store

    make_remote(remote_env).close()
    if authority == "broken_scripts":
        monkeypatch.setattr(
            control_store, "CONTROL_MIGRATIONS", remote_env / "no-repo" / "control"
        )
    elif authority == "ambiguous_heads":

        def ambiguous(self: Any) -> str:
            raise CommandError("The script directory has multiple heads")

        monkeypatch.setattr(ScriptDirectory, "get_current_head", ambiguous)
    else:
        monkeypatch.setattr(ScriptDirectory, "get_current_head", lambda self: None)
    engines: list[Any] = []
    real_engine = control_store.create_engine
    monkeypatch.setattr(
        control_store,
        "create_engine",
        lambda url: engines.append(url) or real_engine(url),
    )
    with pytest.raises(control_store.ControlStoreUnavailable) as exc:
        control_store.connect_control_store(f"sqlite:///{remote_env / 'control.db'}")
    assert str(remote_env) not in str(exc.value)
    assert "no-repo" not in str(exc.value)
    assert engines == []  # nothing acquired, nothing left open


# -- review 5575284483: configured writer identity ----------------------------


@pytest.mark.parametrize("store", ["content", "control"])
def test_a_hard_linked_configured_store_is_refused_before_it_is_opened(
    remote_env: Path, capsys: pytest.CaptureFixture[str], store: str
) -> None:
    """r4316817796: a store file reachable under a second name could be
    served by a second writer with different pathname locks."""
    import hashlib
    import os

    from afterworlds.api.config import ApiSettings
    from afterworlds.remote.control_store import (
        ControlStoreUnavailable,
        connect_control_store,
    )
    from afterworlds.remote.storage import acquire_store_lock, acquire_vector_lock

    make_remote(remote_env).close()
    name = "content.db" if store == "content" else "control.db"
    os.link(remote_env / name, remote_env / f"alias-{name}")
    before = hashlib.sha256((remote_env / name).read_bytes()).hexdigest()
    settings = remote_settings(remote_env)
    key = "database_url" if store == "content" else "control_database_url"
    for target in (name, f"alias-{name}"):
        configured = ApiSettings(
            **{**settings.__dict__, key: f"sqlite:///{remote_env / target}"}
        )
        with pytest.raises(StoreRefused, match="more than one hard link"):
            create_app(configured)
    assert hashlib.sha256((remote_env / name).read_bytes()).hexdigest() == before
    acquire_store_lock(settings.database_url).close()
    acquire_vector_lock(remote_env / "chroma").close()
    if store == "control":
        with pytest.raises(ControlStoreUnavailable, match="hard link"):
            connect_control_store(f"sqlite:///{remote_env / name}")
        assert storage_cli.main(["due"]) == 1
    else:
        # Live-store maintenance refuses; cleanup that never opens it works.
        with pytest.raises(StoreRefused, match="hard link"):
            storage_cli.main(["capture", "--to", str(remote_env / "b1")])
        assert not (remote_env / "b1").exists()
        assert storage_cli.main(["due"]) == 0


@pytest.mark.parametrize("spelling", ["same_path", "canonical_alias"])
def test_a_second_deployment_sharing_the_control_store_is_refused(
    remote_env: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    spelling: str,
) -> None:
    """Sibling: a copied, validly marked content/vector pair configured with
    the serving app's control store gets no writer lease -- startup and
    maintenance refuse before any effect, releasing only their own locks."""
    import hashlib
    import shutil

    from afterworlds.api.config import ApiSettings
    from afterworlds.remote.storage import acquire_store_lock, acquire_vector_lock

    make_remote(remote_env).close()
    copy = remote_env / "copy"
    copy.mkdir()
    shutil.copyfile(remote_env / "content.db", copy / "content.db")
    shutil.copytree(
        remote_env / "chroma",
        copy / "chroma",
        ignore=shutil.ignore_patterns(".afterworlds-serve.lock"),
    )
    (remote_env / "elsewhere").mkdir()  # a traversable alias on every OS
    control = (
        remote_env / "control.db"
        if spelling == "same_path"
        else remote_env / "elsewhere" / ".." / "control.db"
    )
    serving = make_remote(remote_env)
    try:
        before = hashlib.sha256((copy / "content.db").read_bytes()).hexdigest()
        second = ApiSettings(
            **{
                **serving.settings.__dict__,
                "database_url": f"sqlite:///{copy / 'content.db'}",
                "control_database_url": f"sqlite:///{control}",
                "notice_outbox_dir": copy / "outbox",
            }
        )
        monkeypatch.setenv(
            "AFTERWORLDS_RETRIEVAL_PERSIST_DIRECTORY", str(copy / "chroma")
        )
        with pytest.raises(StoreRefused, match="control store"):
            create_app(second)
        monkeypatch.setenv("AFTERWORLDS_DATABASE_URL", second.database_url)
        monkeypatch.setenv("AFTERWORLDS_CONTROL_DATABASE_URL", f"sqlite:///{control}")
        with pytest.raises(StoreRefused, match="control store"):
            storage_cli.main(["capture", "--to", str(remote_env / "b1")])
        assert not (remote_env / "b1").exists()
        assert hashlib.sha256((copy / "content.db").read_bytes()).hexdigest() == before
        # The refused attempts released their own locks only.
        acquire_store_lock(second.database_url).close()
        acquire_vector_lock(copy / "chroma").close()
        with pytest.raises(StoreRefused, match="another process"):
            acquire_store_lock(serving.settings.database_url)
        serving.enroll("still-serving@example.test")
    finally:
        serving.close()
    # With the first owner gone the copied pair could start (supported layout
    # check aside), and the original deployment restarts normally.
    make_remote(remote_env).close()
