"""PR #208 review (CRD Issue 22 §5): an account export's archive and manifest
agree about the actual persisted read boundaries.

The content store is read in one transaction that also selects the
account's Stories; operational records are read in one operations-store
transaction taken after it. Proofs go through the production export seam
(staff approve/execute) and inspect the archive and manifest.
"""

from __future__ import annotations

import threading
import uuid
from typing import Any

import pytest

from afterworlds.entitlement.enums import EntitlementEventType
from afterworlds.entitlement.service import EntitlementService
from afterworlds.operations import export as export_module
from tests.api._remote import RemoteHarness
from tests.operations._data import play_branching, unzip


def _export(remote: RemoteHarness, a: Any, staff: Any) -> dict[str, Any]:
    req = a.post(
        "/api/data-requests", json={"kind": "export", "scope": "account"}
    ).json()
    rid = req["request_id"]
    view = staff.get(f"/api/admin/data-requests/{rid}").json()
    approved = staff.post(
        f"/api/admin/data-requests/{rid}/approve",
        json={"expected_revision": view["revision"], "reason": "verified owner"},
    ).json()
    done = staff.post(
        f"/api/admin/data-requests/{rid}/execute",
        json={"expected_revision": approved["revision"]},
    )
    assert done.status_code == 200, done.text
    assert done.json()["state"] == "completed", done.json()
    return unzip(a.get(f"/api/data-requests/{rid}/artifact").content)


def _adjust(staff: Any, account: str, delta: str = "5") -> dict[str, Any]:
    expected = staff.get(f"/api/admin/accounts/{account}").json()[
        "last_entitlement_event_id"
    ]
    resp = staff.post(
        f"/api/admin/accounts/{account}/credit-adjustments",
        json={
            "operation_id": str(uuid.uuid4()),
            "hosted_credit_delta": delta,
            "reason": "goodwill",
            "expected_last_entitlement_event_id": expected,
        },
    )
    return {"status": resp.status_code, "body": resp.json()}


def _in_thread(fn: Any) -> Any:
    """Run *fn* to completion on another thread (a concurrent request)."""
    out: dict[str, Any] = {}
    t = threading.Thread(target=lambda: out.__setitem__("v", fn()))
    t.start()
    t.join(60)
    assert not t.is_alive()
    return out["v"]


def _ops(files: dict[str, Any]) -> dict[str, Any]:
    return dict(files["account/operational_records.json"])


