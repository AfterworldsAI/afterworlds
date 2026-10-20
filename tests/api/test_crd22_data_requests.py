"""CRD Issue 22 §4-§6 through the built remote app: Story and account-wide
export/deletion requested by the authenticated owner, reviewed, approved and
executed by the Owner administrator in a distinct staff session, with two
accounts, real fake-provider turns and planted orphan-prone history."""

from __future__ import annotations

import uuid
from typing import Any

import sqlalchemy as sa

from afterworlds.entitlement.orm import EntitlementEvent
from afterworlds.operations.orm import RightsEvidenceORM
from afterworlds.remote.control_orm import (
    DeletionSuppressionORM,
    HostedAccountORM,
    IdentityPrincipalORM,
)
from tests.api._remote import PASSWORD, RemoteHarness
from tests.operations._data import (
    chunk_count,
    plant,
    play_branching,
    rows_with,
    unzip,
)


def _error(resp: Any) -> str:
    return str(resp.json()["error_code"])


def _request(
    c: Any, kind: str, scope: str, story_id: str | None = None
) -> dict[str, Any]:
    resp = c.post(
        "/api/data-requests",
        json={"kind": kind, "scope": scope, "story_id": story_id},
    )
    assert resp.status_code == 201, resp.text
    return dict(resp.json())


def _approve_execute(staff: Any, request_id: str) -> dict[str, Any]:
    view = staff.get(f"/api/admin/data-requests/{request_id}").json()
    approved = staff.post(
        f"/api/admin/data-requests/{request_id}/approve",
        json={"expected_revision": view["revision"], "reason": "verified owner"},
    )
    assert approved.status_code == 200, approved.text
    done = staff.post(
        f"/api/admin/data-requests/{request_id}/execute",
        json={"expected_revision": approved.json()["revision"]},
    )
    assert done.status_code == 200, done.text
    return dict(done.json())


def _confirm(c: Any, request: dict[str, Any], password: str | None = None) -> Any:
    preview = c.get(f"/api/data-requests/{request['request_id']}/deletion-preview")
    assert preview.status_code == 200, preview.text
    return c.post(
        f"/api/data-requests/{request['request_id']}/confirm",
        json={
            "expected_revision": request["revision"],
            "scope_revision": preview.json()["scope_revision"],
            "password": password,
        },
    )


def _ledger(remote: RemoteHarness, account_id: str) -> int:
    with remote.app.state.session_factory() as s:
        return int(
            s.scalar(
                sa.select(sa.func.count()).where(
                    EntitlementEvent.sojourner_id == uuid.UUID(account_id)
                )
            )
            or 0
        )


def _phase(view: dict[str, Any], code: str) -> str:
    return next(p["outcome_code"] for p in view["phases"] if p["phase_code"] == code)


