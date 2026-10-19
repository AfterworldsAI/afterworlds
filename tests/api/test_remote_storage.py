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
from afterworlds.remote.access import DelayedWorkScope, StoryAccessDenied, work_scope
from afterworlds.remote.retrieval_guard import (
    GuardedRetrievalMemory,
    GuardedRetrievalWrites,
)
from afterworlds.remote.storage import (
    INITIALIZATION_PROVENANCE_TABLE,
    StoreRefused,
    backup_disposition,
    begin_restore,
    bind_vector_store,
    content_store_id,
    copy_backup,
    dispose_backup,
    due_backups,
    mark_restore_copied,
    pending_restores,
    record_suppression,
    register_backup,
    restore_snapshot,
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

    def test_unmarked_vector_store_is_refused_untouched(self, env: Path) -> None:
        local_vectors = env / "chroma"
        local_vectors.mkdir()
        (local_vectors / "chroma.sqlite3").write_bytes(b"local story memory")
        with pytest.raises(StoreRefused, match="never import local or test data"):
            create_app(remote_settings(env))
        assert (local_vectors / "chroma.sqlite3").read_bytes() == b"local story memory"
        assert not (env / "content.db").exists()  # refused before migration

    def test_another_deployments_vector_store_is_refused(
        self, env: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        make_remote(env).close()  # binds env/chroma to that deployment
        other = env / "other"
        other.mkdir()
        with pytest.raises(StoreRefused, match="vector store"):
            create_app(remote_settings(other))  # fresh SQL, foreign vectors

    def test_two_content_stores_cannot_share_one_vector_store(self, env: Path) -> None:
        first = make_remote(env)
        second = env / "second"
        second.mkdir()
        try:
            with pytest.raises(StoreRefused, match="vector store"):
                create_app(remote_settings(second))
        finally:
            first.close()
        assert not (second / "content.db").exists()

    def test_a_bound_deployment_with_missing_vectors_is_refused(
        self, env: Path
    ) -> None:
        make_remote(env).close()
        shutil.rmtree(env / "chroma")
        with pytest.raises(StoreRefused, match="missing or belongs"):
            create_app(remote_settings(env))

    def test_fresh_store_imports_nothing(self, remote: RemoteHarness) -> None:
        with remote.app.state.session_factory() as s:
            for table in ("stories", "entitlement_event", "sojourner_identity"):
                assert s.execute(_count(table)).scalar() == 0, table
        assert not hasattr(remote.app.state, "sojourner_id")


def _released(env: Path) -> None:
    """Every store handle a failed construction held is gone: both locks can
    be taken, and (on Windows, where open files cannot move) each store file
    and the vector directory can be renamed and put back."""
    _locks_released(env)
    for name in ("content.db", "control.db", "chroma"):
        path = env / name
        if path.exists():
            moved = path.with_name(name + ".moved")
            path.rename(moved)
            moved.rename(path)


def _fail_after(real: Any) -> Any:
    def wrapped(*a: Any, **k: Any) -> Any:
        real(*a, **k)
        raise RuntimeError("injected construction fault")

    return wrapped


class TestFailedConstructionReleasesEverything:
    """Review r4313982093: a construction failing after the first lock
    releases locks, engines and vector clients; the same process retries."""

    @pytest.mark.parametrize(
        "point",
        [
            "vector_config",  # after the content lock, before the vector lock
            "lease_recovery",  # after the content engine
            "pipeline",  # after Chroma clients were opened
            "late_wiring",  # after the pipeline and seams
        ],
    )
    def test_original_error_propagates_and_retry_succeeds(
        self, env: Path, monkeypatch: pytest.MonkeyPatch, point: str
    ) -> None:
        import afterworlds.api.app as app_module

        make_remote(env).close()  # a completed deployment
        with monkeypatch.context() as m:
            if point == "vector_config":
                m.setattr(
                    app_module.RetrievalMemoryConfig, "from_env", _injected_construction
                )
            elif point == "lease_recovery":
                m.setattr(
                    app_module, "clear_orphan_turn_leases", _injected_construction
                )
            elif point == "pipeline":
                m.setattr(
                    app_module, "build_pipeline", _fail_after(app_module.build_pipeline)
                )
            else:
                m.setattr(
                    app_module, "ServerHostedByokUnavailable", _injected_construction
                )
            with pytest.raises(RuntimeError, match="injected construction fault"):
                create_app(remote_settings(env))
        _released(env)
        again = make_remote(env)
        try:
            again.enroll("a@example.test")
        finally:
            again.close()

    def test_a_failed_first_start_releases_and_resumes(
        self, env: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import afterworlds.api.app as app_module

        with monkeypatch.context() as m:
            m.setattr(
                app_module, "build_pipeline", _fail_after(app_module.build_pipeline)
            )
            with pytest.raises(RuntimeError, match="injected construction fault"):
                create_app(remote_settings(env))
        identity = _control_row(env, "deployment_marker")
        assert identity is not None  # initialization itself had completed
        _released(env)
        again = make_remote(env)
        try:
            assert content_store_id(again.app.state.session_factory) == identity
        finally:
            again.close()


def _injected_construction(*_a: object, **_k: object) -> Any:
    raise RuntimeError("injected construction fault")


def _count(table: str) -> Any:
    import sqlalchemy as sa

    return sa.text(f"SELECT COUNT(*) FROM {table}")


def _injected(*_a: object, **_k: object) -> None:
    raise RuntimeError("injected initialization fault")


def _control_row(env: Path, table: str) -> str | None:
    with closing(sqlite3.connect(env / "control.db")) as db:
        row = db.execute(
            f"SELECT content_store_id FROM {table} WHERE id = 1"
        ).fetchone()
    return str(row[0]) if row else None


def _tables(db: Path) -> set[str]:
    with closing(sqlite3.connect(db)) as conn:
        return {
            n
            for (n,) in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }


def _locks_released(env: Path) -> None:
    from afterworlds.remote.storage import acquire_store_lock, acquire_vector_lock

    acquire_store_lock(f"sqlite:///{env / 'content.db'}").close()
    acquire_vector_lock(env / "chroma").close()


def _fail_first_start(env: Path, monkeypatch: pytest.MonkeyPatch, fault: str) -> str:
    """Start a fresh deployment with one injected fault; return the identity
    its durable initialization record carries."""
    with monkeypatch.context() as m:
        if fault == "vector_marker_publication":
            # The temporary marker is written; publishing it fails.
            m.setattr("afterworlds.remote.storage.os.replace", _injected)
        else:
            m.setattr(f"afterworlds.api.app.{fault}", _injected)
        with pytest.raises(RuntimeError, match="injected"):
            create_app(remote_settings(env))
    _locks_released(env)
    assert _control_row(env, "deployment_marker") is None
    intent = _control_row(env, "deployment_initialization")
    assert intent is not None
    return intent


_INIT_FAULTS = [
    "upgrade_to_head",
    "initialize_remote_content_store",
    "vector_marker_publication",
    "complete_remote_initialization",
]


class TestInterruptedInitializationResumes:
    """A legitimate fresh deployment interrupted at any initialization
    boundary resumes the same identity; nothing else is ever adopted."""

    @pytest.mark.parametrize("fault", _INIT_FAULTS)
    def test_retry_completes_the_same_deployment(
        self, env: Path, monkeypatch: pytest.MonkeyPatch, fault: str
    ) -> None:
        from afterworlds.remote.storage import read_vector_marker

        identity = _fail_first_start(env, monkeypatch, fault)
        resumed = make_remote(env)
        try:
            assert content_store_id(resumed.app.state.session_factory) == identity
            assert read_vector_marker(env / "chroma") == identity
            assert _control_row(env, "deployment_marker") == identity
            assert _control_row(env, "deployment_initialization") is None
            with resumed.app.state.session_factory() as s:
                for table in ("stories", "entitlement_event", "sojourner_identity"):
                    assert s.execute(_count(table)).scalar() == 0, table
            resumed.enroll("a@example.test")
        finally:
            resumed.close()
        # A normal restart serves the completed deployment, unchanged.
        again = make_remote(env)
        try:
            assert content_store_id(again.app.state.session_factory) == identity
            assert read_vector_marker(env / "chroma") == identity
        finally:
            again.close()

    def test_a_foreign_content_marker_is_never_adopted(
        self, env: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _fail_first_start(env, monkeypatch, "vector_marker_publication")
        with closing(sqlite3.connect(env / "content.db")) as db, db:
            db.execute(
                "UPDATE remote_store_marker SET content_store_id = ?",
                (str(uuid.uuid4()),),
            )
        before = _sha(env / "content.db")
        with pytest.raises(StoreRefused, match="different deployment"):
            create_app(remote_settings(env))
        assert _sha(env / "content.db") == before
        _locks_released(env)

    def test_user_data_in_an_unmarked_store_is_never_adopted(
        self, env: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _fail_first_start(env, monkeypatch, "initialize_remote_content_store")
        with closing(sqlite3.connect(env / "content.db")) as db, db:
            db.execute(
                "INSERT INTO stories (story_id, title, mode, created_at, updated_at)"
                " VALUES (?, 'local', 'branching', 'x', 'x')",
                (str(uuid.uuid4()),),
            )
        before = _sha(env / "content.db")
        with pytest.raises(StoreRefused, match="did not create"):
            create_app(remote_settings(env))
        assert _sha(env / "content.db") == before
        _locks_released(env)

    def test_unknown_vector_files_are_never_adopted(
        self, env: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _fail_first_start(env, monkeypatch, "upgrade_to_head")
        (env / "chroma" / "chroma.sqlite3").write_bytes(b"local story memory")
        with pytest.raises(StoreRefused, match="did not create"):
            create_app(remote_settings(env))
        assert (env / "chroma" / "chroma.sqlite3").read_bytes() == (
            b"local story memory"
        )
        assert _tables(env / "content.db") == {INITIALIZATION_PROVENANCE_TABLE}
        _locks_released(env)

    def test_a_retry_aimed_at_another_content_store_is_refused(
        self, env: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from afterworlds.api.db_bootstrap import upgrade_to_head
        from afterworlds.remote.storage import acquire_store_lock

        identity = _fail_first_start(env, monkeypatch, "upgrade_to_head")
        # An existing migrated, unmarked store: the three sampled tables are
        # empty, but it holds other data.
        other = env / "other.db"
        upgrade_to_head(f"sqlite:///{other}")
        with closing(sqlite3.connect(other)) as db, db:
            db.execute("CREATE TABLE other_data (note TEXT)")
            db.execute("INSERT INTO other_data VALUES ('not this deployment''s')")
        before = _sha(other)
        retargeted = ApiSettings(
            **{
                **remote_settings(env).__dict__,
                "database_url": f"sqlite:///{other}",
            }
        )
        with pytest.raises(StoreRefused, match="different content or vector"):
            create_app(retargeted)
        assert _sha(other) == before
        acquire_store_lock(f"sqlite:///{other}").close()
        assert _control_row(env, "deployment_initialization") == identity

    def test_a_retry_aimed_at_another_vector_store_is_refused(
        self, env: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        identity = _fail_first_start(env, monkeypatch, "upgrade_to_head")
        monkeypatch.setenv(
            "AFTERWORLDS_RETRIEVAL_PERSIST_DIRECTORY", str(env / "other_chroma")
        )
        with pytest.raises(StoreRefused, match="different content or vector"):
            create_app(remote_settings(env))
        assert not (env / "other_chroma" / "afterworlds-deployment.json").exists()
        assert _tables(env / "content.db") == {INITIALIZATION_PROVENANCE_TABLE}
        assert _control_row(env, "deployment_initialization") == identity

    def test_a_torn_temporary_vector_marker_is_replaced(
        self, env: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from afterworlds.remote.storage import read_vector_marker

        identity = _fail_first_start(env, monkeypatch, "upgrade_to_head")
        temp = env / "chroma" / "afterworlds-deployment.json.tmp"
        temp.write_bytes(b'{"content_st')  # a crash mid-write
        resumed = make_remote(env)
        try:
            assert read_vector_marker(env / "chroma") == identity
            assert not temp.exists()
            assert _control_row(env, "deployment_marker") == identity
        finally:
            resumed.close()

    def test_a_lost_completion_response_restarts_as_completed(
        self, env: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import afterworlds.api.app as app_module

        real = app_module.complete_remote_initialization

        def complete_then_fail(*a: Any, **k: Any) -> None:
            real(*a, **k)
            raise RuntimeError("injected initialization fault")

        with monkeypatch.context() as m:
            m.setattr(app_module, "complete_remote_initialization", complete_then_fail)
            with pytest.raises(RuntimeError, match="injected"):
                create_app(remote_settings(env))
        _locks_released(env)
        identity = _control_row(env, "deployment_marker")
        assert identity is not None
        assert _control_row(env, "deployment_initialization") is None
        again = make_remote(env)
        try:
            assert content_store_id(again.app.state.session_factory) == identity
        finally:
            again.close()

    def test_an_unrelated_store_at_the_recorded_path_is_refused(
        self, env: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from afterworlds.api.db_bootstrap import upgrade_to_head

        identity = _fail_first_start(
            env, monkeypatch, "initialize_remote_content_store"
        )
        # By mistake, another unmarked migrated store is copied over the
        # recorded content path: empty sampled tables, other data present.
        unrelated = env / "unrelated" / "content.db"
        unrelated.parent.mkdir()
        upgrade_to_head(f"sqlite:///{unrelated}")
        with closing(sqlite3.connect(unrelated)) as db, db:
            db.execute("CREATE TABLE other_data (note TEXT)")
            db.execute("INSERT INTO other_data VALUES ('rules and detached rows')")
        for suffix in ("", "-wal", "-shm"):
            (env / f"content.db{suffix}").unlink(missing_ok=True)
        shutil.copyfile(unrelated, env / "content.db")
        before = _sha(env / "content.db")
        with pytest.raises(StoreRefused, match="not created by this deployment"):
            create_app(remote_settings(env))
        assert _sha(env / "content.db") == before
        assert _control_row(env, "deployment_initialization") == identity
        _locks_released(env)

    def test_an_interrupted_provenance_stamp_resumes_its_own_empty_store(
        self, env: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from afterworlds.remote.storage import read_vector_marker

        with monkeypatch.context() as m:
            m.setattr("afterworlds.remote.storage._stamp_initialization", _injected)
            with pytest.raises(RuntimeError, match="injected"):
                create_app(remote_settings(env))
        _locks_released(env)
        identity = _control_row(env, "deployment_initialization")
        assert identity is not None
        assert not (env / "content.db").exists()
        resumed = make_remote(env)
        try:
            assert content_store_id(resumed.app.state.session_factory) == identity
            assert read_vector_marker(env / "chroma") == identity
            assert _control_row(env, "deployment_marker") == identity
        finally:
            resumed.close()

    def test_a_fault_inside_stamp_publication_rolls_back_and_resumes(
        self, env: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        real_connect = sqlite3.connect

        class StampInsertFails(sqlite3.Connection):
            def execute(self, sql: str, *a: Any) -> sqlite3.Cursor:  # type: ignore[override]
                if sql.startswith(
                    f"INSERT OR REPLACE INTO {INITIALIZATION_PROVENANCE_TABLE}"
                ):
                    raise RuntimeError("injected initialization fault")
                return super().execute(sql, *a)

        def connect(*a: Any, **k: Any) -> sqlite3.Connection:
            # Only the stamp's own INSERT, issued through Connection.execute,
            # is failed; SQLAlchemy and Alembic use cursors.
            k.setdefault("factory", StampInsertFails)
            return real_connect(*a, **k)

        with monkeypatch.context() as m:
            m.setattr(sqlite3, "connect", connect)
            with pytest.raises(RuntimeError, match="injected"):
                create_app(remote_settings(env))
        _locks_released(env)
        identity = _control_row(env, "deployment_initialization")
        assert identity is not None
        # The CREATE was rolled back with the failed INSERT: no stampless table.
        assert _tables(env / "content.db") == set()
        resumed = make_remote(env)
        try:
            assert content_store_id(resumed.app.state.session_factory) == identity
            assert _control_row(env, "deployment_marker") == identity
        finally:
            resumed.close()

    def test_a_fault_inside_stamp_retirement_rolls_back_and_resumes(
        self, env: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from sqlalchemy import event
        from sqlalchemy.engine import Engine

        drop = f"DROP TABLE IF EXISTS {INITIALIZATION_PROVENANCE_TABLE}"

        def fail_after_drop(_conn: Any, _cursor: Any, statement: str, *_a: Any) -> None:
            if statement.startswith(drop):
                raise RuntimeError("injected initialization fault")

        event.listen(Engine, "after_cursor_execute", fail_after_drop)
        try:
            with pytest.raises(RuntimeError, match="injected"):
                create_app(remote_settings(env))
        finally:
            event.remove(Engine, "after_cursor_execute", fail_after_drop)
        _locks_released(env)
        identity = _control_row(env, "deployment_initialization")
        assert identity is not None
        # The executed DROP and the flushed marker rolled back together.
        with closing(sqlite3.connect(env / "content.db")) as db:
            assert db.execute(
                f"SELECT content_store_id FROM {INITIALIZATION_PROVENANCE_TABLE}"
            ).fetchall() == [(identity,)]
            assert db.execute("SELECT * FROM remote_store_marker").fetchall() == []
        resumed = make_remote(env)
        try:
            assert content_store_id(resumed.app.state.session_factory) == identity
            assert _control_row(env, "deployment_marker") == identity
        finally:
            resumed.close()
        assert INITIALIZATION_PROVENANCE_TABLE not in _tables(env / "content.db")

    def test_the_provenance_stamp_is_retired_on_completion(self, env: Path) -> None:
        make_remote(env).close()
        assert INITIALIZATION_PROVENANCE_TABLE not in _tables(env / "content.db")

    def test_a_completed_deployment_is_never_reinitialized(self, env: Path) -> None:
        make_remote(env).close()
        identity = _control_row(env, "deployment_marker")
        (env / "chroma" / "afterworlds-deployment.json").unlink()
        with pytest.raises(StoreRefused, match="missing or belongs"):
            create_app(remote_settings(env))
        assert _control_row(env, "deployment_initialization") is None
        assert _control_row(env, "deployment_marker") == identity
        _locks_released(env)


def _snapshot(
    harness: RemoteHarness, target: Path, captured: datetime | None = None
) -> str:
    """A snapshot of the live content store plus a bound (empty) vector
    snapshot, inventoried. The app keeps serving, so the live Chroma files are
    not copied here; ``test_remote_storage_cli`` covers the real copy."""
    target.mkdir()
    db = harness.tmp_path / "content.db"
    with (
        closing(sqlite3.connect(db)) as src,
        closing(sqlite3.connect(target / "content.db")) as dst,
    ):
        src.backup(dst)
    store_id = content_store_id(harness.app.state.session_factory)
    bind_vector_store(target / "chroma", store_id)
    return register_backup(
        harness.app.state.control_factory,
        store_id=store_id,
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
        restore_id = restore_snapshot(
            control,
            backup_id,
            database_path=env / "content.db",
            vector_dir=env / "chroma",
            now=datetime.now(UTC),
        )
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
        # A real copy at its own location (one location, one backup).
        shutil.copytree(remote.tmp_path / "b1", remote.tmp_path / "b1-copy")
        later_copy = copy_backup(
            control, b1, storage_locator=str(remote.tmp_path / "b1-copy")
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
        # Captured after the boundary while the content was still present:
        # creation time proves nothing, so it stays affected (review S3).
        after_unproven = register_backup(
            control,
            store_id="s",
            storage_locator="/c",
            original_capture_at=boundary + timedelta(hours=1),
        )
        # Captured after the capture preconditions proved the content absent.
        after_clean = register_backup(
            control,
            store_id="s",
            storage_locator="/e",
            original_capture_at=boundary + timedelta(days=3),
            clean_suppression_ids=[sup],
        )
        copy_of_clean = copy_backup(control, after_clean, storage_locator="/f")
        report = backup_disposition(control, sup, now=boundary)
        assert report.deadline == boundary + timedelta(days=30)
        assert set(report.pending_backup_ids) == {before, broken, after_unproven}
        assert after_clean not in report.pending_backup_ids
        assert copy_of_clean not in report.pending_backup_ids  # copies keep proof
        assert not report.complete and not report.overdue
        for backup in (before, after_unproven):
            dispose_backup(
                control,
                backup,
                now=boundary + timedelta(days=19),
                evidence="removed",
            )
        report = backup_disposition(control, sup, now=boundary + timedelta(days=30))
        # An inaccessible copy that was never proven disposed is a failure,
        # not presumed compliance.
        assert report.unverified_backup_ids == (broken,)
        assert not report.complete and report.overdue
        # Once its removal is proven, the obligation is discharged; the
        # capture's own status stays a record of what the capture was
        # (review R1).
        dispose_backup(
            control, broken, now=boundary + timedelta(days=29), evidence="removed"
        )
        report = backup_disposition(control, sup, now=boundary + timedelta(days=30))
        assert report.pending_backup_ids == report.unverified_backup_ids == ()
        assert report.complete and not report.overdue
        with pytest.raises(ValueError):
            dispose_backup(control, after_clean, now=boundary, evidence="assumed")
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

        # Direct calls with no trusted scope, or another account's, are refused.
        with pytest.raises(StoryAccessDenied):
            guarded_read.retrieve(story, "q")
        with work_scope(DelayedWorkScope(uuid.UUID(b_id), None, "direct")):
            with pytest.raises(StoryAccessDenied):
                guarded_read.retrieve(story, "q")
            with pytest.raises(StoryAccessDenied):
                guarded.ingest_turn(story, uuid.uuid4(), None, "branching", "x", "t")
        assert read.calls == [] and writes.calls == []
        a_scope = work_scope(DelayedWorkScope(uuid.UUID(a_id), None, "direct"))
        a_scope.__enter__()
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
        a_scope.__exit__(None, None, None)

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
        control = remote.app.state.control_factory
        restore_id = begin_restore(
            control, backup, live_database=_live(remote), now=datetime.now(UTC)
        )
        # Verification never accepts a restore whose copy did not finish.
        with pytest.raises(StoreRefused, match="copying"):
            verify_restore(
                control,
                restore_id,
                remote.app.state.session_factory,
                lambda _s: 0,
                now=datetime.now(UTC),
            )
        mark_restore_copied(control, restore_id)
        return restore_id

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
            store_id=content_store_id(remote.app.state.session_factory),
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


class TestBackfillJobMain:
    """The actual ``scripts/retrieval_backfill.py`` entry point, remotely."""

    def _story_with_turns(self, env: Path) -> tuple[RemoteHarness, str, str]:
        from tests.api.test_remote_isolation import _branching_in_play, _seed_hosted

        h = make_remote(env)
        a = h.enroll("a@example.test")
        account = h.account_id(a)
        _seed_hosted(h, account)
        sid = _branching_in_play(a)
        for text in ("I look around.", "I open the door."):
            assert (
                a.post(
                    f"/api/stories/{sid}/turns", json={"user_input": text}
                ).status_code
                == 200
            )
        return h, sid, account

    def _argv(
        self, env: Path, sid: str, account: str, mode: str = "reindex"
    ) -> list[str]:
        return [
            "--story-id",
            sid,
            "--mode",
            mode,
            "--db-url",
            f"sqlite:///{env / 'content.db'}",
            "--account-id",
            account,
        ]

    def _remote_env(self, env: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("AFTERWORLDS_DEPLOYMENT", "remote")
        monkeypatch.setenv(
            "AFTERWORLDS_CONTROL_DATABASE_URL", f"sqlite:///{env / 'control.db'}"
        )

    def test_refused_beside_a_serving_app_and_during_a_pending_restore(
        self, env: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from scripts import retrieval_backfill

        h, sid, account = self._story_with_turns(env)
        self._remote_env(env, monkeypatch)
        with pytest.raises(SystemExit) as exc:
            retrieval_backfill.main(self._argv(env, sid, account))
        assert exc.value.code == 3  # the app holds the store locks
        backup = _snapshot(h, env / "snap")
        h.close()
        begin_restore(
            h.app.state.control_factory,
            backup,
            live_database=env / "content.db",
            now=datetime.now(UTC),
        )
        with pytest.raises(SystemExit) as exc:
            retrieval_backfill.main(self._argv(env, sid, account))
        assert exc.value.code == 3

    def test_closure_between_writes_stops_the_rest(
        self, env: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from afterworlds.pipeline.retrieval.write_service import (
            RetrievalMemoryWriteService,
        )
        from afterworlds.remote.control_orm import HostedAccountORM
        from scripts import retrieval_backfill

        h, sid, account = self._story_with_turns(env)
        control = h.app.state.control_factory
        h.close()
        self._remote_env(env, monkeypatch)
        # The owner's job runs and ingests.
        retrieval_backfill.main(self._argv(env, sid, account, mode="backfill"))
        writes: list[str] = []
        real_ingest = RetrievalMemoryWriteService.ingest_turn

        def ingest_then_close(self: Any, story_id: Any, turn_id: Any, *a: Any) -> None:
            real_ingest(self, story_id, turn_id, *a)
            writes.append(str(turn_id))
            with control.begin() as s:  # the account closes mid-job
                row = s.get(HostedAccountORM, account)
                assert row is not None
                row.status = "closed"

        monkeypatch.setattr(
            RetrievalMemoryWriteService, "ingest_turn", ingest_then_close
        )
        with pytest.raises(SystemExit) as exc:
            retrieval_backfill.main(self._argv(env, sid, account, mode="reindex"))
        assert exc.value.code == 3
        assert len(writes) == 1  # the guard refused every later write

    def test_delete_cleans_orphan_chunks_after_the_story_row_is_gone(
        self,
        env: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from chromadb.api.shared_system_client import SharedSystemClient

        from afterworlds.pipeline.retrieval.client import build_chroma_client
        from afterworlds.pipeline.retrieval.write_service import (
            RetrievalMemoryWriteService,
        )
        from afterworlds.remote.control_orm import HostedAccountORM
        from scripts import retrieval_backfill

        h, sid, account = self._story_with_turns(env)
        b_account = h.account_id(h.enroll("b@example.test"))
        control = h.app.state.control_factory
        # An interrupted deletion removed the SQL Story (bare Story CRUD);
        # its durable ownership and vector chunks survive.
        with h.app.state.session_factory.begin() as s:
            assert delete_story(s, uuid.UUID(sid))
        h.close()
        self._remote_env(env, monkeypatch)

        def chunks() -> int:
            config = retrieval_backfill.build_effective_config(None)
            try:
                return RetrievalMemoryWriteService(
                    build_chroma_client(config), config
                ).count_for_story(uuid.UUID(sid))
            finally:
                SharedSystemClient.clear_system_cache()

        assert chunks() > 0
        with closing(sqlite3.connect(env / "content.db")) as db:
            assert db.execute(
                "SELECT count(*) FROM stories WHERE story_id = ?", (sid,)
            ).fetchone() == (0,)
            owned = db.execute(
                "SELECT account_id FROM account_resources WHERE resource_id = ?",
                (sid,),
            ).fetchall()
        assert owned == [(account,)]

        # Non-owners, a missing account and non-delete modes delete nothing.
        refusals: list[tuple[list[str], int]] = [
            (self._argv(env, sid, b_account, mode="delete"), 3),
            (self._argv(env, sid, account, mode="delete")[:-2], 3),
            (self._argv(env, sid, account, mode="backfill"), 1),
            (self._argv(env, sid, account, mode="reindex"), 1),
        ]
        for argv, code in refusals:
            with pytest.raises(SystemExit) as exc:
                retrieval_backfill.main(argv)
            assert exc.value.code == code, argv
        assert chunks() > 0
        # A Story with no ownership row cannot be targeted either.
        with pytest.raises(SystemExit) as exc:
            retrieval_backfill.main(
                self._argv(env, str(uuid.uuid4()), account, mode="delete")
            )
        assert exc.value.code == 3

        # The owner's cleanup still works once the account is closed (the
        # closure/suppression cleanup path), and a retry is idempotent.
        with control.begin() as s:
            row = s.get(HostedAccountORM, account)
            assert row is not None
            row.status = "closed"
        capsys.readouterr()
        for _ in range(2):
            retrieval_backfill.main(self._argv(env, sid, account, mode="delete"))
            assert "remaining=0" in capsys.readouterr().out
        assert chunks() == 0


def test_the_corpus_baseline_reset_refuses_in_a_remote_deployment(
    env: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    from scripts import reset_corpus_baseline

    make_remote(env).close()
    marker = (env / "chroma" / "afterworlds-deployment.json").read_bytes()
    monkeypatch.setenv("AFTERWORLDS_DEPLOYMENT", "remote")
    monkeypatch.setattr(
        "sys.argv", ["reset", "--db-url", f"sqlite:///{env / 'content.db'}"]
    )
    assert reset_corpus_baseline.main() == 3
    assert "would erase every account's Story memory" in capsys.readouterr().err
    assert (env / "chroma" / "afterworlds-deployment.json").read_bytes() == marker
