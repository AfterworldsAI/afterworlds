"""Regression controls for Codex review round 1 (four P1 findings).

Grouped here rather than scattered into the suites they touch, because the four
findings are two defect *families* and the families are what the controls are
about:

* **A resolution that returns success without proving what it names.**
  ``resolve_package_reference`` accepted any syntactically valid UUID, and
  ``replay`` loaded an override set and a projection without checking they
  describe one authority.
* **Retained replay evidence that is not actually durable.** The retained
  tables had no append-only enforcement, and a content-addressed version shared
  by several packages was tied to one package's lifecycle by a cascading
  foreign key.

Each control fails against the pre-fix code and passes after it.
"""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest
from sqlalchemy import delete, select, text
from sqlalchemy.exc import IntegrityError, OperationalError

from afterworlds.models.enums import OverrideOperationEnum
from afterworlds.models.rules_package import RuleSliceRequest, RulesPackageBinding
from afterworlds.persistence.orm.rules_authority import (
    OverrideSetEntryORM,
    OverrideSetVersionORM,
)
from afterworlds.persistence.orm.rules_package import RulesPackageORM
from afterworlds.services.rules_authority import (
    EMPTY_OVERRIDE_SET_UUID,
    AuthorityOutcome,
    IncoherentBindingError,
    RulesAuthorityService,
    resolve_package_reference,
)
from afterworlds.services.rules_package import (
    RuleSliceResolutionError,
    RulesPackageService,
)
from tests.services.rules_authority.conftest import (
    DESCRIPTOR_FACT_TARGET,
    NOW,
    RuntimeFixture,
    author_override,
    replace_fact_payload,
)


def service(runtime: RuntimeFixture) -> RulesAuthorityService:
    return RulesAuthorityService(runtime.session, now=NOW)


# ---------------------------------------------------------------------------
# Family 1 — success is never returned without proving what it names
# ---------------------------------------------------------------------------


def test_an_unknown_uuid_reference_is_absent_not_resolved(
    runtime: RuntimeFixture,
) -> None:
    """Finding 1. A well-formed UUID is a reference, not a resolution.

    It used to be returned unchecked, so an unknown package UUID reported
    ``RESOLVED`` while the equivalent unknown slug reported ``ABSENT`` — and a
    caller reading ``RESOLVED`` as "this package exists" proceeded on one that
    did not.
    """
    resolved = resolve_package_reference(runtime.session, str(uuid4()))
    assert resolved.outcome is AuthorityOutcome.ABSENT
    assert resolved.package_uuid is None


def test_a_disabled_package_uuid_reference_is_absent(
    runtime: RuntimeFixture,
) -> None:
    """Both branches resolve against the same enabled-package population."""
    package = runtime.session.execute(
        select(RulesPackageORM).where(
            RulesPackageORM.rules_package_id == str(runtime.package_uuid)
        )
    ).scalar_one()
    package.is_enabled = False
    runtime.session.flush()

    resolved = resolve_package_reference(runtime.session, str(runtime.package_uuid))
    assert resolved.outcome is AuthorityOutcome.ABSENT


def test_uuid_and_slug_branches_agree_on_an_absent_package(
    runtime: RuntimeFixture,
) -> None:
    """The asymmetry itself is the defect, so the symmetry is the assertion."""
    by_uuid = resolve_package_reference(runtime.session, str(uuid4()))
    by_slug = resolve_package_reference(runtime.session, "no-such-package-at-all")
    assert by_uuid.outcome is by_slug.outcome is AuthorityOutcome.ABSENT


def test_the_rule_slice_seam_refuses_an_unknown_uuid(
    runtime: RuntimeFixture,
) -> None:
    """The seam a Character Sheet reference reaches reports it too."""
    unknown = uuid4()
    resolver = RulesPackageService(runtime.session)
    with pytest.raises(RuleSliceResolutionError) as excinfo:
        resolver.resolve_slice_package(
            RuleSliceRequest(package_slug=str(unknown), whole_package=True)
        )
    assert excinfo.value.outcome is AuthorityOutcome.ABSENT


def test_replay_refuses_a_projection_from_another_package(
    runtime: RuntimeFixture,
) -> None:
    """Finding 4. The four components must describe one authority.

    The override set and the projection are loaded from different tables by
    different identities, so loading both proves nothing about them belonging
    together — and the empty override-set identity is legitimately shared, so it
    cannot supply the link either.
    """
    incoherent = RulesPackageBinding(
        package_uuid=runtime.rival_package_uuid,
        release_version=runtime.release_version,
        mechanical_projection_uuid=runtime.projection_uuid,
        override_set_uuid=UUID(EMPTY_OVERRIDE_SET_UUID),
    )
    with pytest.raises(IncoherentBindingError, match="was built over package"):
        service(runtime).replay(incoherent)


def test_replay_refuses_a_projection_from_another_release(
    runtime: RuntimeFixture,
) -> None:
    incoherent = RulesPackageBinding(
        package_uuid=runtime.package_uuid,
        release_version="5.2.1-some-other-release",
        mechanical_projection_uuid=runtime.projection_uuid,
        override_set_uuid=UUID(EMPTY_OVERRIDE_SET_UUID),
    )
    with pytest.raises(IncoherentBindingError, match="was built over release"):
        service(runtime).replay(incoherent)


def test_a_coherent_binding_still_replays(runtime: RuntimeFixture) -> None:
    """The coherence check has to be capable of passing."""
    resolution = service(runtime).resolve(package_uuid=runtime.package_uuid)
    assert resolution.binding is not None
    assert service(runtime).replay(resolution.binding).binding == resolution.binding


