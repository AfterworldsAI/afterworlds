"""Exact binding resolution and its typed refusals — #137 contract 6.

Every state here is one #137 requires to stay distinct, and each is asserted as
a *typed* outcome rather than as an absence: the failure mode this suite exists
to prevent is a resolver that answers "no authority" and "malformed reference"
with the same empty result.
"""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest
from sqlalchemy import select

from afterworlds.models.enums import OverrideOperationEnum
from afterworlds.models.rules_package import RulesPackageBinding
from afterworlds.persistence.orm.mechanical import MechanicalActiveProjectionORM
from afterworlds.persistence.orm.rules_package import RulesPackageORM
from afterworlds.services.rules_authority import (
    AuthorityOutcome,
    RulesAuthorityService,
    package_slug,
    resolve_package_reference,
)
from tests.services.rules_authority.conftest import (
    DESCRIPTOR_FACT_TARGET,
    DISABLE_PAYLOAD,
    NOW,
    PACKAGE_NAME,
    RIVAL_PACKAGE_UUID,
    RuntimeFixture,
    author_override,
)


def service(runtime: RuntimeFixture) -> RulesAuthorityService:
    return RulesAuthorityService(runtime.session, now=NOW)


# ---------------------------------------------------------------------------
# The resolved binding
# ---------------------------------------------------------------------------


def test_resolution_returns_all_four_components(runtime: RuntimeFixture) -> None:
    """The binding is the exact four-component value, never three of four."""
    resolution = service(runtime).resolve(package_uuid=runtime.package_uuid)

    assert resolution.outcome is AuthorityOutcome.RESOLVED
    binding = resolution.binding
    assert binding is not None
    assert binding.package_uuid == runtime.package_uuid
    assert binding.release_version == runtime.release_version
    assert binding.mechanical_projection_uuid == runtime.projection_uuid
    # The override-set identity is a value even with no overrides authored.
    assert isinstance(binding.override_set_uuid, UUID)


def test_base_projection_and_override_identities_are_distinct(
    runtime: RuntimeFixture,
) -> None:
    """ADR-005d Decision 9: the two identities are never collapsed into one."""
    binding = service(runtime).resolve(package_uuid=runtime.package_uuid).binding
    assert binding is not None
    assert binding.mechanical_projection_uuid != binding.override_set_uuid


def test_slug_and_uuid_resolve_to_the_same_binding(runtime: RuntimeFixture) -> None:
    """#137 acceptance criterion 18, the positive half.

    The rival package is renamed first so the slug is unambiguous; it is the
    same fixture that makes the ambiguous case below real.
    """
    rival = runtime.session.execute(
        select(RulesPackageORM).where(
            RulesPackageORM.rules_package_id == RIVAL_PACKAGE_UUID
        )
    ).scalar_one()
    rival.name = "Some other corpus"
    runtime.session.flush()

    by_uuid = service(runtime).resolve(package_uuid=runtime.package_uuid)
    by_slug = service(runtime).resolve(package_reference=package_slug(PACKAGE_NAME))

    assert by_slug.outcome is AuthorityOutcome.RESOLVED
    assert by_slug.binding == by_uuid.binding


def test_a_uuid_string_resolves_through_the_same_reference_path(
    runtime: RuntimeFixture,
) -> None:
    """A UUID reference never reaches slug matching."""
    resolved = resolve_package_reference(runtime.session, str(runtime.package_uuid))
    assert resolved.outcome is AuthorityOutcome.RESOLVED
    assert resolved.package_uuid == runtime.package_uuid


# ---------------------------------------------------------------------------
# Typed refusals
# ---------------------------------------------------------------------------


def test_an_ambiguous_slug_is_ambiguous_not_a_first_match(
    runtime: RuntimeFixture,
) -> None:
    """Two packages share a display name, so the slug names neither of them."""
    resolution = service(runtime).resolve(package_reference=package_slug(PACKAGE_NAME))
    assert resolution.outcome is AuthorityOutcome.AMBIGUOUS
    assert "not canonical authority" in resolution.detail

    resolved = resolve_package_reference(runtime.session, PACKAGE_NAME)
    assert resolved.outcome is AuthorityOutcome.AMBIGUOUS
    assert set(resolved.candidates) == {
        runtime.package_uuid,
        runtime.rival_package_uuid,
    }


@pytest.mark.parametrize("reference", ["", "   ", "!!!", "///"])
def test_a_malformed_reference_is_an_invalid_selector(
    runtime: RuntimeFixture, reference: str
) -> None:
    """Neither a UUID nor a slug — refused, not silently dropped."""
    resolution = service(runtime).resolve(package_reference=reference)
    assert resolution.outcome is AuthorityOutcome.INVALID_SELECTOR


def test_an_unknown_slug_is_absent(runtime: RuntimeFixture) -> None:
    resolution = service(runtime).resolve(package_reference="no-such-package")
    assert resolution.outcome is AuthorityOutcome.ABSENT


def test_an_unknown_package_uuid_is_absent(runtime: RuntimeFixture) -> None:
    resolution = service(runtime).resolve(package_uuid=uuid4())
    assert resolution.outcome is AuthorityOutcome.ABSENT


def test_supplying_both_reference_forms_is_an_invalid_selector(
    runtime: RuntimeFixture,
) -> None:
    resolution = service(runtime).resolve(
        package_uuid=runtime.package_uuid, package_reference="anything"
    )
    assert resolution.outcome is AuthorityOutcome.INVALID_SELECTOR


def test_a_package_without_an_active_projection_is_unpublished(
    runtime: RuntimeFixture,
) -> None:
    """``UNPUBLISHED`` is a typed answer, not an empty result."""
    resolution = service(runtime).resolve(package_uuid=runtime.bare_package_uuid)
    assert resolution.outcome is AuthorityOutcome.UNPUBLISHED
    assert resolution.binding is None


