"""Tests for Rules Package schema, models, and service — CRD Issue 5a.

Acceptance criteria verified:
  AC-RP-001  rp_* table prefix — all five tables registered
  AC-RP-002  No rp_* FK to non-rp_* tables (also in test_schema_separation_invariant)
  AC-RP-003  Publication lifecycle — draft/retired not surfaced at play time
  AC-RP-004  Source membership — disabled-source chunks/entities excluded
  AC-RP-005  Source provenance — source_id non-nullable (ADR-0008)
  AC-RP-006  Override non-mutation — source records unchanged by overrides
  AC-RP-007  Override precedence — applied in ascending precedence order
  AC-RP-008  Override target constraint — exactly one of chunk/entity
  AC-RP-009  Entity type models — each enum value maps to a distinct typed model
  AC-RP-010  get_active_rule_slice — correct chunks + entities + override layering
  AC-RP-011  get_entity_by_type_and_name — package scoping and source_id filter
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import Session

import afterworlds.persistence.orm.rules_package  # noqa: F401
from afterworlds.models.enums import (
    MechanicalEntityTypeEnum,
    OverrideOperationEnum,
    OverrideOriginEnum,
    PublicationStatusEnum,
    RuleSubsystemEnum,
)
from afterworlds.models.rules_package import (
    ActionEntity,
    ConditionEntity,
    ItemEntity,
    RuleOverride,
    SpellEntity,
    StatBlockEntity,
)
from afterworlds.persistence.orm.base import Base
from afterworlds.persistence.orm.rules_package import (
    MechanicalEntityORM,
    RuleChunkORM,
    RuleOverrideORM,
    RuleSourceORM,
    RulesPackageORM,
)
from afterworlds.services.rules_package import (
    RulesPackageService,
    _deserialize_entity_data,
)

# ---------------------------------------------------------------------------
# Helpers — direct ORM row inserts for test setup
# ---------------------------------------------------------------------------

_NOW_ISO = datetime(2026, 4, 9, tzinfo=UTC).isoformat()


def _insert_package(
    session: Session,
    *,
    package_id: str | None = None,
    name: str = "Test Package",
    system: str = "d20",
    version: str = "1.0",
    is_enabled: bool = True,
    publication_status: str = "published",
    published_at: str | None = _NOW_ISO,
) -> str:
    pid = package_id or str(uuid4())
    session.execute(
        sa.insert(RulesPackageORM).values(
            rules_package_id=pid,
            name=name,
            system=system,
            version=version,
            is_enabled=is_enabled,
            publication_status=publication_status,
            published_at=published_at,
            created_at=_NOW_ISO,
            updated_at=_NOW_ISO,
        )
    )
    return pid


def _insert_source(
    session: Session,
    *,
    source_id: str | None = None,
    package_id: str,
    name: str = "Player's Handbook",
    category: str = "core_rulebook",
    precedence_rank: int = 1,
    is_enabled: bool = True,
) -> str:
    sid = source_id or str(uuid4())
    session.execute(
        sa.insert(RuleSourceORM).values(
            source_id=sid,
            rules_package_id=package_id,
            name=name,
            category=category,
            precedence_rank=precedence_rank,
            is_enabled=is_enabled,
            created_at=_NOW_ISO,
        )
    )
    return sid


def _insert_chunk(
    session: Session,
    *,
    chunk_id: str | None = None,
    package_id: str,
    source_id: str,
    subsystem: str = "combat",
    content: str = "Attack action.",
    is_enabled: bool = True,
) -> str:
    cid = chunk_id or str(uuid4())
    session.execute(
        sa.insert(RuleChunkORM).values(
            chunk_id=cid,
            rules_package_id=package_id,
            source_id=source_id,
            subsystem=subsystem,
            content=content,
            source_document="PHB",
            source_locator_type="page",
            source_locator_value="195",
            source_section_label=None,
            is_enabled=is_enabled,
            created_at=_NOW_ISO,
        )
    )
    return cid


def _insert_entity(
    session: Session,
    *,
    entity_id: str | None = None,
    package_id: str,
    source_id: str,
    entity_type: str = "condition",
    name: str = "Blinded",
    structured_data: dict | None = None,
    is_enabled: bool = True,
) -> str:
    eid = entity_id or str(uuid4())
    if structured_data is None:
        structured_data = {"effects": ["Cannot see"]}
    session.execute(
        sa.insert(MechanicalEntityORM).values(
            entity_id=eid,
            rules_package_id=package_id,
            source_id=source_id,
            entity_type=entity_type,
            name=name,
            structured_data=structured_data,
            source_document="PHB",
            source_locator_type="page",
            source_locator_value="290",
            source_section_label=None,
            is_enabled=is_enabled,
            created_at=_NOW_ISO,
        )
    )
    return eid


def _insert_override(
    session: Session,
    *,
    override_id: str | None = None,
    package_id: str,
    target_chunk_id: str | None = None,
    target_entity_id: str | None = None,
    operation: str = "replace",
    payload: dict | None = None,
    precedence: int = 1,
    is_enabled: bool = True,
    origin: str = "house_rule",
) -> str:
    oid = override_id or str(uuid4())
    if payload is None:
        payload = {"content": "Replacement text."}
    session.execute(
        sa.insert(RuleOverrideORM).values(
            override_id=oid,
            rules_package_id=package_id,
            target_chunk_id=target_chunk_id,
            target_entity_id=target_entity_id,
            override_origin=origin,
            override_operation=operation,
            override_payload=json.dumps(payload),
            precedence=precedence,
            is_enabled=is_enabled,
            created_at=_NOW_ISO,
        )
    )
    return oid


# ---------------------------------------------------------------------------
# Service fixture
# ---------------------------------------------------------------------------


@pytest.fixture()
def svc(session: Session) -> RulesPackageService:
    return RulesPackageService(session)


# ---------------------------------------------------------------------------
# AC-RP-001: rp_* table prefix
# ---------------------------------------------------------------------------


class TestRpTablePrefix:
    def test_all_five_rp_tables_registered(self) -> None:
        expected = {
            "rp_packages",
            "rp_sources",
            "rp_chunks",
            "rp_mechanical_entities",
            "rp_overrides",
        }
        actual = {n for n in Base.metadata.tables if n.startswith("rp_")}
        assert (
            expected == actual
        ), f"Expected rp_* tables: {sorted(expected)}\nFound: {sorted(actual)}"


# ---------------------------------------------------------------------------
# AC-RP-002: All rp_* FKs stay within the rp_* namespace
# ---------------------------------------------------------------------------


class TestRpFkSeparation:
    def test_all_rp_fks_stay_within_rp_namespace(self) -> None:
        """Every FK from an rp_* table must target another rp_* table."""
        violations: list[str] = []
        for table_name, table in Base.metadata.tables.items():
            if not table_name.startswith("rp_"):
                continue
            for fk in table.foreign_keys:
                target = fk.column.table.name
                if not target.startswith("rp_"):
                    violations.append(
                        f"  {table_name}.{fk.parent.name} → {target}.{fk.column.name}"
                    )
        assert not violations, (
            "rp_* tables must not carry FK constraints to non-rp_* tables.\n"
            "Violations:\n" + "\n".join(violations)
        )


# ---------------------------------------------------------------------------
# AC-RP-005: Source provenance — source_id non-nullable at ORM level
# ---------------------------------------------------------------------------


class TestSourceProvenance:
    def test_chunk_source_id_is_non_nullable(self) -> None:
        col = RuleChunkORM.__table__.c["source_id"]
        assert (
            not col.nullable
        ), "source_id on rp_chunks must be non-nullable (ADR-0008)"

    def test_entity_source_id_is_non_nullable(self) -> None:
        col = MechanicalEntityORM.__table__.c["source_id"]
        assert (
            not col.nullable
        ), "source_id on rp_mechanical_entities must be non-nullable (ADR-0008)"


# ---------------------------------------------------------------------------
# AC-RP-008: Override target constraint — Pydantic model validator
# ---------------------------------------------------------------------------


class TestRuleOverrideTargetConstraintPydantic:
    def _base_kwargs(self, **overrides: object) -> dict:
        base: dict = dict(
            rules_package_id=uuid4(),
            override_origin=OverrideOriginEnum.HOUSE_RULE,
            override_operation=OverrideOperationEnum.REPLACE,
            override_payload='{"content": "x"}',
            precedence=1,
            created_at=datetime(2026, 4, 9, tzinfo=UTC),
        )
        base.update(overrides)
        return base

    def test_chunk_target_only_is_valid(self) -> None:
        RuleOverride(**self._base_kwargs(target_chunk_id=uuid4()))

    def test_entity_target_only_is_valid(self) -> None:
        RuleOverride(**self._base_kwargs(target_entity_id=uuid4()))

    def test_both_targets_raises(self) -> None:
        with pytest.raises(ValueError, match="Exactly one"):
            RuleOverride(
                **self._base_kwargs(
                    target_chunk_id=uuid4(),
                    target_entity_id=uuid4(),
                )
            )

    def test_no_target_raises(self) -> None:
        with pytest.raises(ValueError, match="Exactly one"):
            RuleOverride(**self._base_kwargs())


# ---------------------------------------------------------------------------
# AC-RP-008: Override target constraint — DB CHECK constraint
# ---------------------------------------------------------------------------


class TestRuleOverrideTargetConstraintDb:
    def test_db_check_constraint_rejects_both_targets(self, session: Session) -> None:
        pid = _insert_package(session)
        sid = _insert_source(session, package_id=pid)
        cid = _insert_chunk(session, package_id=pid, source_id=sid)
        eid = _insert_entity(session, package_id=pid, source_id=sid)
        session.commit()
        with pytest.raises(sa.exc.IntegrityError):
            session.execute(
                sa.insert(RuleOverrideORM).values(
                    override_id=str(uuid4()),
                    rules_package_id=pid,
                    target_chunk_id=cid,
                    target_entity_id=eid,
                    override_origin="house_rule",
                    override_operation="replace",
                    override_payload='{"content": "x"}',
                    precedence=1,
                    is_enabled=True,
                    created_at=_NOW_ISO,
                )
            )
            session.commit()

    def test_db_check_constraint_rejects_no_target(self, session: Session) -> None:
        pid = _insert_package(session)
        session.commit()
        with pytest.raises(sa.exc.IntegrityError):
            session.execute(
                sa.insert(RuleOverrideORM).values(
                    override_id=str(uuid4()),
                    rules_package_id=pid,
                    target_chunk_id=None,
                    target_entity_id=None,
                    override_origin="house_rule",
                    override_operation="replace",
                    override_payload='{"content": "x"}',
                    precedence=1,
                    is_enabled=True,
                    created_at=_NOW_ISO,
                )
            )
            session.commit()


# ---------------------------------------------------------------------------
# AC-RP-009: Entity type models
# ---------------------------------------------------------------------------


class TestEntityTypeModels:
    def test_spell_entity(self) -> None:
        e = SpellEntity(
            casting_time="1 action",
            range="60 feet",
            duration="Instantaneous",
            components=["V", "S"],
            effect_description="Deals 8d6 fire damage.",
        )
        assert e.casting_time == "1 action"
        assert e.components == ["V", "S"]

    def test_condition_entity(self) -> None:
        e = ConditionEntity(effects=["Cannot see", "Disadvantage on attacks"])
        assert len(e.effects) == 2

    def test_stat_block_entity(self) -> None:
        e = StatBlockEntity(
            armor_class=15,
            hit_points=52,
            speed="30 ft.",
            strength=16,
            dexterity=12,
            constitution=14,
            intelligence=10,
            wisdom=10,
            charisma=8,
            actions=["Multiattack", "Longsword"],
        )
        assert e.armor_class == 15

    def test_action_entity(self) -> None:
        e = ActionEntity(
            action_type="melee",
            description="Longsword attack",
            attack_bonus=5,
        )
        assert e.attack_bonus == 5
        assert e.effect is None

    def test_item_entity(self) -> None:
        e = ItemEntity(
            item_type="weapon",
            properties=["versatile"],
            weight=3.0,
            value="15 gp",
        )
        assert e.weight == 3.0

    def test_each_enum_value_dispatches_to_distinct_typed_model(
        self,
    ) -> None:
        """Every MechanicalEntityTypeEnum value must resolve to a typed model."""
        type_to_data: dict[MechanicalEntityTypeEnum, dict] = {
            MechanicalEntityTypeEnum.SPELL: {
                "casting_time": "1 action",
                "range": "60 feet",
                "duration": "Instantaneous",
                "effect_description": "Damage.",
            },
            MechanicalEntityTypeEnum.CONDITION: {"effects": ["stunned"]},
            MechanicalEntityTypeEnum.STAT_BLOCK: {
                "armor_class": 12,
                "hit_points": 20,
                "speed": "30 ft.",
                "strength": 10,
                "dexterity": 10,
                "constitution": 10,
                "intelligence": 10,
                "wisdom": 10,
                "charisma": 10,
            },
            MechanicalEntityTypeEnum.ACTION: {
                "action_type": "bonus",
                "description": "Cunning Action",
            },
            MechanicalEntityTypeEnum.ITEM: {"item_type": "armor"},
        }
        covered_types = set(type_to_data.keys())
        all_types = set(MechanicalEntityTypeEnum)
        assert (
            covered_types == all_types
        ), f"Missing coverage for: {all_types - covered_types}"
        for etype, data in type_to_data.items():
            result = _deserialize_entity_data(etype, data)
            assert result is not None


# ---------------------------------------------------------------------------
# AC-RP-003: Publication lifecycle
# ---------------------------------------------------------------------------


class TestPublicationLifecycle:
    def test_draft_package_not_surfaced_at_play_time(
        self, session: Session, svc: RulesPackageService
    ) -> None:
        pid = _insert_package(session, publication_status="draft", published_at=None)
        session.commit()
        assert svc.get_package_by_id(UUID(pid)) is None

    def test_published_package_surfaced_at_play_time(
        self, session: Session, svc: RulesPackageService
    ) -> None:
        pid = _insert_package(session, publication_status="published")
        session.commit()
        result = svc.get_package_by_id(UUID(pid))
        assert result is not None
        assert result.publication_status == PublicationStatusEnum.PUBLISHED

    def test_retired_package_not_surfaced_at_play_time(
        self, session: Session, svc: RulesPackageService
    ) -> None:
        pid = _insert_package(session, publication_status="retired")
        session.commit()
        assert svc.get_package_by_id(UUID(pid)) is None

    def test_draft_accessible_with_include_non_published(
        self, session: Session, svc: RulesPackageService
    ) -> None:
        pid = _insert_package(session, publication_status="draft", published_at=None)
        session.commit()
        result = svc.get_package_by_id(UUID(pid), include_non_published=True)
        assert result is not None
        assert result.publication_status == PublicationStatusEnum.DRAFT

    def test_disabled_package_never_surfaced(
        self, session: Session, svc: RulesPackageService
    ) -> None:
        pid = _insert_package(session, is_enabled=False, publication_status="published")
        session.commit()
        assert svc.get_package_by_id(UUID(pid)) is None
        assert svc.get_package_by_id(UUID(pid), include_non_published=True) is None

    def test_draft_chunks_not_surfaced_at_play_time(
        self, session: Session, svc: RulesPackageService
    ) -> None:
        pid = _insert_package(session, publication_status="draft", published_at=None)
        sid = _insert_source(session, package_id=pid)
        _insert_chunk(session, package_id=pid, source_id=sid)
        session.commit()
        result = svc.get_chunks_by_subsystem(UUID(pid), RuleSubsystemEnum.COMBAT)
        assert result.chunks == []


# ---------------------------------------------------------------------------
# AC-RP-004: Source membership — disabled source excludes its records
# ---------------------------------------------------------------------------


class TestSourceMembership:
    def test_chunks_from_disabled_source_excluded(
        self, session: Session, svc: RulesPackageService
    ) -> None:
        pid = _insert_package(session)
        enabled_sid = _insert_source(
            session,
            package_id=pid,
            name="Enabled",
            is_enabled=True,
            precedence_rank=1,
        )
        disabled_sid = _insert_source(
            session,
            package_id=pid,
            name="Disabled",
            is_enabled=False,
            precedence_rank=2,
        )
        _insert_chunk(
            session,
            package_id=pid,
            source_id=enabled_sid,
            content="Enabled chunk.",
        )
        _insert_chunk(
            session,
            package_id=pid,
            source_id=disabled_sid,
            content="Disabled chunk.",
        )
        session.commit()
        result = svc.get_chunks_by_subsystem(UUID(pid), RuleSubsystemEnum.COMBAT)
        assert len(result.chunks) == 1
        assert result.chunks[0].content == "Enabled chunk."

    def test_entity_from_disabled_source_excluded(
        self, session: Session, svc: RulesPackageService
    ) -> None:
        pid = _insert_package(session)
        disabled_sid = _insert_source(session, package_id=pid, is_enabled=False)
        _insert_entity(session, package_id=pid, source_id=disabled_sid, name="Blinded")
        session.commit()
        result = svc.get_entity_by_type_and_name(
            UUID(pid), MechanicalEntityTypeEnum.CONDITION, "Blinded"
        )
        assert result is None

    def test_no_enabled_sources_returns_empty_chunks(
        self, session: Session, svc: RulesPackageService
    ) -> None:
        pid = _insert_package(session)
        disabled_sid = _insert_source(session, package_id=pid, is_enabled=False)
        _insert_chunk(session, package_id=pid, source_id=disabled_sid)
        session.commit()
        result = svc.get_chunks_by_subsystem(UUID(pid), RuleSubsystemEnum.COMBAT)
        assert result.chunks == []


# ---------------------------------------------------------------------------
# AC-RP-006: Override non-mutation — source records unchanged
# ---------------------------------------------------------------------------


class TestOverrideNonMutation:
    def test_original_chunk_row_unchanged_after_override(
        self, session: Session, svc: RulesPackageService
    ) -> None:
        pid = _insert_package(session)
        sid = _insert_source(session, package_id=pid)
        cid = _insert_chunk(session, package_id=pid, source_id=sid, content="Original.")
        _insert_override(
            session,
            package_id=pid,
            target_chunk_id=cid,
            operation="replace",
            payload={"content": "Replaced."},
        )
        session.commit()
        row = session.get(RuleChunkORM, cid)
        assert row is not None
        assert row.content == "Original."

    def test_chunk_model_carries_original_content(
        self, session: Session, svc: RulesPackageService
    ) -> None:
        pid = _insert_package(session)
        sid = _insert_source(session, package_id=pid)
        cid = _insert_chunk(session, package_id=pid, source_id=sid, content="Original.")
        _insert_override(
            session,
            package_id=pid,
            target_chunk_id=cid,
            operation="replace",
            payload={"content": "Replaced."},
        )
        session.commit()
        result = svc.get_chunks_by_subsystem(UUID(pid), RuleSubsystemEnum.COMBAT)
        assert len(result.chunks) == 1
        assert result.chunks[0].content == "Original."

    def test_active_rule_slice_applied_content_shows_replacement(
        self, session: Session, svc: RulesPackageService
    ) -> None:
        pid = _insert_package(session)
        sid = _insert_source(session, package_id=pid)
        cid = _insert_chunk(session, package_id=pid, source_id=sid, content="Original.")
        _insert_override(
            session,
            package_id=pid,
            target_chunk_id=cid,
            operation="replace",
            payload={"content": "Replaced."},
        )
        session.commit()
        slice_ = svc.get_active_rule_slice(UUID(pid), [RuleSubsystemEnum.COMBAT], [])
        assert slice_.chunks[0].chunk.content == "Original."
        assert slice_.chunks[0].applied_content == "Replaced."


# ---------------------------------------------------------------------------
# AC-RP-007: Override precedence
# ---------------------------------------------------------------------------


class TestOverridePrecedence:
    def test_overrides_applied_in_ascending_precedence_order(
        self, session: Session, svc: RulesPackageService
    ) -> None:
        pid = _insert_package(session)
        sid = _insert_source(session, package_id=pid)
        cid = _insert_chunk(session, package_id=pid, source_id=sid, content="Base.")
        # Insert higher precedence first to verify sorting, not insertion order
        _insert_override(
            session,
            package_id=pid,
            target_chunk_id=cid,
            operation="append",
            payload={"content": " Two"},
            precedence=2,
        )
        _insert_override(
            session,
            package_id=pid,
            target_chunk_id=cid,
            operation="replace",
            payload={"content": "One"},
            precedence=1,
        )
        session.commit()
        # precedence=1 replace: "Base." → "One"
        # precedence=2 append:  "One" → "One Two"
        slice_ = svc.get_active_rule_slice(UUID(pid), [RuleSubsystemEnum.COMBAT], [])
        assert slice_.chunks[0].applied_content == "One Two"

    def test_disable_override_stops_further_processing(
        self, session: Session, svc: RulesPackageService
    ) -> None:
        pid = _insert_package(session)
        sid = _insert_source(session, package_id=pid)
        cid = _insert_chunk(session, package_id=pid, source_id=sid, content="Base.")
        _insert_override(
            session,
            package_id=pid,
            target_chunk_id=cid,
            operation="disable",
            payload={"content": None},
            precedence=1,
        )
        _insert_override(
            session,
            package_id=pid,
            target_chunk_id=cid,
            operation="append",
            payload={"content": " MUST NOT APPEAR"},
            precedence=2,
        )
        session.commit()
        slice_ = svc.get_active_rule_slice(UUID(pid), [RuleSubsystemEnum.COMBAT], [])
        assert slice_.chunks[0].is_disabled is True
        assert slice_.chunks[0].applied_content == ""
        # Disable override was applied; append override was not
        assert len(slice_.chunks[0].override_ids_applied) == 1

    def test_disabled_override_row_is_skipped(
        self, session: Session, svc: RulesPackageService
    ) -> None:
        pid = _insert_package(session)
        sid = _insert_source(session, package_id=pid)
        cid = _insert_chunk(session, package_id=pid, source_id=sid, content="Base.")
        _insert_override(
            session,
            package_id=pid,
            target_chunk_id=cid,
            operation="replace",
            payload={"content": "Should not appear."},
            precedence=1,
            is_enabled=False,
        )
        session.commit()
        slice_ = svc.get_active_rule_slice(UUID(pid), [RuleSubsystemEnum.COMBAT], [])
        assert slice_.chunks[0].applied_content == "Base."
        assert slice_.chunks[0].override_ids_applied == []

    def test_append_override_adds_to_content(
        self, session: Session, svc: RulesPackageService
    ) -> None:
        pid = _insert_package(session)
        sid = _insert_source(session, package_id=pid)
        cid = _insert_chunk(session, package_id=pid, source_id=sid, content="Base.")
        _insert_override(
            session,
            package_id=pid,
            target_chunk_id=cid,
            operation="append",
            payload={"content": " Addendum."},
            precedence=1,
        )
        session.commit()
        slice_ = svc.get_active_rule_slice(UUID(pid), [RuleSubsystemEnum.COMBAT], [])
        assert slice_.chunks[0].applied_content == "Base. Addendum."


# ---------------------------------------------------------------------------
# AC-RP-010: get_active_rule_slice
# ---------------------------------------------------------------------------


class TestGetActiveRuleSlice:
    def test_returns_chunks_for_requested_subsystems_only(
        self, session: Session, svc: RulesPackageService
    ) -> None:
        pid = _insert_package(session)
        sid = _insert_source(session, package_id=pid)
        _insert_chunk(
            session,
            package_id=pid,
            source_id=sid,
            subsystem="combat",
            content="Combat rule.",
        )
        _insert_chunk(
            session,
            package_id=pid,
            source_id=sid,
            subsystem="spells",
            content="Spell rule.",
        )
        session.commit()
        slice_ = svc.get_active_rule_slice(UUID(pid), [RuleSubsystemEnum.COMBAT], [])
        assert len(slice_.chunks) == 1
        assert slice_.chunks[0].chunk.content == "Combat rule."

    def test_returns_entities_for_requested_refs(
        self, session: Session, svc: RulesPackageService
    ) -> None:
        pid = _insert_package(session)
        sid = _insert_source(session, package_id=pid)
        _insert_entity(
            session,
            package_id=pid,
            source_id=sid,
            entity_type="condition",
            name="Blinded",
            structured_data={"effects": ["Cannot see"]},
        )
        session.commit()
        slice_ = svc.get_active_rule_slice(
            UUID(pid),
            [],
            [(MechanicalEntityTypeEnum.CONDITION, "Blinded")],
        )
        assert len(slice_.entities) == 1
        assert slice_.entities[0].entity.name == "Blinded"

    def test_nonexistent_package_returns_empty_slice(
        self, session: Session, svc: RulesPackageService
    ) -> None:
        slice_ = svc.get_active_rule_slice(uuid4(), [RuleSubsystemEnum.COMBAT], [])
        assert slice_.chunks == []
        assert slice_.entities == []

    def test_missing_entity_ref_not_included(
        self, session: Session, svc: RulesPackageService
    ) -> None:
        pid = _insert_package(session)
        _insert_source(session, package_id=pid)
        session.commit()
        slice_ = svc.get_active_rule_slice(
            UUID(pid),
            [],
            [(MechanicalEntityTypeEnum.CONDITION, "Nonexistent")],
        )
        assert slice_.entities == []

    def test_entity_overrides_recorded_in_applied_entity(
        self, session: Session, svc: RulesPackageService
    ) -> None:
        pid = _insert_package(session)
        sid = _insert_source(session, package_id=pid)
        eid = _insert_entity(
            session,
            package_id=pid,
            source_id=sid,
            entity_type="condition",
            name="Blinded",
        )
        oid = _insert_override(
            session,
            package_id=pid,
            target_entity_id=eid,
            operation="replace",
            payload={"content": "House-ruled description."},
        )
        session.commit()
        slice_ = svc.get_active_rule_slice(
            UUID(pid),
            [],
            [(MechanicalEntityTypeEnum.CONDITION, "Blinded")],
        )
        assert len(slice_.entities) == 1
        assert UUID(oid) in slice_.entities[0].override_ids_applied


# ---------------------------------------------------------------------------
# AC-RP-011: get_entity_by_type_and_name — scoping
# ---------------------------------------------------------------------------


class TestGetEntityByTypeAndName:
    def test_scoped_to_package(
        self, session: Session, svc: RulesPackageService
    ) -> None:
        pid1 = _insert_package(session)
        pid2 = _insert_package(session)
        sid1 = _insert_source(session, package_id=pid1)
        sid2 = _insert_source(session, package_id=pid2)
        _insert_entity(
            session,
            package_id=pid1,
            source_id=sid1,
            name="Blinded",
            entity_type="condition",
            structured_data={"effects": ["pkg1"]},
        )
        _insert_entity(
            session,
            package_id=pid2,
            source_id=sid2,
            name="Blinded",
            entity_type="condition",
            structured_data={"effects": ["pkg2"]},
        )
        session.commit()
        result = svc.get_entity_by_type_and_name(
            UUID(pid1), MechanicalEntityTypeEnum.CONDITION, "Blinded"
        )
        assert result is not None
        assert isinstance(result.structured_data, ConditionEntity)
        assert result.structured_data.effects == ["pkg1"]

    def test_source_id_filter_resolves_ambiguity(
        self, session: Session, svc: RulesPackageService
    ) -> None:
        pid = _insert_package(session)
        sid1 = _insert_source(
            session, package_id=pid, name="Source A", precedence_rank=1
        )
        sid2 = _insert_source(
            session, package_id=pid, name="Source B", precedence_rank=2
        )
        _insert_entity(
            session,
            package_id=pid,
            source_id=sid1,
            name="Blinded",
            entity_type="condition",
            structured_data={"effects": ["from_a"]},
        )
        _insert_entity(
            session,
            package_id=pid,
            source_id=sid2,
            name="Blinded",
            entity_type="condition",
            structured_data={"effects": ["from_b"]},
        )
        session.commit()
        result = svc.get_entity_by_type_and_name(
            UUID(pid),
            MechanicalEntityTypeEnum.CONDITION,
            "Blinded",
            source_id=UUID(sid2),
        )
        assert result is not None
        assert isinstance(result.structured_data, ConditionEntity)
        assert result.structured_data.effects == ["from_b"]

    def test_disabled_entity_not_returned(
        self, session: Session, svc: RulesPackageService
    ) -> None:
        pid = _insert_package(session)
        sid = _insert_source(session, package_id=pid)
        _insert_entity(
            session,
            package_id=pid,
            source_id=sid,
            name="Blinded",
            entity_type="condition",
            is_enabled=False,
        )
        session.commit()
        result = svc.get_entity_by_type_and_name(
            UUID(pid), MechanicalEntityTypeEnum.CONDITION, "Blinded"
        )
        assert result is None

    def test_wrong_entity_type_returns_none(
        self, session: Session, svc: RulesPackageService
    ) -> None:
        pid = _insert_package(session)
        sid = _insert_source(session, package_id=pid)
        _insert_entity(
            session,
            package_id=pid,
            source_id=sid,
            name="Blinded",
            entity_type="condition",
        )
        session.commit()
        result = svc.get_entity_by_type_and_name(
            UUID(pid), MechanicalEntityTypeEnum.SPELL, "Blinded"
        )
        assert result is None


# ---------------------------------------------------------------------------
# get_package_by_id — sources are included and ordered by precedence
# ---------------------------------------------------------------------------


class TestGetPackageById:
    def test_returns_sources_ordered_by_precedence(
        self, session: Session, svc: RulesPackageService
    ) -> None:
        pid = _insert_package(session)
        _insert_source(session, package_id=pid, name="Supplement", precedence_rank=2)
        _insert_source(session, package_id=pid, name="Core Rulebook", precedence_rank=1)
        session.commit()
        result = svc.get_package_by_id(UUID(pid))
        assert result is not None
        assert [s.name for s in result.sources] == ["Core Rulebook", "Supplement"]

    def test_nonexistent_package_returns_none(self, svc: RulesPackageService) -> None:
        assert svc.get_package_by_id(uuid4()) is None

    def test_overrides_for_chunk_ordered_by_precedence(
        self, session: Session, svc: RulesPackageService
    ) -> None:
        pid = _insert_package(session)
        sid = _insert_source(session, package_id=pid)
        cid = _insert_chunk(session, package_id=pid, source_id=sid)
        oid1 = _insert_override(
            session,
            package_id=pid,
            target_chunk_id=cid,
            operation="append",
            payload={"content": " B"},
            precedence=2,
        )
        oid2 = _insert_override(
            session,
            package_id=pid,
            target_chunk_id=cid,
            operation="append",
            payload={"content": " A"},
            precedence=1,
        )
        session.commit()
        overrides = svc.get_overrides_for_chunk(UUID(cid))
        assert [str(o.override_id) for o in overrides] == [oid2, oid1]
