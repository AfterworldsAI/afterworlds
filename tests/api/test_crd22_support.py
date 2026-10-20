"""CRD Issue 22 §1-§3: staff lookup, ordered history and controlled credit
remediation through the built remote app (real identity, bootstrap and
staff sessions; disposable stores)."""

from __future__ import annotations

import threading
import uuid
from decimal import Decimal
from typing import Any

import pytest
import sqlalchemy as sa
from sqlalchemy.exc import OperationalError

from afterworlds.entitlement.orm import EntitlementEvent
from afterworlds.operations.orm import SupportActionEventORM
from afterworlds.operations.support import SupportService
from tests.api._remote import RemoteHarness, make_remote


def _error(resp: Any) -> str:
    return str(resp.json()["error_code"])


def _events(remote: RemoteHarness, account_id: str) -> list[EntitlementEvent]:
    with remote.app.state.session_factory() as s:
        return list(
            s.scalars(
                sa.select(EntitlementEvent)
                .where(EntitlementEvent.sojourner_id == uuid.UUID(account_id))
                .order_by(EntitlementEvent.global_sequence)
            )
        )


def _adjust(
    staff: Any,
    account_id: str,
    *,
    op: str | None = None,
    hosted: str | None = "5",
    top_up: str | None = None,
    reason: str = "goodwill after outage",
    expected: str | None = "current",
) -> Any:
    if expected == "current":
        expected = staff.get(f"/api/admin/accounts/{account_id}").json()[
            "last_entitlement_event_id"
        ]
    return staff.post(
        f"/api/admin/accounts/{account_id}/credit-adjustments",
        json={
            "operation_id": op or str(uuid.uuid4()),
            "hosted_credit_delta": hosted,
            "top_up_credit_delta": top_up,
            "reason": reason,
            "expected_last_entitlement_event_id": expected,
        },
    )


@pytest.fixture()
def setup(remote: RemoteHarness) -> tuple[RemoteHarness, Any, Any, str]:
    b = remote.enroll("b@example.test")
    b_id = remote.account_id(b)
    staff = remote.staff()
    return remote, staff, b, b_id


class TestAuthority:
    ROUTES = (
        ("get", "/api/admin/accounts/{id}/entitlement-history", None),
        ("get", "/api/admin/accounts/{id}/support-actions", None),
        (
            "post",
            "/api/admin/accounts/{id}/credit-adjustments/preview",
            {"hosted_credit_delta": "1"},
        ),
        (
            "post",
            "/api/admin/accounts/{id}/credit-adjustments",
            {
                "operation_id": str(uuid.uuid4()),
                "hosted_credit_delta": "1",
                "reason": "x",
                "expected_last_entitlement_event_id": None,
            },
        ),
        ("get", f"/api/admin/support-operations/{uuid.uuid4()}", None),
    )

    def test_unauthenticated_and_ordinary_sessions_are_refused(
        self, setup: tuple[RemoteHarness, Any, Any, str]
    ) -> None:
        remote, _staff, b, b_id = setup
        owner_ordinary = remote.client()
        owner_ordinary.post(
            "/api/auth/sign-in",
            json={
                "contact_address": "owner@example.test",
                "password": "correct horse battery staple",  # pragma: allowlist secret
            },
        )
        anon = remote.client()
        for method, path, body in self.ROUTES:
            url = path.format(id=b_id)
            kwargs = {"json": body} if body else {}
            assert _error(getattr(anon, method)(url, **kwargs)) == (
                "authentication_required"
            )
            for ordinary in (b, owner_ordinary):
                resp = getattr(ordinary, method)(url, **kwargs)
                assert resp.status_code == 403, (url, resp.text)
                assert _error(resp) == "staff_authority_required"
        assert _events(remote, b_id) == []

    def test_unknown_target_is_404_and_writes_nothing(
        self, setup: tuple[RemoteHarness, Any, Any, str]
    ) -> None:
        remote, staff, _b, _ = setup
        ghost = str(uuid.uuid4())
        assert (
            staff.get(f"/api/admin/accounts/{ghost}/entitlement-history").status_code
            == 404
        )
        assert _adjust(staff, ghost, expected=None).status_code == 404
        with remote.app.state.control_factory() as s:
            assert (
                s.scalar(sa.select(sa.func.count(SupportActionEventORM.event_id))) == 0
            )