def test_story_created_at_snapshot_entry_is_in_membership_and_contents(
    remote: RemoteHarness, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Story membership is selected inside the content snapshot: a Story
    owned by the account when the snapshot is taken is exported, counted and
    named in the manifest (before the fix it was selected earlier)."""
    a = remote.enroll("a@example.test")
    remote.seed_hosted(remote.account_id(a))
    first = play_branching(a, "First", "I begin.")
    staff = remote.staff()
    real = export_module.build_archive
    created: list[str] = []

    def at_entry(*args: Any, **kwargs: Any) -> Any:
        created.append(_in_thread(lambda: play_branching(a, "Late", "I arrive.")))
        return real(*args, **kwargs)

    monkeypatch.setattr(export_module, "build_archive", at_entry)
    from afterworlds.operations import service as service_module

    monkeypatch.setattr(service_module, "build_archive", at_entry)
    files = _export(remote, a, staff)
    manifest = files["manifest.json"]
    assert set(manifest["snapshot_boundary"]["stories"]) == {first, *created}
    assert manifest["counts"]["stories"] == 2
    assert f"stories/{created[0]}/story.json" in files
    assert manifest["snapshot_boundary"]["content"] == {
        "store": "content",
        "read": "single_transaction",
    }
    assert manifest["snapshot_boundary"].get("read") != "single_transaction"


def test_adjustment_committed_at_snapshot_entry_is_in_ledger_and_support(
    remote: RemoteHarness, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An adjustment committed before the content snapshot appears in the
    exported ledger *and* in the support stream, linked to that ledger event
    (before the fix the support stream was read before the ledger)."""
    a = remote.enroll("a@example.test")
    account = remote.account_id(a)
    remote.seed_hosted(account)
    play_branching(a, "First", "I begin.")
    staff = remote.staff()
    real = export_module.build_archive
    adjusted: list[dict[str, Any]] = []

    def at_entry(*args: Any, **kwargs: Any) -> Any:
        adjusted.append(_in_thread(lambda: _adjust(staff, account)))
        return real(*args, **kwargs)

    from afterworlds.operations import service as service_module

    monkeypatch.setattr(service_module, "build_archive", at_entry)
    files = _export(remote, a, staff)
    (result,) = adjusted
    assert result["status"] == 200, result
    event_id = result["body"]["source_entitlement_event_id"]
    ledger = files["account/entitlement_history.json"]
    assert event_id in {e["event_id"] for e in ledger["events"]}
    actions = [
        x
        for x in _ops(files)["support_actions"]
        if x["operation_id"] == result["body"]["operation_id"]
    ]
    assert [x["outcome_code"] for x in actions] == ["requested", "committed"]
    assert {x["entitlement_event_in_export"] for x in actions} == {event_id}
    manifest = files["manifest.json"]
    assert manifest["counts"]["entitlement_events"] == len(ledger["events"])
    assert manifest["snapshot_boundary"]["entitlement_through_sequence"] == (
        ledger["events"][-1]["global_sequence"]
    )


def test_adjustment_after_the_content_snapshot_is_never_inferred(
    remote: RemoteHarness, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An adjustment that commits after the content snapshot was fixed is
    not in the exported ledger; its support records (read later) say so
    instead of claiming an exported effect, and the ledger, counts and
    boundary stay mutually consistent. A new request created meanwhile is
    within the operational boundary."""
    a = remote.enroll("a@example.test")
    account = remote.account_id(a)
    remote.seed_hosted(account)
    story = play_branching(a, "First", "I begin.")
    staff = remote.staff()
    real = export_module._entitlement_view
    late: dict[str, Any] = {}

    def mid_snapshot(session: Any, subject: Any) -> Any:
        ledger = real(session, subject)  # read inside the content snapshot
        late["adjusted"] = _in_thread(lambda: _adjust(staff, account))
        late["request"] = _in_thread(
            lambda: a.post(
                "/api/data-requests",
                json={"kind": "export", "scope": "story", "story_id": story},
            ).json()
        )
        return ledger

    monkeypatch.setattr(export_module, "_entitlement_view", mid_snapshot)
    files = _export(remote, a, staff)
    result = late["adjusted"]
    assert result["status"] == 200, result
    event_id = result["body"]["source_entitlement_event_id"]
    ledger = files["account/entitlement_history.json"]
    assert event_id not in {e["event_id"] for e in ledger["events"]}
    actions = [
        x
        for x in _ops(files)["support_actions"]
        if x["operation_id"] == result["body"]["operation_id"]
    ]
    assert [x["outcome_code"] for x in actions] == ["requested", "committed"]
    assert {x["entitlement_event_in_export"] for x in actions} == {None}
    manifest = files["manifest.json"]
    assert manifest["counts"]["entitlement_events"] == len(ledger["events"])
    operational = manifest["snapshot_boundary"]["operational"]
    assert operational["store"] == "control"
    assert operational["taken"] == "after_content_snapshot"
    requests = {r["request_id"] for r in _ops(files)["data_requests"]}
    assert late["request"]["request_id"] in requests
    assert manifest["counts"]["data_requests"] == len(requests)


def test_in_progress_adjustment_stays_visibly_in_progress(
    remote: RemoteHarness, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An adjustment paused before its effect while the export runs is
    exported as ``requested`` (in progress), source-linked by its operation
    ID, with no ledger event and no invented outcome."""
    a = remote.enroll("a@example.test")
    account = remote.account_id(a)
    remote.seed_hosted(account)
    play_branching(a, "First", "I begin.")
    staff = remote.staff()
    paused, go = threading.Event(), threading.Event()
    real = EntitlementService.receive_entitlement_event

    def hold(self: Any, subject: Any, kind: Any, *rest: Any, **kw: Any) -> Any:
        if kind is EntitlementEventType.MANUAL_CREDIT_ADJUSTMENT:
            paused.set()
            go.wait(30)
        return real(self, subject, kind, *rest, **kw)

    monkeypatch.setattr(EntitlementService, "receive_entitlement_event", hold)
    out: dict[str, Any] = {}
    adjusting = threading.Thread(
        target=lambda: out.__setitem__("r", _adjust(staff, account))
    )
    adjusting.start()
    try:
        assert paused.wait(10)
        files = _export(remote, a, staff)
    finally:
        go.set()
        adjusting.join(30)
    actions = _ops(files)["support_actions"]
    assert [x["outcome_code"] for x in actions] == ["requested"]
    assert actions[0]["entitlement_event_in_export"] is None
    assert out["r"]["status"] == 200  # the effect completed afterwards
