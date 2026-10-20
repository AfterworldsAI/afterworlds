"""CRD Issue 22 §7: anomaly visibility from durable sources only, explicit
unavailability, expected states not flagged, notes append without repair,
and the settlement-warning boundary (turn stays delivered, no retry)."""

from __future__ import annotations

import uuid
from typing import Any

import sqlalchemy as sa

from afterworlds.entitlement.errors import EntitlementSettlementError
from afterworlds.entitlement.orm import EntitlementEvent
from afterworlds.entitlement.service import EntitlementService
from tests.api._remote import RemoteHarness
from tests.operations._data import play_branching


def _ids(report: dict[str, Any]) -> set[str]:
    return {a["signal_code"] for a in report["anomalies"]}


def test_settlement_failure_is_durable_and_never_repaired(
    remote: RemoteHarness, monkeypatch: Any
) -> None:
    a = remote.enroll("a@example.test")
    a_id = remote.account_id(a)
    remote.seed_hosted(a_id)
    staff = remote.staff()
    sid = play_branching(a, "Tale", "Warm up.")

    def fail(*_: Any, **__: Any) -> Any:
        raise EntitlementSettlementError("metrics missing")

    monkeypatch.setattr(EntitlementService, "settle_hosted_turn_cost", fail)
    with remote.app.state.session_factory() as s:
        before = s.scalar(sa.select(sa.func.count(EntitlementEvent.event_id)))
    resp = a.post(f"/api/stories/{sid}/turns", json={"user_input": "Go on."})
    body = resp.json()
    assert resp.status_code == 200 and body["disposition"] == "delivered"
    assert body["settlement_warning"]
    report = staff.get("/api/admin/anomalies").json()
    settlement = [
        a for a in report["anomalies"] if a["source_kind"] == "turn_settlement"
    ]
    assert len(settlement) == 1
    assert settlement[0]["source_id"] == body["turn_id"]
    assert settlement[0]["subject_ref"] == a_id
    # Negative/depleted balances are expected states, not anomalies.
    assert "negative_balance" not in _ids(report)
    assert report["sources"]["commercial_events"] == "not_integrated"
    noted = staff.post(
        f"/api/admin/anomalies/{settlement[0]['anomaly_id']}/notes",
        json={
            "state": "investigating",
            "note_code": "investigating",
            "note_text": "<b>x</b>",
        },
    )
    assert noted.status_code == 200
    assert noted.json()["investigation_state"] == "investigating"
    assert noted.json()["notes"][0]["note_text"] == "<b>x</b>"  # stored as text
    with remote.app.state.session_factory() as s:
        assert s.scalar(sa.select(sa.func.count(EntitlementEvent.event_id))) == before
    # The delivered turn stays delivered after reload.
    assert any(
        t["user_input"] == "Go on."
        for t in a.get(f"/api/stories/{sid}/turns").json()["turns"]
    )


def test_replay_mismatch_failed_requests_and_unavailable_sources(
    remote: RemoteHarness, monkeypatch: Any
) -> None:
    a = remote.enroll("a@example.test")
    a_id = remote.account_id(a)
    remote.seed_hosted(a_id)
    staff = remote.staff()
    engine = remote.app.state.session_factory.kw["bind"]
    with engine.begin() as conn:
        conn.execute(
            sa.text(
                "UPDATE runtime_entitlement_state SET hosted_credit_balance = 7"
                " WHERE sojourner_id = :s"
            ),
            {"s": uuid.UUID(a_id).hex},
        )
    report = staff.get("/api/admin/anomalies").json()
    assert "entitlement_replay_mismatch" in _ids(report)
    assert report["sources"]["entitlement_replay"] == "available"
    # The read repaired nothing.
    with engine.connect() as conn:
        assert (
            conn.scalar(
                sa.text("SELECT hosted_credit_balance FROM runtime_entitlement_state")
            )
            == 7
        )

    from afterworlds.operations import anomalies as module

    def down(*_: Any, **__: Any) -> Any:
        raise sa.exc.OperationalError("select", {}, Exception("disk"))

    monkeypatch.setattr(module, "subjects_with_events", down)
    report = staff.get("/api/admin/anomalies").json()
    assert report["sources"]["entitlement_replay"] == "unavailable"
    assert a.get("/api/admin/anomalies").status_code == 403
