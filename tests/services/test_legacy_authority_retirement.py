"""Final CRD Issue 5d cutover, blocker 2 — the legacy authority is retired.

#137 contract 6 and AC22 require the obsolete prose-only ``MechanicalEntity``
family (with its ORM/table, constructors and callers) and the legacy
chunk/entity override authority to be removed at final cutover, with a
clean-checkout migration and no surviving production caller. These tests prove
the removal from four directions:

* **Surface** — the retired names are gone from the modules that defined them.
* **Code** — no source module names a retired identifier as code (a tokenizer
  scan, so docstrings and comments that record the history do not count).
* **Metadata** — the ORM registers neither table.
* **Migration 0037** — on throwaway SQLite stores. A 0036 store holding
  FK-valid current authority (a published, activated projection; a typed
  override; a retained override-set version with its entries and scope) beside
  pre-release legacy rows is upgraded by the final step alone, with SQLite
  foreign-key enforcement switched on for that migration's connection. Exactly
  the two legacy tables go; every other table's schema and rows are unchanged;
  the store stays FK-consistent; and the retained binding still replays through
  the existing reader. Downgrading recreates the 0036 schema for the legacy
  tables, empty; and the head schema's ``rp_*`` tables equal the ORM's.

The live runtime store is never opened here.
"""

from __future__ import annotations

import io
import tokenize
from pathlib import Path
from uuid import UUID

import pytest
import sqlalchemy as sa
from alembic.config import Config

import afterworlds.ingestion.ingestion_service as ingestion_service
import afterworlds.ingestion.srd_parser as srd_parser
import afterworlds.models.enums as enums
import afterworlds.models.rules_package as rp_models
import afterworlds.persistence.orm.corpus  # noqa: F401
import afterworlds.persistence.orm.mechanical  # noqa: F401
import afterworlds.persistence.orm.rules_authority  # noqa: F401
import afterworlds.persistence.orm.rules_package as rp_orm
from afterworlds.models.enums import OverrideOperationEnum
from afterworlds.models.rules_package import RulesPackageBinding
from afterworlds.persistence.database import create_engine, create_session_factory
from afterworlds.persistence.orm.base import Base
from afterworlds.services.rules_authority import (
    AuthorityOutcome,
    RulesAuthorityService,
)
from afterworlds.services.rules_package import RulesPackageService
from alembic import command
from tests.services.rules_authority.conftest import (
    DESCRIPTOR_FACT_TARGET,
    DISABLE_PAYLOAD,
    NOW,
    PACKAGE_UUID,
    RELEASE_VERSION,
    _publish_bounded_projection,
    _seed_release,
    author_override,
)

_REPO = Path(__file__).resolve().parents[2]
_LEGACY_TABLES = ("rp_mechanical_entities", "rp_overrides")
_RETIRED_MODEL_NAMES = (
    "MechanicalEntity",
    "SpellEntity",
    "ConditionEntity",
    "StatBlockEntity",
    "ActionEntity",
    "ItemEntity",
    "EntityData",
    "RuleOverride",
    "ChunkOverridePayload",
    "AppliedChunk",
    "AppliedEntity",
)
_RETIRED_IDENTIFIERS = frozenset(
    _RETIRED_MODEL_NAMES
    + (
        "MechanicalEntityORM",
        "RuleOverrideORM",
        "MechanicalEntityTypeEnum",
        "ParsedEntity",
        "parse_entities",
        "_persist_entities",
        "get_entity_by_type_and_name",
        "get_overrides_for_chunk",
        "get_overrides_for_entity",
        "resolve_slice_package",
        "_apply_chunk_overrides",
        "entity_refs",
        "subsystem_tags",
    )
)


# ---------------------------------------------------------------------------
# Surface and code
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("name", _RETIRED_MODEL_NAMES)
def test_the_retired_model_is_gone(name: str) -> None:
    assert not hasattr(rp_models, name)