class TestLookupAndHistory:
    def test_lookup_distinguishes_absent_from_zero_and_reports_replay(
        self, setup: tuple[RemoteHarness, Any, Any, str]
    ) -> None:
        remote, staff, _b, b_id = setup
        view = staff.get(f"/api/admin/accounts/{b_id}").json()
        assert view["entitlement_state"] == "absent"
        assert view["credits"]["total"] is None
        assert view["replay"]["status"] == "absent"
        assert view["byok_readiness_source"] == "unavailable_remotely"
        remote.seed_hosted(b_id, credits="0.5")
        view = staff.get(f"/api/admin/accounts/{b_id}").json()
        assert view["entitlement_state"] == "present"
        assert view["hosted_plan"] == "subscription"
        assert view["credits"]["included"] == "0.5000"
        assert view["replay"]["status"] == "consistent"
        assert "b@example.test" not in str(view)

    def test_history_pages_in_global_sequence_without_gaps_or_repeats(
        self, setup: tuple[RemoteHarness, Any, Any, str]
    ) -> None:
        remote, staff, _b, b_id = setup
        other = remote.account_id(remote.enroll("c@example.test"))
        remote.seed_hosted(other)
        remote.seed_hosted(b_id)
        for _ in range(3):
            assert _adjust(staff, b_id).status_code == 200
        expected = [e.global_sequence for e in _events(remote, b_id)]
        seen: list[int] = []
        after = 0
        while True:
            page = staff.get(
                f"/api/admin/accounts/{b_id}/entitlement-history",
                params={"after_sequence": after, "limit": 2},
            ).json()
            assert page["order"] == "global_sequence_ascending"
            assert page["total_events"] == len(expected)
            seen += [e["global_sequence"] for e in page["events"]]
            if page["next_after_sequence"] is None:
                break
            after = page["next_after_sequence"]
        assert seen == expected == sorted(expected)
        manual = [
            e
            for e in staff.get(
                f"/api/admin/accounts/{b_id}/entitlement-history"
            ).json()["events"]
            if e["event_type"] == "manual_credit_adjustment"
        ]
        assert len(manual) == 3 and all(e["support_operation_id"] for e in manual)

    def test_unknown_version_and_mismatch_are_reported_not_repaired(
        self, setup: tuple[RemoteHarness, Any, Any, str]
    ) -> None:
        remote, staff, _b, b_id = setup
        remote.seed_hosted(b_id)
        engine = remote.app.state.session_factory.kw["bind"]
        with engine.begin() as conn:
            conn.execute(
                sa.text(
                    "INSERT INTO entitlement_event (event_id, sojourner_id, event_type,"
                    " payload_json, created_at) VALUES (:e, :s,"
                    " 'top_up_credit_grant', '{\"schema_version\": 2}',"
                    " '2026-01-01 00:00:00')"
                ),
                {"e": uuid.uuid4().hex, "s": uuid.UUID(b_id).hex},
            )
        before = _events(remote, b_id)
        page = staff.get(f"/api/admin/accounts/{b_id}/entitlement-history").json()
        assert page["replay"]["status"] == "unreadable"
        assert page["replay"]["detail_code"] == "unsupported_schema_version"
        assert page["events"][-1]["parse_error"] == "unsupported_schema_version"
        assert len(_events(remote, b_id)) == len(before)


