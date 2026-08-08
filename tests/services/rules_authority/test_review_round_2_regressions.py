"""Regression controls for Codex review round 2 (two P1 findings).

Both findings landed in families this PR's stop condition already named, so they
were reassessed as one structural question rather than patched where quoted:
**what must be proven before a retained override-set version may be applied under
a recorded binding, and what stops that evidence from being rewritten?**

* **Scope was asserted, not proven.** Round 1 removed the version row's
  `package_uuid` to stop a package deletion from destroying content shared with
  other packages. That fixed the cascade and lost the only record of *which*
  packages a version was ever retained for, so `load_override_set_version` took
  the caller's word for it. Semantic keys are stable across SRD-derived releases
  by design, so an override set retained for package A finds live targets in
  package B and replays with B's provenance.
* **Append-only was only half enforced.** `UPDATE` and `DELETE` were guarded;
  `INSERT` was not. A plain insert appends an entry to a sealed version, and
  because SQLite leaves `recursive_triggers` off by default, `INSERT OR REPLACE`
  rewrites a header or an entry without firing the delete guard at all.

Each control below fails against the round-1 code and passes after the round-2
fix.
"""

from __future__ import annotations

import pytest
from sqlalchemy import delete, select, text
from sqlalchemy.exc import IntegrityError, OperationalError

from afterworlds.models.enums import OverrideOperationEnum
from afterworlds.models.rules_package import RuleSliceRequest, RulesPackageBinding
from afterworlds.persistence.orm.rules_authority import (
    OverrideSetScopeORM,
    OverrideSetVersionORM,
)
from afterworlds.persistence.orm.rules_package import RulesPackageORM
from afterworlds.services.rules_authority import (
    AuthorityOutcome,
    OverrideSetRetentionError,
    RulesAuthorityService,
    load_override_set_version,
)
from tests.services.rules_authority.conftest import (
    DESCRIPTOR_FACT_TARGET,
    NOW,
    SPELL_KEY,
    RuntimeFixture,
    author_override,
    replace_fact_payload,
    without_append_only_triggers,
)


def service(runtime: RuntimeFixture) -> RulesAuthorityService:
    return RulesAuthorityService(runtime.session, now=NOW)


def _binding_with_overrides(runtime: RuntimeFixture) -> RulesPackageBinding:
    """A recorded binding for the primary package carrying one real override."""
    author_override(
        runtime.session,
        override_id="ov-scoped",
        target=DESCRIPTOR_FACT_TARGET,
        operation=OverrideOperationEnum.REPLACE,
        payload=replace_fact_payload(),
    )
    resolution = service(runtime).resolve(package_uuid=runtime.package_uuid)
    assert resolution.outcome is AuthorityOutcome.RESOLVED
    assert resolution.binding is not None
    return resolution.binding


# ---------------------------------------------------------------------------
# Finding A — a retained version may only be applied under a scope it was
# actually retained for
# ---------------------------------------------------------------------------


def test_replay_refuses_a_version_retained_for_another_package(
    runtime: RuntimeFixture,
) -> None:
    """The end-to-end false-provenance case, and it is reachable.

    Both packages publish a projection over the same semantic keys — which is
    what SRD-derived releases genuinely look like — so package A's override
    finds a live target in package B. Every other check passes: B's projection
    was built over B, and the retained entries reproduce their own identity.
    Only the scope association can catch it.
    """
    primary = _binding_with_overrides(runtime)

    mis_scoped = RulesPackageBinding(
        package_uuid=runtime.rival_package_uuid,
        release_version=runtime.rival_release_version,
        mechanical_projection_uuid=runtime.rival_projection_uuid,
        override_set_uuid=primary.override_set_uuid,
    )
    with pytest.raises(OverrideSetRetentionError, match="was never retained for"):
        service(runtime).replay(mis_scoped)


def test_replay_refuses_a_version_retained_for_another_release(
    runtime: RuntimeFixture,
) -> None:
    """Release is part of the scope, not only the package."""
    primary = _binding_with_overrides(runtime)
    with pytest.raises(OverrideSetRetentionError, match="was never retained for"):
        load_override_set_version(
            runtime.session,
            str(primary.override_set_uuid),
            package_uuid=str(primary.package_uuid),
            release_version="5.2.1-some-other-release",
        )


