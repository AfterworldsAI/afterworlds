"""Migration 0024 against a real alembic run — CRD Issue 5d runtime authority.

The runtime-authority suite installs the append-only triggers by hand, because
``Base.metadata.create_all`` does not create triggers and a suite without them
would prove nothing about the protection production actually has. Hand-mirroring
is exactly how a fixture drifts away from the migration it stands in for, so this
module runs the real migration and asserts the database ends up with the same
trigger set the fixture installs — and that each guard actually refuses what it
claims to.
"""

from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

from afterworlds.persistence.orm.base import Base
from tests.services.rules_authority.conftest import (
    _ENTRY_CONTENT_COLUMNS,
    _trigger_names,
)

REPO_ROOT = Path(__file__).resolve().parents[2]

RETAINED_TABLES = (
    "rp_mech_overrides",
    "rp_override_set_versions",
    "rp_override_set_entries",
    "rp_override_set_scopes",
)


def _alembic(db: Path, *args: str) -> None:
    """Run alembic against *db* through the repository's own migration chain.

    A temporary config is used rather than a ``-x`` argument because this
    repository's ``env.py`` reads the URL from the ini file; pointing it at a
    throwaway database is what keeps the test from migrating the developer's own.
    """
    ini = db.parent / "alembic.ini"
    if not ini.exists():
        source = (REPO_ROOT / "alembic.ini").read_text()
        ini.write_text(
            source.replace(
                "script_location = alembic",
                f"script_location = {REPO_ROOT / 'alembic'}",
            ).replace(
                "sqlalchemy.url = sqlite:///afterworlds.db",
                f"sqlalchemy.url = sqlite:///{db}",
            )
        )
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "-c", str(ini), *args],
        cwd=REPO_ROOT,
        env={**os.environ, "PYTHONPATH": str(REPO_ROOT / "src")},
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:  # pragma: no cover - surfaced only on failure
        raise AssertionError(
            f"alembic {' '.join(args)} failed:\n{result.stdout}\n{result.stderr}"
        )


@pytest.fixture()
def migrated(tmp_path: Path) -> Path:
    """A database built by the real migration chain, not by ``create_all``."""
    db = tmp_path / "migrated.db"
    _alembic(db, "upgrade", "head")
    return db


def _names(db: Path, kind: str) -> set[str]:
    con = sqlite3.connect(db)
    try:
        return {
            row[0]
            for row in con.execute(
                "SELECT name FROM sqlite_master WHERE type = ?", (kind,)
            )
        }
    finally:
        con.close()


def test_the_migration_creates_every_runtime_authority_table(
    migrated: Path,
) -> None:
    assert set(RETAINED_TABLES) <= _names(migrated, "table")


def test_migrated_columns_match_the_orm_exactly(migrated: Path) -> None:
    """A column present in one and not the other is schema drift, not a detail."""
    con = sqlite3.connect(migrated)
    try:
        for table in RETAINED_TABLES:
            in_db = {row[1] for row in con.execute(f"PRAGMA table_info({table})")}
            in_orm = {column.name for column in Base.metadata.tables[table].columns}
            assert in_db == in_orm, f"{table}: {in_db ^ in_orm}"
    finally:
        con.close()


def test_the_migration_installs_exactly_the_fixture_trigger_set(
    migrated: Path,
) -> None:
    """The mirror the suite installs is the set the migration really creates."""
    installed = {name for name in _names(migrated, "trigger") if "override_set" in name}
    assert installed == set(_trigger_names())


def test_the_version_table_has_no_owning_foreign_key(migrated: Path) -> None:
    """Shared content must not be tied to one package's lifecycle."""
    con = sqlite3.connect(migrated)
    try:
        fks = list(con.execute("PRAGMA foreign_key_list(rp_override_set_versions)"))
    finally:
        con.close()
    assert fks == []


def test_downgrade_removes_every_table_and_trigger(migrated: Path) -> None:
    _alembic(migrated, "downgrade", "0023")
    assert not (set(RETAINED_TABLES) & _names(migrated, "table"))
    assert not {n for n in _names(migrated, "trigger") if "override_set" in n}
    # The preceding migration's objects survive.
    assert "rp_mech_active_projections" in _names(migrated, "table")
    assert "rp_mech_projections" in _names(migrated, "table")


