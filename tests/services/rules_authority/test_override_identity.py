"""Override-set identity — ADR-005d Decision 9, #137 acceptance criterion 21.

The identity is derived from the canonical ordered effective override state, and
these tests are the contract for exactly what "effective override state" means:
which changes must move it, and which must not.

Every test here changes **one** thing. That is deliberate — an identity test
that perturbs two fields at once proves only that something moved.
"""

from __future__ import annotations

import pytest

from afterworlds.ingestion.mechanical.representation import (
    SpellDescriptorFact,
    SpellSchool,
)
from afterworlds.models.enums import OverrideOperationEnum, OverrideOriginEnum
from afterworlds.persistence.orm.rules_authority import MechanicalOverrideORM
from afterworlds.services.rules_authority import (
    EMPTY_OVERRIDE_SET_UUID,
    AuthorityOutcome,
    MechanicalTarget,
    MechanicalTargetKind,
    RulesAuthorityService,
    collect_current_override_state,
    override_set_identity,
)
from tests.services.rules_authority.conftest import (
    ADDED_CHECK,
    CHECK_COMPONENT_TARGET,
    DESCRIPTOR_COMPONENT_TARGET,
    DESCRIPTOR_FACT_TARGET,
    DISABLE_PAYLOAD,
    NOW,
    PACKAGE_UUID,
    RELEASE_VERSION,
    REPLACEMENT_DESCRIPTOR,
    SPELL_KEY,
    RuntimeFixture,
    append_fact_payload,
    author_override,
    replace_component_payload,
    replace_fact_payload,
)


def identity(runtime: RuntimeFixture) -> str:
    return collect_current_override_state(
        runtime.session, PACKAGE_UUID, RELEASE_VERSION
    ).override_set_uuid


def resolved_identity(runtime: RuntimeFixture) -> str:
    resolution = RulesAuthorityService(runtime.session, now=NOW).resolve(
        package_uuid=runtime.package_uuid
    )
    assert resolution.outcome is AuthorityOutcome.RESOLVED
    assert resolution.binding is not None
    return str(resolution.binding.override_set_uuid)


# ---------------------------------------------------------------------------
# The empty set
# ---------------------------------------------------------------------------


def test_the_empty_override_set_has_its_own_deterministic_identity(
    runtime: RuntimeFixture,
) -> None:
    """ "No overrides" is a value, not the absence of one (Decision 9)."""
    assert identity(runtime) == EMPTY_OVERRIDE_SET_UUID
    assert override_set_identity(()) == EMPTY_OVERRIDE_SET_UUID
    assert EMPTY_OVERRIDE_SET_UUID


def test_the_resolved_binding_carries_the_empty_identity(
    runtime: RuntimeFixture,
) -> None:
    """A package with no overrides still binds a real override-set UUID."""
    assert resolved_identity(runtime) == EMPTY_OVERRIDE_SET_UUID


def test_authoring_one_override_moves_the_identity(runtime: RuntimeFixture) -> None:
    before = identity(runtime)
    author_override(
        runtime.session,
        override_id="ov-1",
        target=DESCRIPTOR_FACT_TARGET,
        operation=OverrideOperationEnum.DISABLE,
        payload=DISABLE_PAYLOAD,
    )
    assert identity(runtime) != before


def test_removing_the_only_override_returns_to_the_empty_identity(
    runtime: RuntimeFixture,
) -> None:
    row = author_override(
        runtime.session,
        override_id="ov-1",
        target=DESCRIPTOR_FACT_TARGET,
        operation=OverrideOperationEnum.DISABLE,
        payload=DISABLE_PAYLOAD,
    )
    assert identity(runtime) != EMPTY_OVERRIDE_SET_UUID
    runtime.session.delete(row)
    runtime.session.flush()
    assert identity(runtime) == EMPTY_OVERRIDE_SET_UUID


# ---------------------------------------------------------------------------
# One change at a time
# ---------------------------------------------------------------------------


def _baseline(runtime: RuntimeFixture) -> str:
    author_override(
        runtime.session,
        override_id="ov-baseline",
        target=DESCRIPTOR_FACT_TARGET,
        operation=OverrideOperationEnum.REPLACE,
        payload=replace_fact_payload(),
        precedence=10,
        origin=OverrideOriginEnum.HOUSE_RULE,
    )
    return identity(runtime)