class TestCreditAdjustment:
    def test_preview_then_commit_with_provenance(
        self, setup: tuple[RemoteHarness, Any, Any, str]
    ) -> None:
        remote, staff, _b, b_id = setup
        remote.seed_hosted(b_id, credits="10")
        preview = staff.post(
            f"/api/admin/accounts/{b_id}/credit-adjustments/preview",
            json={"hosted_credit_delta": "-2.5", "top_up_credit_delta": "1.0001"},
        ).json()
        assert preview["resulting_included"] == "7.5000"
        assert preview["resulting_top_up"] == "1.0001"
        assert preview["refusal_code"] is None
        resp = _adjust(
            staff,
            b_id,
            hosted="-2.5",
            top_up="1.0001",
            expected=preview["last_entitlement_event_id"],
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["outcome_code"] == "committed"
        assert body["account"]["credits"]["included"] == "7.5000"
        event = _events(remote, b_id)[-1]
        assert str(event.event_id).replace("-", "") == body[
            "source_entitlement_event_id"
        ].replace("-", "")
        assert '"adjusted_by"' in event.payload_json
        history = staff.get(f"/api/admin/accounts/{b_id}/support-actions").json()
        assert [e["outcome_code"] for e in history["events"]] == [
            "requested",
            "committed",
        ]

    def test_identical_retry_applies_once_and_reuse_conflicts(
        self, setup: tuple[RemoteHarness, Any, Any, str]
    ) -> None:
        remote, staff, _b, b_id = setup
        remote.seed_hosted(b_id, credits="10")
        op = str(uuid.uuid4())
        expected = staff.get(f"/api/admin/accounts/{b_id}").json()[
            "last_entitlement_event_id"
        ]
        first = _adjust(staff, b_id, op=op, expected=expected)
        again = _adjust(staff, b_id, op=op, expected=expected)
        assert first.status_code == again.status_code == 200
        assert (
            first.json()["source_entitlement_event_id"]
            == again.json()["source_entitlement_event_id"]
        )
        assert again.json()["account"]["credits"]["included"] == "15.0000"
        other = remote.account_id(remote.enroll("c@example.test"))
        remote.seed_hosted(other)
        for changed in (
            {"hosted": "6"},
            {"reason": "a different reason"},
        ):
            assert _error(_adjust(staff, b_id, op=op, **changed)) == "operation_conflict"  # type: ignore[arg-type]
        assert _error(_adjust(staff, other, op=op)) == "operation_conflict"
        assert len(_events(remote, b_id)) == 3

    def test_stale_never_activated_and_precision_refusals_have_no_effect(
        self, setup: tuple[RemoteHarness, Any, Any, str]
    ) -> None:
        remote, staff, _b, b_id = setup
        resp = _adjust(staff, b_id, expected=None)
        assert _error(resp) == "operation_precondition_failed"
        assert resp.json()["detail"]["outcome_code"] == "rejected_precondition"
        assert _events(remote, b_id) == []
        remote.seed_hosted(b_id)
        assert _error(_adjust(staff, b_id, expected=None)) == "operation_stale"
        assert _error(_adjust(staff, b_id, hosted="1.00001")) == "validation_failed"
        assert _error(_adjust(staff, b_id, hosted="0")) == "validation_failed"
        for reason in ("   ", "line\x07bell"):
            assert _error(_adjust(staff, b_id, reason=reason)) == "validation_failed"
        assert len(_events(remote, b_id)) == 2

    def test_audit_failure_before_effect_prevents_it(
        self, setup: tuple[RemoteHarness, Any, Any, str], monkeypatch: Any
    ) -> None:
        remote, staff, _b, b_id = setup
        remote.seed_hosted(b_id)

        def refuse(*_: Any, **__: Any) -> Any:
            raise OperationalError("insert", {}, Exception("disk full"))

        monkeypatch.setattr(SupportService, "_row", refuse)
        resp = _adjust(staff, b_id)
        assert resp.status_code == 503 and "disk full" not in resp.text
        assert len(_events(remote, b_id)) == 2

    def test_lost_outcome_is_recovered_by_identity_across_restart(
        self,
        tmp_path: Any,
        monkeypatch: Any,
    ) -> None:
        monkeypatch.setenv(
            "AFTERWORLDS_RETRIEVAL_PERSIST_DIRECTORY", str(tmp_path / "chroma")
        )
        monkeypatch.setenv("AFTERWORLDS_FAKE_PROVIDER", "1")
        remote = make_remote(tmp_path)
        try:
            b_id = remote.account_id(remote.enroll("b@example.test"))
            staff = remote.staff()
            remote.seed_hosted(b_id, credits="10")
            op = str(uuid.uuid4())
            expected = staff.get(f"/api/admin/accounts/{b_id}").json()[
                "last_entitlement_event_id"
            ]
            real = SupportService._finish
            calls = {"n": 0}

            def lose(
                self: SupportService, requested: Any, outcome: str, src: Any
            ) -> Any:
                calls["n"] += 1
                if calls["n"] == 1:
                    raise OperationalError("insert", {}, Exception("lost"))
                return real(self, requested, outcome, src)

            monkeypatch.setattr(SupportService, "_finish", lose)
            resp = _adjust(staff, b_id, op=op, expected=expected)
            assert _error(resp) == "operation_outcome_unknown"
            monkeypatch.setattr(SupportService, "_finish", real)
        finally:
            remote.close()
        remote = make_remote(tmp_path)
        try:
            staff = remote.staff(enroll=False)
            status = staff.get(f"/api/admin/support-operations/{op}").json()
            assert status["outcome_code"] == "committed"
            assert status["account"]["credits"]["included"] == "15.0000"
            retry = _adjust(staff, b_id, op=op, expected=expected)
            assert (
                retry.json()["source_entitlement_event_id"]
                == status["source_entitlement_event_id"]
            )
            assert len(_events(remote, b_id)) == 3
        finally:
            remote.close()

    def test_concurrent_distinct_adjustments_never_overwrite(
        self, setup: tuple[RemoteHarness, Any, Any, str]
    ) -> None:
        remote, staff, _b, b_id = setup
        remote.seed_hosted(b_id, credits="10")
        expected = staff.get(f"/api/admin/accounts/{b_id}").json()[
            "last_entitlement_event_id"
        ]
        results: list[int] = []

        def run() -> None:
            results.append(_adjust(staff, b_id, expected=expected).status_code)

        threads = [threading.Thread(target=run) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        committed = results.count(200)
        assert committed >= 1 and set(results) <= {200, 409}
        total = staff.get(f"/api/admin/accounts/{b_id}").json()["credits"]["included"]
        assert Decimal(total) == Decimal("10") + 5 * committed
        assert len(_events(remote, b_id)) == 2 + committed
