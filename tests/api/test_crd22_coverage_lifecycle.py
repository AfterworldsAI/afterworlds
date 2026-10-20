"""Review of bd0ae1df (CRD Issue 22 #206): the fallback settlement-coverage
gap's whole lifecycle -- creation, supported restore, investigation/closure
and expiry -- through the production commands and app.

A gap is created only when the control store refuses a settlement-failure
record; it then lives in the content store until promoted into the control
store's anomaly streams (startup, sweep, restore boundary, enforce-restore).
"""

from __future__ import annotations

import threading
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
import sqlalchemy as sa
from sqlalchemy.exc import OperationalError

from afterworlds.operations import anomalies, maintenance
from afterworlds.operations.anomalies import GAP_KIND
from afterworlds.operations.orm import AnomalyEventORM
from afterworlds.operations.retention import sweep
from afterworlds.remote import storage_cli
from tests.api._remote import PASSWORD, RemoteHarness, make_remote, remote_settings
from tests.operations._data import play_branching


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
    monkeypatch.setattr(anomalies, "_UNRECORDED", threading.Event())
    return tmp_path


def _cli(
    module: Any, capsys: pytest.CaptureFixture[str], *argv: str
) -> tuple[int, str]:
    capsys.readouterr()
    code = module.main(list(argv))
    captured = capsys.readouterr()
    return code, (captured.out + captured.err).strip()


class _Refusing:
    def begin(self) -> Any:
        raise OperationalError("INSERT", {}, Exception("disk full"))


def _gap_via_turn(h: RemoteHarness, a: Any, story: str) -> None:
    """A delivered hosted turn whose settlement fails while the control
    store refuses the anomaly record: the production fallback path."""
    from afterworlds.api.routes import turns as turns_route
    from afterworlds.entitlement.errors import EntitlementSettlementError
    from afterworlds.entitlement.service import EntitlementService

    def fail(*_: Any, **__: Any) -> Any:
        raise EntitlementSettlementError("metrics missing")

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(EntitlementService, "settle_hosted_turn_cost", fail)
        mp.setattr(
            turns_route,
            "_settlement_sink",
            lambda request: anomalies.SettlementSink(
                _Refusing(),  # type: ignore[arg-type]
                request.app.state.session_factory,
            ),
        )
        turn = a.post(f"/api/stories/{story}/turns", json={"user_input": "Go on."})
    assert turn.status_code == 200, turn.text
    assert turn.json()["settlement_warning"]


def _content_gaps(h: RemoteHarness) -> int:
    with h.app.state.session_factory() as s:
        return len(
            list(
                s.scalars(
                    sa.select(AnomalyEventORM.event_id).where(
                        AnomalyEventORM.source_kind == GAP_KIND
                    )
                )
            )
        )


def _staff(h: RemoteHarness) -> Any:
    """One staff session per running app (sign-in happens once)."""
    if not hasattr(h, "_staff_client"):
        with h.app.state.control_factory() as s:
            known = s.execute(
                sa.text(
                    "SELECT 1 FROM identity_principals WHERE contact_address = "
                    "'owner@example.test'"
                )
            ).first()
        # After a restart the Owner is already enrolled.
        h._staff_client = h.staff(enroll=known is None)  # type: ignore[attr-defined]
    return h._staff_client  # type: ignore[attr-defined]


def _settlement_source(h: RemoteHarness) -> tuple[str, list[dict[str, Any]]]:
    report = _staff(h).get("/api/admin/anomalies").json()
    gaps = [x for x in report["anomalies"] if x["source_kind"] == GAP_KIND]
    return report["sources"]["settlement_failures"], gaps