def test_recreating_an_identical_override_under_a_new_id_moves_the_identity(
    runtime: RuntimeFixture,
) -> None:
    """#137 contract 5, negative control 1.

    Provenance-exact, not merely mechanically equivalent: the same patch under a
    different authoritative record is a different authority.
    """
    before = _baseline(runtime)
    original = runtime.session.get(MechanicalOverrideORM, "ov-baseline")
    assert original is not None
    runtime.session.delete(original)
    runtime.session.flush()
    author_override(
        runtime.session,
        override_id="ov-recreated",
        target=DESCRIPTOR_FACT_TARGET,
        operation=OverrideOperationEnum.REPLACE,
        payload=replace_fact_payload(),
        precedence=10,
        origin=OverrideOriginEnum.HOUSE_RULE,
    )

    assert identity(runtime) != before


def test_changing_only_the_origin_moves_the_identity(
    runtime: RuntimeFixture,
) -> None:
    """#137 contract 5, negative control 2.

    A house rule and a package patch with identical mechanical contents are not
    the same authority.
    """
    before = _baseline(runtime)
    row = runtime.session.get(MechanicalOverrideORM, "ov-baseline")
    assert row is not None
    row.override_origin = OverrideOriginEnum.PACKAGE_PATCH.value
    runtime.session.flush()

    assert identity(runtime) != before


def test_disabling_an_override_moves_the_identity(runtime: RuntimeFixture) -> None:
    before = _baseline(runtime)
    row = runtime.session.get(MechanicalOverrideORM, "ov-baseline")
    assert row is not None
    row.is_enabled = False
    runtime.session.flush()

    assert identity(runtime) != before


def test_reprioritizing_an_override_moves_the_identity(
    runtime: RuntimeFixture,
) -> None:
    before = _baseline(runtime)
    row = runtime.session.get(MechanicalOverrideORM, "ov-baseline")
    assert row is not None
    row.precedence = 999
    runtime.session.flush()

    assert identity(runtime) != before


def test_reordering_two_overrides_moves_the_identity(
    runtime: RuntimeFixture,
) -> None:
    """Order is part of the state, because order decides what wins."""
    author_override(
        runtime.session,
        override_id="ov-a",
        target=DESCRIPTOR_COMPONENT_TARGET,
        operation=OverrideOperationEnum.REPLACE,
        payload=replace_component_payload(),
        precedence=10,
    )
    author_override(
        runtime.session,
        override_id="ov-b",
        target=CHECK_COMPONENT_TARGET,
        operation=OverrideOperationEnum.APPEND,
        payload=append_fact_payload(),
        precedence=20,
    )
    before = identity(runtime)

    first = runtime.session.get(MechanicalOverrideORM, "ov-a")
    second = runtime.session.get(MechanicalOverrideORM, "ov-b")
    assert first is not None and second is not None
    first.precedence, second.precedence = 20, 10
    runtime.session.flush()

    assert identity(runtime) != before


def test_retargeting_an_override_moves_the_identity(runtime: RuntimeFixture) -> None:
    before = _baseline(runtime)
    row = runtime.session.get(MechanicalOverrideORM, "ov-baseline")
    assert row is not None
    row.target_component_key = "some-other-component"
    runtime.session.flush()

    assert identity(runtime) != before


def test_changing_the_operation_moves_the_identity(runtime: RuntimeFixture) -> None:
    before = _baseline(runtime)
    row = runtime.session.get(MechanicalOverrideORM, "ov-baseline")
    assert row is not None
    row.override_operation = OverrideOperationEnum.DISABLE.value
    row.payload = DISABLE_PAYLOAD
    runtime.session.flush()

    assert identity(runtime) != before


def test_changing_the_payload_moves_the_identity(runtime: RuntimeFixture) -> None:
    before = _baseline(runtime)
    row = runtime.session.get(MechanicalOverrideORM, "ov-baseline")
    assert row is not None
    row.payload = replace_fact_payload(_other_descriptor())
    runtime.session.flush()

    assert identity(runtime) != before


# ---------------------------------------------------------------------------
# What identity must *not* depend on
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("created_at", "2027-01-01T00:00:00Z"),
        ("created_by", "someone-else"),
        ("note", "an operator comment added after the fact"),
    ],
)
def test_incidental_audit_metadata_does_not_move_the_identity(
    runtime: RuntimeFixture, field: str, value: str
) -> None:
    """Decision 9: audit metadata stays outside identity.

    Creation timestamps, authors, and comments do not participate in
    applicability, ordering, or resolution, so a re-annotated override is the
    same authority.
    """
    before = _baseline(runtime)
    row = runtime.session.get(MechanicalOverrideORM, "ov-baseline")
    assert row is not None
    setattr(row, field, value)
    runtime.session.flush()

    assert identity(runtime) == before