# ---------------------------------------------------------------------------
# Family 2 — retained replay evidence is durable
# ---------------------------------------------------------------------------


def test_retained_versions_refuse_update(runtime: RuntimeFixture) -> None:
    """Finding 2. Append-only is enforced by the database, not by discipline."""
    service(runtime).resolve(package_uuid=runtime.package_uuid)
    with pytest.raises((IntegrityError, OperationalError), match="append-only"):
        runtime.session.execute(
            text("UPDATE rp_override_set_versions SET entry_count = 99")
        )
    runtime.session.rollback()


def test_retained_versions_refuse_delete(runtime: RuntimeFixture) -> None:
    service(runtime).resolve(package_uuid=runtime.package_uuid)
    with pytest.raises((IntegrityError, OperationalError), match="append-only"):
        runtime.session.execute(text("DELETE FROM rp_override_set_versions"))
    runtime.session.rollback()


def test_retained_entries_refuse_update(runtime: RuntimeFixture) -> None:
    author_override(
        runtime.session,
        override_id="ov-durable",
        target=DESCRIPTOR_FACT_TARGET,
        operation=OverrideOperationEnum.REPLACE,
        payload=replace_fact_payload(),
    )
    service(runtime).resolve(package_uuid=runtime.package_uuid)
    with pytest.raises((IntegrityError, OperationalError), match="append-only"):
        runtime.session.execute(
            text("UPDATE rp_override_set_entries SET precedence = 77")
        )
    runtime.session.rollback()


def test_retained_entries_refuse_delete(runtime: RuntimeFixture) -> None:
    author_override(
        runtime.session,
        override_id="ov-durable",
        target=DESCRIPTOR_FACT_TARGET,
        operation=OverrideOperationEnum.REPLACE,
        payload=replace_fact_payload(),
    )
    service(runtime).resolve(package_uuid=runtime.package_uuid)
    with pytest.raises((IntegrityError, OperationalError), match="append-only"):
        runtime.session.execute(text("DELETE FROM rp_override_set_entries"))
    runtime.session.rollback()


def test_authoring_rows_remain_editable(runtime: RuntimeFixture) -> None:
    """The authoring surface is deliberately *not* append-only.

    Overrides are meant to be edited, disabled, and deleted; that is the whole
    reason the retained versions exist separately. Locking both would make the
    feature unusable, so the boundary between them is asserted rather than
    assumed.
    """
    from afterworlds.persistence.orm.rules_authority import MechanicalOverrideORM

    row = author_override(
        runtime.session,
        override_id="ov-editable",
        target=DESCRIPTOR_FACT_TARGET,
        operation=OverrideOperationEnum.REPLACE,
        payload=replace_fact_payload(),
    )
    row.precedence = 42
    runtime.session.flush()
    runtime.session.execute(
        delete(MechanicalOverrideORM).where(
            MechanicalOverrideORM.override_id == "ov-editable"
        )
    )
    runtime.session.flush()
    assert runtime.session.get(MechanicalOverrideORM, "ov-editable") is None


def test_deleting_a_package_does_not_destroy_shared_replay_evidence(
    runtime: RuntimeFixture,
) -> None:
    """Finding 3. A shared version is content, not one package's possession.

    Both packages resolve the empty override set, which is one row by design.
    Deleting the package that retained it first used to cascade that row away
    and break replay for every recorded binding of every other package that
    reused the identity.
    """
    first = service(runtime).resolve(package_uuid=runtime.package_uuid)
    assert first.binding is not None
    assert str(first.binding.override_set_uuid) == EMPTY_OVERRIDE_SET_UUID

    # The rival package has no active projection, so it reaches the same
    # retained version through a direct retention call rather than a binding.
    from afterworlds.services.rules_authority import (
        collect_current_override_state,
        retain_override_set,
    )

    rival_state = collect_current_override_state(
        runtime.session, str(runtime.rival_package_uuid), runtime.release_version
    )
    assert retain_override_set(runtime.session, rival_state, now=NOW) == str(
        EMPTY_OVERRIDE_SET_UUID
    )

    runtime.session.execute(
        delete(RulesPackageORM).where(
            RulesPackageORM.rules_package_id == str(runtime.rival_package_uuid)
        )
    )
    runtime.session.flush()

    surviving = runtime.session.execute(
        select(OverrideSetVersionORM).where(
            OverrideSetVersionORM.override_set_uuid == EMPTY_OVERRIDE_SET_UUID
        )
    ).scalar_one_or_none()
    assert surviving is not None
    # And the other package's recorded binding still replays.
    assert service(runtime).replay(first.binding).binding == first.binding


def test_a_retained_version_carries_no_owning_package_column(
    runtime: RuntimeFixture,
) -> None:
    """Stated structurally: there is no column to cascade from.

    A fix that kept the column and only removed the cascade would leave a row
    naming whichever package happened to retain it first, which is misleading
    for shared content.
    """
    columns = {c.name for c in OverrideSetVersionORM.__table__.columns}
    assert columns == {"override_set_uuid", "entry_count", "recorded_at"}
    assert not OverrideSetVersionORM.__table__.foreign_keys
    # The entries still cascade from their own version, which is correct: an
    # entry has no meaning apart from the version it belongs to.
    assert {
        fk.column.table.name for fk in OverrideSetEntryORM.__table__.foreign_keys
    } == {"rp_override_set_versions"}
