"""Prerequisite #205 §4/§5: fresh stores, single writer, restore/fence hooks,
backup clocks, Retrieval Memory guard and delayed-work scope.

The suppression instructions here are a disposable fixture standing in for
CRD Issue 22's operational records; the enforcer fixture deletes through the
owning Story CRUD and the ADR-018 D11 delete path.
"""

from __future__ import annotations

import hashlib
import shutil
import sqlite3
import uuid
from contextlib import closing
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from afterworlds.api.app import create_app
from afterworlds.api.config import ApiSettings
from afterworlds.models.context import RetrievalMemoryPayload
from afterworlds.persistence.crud.story import delete_story
from afterworlds.remote.access import DelayedWorkScope, StoryAccessDenied
from afterworlds.remote.retrieval_guard import (
    GuardedRetrievalMemory,
    GuardedRetrievalWrites,
)
from afterworlds.remote.storage import (
    StoreRefused,
    backup_disposition,
    begin_restore,
    content_store_id,
    copy_backup,
    dispose_backup,
    due_backups,
    pending_restores,
    record_suppression,
    register_backup,
    verify_restore,
)
from tests.api._remote import PASSWORD, RemoteHarness, make_remote, remote_settings

T0 = datetime(2026, 10, 1, 12, 0, tzinfo=UTC)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture()
def env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv(
        "AFTERWORLDS_RETRIEVAL_PERSIST_DIRECTORY", str(tmp_path / "chroma")
    )
    monkeypatch.setenv("AFTERWORLDS_FAKE_PROVIDER", "1")
    return tmp_path


class TestFreshStoreAndSingleWriter:
    def test_local_store_is_refused_untouched(self, env: Path) -> None:
        local = ApiSettings(
            database_url=f"sqlite:///{env / 'content.db'}",
            frontend_dist_dir=env / "no_frontend",
        )
        with TestClient(create_app(local)) as c:
            c.post("/api/stories", json={"title": "Local proof", "mode": "branching"})
        before = _sha(env / "content.db")
        with pytest.raises(StoreRefused, match="never import local or test data"):
            create_app(remote_settings(env))
        assert _sha(env / "content.db") == before

    def test_store_of_another_deployment_is_refused(self, env: Path) -> None:
        first = make_remote(env)
        first.close()
        other = remote_settings(env)
        other = ApiSettings(
            **{
                **other.__dict__,
                "control_database_url": f"sqlite:///{env / 'other.db'}",
            }
        )
        with pytest.raises(StoreRefused):
            create_app(other)

    def test_second_writer_process_is_refused(self, env: Path) -> None:
        first = make_remote(env)
        try:
            with pytest.raises(StoreRefused, match="another process"):
                create_app(remote_settings(env))
        finally:
            first.close()

    def test_fresh_store_imports_nothing(self, remote: RemoteHarness) -> None:
        with remote.app.state.session_factory() as s:
            for table in ("stories", "entitlement_event", "sojourner_identity"):
                assert s.execute(_count(table)).scalar() == 0, table
        assert not hasattr(remote.app.state, "sojourner_id")


def _count(table: str) -> Any:
    import sqlalchemy as sa

    return sa.text(f"SELECT COUNT(*) FROM {table}")


def _snapshot(
    harness: RemoteHarness, target: Path, captured: datetime | None = None
) -> str:
    """Capture the content store like ``storage_cli capture`` and inventory it."""
    target.mkdir()
    db = harness.tmp_path / "content.db"
    with (
        closing(sqlite3.connect(db)) as src,
        closing(sqlite3.connect(target / "content.db")) as dst,
    ):
        src.backup(dst)
    return register_backup(
        harness.app.state.control_factory,
        store_id=content_store_id(harness.app.state.session_factory),
        storage_locator=str(target),
        original_capture_at=captured or datetime.now(UTC),
    )


def _live(harness: RemoteHarness) -> Path:
    return harness.tmp_path / "content.db"


