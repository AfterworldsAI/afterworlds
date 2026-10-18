"""Prerequisite #205 §4: the operator storage runbook commands end to end.

capture -> (suppression recorded) -> restore -> the app refuses to serve ->
verify-restore fails while the suppressed Story is present -> enforcement
fixture deletes it -> verify-restore passes -> the app serves again.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from pathlib import Path

import pytest

from afterworlds.api.app import create_app
from afterworlds.persistence.crud.story import delete_story
from afterworlds.persistence.database import create_engine, create_session_factory
from afterworlds.remote import storage_cli
from afterworlds.remote.control_store import open_control_store
from afterworlds.remote.storage import StoreRefused, record_suppression
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