def test_upgrade_downgrade_upgrade_is_clean(migrated: Path) -> None:
    _alembic(migrated, "downgrade", "0023")
    _alembic(migrated, "upgrade", "head")
    assert set(RETAINED_TABLES) <= _names(migrated, "table")
    assert {n for n in _names(migrated, "trigger") if "override_set" in n} == set(
        _trigger_names()
    )


# ---------------------------------------------------------------------------
# The guards, exercised against the migrated database itself
# ---------------------------------------------------------------------------


def _seed(con: sqlite3.Connection) -> None:
    con.execute("PRAGMA foreign_keys=ON")
    con.execute(
        "INSERT INTO rp_packages (rules_package_id, name, system, version,"
        " is_enabled, publication_status, published_at, created_at, updated_at)"
        " VALUES ('pkg', 'p', 'd20', '1', 1, 'published', 't', 't', 't')"
    )
    con.execute("INSERT INTO rp_override_set_versions VALUES ('v1', 1, 't0')")
    con.execute(
        "INSERT INTO rp_override_set_entries (override_set_uuid, apply_order,"
        " override_id, override_origin, target_kind, target_record_key,"
        " target_component_key, target_fact_key, override_operation, precedence,"
        " is_enabled, payload) VALUES ('v1', 0, 'o', 'house_rule', 'record',"
        " 'r', NULL, NULL, 'disable', 1, 1, '{}')"
    )
    con.execute("INSERT INTO rp_override_set_scopes VALUES ('v1', 'pkg', 'rel', 't0')")


@pytest.mark.parametrize(
    ("label", "sql"),
    [
        ("version update", "UPDATE rp_override_set_versions SET entry_count = 9"),
        ("version delete", "DELETE FROM rp_override_set_versions"),
        (
            "version differing replace",
            "INSERT OR REPLACE INTO rp_override_set_versions VALUES ('v1', 9, 't1')",
        ),
        ("entry update", "UPDATE rp_override_set_entries SET precedence = 9"),
        ("entry delete", "DELETE FROM rp_override_set_entries"),
        (
            "entry differing replace",
            "INSERT OR REPLACE INTO rp_override_set_entries (override_set_uuid,"
            " apply_order, override_id, override_origin, target_kind,"
            " target_record_key, target_component_key, target_fact_key,"
            " override_operation, precedence, is_enabled, payload) VALUES ('v1',"
            " 0, 'forged', 'house_rule', 'record', 'r', NULL, NULL, 'disable',"
            " 1, 1, '{}')",
        ),
        (
            "entry appended past the seal",
            "INSERT INTO rp_override_set_entries (override_set_uuid, apply_order,"
            " override_id, override_origin, target_kind, target_record_key,"
            " target_component_key, target_fact_key, override_operation,"
            " precedence, is_enabled, payload) VALUES ('v1', 1, 'extra',"
            " 'house_rule', 'record', 'r', NULL, NULL, 'disable', 1, 1, '{}')",
        ),
        ("scope update", "UPDATE rp_override_set_scopes SET package_uuid = 'other'"),
        ("scope delete while package live", "DELETE FROM rp_override_set_scopes"),
    ],
)
def test_the_migrated_guards_refuse_every_rewrite_path(
    migrated: Path, label: str, sql: str
) -> None:
    """Asserted against the real migrated schema, not the fixture's mirror."""
    con = sqlite3.connect(migrated)
    try:
        _seed(con)
        with pytest.raises(sqlite3.IntegrityError):
            con.execute(sql)
    finally:
        con.close()