class TestRestoreGate:
    def test_restore_cannot_resurrect_sessions_accounts_or_suppressed_stories(
        self, env: Path
    ) -> None:
        h = make_remote(env)
        a = h.enroll("a@example.test")
        b = h.enroll("b@example.test")
        a_id = h.account_id(a)
        deleted = a.post(
            "/api/stories", json={"title": "Erase me", "mode": "branching"}
        ).json()["story_id"]
        kept = a.post(
            "/api/stories", json={"title": "Keep", "mode": "branching"}
        ).json()["story_id"]
        backup_id = _snapshot(h, env / "backup1")
        stale_cookies = dict(a.cookies)

        # Authoritative suppression input (CRD Issue 22 later supplies it):
        # the guard denies the Story at once, before any deletion runs.
        record_suppression(
            h.app.state.control_factory,
            subject_ref=a_id,
            story_refs=[deleted],
            request_id=str(uuid.uuid4()),
            scope="story",
            effective_boundary_at=datetime.now(UTC),
            now=datetime.now(UTC),
        )
        assert a.get(f"/api/stories/{deleted}").status_code == 404
        assert [s["story_id"] for s in a.get("/api/stories").json()["stories"]] == [
            kept
        ]
        # Later identity changes happen only in the control store.
        a.post("/api/auth/sign-out")
        b.post("/api/account/close", json={"password": PASSWORD})
        with h.app.state.session_factory.begin() as s:
            delete_story(s, uuid.UUID(deleted))
        h.close()

        # Restore the pre-deletion snapshot.
        control = h.app.state.control_factory
        restore_id = begin_restore(
            control, backup_id, live_database=env / "content.db", now=datetime.now(UTC)
        )
        shutil.copyfile(env / "backup1" / "content.db", env / "content.db")
        for suffix in ("-wal", "-shm"):
            (env / f"content.db{suffix}").unlink(missing_ok=True)
        with pytest.raises(StoreRefused, match="awaiting deletion-suppression"):
            create_app(remote_settings(env))

        content = h.app.state.session_factory
        assert verify_restore(
            control, restore_id, content, lambda _s: 0, now=datetime.now(UTC)
        ) == [deleted]
        assert pending_restores(control) == [restore_id]
        # Disposable enforcer fixture: owning-service delete, then verify.
        with content.begin() as s:
            delete_story(s, uuid.UUID(deleted))
        unavailable = RuntimeError("chroma read failed")

        def failing_count(_story: str) -> int:
            raise unavailable

        with pytest.raises(RuntimeError):  # an unavailable read is not zero
            verify_restore(
                control, restore_id, content, failing_count, now=datetime.now(UTC)
            )
        assert (
            verify_restore(
                control, restore_id, content, lambda _s: 0, now=datetime.now(UTC)
            )
            == []
        )
        assert pending_restores(control) == []

        h2 = RemoteHarness(
            app=create_app(remote_settings(env)),
            settings=remote_settings(env),
            tmp_path=env,
        )
        try:
            replay = h2.client()
            replay.cookies.update(stale_cookies)
            assert (
                replay.get("/api/stories").status_code == 401
            )  # revoked stays revoked
            closed = h2.client().post(
                "/api/auth/sign-in",
                json={"contact_address": "b@example.test", "password": PASSWORD},
            )
            assert closed.status_code == 401  # closed stays closed
            a2 = h2.client()
            a2.post(
                "/api/auth/sign-in",
                json={"contact_address": "a@example.test", "password": PASSWORD},
            )
            assert [
                s["story_id"] for s in a2.get("/api/stories").json()["stories"]
            ] == [kept]
            assert a2.get(f"/api/stories/{deleted}").status_code == 404
        finally:
            h2.close()


