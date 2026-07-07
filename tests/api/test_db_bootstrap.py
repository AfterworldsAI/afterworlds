"""P1 regression: create_app() bootstraps via real Alembic migrations.

Prior to this fix, create_app() called Base.metadata.create_all(engine)
against whatever ORM modules app.py happened to import at module scope. That
skipped every Alembic-only DDL statement -- including the append-only audit
triggers on entitlement_event, provider_refusal_log, and rpg_roll_audit -- and
could omit tables entirely for ORM modules app.py never imported (entitlement,
provider refusal log, story bible, rules package, rolling summary). These
tests exercise the real create_app() path end-to-end, not a hand-built
migration harness.
"""

from __future__ import annotations

import uuid
from datetime import datetime

import sqlalchemy as sa

from afterworlds.api.app import create_app


def test_create_app_bootstraps_to_alembic_head(app_settings) -> None:  # type: ignore[no-untyped-def]
    create_app(app_settings)

    engine = sa.create_engine(app_settings.database_url)
    try:
        with engine.connect() as conn:
            row = conn.execute(
                sa.text("SELECT version_num FROM alembic_version")
            ).fetchone()
        assert row is not None

        from alembic.config import Config
        from alembic.script import ScriptDirectory

        cfg = Config("alembic.ini")
        script = ScriptDirectory.from_config(cfg)
        assert row[0] == script.get_current_head()
    finally:
        engine.dispose()


def test_create_app_bootstrap_includes_tables_app_py_never_imports(
    app_settings,  # type: ignore[no-untyped-def]
) -> None:
    """Regression for the exact gap Codex found: app.py's old mass-import
    list omitted entitlement/provider-refusal/story-bible/rules-package/
    rolling-summary ORM modules, so create_all() never saw those tables."""
    create_app(app_settings)

    engine = sa.create_engine(app_settings.database_url)
    try:
        inspector = sa.inspect(engine)
        table_names = set(inspector.get_table_names())
    finally:
        engine.dispose()

    for table in (
        "entitlement_event",
        "runtime_entitlement_state",
        "provider_refusal_log",
        "rpg_roll_audit",
        "sb_settings",
        "rp_packages",
    ):
        assert table in table_names, f"{table!r} missing after create_app() bootstrap"


def test_create_app_bootstrap_installs_append_only_triggers(
    app_settings,  # type: ignore[no-untyped-def]
) -> None:
    """Direct UPDATE/DELETE on entitlement_event is rejected by the DB-layer
    trigger created by migration 0009 -- proving create_app() actually ran
    that migration's op.execute() trigger DDL, not just its op.create_table()."""
    create_app(app_settings)

    engine = sa.create_engine(app_settings.database_url)
    try:
        with engine.connect() as conn:
            triggers = {
                row[0]
                for row in conn.execute(
                    sa.text("SELECT name FROM sqlite_master WHERE type = 'trigger'")
                ).fetchall()
            }
            assert "prevent_entitlement_event_update" in triggers
            assert "prevent_entitlement_event_delete" in triggers
            assert "prevent_provider_refusal_log_update" in triggers
            assert "prevent_provider_refusal_log_delete" in triggers
            assert "prevent_rpg_roll_audit_update" in triggers
            assert "prevent_rpg_roll_audit_delete" in triggers

            conn.execute(
                sa.text(
                    "INSERT INTO entitlement_event"
                    " (event_id, sojourner_id, event_type, payload_json, created_at)"
                    " VALUES (:eid, :sid, 'grant', '{}', :now)"
                ),
                {
                    "eid": str(uuid.uuid4()),
                    "sid": str(uuid.uuid4()),
                    "now": datetime.now(),
                },
            )
            conn.commit()

            try:
                conn.execute(
                    sa.text("UPDATE entitlement_event SET event_type = 'tampered'")
                )
                conn.commit()
                raised = False
            except sa.exc.IntegrityError:
                conn.rollback()
                raised = True
            assert raised, "entitlement_event UPDATE should be blocked by trigger"

            try:
                conn.execute(sa.text("DELETE FROM entitlement_event"))
                conn.commit()
                raised = False
            except sa.exc.IntegrityError:
                conn.rollback()
                raised = True
            assert raised, "entitlement_event DELETE should be blocked by trigger"
    finally:
        engine.dispose()