def test_the_entry_guard_covers_the_new_option_scope_column(
    migrated: Path,
) -> None:
    """PR #155: a content column outside the guard is content it cannot protect.

    ``prevent_rp_override_set_entries_reinsert`` names its columns explicitly,
    so adding ``target_option_key`` without recreating the trigger would leave
    the option scope of a retained entry silently rewritable. The trigger-set
    test above compares *names* only and would not have caught it.
    """
    con = sqlite3.connect(migrated)
    try:
        _seed(con)
        # ``INSERT OR REPLACE``, like the sibling case above: a plain INSERT
        # violates ``uq_rp_override_set_entry_order`` on its own, so it would
        # raise whether or not the trigger covers the column.
        with pytest.raises(sqlite3.IntegrityError):
            con.execute(
                "INSERT OR REPLACE INTO rp_override_set_entries (override_set_uuid,"
                " apply_order, override_id, override_origin, target_kind,"
                " target_record_key, target_component_key, target_fact_key,"
                " target_option_key, override_operation, precedence, is_enabled,"
                " payload) VALUES ('v1', 0, 'o', 'house_rule', 'record', 'r',"
                " NULL, NULL, 'forged-option', 'disable', 1, 1, '{}')"
            )
    finally:
        con.close()


#: Every guard ``0024`` attaches to the retained-entry table. A downgrade that
#: rebuilds that table must leave all four standing, not only the one whose
#: column set the migration changed.
_ENTRY_TRIGGERS = (
    "prevent_rp_override_set_entries_update",
    "prevent_rp_override_set_entries_delete",
    "prevent_rp_override_set_entries_reinsert",
    "seal_rp_override_set_entries",
)


def _entry_triggers_on(db: Path) -> set[str]:
    return {n for n in _names(db, "trigger") if "override_set_entries" in n}


@pytest.mark.parametrize("direction", ["upgrade", "downgrade"])
def test_the_0028_boundary_leaves_every_retained_entry_guard_standing(
    tmp_path: Path, direction: str
) -> None:
    """PR #155 round 4: the 0028<->0027 boundary, not the chain through 0024.

    SQLite implements ``DROP COLUMN`` by rebuilding the table, and a rebuild
    drops every trigger attached to the old one. Downgrading only 0028
    restored just the re-insert guard, leaving retained evidence updatable,
    deletable, and extendable past its seal.

    This asserts the boundary directly. The existing downgrade test walks to
    0023, where the table no longer exists — which is exactly why the gap was
    invisible.
    """
    db = tmp_path / "boundary.db"
    _alembic(db, "upgrade", "0027")
    _alembic(db, "upgrade", "0028")
    if direction == "downgrade":
        _alembic(db, "downgrade", "0027")
    assert _entry_triggers_on(db) == set(_ENTRY_TRIGGERS)


def test_the_downgraded_guards_still_refuse_every_rewrite_path(
    tmp_path: Path,
) -> None:
    """Presence is not the claim; refusal is.

    A recreated trigger whose SQL was weakened would still be *named* in
    ``sqlite_master``. Each of the four is therefore exercised through the
    behaviour it exists to refuse, on a database that has actually been rolled
    back from 0028 to 0027.
    """
    db = tmp_path / "rolled-back.db"
    _alembic(db, "upgrade", "0028")
    _alembic(db, "downgrade", "0027")

    con = sqlite3.connect(db)
    try:
        _seed(con)
        attempts = {
            "update": "UPDATE rp_override_set_entries SET precedence = 9",
            "delete": "DELETE FROM rp_override_set_entries",
            "conflicting reinsert": (
                "INSERT OR REPLACE INTO rp_override_set_entries (override_set_uuid,"
                " apply_order, override_id, override_origin, target_kind,"
                " target_record_key, target_component_key, target_fact_key,"
                " override_operation, precedence, is_enabled, payload) VALUES"
                " ('v1', 0, 'forged', 'house_rule', 'record', 'r', NULL, NULL,"
                " 'disable', 1, 1, '{}')"
            ),
            "extension past the seal": (
                "INSERT INTO rp_override_set_entries (override_set_uuid,"
                " apply_order, override_id, override_origin, target_kind,"
                " target_record_key, target_component_key, target_fact_key,"
                " override_operation, precedence, is_enabled, payload) VALUES"
                " ('v1', 1, 'extra', 'house_rule', 'record', 'r', NULL, NULL,"
                " 'disable', 1, 1, '{}')"
            ),
        }
        for label, sql in attempts.items():
            with pytest.raises(sqlite3.IntegrityError):
                con.execute(sql)
                pytest.fail(f"{label} was not refused after rollback")
    finally:
        con.close()