def test_a_version_replays_under_every_scope_it_was_retained_for(
    runtime: RuntimeFixture,
) -> None:
    """Shared content stays shared — the check is scope, not exclusivity.

    Both packages legitimately retain the empty override set, and each replays
    its own binding against it. A fix that made versions single-owner would
    break this, which is the round-1 defect in reverse.
    """
    primary = service(runtime).resolve(package_uuid=runtime.package_uuid)
    rival = service(runtime).resolve(package_uuid=runtime.rival_package_uuid)
    assert primary.binding is not None and rival.binding is not None
    assert primary.binding.override_set_uuid == rival.binding.override_set_uuid

    assert service(runtime).replay(primary.binding).binding == primary.binding
    assert service(runtime).replay(rival.binding).binding == rival.binding

    versions = (
        runtime.session.execute(
            select(OverrideSetVersionORM).where(
                OverrideSetVersionORM.override_set_uuid
                == str(primary.binding.override_set_uuid)
            )
        )
        .scalars()
        .all()
    )
    assert len(versions) == 1


def test_the_scope_association_is_recorded_for_each_package(
    runtime: RuntimeFixture,
) -> None:
    service(runtime).resolve(package_uuid=runtime.package_uuid)
    service(runtime).resolve(package_uuid=runtime.rival_package_uuid)

    scopes = {
        (row.package_uuid, row.release_version)
        for row in runtime.session.execute(select(OverrideSetScopeORM)).scalars().all()
    }
    assert (str(runtime.package_uuid), runtime.release_version) in scopes
    assert (str(runtime.rival_package_uuid), runtime.rival_release_version) in scopes


def test_deleting_a_package_drops_only_its_own_scope_association(
    runtime: RuntimeFixture,
) -> None:
    """Round 1's guarantee, now expressed through the association.

    The shared content survives and the surviving package still replays; only
    the deleted package's association goes with it.
    """
    primary = service(runtime).resolve(package_uuid=runtime.package_uuid)
    rival = service(runtime).resolve(package_uuid=runtime.rival_package_uuid)
    assert primary.binding is not None and rival.binding is not None

    runtime.session.execute(
        delete(RulesPackageORM).where(
            RulesPackageORM.rules_package_id == str(runtime.rival_package_uuid)
        )
    )
    runtime.session.flush()

    surviving = runtime.session.execute(
        select(OverrideSetVersionORM).where(
            OverrideSetVersionORM.override_set_uuid
            == str(primary.binding.override_set_uuid)
        )
    ).scalar_one_or_none()
    assert surviving is not None
    assert service(runtime).replay(primary.binding).binding == primary.binding


def test_a_missing_scope_association_is_a_retention_defect(
    runtime: RuntimeFixture,
) -> None:
    """Deleting the association fails replay closed, never falsely."""
    primary = _binding_with_overrides(runtime)
    runtime.session.execute(
        delete(OverrideSetScopeORM).where(
            OverrideSetScopeORM.override_set_uuid == str(primary.override_set_uuid)
        )
    )
    runtime.session.flush()

    with pytest.raises(OverrideSetRetentionError, match="was never retained for"):
        service(runtime).replay(primary)


# ---------------------------------------------------------------------------
# Finding B — append-only means INSERT too
# ---------------------------------------------------------------------------


def test_a_sealed_version_refuses_an_appended_entry(
    runtime: RuntimeFixture,
) -> None:
    """A plain INSERT used to extend a retained version past its entry count."""
    _binding_with_overrides(runtime)
    with pytest.raises((IntegrityError, OperationalError), match="sealed"):
        runtime.session.execute(
            text(
                "INSERT INTO rp_override_set_entries (override_set_uuid, apply_order,"
                " override_id, override_origin, target_kind, target_record_key,"
                " target_component_key, target_fact_key, override_operation,"
                " precedence, is_enabled, payload) "
                "SELECT override_set_uuid, 1, 'ov-smuggled', override_origin,"
                " target_kind, target_record_key, target_component_key,"
                " target_fact_key, override_operation, precedence, is_enabled,"
                " payload FROM rp_override_set_entries LIMIT 1"
            )
        )
    runtime.session.rollback()


