"""The two authority views and deterministic selection — #137 contract 6.

Both views resolve the same effective authority, both identify the exact
four-component binding that produced them, and neither implies adapter
capability. Selection is deterministic lookup against exact semantic keys or the
explicit ``whole_package`` flag; a selector naming something the projection does
not contain is ``INVALID_REFERENCE``, never an empty slice.
"""

from __future__ import annotations

import dataclasses

from afterworlds.ingestion.mechanical.models import ComponentHandling
from afterworlds.models.enums import OverrideOperationEnum
from afterworlds.models.rules_package import RuleSliceRequest
from afterworlds.services.rules_authority import (
    AuthorityOutcome,
    RulesAuthorityService,
)
from afterworlds.services.rules_authority.views import GameMasterComponent
from tests.services.rules_authority.conftest import (
    CHECK_KEY,
    CREATURE_KEY,
    DESCRIPTOR_FACT_TARGET,
    DESCRIPTOR_KEY,
    NOW,
    OPEN_ENDED_KEY,
    PROSE_TEXT,
    SPELL_KEY,
    WISH_CHUNK,
    RuntimeFixture,
    author_override,
    replace_fact_payload,
)


def service(runtime: RuntimeFixture) -> RulesAuthorityService:
    return RulesAuthorityService(runtime.session, now=NOW)


def whole(runtime: RuntimeFixture) -> RuleSliceRequest:
    return RuleSliceRequest(package_id=runtime.package_uuid, whole_package=True)


# ---------------------------------------------------------------------------
# Consistency between the views
# ---------------------------------------------------------------------------


def test_both_views_identify_the_same_complete_binding(
    runtime: RuntimeFixture,
) -> None:
    """All four components, on every surface (#137 acceptance criterion 19)."""
    binding = service(runtime).resolve(package_uuid=runtime.package_uuid).binding
    assert binding is not None

    sliced = service(runtime).rule_slice(whole(runtime))
    typed = service(runtime).typed_view(whole(runtime))
    gm = service(runtime).gamemaster_view(whole(runtime))

    assert sliced.slice is not None
    assert typed.typed_view is not None
    assert gm.gamemaster_view is not None
    assert (
        sliced.slice.binding
        == typed.typed_view.binding
        == gm.gamemaster_view.binding
        == binding
    )


def test_both_views_report_the_same_applied_override_provenance(
    runtime: RuntimeFixture,
) -> None:
    author_override(
        runtime.session,
        override_id="ov-shared",
        target=DESCRIPTOR_FACT_TARGET,
        operation=OverrideOperationEnum.REPLACE,
        payload=replace_fact_payload(),
    )
    typed = service(runtime).typed_view(whole(runtime)).typed_view
    gm = service(runtime).gamemaster_view(whole(runtime)).gamemaster_view
    assert typed is not None and gm is not None
    assert typed.applied_overrides == gm.applied_overrides
    (applied,) = typed.applied_overrides
    assert applied.override_id == "ov-shared"
    assert applied.applied is True


# ---------------------------------------------------------------------------
# The typed view
# ---------------------------------------------------------------------------


def test_the_typed_view_carries_exact_source_linked_provenance(
    runtime: RuntimeFixture,
) -> None:
    """Every base fact names the 5c leaf subspans it was accepted from."""
    view = service(runtime).typed_view(whole(runtime)).typed_view
    assert view is not None
    facts = [
        fact
        for record in view.records
        for component in record.components
        for fact in component.facts
    ]
    assert facts
    assert all(fact.span_ids for fact in facts)


def test_the_typed_view_declares_no_adapter_capability(
    runtime: RuntimeFixture,
) -> None:
    """Representation and execution are independent (ADR-005d Decision 1).

    Asserted structurally rather than by inspection: no field on any view type
    mentions support, execution, or certification, so there is nowhere for a
    consumer to read a capability claim that this PR has no right to make.
    """
    view = service(runtime).typed_view(whole(runtime)).typed_view
    assert view is not None
    names = {
        field.name
        for record in view.records
        for component in record.components
        for field in dataclasses.fields(component)
    } | {field.name for field in dataclasses.fields(GameMasterComponent)}
    forbidden = ("support", "executable", "certif", "capab", "adapter")
    assert not [n for n in names if any(f in n for f in forbidden)]


