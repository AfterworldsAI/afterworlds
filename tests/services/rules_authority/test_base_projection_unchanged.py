"""Overrides never touch the immutable base projection — Decisions 6 and 10.

ADR-005d is explicit that override state is outside projection identity: an
override change mints a new override-set identity and leaves the base projection
UUID and its rows exactly as published. These tests assert that against the
database, not against the in-memory view — the failure worth catching is an
application path that "helpfully" writes its result back.
"""

from __future__ import annotations

from sqlalchemy import select

from afterworlds.ingestion.mechanical.persistence import (
    reconstruct_candidate,
    verify_persisted_state,
)
from afterworlds.ingestion.mechanical.projection import projection_uuid
from afterworlds.models.enums import OverrideOperationEnum
from afterworlds.models.rules_package import RuleSliceRequest
from afterworlds.persistence.orm.mechanical import (
    MechanicalComponentORM,
    MechanicalFactORM,
    MechanicalProjectionORM,
    MechanicalRecordORM,
)
from afterworlds.services.rules_authority import (
    AuthorityOutcome,
    MechanicalTarget,
    MechanicalTargetKind,
    RulesAuthorityService,
)
from tests.services.rules_authority.conftest import (
    CREATURE_RECORD_TARGET,
    DESCRIPTOR_COMPONENT_TARGET,
    DESCRIPTOR_FACT_TARGET,
    DISABLE_PAYLOAD,
    NOW,
    OPEN_ENDED_KEY,
    SPELL_KEY,
    RuntimeFixture,
    author_override,
    replace_component_payload,
    replace_fact_payload,
)


def _rows(runtime: RuntimeFixture) -> dict[str, list[tuple[str, ...]]]:
    """Every persisted identity and semantic key of the base projection."""
    uuid_ = str(runtime.projection_uuid)
    records = (
        runtime.session.execute(
            select(MechanicalRecordORM)
            .where(MechanicalRecordORM.projection_uuid == uuid_)
            .order_by(MechanicalRecordORM.semantic_key)
        )
        .scalars()
        .all()
    )
    components = (
        runtime.session.execute(
            select(MechanicalComponentORM)
            .where(MechanicalComponentORM.projection_uuid == uuid_)
            .order_by(
                MechanicalComponentORM.record_key,
                MechanicalComponentORM.semantic_key,
            )
        )
        .scalars()
        .all()
    )
    facts = (
        runtime.session.execute(
            select(MechanicalFactORM)
            .where(MechanicalFactORM.projection_uuid == uuid_)
            .order_by(MechanicalFactORM.fact_key)
        )
        .scalars()
        .all()
    )
    return {
        "records": [(r.record_id, r.semantic_key, r.kind) for r in records],
        "components": [
            (c.component_id, c.record_key, c.semantic_key, c.handling)
            for c in components
        ],
        "facts": [
            (f.fact_id, f.record_key, f.component_key, f.fact_key, f.family)
            for f in facts
        ],
    }


def test_applying_overrides_leaves_the_projection_identity_unchanged(
    runtime: RuntimeFixture,
) -> None:
    """The base projection UUID is not reminted by an override (Decision 6)."""
    before = _rows(runtime)
    service = RulesAuthorityService(runtime.session, now=NOW)

    author_override(
        runtime.session,
        override_id="ov-a",
        target=DESCRIPTOR_FACT_TARGET,
        operation=OverrideOperationEnum.REPLACE,
        payload=replace_fact_payload(),
        precedence=10,
    )
    author_override(
        runtime.session,
        override_id="ov-b",
        target=CREATURE_RECORD_TARGET,
        operation=OverrideOperationEnum.DISABLE,
        payload=DISABLE_PAYLOAD,
        precedence=20,
    )
    result = service.typed_view(
        RuleSliceRequest(package_id=runtime.package_uuid, whole_package=True)
    )
    assert result.outcome is AuthorityOutcome.RESOLVED
    assert result.binding is not None
    assert result.binding.mechanical_projection_uuid == runtime.projection_uuid

    assert _rows(runtime) == before


