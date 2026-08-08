"""Typed record/component/fact overrides — ADR-005d Decision 10.

Existing precedence and operation semantics are preserved: ordering is
ascending ``(precedence, override_id)``, ``DISABLE`` suppresses an exact target
and stops later processing of it, ``REPLACE`` supplies a complete validated
replacement, and ``APPEND`` adds only where the owning schema permits
multiplicity.

The negative controls are the point of the module. Each one is a patch that is
*well-formed* and still refused: outside the closed union, aimed at a target that
does not exist, incompatible with its target's type, or appended where nothing
can be appended.
"""

from __future__ import annotations

import pytest

from afterworlds.ingestion.mechanical.models import ComponentHandling
from afterworlds.models.enums import OverrideOperationEnum, OverrideOriginEnum
from afterworlds.models.rules_package import RuleSliceRequest
from afterworlds.services.rules_authority import (
    AuthorityOutcome,
    MechanicalTarget,
    MechanicalTargetKind,
    RulesAuthorityService,
)
from tests.services.rules_authority.conftest import (
    ADDED_CHECK,
    CHECK_COMPONENT_TARGET,
    CHECK_FACT_KEY,
    CHECK_KEY,
    CREATURE_KEY,
    CREATURE_RECORD_TARGET,
    DESCRIPTOR_COMPONENT_TARGET,
    DESCRIPTOR_FACT_KEY,
    DESCRIPTOR_FACT_TARGET,
    DESCRIPTOR_KEY,
    DISABLE_PAYLOAD,
    NOW,
    OPEN_ENDED_KEY,
    PROSE_COMPONENT_TARGET,
    REPLACEMENT_DESCRIPTOR,
    SPELL_KEY,
    SPELL_RECORD_TARGET,
    RuntimeFixture,
    append_component_payload,
    append_fact_payload,
    author_override,
    replace_component_payload,
    replace_fact_payload,
    replace_record_payload,
)


def whole_package(runtime: RuntimeFixture) -> RuleSliceRequest:
    return RuleSliceRequest(package_id=runtime.package_uuid, whole_package=True)


def effective(runtime: RuntimeFixture):  # type: ignore[no-untyped-def]
    result = RulesAuthorityService(runtime.session, now=NOW).typed_view(
        whole_package(runtime)
    )
    assert result.outcome is AuthorityOutcome.RESOLVED, result.detail
    assert result.typed_view is not None
    return result.typed_view


def refusal(runtime: RuntimeFixture):  # type: ignore[no-untyped-def]
    return RulesAuthorityService(runtime.session, now=NOW).typed_view(
        whole_package(runtime)
    )


def record(view, key: str):  # type: ignore[no-untyped-def]
    matches = [r for r in view.records if r.semantic_key == key]
    return matches[0] if matches else None


def component(view, record_key: str, key: str):  # type: ignore[no-untyped-def]
    found = record(view, record_key)
    if found is None:
        return None
    matches = [c for c in found.components if c.semantic_key == key]
    return matches[0] if matches else None


# ---------------------------------------------------------------------------
# The unpatched view
# ---------------------------------------------------------------------------


def test_the_base_view_is_the_projection(runtime: RuntimeFixture) -> None:
    """Without overrides the effective view is the published authority."""
    view = effective(runtime)
    assert {r.semantic_key for r in view.records} == {SPELL_KEY, CREATURE_KEY}
    descriptor = component(view, SPELL_KEY, DESCRIPTOR_KEY)
    assert descriptor is not None
    assert descriptor.handling is ComponentHandling.STRUCTURED
    assert [f.fact_key for f in descriptor.facts] == [DESCRIPTOR_FACT_KEY]
    # Base authority carries 5c span provenance and no override provenance.
    assert descriptor.facts[0].span_ids
    assert descriptor.facts[0].supplied_by_override_id is None
    assert view.applied_overrides == ()


# ---------------------------------------------------------------------------
# DISABLE
# ---------------------------------------------------------------------------