def test_the_retired_orm_enum_parser_and_service_members_are_gone() -> None:
    assert not hasattr(rp_orm, "MechanicalEntityORM")
    assert not hasattr(rp_orm, "RuleOverrideORM")
    assert not hasattr(enums, "MechanicalEntityTypeEnum")
    assert not hasattr(srd_parser, "ParsedEntity")
    assert not hasattr(srd_parser.SRDParser, "parse_entities")
    assert not hasattr(ingestion_service.IngestionService, "_persist_entities")
    for member in (
        "get_entity_by_type_and_name",
        "get_overrides_for_chunk",
        "get_overrides_for_entity",
        "resolve_slice_package",
        "_apply_chunk_overrides",
    ):
        assert not hasattr(RulesPackageService, member), member
    # The retired selectors are no longer request fields.
    assert {"subsystem_tags", "entity_refs", "include_non_published"}.isdisjoint(
        rp_models.RuleSliceRequest.model_fields
    )


def test_no_source_module_names_a_retired_identifier_as_code() -> None:
    """Docstrings and comments record the history; code may not use it."""
    offenders: list[str] = []
    for path in sorted((_REPO / "src" / "afterworlds").rglob("*.py")):
        source = path.read_text(encoding="utf-8")
        for token in tokenize.generate_tokens(io.StringIO(source).readline):
            if token.type == tokenize.NAME and token.string in _RETIRED_IDENTIFIERS:
                offenders.append(
                    f"{path.relative_to(_REPO)}:{token.start[0]} {token.string}"
                )
    assert offenders == []


def test_the_orm_registers_neither_legacy_table() -> None:
    for table in _LEGACY_TABLES:
        assert table not in Base.metadata.tables


# ---------------------------------------------------------------------------
# Migration 0037 on throwaway stores
# ---------------------------------------------------------------------------


def _cfg(db: Path) -> Config:
    cfg = Config(str(_REPO / "alembic.ini"))
    cfg.set_main_option("script_location", str(_REPO / "alembic"))
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db.as_posix()}")
    return cfg


def _engine(db: Path) -> sa.Engine:
    return sa.create_engine(f"sqlite:///{db.as_posix()}")


def _schema(db: Path) -> dict[str, str | None]:
    """``sqlite_master`` entries (tables, indexes, triggers) by name."""
    engine = _engine(db)
    with engine.connect() as conn:
        rows = conn.execute(
            sa.text(
                "SELECT name, sql FROM sqlite_master WHERE name != 'sqlite_sequence'"
            )
        ).all()
    engine.dispose()
    return {name: sql for name, sql in rows}


def _table_rows(db: Path) -> dict[str, list[tuple[object, ...]]]:
    engine = _engine(db)
    with engine.connect() as conn:
        names = [
            r[0]
            for r in conn.execute(
                sa.text("SELECT name FROM sqlite_master WHERE type = 'table'")
            )
        ]
        out = {
            name: sorted(
                (tuple(r) for r in conn.execute(sa.text(f'SELECT * FROM "{name}"'))),
                key=repr,
            )
            for name in names
        }
    engine.dispose()
    return out


_STAMP = "2026-10-10T00:00:00+00:00"


def _seed_legacy_rows(db: Path) -> None:
    """Pre-release development rows of both legacy families, plus source rows."""
    engine = _engine(db)
    with engine.begin() as conn:
        conn.execute(
            sa.text(
                "INSERT INTO rp_packages (rules_package_id, name, system, version, "
                "is_enabled, publication_status, created_at, updated_at) VALUES "
                "('pkg-1', 'Dev package', 'd20', 'dev-1', 1, 'draft', :s, :s)"
            ),
            {"s": _STAMP},
        )
        conn.execute(
            sa.text(
                "INSERT INTO rp_sources (source_id, rules_package_id, name, category, "
                "precedence_rank, is_enabled, created_at) VALUES "
                "('src-1', 'pkg-1', 'SRD', 'core_rulebook', 1, 1, :s)"
            ),
            {"s": _STAMP},
        )
        conn.execute(
            sa.text(
                "INSERT INTO rp_chunks (chunk_id, rules_package_id, source_id, "
                "subsystem, content, source_document, source_locator_type, "
                "source_locator_value, is_enabled, created_at) VALUES "
                "('chunk-1', 'pkg-1', 'src-1', 'conditions', 'Blinded.', 'SRD', "
                "'page', '177', 1, :s)"
            ),
            {"s": _STAMP},
        )
        conn.execute(
            sa.text(
                "INSERT INTO rp_mechanical_entities (entity_id, rules_package_id, "
                "source_id, entity_type, name, structured_data, source_document, "
                "source_locator_type, source_locator_value, is_enabled, created_at) "
                "VALUES ('ent-1', 'pkg-1', 'src-1', 'condition', 'Blinded', "
                "'{\"effects\": []}', 'SRD', 'page', '177', 1, :s)"
            ),
            {"s": _STAMP},
        )
        for override_id, chunk, entity in (
            ("ovr-chunk", "chunk-1", None),
            ("ovr-entity", None, "ent-1"),
        ):
            conn.execute(
                sa.text(
                    "INSERT INTO rp_overrides (override_id, rules_package_id, "
                    "target_chunk_id, target_entity_id, override_origin, "
                    "override_operation, override_payload, precedence, is_enabled, "
                    "created_at) VALUES (:o, 'pkg-1', :c, :e, 'house_rule', "
                    "'replace', '{\"content\": \"x\"}', 1, 1, :s)"
                ),
                {"o": override_id, "c": chunk, "e": entity, "s": _STAMP},
            )
    engine.dispose()


