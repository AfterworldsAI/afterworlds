"""Runtime staleness and historical replay — ADR-005d Decision 9.

The two operations this module separates are the ones ADR-005d says are
different, and the separation is the whole reason override-set versions are
retained at all:

* **Runtime** recomputes the override-set identity from current state. A
  recorded binding that no longer matches is ``STALE`` and fails — never
  silently re-resolved against whatever the overrides say now.
* **Replay** resolves the retained immutable version and must succeed,
  reconstructing what was originally applied, *after* the current rows are
  edited, disabled, reprioritized, retargeted, or deleted. ``STALE`` is not a
  valid answer here.

The last test is the one ADR-005d's rejected-alternative 12 names directly: an
implementation that retains only the identifier and re-derives from current rows
must fail.
"""

from __future__ import annotations

import pytest
from sqlalchemy import delete, select

from afterworlds.models.enums import OverrideOperationEnum, OverrideOriginEnum
from afterworlds.persistence.orm.rules_authority import (
    MechanicalOverrideORM,
    OverrideSetEntryORM,
    OverrideSetVersionORM,
)
from afterworlds.services.rules_authority import (
    AuthorityOutcome,
    OverrideSetRetentionError,
    RulesAuthorityService,
    load_override_set_version,
)
from tests.services.rules_authority.conftest import (
    DESCRIPTOR_FACT_KEY,
    DESCRIPTOR_FACT_TARGET,
    DESCRIPTOR_KEY,
    NOW,
    SPELL_KEY,
    RuntimeFixture,
    author_override,
    replace_fact_payload,
)


def service(runtime: RuntimeFixture) -> RulesAuthorityService:
    return RulesAuthorityService(runtime.session, now=NOW)


def _recorded_binding(runtime: RuntimeFixture):  # type: ignore[no-untyped-def]
    """Author one override, resolve, and return the binding a consumer stores."""
    author_override(
        runtime.session,
        override_id="ov-historic",
        target=DESCRIPTOR_FACT_TARGET,
        operation=OverrideOperationEnum.REPLACE,
        payload=replace_fact_payload(),
        precedence=10,
        origin=OverrideOriginEnum.HOUSE_RULE,
    )
    resolution = service(runtime).resolve(package_uuid=runtime.package_uuid)
    assert resolution.outcome is AuthorityOutcome.RESOLVED
    assert resolution.binding is not None
    return resolution.binding


# ---------------------------------------------------------------------------
# Runtime staleness
# ---------------------------------------------------------------------------


def test_a_superseded_override_set_is_stale_at_runtime(
    runtime: RuntimeFixture,
) -> None:
    """The recorded binding is refused, not quietly re-resolved."""
    recorded = _recorded_binding(runtime)

    row = runtime.session.get(MechanicalOverrideORM, "ov-historic")
    assert row is not None
    row.precedence = 500
    runtime.session.flush()

    resolution = service(runtime).resolve(
        package_uuid=runtime.package_uuid, recorded=recorded
    )
    assert resolution.outcome is AuthorityOutcome.STALE
    assert resolution.current_binding is not None
    assert resolution.current_binding.override_set_uuid != recorded.override_set_uuid
    # Everything else about the binding is unchanged: only the override set
    # moved, and the base projection identity did not.
    assert (
        resolution.current_binding.mechanical_projection_uuid
        == recorded.mechanical_projection_uuid
    )


def test_deleting_the_override_is_also_stale(runtime: RuntimeFixture) -> None:
    recorded = _recorded_binding(runtime)
    runtime.session.execute(
        delete(MechanicalOverrideORM).where(
            MechanicalOverrideORM.override_id == "ov-historic"
        )
    )
    runtime.session.flush()

    assert (
        service(runtime)
        .resolve(package_uuid=runtime.package_uuid, recorded=recorded)
        .outcome
        is AuthorityOutcome.STALE
    )


def test_a_current_binding_is_not_stale(runtime: RuntimeFixture) -> None:
    """The check has to be capable of passing, or it proves nothing."""
    recorded = _recorded_binding(runtime)
    resolution = service(runtime).resolve(
        package_uuid=runtime.package_uuid, recorded=recorded
    )
    assert resolution.outcome is AuthorityOutcome.RESOLVED
    assert resolution.binding == recorded


# ---------------------------------------------------------------------------
# Replay
# ---------------------------------------------------------------------------


def test_replay_reconstructs_the_original_authority_after_mutation(
    runtime: RuntimeFixture,
) -> None:
    """#137 contract 5, negative control 3.

    The recorded binding reconstructs the exact identities, origins, order,
    targets, operations, enablement, and payloads originally applied — after the
    current row has been retargeted, reprioritized, disabled, and re-originated.
    """
    recorded = _recorded_binding(runtime)
    original = service(runtime).replay(recorded)

    row = runtime.session.get(MechanicalOverrideORM, "ov-historic")
    assert row is not None
    row.precedence = 900
    row.is_enabled = False
    row.override_origin = OverrideOriginEnum.PACKAGE_PATCH.value
    row.target_component_key = "somewhere-else"
    runtime.session.flush()

    replayed = service(runtime).replay(recorded)

    assert replayed.applied_overrides == original.applied_overrides
    (applied,) = replayed.applied_overrides
    assert applied.override_id == "ov-historic"
    assert applied.origin is OverrideOriginEnum.HOUSE_RULE
    assert applied.operation is OverrideOperationEnum.REPLACE
    assert applied.precedence == 10
    assert applied.apply_order == 0
    assert applied.is_enabled is True
    assert applied.target == DESCRIPTOR_FACT_TARGET
    assert applied.payload == replace_fact_payload()
    assert applied.applied is True
    # And the reconstructed mechanical result is the original one too.
    assert replayed.records == original.records