def test_disable_suppresses_an_exact_fact(runtime: RuntimeFixture) -> None:
    author_override(
        runtime.session,
        override_id="ov-disable-fact",
        target=DESCRIPTOR_FACT_TARGET,
        operation=OverrideOperationEnum.DISABLE,
        payload=DISABLE_PAYLOAD,
    )
    view = effective(runtime)

    descriptor = component(view, SPELL_KEY, DESCRIPTOR_KEY)
    assert descriptor is not None
    assert descriptor.facts == ()
    # Its sibling record is untouched.
    check = component(view, CREATURE_KEY, CHECK_KEY)
    assert check is not None
    assert [f.fact_key for f in check.facts] == [CHECK_FACT_KEY]


def test_disable_suppresses_an_exact_component(runtime: RuntimeFixture) -> None:
    author_override(
        runtime.session,
        override_id="ov-disable-component",
        target=PROSE_COMPONENT_TARGET,
        operation=OverrideOperationEnum.DISABLE,
        payload=DISABLE_PAYLOAD,
    )
    view = effective(runtime)

    assert component(view, SPELL_KEY, OPEN_ENDED_KEY) is None
    assert component(view, SPELL_KEY, DESCRIPTOR_KEY) is not None


def test_disable_suppresses_an_exact_record(runtime: RuntimeFixture) -> None:
    author_override(
        runtime.session,
        override_id="ov-disable-record",
        target=CREATURE_RECORD_TARGET,
        operation=OverrideOperationEnum.DISABLE,
        payload=DISABLE_PAYLOAD,
    )
    view = effective(runtime)

    assert record(view, CREATURE_KEY) is None
    assert record(view, SPELL_KEY) is not None


def test_disable_stops_later_processing_of_the_same_target(
    runtime: RuntimeFixture,
) -> None:
    """The existing precedence rule: the first winning disable ends the target.

    A later replace does not resurrect suppressed authority, and the provenance
    says why it did not.
    """
    author_override(
        runtime.session,
        override_id="ov-1-disable",
        target=DESCRIPTOR_COMPONENT_TARGET,
        operation=OverrideOperationEnum.DISABLE,
        payload=DISABLE_PAYLOAD,
        precedence=10,
    )
    author_override(
        runtime.session,
        override_id="ov-2-replace",
        target=DESCRIPTOR_COMPONENT_TARGET,
        operation=OverrideOperationEnum.REPLACE,
        payload=replace_component_payload(),
        precedence=20,
    )
    view = effective(runtime)

    assert component(view, SPELL_KEY, DESCRIPTOR_KEY) is None
    first, second = view.applied_overrides
    assert (first.override_id, first.applied) == ("ov-1-disable", True)
    assert (second.override_id, second.applied) == ("ov-2-replace", False)
    assert "already suppressed" in second.note


def test_disabling_a_record_suppresses_the_facts_beneath_it(
    runtime: RuntimeFixture,
) -> None:
    author_override(
        runtime.session,
        override_id="ov-1-disable-record",
        target=SPELL_RECORD_TARGET,
        operation=OverrideOperationEnum.DISABLE,
        payload=DISABLE_PAYLOAD,
        precedence=10,
    )
    author_override(
        runtime.session,
        override_id="ov-2-replace-fact",
        target=DESCRIPTOR_FACT_TARGET,
        operation=OverrideOperationEnum.REPLACE,
        payload=replace_fact_payload(),
        precedence=20,
    )
    view = effective(runtime)

    assert record(view, SPELL_KEY) is None
    assert view.applied_overrides[1].applied is False