class TestExport:
    def test_story_export_is_owner_scoped_visible_and_counted(
        self, remote: RemoteHarness
    ) -> None:
        a = remote.enroll("a@example.test")
        b = remote.enroll("b@example.test")
        a_id = remote.account_id(a)
        remote.seed_hosted(a_id)
        remote.seed_hosted(remote.account_id(b))
        s1 = play_branching(a, "First tale", "I open the gate.")
        s2 = play_branching(a, "Second tale", "I climb the tower.")
        sb = play_branching(b, "B's tale", "B wanders.")
        plant(
            remote.app.state.session_factory, s1, "HIDDENMARK", orphan_marker="ORPHANOK"
        )
        staff = remote.staff()

        # B can neither request nor see A's Story or request.
        assert (
            _error(
                b.post(
                    "/api/data-requests",
                    json={"kind": "export", "scope": "story", "story_id": s1},
                )
            )
            == "not_found"
        )
        req = _request(a, "export", "story", s1)
        assert req["state"] == "awaiting_authorization"
        assert req["export_deadline_at"] is not None
        assert b.get(f"/api/data-requests/{req['request_id']}").status_code == 404
        assert b.get("/api/data-requests").json()["requests"] == []
        # A duplicate open request is refused, naming the existing one.
        dup = a.post(
            "/api/data-requests",
            json={"kind": "export", "scope": "story", "story_id": s1},
        )
        assert _error(dup) == "operation_conflict"
        # Ordinary sessions cannot approve; tracking alone completes nothing.
        assert (
            a.post(
                f"/api/admin/data-requests/{req['request_id']}/approve",
                json={"expected_revision": 1},
            ).status_code
            == 403
        )
        assert (
            a.get(f"/api/data-requests/{req['request_id']}/artifact").status_code == 404
        )

        done = _approve_execute(staff, req["request_id"])
        assert done["state"] == "completed"
        actors = [t["actor_role"] for t in done["transitions"]]
        assert actors == ["requester", "administrator", "administrator", "system"]

        resp = a.get(f"/api/data-requests/{req['request_id']}/artifact")
        assert resp.status_code == 200 and resp.headers["cache-control"] == "no-store"
        files = unzip(resp.content)
        manifest = files["manifest.json"]
        assert manifest["scope"] == "story" and manifest["subject_ref"] == a_id
        assert manifest["counts"]["stories"] == 1
        story = files[f"stories/{s1}/story.json"]
        assert manifest["snapshot_boundary"]["stories"][s1]["turns"] == len(
            story["transcript"]
        )
        assert any("I open the gate." in t["user_input"] for t in story["transcript"])
        everything = str(files)
        assert "HIDDENMARK" not in everything
        # Attributable orphan Turn prose is the player's own transcript.
        assert "ORPHANOK" in everything
        assert s2 not in everything and sb not in everything
        assert "B wanders" not in everything
        codes = {e["code"] for e in manifest["exclusions"]}
        assert {"story_bible_internal_canon", "hidden_rpg_mechanics"} <= codes
        # Another account cannot download it, nor can staff via the owner route.
        assert (
            b.get(f"/api/data-requests/{req['request_id']}/artifact").status_code == 404
        )
        assert (
            staff.get(f"/api/data-requests/{req['request_id']}/artifact").status_code
            == 401
        )

    def test_account_export_enumerates_every_story_and_records(
        self, remote: RemoteHarness
    ) -> None:
        a = remote.enroll("a@example.test")
        a_id = remote.account_id(a)
        remote.seed_hosted(a_id)
        stories = {play_branching(a, f"Tale {i}", f"Act {i}.") for i in range(3)}
        staff = remote.staff()
        req = _request(a, "export", "account")
        done = _approve_execute(staff, req["request_id"])
        assert done["state"] == "completed"
        files = unzip(a.get(f"/api/data-requests/{req['request_id']}/artifact").content)
        manifest = files["manifest.json"]
        assert set(manifest["snapshot_boundary"]["stories"]) == stories
        assert manifest["counts"]["stories"] == 3
        assert files["account/account.json"]["contact_address"] == "a@example.test"
        ledger = files["account/entitlement_history.json"]
        assert ledger["total_events"] == manifest["counts"]["entitlement_events"] >= 2
        ops = files["account/operational_records.json"]
        assert any(r["request_id"] == req["request_id"] for r in ops["data_requests"])
        assert PASSWORD not in str(files)

    def test_export_survives_credit_exhaustion_and_lapse(
        self, remote: RemoteHarness
    ) -> None:
        a = remote.enroll("a@example.test")
        s1 = a.post(
            "/api/stories", json={"title": "Quiet", "mode": "branching"}
        ).json()["story_id"]
        # No hosted access at all: owned-content export needs no billing gate.
        staff = remote.staff()
        req = _request(a, "export", "story", s1)
        assert _approve_execute(staff, req["request_id"])["state"] == "completed"