class TestBackupClocks:
    def test_lifetime_runs_from_original_capture(self, remote: RemoteHarness) -> None:
        control = remote.app.state.control_factory
        b1 = _snapshot(remote, remote.tmp_path / "b1", captured=T0)
        later_copy = copy_backup(
            control, b1, storage_locator=str(remote.tmp_path / "b1")
        )
        day21 = T0 + timedelta(days=21)
        live = _live(remote)
        assert due_backups(control, now=day21 - timedelta(seconds=1)) == []
        assert set(due_backups(control, now=day21)) == {b1, later_copy}
        with pytest.raises(StoreRefused, match="21-day"):
            # copies never renew
            begin_restore(control, later_copy, live_database=live, now=day21)
        begin_restore(
            control, later_copy, live_database=live, now=day21 - timedelta(seconds=1)
        )

    def test_deletion_backup_deadline_is_thirty_days_overall(
        self, remote: RemoteHarness
    ) -> None:
        control = remote.app.state.control_factory
        before = register_backup(
            control, store_id="s", storage_locator="/a", original_capture_at=T0
        )
        broken = register_backup(
            control,
            store_id="s",
            storage_locator="/b",
            original_capture_at=T0,
            verification_status="inaccessible",
        )
        after = register_backup(
            control,
            store_id="s",
            storage_locator="/c",
            original_capture_at=T0 + timedelta(days=3),
        )
        boundary = T0 + timedelta(days=2)
        sup = record_suppression(
            control,
            subject_ref="acct",
            story_refs=["s1"],
            request_id="r",
            scope="story",
            effective_boundary_at=boundary,
            now=boundary,
        )
        report = backup_disposition(control, sup, now=boundary)
        assert report.deadline == boundary + timedelta(days=30)
        assert set(report.pending_backup_ids) == {before, broken}
        assert after not in report.pending_backup_ids
        assert not report.complete and not report.overdue
        dispose_backup(control, before, now=boundary + timedelta(days=19))
        dispose_backup(control, broken, now=boundary + timedelta(days=19))
        report = backup_disposition(control, sup, now=boundary + timedelta(days=30))
        # Unverified coverage is a failure, not presumed compliance.
        assert report.unverified_backup_ids == (broken,)
        assert not report.complete and report.overdue
        unverified = register_backup(
            control,
            store_id="s",
            storage_locator="/d",
            original_capture_at=T0,
            verification_status="unverified",
        )
        with pytest.raises(StoreRefused, match="unverified"):
            begin_restore(control, unverified, live_database=_live(remote), now=T0)


class _FakeRead:
    calls: list[uuid.UUID]

    def __init__(self) -> None:
        self.calls = []

    def retrieve(self, story_id: uuid.UUID, query: str) -> RetrievalMemoryPayload:
        self.calls.append(story_id)
        return RetrievalMemoryPayload()


class _FakeWrites:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def ingest_turn(self, story_id: uuid.UUID, *args: object) -> None:
        self.calls.append(f"ingest:{story_id}")

    def delete_turn(self, story_id: uuid.UUID, turn_id: uuid.UUID) -> None:
        self.calls.append(f"delete_turn:{story_id}")

    def count_for_story(self, story_id: uuid.UUID) -> int:
        self.calls.append(f"count:{story_id}")
        return 0

    def delete_story(self, story_id: uuid.UUID) -> int:
        self.calls.append(f"delete:{story_id}")
        return 0