def test_the_persisted_projection_still_derives_its_own_identity(
    runtime: RuntimeFixture,
) -> None:
    """Reconstructed persisted state still hashes to the published UUID."""
    service = RulesAuthorityService(runtime.session, now=NOW)
    author_override(
        runtime.session,
        override_id="ov-replace-component",
        target=DESCRIPTOR_COMPONENT_TARGET,
        operation=OverrideOperationEnum.REPLACE,
        payload=replace_component_payload(),
    )
    service.typed_view(
        RuleSliceRequest(package_id=runtime.package_uuid, whole_package=True)
    )

    candidate = reconstruct_candidate(runtime.session, str(runtime.projection_uuid))
    assert projection_uuid(candidate) == str(runtime.projection_uuid)
    assert (
        verify_persisted_state(
            runtime.session,
            str(runtime.projection_uuid),
            expected_status="published",
        )
        == ()
    )


def test_the_published_header_is_untouched(runtime: RuntimeFixture) -> None:
    header_before = _header_snapshot(runtime)
    service = RulesAuthorityService(runtime.session, now=NOW)
    author_override(
        runtime.session,
        override_id="ov-disable",
        target=CREATURE_RECORD_TARGET,
        operation=OverrideOperationEnum.DISABLE,
        payload=DISABLE_PAYLOAD,
    )
    service.gamemaster_view(
        RuleSliceRequest(package_id=runtime.package_uuid, whole_package=True)
    )
    assert _header_snapshot(runtime) == header_before


def _header_snapshot(runtime: RuntimeFixture) -> tuple[object, ...]:
    header = runtime.session.execute(
        select(MechanicalProjectionORM).where(
            MechanicalProjectionORM.projection_uuid == str(runtime.projection_uuid)
        )
    ).scalar_one()
    return (
        header.projection_uuid,
        header.payload_hash,
        header.persisted_state_digest,
        header.publication_status,
        header.published_at,
        header.evidence_report_hash,
        header.oracle_identity,
    )


def test_a_prose_replace_clearing_the_effective_reason_leaves_the_base_row_untouched(
    runtime: RuntimeFixture,
) -> None:
    """A PROSE REPLACE clears the source-derived irreducibility reason from
    the *effective* view (application.py's ``_apply_prose_entry``). This must
    never reach the persisted base row: ``MechanicalComponentORM`` is written
    once at publication and is not a place override application writes to.
    """
    persisted_before = runtime.session.execute(
        select(MechanicalComponentORM).where(
            MechanicalComponentORM.projection_uuid == str(runtime.projection_uuid),
            MechanicalComponentORM.record_key == SPELL_KEY,
            MechanicalComponentORM.semantic_key == OPEN_ENDED_KEY,
        )
    ).scalar_one()
    assert persisted_before.irreducibility_reason_code == "open_ended_effect"
    rows_before = _rows(runtime)

    service = RulesAuthorityService(runtime.session, now=NOW)
    author_override(
        runtime.session,
        override_id="ov-replace-prose",
        target=MechanicalTarget(
            kind=MechanicalTargetKind.PROSE,
            record_key=SPELL_KEY,
            component_key=OPEN_ENDED_KEY,
        ),
        operation=OverrideOperationEnum.REPLACE,
        payload={"patch": "replace_prose", "text": "the authored replacement"},
    )
    result = service.typed_view(
        RuleSliceRequest(package_id=runtime.package_uuid, whole_package=True)
    )
    assert result.outcome is AuthorityOutcome.RESOLVED
    assert result.typed_view is not None
    (record,) = [r for r in result.typed_view.records if r.semantic_key == SPELL_KEY]
    (component,) = [c for c in record.components if c.semantic_key == OPEN_ENDED_KEY]
    assert component.irreducibility_reason_code is None
    assert result.binding is not None
    assert result.binding.mechanical_projection_uuid == runtime.projection_uuid

    persisted_after = runtime.session.execute(
        select(MechanicalComponentORM).where(
            MechanicalComponentORM.projection_uuid == str(runtime.projection_uuid),
            MechanicalComponentORM.record_key == SPELL_KEY,
            MechanicalComponentORM.semantic_key == OPEN_ENDED_KEY,
        )
    ).scalar_one()
    assert persisted_after.irreducibility_reason_code == "open_ended_effect"
    assert persisted_after.handling == persisted_before.handling
    assert _rows(runtime) == rows_before