class TestStoryDeletion:
    def test_confirmed_story_deletion_removes_orphan_prone_content(
        self, remote: RemoteHarness
    ) -> None:
        a = remote.enroll("a@example.test")
        b = remote.enroll("b@example.test")
        a_id = remote.account_id(a)
        remote.seed_hosted(a_id)
        remote.seed_hosted(remote.account_id(b))
        s1 = play_branching(a, "Doomed", "I ring the bell.")
        s2 = play_branching(a, "Kept", "I stay home.")
        sb = play_branching(b, "Other", "B stays.")
        content = remote.app.state.session_factory
        planted = plant(content, s1, "ERASEMARK")
        assert chunk_count(s1) > 0
        staff = remote.staff()
        ledger = _ledger(remote, a_id)

        req = _request(a, "deletion", "story", s1)
        assert req["state"] == "requested"
        # Stale confirmation and a wrong scope revision are refused.
        stale = a.post(
            f"/api/data-requests/{req['request_id']}/confirm",
            json={"expected_revision": 1, "scope_revision": "nope"},
        )
        assert _error(stale) == "operation_stale"
        assert (
            _error(
                staff.post(
                    f"/api/admin/data-requests/{req['request_id']}/approve",
                    json={"expected_revision": 1, "reason": "verified owner request"},
                )
            )
            == "operation_conflict"
        )
        confirmed = _confirm(a, req)
        assert confirmed.status_code == 200, confirmed.text
        body = confirmed.json()["request"]
        assert body["state"] == "awaiting_authorization"
        assert confirmed.json()["receipt_credential"] is None
        assert body["live_deadline_at"] and body["backup_deadline_at"]

        done = _approve_execute(staff, req["request_id"])
        assert done["state"] == "in_progress", done
        assert _phase(done, "sql_content") == "succeeded"
        assert _phase(done, "vector_logical") == "succeeded"
        assert _phase(done, "backups") == "succeeded"  # no backup exists
        assert _phase(done, "physical_compaction") == "pending"
        assert "physical_compaction" in done["progress_code"]

        assert rows_with(content, "ERASEMARK") == []
        assert chunk_count(s1) == 0
        with content() as s:
            for turn in planted.values():
                assert (
                    s.scalar(
                        sa.text("SELECT count(*) FROM turns WHERE turn_id=:t"),
                        {"t": turn},
                    )
                    == 0
                )
        assert a.get(f"/api/stories/{s1}").status_code == 404
        assert a.get(f"/api/stories/{s2}").status_code == 200
        assert b.get(f"/api/stories/{sb}/turns").json()["turns"]
        assert chunk_count(s2) > 0 and chunk_count(sb) > 0
        with remote.app.state.control_factory() as s:
            sup = s.scalars(
                sa.select(DeletionSuppressionORM).where(
                    DeletionSuppressionORM.request_id == req["request_id"]
                )
            ).one()
            assert sup.effective_boundary_at == body["confirmed_at"].replace(
                "Z", "+00:00"
            ) or sup.effective_boundary_at.startswith(body["confirmed_at"][:19])
        # Story deletion does not close the account or touch its ledger.
        assert _ledger(remote, a_id) == ledger
        assert a.get("/api/account").status_code == 200

    def test_unavailable_vector_store_fails_visibly_and_retry_completes(
        self, remote: RemoteHarness
    ) -> None:
        a = remote.enroll("a@example.test")
        remote.seed_hosted(remote.account_id(a))
        s1 = play_branching(a, "Flaky", "Hello.")
        staff = remote.staff()
        req = _request(a, "deletion", "story", s1)
        assert _confirm(a, req).status_code == 200
        ctx = remote.app.state.data_requests.deletion
        real = ctx.delete_story_chunks

        def broken(_: str) -> int:
            raise RuntimeError("chroma down")

        ctx.delete_story_chunks = broken
        first = _approve_execute(staff, req["request_id"])
        assert first["state"] == "failed"
        assert _phase(first, "vector_logical") == "failed"
        # Nothing was detached: the SQL content is still there to retry.
        assert a.get(f"/api/stories/{s1}").status_code == 404  # suppressed
        ctx.delete_story_chunks = real
        retry = staff.post(
            f"/api/admin/data-requests/{req['request_id']}/execute",
            json={"expected_revision": first["revision"]},
        ).json()
        assert retry["state"] == "in_progress"
        assert _phase(retry, "sql_content") == "succeeded"
        states = [t["state"] for t in retry["transitions"]]
        assert states.count("failed") == 1 and states.count("in_progress") == 2