# ---------------------------------------------------------------------------
# The GameMaster view
# ---------------------------------------------------------------------------


def test_the_gamemaster_view_resolves_exact_governing_prose(
    runtime: RuntimeFixture,
) -> None:
    """Bound by chunk identity, read from the authoritative 5c RuleChunk."""
    view = service(runtime).gamemaster_view(whole(runtime)).gamemaster_view
    assert view is not None
    (prose_bound,) = [c for c in view.components if c.component_key == OPEN_ENDED_KEY]
    assert prose_bound.handling is ComponentHandling.PROSE_BOUND
    assert prose_bound.irreducibility_reason_code == "open_ended_effect"
    (passage,) = prose_bound.governing_prose
    assert passage.chunk_id == WISH_CHUNK
    assert passage.text == PROSE_TEXT


def test_the_gamemaster_view_carries_structured_context_and_handling(
    runtime: RuntimeFixture,
) -> None:
    view = service(runtime).gamemaster_view(whole(runtime)).gamemaster_view
    assert view is not None
    (descriptor,) = [c for c in view.components if c.component_key == DESCRIPTOR_KEY]
    assert descriptor.handling is ComponentHandling.STRUCTURED
    assert descriptor.governing_prose == ()
    # Provenance lives where the projection puts it: a component's obligation is
    # span coverage under the classification contract, while each fact carries
    # its own edge (ADR-005d Decision 3). The view reports both as they are
    # rather than inventing a component-level edge.
    (fact,) = descriptor.structured_context
    assert fact.span_ids


def test_a_missing_bound_chunk_is_reported_not_substituted(
    runtime: RuntimeFixture,
) -> None:
    """A nearby passage is not the governing passage.

    The bound chunk is removed from the store; the view still names the exact
    chunk it is bound to and reports the text as absent rather than resolving
    something else in its place.
    """
    from sqlalchemy import delete

    from afterworlds.persistence.orm.rules_package import RuleChunkORM

    runtime.session.execute(
        delete(RuleChunkORM).where(RuleChunkORM.chunk_id == WISH_CHUNK)
    )
    runtime.session.flush()

    view = service(runtime).gamemaster_view(whole(runtime)).gamemaster_view
    assert view is not None
    (prose_bound,) = [c for c in view.components if c.component_key == OPEN_ENDED_KEY]
    (passage,) = prose_bound.governing_prose
    assert passage.chunk_id == WISH_CHUNK
    assert passage.text is None


# ---------------------------------------------------------------------------
# Deterministic selection
# ---------------------------------------------------------------------------


def test_whole_package_returns_every_record(runtime: RuntimeFixture) -> None:
    sliced = service(runtime).rule_slice(whole(runtime))
    assert sliced.slice is not None
    assert sliced.slice.whole_package is True
    assert {r.semantic_key for r in sliced.slice.records} == {
        SPELL_KEY,
        CREATURE_KEY,
    }


def test_a_record_selector_returns_that_record_whole(
    runtime: RuntimeFixture,
) -> None:
    sliced = service(runtime).rule_slice(
        RuleSliceRequest(package_id=runtime.package_uuid, record_selectors=(SPELL_KEY,))
    )
    assert sliced.slice is not None
    (record,) = sliced.slice.records
    assert record.semantic_key == SPELL_KEY
    assert {c.semantic_key for c in record.components} == {
        DESCRIPTOR_KEY,
        OPEN_ENDED_KEY,
    }


def test_a_component_selector_narrows_to_that_component(
    runtime: RuntimeFixture,
) -> None:
    sliced = service(runtime).rule_slice(
        RuleSliceRequest(
            package_id=runtime.package_uuid,
            component_selectors=((SPELL_KEY, DESCRIPTOR_KEY),),
        )
    )
    assert sliced.slice is not None
    (record,) = sliced.slice.records
    assert [c.semantic_key for c in record.components] == [DESCRIPTOR_KEY]