def test_gap_survives_capture_fault_restore_enforce_verify(
    remote_env: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """P1: capture at E0 -> settlement + control anomaly write fail (no
    ledger event) -> restore E0 -> enforce -> verify -> fresh app: the gap
    is still reported and the source is degraded."""
    h = make_remote(remote_env)
    a = h.enroll("a@example.test")
    h.seed_hosted(h.account_id(a))
    story = play_branching(a, "Tale", "Warm up.")
    h.close()
    code, backup = _cli(storage_cli, capsys, "capture", "--to", str(remote_env / "b1"))
    assert code == 0, backup

    h = make_remote(remote_env)  # its startup finds nothing to promote yet
    a = h.client()
    signed_in = a.post(
        "/api/auth/sign-in",
        json={"contact_address": "a@example.test", "password": PASSWORD},
    )
    assert signed_in.status_code == 200, signed_in.text
    _gap_via_turn(h, a, story)
    assert _content_gaps(h) == 1  # only the content store holds it
    h.close()

    code, restore_id = _cli(storage_cli, capsys, "restore", "--backup-id", backup)
    assert code == 0, restore_id
    code, out = _cli(maintenance, capsys, "enforce-restore")
    assert code == 0, out
    assert _cli(storage_cli, capsys, "verify-restore", "--restore-id", restore_id) == (
        0,
        "verified",
    )

    h = make_remote(remote_env)
    try:
        assert _content_gaps(h) == 0  # the restored snapshot never had it
        source, gaps = _settlement_source(h)
        assert source == "degraded"
        assert len(gaps) == 1 and gaps[0]["subject_ref"] is None
    finally:
        h.close()


def test_closure_and_expiry_share_one_lifecycle(remote_env: Path) -> None:
    """P2: a closed gap expires with its notes 24 months after closure and
    never reopens -- not after a restart, nor from a restored copy."""
    h = make_remote(remote_env)
    a = h.enroll("a@example.test")
    h.seed_hosted(h.account_id(a))
    story = play_branching(a, "Tale", "Warm up.")
    _gap_via_turn(h, a, story)
    with h.app.state.session_factory() as s:
        copy = s.scalars(
            sa.select(AnomalyEventORM).where(AnomalyEventORM.source_kind == GAP_KIND)
        ).one()
        restored_copy = {
            c.name: getattr(copy, c.name)
            for c in AnomalyEventORM.__table__.columns
            if c.name != "event_order"
        }
    h.close()

    h = make_remote(remote_env)  # startup promotes the gap
    try:
        assert _content_gaps(h) == 0
        source, (gap,) = _settlement_source(h)
        assert source == "degraded"
        staff = _staff(h)
        closed = staff.post(
            f"/api/admin/anomalies/{gap['anomaly_id']}/notes",
            json={"state": "closed", "note_code": "resolved"},
        )
        assert closed.status_code == 200, closed.text
        assert _settlement_source(h)[0] == "available"  # closed by staff
        control = h.app.state.control_factory
        content = h.app.state.session_factory
        closed_at = datetime.now(UTC)

        just_before = closed_at + timedelta(days=730) - timedelta(days=3)
        sweep(ops=control, content=content, control=control, now=just_before)
        with control() as s:
            assert s.scalars(
                sa.select(AnomalyEventORM.event_id).where(
                    AnomalyEventORM.anomaly_id == gap["anomaly_id"]
                )
            ).all()  # closed, not yet expired: history kept

        after = closed_at + timedelta(days=740)
        result = sweep(ops=control, content=content, control=control, now=after)
        assert result.anomalies_expired >= 1
        with control() as s:
            assert not s.scalars(
                sa.select(AnomalyEventORM.event_id).where(
                    AnomalyEventORM.anomaly_id == gap["anomaly_id"]
                )
            ).all()  # source event and notes went together

        # A restored content snapshot brings the old copy back.
        with content.begin() as s:
            s.add(AnomalyEventORM(**restored_copy))
        sweep(ops=control, content=content, control=control, now=after)
        assert _content_gaps(h) == 0
        with control() as s:
            assert not s.scalars(
                sa.select(AnomalyEventORM.event_id).where(
                    AnomalyEventORM.source_kind == GAP_KIND
                )
            ).all()  # not resurrected
    finally:
        h.close()

    h = make_remote(remote_env)  # restart
    try:
        assert _settlement_source(h) == ("available", [])
    finally:
        h.close()


@pytest.mark.parametrize(
    ("investigated", "age_days", "expired"),
    [
        (False, 29, False),
        (False, 30, True),
        (True, 800, False),  # investigating, never closed: kept
    ],
)
def test_gap_clocks_follow_the_anomaly_record_class(
    remote_env: Path, investigated: bool, age_days: int, expired: bool
) -> None:
    h = make_remote(remote_env)
    try:
        a = h.enroll("a@example.test")
        h.seed_hosted(h.account_id(a))
        story = play_branching(a, "Tale", "Warm up.")
        _gap_via_turn(h, a, story)
        control = h.app.state.control_factory
        content = h.app.state.session_factory
        now = datetime.now(UTC)
        sweep(ops=control, content=content, control=control, now=now)  # promotes
        (gap,) = _settlement_source(h)[1]
        if investigated:
            noted = _staff(h).post(
                f"/api/admin/anomalies/{gap['anomaly_id']}/notes",
                json={"state": "investigating", "note_code": "investigating"},
            )
            assert noted.status_code == 200, noted.text
        later = now + timedelta(days=age_days, seconds=5)
        sweep(ops=control, content=content, control=control, now=later)
        with control() as s:
            left = s.scalars(
                sa.select(AnomalyEventORM.event_id).where(
                    AnomalyEventORM.anomaly_id == gap["anomaly_id"]
                )
            ).all()
        assert (not left) is expired
        assert _settlement_source(h)[0] == ("available" if expired else "degraded")
    finally:
        h.close()