def _revision(db: Path) -> str:
    engine = _engine(db)
    with engine.connect() as conn:
        (version,) = conn.execute(
            sa.text("SELECT version_num FROM alembic_version")
        ).one()
    engine.dispose()
    return str(version)


#: Current authority the cutover must leave untouched: a populated row in each
#: proves the before/after comparison is not vacuous.
_PROTECTED_TABLES = (
    "rp_packages",
    "rp_sources",
    "rp_chunks",
    "rp_corpus_releases",
    "rp_mech_projections",
    "rp_mech_records",
    "rp_mech_components",
    "rp_mech_facts",
    "rp_mech_prose_bindings",
    "rp_mech_provenance",
    "rp_mech_active_projections",
    "rp_mech_overrides",
    "rp_override_set_versions",
    "rp_override_set_entries",
    "rp_override_set_scopes",
)
_OVERRIDE_ID = "migration-0037-disable-descriptor-fact"


def _seed_current_authority(db: Path) -> RulesPackageBinding:
    """Published, activated authority with a typed override and its retained version.

    Built with the bounded runtime fixture's own builders (the genuine
    publish/activate path), not the accepted production corpus.
    """
    engine = create_engine(f"sqlite:///{db.as_posix()}")
    try:
        with create_session_factory(engine)() as session:
            root = _seed_release(session, PACKAGE_UUID, RELEASE_VERSION)
            _publish_bounded_projection(session, root)
            author_override(
                session,
                override_id=_OVERRIDE_ID,
                target=DESCRIPTOR_FACT_TARGET,
                operation=OverrideOperationEnum.DISABLE,
                payload=DISABLE_PAYLOAD,
            )
            resolved = RulesAuthorityService(session, now=NOW).resolve(
                package_uuid=UUID(PACKAGE_UUID)
            )
            assert resolved.outcome is AuthorityOutcome.RESOLVED, resolved.detail
            assert resolved.binding is not None
            session.commit()
            return resolved.binding
    finally:
        engine.dispose()


def _foreign_key_violations(db: Path) -> list[tuple[object, ...]]:
    engine = _engine(db)
    with engine.connect() as conn:
        rows = [tuple(r) for r in conn.execute(sa.text("PRAGMA foreign_key_check"))]
    engine.dispose()
    return rows


def _upgrade_with_foreign_keys(db: Path) -> list[int]:
    """Run ``upgrade head`` with ``PRAGMA foreign_keys=ON`` on its connections.

    A connect hook scoped to this call only and removed in ``finally``: the store
    is already at 0036, so it imposes nothing on historical migration steps,
    and it changes no global Alembic configuration. Returns the enforcement
    state each migration connection reported.
    """
    states: list[int] = []

    def enforce(dbapi_connection: object, _record: object) -> None:
        cursor = dbapi_connection.cursor()  # type: ignore[attr-defined]
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA foreign_keys")
        states.append(int(cursor.fetchone()[0]))
        cursor.close()

    sa.event.listen(sa.engine.Engine, "connect", enforce)
    try:
        command.upgrade(_cfg(db), "head")
    finally:
        sa.event.remove(sa.engine.Engine, "connect", enforce)
    return states