def test_an_override_authored_disabled_changes_nothing(
    runtime: RuntimeFixture,
) -> None:
    """It still appears in the ordered provenance, marked as not applied."""
    author_override(
        runtime.session,
        override_id="ov-inactive",
        target=DESCRIPTOR_FACT_TARGET,
        operation=OverrideOperationEnum.DISABLE,
        payload=DISABLE_PAYLOAD,
        is_enabled=False,
    )
    view = effective(runtime)

    descriptor = component(view, SPELL_KEY, DESCRIPTOR_KEY)
    assert descriptor is not None
    assert [f.fact_key for f in descriptor.facts] == [DESCRIPTOR_FACT_KEY]
    (entry,) = view.applied_overrides
    assert entry.applied is False
    assert entry.note == "authored disabled"


# ---------------------------------------------------------------------------
# REPLACE
# ---------------------------------------------------------------------------


def test_replace_supplies_a_complete_fact(runtime: RuntimeFixture) -> None:
    author_override(
        runtime.session,
        override_id="ov-replace-fact",
        target=DESCRIPTOR_FACT_TARGET,
        operation=OverrideOperationEnum.REPLACE,
        payload=replace_fact_payload(),
        origin=OverrideOriginEnum.PACKAGE_PATCH,
    )
    view = effective(runtime)

    descriptor = component(view, SPELL_KEY, DESCRIPTOR_KEY)
    assert descriptor is not None
    (fact,) = descriptor.facts
    assert fact.fact == REPLACEMENT_DESCRIPTOR
    # Provenance-exact: the override record and its origin, not a source span.
    assert fact.supplied_by_override_id == "ov-replace-fact"
    assert fact.supplied_by_origin is OverrideOriginEnum.PACKAGE_PATCH
    assert fact.span_ids == ()


def test_replace_supplies_a_complete_component(runtime: RuntimeFixture) -> None:
    author_override(
        runtime.session,
        override_id="ov-replace-component",
        target=DESCRIPTOR_COMPONENT_TARGET,
        operation=OverrideOperationEnum.REPLACE,
        payload=replace_component_payload(),
    )
    view = effective(runtime)

    descriptor = component(view, SPELL_KEY, DESCRIPTOR_KEY)
    assert descriptor is not None
    assert descriptor.supplied_by_override_id == "ov-replace-component"
    assert [f.fact for f in descriptor.facts] == [REPLACEMENT_DESCRIPTOR]


def test_replace_record_is_record_kind_specific(runtime: RuntimeFixture) -> None:
    """A whole record is replaceable only through its own kind's patch."""
    author_override(
        runtime.session,
        override_id="ov-replace-record",
        target=SPELL_RECORD_TARGET,
        operation=OverrideOperationEnum.REPLACE,
        payload=replace_record_payload(),
    )
    view = effective(runtime)

    spell = record(view, SPELL_KEY)
    assert spell is not None
    assert [c.semantic_key for c in spell.components] == [DESCRIPTOR_KEY]
    assert spell.supplied_by_override_id == "ov-replace-record"


# ---------------------------------------------------------------------------
# APPEND
# ---------------------------------------------------------------------------


def test_append_adds_a_fact_where_a_component_permits_multiplicity(
    runtime: RuntimeFixture,
) -> None:
    author_override(
        runtime.session,
        override_id="ov-append-fact",
        target=CHECK_COMPONENT_TARGET,
        operation=OverrideOperationEnum.APPEND,
        payload=append_fact_payload(),
    )
    view = effective(runtime)

    check = component(view, CREATURE_KEY, CHECK_KEY)
    assert check is not None
    assert {f.fact for f in check.facts} == {check.facts[0].fact, ADDED_CHECK}
    added = [f for f in check.facts if f.supplied_by_override_id][0]
    assert added.fact == ADDED_CHECK


def test_append_adds_a_component_where_a_record_permits_multiplicity(
    runtime: RuntimeFixture,
) -> None:
    author_override(
        runtime.session,
        override_id="ov-append-component",
        target=CREATURE_RECORD_TARGET,
        operation=OverrideOperationEnum.APPEND,
        payload=append_component_payload(),
    )
    view = effective(runtime)

    added = component(view, CREATURE_KEY, "house-rider")
    assert added is not None
    assert added.supplied_by_override_id == "ov-append-component"
    assert component(view, CREATURE_KEY, CHECK_KEY) is not None