def test_an_unpublished_package_row_is_unpublished(runtime: RuntimeFixture) -> None:
    package = runtime.session.execute(
        select(RulesPackageORM).where(
            RulesPackageORM.rules_package_id == str(runtime.package_uuid)
        )
    ).scalar_one()
    package.publication_status = "draft"
    runtime.session.flush()

    resolution = service(runtime).resolve(package_uuid=runtime.package_uuid)
    assert resolution.outcome is AuthorityOutcome.UNPUBLISHED


def test_a_disabled_package_is_absent(runtime: RuntimeFixture) -> None:
    package = runtime.session.execute(
        select(RulesPackageORM).where(
            RulesPackageORM.rules_package_id == str(runtime.package_uuid)
        )
    ).scalar_one()
    package.is_enabled = False
    runtime.session.flush()

    assert (
        service(runtime).resolve(package_uuid=runtime.package_uuid).outcome
        is AuthorityOutcome.ABSENT
    )


def test_a_different_expected_release_is_a_mismatched_release(
    runtime: RuntimeFixture,
) -> None:
    resolution = service(runtime).resolve(
        package_uuid=runtime.package_uuid, expected_release="5.2.1-something-else"
    )
    assert resolution.outcome is AuthorityOutcome.MISMATCHED_RELEASE
    assert runtime.release_version in resolution.detail


def test_a_recorded_binding_naming_another_release_is_mismatched(
    runtime: RuntimeFixture,
) -> None:
    current = service(runtime).resolve(package_uuid=runtime.package_uuid).binding
    assert current is not None
    recorded = RulesPackageBinding(
        package_uuid=current.package_uuid,
        release_version="5.2.1-older",
        mechanical_projection_uuid=current.mechanical_projection_uuid,
        override_set_uuid=current.override_set_uuid,
    )

    resolution = service(runtime).resolve(
        package_uuid=runtime.package_uuid, recorded=recorded
    )
    assert resolution.outcome is AuthorityOutcome.MISMATCHED_RELEASE
    # The refusal still reports what superseded it, so a caller need not
    # resolve a second time to find out.
    assert resolution.current_binding == current


def test_a_recorded_binding_naming_another_projection_is_stale(
    runtime: RuntimeFixture,
) -> None:
    current = service(runtime).resolve(package_uuid=runtime.package_uuid).binding
    assert current is not None
    recorded = RulesPackageBinding(
        package_uuid=current.package_uuid,
        release_version=current.release_version,
        mechanical_projection_uuid=uuid4(),
        override_set_uuid=current.override_set_uuid,
    )

    resolution = service(runtime).resolve(
        package_uuid=runtime.package_uuid, recorded=recorded
    )
    assert resolution.outcome is AuthorityOutcome.STALE


def test_a_recorded_binding_naming_another_package_is_an_invalid_selector(
    runtime: RuntimeFixture,
) -> None:
    """A binding for a different package is not stale — it is the wrong ask."""
    current = service(runtime).resolve(package_uuid=runtime.package_uuid).binding
    assert current is not None
    recorded = RulesPackageBinding(
        package_uuid=runtime.rival_package_uuid,
        release_version=current.release_version,
        mechanical_projection_uuid=current.mechanical_projection_uuid,
        override_set_uuid=current.override_set_uuid,
    )

    resolution = service(runtime).resolve(
        package_uuid=runtime.package_uuid, recorded=recorded
    )
    assert resolution.outcome is AuthorityOutcome.INVALID_SELECTOR


def test_an_activation_row_pointing_elsewhere_is_stale(
    runtime: RuntimeFixture,
) -> None:
    """Activation is not self-certifying: a row alone is not authority."""
    row = runtime.session.execute(
        select(MechanicalActiveProjectionORM).where(
            MechanicalActiveProjectionORM.package_uuid == str(runtime.package_uuid)
        )
    ).scalar_one()
    runtime.session.delete(row)
    runtime.session.flush()

    assert (
        service(runtime).resolve(package_uuid=runtime.package_uuid).outcome
        is AuthorityOutcome.UNPUBLISHED
    )


def test_a_cross_release_override_is_an_invalid_override(
    runtime: RuntimeFixture,
) -> None:
    """#137 contract 6: a cross-release patch fails explicitly.

    Not filtered out, which would make the override invisible and let the
    binding resolve to the identity of a package that never had it.
    """
    author_override(
        runtime.session,
        override_id="ov-cross-release",
        target=DESCRIPTOR_FACT_TARGET,
        operation=OverrideOperationEnum.DISABLE,
        payload=DISABLE_PAYLOAD,
        release_version="5.2.1-some-other-release",
    )

    resolution = service(runtime).resolve(package_uuid=runtime.package_uuid)
    assert resolution.outcome is AuthorityOutcome.INVALID_OVERRIDE
    assert "authored against release" in resolution.detail


def test_an_unreadable_override_row_is_an_invalid_override(
    runtime: RuntimeFixture,
) -> None:
    """A row whose typed columns do not parse cannot be silently skipped."""
    row = author_override(
        runtime.session,
        override_id="ov-bad-origin",
        target=DESCRIPTOR_FACT_TARGET,
        operation=OverrideOperationEnum.DISABLE,
        payload=DISABLE_PAYLOAD,
    )
    row.override_origin = "not-an-origin"
    runtime.session.flush()

    resolution = service(runtime).resolve(package_uuid=runtime.package_uuid)
    assert resolution.outcome is AuthorityOutcome.INVALID_OVERRIDE