def test_0037_drops_exactly_the_legacy_tables_and_keeps_everything_else(
    tmp_path: Path,
) -> None:
    db = tmp_path / "upgrade.db"
    command.upgrade(_cfg(db), "0036")
    binding = _seed_current_authority(db)
    _seed_legacy_rows(db)
    schema_before = _schema(db)
    rows_before = _table_rows(db)
    assert len(rows_before["rp_mechanical_entities"]) == 1
    assert len(rows_before["rp_overrides"]) == 2
    empty = [table for table in _PROTECTED_TABLES if not rows_before[table]]
    assert empty == [], f"comparison would be vacuous for {empty}"
    assert _foreign_key_violations(db) == []

    states = _upgrade_with_foreign_keys(db)
    assert states and set(states) == {1}, states

    assert _revision(db) == "0037"
    schema_after = _schema(db)
    rows_after = _table_rows(db)
    for table in _LEGACY_TABLES:
        assert table not in schema_after
        assert table not in rows_after
    # Every other table, index and trigger is byte-identical, and every other
    # row survives: the source corpus is kept, the legacy rows are not guessed
    # into anything.
    expected_schema = {
        name: sql
        for name, sql in schema_before.items()
        if not any(name == t or t in name for t in _LEGACY_TABLES)
        and "rp_entities" not in name
    }
    assert {
        name: sql for name, sql in schema_after.items() if name in expected_schema
    } == expected_schema
    assert set(schema_after) == set(expected_schema)
    for table, rows in rows_before.items():
        if table in _LEGACY_TABLES or table == "alembic_version":
            continue
        assert rows_after[table] == rows, table
    assert "Blinded." in {row[4] for row in rows_after["rp_chunks"]}
    assert _foreign_key_violations(db) == []

    # The retained binding still reconstructs, with its override, through the
    # existing reader; and it is still the current binding at runtime.
    engine = create_engine(f"sqlite:///{db.as_posix()}")
    try:
        with create_session_factory(engine)() as session:
            service = RulesAuthorityService(session, now=NOW)
            replayed = service.replay(binding)
            assert replayed.binding == binding
            assert [(o.override_id, o.applied) for o in replayed.applied_overrides] == [
                (_OVERRIDE_ID, True)
            ]
            current = service.resolve(
                package_uuid=binding.package_uuid, recorded=binding, retain=False
            )
            assert current.outcome is AuthorityOutcome.RESOLVED, current.detail
            assert current.binding == binding
            session.rollback()
    finally:
        engine.dispose()


def test_0037_downgrade_recreates_the_0036_schema_empty_and_reupgrades(
    tmp_path: Path,
) -> None:
    reference = tmp_path / "reference-0036.db"
    command.upgrade(_cfg(reference), "0036")
    reference_schema = _schema(reference)

    db = tmp_path / "roundtrip.db"
    command.upgrade(_cfg(db), "0036")
    _seed_legacy_rows(db)
    command.upgrade(_cfg(db), "head")
    command.downgrade(_cfg(db), "0036")

    assert _revision(db) == "0036"
    assert _schema(db) == reference_schema
    rows = _table_rows(db)
    # The schema returns; the deleted pre-release rows do not.
    assert rows["rp_mechanical_entities"] == []
    assert rows["rp_overrides"] == []
    assert len(rows["rp_chunks"]) == 1

    command.upgrade(_cfg(db), "head")
    assert _revision(db) == "0037"
    assert set(_LEGACY_TABLES).isdisjoint(_schema(db))


def test_the_head_schema_rules_package_tables_equal_the_orm(tmp_path: Path) -> None:
    """Installed metadata behaviour: the migrated ``rp_*`` set is the ORM's."""
    db = tmp_path / "head.db"
    command.upgrade(_cfg(db), "head")
    engine = _engine(db)
    installed = {n for n in sa.inspect(engine).get_table_names() if n.startswith("rp_")}
    engine.dispose()
    registered = {n for n in Base.metadata.tables if n.startswith("rp_")}
    assert installed == registered
    assert set(_LEGACY_TABLES).isdisjoint(installed)