def test_the_broader_selector_wins_regardless_of_order(
    runtime: RuntimeFixture,
) -> None:
    """Selector order cannot change what a slice contains."""
    both = RuleSliceRequest(
        package_id=runtime.package_uuid,
        record_selectors=(SPELL_KEY,),
        component_selectors=((SPELL_KEY, DESCRIPTOR_KEY),),
    )
    sliced = service(runtime).rule_slice(both)
    assert sliced.slice is not None
    (record,) = sliced.slice.records
    assert {c.semantic_key for c in record.components} == {
        DESCRIPTOR_KEY,
        OPEN_ENDED_KEY,
    }


def test_an_unknown_record_selector_is_an_invalid_reference(
    runtime: RuntimeFixture,
) -> None:
    """Not an empty slice, which would read as "that rule does not apply"."""
    result = service(runtime).rule_slice(
        RuleSliceRequest(
            package_id=runtime.package_uuid, record_selectors=("spell:nonesuch",)
        )
    )
    assert result.outcome is AuthorityOutcome.INVALID_REFERENCE
    assert "spell:nonesuch" in result.detail
    assert result.slice is None


def test_an_unknown_component_selector_is_an_invalid_reference(
    runtime: RuntimeFixture,
) -> None:
    result = service(runtime).rule_slice(
        RuleSliceRequest(
            package_id=runtime.package_uuid,
            component_selectors=((SPELL_KEY, "no-such-component"),),
        )
    )
    assert result.outcome is AuthorityOutcome.INVALID_REFERENCE
    assert "no-such-component" in result.detail


def test_views_refuse_with_the_same_typed_outcome_as_the_slice(
    runtime: RuntimeFixture,
) -> None:
    """One resolution behind all three surfaces, so none can be softer."""
    bad = RuleSliceRequest(
        package_id=runtime.package_uuid, record_selectors=("spell:nonesuch",)
    )
    assert (
        service(runtime).rule_slice(bad).outcome
        is service(runtime).typed_view(bad).outcome
        is service(runtime).gamemaster_view(bad).outcome
        is AuthorityOutcome.INVALID_REFERENCE
    )


def test_a_slug_request_resolves_to_the_same_slice(
    runtime: RuntimeFixture,
) -> None:
    from sqlalchemy import select

    from afterworlds.persistence.orm.rules_package import RulesPackageORM
    from afterworlds.services.rules_authority import package_slug
    from tests.services.rules_authority.conftest import (
        PACKAGE_NAME,
        RIVAL_PACKAGE_UUID,
    )

    rival = runtime.session.execute(
        select(RulesPackageORM).where(
            RulesPackageORM.rules_package_id == RIVAL_PACKAGE_UUID
        )
    ).scalar_one()
    rival.name = "Another corpus entirely"
    runtime.session.flush()

    by_uuid = service(runtime).rule_slice(whole(runtime))
    by_slug = service(runtime).rule_slice(
        RuleSliceRequest(package_slug=package_slug(PACKAGE_NAME), whole_package=True)
    )
    assert by_slug.outcome is AuthorityOutcome.RESOLVED
    assert by_uuid.slice is not None and by_slug.slice is not None
    assert by_slug.slice.binding == by_uuid.slice.binding
    assert by_slug.slice.records == by_uuid.slice.records


def test_a_slice_over_an_unpublished_package_is_typed(
    runtime: RuntimeFixture,
) -> None:
    result = service(runtime).rule_slice(
        RuleSliceRequest(package_id=runtime.rival_package_uuid, whole_package=True)
    )
    assert result.outcome is AuthorityOutcome.UNPUBLISHED
    assert result.slice is None


def test_selection_reaches_a_creature_component(runtime: RuntimeFixture) -> None:
    sliced = service(runtime).rule_slice(
        RuleSliceRequest(
            package_id=runtime.package_uuid,
            component_selectors=((CREATURE_KEY, CHECK_KEY),),
        )
    )
    assert sliced.slice is not None
    (record,) = sliced.slice.records
    assert record.semantic_key == CREATURE_KEY
    assert [c.semantic_key for c in record.components] == [CHECK_KEY]