# ---------------------------------------------------------------------------
# Negative controls
# ---------------------------------------------------------------------------


def test_append_onto_a_fact_is_refused(runtime: RuntimeFixture) -> None:
    """A fact is a single value; the owning schema declares no multiplicity."""
    author_override(
        runtime.session,
        override_id="ov-append-fact-target",
        target=DESCRIPTOR_FACT_TARGET,
        operation=OverrideOperationEnum.APPEND,
        payload=append_fact_payload(),
    )
    result = refusal(runtime)
    assert result.outcome is AuthorityOutcome.INVALID_OVERRIDE
    assert "no multiplicity" in result.detail


def test_a_type_incompatible_record_patch_is_refused(
    runtime: RuntimeFixture,
) -> None:
    """The declared record kind must be the target record's kind."""
    author_override(
        runtime.session,
        override_id="ov-wrong-kind",
        target=SPELL_RECORD_TARGET,
        operation=OverrideOperationEnum.REPLACE,
        payload=replace_record_payload(record_kind="creature"),
    )
    result = refusal(runtime)
    assert result.outcome is AuthorityOutcome.INVALID_OVERRIDE
    assert "declares kind" in result.detail


def test_a_patch_of_the_wrong_family_is_refused(runtime: RuntimeFixture) -> None:
    """A well-formed payload of another family is still the wrong patch."""
    author_override(
        runtime.session,
        override_id="ov-wrong-family",
        target=DESCRIPTOR_FACT_TARGET,
        operation=OverrideOperationEnum.REPLACE,
        payload=replace_component_payload(),
    )
    result = refusal(runtime)
    assert result.outcome is AuthorityOutcome.INVALID_OVERRIDE
    assert "requires a replace_fact patch" in result.detail


def test_a_fact_outside_the_closed_union_is_refused(
    runtime: RuntimeFixture,
) -> None:
    author_override(
        runtime.session,
        override_id="ov-unknown-family",
        target=DESCRIPTOR_FACT_TARGET,
        operation=OverrideOperationEnum.REPLACE,
        payload={
            "patch": "replace_fact",
            "fact": {"family": "damage_expression", "expression": "2d6+3"},
        },
    )
    result = refusal(runtime)
    assert result.outcome is AuthorityOutcome.INVALID_OVERRIDE
    assert "closed typed-fact union" in result.detail


def test_a_mistyped_fact_field_is_refused(runtime: RuntimeFixture) -> None:
    """No coercion: ``"9"`` is not 9, here or in persistence."""
    author_override(
        runtime.session,
        override_id="ov-mistyped",
        target=DESCRIPTOR_FACT_TARGET,
        operation=OverrideOperationEnum.REPLACE,
        payload={
            "patch": "replace_fact",
            "fact": {
                "family": "spell_descriptor",
                "level": "9",
                "school": "illusion",
                "ritual": False,
                "concentration": False,
            },
        },
    )
    result = refusal(runtime)
    assert result.outcome is AuthorityOutcome.INVALID_OVERRIDE


def test_a_prose_bound_override_component_is_refused(
    runtime: RuntimeFixture,
) -> None:
    """Runtime patches cannot author governing prose (#137 contract 3)."""
    author_override(
        runtime.session,
        override_id="ov-prose",
        target=DESCRIPTOR_COMPONENT_TARGET,
        operation=OverrideOperationEnum.REPLACE,
        payload={
            "patch": "replace_component",
            "component": {"handling": "prose_bound", "facts": []},
        },
    )
    result = refusal(runtime)
    assert result.outcome is AuthorityOutcome.INVALID_OVERRIDE
    assert "must be structured" in result.detail


