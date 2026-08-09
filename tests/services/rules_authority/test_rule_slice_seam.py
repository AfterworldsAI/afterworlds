"""The extended ``RuleSliceRequest`` seam — #137 contract 6.

Two fail-open behaviours had to lose every surviving caller:

* a package reference parsed with ``UUID(...)`` and, on ``ValueError``, silently
  dropped; and
* a request carrying no selectors at all, which always produced an empty slice
  that read like "no rule applies".

These tests assert the model itself now refuses both, so no caller can
reintroduce either by construction, and that the code-owned resolution seam
reports a typed reason instead of an empty result.
"""

from __future__ import annotations

import pytest
from sqlalchemy import select

from afterworlds.models.enums import MechanicalEntityTypeEnum, RuleSubsystemEnum
from afterworlds.models.rules_package import RuleSliceRequest
from afterworlds.persistence.orm.rules_package import RulesPackageORM
from afterworlds.services.rules_authority import AuthorityOutcome, package_slug
from afterworlds.services.rules_package import (
    RuleSliceResolutionError,
    RulesPackageService,
)
from tests.services.rules_authority.conftest import (
    PACKAGE_NAME,
    RIVAL_PACKAGE_UUID,
    SPELL_KEY,
    RuntimeFixture,
)

# ---------------------------------------------------------------------------
# The accidentally-empty selector
# ---------------------------------------------------------------------------


def test_a_request_selecting_nothing_is_refused_at_construction(
    runtime: RuntimeFixture,
) -> None:
    """The exact shape the orchestrator used to build, now unbuildable."""
    with pytest.raises(ValueError, match="selects nothing"):
        RuleSliceRequest(package_id=runtime.package_uuid)


@pytest.mark.parametrize(
    "selector",
    [
        {"whole_package": True},
        {"subsystem_tags": [RuleSubsystemEnum.COMBAT]},
        {"entity_refs": [(MechanicalEntityTypeEnum.SPELL, "Wish")]},
        {"record_selectors": (SPELL_KEY,)},
        {"component_selectors": ((SPELL_KEY, "descriptor"),)},
    ],
)
def test_an_explicit_selection_is_accepted(
    runtime: RuntimeFixture, selector: dict[str, object]
) -> None:
    """Every way of saying what is wanted, including saying "all of it"."""
    request = RuleSliceRequest(package_id=runtime.package_uuid, **selector)
    assert request.package_id == runtime.package_uuid


# ---------------------------------------------------------------------------
# The package reference
# ---------------------------------------------------------------------------


def test_exactly_one_package_reference_form_is_required(
    runtime: RuntimeFixture,
) -> None:
    with pytest.raises(ValueError, match="exactly one of package_id"):
        RuleSliceRequest(whole_package=True)
    with pytest.raises(ValueError, match="exactly one of package_id"):
        RuleSliceRequest(
            package_id=runtime.package_uuid,
            package_slug="srd-5-2-1-corpus",
            whole_package=True,
        )


def test_a_slug_request_resolves_through_the_code_owned_path(
    runtime: RuntimeFixture,
) -> None:
    rival = runtime.session.execute(
        select(RulesPackageORM).where(
            RulesPackageORM.rules_package_id == RIVAL_PACKAGE_UUID
        )
    ).scalar_one()
    rival.name = "Unrelated corpus"
    runtime.session.flush()

    service = RulesPackageService(runtime.session)
    resolved = service.resolve_slice_package(
        RuleSliceRequest(package_slug=package_slug(PACKAGE_NAME), whole_package=True)
    )
    assert resolved == runtime.package_uuid


def test_a_uuid_request_passes_straight_through(runtime: RuntimeFixture) -> None:
    service = RulesPackageService(runtime.session)
    assert (
        service.resolve_slice_package(
            RuleSliceRequest(package_id=runtime.package_uuid, whole_package=True)
        )
        == runtime.package_uuid
    )


def test_an_ambiguous_slug_raises_a_typed_resolution_error(
    runtime: RuntimeFixture,
) -> None:
    """Explicit failure, carrying which state it is — not an empty slice."""
    service = RulesPackageService(runtime.session)
    with pytest.raises(RuleSliceResolutionError) as excinfo:
        service.resolve_slice_package(
            RuleSliceRequest(
                package_slug=package_slug(PACKAGE_NAME), whole_package=True
            )
        )
    assert excinfo.value.outcome is AuthorityOutcome.AMBIGUOUS


def test_an_unknown_slug_raises_a_typed_resolution_error(
    runtime: RuntimeFixture,
) -> None:
    service = RulesPackageService(runtime.session)
    with pytest.raises(RuleSliceResolutionError) as excinfo:
        service.resolve_slice_package(
            RuleSliceRequest(package_slug="nothing-here", whole_package=True)
        )
    assert excinfo.value.outcome is AuthorityOutcome.ABSENT


def test_a_malformed_slug_raises_a_typed_resolution_error(
    runtime: RuntimeFixture,
) -> None:
    service = RulesPackageService(runtime.session)
    with pytest.raises(RuleSliceResolutionError) as excinfo:
        service.resolve_slice_package(
            RuleSliceRequest(package_slug="!!!", whole_package=True)
        )
    assert excinfo.value.outcome is AuthorityOutcome.INVALID_SELECTOR
