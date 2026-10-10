"""The extended ``RuleSliceRequest`` seam — #137 contract 6.

Two fail-open behaviours had to lose every surviving caller:

* a package reference parsed with ``UUID(...)`` and, on ``ValueError``, silently
  dropped; and
* a request carrying no selectors at all, which always produced an empty slice
  that read like "no rule applies".

These tests assert the model itself now refuses both, so no caller can
reintroduce either by construction, and that the production rule-slice path
(``RulesPackageService.get_active_rule_slice``, extended at the final cutover)
reports a typed reason instead of an empty result. The UUID-passthrough
``resolve_slice_package`` seam was deleted at that cutover: the request now goes
to the typed authority whole.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from sqlalchemy import select

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


@pytest.mark.parametrize(
    "legacy",
    [
        {"subsystem_tags": ["combat"]},
        {"entity_refs": [("spell", "Wish")]},
        {"include_non_published": True},
    ],
)
def test_a_retired_legacy_selector_is_refused_not_ignored(
    runtime: RuntimeFixture, legacy: dict[str, object]
) -> None:
    """Final cutover: the legacy chunk/``MechanicalEntity`` selectors are gone.

    Refused even beside a valid selection, so a caller still sending one learns
    it selects nothing on the typed path instead of having it silently dropped.
    """
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        RuleSliceRequest(package_id=runtime.package_uuid, whole_package=True, **legacy)


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
    sliced = service.get_active_rule_slice(
        RuleSliceRequest(package_slug=package_slug(PACKAGE_NAME), whole_package=True)
    )
    assert sliced.binding.package_uuid == runtime.package_uuid


def test_a_uuid_request_resolves_to_the_same_exact_binding(
    runtime: RuntimeFixture,
) -> None:
    """AC18: a valid slug and the matching UUID bind identically."""
    rival = runtime.session.execute(
        select(RulesPackageORM).where(
            RulesPackageORM.rules_package_id == RIVAL_PACKAGE_UUID
        )
    ).scalar_one()
    rival.name = "Unrelated corpus"
    runtime.session.flush()
    service = RulesPackageService(runtime.session)
    by_uuid = service.get_active_rule_slice(
        RuleSliceRequest(package_id=runtime.package_uuid, whole_package=True)
    )
    by_slug = service.get_active_rule_slice(
        RuleSliceRequest(package_slug=package_slug(PACKAGE_NAME), whole_package=True)
    )
    assert by_uuid.binding == by_slug.binding
    assert by_uuid.binding.mechanical_projection_uuid == runtime.projection_uuid


def test_an_ambiguous_slug_raises_a_typed_resolution_error(
    runtime: RuntimeFixture,
) -> None:
    """Explicit failure, carrying which state it is — not an empty slice."""
    service = RulesPackageService(runtime.session)
    with pytest.raises(RuleSliceResolutionError) as excinfo:
        service.get_active_rule_slice(
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
        service.get_active_rule_slice(
            RuleSliceRequest(package_slug="nothing-here", whole_package=True)
        )
    assert excinfo.value.outcome is AuthorityOutcome.ABSENT


def test_a_malformed_slug_raises_a_typed_resolution_error(
    runtime: RuntimeFixture,
) -> None:
    service = RulesPackageService(runtime.session)
    with pytest.raises(RuleSliceResolutionError) as excinfo:
        service.get_active_rule_slice(
            RuleSliceRequest(package_slug="!!!", whole_package=True)
        )
    assert excinfo.value.outcome is AuthorityOutcome.INVALID_SELECTOR