def test_an_override_targeting_a_missing_record_is_refused(
    runtime: RuntimeFixture,
) -> None:
    author_override(
        runtime.session,
        override_id="ov-missing-record",
        target=MechanicalTarget(
            kind=MechanicalTargetKind.RECORD, record_key="spell:no-such-spell"
        ),
        operation=OverrideOperationEnum.DISABLE,
        payload=DISABLE_PAYLOAD,
    )
    result = refusal(runtime)
    assert result.outcome is AuthorityOutcome.INVALID_OVERRIDE
    assert "names no record" in result.detail


def test_an_override_targeting_a_missing_fact_is_refused(
    runtime: RuntimeFixture,
) -> None:
    author_override(
        runtime.session,
        override_id="ov-missing-fact",
        target=MechanicalTarget(
            kind=MechanicalTargetKind.FACT,
            record_key=SPELL_KEY,
            component_key=DESCRIPTOR_KEY,
            fact_key="0" * 16,
        ),
        operation=OverrideOperationEnum.DISABLE,
        payload=DISABLE_PAYLOAD,
    )
    result = refusal(runtime)
    assert result.outcome is AuthorityOutcome.INVALID_OVERRIDE
    assert "names no fact" in result.detail


def test_appending_a_duplicate_fact_is_refused(runtime: RuntimeFixture) -> None:
    """Duplicate-as-coverage is refused at runtime as it is at publication."""
    author_override(
        runtime.session,
        override_id="ov-duplicate",
        target=CHECK_COMPONENT_TARGET,
        operation=OverrideOperationEnum.APPEND,
        payload=append_fact_payload(_existing_check()),
    )
    result = refusal(runtime)
    assert result.outcome is AuthorityOutcome.INVALID_OVERRIDE
    assert "would duplicate" in result.detail


def test_appending_a_duplicate_component_is_refused(
    runtime: RuntimeFixture,
) -> None:
    author_override(
        runtime.session,
        override_id="ov-duplicate-component",
        target=CREATURE_RECORD_TARGET,
        operation=OverrideOperationEnum.APPEND,
        payload=append_component_payload(semantic_key=CHECK_KEY),
    )
    result = refusal(runtime)
    assert result.outcome is AuthorityOutcome.INVALID_OVERRIDE
    assert "would duplicate" in result.detail


def test_appending_a_fact_to_prose_bound_authority_is_refused(
    runtime: RuntimeFixture,
) -> None:
    """A published prose-bound judgement is not reversible by an override."""
    author_override(
        runtime.session,
        override_id="ov-append-to-prose",
        target=PROSE_COMPONENT_TARGET,
        operation=OverrideOperationEnum.APPEND,
        payload=append_fact_payload(),
    )
    result = refusal(runtime)
    assert result.outcome is AuthorityOutcome.INVALID_OVERRIDE
    assert "prose-bound" in result.detail


def test_a_structured_override_component_with_no_facts_is_refused(
    runtime: RuntimeFixture,
) -> None:
    author_override(
        runtime.session,
        override_id="ov-empty-structured",
        target=DESCRIPTOR_COMPONENT_TARGET,
        operation=OverrideOperationEnum.REPLACE,
        payload={
            "patch": "replace_component",
            "component": {"handling": "structured", "facts": []},
        },
    )
    result = refusal(runtime)
    assert result.outcome is AuthorityOutcome.INVALID_OVERRIDE
    assert "no facts" in result.detail


@pytest.mark.parametrize(
    "payload",
    [
        {"patch": "disable", "extra": 1},
        {"patch": "not-a-family"},
        {"nothing": True},
    ],
)
def test_a_payload_outside_the_closed_patch_union_is_refused(
    runtime: RuntimeFixture, payload: dict[str, object]
) -> None:
    author_override(
        runtime.session,
        override_id="ov-malformed",
        target=DESCRIPTOR_FACT_TARGET,
        operation=OverrideOperationEnum.DISABLE,
        payload=payload,
    )
    assert refusal(runtime).outcome is AuthorityOutcome.INVALID_OVERRIDE


def _existing_check():  # type: ignore[no-untyped-def]
    from tests.services.rules_authority.conftest import CHECK_FACT

    return CHECK_FACT