def test_a_retained_version_refuses_insert_or_replace(
    runtime: RuntimeFixture,
) -> None:
    """SQLite leaves ``recursive_triggers`` off, so REPLACE skips delete guards.

    Verified rather than assumed: without a guard on INSERT itself, this
    rewrites the header and the ``BEFORE DELETE`` trigger never fires.
    """
    _binding_with_overrides(runtime)
    with pytest.raises((IntegrityError, OperationalError), match="append-only"):
        runtime.session.execute(
            text(
                "INSERT OR REPLACE INTO rp_override_set_versions "
                "(override_set_uuid, entry_count, recorded_at) "
                "SELECT override_set_uuid, 99, recorded_at "
                "FROM rp_override_set_versions LIMIT 1"
            )
        )
    runtime.session.rollback()


def test_a_retained_entry_refuses_insert_or_replace(
    runtime: RuntimeFixture,
) -> None:
    """Refused — by the seal guard or the re-insert guard, whichever fires first.

    Both cover this write and the assertion accepts either, because the property
    under test is that the retained entry cannot be rewritten, not which of the
    two guards happens to reach it.
    """
    _binding_with_overrides(runtime)
    with pytest.raises((IntegrityError, OperationalError), match="append-only|sealed"):
        runtime.session.execute(
            text(
                "INSERT OR REPLACE INTO rp_override_set_entries (override_set_uuid,"
                " apply_order, override_id, override_origin, target_kind,"
                " target_record_key, target_component_key, target_fact_key,"
                " override_operation, precedence, is_enabled, payload) "
                "SELECT override_set_uuid, apply_order, 'ov-swapped',"
                " override_origin, target_kind, target_record_key,"
                " target_component_key, target_fact_key, override_operation,"
                " precedence, is_enabled, payload "
                "FROM rp_override_set_entries LIMIT 1"
            )
        )
    runtime.session.rollback()


def test_the_scope_association_refuses_update(runtime: RuntimeFixture) -> None:
    """An association may not be silently relabelled onto another package."""
    service(runtime).resolve(package_uuid=runtime.package_uuid)
    with pytest.raises((IntegrityError, OperationalError), match="append-only"):
        runtime.session.execute(
            text("UPDATE rp_override_set_scopes SET package_uuid = 'somewhere-else'")
        )
    runtime.session.rollback()


def test_retention_remains_idempotent_under_the_insert_guards(
    runtime: RuntimeFixture,
) -> None:
    """The guards must not break the ordinary repeated-resolution path.

    Resolution retains on every read, so a guard that refused the second
    identical retention would break every second binding resolution.
    """
    for _ in range(3):
        assert (
            service(runtime).resolve(package_uuid=runtime.package_uuid).outcome
            is AuthorityOutcome.RESOLVED
        )


def test_read_time_verification_still_catches_a_bypassed_write(
    runtime: RuntimeFixture,
) -> None:
    """Both layers stay load-bearing.

    The triggers stop the ordinary path; this models a database restored without
    them and asserts reconstruction still refuses the result rather than
    replaying a rewritten version.
    """
    primary = _binding_with_overrides(runtime)
    with without_append_only_triggers(runtime.session):
        runtime.session.execute(
            text("UPDATE rp_override_set_entries SET override_id = 'ov-forged'")
        )
        runtime.session.flush()

    with pytest.raises(OverrideSetRetentionError, match="reconstructs as"):
        service(runtime).replay(primary)


def test_the_primary_record_is_still_reachable_after_all_of_this(
    runtime: RuntimeFixture,
) -> None:
    """A sanity anchor: the fixture still describes real authority."""
    result = service(runtime).typed_view(
        RuleSliceRequest(package_id=runtime.package_uuid, whole_package=True)
    )
    assert result.outcome is AuthorityOutcome.RESOLVED
    assert result.typed_view is not None
    assert any(r.semantic_key == SPELL_KEY for r in result.typed_view.records)