def test_the_downgraded_reinsert_guard_sheds_only_the_dropped_column(
    tmp_path: Path,
) -> None:
    """0027's guard must cover 0027's columns — no more, no less.

    Recreating the family must not smuggle ``target_option_key`` back into a
    schema that no longer has the column, which would make every retained
    insert fail on an unknown identifier.
    """
    db = tmp_path / "shed.db"
    _alembic(db, "upgrade", "0028")
    _alembic(db, "downgrade", "0027")
    con = sqlite3.connect(db)
    try:
        (sql,) = con.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'trigger' AND name = "
            "'prevent_rp_override_set_entries_reinsert'"
        ).fetchone()
    finally:
        con.close()
    assert "target_option_key" not in sql
    for column in _ENTRY_CONTENT_COLUMNS:
        if column != "target_option_key":
            assert f"{column} IS NOT NEW.{column}" in sql


def test_the_fixture_mirror_guards_every_column_the_migration_guards(
    migrated: Path,
) -> None:
    """The suite's trigger mirror and the migration must name the same columns.

    They are two hand-maintained copies of one guard, and the trigger-set test
    above compares only *names*. If they drift, every retention and
    override-set test runs against a guard the production schema does not
    have — and passes, silently.
    """
    con = sqlite3.connect(migrated)
    try:
        (sql,) = con.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'trigger' AND name = "
            "'prevent_rp_override_set_entries_reinsert'"
        ).fetchone()
    finally:
        con.close()
    missing = [c for c in _ENTRY_CONTENT_COLUMNS if f"{c} IS NOT NEW.{c}" not in sql]
    assert not missing, f"migrated guard does not cover {missing}"


def test_an_identical_reinsert_is_permitted_on_the_migrated_schema(
    migrated: Path,
) -> None:
    """The other half of the design: benign repeats must pass.

    A guard that also refused these would make the service's
    ``ON CONFLICT DO NOTHING`` retention fail under concurrency, which is the
    coupling this migration and :mod:`retention` are designed around.
    """
    con = sqlite3.connect(migrated)
    try:
        _seed(con)
        con.execute(
            "INSERT INTO rp_override_set_versions VALUES ('v1', 1, 't9')"
            " ON CONFLICT DO NOTHING"
        )
        con.execute(
            "INSERT INTO rp_override_set_entries (override_set_uuid, apply_order,"
            " override_id, override_origin, target_kind, target_record_key,"
            " target_component_key, target_fact_key, override_operation,"
            " precedence, is_enabled, payload) VALUES ('v1', 0, 'o',"
            " 'house_rule', 'record', 'r', NULL, NULL, 'disable', 1, 1, '{}')"
            " ON CONFLICT DO NOTHING"
        )
        con.execute(
            "INSERT INTO rp_override_set_scopes VALUES ('v1', 'pkg', 'rel', 't9')"
            " ON CONFLICT DO NOTHING"
        )
        assert con.execute(
            "SELECT recorded_at FROM rp_override_set_versions"
        ).fetchone() == ("t0",)
        assert (
            con.execute("SELECT COUNT(*) FROM rp_override_set_entries").fetchone()[0]
            == 1
        )
    finally:
        con.close()


# ---------------------------------------------------------------------------
# `INSERT OR REPLACE` at an *identical* entry_count
# ---------------------------------------------------------------------------
#
# The content-aware guard lets that statement past on purpose — refusing it would
# also refuse the service's `ON CONFLICT DO NOTHING`. What stops it from wiping
# the version's children is a second mechanism, and the distinction is subtle
# enough to be worth pinning: REPLACE's own conflict-resolution delete skips
# BEFORE DELETE triggers while `recursive_triggers` is off, but the foreign-key
# CASCADE it sets off does *not* — the children's own DELETE guards fire and
# abort the statement. These assert that state by state instead of reasoning
# about it.


