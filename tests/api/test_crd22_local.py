"""CRD Issue 22 local BYOK data operations: the local owner exports and
deletes Stories and all local data without any cloud account, sign-in or
upload; remote-only administration is unavailable locally."""

from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient

from afterworlds.api.app import create_app
from afterworlds.api.config import ApiSettings
from tests.operations._data import chunk_count, plant, play_branching, rows_with, unzip


@pytest.fixture()
def local(app_settings: ApiSettings, monkeypatch: pytest.MonkeyPatch) -> Any:
    monkeypatch.setenv("AFTERWORLDS_FAKE_PROVIDER", "1")
    app = create_app(app_settings)
    with TestClient(app) as c:
        yield app, c


def _seed_byok(app: Any) -> None:
    from datetime import UTC, datetime
    from decimal import Decimal

    from afterworlds.entitlement.enums import EntitlementEventType, HostedAccessPlan
    from afterworlds.entitlement.payloads import (
        HostedAccessActivatedPayload,
        SubscriptionCreditGrantPayload,
    )
    from afterworlds.entitlement.service import EntitlementService

    with app.state.session_factory() as s:
        service = EntitlementService(s)
        service.receive_entitlement_event(
            app.state.sojourner_id,
            EntitlementEventType.HOSTED_ACCESS_ACTIVATED,
            HostedAccessActivatedPayload(
                plan=HostedAccessPlan.SUBSCRIPTION, effective_at=datetime.now(UTC)
            ),
        )
        service.receive_entitlement_event(
            app.state.sojourner_id,
            EntitlementEventType.SUBSCRIPTION_CREDIT_GRANT,
            SubscriptionCreditGrantPayload(hosted_credit_delta=Decimal("100")),
        )


def _execute(c: TestClient, request: dict[str, Any]) -> dict[str, Any]:
    resp = c.post(
        f"/api/data-requests/{request['request_id']}/execute",
        json={"expected_revision": request["revision"]},
    )
    assert resp.status_code == 200, resp.text
    return dict(resp.json())


def test_local_export_and_deletion_need_no_cloud_account(local: Any) -> None:
    app, c = local
    _seed_byok(app)
    assert c.get("/api/auth/session").json()["signed_in"] is False
    s1 = play_branching(c, "Local one", "I light a lamp.")
    s2 = play_branching(c, "Local two", "I read.")
    plant(app.state.session_factory, s1, "LOCALMARK")

    exp = c.post(
        "/api/data-requests", json={"kind": "export", "scope": "account"}
    ).json()
    assert exp["environment"] == "local"
    done = _execute(c, exp)
    assert done["state"] == "completed"
    files = unzip(c.get(f"/api/data-requests/{exp['request_id']}/artifact").content)
    assert set(files["manifest.json"]["snapshot_boundary"]["stories"]) == {s1, s2}
    assert "LOCALMARK" not in str(files)

    req = c.post(
        "/api/data-requests",
        json={"kind": "deletion", "scope": "story", "story_id": s1},
    ).json()
    preview = c.get(f"/api/data-requests/{req['request_id']}/deletion-preview").json()
    confirmed = c.post(
        f"/api/data-requests/{req['request_id']}/confirm",
        json={"expected_revision": 1, "scope_revision": preview["scope_revision"]},
    ).json()["request"]
    done = _execute(c, confirmed)
    assert done["state"] == "completed", done
    phases = {p["phase_code"]: p["outcome_code"] for p in done["phases"]}
    assert phases["physical_compaction"] == "owner_controlled"
    assert phases["backups"] == "not_applicable"
    assert rows_with(app.state.session_factory, "LOCALMARK") == []
    assert chunk_count(s1) == 0 and chunk_count(s2) > 0
    assert c.get(f"/api/stories/{s1}").status_code == 404
    assert c.get(f"/api/stories/{s2}").status_code == 200
    # The earlier account export carried s1: its service-managed copy is gone.
    assert c.get(f"/api/data-requests/{exp['request_id']}/artifact").status_code == 404
    # Local BYOK settings and licence state are untouched.
    assert c.get("/api/account").status_code == 200
    # Remote-only administration does not exist locally.
    assert c.get("/api/admin/data-requests").status_code == 404


def test_local_account_wide_deletion_keeps_licence_state(local: Any) -> None:
    app, c = local
    _seed_byok(app)
    for i in range(2):
        play_branching(c, f"Tale {i}", "Go.")
    with app.state.session_factory() as s:
        before = s.execute(
            __import__("sqlalchemy").text("SELECT count(*) FROM entitlement_event")
        ).scalar()
    req = c.post(
        "/api/data-requests", json={"kind": "deletion", "scope": "account"}
    ).json()
    preview = c.get(f"/api/data-requests/{req['request_id']}/deletion-preview").json()
    assert preview["final_deletion_limit_days"] is None  # no service backups locally
    confirmed = c.post(
        f"/api/data-requests/{req['request_id']}/confirm",
        json={"expected_revision": 1, "scope_revision": preview["scope_revision"]},
    ).json()
    assert confirmed["receipt_credential"] is None  # no account to close
    done = _execute(c, confirmed["request"])
    assert done["state"] == "completed", done
    assert c.get("/api/stories").json()["stories"] == []
    with app.state.session_factory() as s:
        after = s.execute(
            __import__("sqlalchemy").text("SELECT count(*) FROM entitlement_event")
        ).scalar()
    assert after == before
    receipt = next(
        r for r in done["receipts"] if r["receipt_kind"] == "deletion_receipt"
    )
    assert receipt["body"]["environment"] == "local"