class TestRetrievalGuardAndDelayedWork:
    def _setup(self, remote: RemoteHarness) -> tuple[Any, str, str, str]:
        a = remote.enroll("a@example.test")
        b = remote.enroll("b@example.test")
        sid = a.post("/api/stories", json={"title": "A", "mode": "branching"}).json()[
            "story_id"
        ]
        return a, sid, remote.account_id(a), remote.account_id(b)

    def test_vector_access_requires_owned_active_unsuppressed_story(
        self, remote: RemoteHarness
    ) -> None:
        a, sid, a_id, b_id = self._setup(remote)
        policy = remote.app.state.access_policy
        factory = remote.app.state.session_factory
        read, writes = _FakeRead(), _FakeWrites()
        guarded_read = GuardedRetrievalMemory(read, policy, factory)
        guarded = GuardedRetrievalWrites(writes, policy, factory)  # type: ignore[arg-type]
        story = uuid.UUID(sid)

        guarded_read.retrieve(story, "q")
        guarded.ingest_turn(story, uuid.uuid4(), None, "branching", "prose", "t")
        assert read.calls == [story] and len(writes.calls) == 1
        with pytest.raises(StoryAccessDenied):
            guarded_read.retrieve(uuid.uuid4(), "q")  # unowned
        with pytest.raises(StoryAccessDenied):
            guarded.delete_story_for(DelayedWorkScope(uuid.UUID(b_id), story, "delete"))

        record_suppression(
            remote.app.state.control_factory,
            subject_ref=a_id,
            story_refs=[sid],
            request_id="r",
            scope="story",
            effective_boundary_at=datetime.now(UTC),
            now=datetime.now(UTC),
        )
        for call in (
            lambda: guarded_read.retrieve(story, "q"),
            lambda: guarded.ingest_turn(
                story, uuid.uuid4(), None, "branching", "x", "t"
            ),
            lambda: guarded.count_for_story(story),
        ):
            with pytest.raises(StoryAccessDenied):
                call()
        # Deletion enforces the suppression, so the owner may still delete.
        assert (
            guarded.delete_story_for(DelayedWorkScope(uuid.UUID(a_id), story, "delete"))
            == 0
        )
        assert read.calls == [story]
        assert writes.calls[-1] == f"delete:{story}"

    def test_delayed_work_rechecks_scope_when_it_runs(
        self, remote: RemoteHarness
    ) -> None:
        a, sid, a_id, b_id = self._setup(remote)
        policy = remote.app.state.access_policy
        story = uuid.UUID(sid)
        with remote.app.state.session_factory() as s:
            policy.check_delayed_work(
                s, DelayedWorkScope(uuid.UUID(a_id), story, "reindex")
            )
            with pytest.raises(StoryAccessDenied):
                policy.check_delayed_work(
                    s, DelayedWorkScope(uuid.UUID(b_id), story, "reindex")
                )
        a.post("/api/account/close", json={"password": PASSWORD})
        with remote.app.state.session_factory() as s, pytest.raises(StoryAccessDenied):
            policy.check_delayed_work(
                s, DelayedWorkScope(uuid.UUID(a_id), story, "reindex")
            )

    def test_backfill_job_requires_and_rechecks_account_scope(
        self, remote: RemoteHarness, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from scripts import retrieval_backfill

        _a, sid, a_id, b_id = self._setup(remote)
        monkeypatch.setenv("AFTERWORLDS_DEPLOYMENT", "remote")
        monkeypatch.setenv(
            "AFTERWORLDS_CONTROL_DATABASE_URL",
            str(remote.settings.control_database_url),
        )
        factory = remote.app.state.session_factory
        story = uuid.UUID(sid)
        retrieval_backfill.remote_scope_check(factory, story, a_id, "backfill")
        for account, mode in ((None, "backfill"), (b_id, "reindex"), (b_id, "delete")):
            with pytest.raises(SystemExit) as exc:
                retrieval_backfill.remote_scope_check(factory, story, account, mode)
            assert exc.value.code == 3


class TestRestoreVerificationScope:
    def _restore(self, remote: RemoteHarness) -> str:
        backup = _snapshot(remote, remote.tmp_path / "snap")
        return begin_restore(
            remote.app.state.control_factory,
            backup,
            live_database=_live(remote),
            now=datetime.now(UTC),
        )

    def test_account_scope_covers_every_owned_story(
        self, remote: RemoteHarness
    ) -> None:
        a = remote.enroll("a@example.test")
        listed = a.post(
            "/api/stories", json={"title": "1", "mode": "branching"}
        ).json()["story_id"]
        unlisted = a.post("/api/stories", json={"title": "2", "mode": "rpg"}).json()[
            "story_id"
        ]
        restore_id = self._restore(remote)
        record_suppression(
            remote.app.state.control_factory,
            subject_ref=remote.account_id(a),
            story_refs=[listed],  # incomplete on purpose
            request_id="r",
            scope="account",
            effective_boundary_at=datetime.now(UTC),
            now=datetime.now(UTC),
        )
        remaining = verify_restore(
            remote.app.state.control_factory,
            restore_id,
            remote.app.state.session_factory,
            lambda _s: 0,
            now=datetime.now(UTC),
        )
        assert remaining == sorted([listed, unlisted])

    def test_cascade_survivors_keep_a_story_unverified(
        self, remote: RemoteHarness
    ) -> None:
        from afterworlds.persistence.orm.story_bible import (
            SBDynamicFieldHistoryORM,
        )

        a = remote.enroll("a@example.test")
        sid = a.post("/api/stories", json={"title": "1", "mode": "branching"}).json()[
            "story_id"
        ]
        with remote.app.state.session_factory.begin() as s:
            s.add(
                SBDynamicFieldHistoryORM(
                    history_id=str(uuid.uuid4()),
                    story_id=sid,
                    entity_type="setting",
                    entity_id=str(uuid.uuid4()),
                    field_name="dynamic_conditions",
                    old_value='"old canon"',
                    changed_at=datetime.now(UTC).isoformat(),
                )
            )
        restore_id = self._restore(remote)
        record_suppression(
            remote.app.state.control_factory,
            subject_ref=remote.account_id(a),
            story_refs=[sid],
            request_id="r",
            scope="story",
            effective_boundary_at=datetime.now(UTC),
            now=datetime.now(UTC),
        )
        # Bare Story CRUD deletion leaves the plain-string history row behind.
        with remote.app.state.session_factory.begin() as s:
            delete_story(s, uuid.UUID(sid))
        args = (
            remote.app.state.control_factory,
            restore_id,
            remote.app.state.session_factory,
            lambda _s: 0,
        )
        assert verify_restore(*args, now=datetime.now(UTC)) == [sid]
        with remote.app.state.session_factory.begin() as s:
            s.query(SBDynamicFieldHistoryORM).filter_by(story_id=sid).delete()
        assert verify_restore(*args, now=datetime.now(UTC)) == []


class TestEntitlementLedgerContinuity:
    """A restore must never silently rewind append-only accounting authority."""

    def _grant(self, remote: RemoteHarness, account: str) -> None:
        from afterworlds.entitlement.enums import EntitlementEventType
        from afterworlds.entitlement.payloads import ByokLicenseActivatedPayload
        from afterworlds.entitlement.service import EntitlementService

        with remote.app.state.session_factory() as session:
            EntitlementService(session).receive_entitlement_event(
                uuid.UUID(account),
                EntitlementEventType.BYOK_LICENSE_ACTIVATED,
                ByokLicenseActivatedPayload(purchased_at=datetime.now(UTC)),
            )
            session.commit()

    def test_an_event_recorded_after_capture_refuses_the_restore(
        self, remote: RemoteHarness
    ) -> None:
        a = remote.enroll("a@example.test")
        account = remote.account_id(a)
        self._grant(remote, account)
        backup = _snapshot(remote, remote.tmp_path / "before")
        control = remote.app.state.control_factory
        # Equal ledgers restore.
        begin_restore(
            control, backup, live_database=_live(remote), now=datetime.now(UTC)
        )
        self._grant(remote, account)  # recorded after capture
        with pytest.raises(StoreRefused, match=r"discard 1 entitlement event"):
            begin_restore(
                control, backup, live_database=_live(remote), now=datetime.now(UTC)
            )

    def test_a_divergent_ledger_refuses_the_restore(
        self, remote: RemoteHarness
    ) -> None:
        a = remote.enroll("a@example.test")
        backup = _snapshot(remote, remote.tmp_path / "snap")
        snapshot = remote.tmp_path / "snap" / "content.db"
        with closing(sqlite3.connect(snapshot)) as conn:
            conn.execute(
                "INSERT INTO entitlement_event (event_id, sojourner_id, event_type,"
                " payload_json, created_at) VALUES ('foreign', ?, 'x', '{}', 't')",
                (remote.account_id(a),),
            )
            conn.commit()
        self._grant(remote, remote.account_id(a))
        with pytest.raises(StoreRefused, match="diverges"):
            begin_restore(
                remote.app.state.control_factory,
                backup,
                live_database=_live(remote),
                now=datetime.now(UTC),
            )

    def test_a_missing_live_store_cannot_prove_continuity(
        self, remote: RemoteHarness
    ) -> None:
        backup = _snapshot(remote, remote.tmp_path / "snap")
        with pytest.raises(StoreRefused, match="live content store is missing"):
            begin_restore(
                remote.app.state.control_factory,
                backup,
                live_database=remote.tmp_path / "lost" / "content.db",
                now=datetime.now(UTC),
            )

    def test_a_missing_snapshot_is_refused(self, remote: RemoteHarness) -> None:
        backup = register_backup(
            remote.app.state.control_factory,
            store_id="s",
            storage_locator=str(remote.tmp_path / "nowhere"),
            original_capture_at=datetime.now(UTC),
        )
        with pytest.raises(StoreRefused, match="snapshot is missing"):
            begin_restore(
                remote.app.state.control_factory,
                backup,
                live_database=_live(remote),
                now=datetime.now(UTC),
            )