def _seed_state(
    con: sqlite3.Connection, *, entries: int, scope: bool, live_package: bool
) -> None:
    con.execute("PRAGMA foreign_keys=ON")
    if scope or live_package:
        con.execute(
            "INSERT INTO rp_packages (rules_package_id, name, system, version,"
            " is_enabled, publication_status, published_at, created_at, updated_at)"
            " VALUES ('pkg', 'p', 'd20', '1', 1, 'published', 't', 't', 't')"
        )
    con.execute(
        "INSERT INTO rp_override_set_versions VALUES ('v1', ?, 't0')", (entries,)
    )
    for order in range(entries):
        con.execute(
            "INSERT INTO rp_override_set_entries (override_set_uuid, apply_order,"
            " override_id, override_origin, target_kind, target_record_key,"
            " target_component_key, target_fact_key, override_operation, precedence,"
            " is_enabled, payload) VALUES ('v1', ?, 'o', 'house_rule', 'record',"
            " 'r', NULL, NULL, 'disable', 1, 1, '{}')",
            (order,),
        )
    if scope:
        con.execute(
            "INSERT INTO rp_override_set_scopes VALUES ('v1', 'pkg', 'rel', 't0')"
        )
    if not live_package:
        con.execute("DELETE FROM rp_packages WHERE rules_package_id = 'pkg'")


def _row_counts(con: sqlite3.Connection) -> tuple[int, int, int]:
    return tuple(  # type: ignore[return-value]
        con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        for table in RETAINED_TABLES[1:]
    )


@pytest.mark.parametrize(
    ("label", "entries", "scope", "live_package"),
    [
        ("entries and scope, package live", 1, True, True),
        ("entries and scope, package deleted", 1, True, False),
        ("entries, association already gone", 1, False, False),
        ("empty set with a scope", 0, True, True),
    ],
)
def test_an_identical_count_replace_cannot_destroy_retained_evidence(
    migrated: Path, label: str, entries: int, scope: bool, live_package: bool
) -> None:
    """Refused in every state where there is retained evidence to destroy."""
    con = sqlite3.connect(migrated)
    try:
        _seed_state(con, entries=entries, scope=scope, live_package=live_package)
        before = _row_counts(con)
        with pytest.raises(sqlite3.IntegrityError):
            con.execute(
                "INSERT OR REPLACE INTO rp_override_set_versions"
                " VALUES ('v1', ?, 'forged')",
                (entries,),
            )
        assert _row_counts(con) == before
        assert con.execute(
            "SELECT recorded_at FROM rp_override_set_versions"
        ).fetchone() == ("t0",)
    finally:
        con.close()


def test_a_childless_header_is_the_only_replaceable_shape_and_is_inert(
    migrated: Path,
) -> None:
    """The residue, stated exactly rather than left as an unknown.

    A header with no entries and no association has nothing to cascade into, so
    the replacement lands. It is inert: retention never produces this shape — the
    scope is written in the same unit — the entry count cannot move without
    tripping the content-aware guard, and the one column that does change is the
    ``recorded_at`` audit stamp, which ADR-005d Decision 9 keeps outside identity.
    Such a version already fails replay closed for want of a scope.
    """
    con = sqlite3.connect(migrated)
    try:
        _seed_state(con, entries=0, scope=False, live_package=False)
        con.execute(
            "INSERT OR REPLACE INTO rp_override_set_versions VALUES ('v1', 0, 'forged')"
        )
        assert con.execute(
            "SELECT override_set_uuid, entry_count FROM rp_override_set_versions"
        ).fetchall() == [("v1", 0)]
        # And the count still cannot be moved, which is what identity rests on.
        with pytest.raises(sqlite3.IntegrityError):
            con.execute(
                "INSERT OR REPLACE INTO rp_override_set_versions"
                " VALUES ('v1', 3, 'forged')"
            )
    finally:
        con.close()


def test_package_deletion_cascades_the_scope_association(migrated: Path) -> None:
    """The contractual carve-out the delete guard is conditional on."""
    con = sqlite3.connect(migrated)
    try:
        _seed(con)
        con.execute("DELETE FROM rp_packages WHERE rules_package_id = 'pkg'")
        assert (
            con.execute("SELECT COUNT(*) FROM rp_override_set_scopes").fetchone()[0]
            == 0
        )
        # The shared content itself is untouched by that cascade.
        assert (
            con.execute("SELECT COUNT(*) FROM rp_override_set_versions").fetchone()[0]
            == 1
        )
    finally:
        con.close()