def test_replay_survives_deletion_of_the_current_override(
    runtime: RuntimeFixture,
) -> None:
    """Current rows are the authoring surface, not the replay evidence."""
    recorded = _recorded_binding(runtime)
    original = service(runtime).replay(recorded)

    runtime.session.execute(
        delete(MechanicalOverrideORM).where(
            MechanicalOverrideORM.override_id == "ov-historic"
        )
    )
    runtime.session.flush()
    assert runtime.session.execute(select(MechanicalOverrideORM)).all() == []

    replayed = service(runtime).replay(recorded)
    assert replayed.applied_overrides == original.applied_overrides
    assert replayed.records == original.records


def test_replay_identifies_the_complete_effective_binding(
    runtime: RuntimeFixture,
) -> None:
    """Replay evidence names all four components that produced it."""
    recorded = _recorded_binding(runtime)
    replayed = service(runtime).replay(recorded)
    assert replayed.binding == recorded


def test_replay_of_an_unretained_version_is_a_retention_defect(
    runtime: RuntimeFixture,
) -> None:
    """Not ``STALE``: a missing version is a defect in retention itself."""
    recorded = _recorded_binding(runtime)
    runtime.session.execute(
        delete(OverrideSetEntryORM).where(
            OverrideSetEntryORM.override_set_uuid == str(recorded.override_set_uuid)
        )
    )
    runtime.session.execute(
        delete(OverrideSetVersionORM).where(
            OverrideSetVersionORM.override_set_uuid == str(recorded.override_set_uuid)
        )
    )
    runtime.session.flush()

    with pytest.raises(OverrideSetRetentionError, match="no retained override-set"):
        service(runtime).replay(recorded)


def test_a_retained_version_that_no_longer_derives_its_identity_is_a_defect(
    runtime: RuntimeFixture,
) -> None:
    """Retained evidence is verified on read, never trusted for being stored."""
    recorded = _recorded_binding(runtime)
    entry = runtime.session.execute(
        select(OverrideSetEntryORM).where(
            OverrideSetEntryORM.override_set_uuid == str(recorded.override_set_uuid)
        )
    ).scalar_one()
    entry.precedence = 77
    runtime.session.flush()

    with pytest.raises(OverrideSetRetentionError, match="reconstructs as"):
        load_override_set_version(runtime.session, str(recorded.override_set_uuid))


def test_a_retained_version_missing_an_entry_is_a_defect(
    runtime: RuntimeFixture,
) -> None:
    recorded = _recorded_binding(runtime)
    runtime.session.execute(
        delete(OverrideSetEntryORM).where(
            OverrideSetEntryORM.override_set_uuid == str(recorded.override_set_uuid)
        )
    )
    runtime.session.flush()

    with pytest.raises(OverrideSetRetentionError, match="entries"):
        load_override_set_version(runtime.session, str(recorded.override_set_uuid))


def test_retaining_the_same_state_twice_is_idempotent(
    runtime: RuntimeFixture,
) -> None:
    """Identity is the primary key, so an identical state is the same version."""
    recorded = _recorded_binding(runtime)
    service(runtime).resolve(package_uuid=runtime.package_uuid)
    service(runtime).resolve(package_uuid=runtime.package_uuid)

    versions = (
        runtime.session.execute(
            select(OverrideSetVersionORM).where(
                OverrideSetVersionORM.override_set_uuid
                == str(recorded.override_set_uuid)
            )
        )
        .scalars()
        .all()
    )
    assert len(versions) == 1
    entries = (
        runtime.session.execute(
            select(OverrideSetEntryORM).where(
                OverrideSetEntryORM.override_set_uuid == str(recorded.override_set_uuid)
            )
        )
        .scalars()
        .all()
    )
    assert len(entries) == 1


def test_current_rows_cannot_substitute_for_retained_provenance(
    runtime: RuntimeFixture,
) -> None:
    """#137 contract 5, negative control 4 — stated as an equivalence failure.

    An implementation that kept only the ``override_set_uuid`` and re-derived
    from current rows would answer this replay with *today's* authority. The
    assertion is that replay and a fresh derivation from current state disagree,
    and that replay is the one that still matches what was recorded.
    """
    recorded = _recorded_binding(runtime)

    row = runtime.session.get(MechanicalOverrideORM, "ov-historic")
    assert row is not None
    row.payload = replace_fact_payload(_third_descriptor())
    runtime.session.flush()

    current = service(runtime).resolve(package_uuid=runtime.package_uuid)
    assert current.outcome is AuthorityOutcome.RESOLVED
    assert current.binding is not None
    assert current.binding.override_set_uuid != recorded.override_set_uuid

    replayed = service(runtime).replay(recorded)
    (applied,) = replayed.applied_overrides
    assert applied.payload == replace_fact_payload()
    assert applied.payload != replace_fact_payload(_third_descriptor())

    # And the replayed mechanical value is the original one, not the current.
    (record,) = [r for r in replayed.records if r.semantic_key == SPELL_KEY]
    (component,) = [c for c in record.components if c.semantic_key == DESCRIPTOR_KEY]
    (fact,) = component.facts
    assert fact.fact.level == 7
    assert fact.fact_key != DESCRIPTOR_FACT_KEY


def _third_descriptor():  # type: ignore[no-untyped-def]
    from afterworlds.ingestion.mechanical.representation import (
        SpellDescriptorFact,
        SpellSchool,
    )

    return SpellDescriptorFact(
        level=2, school=SpellSchool.NECROMANCY, ritual=False, concentration=False
    )