class TestAccountDeletion:
    def test_account_deletion_closes_access_keeps_minimized_records(
        self, remote: RemoteHarness
    ) -> None:
        a = remote.enroll("a@example.test")
        b = remote.enroll("b@example.test")
        a_id = remote.account_id(a)
        remote.seed_hosted(a_id)
        remote.seed_hosted(remote.account_id(b))
        play_branching(a, "Mine", "I write.")
        sb = play_branching(b, "Theirs", "They write.")
        staff = remote.staff()
        ledger = _ledger(remote, a_id)
        req = _request(a, "deletion", "account")
        assert _error(_confirm(a, req)) == "operation_precondition_failed"
        confirmed = _confirm(a, req, password=PASSWORD)
        assert confirmed.status_code == 200, confirmed.text
        credential = confirmed.json()["receipt_credential"]
        assert credential

        done = _approve_execute(staff, req["request_id"])
        assert _phase(done, "identity") == "succeeded"
        # Live hosted subscription: CRD Issue 23's closure contract is absent,
        # so the request cannot complete.
        assert _phase(done, "commercial") == "dependency_unavailable"
        assert done["state"] == "in_progress"
        # Undelivered notices (address and codes) went with the profile.
        import json as _json

        assert not [
            n
            for n in remote.outbox.glob("*.json")
            if _json.loads(n.read_text(encoding="utf-8"))["to"] == "a@example.test"
        ]
        assert any(remote.outbox.glob("*.json"))  # B's notices are untouched
        # The account's sessions are gone; status survives via the credential.
        assert a.get("/api/data-requests").status_code == 401
        anon = remote.client()
        receipt = anon.post(
            "/api/data-requests/receipt",
            json={"request_id": req["request_id"], "credential": credential},
        )
        assert receipt.status_code == 200 and receipt.json()["state"] == "in_progress"
        for wrong in (
            {"request_id": req["request_id"], "credential": "x" * 43},
            {"request_id": str(uuid.uuid4()), "credential": credential},
        ):
            assert (
                anon.post("/api/data-requests/receipt", json=wrong).status_code == 404
            )
        with remote.app.state.control_factory() as s:
            account = s.get(HostedAccountORM, a_id)
            assert account is not None and account.status == "closed"
            assert (
                s.scalar(
                    sa.select(sa.func.count()).where(
                        IdentityPrincipalORM.contact_address == "a@example.test"
                    )
                )
                == 0
            )
        # Minimized ledger retained for the closed-account lifetime.
        assert _ledger(remote, a_id) == ledger
        assert b.get(f"/api/stories/{sb}/turns").json()["turns"]
        # Signing in again as the deleted address fails like any unknown one.
        again = remote.client().post(
            "/api/auth/sign-in",
            json={"contact_address": "a@example.test", "password": PASSWORD},
        )
        assert _error(again) == "authentication_failed"

    def test_byok_rights_survive_and_inactive_commercial_is_not_applicable(
        self, remote: RemoteHarness
    ) -> None:
        from datetime import UTC, datetime

        from afterworlds.entitlement.enums import EntitlementEventType
        from afterworlds.entitlement.payloads import ByokLicenseActivatedPayload
        from afterworlds.entitlement.service import EntitlementService

        a = remote.enroll("a@example.test")
        a_id = remote.account_id(a)
        with remote.app.state.session_factory() as s:
            EntitlementService(s).receive_entitlement_event(
                uuid.UUID(a_id),
                EntitlementEventType.BYOK_LICENSE_ACTIVATED,
                ByokLicenseActivatedPayload(
                    purchased_at=datetime(2026, 1, 1, tzinfo=UTC),
                    external_source="store",
                    external_reference_id="lic-1",
                ),
            )
        staff = remote.staff()
        req = _request(a, "deletion", "account")
        assert _confirm(a, req, password=PASSWORD).status_code == 200
        done = _approve_execute(staff, req["request_id"])
        assert _phase(done, "commercial") == "not_applicable"
        assert _phase(done, "rights_evidence") == "succeeded"
        with remote.app.state.control_factory() as s:
            rights = s.scalars(sa.select(RightsEvidenceORM)).one()
            assert rights.subject_ref == a_id
            assert rights.external_reference_id == "lic-1"

    def test_owner_administrator_account_cannot_be_erased(
        self, remote: RemoteHarness
    ) -> None:
        staff = remote.staff()
        owner = remote.client()
        owner.post(
            "/api/auth/sign-in",
            json={"contact_address": "owner@example.test", "password": PASSWORD},
        )
        req = _request(owner, "deletion", "account")
        assert _confirm(owner, req, password=PASSWORD).status_code == 200
        done = _approve_execute(staff, req["request_id"])
        assert done["state"] == "failed"
        assert _phase(done, "identity") == "failed"
        assert staff.get("/api/admin/data-requests").status_code == 200