def test_package_scope_does_not_reach_inside_the_identity(
    runtime: RuntimeFixture,
) -> None:
    """The enclosing binding supplies package scope (Decision 9).

    Two packages with no overrides therefore share the empty identity — which is
    what makes it *the* empty override set rather than one per package. The
    binding still distinguishes them, because its other three components do.
    """
    primary = collect_current_override_state(
        runtime.session, PACKAGE_UUID, RELEASE_VERSION
    )
    rival = collect_current_override_state(
        runtime.session, str(runtime.rival_package_uuid), RELEASE_VERSION
    )
    assert primary.override_set_uuid == rival.override_set_uuid


def test_identity_is_stable_across_repeated_derivation(
    runtime: RuntimeFixture,
) -> None:
    """Content-derived means reproducible, not merely unique."""
    _baseline(runtime)
    assert identity(runtime) == identity(runtime) == resolved_identity(runtime)


# ---------------------------------------------------------------------------
# Target shape
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "kwargs",
    [
        {"kind": MechanicalTargetKind.COMPONENT, "record_key": SPELL_KEY},
        {
            "kind": MechanicalTargetKind.RECORD,
            "record_key": SPELL_KEY,
            "component_key": "c",
        },
        {
            "kind": MechanicalTargetKind.FACT,
            "record_key": SPELL_KEY,
            "component_key": "c",
        },
        {
            "kind": MechanicalTargetKind.COMPONENT,
            "record_key": SPELL_KEY,
            "component_key": "c",
            "fact_key": "f",
        },
        {"kind": MechanicalTargetKind.RECORD, "record_key": "  "},
    ],
)
def test_a_target_whose_keys_do_not_match_its_kind_is_refused(
    kwargs: dict[str, object],
) -> None:
    """A target that identifies nothing cannot participate in an identity."""
    with pytest.raises(Exception) as excinfo:
        MechanicalTarget(**kwargs)  # type: ignore[arg-type]
    assert "target" in str(excinfo.value)


def _other_descriptor() -> SpellDescriptorFact:
    return SpellDescriptorFact(
        level=3, school=SpellSchool.EVOCATION, ritual=False, concentration=True
    )


def test_identity_is_over_the_canonical_patch_not_the_stored_bytes(
    runtime: RuntimeFixture,
) -> None:
    """Equivalent patches are one authority (ADR-005d Decision 9).

    The identity covers the complete *validated* payload, so a payload that
    lists the same facts in a different order canonicalizes to the same patch
    and must not mint a second identity. Hashing the stored bytes directly is
    the canonicalization gap this asserts against — the same defect family that
    made partial sort keys leak authoring order into the projection UUID.
    """
    author_override(
        runtime.session,
        override_id="ov-order-a",
        target=DESCRIPTOR_COMPONENT_TARGET,
        operation=OverrideOperationEnum.REPLACE,
        payload=replace_component_payload((REPLACEMENT_DESCRIPTOR, ADDED_CHECK)),
    )
    forward = identity(runtime)

    row = runtime.session.get(MechanicalOverrideORM, "ov-order-a")
    assert row is not None
    row.payload = replace_component_payload((ADDED_CHECK, REPLACEMENT_DESCRIPTOR))
    runtime.session.flush()

    assert identity(runtime) == forward


def test_a_payload_with_no_canonical_form_is_refused_not_identified(
    runtime: RuntimeFixture,
) -> None:
    """A malformed override cannot be skipped into someone else's identity."""
    author_override(
        runtime.session,
        override_id="ov-not-a-patch",
        target=DESCRIPTOR_FACT_TARGET,
        operation=OverrideOperationEnum.REPLACE,
        payload={"patch": "replace_fact", "fact": {"family": "made_up"}},
    )
    with pytest.raises(Exception, match="closed typed-fact union"):
        identity(runtime)
    assert (
        RulesAuthorityService(runtime.session, now=NOW)
        .resolve(package_uuid=runtime.package_uuid)
        .outcome
        is AuthorityOutcome.INVALID_OVERRIDE
    )
